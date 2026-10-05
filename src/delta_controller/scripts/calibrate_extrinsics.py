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
from delta_controller.scene import (
    REAL_CALIB_MARKERS,
    real_calib_markers_virtual,
    SCALE,
    TABLE_Z,
)
import numpy as np

# Chay duoc ca khi chua `source install/setup.bash`: them thu muc goi vao duong dan.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')))
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


def marker_errors_mm(found, centers):
    """
    Sai số từng marker quy ra MILIMÉT trên mặt bàn và trong không gian ảo.

    Pixel không phải đơn vị để phán xét: cùng một sai số chiếu lại tính bằng pixel ứng với số
    milimét khác hẳn nhau tùy camera đặt gần hay xa, và thứ quyết định gắp được hay không là
    milimét trong không gian ảo so với dung sai giác hút 12 mm. Đo 2026-10-05: RMS 3.25 px nghe
    như hỏng, quy ra chỉ ~1 mm ảo, ngang mô phỏng (1.13 mm).
    """
    out = {}
    for i in found.marker_ids:
        u, v = centers[i]
        got = np.array(found.model.pixel_to_plane(u, v, TABLE_Z)[:2])
        want = np.array(REAL_CALIB_MARKERS[i]) / SCALE
        virtual_mm = 1000.0 * float(np.linalg.norm(got - want))
        out[i] = (virtual_mm * SCALE, virtual_mm)
    return out


def summarise(found, frames_used, frames_seen, centers):
    """In kết quả kèm số liệu đối chiếu được bằng thước."""
    x, y, z = found.position_real_mm()
    print('\n== KET QUA')
    print(f'  marker dung       {len(found.marker_ids)}/{len(REAL_CALIB_MARKERS)}: '
          f'{", ".join(str(i) for i in found.marker_ids)}')
    print(f'  khung dung        {frames_used}/{frames_seen}')
    errors = marker_errors_mm(found, centers)
    virtual = np.array([v for _, v in errors.values()])
    rms_mm = float(np.sqrt(np.mean(virtual ** 2)))
    print(f'  sai so chieu lai  RMS {found.rms_px:.2f} px')
    print(f'  quy ra milimet    RMS {rms_mm:.2f} mm AO '
          f'({rms_mm * SCALE:.1f} mm tren ban that), lon nhat {virtual.max():.2f} mm ao')
    for i, (real_mm, virt_mm) in sorted(errors.items()):
        print(f'      ID {i}: {real_mm:5.1f} mm tren ban  ->  {virt_mm:4.2f} mm ao')
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
    # Ngưỡng tính theo dung sai giác hút 12 mm ảo: 1/4 dung sai là thoải mái, 1/2 là nên xem lại.
    if rms_mm > 6.0:
        print(f'  LOI  sai so {rms_mm:.2f} mm ao qua lon (nua dung sai giac hut 12 mm). '
              'Kiem tra toa do dan marker so voi scene.REAL_CALIB_MARKERS.')
        ok = False
    elif rms_mm > 3.0:
        print(f'  CANH BAO sai so {rms_mm:.2f} mm ao — dung duoc nhung nen do lai toa do marker.')
    else:
        print(f'  OK   sai so {rms_mm:.2f} mm ao (mo phong dat 1.13 mm, dung sai 12 mm)')
    worst = max(errors, key=lambda i: errors[i][1])
    if errors[worst][1] > 2.5 * rms_mm and errors[worst][1] > 2.0:
        print(f'  CANH BAO marker {worst} lech han cac marker khac '
              f'({errors[worst][0]:.0f} mm tren ban) — nhieu kha nang dan sai toa do cai do.')
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
    ok = summarise(found, len(samples), seen, averaged)

    out = os.path.join(WS, 'calibration', f'{args.name}.yaml')
    errors = marker_errors_mm(found, averaged)
    rms_mm = float(np.sqrt(np.mean([v for _, v in errors.values()])))
    data = {'camera': found.model.to_dict(),
            'meta': {'device': args.device, 'width': mode[0], 'height': mode[1],
                     'scale': SCALE, 'markers': list(found.marker_ids),
                     'rms_px': found.rms_px,
                     'rms_mm_virtual': round(rms_mm, 3), 'frames': len(samples),
                     'position_real_mm': [round(v, 1) for v in found.position_real_mm()],
                     'tilt_deg': round(found.tilt_deg(), 2),
                     'intrinsics': os.path.basename(args.intrinsics),
                     'date': time.strftime('%Y-%m-%d %H:%M')}}
    with open(out, 'w') as f:
        yaml.safe_dump(data, f, sort_keys=False)
    print(f'\nDa ghi {out}' + ('' if ok else '  (van ghi de ban xem, nhung dung dung)'))


if __name__ == '__main__':
    main()
