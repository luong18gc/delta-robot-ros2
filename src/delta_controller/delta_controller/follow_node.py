"""
BÁM THEO LON (Bước 11): lon THẬT dịch trên bàn -> robot đuổi theo, giữ đầu hút ngay trên đỉnh lon.

    ros2 run delta_controller follow                         # bám lon VỪA DỊCH
    ros2 run delta_controller follow --ros-args -p object:=coca_can    # chỉ bám một lon
    ros2 topic pub -1 /follow/target std_msgs/msg/String "{data: pepsi_can}"   # đổi lúc đang chạy

Chạy kèm `digital_twin.launch.py` (mô phỏng + camera thật + bản sao số).

**Bám lon ẢO chứ không bám thẳng kết quả camera**, và đó là lựa chọn có chủ ý: lon ảo đã qua bộ lọc
của `digital_twin` (bỏ ước lượng không tin cậy, đòi 5 khung xác nhận cho mỗi cú nhảy xa), nên robot
không bao giờ lao theo một khung hình nhiễu. Chuỗi đầy đủ là

    lon thật -> camera -> real_vision -> digital_twin -> lon ảo -> node này -> robot

tức đúng vòng kín mà đồ án muốn chứng minh: thế giới thật điều khiển robot qua bản sao số.

**Vì sao là vòng servo chứ không phải quỹ đạo điểm-tới-điểm.** `cartesian_control` lập trọn quỹ
đạo rồi mới chạy — đúng cho lệnh "đi tới đó", sai cho bám đuổi: đích đổi ngay trong lúc đang đi.
Ở đây mỗi nhịp chỉ kéo vị trí lệnh về phía đích một đoạn ngắn, giới hạn bởi `max_speed`. Giới hạn
tốc độ chính là thứ làm mượt: camera 10 Hz, vòng điều khiển 50 Hz, nên một bước nhảy của ước lượng
được rải ra thành nhiều nhịp nhỏ thay vì giật một cái.

**Mặc định bám lon VỪA DỊCH.** Đặt một lon cố định làm đích thì phải tắt node mới đổi được, trong
khi việc tự nhiên khi trình diễn là đẩy bất kỳ lon nào và robot đi theo. Node theo dõi cả ba lon;
lon nào dịch quá `SWITCH_MOVE` thì thành đích mới, và giữ đích đó cho tới khi có lon khác dịch.

⚠️ Node KHÔNG gắp, chỉ giữ đầu hút lơ lửng trên đỉnh lon. Muốn gắp thì dùng `cartesian_control`.
"""

import math
import threading

from delta_controller.delta_kinematics import forward_kinematics, inverse_kinematics
from delta_controller.joint_commander import JointCommander
from delta_controller.scene import OBJECTS, SCALE, TABLE_Z
from nav_msgs.msg import Odometry
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import String

BASE_Z = 1.0
# Khe giữa MẶT DƯỚI platform và đỉnh lon (m ảo). Platform dày 6 mm nên tâm tool0 cao hơn đỉnh lon
# đúng 0.003 + khe này. 0.02 m ảo = 60 mm thật — nhìn rõ là robot đang bám chứ không chạm vào lon.
HOVER = 0.02
PLATFORM_HALF_THICKNESS = 0.003
# Đích lệch dưới mức này thì đứng yên: không có vòng servo nào nên rung quanh đích vì nhiễu đo.
DEADBAND = 0.0015
# Không nhận được vị trí lon quá lâu thì dừng tại chỗ thay vì bám theo số liệu cũ.
STALE_SEC = 2.0
# Ở chế độ tự chọn, lon phải dịch quá bấy nhiêu mét ảo thì mới giành quyền làm đích. 0.01 m ảo =
# 30 mm thật — đủ lớn so với nhiễu đo (0,5–0,9 mm) để robot không nhảy qua lại giữa các lon.
SWITCH_MOVE = 0.01
AUTO = 'auto'


