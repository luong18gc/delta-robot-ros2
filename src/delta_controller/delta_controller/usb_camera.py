"""
Mở và điều khiển camera USB (thuần Python, không phụ thuộc ROS).

Tách khỏi `scripts/probe_camera.py` để NODE ROS dùng được: thư mục `scripts/` không được cài vào
package nên module trong package không import được từ đó.

⚠️ Số thứ tự /dev/videoN KHÔNG ổn định — khởi động lại máy hay cắm lại cổng là đổi (đo 2026-09-30:
C270 từ video2 nhảy về video0, webcam tích hợp chiếm chỗ video2). Vì vậy mặc định là tìm theo TÊN.
"""

import subprocess
import sys
import time

import cv2

MANUAL = (
    ('focus_automatic_continuous', 0),
    ('auto_exposure', 1),               # 1 = Manual Mode theo chuẩn UVC
    ('white_balance_automatic', 0),
    ('backlight_compensation', 0),
    ('exposure_dynamic_framerate', 0),
)

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
