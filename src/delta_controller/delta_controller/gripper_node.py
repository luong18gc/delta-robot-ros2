"""
Node giác hút ảo cho robot delta: dịch vụ /gripper/grip và /gripper/release.

Hút = gửi attach tới DetachableJoint (tool0 -> vật) trong Gazebo, chỉ khi platform nằm sát
đỉnh vật (gripper_logic.select_graspable). Vị trí platform lấy từ FK của /joint_states,
vị trí vật lấy từ OdometryPublisher của từng vật (pose thế giới).

Plugin DetachableJoint (gz-sim8) tự attach ngay khi mô phỏng khởi động, nên node gửi detach
cho mọi vật lúc bắt đầu cho tới khi nhận được trạng thái "detached".
"""

import threading
import time

from delta_controller.delta_kinematics import forward_kinematics, UnreachableError
from delta_controller.gripper_logic import (
    GraspTolerance,
    NoGraspableObject,
    ObjectState,
    select_graspable,
)
from delta_controller.scene import OBJECTS
from nav_msgs.msg import Odometry
import rclpy
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile
from sensor_msgs.msg import JointState
from std_msgs.msg import Empty, String
from std_srvs.srv import Trigger

ACTIVE_JOINTS = ('Chain1_1', 'Chain2_1', 'Chain3_1')
STATE_TIMEOUT_SEC = 2.0
STARTUP_RELEASE_TIMEOUT_SEC = 60.0


def gripper_topic(obj, leaf):
    """Topic riêng của từng vật — KHÔNG dùng topic mặc định của DetachableJoint mạch kín."""
    return f'/delta_3dof/gripper/{obj}/{leaf}'


