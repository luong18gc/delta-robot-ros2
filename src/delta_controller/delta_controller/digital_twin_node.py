"""
BẢN SAO SỐ (Bước 10b): lon THẬT trên bàn dịch đi -> lon ẢO trong Gazebo dịch theo.

    ros2 launch delta_controller digital_twin.launch.py

Vào : /vision/objects — vị trí lon trong hệ ẢO, do `real_vision` phát từ camera THẬT. Node này
      KHÔNG đọc camera và không biết gì về pixel; mọi chuyện thị giác đã xong ở tầng dưới.
Ra  : dịch vụ /world/delta_world/set_pose (Gazebo, qua ros_gz_bridge).

Đây là chỗ hai thế giới gặp nhau, và nó mỏng đúng như phải thế: khối thị giác đã phát tọa độ trong
hệ ẢO sẵn (xem scene.real_calib_markers_virtual — tọa độ ảo đi vào PnP ngay từ khâu hiệu chuẩn),
nên ở đây chỉ còn cộng thêm độ cao đế robot. Không có phép đổi tỉ lệ nào ở tầng này.

Bốn điều phải cẩn thận, đều học được từ các bước trước:

1. **Chỉ tin vật nhìn RÕ.** `score = 0` nghĩa là cờ tin cậy nói "có thể đang bị che" — dịch lon ảo
   theo một ước lượng như thế thì làm hỏng cả cảnh. Bỏ qua, giữ nguyên chỗ cũ.

2. **Đừng đánh nhau với vật lý.** `set_pose` là DỊCH CỨNG: gọi liên tục thì lon ảo không bao giờ
   được rơi, được va chạm, được nằm yên. Chỉ gọi khi lon thật đã dịch quá `MIN_MOVE`; dưới mức đó
   là nhiễu đo, để yên cho bộ giải vật lý.

3. **Đừng giật vật khỏi tay robot.** Lúc giác hút đang giữ lon, vị trí lon ảo do ROBOT quyết định,
   không phải camera. Camera cũng không nhìn thấy lon thật nào đang bay cả — lon thật vẫn nằm trên
   bàn. Bỏ qua lon đang bị giữ.

4. **Dịch vụ phải gọi BẤT ĐỒNG BỘ.** Gọi đồng bộ trong callback thì khóa chết executor: callback
   chờ phản hồi, mà phản hồi lại cần chính executor đó xử lý.
"""

from delta_controller.scene import OBJECTS, SCALE
from geometry_msgs.msg import Pose
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from ros_gz_interfaces.srv import SetEntityPose
from std_msgs.msg import String
from vision_msgs.msg import Detection3DArray

# base_link nằm ở world z = 1.0 (xem README của repo gốc); hệ robot = world − (0, 0, BASE_Z).
BASE_Z = 1.0
# Lon thật phải dịch quá bấy nhiêu mét ẢO thì mới dời lon ảo. 0.002 m ảo = 6 mm thật, rộng rãi so
# với nhiễu đo được của khối thị giác (0.5–0.9 mm thật, đo 2026-10-07).
MIN_MOVE = 0.002
DEFAULT_WORLD = 'delta_world'


class DigitalTwinNode(Node):
    """Chép vị trí lon thật sang lon ảo trong Gazebo."""

    def __init__(self):
        super().__init__('delta_digital_twin')
        world = self.declare_parameter('world', DEFAULT_WORLD).value
        self._min_move = float(self.declare_parameter('min_move', MIN_MOVE).value)
        self._known = {o.name for o in OBJECTS}

        self._client = self.create_client(SetEntityPose, f'/world/{world}/set_pose')
        self._placed = {}        # tên lon -> (x, y) ảo đã ra lệnh lần cuối
        self._held = ''
        self._pending = set()    # lon đang có lệnh chưa nhận phản hồi
        self._moves = 0

        self.create_subscription(Detection3DArray, '/vision/objects', self._on_objects, 10)
        self.create_subscription(String, '/gripper/held_object', self._on_held, 10)
        self.create_timer(10.0, self._report)

        self.get_logger().info(f'Cho dich vu /world/{world}/set_pose (ros_gz_bridge)...')
        if not self._client.wait_for_service(timeout_sec=20.0):
            raise SystemExit(
                f'Khong thay /world/{world}/set_pose. Co chay ros_gz_bridge voi '
                f'"/world/{world}/set_pose@ros_gz_interfaces/srv/SetEntityPose" khong?')
        self.get_logger().info(
            f'San sang. Lon that dich qua {1000 * SCALE * self._min_move:.0f} mm that '
            f'thi lon ao di theo.')

    def _on_held(self, msg):
        self._held = msg.data

    def _on_objects(self, msg):
        for det in msg.detections:
            name = det.id
            if name not in self._known or name == self._held:
                continue
            if not det.results or det.results[0].hypothesis.score <= 0.0:
                continue        # cờ tin cậy nói không nhìn rõ -> giữ nguyên chỗ cũ
            p = det.bbox.center.position
            before = self._placed.get(name)
            if before is not None and max(abs(p.x - before[0]), abs(p.y - before[1])) < \
                    self._min_move:
                continue        # nhiễu đo, không phải lon dịch -> để yên cho vật lý
            if name in self._pending:
                continue
            self._send(name, p.x, p.y, p.z)

    def _send(self, name, x, y, z):
        req = SetEntityPose.Request()
        req.entity.name = name
        req.entity.type = req.entity.MODEL
        req.pose = Pose()
        req.pose.position.x = float(x)
        req.pose.position.y = float(y)
        req.pose.position.z = float(z) + BASE_Z
        req.pose.orientation.w = 1.0
        self._pending.add(name)
        future = self._client.call_async(req)
        future.add_done_callback(lambda f, n=name, q=(x, y): self._done(f, n, q))

    def _done(self, future, name, xy):
        self._pending.discard(name)
        try:
            ok = future.result().success
        except Exception as err:                       # noqa: BLE001 — chỉ để ghi log
            self.get_logger().warning(f'{name}: goi set_pose that bai ({err})')
            return
        if ok:
            self._placed[name] = xy
            self._moves += 1
        else:
            self.get_logger().warning(f'{name}: Gazebo tu choi set_pose (co model nay khong?)')

    def _report(self):
        if self._moves:
            where = ', '.join(
                f'{n.split("_")[0]} ({1000 * SCALE * x:+.0f},{1000 * SCALE * y:+.0f})'
                for n, (x, y) in sorted(self._placed.items()))
            self.get_logger().info(f'{self._moves} lan doi cho / 10 s. Lon that (mm): {where}')
            self._moves = 0


def main(args=None):
    rclpy.init(args=args)
    node = DigitalTwinNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
