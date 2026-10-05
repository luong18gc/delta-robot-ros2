"""
Node thị giác cho CAMERA THẬT (Bước 10a) — phát ra đúng các topic mà khối điều khiển đang dùng.

    ros2 run delta_controller real_vision

Vào : ảnh USB đọc thẳng từ camera (không qua ROS); nội tham số `calibration/c270_intrinsics.yaml`.
Ra  : /vision/detections, /vision/objects (frame base_link), /vision/debug_image — GIỐNG HỆT node
      `vision` của camera mô phỏng, nên `task_executor`, cờ tin cậy, trí nhớ quan sát và toàn bộ
      lệnh cấp cao chạy lại nguyên vẹn, không sửa dòng nào.

Ba khác biệt so với node mô phỏng, đều có lý do đo được:

1. **Ngoại tham số giải lại MỖI KHUNG** (`real_camera.PoseTracker`) thay vì nạp một file cố định.
   Camera xoay 1° là vị trí vật sai 7.7 mm ảo, 2° là vượt dung sai giác hút 12 mm — mà giá kẹp bàn
   bị chạm tay thì không có gì báo. Marker nằm cố định ở rìa bàn nên lúc nào cũng thấy.

2. **Giới hạn vùng xét theo HÌNH HỌC** (`table_roi_mask`): chiếu vùng bàn lên ảnh, bỏ hết phần
   ngoài. Tường và sàn chiếm 18% khung hình; đo 2026-10-05 thì vô hại (S = 57 < ngưỡng 90) nhưng
   ở lab tường từng bị nhận là vật xanh lá (S ≈ 113). Loại bằng hình học thì không phụ thuộc
   ánh sáng.

3. **Đọc ảnh bằng vòng hẹn giờ** chứ không chờ topic: camera USB không đi qua ROS. Hàng đợi V4L2
   đặt về 1 khung (bớt 2 trong 5 khung trễ, xem probe_camera.open_camera).
"""

import os
import time

import cv2
from cv_bridge import CvBridge
from delta_controller import usb_camera
from delta_controller.color_detector import detect_objects, draw_detections
from delta_controller.real_camera import aruco_detector, PoseTracker, table_roi_mask
from delta_controller.scene import REAL_OBJECTS, SCALE
from delta_controller.vision_estimation import estimate_object
import numpy as np
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import Image
from vision_msgs.msg import (
    Detection2D,
    Detection2DArray,
    Detection3D,
    Detection3DArray,
    ObjectHypothesisWithPose,
)
import yaml

WS = os.path.expanduser('~/ros2_closed_loop_ws')
DEFAULT_INTRINSICS = os.path.join(WS, 'calibration', 'c270_intrinsics.yaml')
# Dùng REAL_OBJECTS (tỉ lệ màu của lon THẬT), không phải OBJECTS của cảnh mô phỏng.
COLOR_TO_OBJECT = {o.color: o.name for o in REAL_OBJECTS}
OBJECT_OF_COLOR = {o.color: o for o in REAL_OBJECTS}


