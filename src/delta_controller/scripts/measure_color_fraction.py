#!/usr/bin/env python3
"""
Đo TỈ LỆ MÀU DANH NGHĨA của từng vật: diện tích pixel mang màu / diện tích hình bóng dự đoán.

    python3 src/delta_controller/scripts/measure_color_fraction.py

Cần mô phỏng đang chạy. Dời từng vật qua một lưới vị trí trong tầm với (dịch vụ Gazebo set_pose),
mỗi vị trí đo tỉ lệ màu khi vật KHÔNG bị che, rồi in trung vị để điền vào
`scene.SceneObject.color_fraction`.

Vì sao cần: `vision_estimation` tính tỉ lệ nhìn thấy = diện tích màu / (hình bóng x
color_fraction).
Vật nhiều màu (lon có nắp trắng, vành nhãn, vành logo) chỉ mang màu trên một phần hình bóng. Khai
báo color_fraction quá NHỎ thì tỉ lệ nhìn thấy luôn > 1 và cờ che khuất mất tác dụng; quá LỚN thì
vật lành lặn cũng bị coi là bị che.
"""

import statistics
import subprocess
import sys
import time

sys.path.insert(0, __file__.rsplit('/scripts/', 1)[0])
from cv_bridge import CvBridge                                       # noqa: E402
from delta_controller.camera_model import CameraModel                # noqa: E402
from delta_controller.color_detector import detect_objects           # noqa: E402
from delta_controller.scene import OBJECTS, TABLE_Z                  # noqa: E402
from delta_controller.vision_estimation import silhouette_features   # noqa: E402
import rclpy                                                         # noqa: E402
from rclpy.node import Node                                          # noqa: E402
from sensor_msgs.msg import Image                                    # noqa: E402
import yaml                                                          # noqa: E402

CALIBRATION = '/home/luong18gc/ros2_closed_loop_ws/calibration/side_camera.yaml'
BASE_Z = 1.0
# Lưới vị trí trong tầm với, đủ xa nhau để ba vật không che nhau.
GRID = [(0.00, 0.00), (0.06, 0.00), (0.09, 0.00), (0.00, 0.08), (0.00, -0.08),
        (0.06, 0.07), (0.06, -0.07), (-0.05, 0.06), (-0.05, -0.06)]
PARK = (0.0, -0.30)      # chỗ để hai vật còn lại ra ngoài khung hình
SETTLE_SEC = 1.0


class Camera(Node):
    def __init__(self):
        super().__init__('measure_color_fraction')
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
    print('vat          | vi tri (mm)   | dien tich mau | hinh bong | ti le')
    summary = {}
    for obj in OBJECTS:
        others = [o for o in OBJECTS if o is not obj]
        for other in others:                       # dọn hai vật kia ra ngoài khung
            set_pose(other.name, PARK[0], PARK[1] + 0.06 * OBJECTS.index(other),
                     BASE_Z + TABLE_Z + other.half_height)
        fractions = []
        for x, y in GRID:
            set_pose(obj.name, x, y, BASE_Z + TABLE_Z + obj.half_height)
            time.sleep(SETTLE_SEC)
            image = node.fresh_image()
            if image is None:
                print('  khong nhan duoc anh')
                continue
            found = detect_objects(image)
            if obj.color not in found:
                print(f'{obj.name:12s} | ({1000 * x:+4.0f},{1000 * y:+4.0f}) | KHONG THAY')
                continue
            detection = found[obj.color]
            area, _, _ = silhouette_features(camera, obj,
                                             (x, y, TABLE_Z + obj.half_height))
            fraction = detection.area / area
            fractions.append(fraction)
            print(f'{obj.name:12s} | ({1000 * x:+4.0f},{1000 * y:+4.0f}) | '
                  f'{detection.area:8d} px  | {area:7.0f} px | {fraction:.3f}')
        if fractions:
            summary[obj.name] = fractions
        for other in others:                       # trả hai vật kia về chỗ cũ
            set_pose(other.name, other.home_xy[0], other.home_xy[1],
                     BASE_Z + TABLE_Z + other.half_height)
    for obj in OBJECTS:                            # trả vật đang đo về chỗ cũ
        set_pose(obj.name, obj.home_xy[0], obj.home_xy[1],
                 BASE_Z + TABLE_Z + obj.half_height)

    print('\nKET QUA (dien vao scene.SceneObject.color_fraction):')
    for name, values in summary.items():
        spread = max(values) - min(values)
        print(f'  {name:12s} trung vi {statistics.median(values):.2f}  '
              f'(nho nhat {min(values):.2f}, lon nhat {max(values):.2f}, '
              f'bien do {spread:.2f}, n = {len(values)})')
    rclpy.shutdown()


if __name__ == '__main__':
    main()
