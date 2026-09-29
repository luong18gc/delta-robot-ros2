#!/usr/bin/env python3
"""
Đo ĐỘ NHẠY của cờ tin cậy khi một lon bị lon khác che.

    python3 src/delta_controller/scripts/measure_occlusion.py

Cần mô phỏng đang chạy. Đặt lon pepsi nằm trên đường nhìn từ camera tới lon coca, dịch dần sang
ngang để che coca từ nhiều tới ít, mỗi bước in tỉ lệ nhìn thấy + sai số ước lượng. Dùng để chọn
`scene.SceneObject.color_fraction` sao cho lon lành lặn không bị từ chối mà lon bị che vẫn bị bắt.
"""

import os
import subprocess
import sys
import time

sys.path.insert(0, __file__.rsplit('/scripts/', 1)[0])
import cv2                                                           # noqa: E402
from cv_bridge import CvBridge                                       # noqa: E402
from delta_controller.camera_model import CameraModel                # noqa: E402
from delta_controller.color_detector import detect_objects, draw_detections  # noqa: E402
from delta_controller.scene import OBJECTS, TABLE_Z                  # noqa: E402
from delta_controller.vision_estimation import estimate_object       # noqa: E402
import rclpy                                                         # noqa: E402
from rclpy.node import Node                                          # noqa: E402
from sensor_msgs.msg import Image                                    # noqa: E402
import yaml                                                          # noqa: E402

CALIBRATION = '/home/luong18gc/ros2_closed_loop_ws/calibration/side_camera.yaml'
BASE_Z = 1.0
TARGET, BLOCKER = 'coca_can', 'pepsi_can'
TARGET_XY = (0.06, 0.0)            # lon bị che, nằm xa camera
BLOCKER_X = 0.0                    # lon che, nằm giữa camera và lon kia
OFFSETS = [0.0, 0.006, 0.012, 0.018, 0.024, 0.030, 0.045]
PARK = (0.0, -0.32)
OUT_DIR = os.environ.get('OUT_DIR', '/tmp/claude-1000')
SETTLE_SEC = 1.0


class Camera(Node):
    def __init__(self):
        super().__init__('measure_occlusion')
        self._bridge = CvBridge()
        self.image = None
        self.create_subscription(Image, '/side_camera/image', self._on_image, 1)

    def _on_image(self, msg):
        self.image = self._bridge.imgmsg_to_cv2(msg, 'bgr8')

    def fresh_image(self, timeout_sec=10.0):
        self.image = None
        deadline = time.monotonic() + timeout_sec
        while self.image is None and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
        return self.image


def set_pose(name, x, y, z):
    request = (f'name: "{name}", position: {{x: {x}, y: {y}, z: {z}}}, '
               'orientation: {x: 0, y: 0, z: 0, w: 1}')
    subprocess.run(['gz', 'service', '-s', '/world/delta_world/set_pose',
                    '--reqtype', 'gz.msgs.Pose', '--reptype', 'gz.msgs.Boolean',
                    '--timeout', '2000', '--req', request], capture_output=True)


def main():
    rclpy.init()
    node = Camera()
    camera = CameraModel.from_dict(yaml.safe_load(open(CALIBRATION))['camera'])
    objs = {o.name: o for o in OBJECTS}
    target, blocker = objs[TARGET], objs[BLOCKER]
    other = [o for o in OBJECTS if o.name not in (TARGET, BLOCKER)][0]
    set_pose(other.name, PARK[0], PARK[1], BASE_Z + TABLE_Z + other.half_height)
    set_pose(target.name, TARGET_XY[0], TARGET_XY[1], BASE_Z + TABLE_Z + target.half_height)

    print('lech ngang lon che | ti le nhin thay | tin cay | sai so uoc luong')
    for dy in OFFSETS:
        set_pose(blocker.name, BLOCKER_X, dy, BASE_Z + TABLE_Z + blocker.half_height)
        time.sleep(SETTLE_SEC)
        image = node.fresh_image()
        found = detect_objects(image)
        if target.color not in found:
            print(f'{1000 * dy:+6.0f} mm        | KHONG THAY')
            continue
        det = found[target.color]
        est = estimate_object(det, camera, target, image.shape)
        err = 1000 * ((est.position[0] - TARGET_XY[0]) ** 2
                      + (est.position[1] - TARGET_XY[1]) ** 2) ** 0.5
        print(f'{1000 * dy:+6.0f} mm        | {est.visible_fraction:12.2f}  | '
              f'{"OK " if est.reliable else "BI CHE":7s} | {err:6.1f} mm  ({est.method})'
              f'  | {det.pieces} manh, bbox {det.bbox}, {det.area} px')
        cv2.imwrite(f'{OUT_DIR}/occlusion_{1000 * dy:03.0f}.png',
                    draw_detections(image, found))

    for o in OBJECTS:
        set_pose(o.name, o.home_xy[0], o.home_xy[1], BASE_Z + TABLE_Z + o.half_height)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
