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

5. **Nhảy xa phải có nhiều khung xác nhận.** Cờ tin cậy KHÔNG bắt được vị trí sai, và đây là tính
   chất cấu trúc chứ không phải ngưỡng đặt chưa khéo: `estimate_object` ước lượng vị trí TRƯỚC rồi
   mới dựng hình bóng dự đoán TẠI CHÍNH vị trí đó. Vùng ảnh to hơn thì phép khớp đẩy vật lại gần
   camera hơn, mà ở gần thì hình bóng dự đoán CŨNG to hơn — tỉ lệ tự chuẩn hóa về ~1. Nó chỉ bắt
   được CHE KHUẤT (méo hình dáng mà phép khớp không bù được).
   Ràng buộc không tự chuẩn hóa duy nhất là VẬT LÝ: lon không dịch 284 mm trong 1/10 giây. Gặp thật
   2026-10-07: bàn tay với vào dời lon rơi vào lớp màu của Coca, lon ảo nhảy 284 mm rồi quay về,
   score vẫn 1.00. Nhấc lon đặt chỗ khác thì chỗ mới TRỤ LẠI, còn nhiễu thì không.
"""

import math

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
# Dịch quá bấy nhiêu mét ẢO trong MỘT lần đo thì phải có `CONFIRM_FRAMES` khung liên tiếp xác nhận
# mới ghi vào Gazebo. 0.02 m ảo = 60 mm thật; ở 10 Hz tức 0.6 m/s — nhanh hơn mức đó thì không phải
# lon trượt trên bàn nữa.
JUMP = 0.02
CONFIRM_FRAMES = 5
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
        self._candidate = {}     # tên lon -> ((x, y) chỗ mới đang chờ, số khung đã xác nhận)
        self._held = ''
        self._pending = set()    # lon đang có lệnh chưa nhận phản hồi
        self._moves = self._rejected = 0

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
            if before is not None:
                moved = math.hypot(p.x - before[0], p.y - before[1])
                if moved < self._min_move:
                    self._candidate.pop(name, None)
                    continue    # nhiễu đo, không phải lon dịch -> để yên cho vật lý
                if moved >= JUMP and not self._confirmed(name, p.x, p.y):
                    continue    # nhảy xa chưa đủ khung xác nhận -> giữ nguyên chỗ cũ
            self._candidate.pop(name, None)
            if name in self._pending:
                continue
            self._send(name, p.x, p.y, p.z)

    def _confirmed(self, name, x, y):
        """Chỗ mới đã trụ lại đủ `CONFIRM_FRAMES` khung liên tiếp chưa."""
        where, count = self._candidate.get(name, (None, 0))
        if where is None or math.hypot(x - where[0], y - where[1]) > self._min_move:
            self._candidate[name] = ((x, y), 1)     # chỗ mới khác hẳn -> đếm lại từ đầu
            self._rejected += 1
            return False
        count += 1
        self._candidate[name] = ((x, y), count)
        if count < CONFIRM_FRAMES:
            self._rejected += 1
            return False
        return True

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
        if self._moves or self._rejected:
            where = ', '.join(
                f'{n.split("_")[0]} ({1000 * SCALE * x:+.0f},{1000 * SCALE * y:+.0f})'
                for n, (x, y) in sorted(self._placed.items()))
            extra = f', bo {self._rejected} khung nhay xa chua xac nhan' if self._rejected else ''
            self.get_logger().info(
                f'{self._moves} lan doi cho / 10 s{extra}. Lon that (mm): {where}')
        self._moves = self._rejected = 0


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