class GripperNode(Node):
    """Quản lý trạng thái hút/nhả của các vật trong world."""

    def __init__(self):
        super().__init__('delta_gripper')
        names = self.declare_parameter('objects', [o.name for o in OBJECTS]).value
        half_heights = self.declare_parameter(
            'object_half_heights', [o.half_height for o in OBJECTS]).value
        if len(names) != len(half_heights):
            raise ValueError('objects va object_half_heights phai cung do dai')
        self._base_z = self.declare_parameter('base_z', 1.0).value
        self._tolerance = GraspTolerance(
            max_xy_offset=self.declare_parameter('max_xy_offset', 0.012).value,
            min_gap=self.declare_parameter('min_gap', -0.004).value,
            max_gap=self.declare_parameter('max_gap', 0.006).value,
        )

        self._half_heights = dict(zip(names, half_heights))
        self._lock = threading.Lock()
        self._joints = None
        self._object_centers = {}
        self._attach_state = {name: None for name in names}
        self._state_changed = threading.Condition(self._lock)
        self._held = None

        group = ReentrantCallbackGroup()
        self.create_subscription(JointState, '/joint_states', self._on_joints, 10,
                                 callback_group=group)
        self._attach_pubs = {}
        self._detach_pubs = {}
        for name in names:
            self.create_subscription(
                Odometry, f'/objects/{name}/odometry',
                lambda msg, n=name: self._on_odometry(n, msg), 10, callback_group=group)
            self.create_subscription(
                String, gripper_topic(name, 'state'),
                lambda msg, n=name: self._on_state(n, msg), 10, callback_group=group)
            self._attach_pubs[name] = self.create_publisher(
                Empty, gripper_topic(name, 'attach'), 10)
            self._detach_pubs[name] = self.create_publisher(
                Empty, gripper_topic(name, 'detach'), 10)

        latched = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self._held_pub = self.create_publisher(String, '/gripper/held_object', latched)
        self._publish_held()

        self.create_service(Trigger, '/gripper/grip', self._on_grip, callback_group=group)
        self.create_service(Trigger, '/gripper/release', self._on_release, callback_group=group)

        self._startup_deadline = time.monotonic() + STARTUP_RELEASE_TIMEOUT_SEC
        self._startup_timer = self.create_timer(0.5, self._release_all_on_startup,
                                                callback_group=group)

    # ------------------------------------------------------------------ callbacks

    def _on_joints(self, msg):
        positions = dict(zip(msg.name, msg.position))
        if all(n in positions for n in ACTIVE_JOINTS):
            with self._lock:
                self._joints = tuple(positions[n] for n in ACTIVE_JOINTS)

    def _on_odometry(self, name, msg):
        p = msg.pose.pose.position
        with self._lock:
            self._object_centers[name] = (p.x, p.y, p.z - self._base_z)

    def _on_state(self, name, msg):
        with self._state_changed:
            self._attach_state[name] = msg.data
            self._state_changed.notify_all()

    def _release_all_on_startup(self):
        """Gửi detach cho các vật chưa xác nhận 'detached' (plugin tự attach lúc khởi động)."""
        with self._lock:
            pending = [n for n, s in self._attach_state.items() if s != 'detached']
        if not pending:
            self.get_logger().info('Da nha tat ca vat luc khoi dong, giac hut san sang.')
            self._startup_timer.cancel()
            return
        if time.monotonic() > self._startup_deadline:
            self.get_logger().warning(
                f'Khong xac nhan duoc trang thai "detached" cua {pending} sau '
                f'{STARTUP_RELEASE_TIMEOUT_SEC:.0f}s (mo phong co dang chay voi '
                f'delta_objects_world khong?). Van tiep tuc.')
            self._startup_timer.cancel()
            return
        for name in pending:
            self._detach_pubs[name].publish(Empty())

    # ------------------------------------------------------------------ dịch vụ

    def _wait_for_state(self, name, expected):
        deadline = time.monotonic() + STATE_TIMEOUT_SEC
        with self._state_changed:
            while self._attach_state[name] != expected:
                remaining = deadline - time.monotonic()
                if remaining <= 0.0:
                    return False
                self._state_changed.wait(remaining)
            return True

    def _on_grip(self, request, response):
        with self._lock:
            held = self._held
            joints = self._joints
            objects = {
                n: ObjectState(c, self._half_heights[n]) for n, c in self._object_centers.items()
            }
            state = dict(self._attach_state)
        if held is not None:
            response.success, response.message = False, f'Dang giu {held}, hay release truoc'
            return response
        if joints is None:
            response.success, response.message = False, 'Chua nhan duoc /joint_states'
            return response
        try:
            tool = forward_kinematics(*joints)
            name = select_graspable(tool, objects, self._tolerance)
        except (NoGraspableObject, UnreachableError) as e:
            response.success, response.message = False, str(e)
            return response

        if state[name] == 'attached':
            # Có thể còn dính từ lúc khởi động -> nhả trước để attach lại ở vị trí hiện tại.
            self._detach_pubs[name].publish(Empty())
            self._wait_for_state(name, 'detached')
        self._attach_pubs[name].publish(Empty())
        if not self._wait_for_state(name, 'attached'):
            response.success = False
            response.message = f'Da gui attach {name} nhung Gazebo khong xac nhan'
            return response

        with self._lock:
            self._held = name
        self._publish_held()
        response.success, response.message = True, f'Da hut {name}'
        self.get_logger().info(response.message)
        return response

    def _on_release(self, request, response):
        with self._lock:
            held = self._held
        if held is None:
            response.success, response.message = False, 'Khong giu vat nao'
            return response
        self._detach_pubs[held].publish(Empty())
        if not self._wait_for_state(held, 'detached'):
            response.success = False
            response.message = f'Da gui detach {held} nhung Gazebo khong xac nhan'
            return response
        with self._lock:
            self._held = None
        self._publish_held()
        response.success, response.message = True, f'Da nha {held}'
        self.get_logger().info(response.message)
        return response

    def _publish_held(self):
        with self._lock:
            held = self._held
        self._held_pub.publish(String(data=held or ''))


def main(args=None):
    rclpy.init(args=args)
    node = GripperNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
