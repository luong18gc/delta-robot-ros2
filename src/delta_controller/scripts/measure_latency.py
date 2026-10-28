#!/usr/bin/env python3
"""
Đo ĐỘ TRỄ ĐẦU-CUỐI của chuỗi nhận thức — số liệu cho khóa luận, cần camera và băng tải còn lắp.

    # hệ thống phải đang chạy: ros2 launch delta_controller conveyor_cycle.launch.py
    python3 src/delta_controller/scripts/measure_latency.py

VÌ SAO CẦN BĂNG TẢI ĐỂ ĐO: độ trễ là khoảng cách giữa lúc THẾ GIỚI đổi và lúc MÔ HÌNH biết điều
đó. Muốn đo thì phải biết chính xác thời điểm thế giới đổi — mà dùng tay đẩy vật thì không ai biết
tay bắt đầu đẩy lúc nào. Băng tải giải được: chính máy tính ra lệnh cho băng chạy, nên thời điểm
vật bắt đầu dịch là thời điểm GỬI LỆNH, biết tới từng mili giây.

Đo ba mốc, tách được ba chặng trễ khác nhau:

    t0  gửi lệnh chạy băng              <- thế giới bắt đầu đổi
    t1  `/vision/objects` thấy vật dịch <- khâu nhận thức đã biết
    t2  vật ảo trong mô phỏng dịch      <- mô hình đã đổi theo

    t1 − t0 : trễ của khâu NHẬN THỨC (phơi sáng + truyền ảnh + xử lý + ngưỡng phát hiện dịch)
    t2 − t1 : trễ của khâu ĐỒNG BỘ (lọc tin cậy + ngưỡng ghi + gọi dịch vụ)
    t2 − t0 : trễ TOÀN CHUỖI — con số đi vào khóa luận

⚠️ Cận trên chứ không phải giá trị đúng tuyệt đối: trong t1 − t0 có cả thời gian động cơ khởi
động và thời gian vật dịch đủ xa để vượt ngưỡng phát hiện. Cả hai đều làm con số ĐO ĐƯỢC lớn hơn
độ trễ thật, nên kết quả là một cận trên an toàn — nói "không quá X ms" thì luôn đúng.
"""

import argparse
import glob
import json
import math
import os
import statistics
import sys
import threading
import time

sys.path.insert(0, __file__.rsplit('/scripts/', 1)[0])

from delta_controller.scene import OBJECTS, SCALE                  # noqa: E402
from nav_msgs.msg import Odometry                                  # noqa: E402
import rclpy                                                       # noqa: E402
from rclpy.node import Node                                        # noqa: E402
import serial                                                      # noqa: E402
from vision_msgs.msg import Detection3DArray                       # noqa: E402

RESULT = os.path.join(__file__.rsplit('/src/', 1)[0], 'docs', 'results', 'latency.json')
BAUD = 115200
MOVE_MM = 3.0          # vật phải dịch bấy nhiêu mm THẬT mới coi là "đã thấy dịch"
BURST_SEC = 2.5        # mỗi lượt cho băng chạy bao lâu
SETTLE_SEC = 2.5
BASE_Z = 1.0


class Watcher(Node):
    """Ghi mốc thời gian khi vật dịch, ở cả hai nơi: camera và mô phỏng."""

    def __init__(self, name):
        super().__init__('measure_latency')
        self._name = name
        self._lock = threading.Lock()
        self.vision = []       # (t, x, y) hệ mô phỏng
        self.gazebo = []
        self.create_subscription(Detection3DArray, '/vision/objects', self._on_vision, 20)
        self.create_subscription(Odometry, f'/objects/{name}/odometry', self._on_gazebo, 20)

    def _on_vision(self, msg):
        for det in msg.detections:
            if det.id == self._name and det.results and det.results[0].hypothesis.score > 0.0:
                p = det.bbox.center.position
                with self._lock:
                    self.vision.append((time.monotonic(), p.x, p.y))

    def _on_gazebo(self, msg):
        p = msg.pose.pose.position
        with self._lock:
            self.gazebo.append((time.monotonic(), p.x, p.y))

    def clear(self):
        with self._lock:
            self.vision.clear()
            self.gazebo.clear()

    def first_move(self, series, origin, after):
        """Mốc đầu tiên SAU `after` mà vật đã dịch quá ngưỡng; None nếu chưa thấy."""
        with self._lock:
            rows = list(series)
        for t, x, y in rows:
            if t < after:
                continue
            if math.hypot(x - origin[0], y - origin[1]) * SCALE * 1000 >= MOVE_MM:
                return t
        return None

    def resting(self, series):
        with self._lock:
            rows = list(series)[-5:]
        if not rows:
            return None
        return (statistics.median(r[1] for r in rows), statistics.median(r[2] for r in rows))


