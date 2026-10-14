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
import json
import os
import sys
import threading
import time

sys.path.insert(0, __file__.rsplit('/scripts/', 1)[0])

from delta_controller.scene import (            # noqa: E402
    BELT_CENTER, BELT_LENGTH, BELT_PICK_XY, OBJECTS, REAL_BELT_PICK_Y, SCALE,
)
import rclpy                                    # noqa: E402
from rclpy.node import Node                     # noqa: E402
import serial                                   # noqa: E402
from vision_msgs.msg import Detection3DArray    # noqa: E402

BAUD = 115200
RESULT_FILE = os.path.join(__file__.rsplit('/src/', 1)[0],
                           'docs', 'results', 'belt_calibration.json')
SETTLED_SEC = 1.5          # đứng yên bao lâu thì coi là đã tới cuối
MOVE_EPS = 0.0015          # m ảo: dịch dưới mức này coi như đứng yên (nhiễu đo 0.5-0.9 mm thật)
MAX_RUN_SEC = 30.0
# Dừng băng khi lon còn cách mép băng chừng này. Cuối băng KHÔNG có vật chặn: 2026-10-14 lon chạy
# quá đầu băng và rơi xuống bàn. Không chờ lon "tự dừng" được, vì nó không bao giờ tự dừng.
# 25 mm thật = quãng cho camera 10 Hz kịp thấy + lệnh kịp tới + lon kịp trôi nốt theo quán tính.
STOP_MARGIN = 0.025 / SCALE          # m ảo
DIRECTION_FRAMES = 4       # số khung để biết lon chạy về phía nào
SETTLE_AFTER_STOP = 2.5    # giây chờ lon trôi nốt sau khi băng dừng


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

    # Biết lon chạy về phía nào rồi mới biết mép nào là mép nguy hiểm — không giả định chiều,
    # vì chiều băng là thứ vừa mới đổi quy ước hôm qua.
    far_end = None
    last_move = time.monotonic()
    last_pos = None
    reason = 'het gio'
    while time.monotonic() - run_start < MAX_RUN_SEC:
        time.sleep(0.05)
        if not node.track:
            continue
        _, x, y = node.track[-1]

        if far_end is None and len(node.track) >= DIRECTION_FRAMES:
            moved = node.track[-1][2] - node.track[0][2]
            if abs(moved) > MOVE_EPS:
                sign = 1.0 if moved > 0 else -1.0
                far_end = BELT_CENTER[1] + sign * BELT_LENGTH / 2.0
                print(f'  lon chay ve phia {"+Y" if sign > 0 else "-Y"}, '
                      f'mep bang o y={far_end * SCALE * 1000:+.0f} mm that')

        if far_end is not None:
            remaining = (far_end - y) if far_end > BELT_CENTER[1] else (y - far_end)
            if remaining <= STOP_MARGIN:
                reason = 'lon sap toi mep bang'
                break

        if last_pos is None or abs(y - last_pos) > MOVE_EPS:
            if last_pos is not None:
                last_move = time.monotonic()
            last_pos = y
        if time.monotonic() - last_move > SETTLED_SEC and len(node.track) > 5:
            reason = 'lon da dung lai'
            break
    print(f'Dung bang: {reason}.')

    stop_flag.set()
    time.sleep(0.1)
    port.write(b'S')
    at_stop = node.track[-1] if node.track else None
    # Lon KHÔNG đứng ngay khi băng dừng — nó còn trôi. Quãng trôi đó là số máy trạng thái cần:
    # muốn lon dừng ĐÚNG điểm gắp thì phải ra lệnh dừng sớm trước đúng quãng này.
    print('Cho lon dung han...')
    time.sleep(SETTLE_AFTER_STOP)
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
        speed_real = abs(slope) * SCALE * 1000
        print(f'TOC DO BANG: {speed_real:.0f} mm that/giay '
              f'({abs(slope) * 1000:.1f} mm ao/giay), do tren {ts[-1]:.1f}s')
        travel = abs(moving[-1][2] - moving[0][2]) * SCALE * 1000
        print(f'  quang duong quan sat duoc: {travel:.0f} mm that')
    else:
        speed_real = None
        print('Lon dich qua it de do toc do — co the no da o cuoi bang san.')

    coast = None
    if at_stop is not None:
        coast = abs(track[-1][2] - at_stop[2]) * SCALE * 1000
        print(f'\nQUANG TROI sau khi ra lenh dung: {coast:.0f} mm that')
        print('  => may trang thai phai ra lenh dung SOM truoc diem gap dung quang nay.')

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

    # Ghi ra file: ba con số này đi vào máy trạng thái, để chúng trôi trong màn hình là mất.
    result = {
        'do_luc': time.strftime('%Y-%m-%d %H:%M'),
        'pwm': args.speed,
        'vat': args.object,
        'toc_do_mm_s_that': round(speed_real, 1) if speed_real is not None else None,
        'quang_troi_mm_that': round(coast, 1) if coast is not None else None,
        'diem_gap_that_mm': [round(fx * SCALE * 1000, 1), round(fy * SCALE * 1000, 1)],
        'diem_gap_ao_m': [round(fx, 5), round(fy, 5)],
        'so_khung_tin_cay': len(track),
    }
    try:
        os.makedirs(os.path.dirname(RESULT_FILE), exist_ok=True)
        with open(RESULT_FILE, 'w', encoding='utf-8') as fh:
            json.dump(result, fh, ensure_ascii=False, indent=2)
        print(f'\nDa ghi {RESULT_FILE}')
    except OSError as err:                           # noqa: BLE001 — chỉ là tiện ích
        print(f'(khong ghi duoc file ket qua: {err})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
