#!/usr/bin/env python3
"""
Đo TỈ LỆ MÀU DANH NGHĨA của LON THẬT, quét qua nhiều vị trí trên bàn (Bước 10a).

    python3 src/delta_controller/scripts/measure_real_color_fraction.py

Đặt lon lên bàn rồi DI CHUYỂN chúng khắp vùng làm việc trong lúc script chạy. Nó đo liên tục tỉ lệ
(diện tích pixel mang màu / diện tích hình bóng dự đoán) và in ra nhỏ nhất / trung vị / lớn nhất
cho từng lon. Ctrl+C để kết thúc và xem kết luận.

Vì sao phải quét nhiều vị trí thay vì đo một chỗ: tỉ lệ này KHÔNG phải hằng số. Phép đóng hình thái
học lấp vành nhãn nhiều hay ít tùy ảnh lon to hay nhỏ, nên lon càng xa camera tỉ lệ càng cao — đo
trong mô phỏng 2026-09-29 thấy chênh 0.67–0.80 trên cùng một vật.

Lấy giá trị NHỎ NHẤT điền vào `scene.REAL_COLOR_FRACTION`: khai thấp thì lon lành lặn không bao giờ
bị cờ tin cậy từ chối; khai cao thì lon tử tế cũng bị coi là bị che và robot không chịu gắp.

⚠️ CHỈ di chuyển lon khi chúng KHÔNG che nhau và không bị tay che — đang đo lon lành lặn trông như
thế nào, nên mọi khung bị che sẽ kéo kết quả xuống sai.
"""

import argparse
import signal
import sys

import _workspace  # noqa: F401
import cv2
from delta_controller import usb_camera
from delta_controller.color_detector import detect_objects
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
    ap.add_argument('--min-move', type=float, default=15.0,
                    help='chi ghi mau khi lon da dich chuyen bay nhieu mm (tranh dem trung cho)')
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
    stop = []
    signal.signal(signal.SIGINT, lambda *_: stop.append(True))
    print('Di chuyen lon khap vung lam viec. Ctrl+C de ket thuc.')
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
        line = []
        for color, det in found.items():
            obj = objects.get(color)
            if obj is None:
                continue
            est = estimate_object(det, tracker.model, obj, frame.shape)
            here = np.array(est.position[:2]) * 1000 * SCALE
            before = last_at.get(obj.name)
            if before is not None and np.linalg.norm(here - before) < args.min_move:
                continue
            last_at[obj.name] = here
            area, _, _ = silhouette_features(tracker.model, obj, est.position)
            if area > 0:
                samples[obj.name].append(det.area / area)
            line.append(f'{obj.name.split("_")[0]} {len(samples[obj.name]):3d}')
        if line:
            print('\r  so mau: ' + ' | '.join(line) + '   ', end='', flush=True)
    cap.release()

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
