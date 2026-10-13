#!/usr/bin/env python3
"""
Đo tốc độ băng tải VÀ điểm gắp thật, bằng chính camera đã hiệu chuẩn.

Cần đang chạy: ros2 launch delta_controller digital_twin.launch.py
Rồi:           python3 src/delta_controller/scripts/measure_belt_speed.py

Hai con số, một phép đo. Đặt lon ở đầu nạp, script cho băng chạy, theo dõi lon qua
`/vision/objects` cho tới khi nó đứng lại, rồi báo:

  * TỐC ĐỘ BĂNG (mm thật/giây) — máy trạng thái cần để biết chờ bao lâu là hợp lý, và để đặt
    hạn chờ: lon không tới sau quãng đó thì có chuyện (lon kẹt, dây trượt, không ai đặt lon).
  * ĐIỂM GẮP THẬT — chỗ lon TỰ dừng khi chạy tới cuối. Khác với chỗ đặt lon bằng tay rồi tì sát
    con lăn: lon chạy tới còn trượt thêm theo quán tính, và trượt bao nhiêu thì chỉ đo mới biết.

Đo bằng camera chứ không bằng thước: cùng khối thị giác mà hệ thống dùng lúc chạy thật, nên con
số đo được là con số hệ thống SẼ THẤY, kể cả khi nó lệch so với thực địa.
"""

import argparse
import glob
import sys
import threading
import time

sys.path.insert(0, __file__.rsplit('/scripts/', 1)[0])

from delta_controller.scene import (            # noqa: E402
    BELT_PICK_XY, OBJECTS, REAL_BELT_PICK_Y, SCALE,
)
import rclpy                                    # noqa: E402
from rclpy.node import Node                     # noqa: E402
import serial                                   # noqa: E402
from vision_msgs.msg import Detection3DArray    # noqa: E402

BAUD = 115200
SETTLED_SEC = 1.5          # đứng yên bao lâu thì coi là đã tới cuối
MOVE_EPS = 0.0015          # m ảo: dịch dưới mức này coi như đứng yên (nhiễu đo 0.5-0.9 mm thật)
MAX_RUN_SEC = 30.0


class BeltWatcher(Node):
    """Ghi lại vị trí một lon theo thời gian từ /vision/objects."""

    def __init__(self, obj_name):
        super().__init__('measure_belt_speed')
        self._name = obj_name
        self.track = []                      # (t, x, y) hệ ảo, chỉ khung tin cậy
        self.create_subscription(Detection3DArray, '/vision/objects', self._on_objects, 10)

    def _on_objects(self, msg):
        for d in msg.detections:
            if d.id != self._name or not d.results:
                continue
            if d.results[0].hypothesis.score <= 0.0:
                return                       # không tin cậy: bỏ, đừng vẽ đường bằng số liệu xấu
            p = d.bbox.center.position
            self.track.append((time.monotonic(), p.x, p.y))
            return


