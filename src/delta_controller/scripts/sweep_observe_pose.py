#!/usr/bin/env python3
"""
Quét vài tư thế quan sát, đo xem ở tư thế nào camera thấy rõ nhất mọi vật.

    python3 src/delta_controller/scripts/sweep_observe_pose.py

Cần mô phỏng đang chạy. Với mỗi tư thế: đưa robot tới đó, chờ ổn định, rồi so sánh
/vision/objects với vị trí THẬT từ odometry. In sai số và điểm tin cậy của từng vật.

Dùng để chọn `scene.OBSERVE_XYZ`: cánh tay robot che vùng nào thì vật ở đó bị hỏng phép khớp
hình bóng, mà vùng bị che đổi theo vị trí platform.
"""

import math
import sys
import time

sys.path.insert(0, __file__.rsplit('/scripts/', 1)[0])
from delta_controller.delta_kinematics import inverse_kinematics    # noqa: E402
from delta_controller.joint_commander import JointCommander         # noqa: E402
from delta_controller.scene import OBJECTS                          # noqa: E402
from nav_msgs.msg import Odometry                                   # noqa: E402
import rclpy                                                        # noqa: E402
from rclpy.node import Node                                         # noqa: E402
from vision_msgs.msg import Detection3DArray                        # noqa: E402

POSES = [
    (0.0, 0.0, -0.11),
    (0.05, 0.0, -0.11),
    (0.08, 0.0, -0.12),
    (0.0, 0.0, -0.13),
    (-0.04, 0.0, -0.11),
]
SETTLE_SEC = 4.0


class Watch(Node):
    def __init__(self):
        super().__init__('sweep_observe')
        self.vision = None
        self.truth = {}
        self.create_subscription(Detection3DArray, '/vision/objects', self._on_vision, 1)
        for obj in OBJECTS:
            self.create_subscription(
                Odometry, f'/objects/{obj.name}/odometry',
                lambda m, n=obj.name: self.truth.__setitem__(
                    n, (m.pose.pose.position.x, m.pose.pose.position.y)), 1)

    def _on_vision(self, msg):
        self.vision = {d.results[0].hypothesis.class_id:
                       (d.results[0].pose.pose.position, d.results[0].hypothesis.score)
                       for d in msg.detections}

    def fresh_vision(self, seconds):
        """Bỏ kết quả cũ rồi chờ kết quả mới (camera mô phỏng chỉ vài hình/giây)."""
        self.vision = None
        deadline = time.monotonic() + seconds
        while self.vision is None and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
        return self.vision


def main():
    rclpy.init()
    node = Watch()
    commander = JointCommander(node)
    commander.wait_for_connection()
    for goal in POSES:
        commander.send(*inverse_kinematics(*goal))
        deadline = time.monotonic() + SETTLE_SEC
        while time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
        seen = node.fresh_vision(15.0)
        print(f'\n=== tu the quan sat {goal} ===')
        if not seen:
            print('  khong nhan duoc /vision/objects')
            continue
        for obj in OBJECTS:
            truth = node.truth.get(obj.name)
            if obj.name not in seen or truth is None:
                print(f'  {obj.name:12s} KHONG THAY')
                continue
            p, score = seen[obj.name]
            error = 1000 * math.hypot(p.x - truth[0], p.y - truth[1])
            print(f'  {obj.name:12s} lech {error:6.1f} mm  score {score:.2f}'
                  f'{"" if score > 0 else "   <- bi loai"}')
    rclpy.shutdown()


if __name__ == '__main__':
    main()
