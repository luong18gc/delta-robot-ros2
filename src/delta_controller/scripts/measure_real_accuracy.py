#!/usr/bin/env python3
"""
Đo SAI SỐ THẬT của khối thị giác camera thật, so với vị trí biết trước (Bước 10a).

    python3 src/delta_controller/scripts/measure_real_accuracy.py

Script dẫn từng lượt: in ra chỗ phải đặt từng lon, bạn đặt rồi bấm Enter, nó chụp nhiều khung, lấy
TRUNG VỊ rồi so với vị trí đúng. Cuối cùng in bảng sai số để đối chiếu với 1.13 mm của mô phỏng.

Ba lon đổi chỗ cho nhau qua các lượt, nên mỗi lon được đo ở mọi điểm mà chỉ cần ít lần đặt.

CHUẨN BỊ: dán băng dính đánh dấu các điểm trong bảng dưới lên mặt bàn, đo từ gốc O theo trục X, Y
đã kẻ khi dán marker. Đặt TÂM ĐÁY lon trùng dấu.

⚠️ Vị trí đúng phải đo cẩn thận — sai số của thước đi thẳng vào kết quả. Đánh dấu bằng bút chì mảnh
rồi đặt lon cho mép đáy bao quanh dấu đều nhau.
"""

import argparse
import collections
import sys

import _workspace  # noqa: F401
import cv2
from delta_controller import usb_camera
from delta_controller.color_detector import COLOR_CLASSES
from delta_controller.object_detector import detect_by_color
from delta_controller.real_camera import aruco_detector, PoseTracker, table_roi_mask
from delta_controller.scene import REAL_OBJECTS, SCALE
from delta_controller.vision_estimation import estimate_object
import numpy as np
import yaml

WS = '/home/luong18gc/ros2_closed_loop_ws'
INTRINSICS = f'{WS}/calibration/c270_intrinsics.yaml'
# Sáu điểm phủ vùng đặt lon (x 0…280, y ±190 mm). Mỗi lượt ba lon vào ba điểm, lượt sau đổi vòng,
# nên sau 3 lượt mỗi lon đã qua cả ba điểm của bộ đó.
POINT_SETS = (((20.0, 150.0), (140.0, 0.0), (260.0, -150.0)),
              ((20.0, -150.0), (140.0, 170.0), (260.0, 20.0)))
FRAMES = 15


def measure(cap, tracker, detector, objects, frames):
    """{tên lon: (x, y) mm thật} — trung vị qua `frames` khung."""
    seen = collections.defaultdict(list)
    tries = 0
    while min([len(v) for v in seen.values()] or [0]) < frames and tries < frames * 8:
        tries += 1
        ok, frame = cap.read()
        if not ok:
            continue
        tracker.update(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), detector)
        if not tracker.ready:
            continue
        roi = table_roi_mask(tracker.model, frame.shape)
        for color, det in detect_by_color(frame, COLOR_CLASSES, roi=roi).items():
            obj = objects.get(color)
            if obj is None:
                continue
            est = estimate_object(det, tracker.model, obj, frame.shape)
            if est.reliable:
                seen[obj.name].append(np.array(est.position[:2]) * 1000 * SCALE)
        if len(seen) == len(objects) and min(len(v) for v in seen.values()) >= frames:
            break
    return {n: np.median(np.array(v), axis=0) for n, v in seen.items() if len(v) >= 3}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--device', default='auto')
    ap.add_argument('--intrinsics', default=INTRINSICS)
    ap.add_argument('--frames', type=int, default=FRAMES)
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
    names = [o.name for o in REAL_OBJECTS]

    print(__doc__.split('CHUẨN BỊ:')[1].split('⚠️')[0].strip())
    print('\nCac diem can danh dau (mm, do tu goc O):')
    for pts in POINT_SETS:
        for x, y in pts:
            print(f'   ({x:+6.0f}, {y:+6.0f})')

    rows = []
    for pts in POINT_SETS:
        for turn in range(len(names)):
            truth = {names[i]: pts[(i + turn) % len(pts)] for i in range(len(names))}
            print('\n--- Luot', len(rows) // 3 + 1)
            for n in names:
                print(f'   dat {n:12s} tai ({truth[n][0]:+6.0f}, {truth[n][1]:+6.0f})')
            if input('   xong thi bam Enter (go q de dung): ').strip().lower() == 'q':
                pts = None
                break
            got = measure(cap, tracker, detector, objects, args.frames)
            for n in names:
                if n not in got:
                    print(f'   {n}: KHONG DO DUOC (bi che? ngoai vung xet?)')
                    continue
                err = got[n] - np.array(truth[n])
                rows.append((n, truth[n], got[n], err))
                print(f'   {n:12s} do duoc ({got[n][0]:+6.0f},{got[n][1]:+6.0f})  '
                      f'lech ({err[0]:+5.1f},{err[1]:+5.1f}) = {np.linalg.norm(err):5.1f} mm that'
                      f'  -> {np.linalg.norm(err) / SCALE:4.2f} mm ao')
        if pts is None:
            break
    cap.release()

    if not rows:
        return 1
    print('\n== KET QUA')
    print('vat            so diem   TB (mm ao)   lon nhat   lech he thong X / Y (mm that)')
    for n in names:
        mine = [r for r in rows if r[0] == n]
        if not mine:
            continue
        e = np.array([r[3] for r in mine])
        d = np.linalg.norm(e, axis=1) / SCALE
        print(f'  {n:12s} {len(mine):5d}      {d.mean():6.2f}      {d.max():6.2f}      '
              f'{e[:, 0].mean():+6.1f} / {e[:, 1].mean():+5.1f}')
    allerr = np.linalg.norm(np.array([r[3] for r in rows]), axis=1) / SCALE
    print(f'\n  CHUNG: TB {allerr.mean():.2f} mm ao, lon nhat {allerr.max():.2f} mm '
          f'({len(rows)} phep do)')
    print('  (mo phong dat 1.13 mm; dung sai giac hut 12 mm)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
