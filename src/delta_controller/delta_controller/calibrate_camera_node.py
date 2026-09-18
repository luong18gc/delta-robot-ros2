"""
Hiệu chuẩn ngoại tham số camera bằng marker ArUco trên bàn (Bước 8.3).

    ros2 run delta_controller calibrate_camera

Thu N khung ảnh, nhận dạng marker, lấy trung bình tâm từng marker (giảm nhiễu cảm biến), giải PnP
với K từ camera_info, lưu YAML + ảnh minh họa. Cần thấy ít nhất 4 marker.
Tham số: image_topic, camera_info_topic, frames (20), output (đường dẫn YAML),
         compare_ground_truth (True: so với pose thật của camera mô phỏng — chỉ để đánh giá).
"""

import math
import os

import cv2
from cv_bridge import CvBridge
from delta_controller.camera_model import (
    camera_model_from_gazebo_pose,
    estimate_pose,
    marker_center,
)
from delta_controller.scene import (
    CALIB_ARUCO_DICT,
    CALIB_MARKER_Z,
    CALIB_MARKERS,
    SIDE_CAMERA_GT_RPY,
    SIDE_CAMERA_GT_XYZ,
)
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CameraInfo, Image
import yaml

DEFAULT_OUTPUT = os.path.expanduser('~/ros2_closed_loop_ws/calibration/side_camera.yaml')
MIN_MARKERS = 4


class CalibrationCollector(Node):
    """Thu ảnh và camera_info cho tới khi đủ số khung."""

    def __init__(self):
        super().__init__('delta_calibrate_camera')
        self.frames_needed = self.declare_parameter('frames', 20).value
        self.output = os.path.expanduser(self.declare_parameter('output', DEFAULT_OUTPUT).value)
        self.compare_gt = self.declare_parameter('compare_ground_truth', True).value
        image_topic = self.declare_parameter('image_topic', '/side_camera/image').value
        info_topic = self.declare_parameter('camera_info_topic', '/side_camera/camera_info').value
        self.bridge = CvBridge()
        self.dictionary = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, CALIB_ARUCO_DICT))
        # Tinh chỉnh góc marker dưới mức pixel. Mặc định (NONE) góc là pixel nguyên nên 20 khung
        # cho kết quả y hệt nhau; so trên ảnh thật: NONE 0.43 mm / 0.042°,
        # CONTOUR 0.33 mm / 0.015°.
        self.aruco_params = cv2.aruco.DetectorParameters_create()
        self.aruco_params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_CONTOUR
        self.K = None
        self.dist = None
        self.centers = {}     # id -> list tâm (u, v) qua các khung
        self.frames = 0
        self.last_image = None
        self.last_corners = None
        self.create_subscription(CameraInfo, info_topic, self._on_info, 10)
        self.create_subscription(Image, image_topic, self._on_image, qos_profile_sensor_data)

    def _on_info(self, msg):
        self.K = np.array(msg.k, float).reshape(3, 3)
        self.dist = np.array(msg.d, float) if len(msg.d) else np.zeros(5)

    def _on_image(self, msg):
        if self.frames >= self.frames_needed:
            return
        bgr = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        corners, ids, _ = cv2.aruco.detectMarkers(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY),
                                                  self.dictionary, parameters=self.aruco_params)
        if ids is None:
            return
        for c, marker_id in zip(corners, ids.flatten()):
            if int(marker_id) in CALIB_MARKERS:
                self.centers.setdefault(int(marker_id), []).append(marker_center(c))
        self.frames += 1
        self.last_image = bgr
        self.last_corners = (corners, ids)

    @property
    def done(self):
        return self.frames >= self.frames_needed and self.K is not None


def main(args=None):
    rclpy.init(args=args)
    node = CalibrationCollector()
    log = node.get_logger()
    log.info(f'Thu {node.frames_needed} khung anh co marker ArUco...')
    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.5)
    except KeyboardInterrupt:
        node.destroy_node()
        rclpy.try_shutdown()
        return

    ids = sorted(node.centers)
    if len(ids) < MIN_MARKERS:
        log.error(f'Chi thay marker {ids}, can it nhat {MIN_MARKERS}. '
                  'Robot/vat co che marker khong?')
        node.destroy_node()
        rclpy.try_shutdown()
        return

    obj = [(*CALIB_MARKERS[i], CALIB_MARKER_Z) for i in ids]
    img_pts = [tuple(np.mean(node.centers[i], axis=0)) for i in ids]
    spread = {i: float(np.max(np.std(node.centers[i], axis=0))) for i in ids}
    result = estimate_pose(obj, img_pts, node.K, node.dist)
    model = result.model
    pos = model.position()
    axis = model.optical_axis()
    tilt = math.degrees(math.asin(-axis[2]))
    heading = math.degrees(math.atan2(axis[1], axis[0]))

    print('\n=== KET QUA HIEU CHUAN CAMERA ===')
    print(f'Marker dung: {ids} ({len(ids)}), moi marker trung binh {node.frames} khung')
    for i, err in zip(ids, result.errors_px):
        print(f'  M{i}: sai so chieu lai {err:.2f} px, do dao dong tam {spread[i]:.2f} px')
    print(f'Sai so chieu lai RMS: {result.rms_px:.3f} px')
    print(f'Vi tri camera (he robot): ({pos[0]:+.4f}, {pos[1]:+.4f}, {pos[2]:+.4f}) m')
    print(f'Huong nhin: chuc xuong {tilt:.2f} do, huong {heading:.2f} do so voi truc X robot')

    report = {
        'markers_used': ids,
        'frames': node.frames,
        'rms_reprojection_px': result.rms_px,
        'camera_position_robot': [float(v) for v in pos],
        'tilt_down_deg': tilt,
        'heading_deg': heading,
    }
    if node.compare_gt:
        gt = camera_model_from_gazebo_pose(node.K, SIDE_CAMERA_GT_XYZ, SIDE_CAMERA_GT_RPY)
        pos_err = float(np.linalg.norm(pos - gt.position()))
        ang_err = math.degrees(math.acos(min(1.0, float(np.dot(axis, gt.optical_axis())))))
        print(f'So voi pose that (chi de danh gia): lech vi tri {pos_err * 1000:.2f} mm, '
              f'lech huong nhin {ang_err:.3f} do')
        report['ground_truth_position_error_mm'] = pos_err * 1000
        report['ground_truth_axis_error_deg'] = ang_err

    os.makedirs(os.path.dirname(node.output), exist_ok=True)
    with open(node.output, 'w') as f:
        yaml.safe_dump({'camera': model.to_dict(), 'report': report}, f, sort_keys=False,
                       allow_unicode=True)
    vis = node.last_image.copy()
    corners, marker_ids = node.last_corners
    cv2.aruco.drawDetectedMarkers(vis, corners, marker_ids)
    for (u, v), p in zip(img_pts, model.project(obj)):
        cv2.circle(vis, (int(round(u)), int(round(v))), 5, (0, 255, 0), 1)
        cv2.drawMarker(vis, (int(round(p[0])), int(round(p[1]))), (0, 0, 255),
                       cv2.MARKER_CROSS, 8, 1)
    image_path = os.path.splitext(node.output)[0] + '.png'
    cv2.imwrite(image_path, vis)
    print(f'Da luu: {node.output}\n        {image_path} (vong xanh = do duoc, dau do = chieu lai)')

    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
