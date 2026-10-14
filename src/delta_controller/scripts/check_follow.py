#!/usr/bin/env python3
"""
Đo xem `follow` bám lon sát tới đâu — in liên tục trong lúc bạn đẩy lon thật.

    ros2 run delta_controller follow            # cửa sổ 1
    python3 src/delta_controller/scripts/check_follow.py            # đẩy lon bằng tay
    python3 src/delta_controller/scripts/check_follow.py --belt     # CHO BĂNG CHẠY

Nhìn bằng mắt thì chỉ biết "trông có vẻ đúng". Ba cột dưới đây mới nói được robot bám sát bao
nhiêu, và quan trọng hơn là nó có GIỮ được độ sát đó trong lúc lon đang dịch hay không — đứng yên
mà đúng thì dễ, đang chạy mà vẫn đúng mới là bám.

  LECH NGANG  khoảng cách ngang từ tâm đầu hút tới tâm lon. Dung sai giác hút là 12 mm ảo.
  KHE         đáy platform cách đỉnh lon bao nhiêu. Phải xấp xỉ `hover` của follow (mặc định
              20 mm ảo = 60 mm thật) và KHÔNG ĐƯỢC ÂM — âm là đã đâm vào lon.
  TOC DO LON  để biết số liệu đang đo lúc lon đứng yên hay lúc đang dịch.

`--belt` cho băng chạy rồi tự dừng trước khi lon tới mép (cuối băng không có vật chặn). Đây là
phép thử đáng giá hơn đẩy tay: băng đưa lon đi ĐỀU và LIÊN TỤC, nên sai lệch đo được là sai lệch
bám thật sự, không lẫn với cú giật của bàn tay.

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
from delta_controller.scene import (                               # noqa: E402
    BELT_CENTER, BELT_LENGTH, OBJECTS, on_belt, SCALE,
)
from nav_msgs.msg import Odometry                                  # noqa: E402
import rclpy                                                       # noqa: E402
from rclpy.node import Node                                        # noqa: E402
from sensor_msgs.msg import JointState                             # noqa: E402
from std_srvs.srv import Trigger                                   # noqa: E402

ACTIVE_JOINTS = ('Chain1_1', 'Chain2_1', 'Chain3_1')
STOP_MARGIN = 0.025 / SCALE        # m ảo: dừng băng khi lon còn cách mép chừng này
PLATFORM_HALF_THICKNESS = 0.003
BASE_Z = 1.0


class BeltDriver:
    """
    Cho băng chạy và tự dừng trước khi lon tới mép.

    Cuối băng KHÔNG có vật chặn — 2026-10-14 lon chạy quá đầu băng và rơi xuống bàn. Nên công cụ
    nào cho băng chạy cũng phải tự lo chuyện dừng, không trông vào người bấm kịp.
    """

    def __init__(self, node):
        self._run = node.create_client(Trigger, '/conveyor/run')
        self._stop = node.create_client(Trigger, '/conveyor/stop')
        self._far = None
        self.running = False

    def _call(self, client, what):
        if not client.wait_for_service(timeout_sec=2.0):
            raise SystemExit(f'Khong thay {what}. Chay: ros2 run delta_controller conveyor')
        done = threading.Event()
        future = client.call_async(Trigger.Request())
        future.add_done_callback(lambda _: done.set())
        done.wait(5.0)

    def start(self):
        self._call(self._run, '/conveyor/run')
        self.running = True
        print('Bang DANG CHAY. Se tu dung truoc khi lon toi mep.')

    def near_edge(self, y):
        """Lon đã tới sát mép chưa — mép nào là mép nguy hiểm thì suy từ chiều lon đang đi."""
        if self._far is None:
            return False
        return (self._far - y if self._far > BELT_CENTER[1] else y - self._far) <= STOP_MARGIN

    def note_direction(self, y_now, y_before):
        if self._far is None and abs(y_now - y_before) > 0.002:
            sign = 1.0 if y_now > y_before else -1.0
            self._far = BELT_CENTER[1] + sign * BELT_LENGTH / 2.0

    def stop(self, why):
        if not self.running:
            return
        self._call(self._stop, '/conveyor/stop')
        self.running = False
        print(f'Da dung bang ({why}).')


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
    ap.add_argument('--belt', action='store_true',
                    help='cho bang chay, tu dung truoc khi lon toi mep bang')
    args = ap.parse_args()

    rclpy.init()
    node = Watcher()
    threading.Thread(target=rclpy.spin, args=(node,), daemon=True).start()

    belt = BeltDriver(node) if args.belt else None
    if belt is not None:
        belt.start()

    half = {o.name: o.half_height for o in OBJECTS}
    previous = {}
    moving = []                    # lệch ngang đo được trong lúc lon ĐANG dịch
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
                if belt is not None:
                    belt.note_direction(cy, was[1])
            previous[name] = (cx, cy, cz, t)
            worst_gap = gap if worst_gap is None else min(worst_gap, gap)
            if belt is not None and belt.running and on_belt(cx, cy):
                if belt.near_edge(cy):
                    belt.stop('lon sap toi mep bang')
            if speed > 1.0:
                moving.append(flat)
            flag = '  <-- DAM VAO LON' if gap < 0 else ''
            print(f'{name:12s} {flat * SCALE * 1000:10.1f} / {flat * 1000:7.1f} '
                  f'{gap * SCALE * 1000:15.1f} {speed:14.1f}{flag}')
    except KeyboardInterrupt:
        pass
    if belt is not None:
        belt.stop('ket thuc')
    if moving:
        worst = max(moving) * SCALE * 1000
        mean = sum(moving) / len(moving) * SCALE * 1000
        print(f'\nLUC LON DANG DICH ({len(moving)} mau): lech ngang TB {mean:.1f} mm that, '
              f'te nhat {worst:.1f} mm ({"TRONG" if worst / SCALE < 12.0 else "VUOT"} dung sai '
              f'giac hut 12 mm ao)')
    else:
        print('\nKhong co mau nao luc lon dang dich — lon co chay khong?')
    if worst_gap is not None:
        print(f'\nKhe NHO NHAT trong ca luot: {worst_gap * SCALE * 1000:.1f} mm that '
              f'({"OK" if worst_gap > 0 else "DA DAM VAO LON"})')
    rclpy.shutdown()
    return 0


if __name__ == '__main__':
    sys.exit(main())
