#!/usr/bin/env python3
"""
Xem trực tiếp camera thật kèm các số liệu quyết định chất lượng ảnh (Bước 10a).

    python3 src/delta_controller/scripts/view_camera.py                 # xem + tìm marker
    python3 src/delta_controller/scripts/view_camera.py --chess         # xem + tìm bàn cờ
    python3 src/delta_controller/scripts/view_camera.py --plain         # chỉ xem

Dùng để NGẮM camera: chỉnh giá đỡ tới khi thấy đủ 6 marker và trọn vùng đặt lon, không vùng nào
cháy sáng. Phím `q` hoặc Esc để thoát, `s` để lưu một ảnh.

Ba con số trên góc trái, theo đúng thứ tự quan trọng:
  • CHAY SANG — tỉ lệ pixel bão hòa (≥ 250). Vùng cháy sáng MẤT HẲN thông tin màu, không thuật
    toán nào cứu được; phải xoay camera hoặc che nguồn sáng. Dưới 2% là tốt.
  • TOI — tỉ lệ pixel V < 40. Đây đúng là ngưỡng `color_detector` loại nền, nên phần vật rơi vào
    vùng này coi như không nhận dạng được (xem mục "bàn đen" trong CLAUDE.md).
  • DO NET — phương sai Laplacian. Dùng để so sánh tương đối khi chỉnh tiêu cự/khoảng cách; C270
    lấy nét cố định nên chỉ cần tránh đặt quá gần (dưới ~30 cm là mờ).
"""

import argparse
import os
import sys
import time

import cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probe_camera as probe   # noqa: E402

WS = os.path.expanduser('~/ros2_closed_loop_ws')
PATTERN = (9, 6)
ARUCO_DICT = 'DICT_4X4_50'
EXPECTED_IDS = set(range(6))
DARK_V = 40          # ngưỡng V của color_detector
BRIGHT = 250


def stats(frame):
    """(tỉ lệ cháy sáng, tỉ lệ tối, độ nét, sáng trung bình)."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    v = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)[:, :, 2]
    return (float((gray >= BRIGHT).mean()), float((v < DARK_V).mean()),
            float(cv2.Laplacian(gray, cv2.CV_64F).var()), float(gray.mean()))


def draw_bar(view, text, y, color):
    cv2.putText(view, text, (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 4, cv2.LINE_AA)
    cv2.putText(view, text, (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1, cv2.LINE_AA)


def overlay_markers(view, gray, detector):
    corners, ids, _ = detector(gray)
    found = set()
    if ids is not None:
        cv2.aruco.drawDetectedMarkers(view, corners, ids)
        found = {int(i) for i in ids.flatten()}
    missing = sorted(EXPECTED_IDS - found)
    ok = not missing
    draw_bar(view, f'MARKER {len(found & EXPECTED_IDS)}/6'
             + ('' if ok else '  thieu ID ' + ','.join(map(str, missing))),
             112, (0, 220, 0) if ok else (0, 160, 255))
    return ok


def overlay_chessboard(view, gray):
    found, corners = cv2.findChessboardCorners(
        gray, PATTERN, flags=cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_NORMALIZE_IMAGE
        | cv2.CALIB_CB_FAST_CHECK)
    if found:
        cv2.drawChessboardCorners(view, PATTERN, corners, True)
    draw_bar(view, 'BAN CO: thay' if found else 'BAN CO: khong thay', 112,
             (0, 220, 0) if found else (0, 160, 255))
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--device', default='auto',
                    help='/dev/videoN, hoac "auto" (mac dinh) de tu tim theo ten')
    ap.add_argument('--chess', action='store_true', help='tim ban co thay vi marker')
    ap.add_argument('--plain', action='store_true', help='khong tim gi ca')
    ap.add_argument('--no-lock', action='store_true', help='khong khoa phoi sang/can bang trang')
    ap.add_argument('--out', default=os.path.join(WS, 'datasets/real_camera'))
    args = ap.parse_args()
    args.device = probe.resolve_device(args.device)

    mode = probe.best_mjpg_mode(args.device)
    if mode is None:
        sys.exit(f'Khong doc duoc che do MJPG tu {args.device} — camera da cam chua?')
    if not args.no_lock:
        probe.lock_manual(args.device, log=lambda s: None)
    cap = probe.open_camera(args.device, mode[0], mode[1])
    probe.warm_up(cap)
    os.makedirs(args.out, exist_ok=True)
    print(f'{mode[0]}x{mode[1]} @ {mode[2]:.0f} fps MJPG — q/Esc thoat, s luu anh')

    detector = None
    if not args.plain and not args.chess:
        d = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, ARUCO_DICT))
        # ⚠️ OpenCV 4.6: phải dùng DetectorParameters_create(); kiểu mới segfault trong
        # detectMarkers (đã gặp 2026-09-28).
        params = cv2.aruco.DetectorParameters_create()
        params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_CONTOUR
        detector = lambda g: cv2.aruco.detectMarkers(g, d, parameters=params)   # noqa: E731

    # ⚠️ WINDOW_NORMAL + resizeWindow: để mặc định (WINDOW_AUTOSIZE) thì cửa sổ Qt hiện ra TRƯỚC
    # khi có khung hình đầu -> người dùng thấy một ô ĐEN bé tí và tưởng camera hỏng. Cỡ cố định
    # 960x540 cũng vừa màn hình laptop, và kéo to nhỏ được.
    # Tiêu đề chỉ dùng ASCII: Qt làm hỏng dấu tiếng Việt (hiện ra thành '?').
    title = 'camera that (q thoat, s luu anh)'
    cv2.namedWindow(title, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(title, 960, 540)

    saved, last_log = 0, 0.0
    while True:
        ok, frame = cap.read()
        if not ok:
            continue
        view = frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blown, dark, sharp, mean = stats(frame)
        draw_bar(view, f'CHAY SANG {100 * blown:4.1f}%', 32,
                 (0, 220, 0) if blown < 0.02 else (0, 160, 255) if blown < 0.10 else (0, 0, 255))
        draw_bar(view, f'TOI (V<{DARK_V}) {100 * dark:4.1f}%', 58,
                 (0, 220, 0) if dark < 0.20 else (0, 160, 255))
        draw_bar(view, f'DO NET {sharp:5.0f}   sang TB {mean:3.0f}', 84, (220, 220, 220))
        if detector is not None:
            overlay_markers(view, gray, detector)
        elif args.chess:
            overlay_chessboard(view, gray)
        cv2.imshow(title, view)
        if time.monotonic() - last_log > 2.0:     # in ra terminal để biết cửa sổ có đang cập nhật
            last_log = time.monotonic()
            print(f'  sang TB {mean:3.0f} | chay sang {100 * blown:4.1f}% | '
                  f'toi {100 * dark:4.1f}% | do net {sharp:5.0f}')
        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), 27):
            break
        if key == ord('s'):
            saved += 1
            path = os.path.join(args.out, time.strftime(f'view_%Y%m%d_%H%M%S_{saved:02d}.png'))
            cv2.imwrite(path, frame)
            print(f'  da luu {path}')
    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
