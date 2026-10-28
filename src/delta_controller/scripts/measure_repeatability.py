#!/usr/bin/env python3
"""
Đo ĐỘ LẶP LẠI của khâu thị giác — số liệu cho khóa luận, cần camera thật còn lắp.

    # hệ thống phải đang chạy: ros2 launch delta_controller digital_twin.launch.py
    python3 src/delta_controller/scripts/measure_repeatability.py            # tự động
    python3 src/delta_controller/scripts/measure_repeatability.py --rounds 10   # có đặt lại vật

Sai số trung bình trả lời "phép đo đúng tới đâu", còn ĐỘ LẶP LẠI trả lời một câu khác và hội đồng
hay hỏi: "đo lại nhiều lần thì kết quả có như nhau không". Hai đại lượng độc lập — một phép đo có
thể lệch đều 10 mm mà rất ổn định, hoặc đúng trung bình mà tản mạn ±20 mm.

Script đo HAI mức, vì chúng tách được hai nguồn tản mạn khác nhau:

1. **Độ ổn định của phép đo** (tự động, không cần làm gì): vật đứng yên, lấy N khung liên tiếp.
   Phần tản mạn ở đây hoàn toàn do nhiễu ảnh và thuật toán, KHÔNG có sai số đặt vật.
2. **Độ lặp lại khi đặt lại vật** (`--rounds K`): mỗi vòng bạn nhấc vật lên rồi đặt lại vào đúng
   dấu cũ. Phần tản mạn giữa các vòng gồm cả sai số của tay người — đây mới là con số mà một dây
   chuyền thật phải sống chung.

Mức 2 bao giờ cũng lớn hơn mức 1; hiệu giữa chúng cho biết bao nhiêu phần là do hệ thống và bao
nhiêu là do thao tác đặt vật.
"""

import argparse
import json
import math
import os
import statistics
import sys
import threading
import time

sys.path.insert(0, __file__.rsplit('/scripts/', 1)[0])

from delta_controller.scene import SCALE                           # noqa: E402
import rclpy                                                       # noqa: E402
from rclpy.node import Node                                        # noqa: E402
from vision_msgs.msg import Detection3DArray                       # noqa: E402

RESULT = os.path.join(__file__.rsplit('/src/', 1)[0], 'docs', 'results', 'repeatability.json')
SETTLE_SEC = 1.0


class Sampler(Node):
    """Thu vị trí vật từ `/vision/objects`, chỉ giữ khung được gắn cờ tin cậy."""

    def __init__(self):
        super().__init__('measure_repeatability')
        self.frames = []
        self.create_subscription(Detection3DArray, '/vision/objects', self._on_objects, 20)

    def _on_objects(self, msg):
        entry = {}
        for det in msg.detections:
            if det.results and det.results[0].hypothesis.score > 0.0:
                p = det.bbox.center.position
                entry[det.id] = (p.x, p.y)
        if entry:
            self.frames.append((time.monotonic(), entry))

    def collect(self, count, timeout=25.0):
        """Chờ tới khi có `count` khung MỚI; trả về {tên -> [(x, y), ...]}."""
        self.frames.clear()
        deadline = time.monotonic() + timeout
        while len(self.frames) < count and time.monotonic() < deadline:
            time.sleep(0.05)
        out = {}
        for _, entry in self.frames[:count]:
            for name, xy in entry.items():
                out.setdefault(name, []).append(xy)
        return out


def spread(points):
    """
    (độ lệch chuẩn theo x, theo y, bán kính trung bình quanh tâm) — đơn vị mm THẬT.

    Dùng bán kính quanh tâm chứ không chỉ σ từng trục vì sai số định vị là đại lượng HAI CHIỀU;
    hội đồng quan tâm "lệch bao xa", không phải lệch theo trục nào.
    """
    xs = [p[0] * SCALE * 1000 for p in points]
    ys = [p[1] * SCALE * 1000 for p in points]
    if len(points) < 2:
        return 0.0, 0.0, 0.0, 0.0
    cx, cy = statistics.mean(xs), statistics.mean(ys)
    radii = [math.hypot(x - cx, y - cy) for x, y in zip(xs, ys)]
    return (statistics.stdev(xs), statistics.stdev(ys),
            statistics.mean(radii), max(radii))


