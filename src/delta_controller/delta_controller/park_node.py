"""
Đưa robot lên tư thế quan sát ngay khi mô phỏng khởi động, rồi tự thoát.

    ros2 run delta_controller park
    ros2 run delta_controller park --ros-args -p xyz:="[0.0, 0.0, -0.11]"

VÌ SAO CẦN: ở tư thế gốc, bàn máy nằm thấp (z = −140,5 mm) và CHE mất vật ở vùng xa trong tầm
nhìn camera — đo trước đây cho thấy một vật ở x = 120 mm bị che hoàn toàn, cờ tin cậy báo 0. Nâng
lên z = −110 mm thì thấy rõ cả ba vật. Trước đây việc nâng này chỉ xảy ra khi có lệnh gắp đầu
tiên, nên vừa mở mô phỏng là camera không thấy đủ vật và người dùng tưởng khâu nhận dạng hỏng.

VÌ SAO KHÔNG SỬA TƯ THẾ GỐC TRONG MÔ HÌNH: tư thế gốc là nơi hai khâu của mỗi mối hàn mạch kín
trùng khung tọa độ. Đổi nó đi thì các mối hàn bị giật hoặc hỏng ngay khi mô phỏng khởi động — xem
phần cơ cấu mạch kín. Nâng bằng LỆNH ĐIỀU KHIỂN thì không đụng gì tới mô hình.

Nút này chạy một lần rồi thoát, nên nó không giữ quyền điều khiển robot: mở `gui` hay
`cartesian_control` sau đó là chúng tiếp quản từ vị trí đo được.
"""

import sys
import threading
import time

from delta_controller.delta_kinematics import forward_kinematics, UnreachableError
from delta_controller.joint_commander import JointCommander
from delta_controller.scene import OBSERVE_XYZ
from delta_controller.trajectory import plan_path
import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from sensor_msgs.msg import JointState

ACTIVE_JOINTS = ('Chain1_1', 'Chain2_1', 'Chain3_1')
MAX_SPEED = 0.05           # m/s ảo
RATE_HZ = 50.0
JOINTS_WAIT_SEC = 20.0


class Park(Node):
    """Đi tới một tư thế rồi dừng."""

    def __init__(self):
        super().__init__('delta_park')
        xyz = self.declare_parameter('xyz', list(OBSERVE_XYZ)).value
        self._goal = (float(xyz[0]), float(xyz[1]), float(xyz[2]))
        self._speed = float(self.declare_parameter('max_speed', MAX_SPEED).value)
        self._measured = None
        self._lock = threading.Lock()
        self.create_subscription(JointState, '/joint_states', self._on_joints, 10)
        self._commander = JointCommander(self)

    def _on_joints(self, msg):
        pos = dict(zip(msg.name, msg.position))
        if all(j in pos for j in ACTIVE_JOINTS):
            with self._lock:
                self._measured = tuple(pos[j] for j in ACTIVE_JOINTS)

    def measured(self):
        with self._lock:
            return self._measured

    def go(self):
        """
        Chờ mô phỏng sẵn sàng rồi đi tới đích. Trả về True nếu đã đi.

        Chờ `/joint_states` chứ không chờ một khoảng thời gian cố định: thời gian khởi động của
        trình mô phỏng thay đổi theo tải máy, và một con số đoán được sẽ hoặc quá ngắn (lệnh gửi
        vào chỗ chưa ai nghe) hoặc quá dài một cách vô ích.
        """
        if not self._commander.wait_for_connection(timeout_sec=JOINTS_WAIT_SEC):
            self.get_logger().warning('Chua ket noi duoc cmd_pos — bo qua viec nang tu the.')
            return False
        deadline = time.monotonic() + JOINTS_WAIT_SEC
        while self.measured() is None:
            if time.monotonic() > deadline:
                self.get_logger().warning('Chua nhan duoc /joint_states — bo qua.')
                return False
            time.sleep(0.05)

        start = forward_kinematics(*self.measured())
        try:
            plan = plan_path([start, self._goal], self._speed, RATE_HZ)
        except UnreachableError as err:
            self.get_logger().error(f'Tu the dich ngoai tam voi: {err}')
            return False

        period = 1.0 / RATE_HZ
        next_time = time.monotonic()
        for _, thetas in plan:
            self._commander.send(*thetas)
            next_time += period
            time.sleep(max(0.0, next_time - time.monotonic()))
        self.get_logger().info(
            f'Da nang len tu the quan sat {tuple(round(1000 * g, 1) for g in self._goal)} mm — '
            f'camera nhin thay ca ba vat.')
        return True


def main(args=None):
    rclpy.init(args=args)
    node = Park()
    executor = SingleThreadedExecutor()
    executor.add_node(node)
    spin = threading.Thread(target=executor.spin, daemon=True)
    spin.start()
    try:
        node.go()
    finally:
        executor.shutdown()
        spin.join(timeout=2.0)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return 0


if __name__ == '__main__':
    sys.exit(main())
