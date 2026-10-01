#!/usr/bin/env python3
"""
Đo NGOẠI THAM SỐ camera thật từ 6 marker ArUco trên bàn (Bước 10a).

    python3 src/delta_controller/scripts/calibrate_extrinsics.py            # đo và lưu file
    python3 src/delta_controller/scripts/calibrate_extrinsics.py --watch    # theo dõi liên tục

Cần `calibration/c270_intrinsics.yaml` (chạy calibrate_intrinsics.py trước).

Chế độ mặc định: lấy trung bình nhiều khung rồi ghi `calibration/c270.yaml` — dùng để KIỂM TRA bố
trí đã đúng chưa (vị trí camera đo được có khớp thước đo không, sai số chiếu lại bao nhiêu).

⚠️ Khi VẬN HÀNH thì đừng dựa vào file này: camera xoay 1° là vị trí vật sai 7.7 mm ảo (dung sai
giác hút 12 mm), 2° là hỏng hẳn — mà hỏng không có dấu hiệu gì. Marker nằm cố định trong khung
hình nên khối thị giác sẽ dùng `real_camera.PoseTracker` giải lại tư thế MỖI KHUNG; file này chỉ
là ảnh chụp một thời điểm, tiện cho việc dựng bố trí và viết báo cáo.

Chế độ `--watch` in liên tục vị trí/góc đo được: dùng khi đang vặn giá đỡ, để thấy ngay mình đang
chỉnh tới đâu.
"""

import argparse
import os
import sys
import time

import cv2
from delta_controller.real_camera import (
    aruco_detector,
    detect_marker_centers,
    estimate_extrinsics,
    MIN_MARKERS,
)
from delta_controller.scene import REAL_CALIB_MARKERS, real_calib_markers_virtual, SCALE
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probe_camera as probe   # noqa: E402
import yaml                    # noqa: E402

WS = os.path.expanduser('~/ros2_closed_loop_ws')
INTRINSICS = os.path.join(WS, 'calibration', 'c270_intrinsics.yaml')


def load_intrinsics(path):
    with open(path) as f:
        data = yaml.safe_load(f)
    K = np.array(data['camera']['K'], float)
    dist = np.array(data['camera']['dist'], float)
    return K, dist, data.get('meta', {})