def open_belt(port_name):
    if port_name == 'auto':
        found = sorted(glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*'))
        if not found:
            raise SystemExit('Khong thay cong serial. Da cam Arduino chua?')
        port_name = found[0]
    port = serial.Serial(port_name, BAUD, timeout=0.3)
    time.sleep(2.5)                       # mở cổng làm vi điều khiển khởi động lại
    port.reset_input_buffer()
    return port, port_name


def keep_running(port, stop):
    """Nhắc lại lệnh chạy mỗi nửa giây cho tới khi được bảo dừng."""
    while not stop.wait(0.5):
        port.write(b'R')


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--object', default=OBJECTS[0].name)
    ap.add_argument('--port', default='auto')
    ap.add_argument('--bursts', type=int, default=8, help='số lượt đo')
    args = ap.parse_args()

    port, port_name = open_belt(args.port)
    print(f'Băng tải trên {port_name}. Đặt MỘT vật vào đầu nạp của băng rồi nhấn Enter.')
    input()

    rclpy.init()
    node = Watcher(args.object)
    threading.Thread(target=rclpy.spin, args=(node,), daemon=True).start()
    time.sleep(2.0)

    samples = []
    beat = threading.Event()

    for i in range(args.bursts):
        time.sleep(SETTLE_SEC)
        origin_v = node.resting(node.vision)
        origin_g = node.resting(node.gazebo)
        if origin_v is None or origin_g is None:
            print(f'  lượt {i + 1}: chưa thấy vật, bỏ qua')
            continue
        origin_g = (origin_g[0], origin_g[1])
        node.clear()
        time.sleep(0.4)

        t0 = time.monotonic()
        port.write(b'R')
        # Nhắc lại lệnh chạy, vì lưới an toàn của băng hết hạn sau 3 giây (xem conveyor_arduino).
        beat.clear()
        keep = threading.Thread(target=keep_running, args=(port, beat), daemon=True)
        keep.start()
        time.sleep(BURST_SEC)
        beat.set()
        keep.join(timeout=1.0)
        port.write(b'S')

        t1 = node.first_move(node.vision, origin_v, t0)
        t2 = node.first_move(node.gazebo, origin_g, t0)
        if t1 is None or t2 is None:
            print(f'  lượt {i + 1}: vật chưa dịch đủ {MOVE_MM:.0f} mm, bỏ qua')
            continue
        samples.append({'nhan_thuc_ms': (t1 - t0) * 1000,
                        'dong_bo_ms': (t2 - t1) * 1000,
                        'toan_chuoi_ms': (t2 - t0) * 1000})
        print(f'  lượt {i + 1}: nhận thức {(t1 - t0) * 1000:6.0f} ms | '
              f'đồng bộ {(t2 - t1) * 1000:6.0f} ms | toàn chuỗi {(t2 - t0) * 1000:6.0f} ms')

    port.write(b'S')
    port.close()

    if len(samples) < 2:
        node.destroy_node()
        rclpy.shutdown()
        raise SystemExit('Khong du mau. Vat con tren bang khong? Bang co chay khong?')

    print(f'\n=== ĐỘ TRỄ, {len(samples)} lượt đo ===')
    print(f'{"chặng":16s} {"trung bình":>12s} {"độ lệch chuẩn":>15s} {"nhỏ nhất":>10s} '
          f'{"lớn nhất":>10s}')
    summary = {}
    for key, label in (('nhan_thuc_ms', 'nhận thức'), ('dong_bo_ms', 'đồng bộ'),
                       ('toan_chuoi_ms', 'TOÀN CHUỖI')):
        vals = [s[key] for s in samples]
        summary[key] = {'n': len(vals), 'tb': round(statistics.mean(vals), 1),
                        'sigma': round(statistics.stdev(vals), 1),
                        'min': round(min(vals), 1), 'max': round(max(vals), 1)}
        print(f'{label:16s} {statistics.mean(vals):9.0f} ms {statistics.stdev(vals):12.0f} ms '
              f'{min(vals):7.0f} ms {max(vals):7.0f} ms')
    print(f'\n⚠️ Đây là CẬN TRÊN: trong chặng nhận thức có cả thời gian động cơ khởi động và thời '
          f'gian vật dịch đủ {MOVE_MM:.0f} mm để vượt ngưỡng phát hiện.')

    try:
        os.makedirs(os.path.dirname(RESULT), exist_ok=True)
        with open(RESULT, 'w', encoding='utf-8') as fh:
            json.dump({'do_luc': time.strftime('%Y-%m-%d %H:%M'), 'vat': args.object,
                       'nguong_dich_mm': MOVE_MM, 'tong_hop': summary, 'mau': samples},
                      fh, ensure_ascii=False, indent=2)
        print(f'Đã ghi {RESULT}')
    except OSError as err:                                         # noqa: BLE001 — chỉ là tiện ích
        print(f'(không ghi được tệp kết quả: {err})')
    node.destroy_node()
    rclpy.shutdown()
    return 0


if __name__ == '__main__':
    sys.exit(main())
