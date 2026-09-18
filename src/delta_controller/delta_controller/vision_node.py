"""
Node nhận dạng vật theo màu từ ảnh camera (Bước 8.2).

Vào : ảnh camera (mặc định /side_camera/image).
Ra  : /vision/detections  (vision_msgs/Detection2DArray) — tọa độ PIXEL, chưa đổi sang hệ robot.
        Mỗi Detection2D: id = tên vật (theo scene.OBJECTS), bbox = khung bao phần nhìn thấy,
        results[0].pose.pose.position.(x, y) = tâm khối (u, v) của phần nhìn thấy.
      /vision/debug_image (sensor_msgs/Image, bgr8) — ảnh chú thích để xem bằng rqt_image_view.
"""

import time

from cv_bridge import CvBridge
from delta_controller.color_detector import detect_objects, draw_detections
from delta_controller.scene import OBJECTS
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2D, Detection2DArray, ObjectHypothesisWithPose

COLOR_TO_OBJECT = {o.color: o.name for o in OBJECTS}


class VisionNode(Node):
    """Nhận ảnh, nhận dạng theo màu, phát kết quả và ảnh chú thích."""

    def __init__(self):
        super().__init__('delta_vision')
        image_topic = self.declare_parameter('image_topic', '/side_camera/image').value
        self._bridge = CvBridge()
        self._det_pub = self.create_publisher(Detection2DArray, '/vision/detections', 10)
        self._debug_pub = self.create_publisher(Image, '/vision/debug_image', 10)
        self.create_subscription(Image, image_topic, self._on_image, qos_profile_sensor_data)
        self._last_seen = None
        self._frames = 0
        self._busy_sec = 0.0
        self.create_timer(10.0, self._report)
        self.get_logger().info(f'Dang nhan anh tu {image_topic}')

    def _on_image(self, msg):
        start = time.perf_counter()
        bgr = self._bridge.imgmsg_to_cv2(msg, 'bgr8')
        detections = detect_objects(bgr)

        out = Detection2DArray()
        out.header = msg.header
        for color, det in detections.items():
            d = Detection2D()
            d.header = msg.header
            d.id = COLOR_TO_OBJECT.get(color, color)
            x, y, w, h = det.bbox
            d.bbox.center.position.x = x + w / 2.0
            d.bbox.center.position.y = y + h / 2.0
            d.bbox.size_x = float(w)
            d.bbox.size_y = float(h)
            hyp = ObjectHypothesisWithPose()
            hyp.hypothesis.class_id = d.id
            hyp.hypothesis.score = 1.0
            hyp.pose.pose.position.x = det.centroid[0]
            hyp.pose.pose.position.y = det.centroid[1]
            d.results.append(hyp)
            out.detections.append(d)
        self._det_pub.publish(out)

        if self._debug_pub.get_subscription_count() > 0:
            debug = draw_detections(bgr, detections, labels=COLOR_TO_OBJECT)
            debug_msg = self._bridge.cv2_to_imgmsg(debug, 'bgr8')
            debug_msg.header = msg.header
            self._debug_pub.publish(debug_msg)

        seen = sorted(COLOR_TO_OBJECT.get(c, c) for c in detections)
        if seen != self._last_seen:
            self.get_logger().info(f'Thay {len(seen)} vat: {", ".join(seen) or "(khong co)"}')
            self._last_seen = seen
        self._frames += 1
        self._busy_sec += time.perf_counter() - start

    def _report(self):
        if self._frames:
            self.get_logger().info(
                f'{self._frames / 10.0:.1f} anh/s, xu ly trung binh '
                f'{1000.0 * self._busy_sec / self._frames:.1f} ms/anh')
        self._frames = 0
        self._busy_sec = 0.0


def main(args=None):
    rclpy.init(args=args)
    node = VisionNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