def summarise(found, frames_used, frames_seen):
    """In kết quả kèm số liệu đối chiếu được bằng thước."""
    x, y, z = found.position_real_mm()
    print('\n== KET QUA')
    print(f'  marker dung       {len(found.marker_ids)}/{len(REAL_CALIB_MARKERS)}: '
          f'{", ".join(str(i) for i in found.marker_ids)}')
    print(f'  khung dung        {frames_used}/{frames_seen}')
    print(f'  sai so chieu lai  RMS {found.rms_px:.2f} px  '
          f'(tung marker: {min(found.errors_px):.2f} – {max(found.errors_px):.2f})')
    print(f'  camera o          X {x:+.0f} mm, Y {y:+.0f} mm, cao {z:+.0f} mm so voi mat ban')
    print(f'                    (do bang thuoc de doi chieu: lui {-x:.0f} mm, cao {z:.0f} mm)')
    print(f'  goc chuc xuong    {found.tilt_deg():.1f}°')
    print('\n== DANH GIA')
    ok = True
    if len(found.marker_ids) < len(REAL_CALIB_MARKERS):
        missing = sorted(set(REAL_CALIB_MARKERS) - set(found.marker_ids))
        print(f'  CANH BAO thieu marker {missing} — chinh lai huong camera cho thay DU 6. '
              'Thieu marker thi tu the kem on dinh va de sai khi mot cai bi che.')
    else:
        print('  OK   thay du 6 marker')
    if found.rms_px > 2.0:
        print(f'  LOI  sai so chieu lai {found.rms_px:.2f} px qua lon. Kiem tra: toa do dan '
              'marker co dung bang trong scene.REAL_CALIB_MARKERS khong; marker co phang khong.')
        ok = False
    elif found.rms_px > 1.0:
        print(f'  CANH BAO sai so chieu lai {found.rms_px:.2f} px hoi cao — nen kiem tra lai '
              'toa do dan marker.')
    else:
        print(f'  OK   sai so chieu lai {found.rms_px:.2f} px')
    worst = int(np.argmax(found.errors_px))
    if found.errors_px[worst] > 2 * found.rms_px and found.rms_px > 0.5:
        print(f'  CANH BAO marker {found.marker_ids[worst]} lech han cac marker khac '
              f'({found.errors_px[worst]:.2f} px) — nhieu kha nang dan sai toa do cai do.')
    print('  ' + ('=> DUNG DUOC' if ok else '=> SUA ROI DO LAI'))
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--device', default='auto')
    ap.add_argument('--intrinsics', default=INTRINSICS)
    ap.add_argument('--frames', type=int, default=20, help='so khung lay trung binh')
    ap.add_argument('--watch', action='store_true', help='in lien tuc, khong ghi file')
    ap.add_argument('--name', default='c270', help='ten file ket qua trong calibration/')
    args = ap.parse_args()
    args.device = probe.resolve_device(args.device)

    if not os.path.exists(args.intrinsics):
        sys.exit(f'Chua co {args.intrinsics} — chay calibrate_intrinsics.py truoc.')
    K, dist, meta = load_intrinsics(args.intrinsics)
    print(f'Noi tham so: {args.intrinsics} ({meta.get("width")}x{meta.get("height")}, '
          f'RMS {meta.get("rms_px", 0):.3f} px)')

    mode = probe.best_mjpg_mode(args.device)
    if mode is None:
        sys.exit('Khong doc duoc che do MJPG — camera da cam chua?')
    if (mode[0], mode[1]) != (meta.get('width'), meta.get('height')):
        sys.exit(f'Camera dang o {mode[0]}x{mode[1]} nhung noi tham so hieu chuan o '
                 f'{meta.get("width")}x{meta.get("height")} — K khong dung cho do phan giai khac.')
    probe.lock_manual(args.device, log=lambda _: None)
    cap = probe.open_camera(args.device, mode[0], mode[1])
    probe.warm_up(cap)
    detector = aruco_detector()
    layout = real_calib_markers_virtual()

    try:
        if args.watch:
            print('Theo doi lien tuc (Ctrl+C de dung). Vặn gia do va nhin so thay doi.')
            while True:
                ok, frame = cap.read()
                if not ok:
                    continue
                centers = detect_marker_centers(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
                                                detector, layout)
                if len(centers) < MIN_MARKERS:
                    print(f'\r  chi thay {len(centers)}/6 marker: '
                          f'{sorted(centers)}            ', end='', flush=True)
                    continue
                found = estimate_extrinsics(centers, K, dist, layout)
                x, y, z = found.position_real_mm()
                print(f'\r  {len(found.marker_ids)}/6 marker | lui {-x:4.0f} mm | '
                      f'lech ngang {y:+4.0f} mm | cao {z:4.0f} mm | chuc {found.tilt_deg():4.1f}° '
                      f'| RMS {found.rms_px:4.2f} px   ', end='', flush=True)
                time.sleep(0.1)
        samples, seen = [], 0
        print(f'Lay {args.frames} khung...')
        while len(samples) < args.frames:
            ok, frame = cap.read()
            if not ok:
                continue
            seen += 1
            centers = detect_marker_centers(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
                                            detector, layout)
            if len(centers) >= MIN_MARKERS:
                samples.append(centers)
            elif seen > 20 * args.frames:
                sys.exit(f'Chi thay toi da {len(centers)} marker — camera co nhin thay bo marker '
                         'khong? Dung view_camera.py de ngam.')
    except KeyboardInterrupt:
        print()
        return
    finally:
        cap.release()

    # Trung bình tâm marker qua các khung rồi mới giải PnP một lần: nhiễu nhận góc giảm theo
    # căn số khung, mà PnP vẫn chỉ chạy trên một bộ điểm nhất quán.
    ids = sorted(set.intersection(*(set(s) for s in samples)))
    averaged = {i: tuple(np.mean([s[i] for s in samples], axis=0)) for i in ids}
    found = estimate_extrinsics(averaged, K, dist, layout)
    ok = summarise(found, len(samples), seen)

    out = os.path.join(WS, 'calibration', f'{args.name}.yaml')
    data = {'camera': found.model.to_dict(),
            'meta': {'device': args.device, 'width': mode[0], 'height': mode[1],
                     'scale': SCALE, 'markers': list(found.marker_ids),
                     'rms_px': found.rms_px, 'frames': len(samples),
                     'position_real_mm': [round(v, 1) for v in found.position_real_mm()],
                     'tilt_deg': round(found.tilt_deg(), 2),
                     'intrinsics': os.path.basename(args.intrinsics),
                     'date': time.strftime('%Y-%m-%d %H:%M')}}
    with open(out, 'w') as f:
        yaml.safe_dump(data, f, sort_keys=False)
    print(f'\nDa ghi {out}' + ('' if ok else '  (van ghi de ban xem, nhung dung dung)'))


if __name__ == '__main__':
    main()