def report(title, per_object, note):
    print(f'\n=== {title} ===')
    print(f'{"vật":14s} {"n":>3s} {"σx":>7s} {"σy":>7s} {"bán kính TB":>12s} {"lớn nhất":>10s}')
    rows = {}
    for name in sorted(per_object):
        points = per_object[name]
        sx, sy, mean_r, max_r = spread(points)
        rows[name] = {'n': len(points), 'sigma_x_mm': round(sx, 2), 'sigma_y_mm': round(sy, 2),
                      'ban_kinh_tb_mm': round(mean_r, 2), 'lon_nhat_mm': round(max_r, 2)}
        print(f'{name:14s} {len(points):3d} {sx:7.2f} {sy:7.2f} {mean_r:12.2f} {max_r:10.2f}')
    print(f'  ({note}; đơn vị mm THẬT trên mặt bàn)')
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--frames', type=int, default=40, help='số khung cho phép đo tự động')
    ap.add_argument('--rounds', type=int, default=0,
                    help='số lần nhấc và đặt lại vật (0 = bỏ qua phần này)')
    ap.add_argument('--per-round', type=int, default=10, help='số khung lấy trong mỗi vòng')
    args = ap.parse_args()

    rclpy.init()
    node = Sampler()
    threading.Thread(target=rclpy.spin, args=(node,), daemon=True).start()

    print('Đặt vật lên bàn (hoặc lên băng) rồi để yên. Nhấn Enter để bắt đầu.')
    input()

    result = {'do_luc': time.strftime('%Y-%m-%d %H:%M'), 'so_khung': args.frames}
    auto = node.collect(args.frames)
    if not auto:
        raise SystemExit('Khong nhan duoc khung tin cay nao — he thong co dang chay khong?')
    result['on_dinh_phep_do'] = report(
        'MỨC 1 — độ ổn định của phép đo (vật đứng yên)', auto,
        'vật không bị đụng tới, nên tản mạn chỉ do nhiễu ảnh và thuật toán')

    if args.rounds:
        print(f'\nMỨC 2 — đặt lại vật {args.rounds} lần. Mỗi vòng: NHẤC vật lên, ĐẶT lại vào '
              f'đúng dấu cũ, rồi nhấn Enter.')
        rounds = {}
        for i in range(args.rounds):
            input(f'  vòng {i + 1}/{args.rounds} — đặt xong rồi nhấn Enter... ')
            time.sleep(SETTLE_SEC)
            seen = node.collect(args.per_round)
            for name, points in seen.items():
                # Trung vị trong một vòng để nhiễu khung không lẫn vào tản mạn GIỮA các vòng.
                rounds.setdefault(name, []).append(
                    (statistics.median(p[0] for p in points),
                     statistics.median(p[1] for p in points)))
        result['lap_lai_khi_dat_lai'] = report(
            'MỨC 2 — độ lặp lại khi đặt lại vật', rounds,
            'gồm cả sai số của thao tác đặt vật bằng tay')

        print('\nSo sánh hai mức: phần vượt của mức 2 so với mức 1 là do thao tác đặt vật,')
        print('phần còn lại là của hệ thống.')

    try:
        os.makedirs(os.path.dirname(RESULT), exist_ok=True)
        with open(RESULT, 'w', encoding='utf-8') as fh:
            json.dump(result, fh, ensure_ascii=False, indent=2)
        print(f'\nĐã ghi {RESULT}')
    except OSError as err:                                         # noqa: BLE001 — chỉ là tiện ích
        print(f'(không ghi được tệp kết quả: {err})')
    node.destroy_node()
    rclpy.shutdown()
    return 0


if __name__ == '__main__':
    sys.exit(main())