class RealVisionNode(Node):
    """Đọc camera USB, nhận dạng lon, phát vị trí trong hệ ẢO."""

    def __init__(self):
        super().__init__('delta_real_vision')
        device = self.declare_parameter('device', 'auto').value
        intrinsics = os.path.expanduser(
            self.declare_parameter('intrinsics_file', DEFAULT_INTRINSICS).value)
        rate = float(self.declare_parameter('rate_hz', 10.0).value)

        if not os.path.exists(intrinsics):
            raise SystemExit(f'Chua co {intrinsics} — chay calibrate_intrinsics.py truoc.')
        with open(intrinsics) as f:
            data = yaml.safe_load(f)
        self._K = np.array(data['camera']['K'], float)
        self._dist = np.array(data['camera']['dist'], float)
        meta = data.get('meta', {})

        device = usb_camera.resolve_device(device, log=self.get_logger().info)
        mode = usb_camera.best_mjpg_mode(device)
        if mode is None:
            raise SystemExit(f'Khong doc duoc che do MJPG tu {device}')
        if (mode[0], mode[1]) != (meta.get('width'), meta.get('height')):
            raise SystemExit(
                f'Camera o {mode[0]}x{mode[1]} nhung noi tham so hieu chuan o '
                f'{meta.get("width")}x{meta.get("height")} — K khong dung cho do phan giai khac.')
        usb_camera.lock_manual(device, log=lambda _: None)
        self._cap = usb_camera.open_camera(device, mode[0], mode[1])
        usb_camera.warm_up(self._cap)

        self._tracker = PoseTracker(self._K, self._dist)
        self._detector = aruco_detector()
        self._bridge = CvBridge()
        self._roi = None
        self._det_pub = self.create_publisher(Detection2DArray, '/vision/detections', 10)
        self._obj_pub = self.create_publisher(Detection3DArray, '/vision/objects', 10)
        self._debug_pub = self.create_publisher(Image, '/vision/debug_image', 10)
        self._frames = self._busy_sec = 0
        self._last_seen = None
        self.create_timer(1.0 / rate, self._tick)
        self.create_timer(10.0, self._report)
        self.get_logger().info(
            f'Camera {mode[0]}x{mode[1]} @ {rate:.0f} Hz, noi tham so RMS '
            f'{meta.get("rms_px", 0):.3f} px. Ngoai tham so giai lai moi khung tu marker.')

    # ------------------------------------------------------------------ vòng xử lý

    def _tick(self):
        ok, frame = self._cap.read()
        if not ok:
            return
        start = time.perf_counter()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self._tracker.update(gray, self._detector)
        if not self._tracker.ready:
            self._warn_no_pose()
            return
        camera = self._tracker.model
        # Vùng xét đổi theo tư thế camera; dựng lại mỗi khung (dưới 1 ms) để camera xê dịch là
        # vùng xét đi theo, không bị lệch dần.
        self._roi = table_roi_mask(camera, frame.shape)
        masked = cv2.bitwise_and(frame, frame, mask=self._roi)

        detections = detect_objects(masked)
        stamp = self.get_clock().now().to_msg()
        self._publish_pixels(detections, stamp)
        estimates = {c: estimate_object(d, camera, OBJECT_OF_COLOR[c], frame.shape)
                     for c, d in detections.items() if c in OBJECT_OF_COLOR}
        self._publish_objects(estimates, stamp)
        if self._debug_pub.get_subscription_count() > 0:
            self._publish_debug(frame, detections, estimates, stamp)

        seen = sorted(COLOR_TO_OBJECT.get(c, c) for c in detections)
        if seen != self._last_seen:
            self.get_logger().info(f'Thay {len(seen)} vat: {", ".join(seen) or "(khong co)"}')
            self._last_seen = seen
        self._frames += 1
        self._busy_sec += time.perf_counter() - start

    def _warn_no_pose(self):
        if self._last_seen != 'no-pose':
            self.get_logger().warning(
                'Chua khoa duoc tu the camera — co thay du marker khong? '
                'Dung view_camera.py de ngam.')
            self._last_seen = 'no-pose'

    # ------------------------------------------------------------------ phát tin

    def _publish_pixels(self, detections, stamp):
        out = Detection2DArray()
        out.header.stamp = stamp
        for color, det in detections.items():
            d = Detection2D()
            d.header = out.header
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

    def _publish_objects(self, estimates, stamp):
        objects = Detection3DArray()
        objects.header.stamp = stamp
        objects.header.frame_id = 'base_link'
        for color, est in estimates.items():
            x, y, z = est.position
            d3 = Detection3D()
            d3.header = objects.header
            d3.id = COLOR_TO_OBJECT[color]
            d3.bbox.center.position.x = float(x)
            d3.bbox.center.position.y = float(y)
            d3.bbox.center.position.z = float(z)
            hyp = ObjectHypothesisWithPose()
            hyp.hypothesis.class_id = d3.id
            hyp.hypothesis.score = min(1.0, est.visible_fraction) if est.reliable else 0.0
            hyp.pose.pose.position = d3.bbox.center.position
            d3.results.append(hyp)
            objects.detections.append(d3)
        self._obj_pub.publish(objects)

    def _publish_debug(self, frame, detections, estimates, stamp):
        labels = {c: COLOR_TO_OBJECT.get(c, c) for c in detections}
        for c, est in estimates.items():
            x, y, _ = est.position
            labels[c] += (f' {x * 1000 * SCALE:+.0f},{y * 1000 * SCALE:+.0f}mm that'
                          f' {100 * est.visible_fraction:.0f}%')
            if est.method in ('top_edge', 'bottom_edge'):
                labels[c] += f' [{est.method}]'
            if not est.reliable:
                labels[c] += ' BI CHE?'
        debug = draw_detections(frame, detections, labels=labels)
        if self._roi is not None:                      # viền vùng xét, để ngắm cho dễ
            edges = cv2.morphologyEx(self._roi, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
            debug[edges > 0] = (80, 80, 255)
        last = self._tracker.last
        if last is not None:
            px, py, pz = last.position_real_mm()
            cv2.putText(debug, f'camera: lui {-px:.0f} cao {pz:.0f} chuc {last.tilt_deg():.0f}deg'
                        f'  {len(last.marker_ids)}/6 marker  RMS {last.rms_px:.1f}px',
                        (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
        msg = self._bridge.cv2_to_imgmsg(debug, 'bgr8')
        msg.header.stamp = stamp
        self._debug_pub.publish(msg)

    def _report(self):
        if self._frames:
            tracker = self._tracker
            self.get_logger().info(
                f'{self._frames / 10.0:.1f} anh/s, xu ly '
                f'{1000.0 * self._busy_sec / self._frames:.1f} ms/anh; '
                f'tu the: {tracker.updates} khung dung, {tracker.skipped} bo qua')
            tracker.updates = tracker.skipped = 0
        self._frames = self._busy_sec = 0

    def destroy_node(self):
        if getattr(self, '_cap', None) is not None:
            self._cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = RealVisionNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