class FollowNode(Node):
    """Giữ đầu hút ngay trên đỉnh một lon, đuổi theo khi lon dịch."""

    def __init__(self):
        super().__init__('delta_follow')
        name = self.declare_parameter('object', AUTO).value
        self._max_speed = float(self.declare_parameter('max_speed', 0.05).value)
        self._rate = float(self.declare_parameter('rate_hz', 50.0).value)
        self._hover = float(self.declare_parameter('hover', HOVER).value)

        objects = {o.name: o for o in OBJECTS}
        if name != AUTO and name not in objects:
            raise SystemExit(
                f'Khong co vat ten "{name}". Co: {AUTO}, {", ".join(sorted(objects))}')
        self._objects = objects
        self._auto = name == AUTO
        # Mọi lon cùng kích thước nên cao độ bám như nhau; lấy lon bất kỳ để tính.
        self._obj = objects[next(iter(objects))] if self._auto else objects[name]
        self._name = None if self._auto else name
        self._resting = {}        # tên lon -> (x, y) chỗ nó đứng yên lần cuối
        # Đỉnh lon = mặt bàn + chiều cao lon; tâm tool0 phải cao hơn đỉnh đúng nửa bề dày platform.
        self._z = (TABLE_Z + 2 * self._obj.half_height
                   + PLATFORM_HALF_THICKNESS + self._hover)

        self._commander = JointCommander(self)
        self._target = None          # (x, y) ảo, chỗ lon đang đứng
        self._target_at = None       # thời điểm nhận, để biết số liệu có cũ quá không
        self._here = None            # vị trí lệnh hiện tại (x, y, z): điểm đang kéo robot tới
        self._joints = None
        self._lock = threading.Lock()
        self._warned_reach = False

        self.create_subscription(JointState, '/joint_states', self._on_joints, 10)
        for each in objects:
            self.create_subscription(Odometry, f'/objects/{each}/odometry',
                                     self._make_object(each), 10)
        self.create_subscription(String, '/follow/target', self._on_target, 10)
        self.create_timer(1.0 / self._rate, self._tick)
        self.create_timer(5.0, self._report)
        self.get_logger().info(
            f'Bam {"lon VUA DICH" if self._auto else name}: giu tool0 o z = {self._z:.4f} m ao '
            f'(khe {1000 * SCALE * self._hover:.0f} mm that tren dinh lon), '
            f'toc do toi da {self._max_speed:.3f} m/s ao.')

    # ------------------------------------------------------------------ nhận tin

    def _on_joints(self, msg):
        if len(msg.position) >= 3:
            self._joints = tuple(msg.position[:3])

    def _make_object(self, name):
        def callback(msg):
            p = msg.pose.pose.position
            here = (p.x, p.y)
            with self._lock:
                if self._auto:
                    was = self._resting.get(name)
                    if was is None:
                        self._resting[name] = here
                    elif math.hypot(here[0] - was[0], here[1] - was[1]) >= SWITCH_MOVE:
                        self._resting[name] = here
                        if self._name != name:
                            self._name = name
                            self.get_logger().info(f'Doi sang bam {name} (vua dich).')
                if name != self._name:
                    return
                self._target = here
                self._target_at = self.get_clock().now().nanoseconds * 1e-9
        return callback

    def _on_target(self, msg):
        name = msg.data.strip()
        if name == AUTO:
            with self._lock:
                self._auto, self._name = True, None
            self.get_logger().info('Chuyen sang bam lon VUA DICH.')
            return
        if name not in self._objects:
            self.get_logger().warning(f'Khong co vat ten "{name}".')
            return
        with self._lock:
            self._auto, self._name, self._target = False, name, None
        self.get_logger().info(f'Doi sang bam {name}.')

    # ------------------------------------------------------------------ vòng điều khiển

    def _tick(self):
        with self._lock:
            target, seen_at = self._target, self._target_at
        if target is None or self._joints is None:
            return
        now = self.get_clock().now().nanoseconds * 1e-9
        if seen_at is not None and now - seen_at > STALE_SEC:
            return                      # mất dấu lon -> đứng yên, không bám số liệu cũ

        if self._here is None:
            # Xuất phát từ vị trí ĐO ĐƯỢC, không phải lệnh cuối: robot có thể đang ở đâu đó khác.
            self._here = forward_kinematics(*self._joints)

        dx, dy = target[0] - self._here[0], target[1] - self._here[1]
        dz = self._z - self._here[2]
        dist = math.sqrt(dx * dx + dy * dy + dz * dz)
        if dist < DEADBAND:
            return
        step = min(self._max_speed / self._rate, dist)
        k = step / dist
        goal = (self._here[0] + k * dx, self._here[1] + k * dy, self._here[2] + k * dz)

        try:
            angles = inverse_kinematics(*goal)
        except ValueError:
            # Ngoài tầm với: đứng yên tại chỗ hợp lệ gần nhất thay vì nhích tiếp rồi hỏng.
            if not self._warned_reach:
                self.get_logger().warning(
                    f'Lon o ({1000 * SCALE * target[0]:+.0f},{1000 * SCALE * target[1]:+.0f}) mm '
                    f'that — ngoai tam voi, dung lai cho nay.')
                self._warned_reach = True
            return
        self._warned_reach = False
        self._here = goal
        self._commander.send(*angles)

    def _report(self):
        with self._lock:
            target = self._target
        if target is None or self._here is None:
            return
        off = 1000 * SCALE * math.hypot(target[0] - self._here[0], target[1] - self._here[1])
        self.get_logger().info(
            f'dau hut ({1000 * SCALE * self._here[0]:+.0f},{1000 * SCALE * self._here[1]:+.0f}) '
            f'| {self._name or "(chua co dich)"} '
            f'({1000 * SCALE * target[0]:+.0f},{1000 * SCALE * target[1]:+.0f}) '
            f'| con cach {off:.0f} mm that')


def main(args=None):
    rclpy.init(args=args)
    node = FollowNode()
    if not node._commander.wait_for_connection():
        node.get_logger().warning('Chua ket noi duoc cmd_pos — mo phong da chay chua?')
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
