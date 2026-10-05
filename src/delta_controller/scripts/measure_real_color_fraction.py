#!/usr/bin/env python3
"""
Đo TỈ LỆ MÀU DANH NGHĨA của LON THẬT, quét qua nhiều vị trí trên bàn (Bước 10a).

    python3 src/delta_controller/scripts/measure_real_color_fraction.py

Đặt lon lên bàn rồi DI CHUYỂN chúng khắp vùng làm việc trong lúc script chạy. Cửa sổ camera hiện
vùng màu đang bắt được và số mẫu đã thu của từng lon, nên nhìn là biết lon có đang bị che không.
Bấm `q` (hoặc Ctrl+C) để kết thúc và xem kết luận.

Vì sao phải quét nhiều vị trí thay vì đo một chỗ: tỉ lệ này KHÔNG phải hằng số. Phép đóng hình thái
học lấp vành nhãn nhiều hay ít tùy ảnh lon to hay nhỏ, nên lon càng xa camera tỉ lệ càng cao — đo
trong mô phỏng 2026-09-29 thấy chênh 0.67–0.80 trên cùng một vật.

Lấy giá trị NHỎ NHẤT điền vào `scene.REAL_COLOR_FRACTION`: khai thấp thì lon lành lặn không bao giờ
bị cờ tin cậy từ chối; khai cao thì lon tử tế cũng bị coi là bị che và robot không chịu gắp.

⚠️ CHỈ di chuyển lon khi chúng KHÔNG che nhau và không bị tay che — đang đo lon lành lặn trông như
thế nào, nên mọi khung bị che sẽ kéo kết quả xuống sai.
"""

import argparse
import collections
import signal
import sys

import _workspace  # noqa: F401
import cv2
from delta_controller import usb_camera
from delta_controller.color_detector import detect_objects, draw_detections
from delta_controller.real_camera import aruco_detector, PoseTracker, table_roi_mask
from delta_controller.scene import REAL_COLOR_FRACTION, REAL_OBJECTS, SCALE
from delta_controller.vision_estimation import estimate_object, silhouette_features
import numpy as np
import yaml

WS = '/home/luong18gc/ros2_closed_loop_ws'
INTRINSICS = f'{WS}/calibration/c270_intrinsics.yaml'


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--device', default='auto')
    ap.add_argument('--intrinsics', default=INTRINSICS)
    ap.add_argument('--min-move', type=float, default=40.0,
                    help='chi ghi mau khi lon da dich chuyen bay nhieu mm (tranh dem trung cho)')
    ap.add_argument('--smooth', type=int, default=5,
                    help='lay trung vi bay nhieu khung truoc khi xet da dich chuyen chua')
    ap.add_argument('--no-window', action='store_true', help='chi in ra terminal, khong mo cua so')
    args = ap.parse_args()

    with open(args.intrinsics) as f:
        data = yaml.safe_load(f)
    K = np.array(data['camera']['K'], float)
    dist = np.array(data['camera']['dist'], float)

    device = usb_camera.resolve_device(args.device)
    mode = usb_camera.best_mjpg_mode(device)
    usb_camera.lock_manual(device, log=lambda _: None)
    cap = usb_camera.open_camera(device, mode[0], mode[1])
    usb_camera.warm_up(cap)
    tracker = PoseTracker(K, dist)
    detector = aruco_detector()
    objects = {o.color: o for o in REAL_OBJECTS}

    samples = {o.name: [] for o in REAL_OBJECTS}
    last_at = {}
    # Lọc trung vị trước khi hỏi "đã dịch chưa": ước lượng của lon đứng YÊN vẫn nhảy tới 48 mm
    # giữa hai khung (đo 2026-10-05 trên lon 7Up thật — màu chỉ còn vành trên nên mép đáy không
    # ổn định). Không lọc thì script đếm mẫu liên tục dù lon không nhúc nhích.
    recent = collections.defaultdict(lambda: collections.deque(maxlen=max(1, args.smooth)))
    stop = []
    signal.signal(signal.SIGINT, lambda *_: stop.append(True))
    title = 'do ti le mau - q de ket thuc'
    if not args.no_window:
        cv2.namedWindow(title, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(title, 960, 540)
    print('Di chuyen lon khap vung lam viec. Bam q tren cua so (hoac Ctrl+C) de ket thuc.')
    print('(chi di chuyen khi lon KHONG che nhau va khong bi tay che)\n')

    while not stop:
        ok, frame = cap.read()
        if not ok:
            continue
        tracker.update(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), detector)
        if not tracker.ready:
            continue
        roi = table_roi_mask(tracker.model, frame.shape)
        found = detect_objects(cv2.bitwise_and(frame, frame, mask=roi))
        labels, line = {}, []
        for color, det in found.items():
            obj = objects.get(color)
            if obj is None:
                continue
            est = estimate_object(det, tracker.model, obj, frame.shape)
            recent[obj.name].append(np.array(est.position[:2]) * 1000 * SCALE)
            here = np.median(np.array(recent[obj.name]), axis=0)
            area, _, _ = silhouette_features(tracker.model, obj, est.position)
            ratio = det.area / area if area > 0 else 0.0
            before = last_at.get(obj.name)
            moved = before is None or np.linalg.norm(here - before) >= args.min_move
            if moved and area > 0:
                last_at[obj.name] = here
                samples[obj.name].append(ratio)
            n = len(samples[obj.name])
            labels[color] = (f'{obj.name.split("_")[0]} {n} mau | ti le {ratio:.2f}'
                             + ('' if moved else ' (chua di chuyen)'))
            line.append(f'{obj.name.split("_")[0]} {n:3d}')
        if line:
            print('\r  so mau: ' + ' | '.join(line) + '   ', end='', flush=True)
        if not args.no_window:
            view = draw_detections(frame, found, labels=labels)
            edge = cv2.morphologyEx(roi, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
            view[edge > 0] = (80, 80, 255)
            missing = [o.name.split('_')[0] for o in REAL_OBJECTS if o.color not in found]
            text = ('THIEU: ' + ', '.join(missing)) if missing else 'thay du 3 lon'
            cv2.putText(view, text, (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4)
            cv2.putText(view, text, (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (0, 220, 0) if not missing else (0, 160, 255), 1)
            cv2.imshow(title, view)
            if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
                break
    cap.release()
    cv2.destroyAllWindows()

    print('\n\nvat           so mau   nho nhat   trung vi   lon nhat   dang khai bao')
    for name, values in samples.items():
        if len(values) < 5:
            print(f'  {name:12s} {len(values):5d}   (chua du mau, can >= 5)')
            continue
        v = np.array(values)
        print(f'  {name:12s} {len(v):5d}     {v.min():5.2f}      {np.median(v):5.2f}      '
              f'{v.max():5.2f}        {REAL_COLOR_FRACTION.get(name, 1.0):5.2f}')
    print('\nDien gia tri NHO NHAT vao scene.REAL_COLOR_FRACTION.')


if __name__ == '__main__':
    sys.exit(main())
