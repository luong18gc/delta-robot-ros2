"""
Node điều khiển BĂNG TẢI thật qua cổng serial (Bước 10d).

    ros2 run delta_controller conveyor
    ros2 run delta_controller conveyor --ros-args -p port:=/dev/ttyUSB0 -p speed:=180

Dịch vụ : /conveyor/run, /conveyor/stop (std_srvs/Trigger)
Topic ra: /conveyor/running (std_msgs/Bool, latched)

**Lệnh "chạy" là lời khẳng định phải nhắc lại, không phải công tắc bật-và-quên.** Node gửi `R` lại
mỗi `HEARTBEAT_SEC`; Arduino tự dừng băng nếu quá 3 giây không nhận. Nhờ vậy node chết, cáp USB
tuột hay máy treo đều làm băng DỪNG chứ không chạy mãi. Đây là lưới an toàn rẻ nhất cho một thứ
chuyển động điều khiển từ xa — không cần nút dừng khẩn, không cần cảm biến.

⚠️ Người dùng phải thuộc nhóm `dialout` mới mở được cổng serial:
    sudo usermod -aG dialout $USER     (rồi đăng xuất, đăng nhập lại)
"""

import glob
import threading

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile
import serial
from std_msgs.msg import Bool
from std_srvs.srv import Trigger

BAUD = 115200
HEARTBEAT_SEC = 0.5        # nhắc lại "R"; Arduino hết hạn sau 3 s nên dư gấp 6 lần
PORT_PATTERNS = ('/dev/ttyUSB*', '/dev/ttyACM*')


def find_port():
    """Cổng serial đầu tiên trông giống Arduino; None nếu không có."""
    for pattern in PORT_PATTERNS:
        found = sorted(glob.glob(pattern))
        if found:
            return found[0]
    return None


class ConveyorNode(Node):
    """Băng tải: chạy, dừng, đặt tốc độ."""

    def __init__(self):
        super().__init__('delta_conveyor')
        port = self.declare_parameter('port', 'auto').value
        speed = int(self.declare_parameter('speed', 180).value)
        self._heartbeat = float(self.declare_parameter('heartbeat_sec', HEARTBEAT_SEC).value)

        if port == 'auto':
            port = find_port()
            if port is None:
                raise SystemExit(
                    'Khong tim thay cong serial nao (/dev/ttyUSB*, /dev/ttyACM*). '
                    'Da cam Arduino chua? Hoac truyen -p port:=/dev/ttyXXX')
        try:
            self._serial = serial.Serial(port, BAUD, timeout=0.3)
        except serial.SerialException as err:
            raise SystemExit(
                f'Khong mo duoc {port}: {err}\n'
                f'Neu bao "Permission denied" thi chay: sudo usermod -aG dialout $USER '
                f'roi dang xuat va dang nhap lai.')
        self._lock = threading.Lock()
        self._want_run = False
        # Arduino tự khởi động lại khi mở cổng serial (DTR) — chờ nó xong rồi mới nói chuyện.
        self.create_timer(2.0, self._announce_once)
        self._ready = False

        latched = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self._state_pub = self.create_publisher(Bool, '/conveyor/running', latched)
        self.create_service(Trigger, '/conveyor/run', self._on_run)
        self.create_service(Trigger, '/conveyor/stop', self._on_stop)
        self.create_timer(self._heartbeat, self._tick)
        self._port, self._speed = port, speed
        self.get_logger().info(f'Cong {port}, dang cho Arduino khoi dong lai...')

    # ------------------------------------------------------------------ serial

    def _send(self, line):
        """Gửi một lệnh, trả về dòng trả lời (chuỗi rỗng nếu không có)."""
        with self._lock:
            try:
                self._serial.reset_input_buffer()
                self._serial.write((line + '\n').encode())
                return self._serial.readline().decode(errors='replace').strip()
            except serial.SerialException as err:
                self.get_logger().error(f'Loi serial: {err}')
                return ''

    def _announce_once(self):
        if self._ready:
            return
        self._ready = True
        reply = self._send(f'V{self._speed}')
        self.get_logger().info(
            f'San sang. Toc do PWM {self._speed} (tra loi: "{reply}"). '
            f'Bang chi chay khi co lenh /conveyor/run va se tu dung neu node nay chet.')
        self._publish()

    # ------------------------------------------------------------------ dịch vụ

    def _on_run(self, request, response):
        self._want_run = True
        self._send('R')
        self._publish()
        response.success = True
        response.message = 'Bang dang chay'
        self.get_logger().info(response.message)
        return response

    def _on_stop(self, request, response):
        self._want_run = False
        self._send('S')
        self._publish()
        response.success = True
        response.message = 'Bang da dung'
        self.get_logger().info(response.message)
        return response

    def _publish(self):
        msg = Bool()
        msg.data = self._want_run
        self._state_pub.publish(msg)

    def _tick(self):
        """Nhắc lại lời khẳng định "chạy". Không chạy thì không gửi gì — im lặng là dừng."""
        if self._ready and self._want_run:
            self._send('R')

    def destroy_node(self):
        if getattr(self, '_serial', None) is not None:
            try:
                self._send('S')
                self._serial.close()
            except Exception:                      # noqa: BLE001 — đang tắt, không cứu được gì
                pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = ConveyorNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
