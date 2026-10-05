#!/usr/bin/env python3
"""
Kiểm tra một camera USB có dùng được cho đồ án không, khóa chế độ thủ công và thu ảnh mẫu.

    python3 src/delta_controller/scripts/probe_camera.py                    # kiểm tra + khóa
    python3 src/delta_controller/scripts/probe_camera.py --shots 20 --out datasets/lab_2026_09_28
    python3 src/delta_controller/scripts/probe_camera.py --device /dev/video2 --no-lock

Ba điều kiện bắt buộc với camera thật (kiểm tra tự động, in KẾT LUẬN ở cuối):
  1. Tắt được lấy nét tự động — lấy nét đổi thì tiêu cự đổi, file hiệu chuẩn hết đúng.
  2. Tắt được phơi sáng tự động — ngưỡng màu HSV cần độ sáng ổn định.
  3. Tắt được cân bằng trắng tự động — cân bằng trắng đổi thì sắc màu H đổi.
Cần v4l-utils (lệnh v4l2-ctl). Không có thì vẫn chụp được ảnh nhưng không khóa được chế độ.
"""

import argparse
import os
import time

import _workspace  # noqa: F401
import cv2
from delta_controller.usb_camera import (
    best_mjpg_mode,
    grab,
    list_controls,
    lock_manual,
    open_camera,
    resolve_device,
    warm_up,
    WARMUP_FRAMES,
)
import numpy as np

# Các nút v4l2 cần cho ba điều kiện trên: tên nút -> giá trị đặt để chuyển sang thủ công.
REQUIRED = ('auto_exposure', 'white_balance_automatic')
# Camera lấy nét cố định (vd. Logitech C270) KHÔNG có nút focus nào — như vậy còn tốt hơn: không
# có gì để trôi. Chỉ camera CÓ mô-tơ lấy nét mới cần tắt được lấy nét tự động.
FOCUS_CONTROLS = ('focus_automatic_continuous', 'focus_absolute')


def focus_verdict(controls):
    """('OK'|'LOI', mô tả) về khả năng giữ nguyên tiêu cự của camera."""
    present = [c for c in FOCUS_CONTROLS if c in controls]
    if not present:
        return 'OK', 'lay net co dinh (khong co nut focus) -> tieu cu khong the troi'
    if 'focus_automatic_continuous' in controls:
        return 'OK', 'co lay net tu dong nhung tat duoc -> khoa net thu cong'
    return 'LOI', 'co mo-to lay net nhung KHONG tat duoc tu dong -> hieu chuan se troi'


# Webcam tích hợp của máy nhìn vào NGƯỜI dùng -> không bao giờ là camera của đồ án.
def measure_noise(cap):
    """Độ lệch chuẩn nhiễu cảm biến (mức xám), đo trên hai khung liên tiếp của cảnh tĩnh."""
    a = grab(cap, 5).astype(np.float64)
    b = grab(cap, 5).astype(np.float64)
    return float((a - b).std() / np.sqrt(2))


def report_frame(frame, tag):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    print(f'  [{tag}] sang TB {gray.mean():5.1f}'
          f' | do net {cv2.Laplacian(gray, cv2.CV_64F).var():6.0f}'
          f' | chay sang {(gray > 250).mean() * 100:4.1f}%'
          f' | toi {(gray < 5).mean() * 100:4.1f}%')


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--device', default='auto',
                    help='/dev/videoN, hoac "auto" (mac dinh) de tu tim theo ten')
    ap.add_argument('--shots', type=int, default=0, help='so anh thu vao --out (0 = khong thu)')
    ap.add_argument('--interval', type=float, default=3.0, help='giay giua hai anh khi thu')
    ap.add_argument('--out', default='datasets/real_camera')
    ap.add_argument('--no-lock', action='store_true', help='khong khoa che do thu cong')
    args = ap.parse_args()
    args.device = resolve_device(args.device)

    print(f'== Camera {args.device}')
    controls = list_controls(args.device)
    if controls is None:
        print('  (chua cai v4l-utils -> khong kiem tra / khoa duoc che do)')
    else:
        for name in REQUIRED:
            print(f'  {"CO   " if name in controls else "THIEU"} {name}')
        verdict, why = focus_verdict(controls)
        print(f'  {"OK   " if verdict == "OK" else "LOI  "} lay net: {why}')

    mode = best_mjpg_mode(args.device)
    if mode:
        print(f'  MJPG lon nhat >= 15 fps: {mode[0]}x{mode[1]} @ {mode[2]:.0f} fps')
    width, height = (mode[0], mode[1]) if mode else (1280, 720)

    cap = open_camera(args.device, width, height)
    print(f'  mo o {int(cap.get(3))}x{int(cap.get(4))} @ {cap.get(cv2.CAP_PROP_FPS):.0f} fps')
    report_frame(warm_up(cap), 'tu dong')

    if not args.no_lock and controls is not None:
        print('== Khoa che do thu cong')
        state = lock_manual(args.device, controls)
        report_frame(grab(cap, WARMUP_FRAMES), 'thu cong')
        print('  doc lai:', state)

    noise = measure_noise(cap)
    print(f'== Nhieu cam bien: sigma ~ {noise:.1f} muc xam '
          f'({"vo hai" if noise <= 10 else "dang ke" if noise <= 20 else "cao"}; '
          f'Buoc 8.4: <= 10 khong anh huong, 20 bat dau giam nhan dang)')

    if args.shots:
        out = os.path.abspath(os.path.expanduser(args.out))
        os.makedirs(out, exist_ok=True)
        print(f'== Thu {args.shots} anh vao {out} (cach nhau {args.interval:.0f} s)')
        print('   Doi canh giua cac lan chup: goc nhin, khoang cach, vi tri vat, bang co...')
        for i in range(args.shots):
            frame = grab(cap, 5)
            path = os.path.join(out, f'frame_{i:03d}.png')
            cv2.imwrite(path, frame)
            print(f'   [{i + 1}/{args.shots}] {os.path.basename(path)}')
            if i < args.shots - 1:
                time.sleep(args.interval)

    cap.release()

    ok = (controls is not None and all(n in controls for n in REQUIRED)
          and focus_verdict(controls)[0] == 'OK')
    verdict = ('camera DUNG DUOC cho do an (khoa duoc net, phoi sang, can bang trang)' if ok
               else 'THIEU nut chinh bat buoc -> can camera khac, xem danh sach o tren')
    print('== KET LUAN: ' + verdict)


if __name__ == '__main__':
    main()
