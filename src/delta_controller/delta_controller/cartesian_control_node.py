"""
Node tương tác điều khiển robot delta theo tọa độ Descartes (x, y, z).

Nhập vị trí tâm platform [m] -> sinh quỹ đạo -> giải IK từng điểm -> gửi góc khớp qua
JointCommander. Điểm xuất phát lấy từ FK của góc khớp đo trên /joint_states.
"""

import math
import threading
import time

from delta_controller.delta_kinematics import (
    forward_kinematics,
    inverse_kinematics,
    UnreachableError,
)
from delta_controller.joint_commander import JointCommander
from delta_controller.trajectory import plan_path, safe_waypoints
import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile
from rclpy.signals import SignalHandlerOptions
from sensor_msgs.msg import JointState
from std_msgs.msg import String
from std_srvs.srv import Trigger


HOME_XYZ = (0.0, 0.0, -0.1405)
ACTIVE_JOINTS = ('Chain1_1', 'Chain2_1', 'Chain3_1')

HELP_TEXT = """
Nhap toa do tam platform (met). He truc: goc tai tam de, X huong ra chan 1, Z huong len (z am).

Lenh di chuyen:
  x y z           -> di THANG toi (x, y, z), khoi dong/dung em
  safe x y z      -> nang len do cao an toan -> di ngang -> ha xuong (tranh quet trung vat)
  jump x y z      -> gui thang goc khop (khong noi suy, nhu ban cu - de so sanh)
  home            -> ve (0, 0, -0.1405) theo duong an toan

Giac hut (can: ros2 launch delta_controller pick_place.launch.py):
  grip            -> hut vat ngay duoi platform (platform phai cham dinh vat)
  release         -> nha vat dang giu
  Khi dang giu vat, duong 'safe' tu nang len safe_z_holding de vat khong quet trung vat khac.

Lenh khac:
  where           -> vi tri platform hien tai (FK tu goc khop do duoc)
  state           -> goc khop do duoc va sai lech so voi lenh cuoi
  speed v         -> dat van toc dinh v (m/s), vd: speed 0.05
  help            -> hien lai huong dan nay
  q / quit / exit -> thoat (Ctrl+C khi dang chay -> dung quy dao)

Vi du: 0 0 -0.15    safe 0.06 0 -0.185    speed 0.03
"""


def parse_xyz(raw: str):
    """Tách chuỗi nhập thành (x, y, z)."""
    parts = raw.replace(',', ' ').split()
    if len(parts) != 3:
        raise ValueError('Can nhap dung 3 gia tri x y z, vi du: 0 0 -0.15')
    return tuple(float(p) for p in parts)


class CartesianController(Node):
    """Nhận tọa độ platform, sinh quỹ đạo, giải IK và publish lệnh góc khớp."""

    def __init__(self):
        super().__init__('delta_cartesian_control')
        self.max_speed = self.declare_parameter('max_speed', 0.05).value
        self.rate_hz = self.declare_parameter('rate_hz', 50.0).value
        self.safe_z = self.declare_parameter('safe_z', -0.16).value
        # Khi mang vật cao 3 cm: đáy vật = tool0 - 0.033 phải cao hơn đỉnh vật khác (-0.19)
        # và thành khay (-0.20) -> tool0 >= -0.147; chọn -0.14 để dư ~7 mm.
        self.safe_z_holding = self.declare_parameter('safe_z_holding', -0.14).value

        self._commander = JointCommander(self)
        self._lock = threading.Lock()
        self._measured = None
        self._last_command = None
        self._held_object = ''
        self.create_subscription(JointState, '/joint_states', self._on_joint_state, 10)
        latched = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.create_subscription(String, '/gripper/held_object', self._on_held, latched)
        self._grip_client = self.create_client(Trigger, '/gripper/grip')
        self._release_client = self.create_client(Trigger, '/gripper/release')

    def _on_joint_state(self, msg):
        positions = dict(zip(msg.name, msg.position))
        if all(name in positions for name in ACTIVE_JOINTS):
            with self._lock:
                self._measured = tuple(positions[name] for name in ACTIVE_JOINTS)

    def _on_held(self, msg):
        with self._lock:
            self._held_object = msg.data

    @property
    def held_object(self):
        with self._lock:
            return self._held_object

    def wait_for_connection(self, timeout_sec=5.0):
        """Chờ bridge subscribe cmd_pos VÀ nhận /joint_states đầu tiên (cần cho FK điểm đầu)."""
        deadline = time.monotonic() + timeout_sec
        if not self._commander.wait_for_connection(timeout_sec):
            return False
        while self.measured() is None:
            if time.monotonic() > deadline:
                return False
            time.sleep(0.05)
        return True

    def call_gripper(self, release, timeout_sec=5.0):
        """Gọi dịch vụ grip/release, trả về (success, message)."""
        client = self._release_client if release else self._grip_client
        if not client.wait_for_service(timeout_sec=1.0):
            return False, ('Khong thay dich vu giac hut - hay chay: '
                           'ros2 launch delta_controller pick_place.launch.py')
        done = threading.Event()
        future = client.call_async(Trigger.Request())
        future.add_done_callback(lambda _: done.set())
        if not done.wait(timeout_sec):
            return False, 'Dich vu giac hut khong tra loi'
        result = future.result()
        return result.success, result.message

    def measured(self):
        with self._lock:
            return self._measured

    @property
    def last_command(self):
        return self._last_command

    def current_position(self):
        """Vị trí platform hiện tại theo FK của góc khớp đo được; None nếu chưa có dữ liệu."""
        measured = self.measured()
        if measured is None:
            return None
        return forward_kinematics(*measured)

    def _send(self, thetas):
        self._commander.send(*thetas)
        self._last_command = thetas

    def jump_to(self, x, y, z):
        """Gửi thẳng góc khớp đích, không nội suy."""
        thetas = inverse_kinematics(x, y, z)
        self._send(thetas)
        return thetas

    def move(self, goal, safe):
        """
        Đi tới goal theo đường thẳng (safe=False) hoặc nâng-ngang-hạ (safe=True).

        Lập kế hoạch và giải IK cho toàn bộ quỹ đạo trước; ném UnreachableError nếu có điểm
        ngoài tầm với (robot chưa di chuyển). Trả về (số điểm, thời gian dự kiến [s]).
        """
        start = self.current_position()
        if start is None:
            raise RuntimeError('Chua nhan duoc /joint_states nen chua biet vi tri xuat phat')
        safe_z = self.safe_z_holding if self.held_object else self.safe_z
        waypoints = safe_waypoints(start, goal, safe_z) if safe else [start, goal]
        plan = plan_path(waypoints, self.max_speed, self.rate_hz)

        period = 1.0 / self.rate_hz
        next_time = time.monotonic()
        for _, thetas in plan:
            self._send(thetas)
            next_time += period
            time.sleep(max(0.0, next_time - time.monotonic()))
        return waypoints, len(plan), len(plan) * period


