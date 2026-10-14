#!/usr/bin/env python3
"""
Đo xem `follow` bám lon sát tới đâu — in liên tục trong lúc bạn đẩy lon thật.

    ros2 run delta_controller follow            # cửa sổ 1
    python3 src/delta_controller/scripts/check_follow.py     # cửa sổ 2

Nhìn bằng mắt thì chỉ biết "trông có vẻ đúng". Ba cột dưới đây mới nói được robot bám sát bao
nhiêu, và quan trọng hơn là nó có GIỮ được độ sát đó trong lúc lon đang dịch hay không — đứng yên
mà đúng thì dễ, đang chạy mà vẫn đúng mới là bám.

  LECH NGANG  khoảng cách ngang từ tâm đầu hút tới tâm lon. Dung sai giác hút là 12 mm ảo.
  KHE         đáy platform cách đỉnh lon bao nhiêu. Phải xấp xỉ `hover` của follow (mặc định
              20 mm ảo = 60 mm thật) và KHÔNG ĐƯỢC ÂM — âm là đã đâm vào lon.
  TOC DO LON  để biết số liệu đang đo lúc lon đứng yên hay lúc đang dịch.

Vị trí đầu hút lấy bằng FK từ `/joint_states` (góc khớp ĐO ĐƯỢC), không phải từ lệnh đã gửi — nên
nó phản ánh robot thật sự ở đâu, kể cả khi còn đang đuổi theo.
"""

import argparse
import math
import sys
import threading
import time

sys.path.insert(0, __file__.rsplit('/scripts/', 1)[0])

from delta_controller.delta_kinematics import forward_kinematics   # noqa: E402
from delta_controller.scene import OBJECTS, SCALE                  # noqa: E402
from nav_msgs.msg import Odometry                                  # noqa: E402
import rclpy                                                       # noqa: E402
from rclpy.node import Node                                        # noqa: E402
from sensor_msgs.msg import JointState                             # noqa: E402

ACTIVE_JOINTS = ('Chain1_1', 'Chain2_1', 'Chain3_1')
PLATFORM_HALF_THICKNESS = 0.003
BASE_Z = 1.0


class Watcher(Node):
    """Đọc góc khớp và vị trí lon, không ra lệnh gì cho robot."""

    def __init__(self):
        super().__init__('check_follow')
        self.joints = None
        self.cans = {}                     # tên -> (x, y, z, t)
        self.create_subscription(JointState, '/joint_states', self._on_joints, 10)
        for obj in OBJECTS:
            self.create_subscription(
                Odometry, f'/objects/{obj.name}/odometry', self._make(obj.name), 10)

    def _on_joints(self, msg):
        pos = dict(zip(msg.name, msg.position))
        if all(j in pos for j in ACTIVE_JOINTS):
            self.joints = tuple(pos[j] for j in ACTIVE_JOINTS)

    def _make(self, name):
        def callback(msg):
            p = msg.pose.pose.position
            self.cans[name] = (p.x, p.y, p.z - BASE_Z, time.monotonic())
        return callback


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--seconds', type=float, default=0.0, help='0 = chay mai (Ctrl+C de dung)')
    args = ap.parse_args()

    rclpy.init()
    node = Watcher()
    threading.Thread(target=rclpy.spin, args=(node,), daemon=True).start()

    half = {o.name: o.half_height for o in OBJECTS}
    previous = {}
    print(f'{"lon":12s} {"LECH NGANG":>22s} {"KHE":>18s} {"TOC DO LON":>14s}')
    print(f'{"":12s} {"(mm that / mm ao)":>22s} {"(mm that)":>18s} {"(mm that/s)":>14s}')
    deadline = time.monotonic() + args.seconds if args.seconds else None
    worst_gap = None
    try:
        while deadline is None or time.monotonic() < deadline:
            time.sleep(0.5)
            if node.joints is None or not node.cans:
                print('  cho /joint_states va /objects/*/odometry...')
                continue
            tx, ty, tz = forward_kinematics(*node.joints)
            # Lon gần đầu hút nhất chính là lon follow đang bám.
            name, (cx, cy, cz, t) = min(
                node.cans.items(), key=lambda kv: math.hypot(kv[1][0] - tx, kv[1][1] - ty))
            flat = math.hypot(cx - tx, cy - ty)
            gap = (tz - PLATFORM_HALF_THICKNESS) - (cz + half[name])
            was = previous.get(name)
            speed = 0.0
            if was is not None and t > was[3]:
                speed = math.hypot(cx - was[0], cy - was[1]) / (t - was[3]) * SCALE * 1000
            previous[name] = (cx, cy, cz, t)
            worst_gap = gap if worst_gap is None else min(worst_gap, gap)
            flag = '  <-- DAM VAO LON' if gap < 0 else ''
            print(f'{name:12s} {flat * SCALE * 1000:10.1f} / {flat * 1000:7.1f} '
                  f'{gap * SCALE * 1000:15.1f} {speed:14.1f}{flag}')
    except KeyboardInterrupt:
        pass
    if worst_gap is not None:
        print(f'\nKhe NHO NHAT trong ca luot: {worst_gap * SCALE * 1000:.1f} mm that '
              f'({"OK" if worst_gap > 0 else "DA DAM VAO LON"})')
    rclpy.shutdown()
    return 0


if __name__ == '__main__':
    sys.exit(main())
