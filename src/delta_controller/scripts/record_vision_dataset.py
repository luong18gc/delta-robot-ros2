#!/usr/bin/env python3
"""
Thu bộ dữ liệu đánh giá thị giác (Bước 8.4): ảnh camera + vị trí thật của vật.

Chạy khi mô phỏng đang chạy (ros2 launch delta_controller pick_place.launch.py), robot ở home:
    python3 src/delta_controller/scripts/record_vision_dataset.py [thư_mục_ra]
Mặc định ghi vào ~/ros2_closed_loop_ws/datasets/vision_eval/ : ảnh PNG + labels.json.

Kịch bản:
  grid      — lần lượt từng vật dời tới các điểm lưới trên bàn (vật khác ở vị trí ban đầu).
  occlusion — robot lơ lửng phía trên từng vật ở nhiều độ cao (platform che một phần).
  bin       — từng vật đặt vào từng ô khay (vật khác ở vị trí ban đầu).
Dời vật bằng dịch vụ Gazebo /world/<w>/set_pose; vị trí thật đọc từ /objects/<vật>/odometry.
"""

import json
import math
import os
import subprocess
import sys
import time

import cv2
from cv_bridge import CvBridge
from delta_controller.delta_kinematics import inverse_kinematics
from delta_controller.joint_commander import JointCommander
from delta_controller.scene import (
    BIN_CENTER,
    BIN_FLOOR_Z,
    BIN_OUTER_HALF,
    BIN_SLOTS,
    CALIB_MARKER_SIZE,
    CALIB_MARKERS,
    OBJECTS,
    TABLE_Z,
)
from nav_msgs.msg import Odometry
import rclpy
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image

BASE_Z = 1.0                 # world = robot + (0, 0, 1)
REST_EXTRA = {'blue_sphere': 0.0005}   # đế chống lăn nâng cầu 0.5 mm
GRID_STEP = 0.03
SETTLE_SEC = 0.8
HOME = (0.0, 0.0, -0.1405)
OCCLUSION_HEIGHTS = (0.060, 0.030, 0.015, 0.005)   # khe từ mặt dưới platform tới đỉnh vật (m)


def rest_z(obj, surface_z):
    return surface_z + obj.half_height + REST_EXTRA.get(obj.name, 0.0)


def grid_points():
    """Điểm lưới trên bàn, tránh khay, marker và vị trí ban đầu của các vật."""
    pts = []
    n = int(round(0.15 / GRID_STEP))
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            x, y = i * GRID_STEP, j * GRID_STEP
            if abs(x) > 0.16 or abs(y) > 0.16:
                continue
            margin = BIN_OUTER_HALF + 0.02
            if abs(x - BIN_CENTER[0]) < margin and abs(y - BIN_CENTER[1]) < margin:
                continue
            if any(math.hypot(x - mx, y - my) < CALIB_MARKER_SIZE * 0.7 + 0.02
                   for mx, my in CALIB_MARKERS.values()):
                continue
            pts.append((round(x, 3), round(y, 3)))
    return pts