def _format_angles(thetas):
    return ', '.join(f'{t:+.4f} rad ({math.degrees(t):+.1f}°)' for t in thetas)


def _format_xyz(p):
    return f'({p[0]:+.4f}, {p[1]:+.4f}, {p[2]:+.4f})'


def _handle(node, raw):
    """Xử lý một dòng lệnh. Trả về False nếu người dùng muốn thoát."""
    command, _, rest = raw.partition(' ')
    command = command.lower()

    if command in ('q', 'quit', 'exit'):
        return False
    if command == 'help':
        print(HELP_TEXT)
        return True
    if command == 'state':
        measured = node.measured()
        if measured is None:
            print('Chua nhan duoc /joint_states (mo phong da chay chua?)')
            return True
        print(f'-> Do duoc:  {_format_angles(measured)}')
        if node.last_command is not None:
            errors = [m - c for m, c in zip(measured, node.last_command)]
            print(f'-> Sai lech: {", ".join(f"{e:+.4f}" for e in errors)} rad')
        return True
    if command == 'where':
        p = node.current_position()
        if p is None:
            print('Chua nhan duoc /joint_states')
        else:
            print(f'-> Platform tai {_format_xyz(p)} m')
        return True
    if command in ('grip', 'release'):
        success, message = node.call_gripper(release=(command == 'release'))
        print(f'-> {message}' if success else f'Loi: {message}')
        return True
    if command == 'speed':
        speed = float(rest)
        if speed <= 0.0:
            raise ValueError('Van toc phai > 0')
        node.max_speed = speed
        print(f'-> Van toc dinh = {speed} m/s')
        return True

    if command == 'home':
        goal, mode = HOME_XYZ, 'safe'
    elif command in ('safe', 'jump'):
        goal, mode = parse_xyz(rest), command
    else:
        goal, mode = parse_xyz(raw), 'line'

    if mode == 'jump':
        thetas = node.jump_to(*goal)
        print(f'-> Nhay toi {_format_xyz(goal)}, goc khop: {_format_angles(thetas)}')
        return True

    waypoints, n_points, duration = node.move(goal, safe=(mode == 'safe'))
    route = ' -> '.join(_format_xyz(p) for p in waypoints)
    print(f'-> Da di {n_points} diem trong ~{duration:.1f}s: {route}')
    return True


def main(args=None):
    # Tắt signal handler của rclpy (nó shutdown context khi Ctrl+C) để Ctrl+C chỉ dừng quỹ đạo.
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    node = CartesianController()

    # input() và vòng chạy quỹ đạo chặn luồng chính, nên spin ở luồng phụ để callback
    # /joint_states vẫn chạy.
    executor = SingleThreadedExecutor()
    executor.add_node(node)
    spin_thread = threading.Thread(target=executor.spin, daemon=True)
    spin_thread.start()

    print('Dang cho ket noi toi mo phong...')
    if node.wait_for_connection():
        print('Da ket noi.')
    else:
        print('Canh bao: sau 5s chua ket noi duoc mo phong (cmd_pos / joint_states)')

    print(HELP_TEXT)
    try:
        while rclpy.ok():
            try:
                raw = input('Nhap lenh > ').strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not raw:
                continue
            try:
                if not _handle(node, raw):
                    break
            except UnreachableError as e:
                print(f'Khong toi duoc: {e}')
            except (ValueError, RuntimeError) as e:
                print(f'Loi: {e}')
            except KeyboardInterrupt:
                print('\n-> Da dung quy dao (robot giu diem lenh cuoi).')
    finally:
        # Dừng executor và CHỜ luồng spin kết thúc trước khi hủy node, nếu không có thể
        # "terminate called without an active exception" (đã gặp khi thoát bằng EOF).
        executor.shutdown()
        spin_thread.join(timeout=2.0)
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
