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
import subprocess
import sys
import time

import cv2
import numpy as np

# Các nút v4l2 cần cho ba điều kiện trên: tên nút -> giá trị đặt để chuyển sang thủ công.
MANUAL = (
    ('focus_automatic_continuous', 0),
    ('auto_exposure', 1),               # 1 = Manual Mode theo chuẩn UVC
    ('white_balance_automatic', 0),
    ('backlight_compensation', 0),
    ('exposure_dynamic_framerate', 0),
)
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
BUILTIN_HINTS = ('USB2.0 HD UVC WebCam',)
PREFERRED = ('C270',)


def list_devices():
    """[(tên thiết bị, [/dev/videoN, ...]), ...] theo `v4l2-ctl --list-devices`."""
    try:
        out = subprocess.run(['v4l2-ctl', '--list-devices'],
                             capture_output=True, text=True).stdout
    except FileNotFoundError:
        return []
    devices, name = [], None
    for line in out.splitlines():
        if not line.strip():
            continue
        if not line.startswith((' ', '\t')):
            name = line.rstrip(':').strip()
            devices.append((name, []))
        elif devices and line.strip().startswith('/dev/video'):
            devices[-1][1].append(line.strip())
    return devices


def captures(node):
    """Node này có quay được không — thiết bị UVC còn có node phụ chỉ mang metadata."""
    out, err = v4l2(node, ['--list-formats-ext'])
    return err is not None and 'Size:' in out


def find_device(prefer=PREFERRED):
    """
    Tự chọn camera của đồ án: (node, tên) hoặc (None, lý do).

    Số thứ tự /dev/videoN KHÔNG ổn định — khởi động lại máy hay cắm lại cổng là đổi (đo
    2026-09-30: C270 từ video2 nhảy về video0, webcam tích hợp chiếm chỗ video2). Bắt người dùng
    nhớ số là sẽ có lúc hiệu chuẩn nhầm camera mà không biết. Chọn theo TÊN: ưu tiên tên khớp
    `prefer`, sau đó là mọi camera không phải webcam tích hợp.
    """
    devices = list_devices()
    if not devices:
        return None, 'khong chay duoc v4l2-ctl --list-devices (da cai v4l-utils chua?)'
    ranked = sorted(devices, key=lambda d: (
        0 if any(k.lower() in d[0].lower() for k in prefer) else
        2 if any(k.lower() in d[0].lower() for k in BUILTIN_HINTS) else 1))
    for name, nodes in ranked:
        for node in nodes:
            if captures(node):
                return node, name
    return None, 'khong thay camera nao quay duoc'


def resolve_device(device, log=print):
    """Đổi giá trị --device thành node thật; 'auto' thì tự tìm."""
    if device and device != 'auto':
        return device
    node, name = find_device()
    if node is None:
        sys.exit(f'Khong tim duoc camera: {name}')
    log(f'Camera: {name} -> {node}')
    return node


def v4l2(device, args):
    """Chạy v4l2-ctl, trả về (stdout, stderr); ('', None) nếu máy chưa cài v4l-utils."""
    try:
        r = subprocess.run(['v4l2-ctl', '-d', device] + args, capture_output=True, text=True)
    except FileNotFoundError:
        return '', None
    return r.stdout.strip(), r.stderr.strip()


def list_controls(device):
    """Tên các nút chỉnh camera hỗ trợ."""
    out, err = v4l2(device, ['-L'])
    if err is None:
        return None
    return {line.split()[0] for line in out.splitlines()
            if line.strip() and not line.startswith(' ' * 20)}


def best_mjpg_mode(device):
    """Độ phân giải MJPG lớn nhất chạy được >= 15 fps (YUYV ở 1080p thường chỉ 2 fps)."""
    out, err = v4l2(device, ['--list-formats-ext'])
    if err is None or not out:
        return None
    best, fmt, size = None, None, None
    for line in out.splitlines():
        line = line.strip()
        if line.startswith('['):
            fmt = 'MJPG' if 'MJPG' in line else 'other'
        elif line.startswith('Size:') and fmt == 'MJPG':
            size = tuple(int(v) for v in line.split()[-1].split('x'))
        elif line.startswith('Interval:') and size and fmt == 'MJPG':
            fps = float(line.split('(')[1].split()[0])
            if fps >= 15 and (best is None or size[0] * size[1] > best[0] * best[1]):
                best = (size[0], size[1], fps)
    return best


def open_camera(device, width, height):
    cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    # Hàng đợi mặc định của V4L2 là 4 khung: khung lấy ra luôn là khung CŨ NHẤT còn trong hàng,
    # nên ảnh hiện ra trễ thêm vài khung. Đo 2026-09-30 (đổi phơi sáng rồi đếm khung tới lúc ảnh
    # đổi theo): 4 -> trễ 5 khung; 1 -> trễ 3 khung. Ba khung còn lại (~100 ms) là độ trễ nội tại
    # của C270 (cảm biến + nén MJPG + truyền USB), phần mềm không bỏ được.
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    if not cap.isOpened():
        sys.exit(f'Khong mo duoc {device}')
    return cap


def grab(cap, warmup=10):
    frame = None
    for _ in range(warmup):
        ok, f = cap.read()
        if ok:
            frame = f
    if frame is None:
        sys.exit('Khong doc duoc khung hinh')
    return frame


# C270 tra ve ~30 khung ĐEN ngay sau khi mo thiet bi (do 2026-09-30: khung 0–30 sang TB 2.0,
# on dinh tu khung ~35). Moi phep do phai bo qua giai doan nay, neu khong se ket luan sai.
WARMUP_FRAMES = 40


def warm_up(cap):
    frame = grab(cap, WARMUP_FRAMES)
    return frame


def lock_manual(device, controls=None, log=print):
    """
    Chuyển camera sang phơi sáng / cân bằng trắng / lấy nét THỦ CÔNG, rồi đọc lại xác nhận.

    Trả về chuỗi trạng thái đọc lại (rỗng nếu máy không có v4l2-ctl). Bắt buộc trước mọi phép đo:
    để tự động thì ngưỡng HSV trôi giữa các khung và nội tham số hiệu chuẩn xong cũng vô nghĩa.
    """
    if controls is None:
        controls = list_controls(device)
    if controls is None:
        return ''
    for name, value in MANUAL:
        if name not in controls:
            continue
        _, err = v4l2(device, ['-c', f'{name}={value}'])
        log(f'  {name}={value}' + (f'  LOI: {err}' if err else '  OK'))
    time.sleep(1.0)
    have = [n for n, _ in MANUAL if n in controls]
    state, _ = v4l2(device, ['-C', ','.join(have)])
    return ' | '.join(state.splitlines())


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