class Recorder:
    def __init__(self, out_dir):
        self.out = out_dir
        os.makedirs(out_dir, exist_ok=True)
        self.node = rclpy.create_node('vision_dataset_recorder')
        self.bridge = CvBridge()
        self.image = None
        self.image_wall = 0.0
        self.gt = {}
        self.node.create_subscription(Image, '/side_camera/image', self._on_image,
                                      qos_profile_sensor_data)
        for obj in OBJECTS:
            self.node.create_subscription(
                Odometry, f'/objects/{obj.name}/odometry',
                lambda m, n=obj.name: self.gt.__setitem__(
                    n, (m.pose.pose.position.x, m.pose.pose.position.y,
                        m.pose.pose.position.z - BASE_Z)), 10)
        self.commander = JointCommander(self.node)
        self.labels = []
        self.count = 0

    def _on_image(self, msg):
        self.image = msg
        self.image_wall = time.monotonic()

    def spin_for(self, sec):
        end = time.monotonic() + sec
        while time.monotonic() < end:
            rclpy.spin_once(self.node, timeout_sec=0.02)

    def set_pose(self, name, x, y, z):
        req = f'name: "{name}", position: {{x: {x}, y: {y}, z: {z + BASE_Z}}}'
        subprocess.run(['gz', 'service', '-s', '/world/delta_world/set_pose',
                        '--reqtype', 'gz.msgs.Pose', '--reptype', 'gz.msgs.Boolean',
                        '--timeout', '2000', '--req', req],
                       check=True, capture_output=True)

    def all_home(self):
        for obj in OBJECTS:
            self.set_pose(obj.name, *obj.home_xy, rest_z(obj, TABLE_Z))

    def move_robot(self, xyz, wait=2.5):
        self.commander.send(*inverse_kinematics(*xyz))
        self.spin_for(wait)

    def capture(self, scenario, meta):
        """Chờ ổn định rồi lấy ảnh chụp SAU thời điểm đó, cùng vị trí thật hiện tại."""
        self.spin_for(SETTLE_SEC)
        t = time.monotonic()
        while self.image_wall <= t:
            rclpy.spin_once(self.node, timeout_sec=0.05)
        self.spin_for(0.05)
        name = f'{self.count:04d}_{scenario}.png'
        cv2.imwrite(os.path.join(self.out, name), self.bridge.imgmsg_to_cv2(self.image, 'bgr8'))
        self.labels.append({'image': name, 'scenario': scenario, **meta,
                            'ground_truth': {k: list(v) for k, v in self.gt.items()}})
        self.count += 1

    def save(self):
        with open(os.path.join(self.out, 'labels.json'), 'w') as f:
            json.dump({'base_z': BASE_Z, 'table_z': TABLE_Z, 'samples': self.labels}, f, indent=1)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
        '~/ros2_closed_loop_ws/datasets/vision_eval')
    rclpy.init()
    rec = Recorder(out)
    if not rec.commander.wait_for_connection(5.0):
        print('Khong ket noi duoc mo phong')
        return
    rec.spin_for(1.0)
    rec.move_robot(HOME)
    rec.all_home()

    points = grid_points()
    print(f'grid: {len(points)} diem x {len(OBJECTS)} vat')
    for obj in OBJECTS:
        others = {o.name: o.home_xy for o in OBJECTS if o.name != obj.name}
        for x, y in points:
            if any(math.hypot(x - ox, y - oy) < 0.04 for ox, oy in others.values()):
                continue
            rec.set_pose(obj.name, x, y, rest_z(obj, TABLE_Z))
            rec.capture('grid', {'moved': obj.name})
        rec.set_pose(obj.name, *obj.home_xy, rest_z(obj, TABLE_Z))
        print(f'  xong {obj.name}: {rec.count} anh')

    print('occlusion: robot lo lung tren tung vat')
    rec.all_home()
    for obj in OBJECTS:
        top = rest_z(obj, TABLE_Z) + obj.half_height
        for gap in OCCLUSION_HEIGHTS:
            rec.move_robot((obj.home_xy[0], obj.home_xy[1], top + 0.003 + gap))
            rec.capture('occlusion', {'target': obj.name, 'gap_mm': gap * 1000})
        rec.move_robot(HOME)

    print('bin: tung vat vao tung o khay')
    for obj in OBJECTS:
        for slot, (x, y) in BIN_SLOTS.items():
            rec.set_pose(obj.name, x, y, rest_z(obj, BIN_FLOOR_Z))
            rec.capture('bin', {'moved': obj.name, 'slot': slot})
        rec.set_pose(obj.name, *obj.home_xy, rest_z(obj, TABLE_Z))

    rec.all_home()
    rec.save()
    print(f'Da luu {rec.count} anh + labels.json vao {out}')
    rec.node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
