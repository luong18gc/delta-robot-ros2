"""
Node nhận dạng vật theo màu từ ảnh camera (Bước 8.2) và đổi ra tọa độ robot (Bước 8.3).

Vào : ảnh camera (mặc định /side_camera/image); file hiệu chuẩn (tham số calibration_file,
      tạo bằng `ros2 run delta_controller calibrate_camera`).
Ra  : /vision/detections  (vision_msgs/Detection2DArray) — tọa độ PIXEL.
        Mỗi Detection2D: id = tên vật (theo scene.OBJECTS), bbox = khung bao phần nhìn thấy,
        results[0].pose.pose.position.(x, y) = tâm khối (u, v) của phần nhìn thấy.
      /vision/objects (vision_msgs/Detection3DArray, frame base_link) — tọa độ ROBOT (m), chỉ khi
        có file hiệu chuẩn: tia nhìn qua tâm khối giao với mặt phẳng z = mặt bàn + nửa chiều cao
        vật (vật nằm trên bàn). id và class_id = tên vật; bbox.center.position = tâm vật ước lượng.
      /vision/debug_image (sensor_msgs/Image, bgr8) — ảnh chú thích để xem bằng rqt_image_view.
"""

import os
import time

from cv_bridge import CvBridge
from delta_controller.calibrate_camera_node import DEFAULT_OUTPUT as DEFAULT_CALIBRATION
from delta_controller.camera_model import CameraModel
from delta_controller.color_detector import detect_objects, draw_detections
from delta_controller.scene import OBJECTS, TABLE_Z
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from vision_msgs.msg import (
    Detection2D,
    Detection2DArray,
    Detection3D,
    Detection3DArray,
    ObjectHypothesisWithPose,
)
import yaml

COLOR_TO_OBJECT = {o.color: o.name for o in OBJECTS}
CENTER_Z = {o.color: TABLE_Z + o.half_height for o in OBJECTS}   # độ cao tâm vật nằm trên bàn


class VisionNode(Node):
    """Nhận ảnh, nhận dạng theo màu, phát kết quả và ảnh chú thích."""

    def __init__(self):
        super().__init__('delta_vision')
        image_topic = self.declare_parameter('image_topic', '/side_camera/image').value
        calibration = os.path.expanduser(
            self.declare_parameter('calibration_file', DEFAULT_CALIBRATION).value)
        self._camera = self._load_calibration(calibration)
        self._bridge = CvBridge()
        self._det_pub = self.create_publisher(Detection2DArray, '/vision/detections', 10)
        self._obj_pub = self.create_publisher(Detection3DArray, '/vision/objects', 10)
        self._debug_pub = self.create_publisher(Image, '/vision/debug_image', 10)
        self.create_subscription(Image, image_topic, self._on_image, qos_profile_sensor_data)
        self._last_seen = None
        self._frames = 0
        self._busy_sec = 0.0
        self.create_timer(10.0, self._report)
        self.get_logger().info(f'Dang nhan anh tu {image_topic}')

    def _load_calibration(self, path):
        if not os.path.exists(path):
            self.get_logger().warning(
                f'Chua co file hieu chuan {path} -> chi phat toa do pixel. '
                'Chay: ros2 run delta_controller calibrate_camera')
            return None
        with open(path) as f:
            camera = CameraModel.from_dict(yaml.safe_load(f)['camera'])
        x, y, z = camera.position()
        self.get_logger().info(
            f'Da nap hieu chuan {path}: camera tai ({x:+.3f}, {y:+.3f}, {z:+.3f}) m (he robot)')
        return camera

    def _robot_positions(self, detections):
        """Tâm khối pixel -> tọa độ robot (m) trên mặt phẳng độ cao tâm vật."""
        if self._camera is None:
            return {}
        return {c: self._camera.pixel_to_plane(*d.centroid, CENTER_Z[c])
                for c, d in detections.items() if c in CENTER_Z}

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

        positions = self._robot_positions(detections)
        if self._camera is not None:
            objects = Detection3DArray()
            objects.header.stamp = msg.header.stamp
            objects.header.frame_id = 'base_link'
            for color, (x, y, z) in positions.items():
                d3 = Detection3D()
                d3.header = objects.header
                d3.id = COLOR_TO_OBJECT[color]
                d3.bbox.center.position.x = x
                d3.bbox.center.position.y = y
                d3.bbox.center.position.z = z
                hyp = ObjectHypothesisWithPose()
                hyp.hypothesis.class_id = d3.id
                hyp.hypothesis.score = 1.0
                hyp.pose.pose.position = d3.bbox.center.position
                d3.results.append(hyp)
                objects.detections.append(d3)
            self._obj_pub.publish(objects)

        if self._debug_pub.get_subscription_count() > 0:
            labels = {c: COLOR_TO_OBJECT.get(c, c) for c in detections}
            for c, (x, y, _) in positions.items():
                labels[c] += f' {x * 1000:+.0f},{y * 1000:+.0f}mm'
            debug = draw_detections(bgr, detections, labels=labels)
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