def open_belt(port_name):
    """Mở cổng serial tới Arduino băng tải."""
    if port_name == 'auto':
        found = sorted(glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*'))
        if not found:
            raise SystemExit('Khong thay cong serial. Da cam Arduino chua?')
        port_name = found[0]
    port = serial.Serial(port_name, BAUD, timeout=0.3)
    time.sleep(2.5)                          # mo cong lam Arduino reset
    port.reset_input_buffer()
    return port, port_name


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--object', default=OBJECTS[0].name)
    ap.add_argument('--port', default='auto')
    ap.add_argument('--speed', type=int, default=255)
    args = ap.parse_args()

    port, port_name = open_belt(args.port)
    print(f'Bang tai tren {port_name}, PWM {args.speed}')
    port.write(f'V{args.speed}'.encode())
    time.sleep(0.3)

    rclpy.init()
    node = BeltWatcher(args.object)
    spin = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin.start()

    print(f'Cho camera thay lon "{args.object}"...')
    deadline = time.monotonic() + 10.0
    while not node.track and time.monotonic() < deadline:
        time.sleep(0.1)
    if not node.track:
        port.close()
        raise SystemExit(f'Camera khong thay "{args.object}". Dat lon vao dau nap roi chay lai.')
    start = node.track[-1]
    print(f'Thay lon tai x={start[1]*SCALE*1000:+.0f} y={start[2]*SCALE*1000:+.0f} mm that.')

    stop_flag = threading.Event()

    def beat():
        while not stop_flag.wait(0.5):
            port.write(b'R')

    print('Cho bang CHAY. Theo doi lon...')
    port.write(b'R')
    threading.Thread(target=beat, daemon=True).start()
    run_start = time.monotonic()
    node.track.clear()

    last_move = time.monotonic()
    last_pos = None
    while time.monotonic() - run_start < MAX_RUN_SEC:
        time.sleep(0.1)
        if not node.track:
            continue
        _, x, y = node.track[-1]
        if last_pos is None or abs(y - last_pos) > MOVE_EPS:
            if last_pos is not None:
                last_move = time.monotonic()
            last_pos = y
        if time.monotonic() - last_move > SETTLED_SEC and len(node.track) > 5:
            print('Lon da dung lai.')
            break
    else:
        print(f'Het {MAX_RUN_SEC:.0f}s ma lon chua dung. Dung bang.')

    stop_flag.set()
    time.sleep(0.1)
    port.write(b'S')
    time.sleep(0.3)
    port.close()

    track = list(node.track)
    rclpy.shutdown()

    if len(track) < 5:
        raise SystemExit(f'Chi co {len(track)} khung tin cay — khong du de do.')

    # Tốc độ: lấy đoạn lon ĐANG dịch (bỏ phần đứng yên ở cuối) rồi khớp đường thẳng y theo t.
    moving = [p for p in track if abs(p[2] - track[-1][2]) > MOVE_EPS]
    print(f'\n{len(track)} khung tin cay, {len(moving)} khung lon dang dich.')
    if len(moving) >= 3:
        t0 = moving[0][0]
        ts = [p[0] - t0 for p in moving]
        ys = [p[2] for p in moving]
        n = len(ts)
        mt, my = sum(ts) / n, sum(ys) / n
        var = sum((t - mt) ** 2 for t in ts)
        slope = sum((t - mt) * (y - my) for t, y in zip(ts, ys)) / var if var else 0.0
        print(f'TOC DO BANG: {abs(slope) * SCALE * 1000:.0f} mm that/giay '
              f'({abs(slope) * 1000:.1f} mm ao/giay), do tren {ts[-1]:.1f}s')
        travel = abs(moving[-1][2] - moving[0][2]) * SCALE * 1000
        print(f'  quang duong quan sat duoc: {travel:.0f} mm that')
    else:
        print('Lon dich qua it de do toc do — co the no da o cuoi bang san.')

    # Điểm gắp thật: trung vị mấy khung cuối, lúc lon đã đứng.
    tail = track[-5:]
    fx = sorted(p[1] for p in tail)[len(tail) // 2]
    fy = sorted(p[2] for p in tail)[len(tail) // 2]
    print(f'\nDIEM GAP THAT (lon tu dung): x={fx * SCALE * 1000:+.1f} '
          f'y={fy * SCALE * 1000:+.1f} mm that')
    print(f'                              x={fx * 1000:+.1f} y={fy * 1000:+.1f} mm ao')
    print(f'scene.BELT_PICK_XY dang la:   x={BELT_PICK_XY[0] * 1000:+.1f} '
          f'y={BELT_PICK_XY[1] * 1000:+.1f} mm ao')
    gap = (fy - BELT_PICK_XY[1]) * SCALE * 1000
    print(f'Lech theo Y: {gap:+.1f} mm that')
    if abs(gap) > 10.0:
        print(f'=> Nen sua scene.REAL_BELT_PICK_Y: {REAL_BELT_PICK_Y:.4f} -> {fy * SCALE:.4f}')
    else:
        print('=> Trong 10 mm, giu nguyen.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
