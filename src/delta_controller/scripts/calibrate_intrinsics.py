#!/usr/bin/env python3
"""
Hiệu chuẩn NỘI THAM SỐ camera thật bằng bàn cờ (Bước 10a).

    python3 src/delta_controller/scripts/calibrate_intrinsics.py --device /dev/video2

Cầm bàn cờ đã in (docs/calibration/chessboard_A4.pdf) đưa qua trước camera ở nhiều tư thế; script
tự nhận bàn cờ và CHỈ NHẬN khung nào đủ KHÁC các khung đã nhận, nên không cần bấm gì. Đủ số khung
thì chạy cv2.calibrateCamera và ghi calibration/<tên>_intrinsics.yaml.

Vì sao phải làm bước này (camera mô phỏng không cần): ống kính thật có méo. Camera mô phỏng là lỗ
kim lý tưởng nên `dist = 0` và K suy ra được từ hfov. Ống kính C270 méo thùng thấy rõ ở rìa ảnh;
bỏ qua thì sai số dồn hết vào phần rìa — đúng chỗ đặt marker hiệu chuẩn, tức là làm hỏng luôn cả
ngoại tham số.

⚠️ Nội tham số gắn với TỪNG MÁY và TỪNG ĐỘ PHÂN GIẢI. Đổi camera hoặc đổi độ phân giải là phải
hiệu chuẩn lại; file lưu kèm độ phân giải để về sau kiểm tra chéo.

⚠️ Kích thước ô KHÔNG ảnh hưởng K và dist (chỉ ảnh hưởng vectơ tịnh tiến của từng khung, mà ta
không dùng) — nhưng cứ đo thước rồi truyền `--square` cho đúng, vì sai số chiếu lại in ra sẽ dễ so
với tài liệu khác.
"""

import argparse
import math
import os
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probe_camera as probe   # noqa: E402  (dùng lại phần chọn chế độ + khóa thủ công)
import yaml                    # noqa: E402

# Bàn cờ trong docs/calibration/chessboard_A4.pdf: 10x7 ô -> 9x6 GÓC TRONG.
PATTERN = (9, 6)
SQUARE_MM = 20.0
WS = os.path.expanduser('~/ros2_closed_loop_ws')
# Khung mới phải lệch khung đã nhận ít nhất bấy nhiêu pixel (trung bình trên 54 góc) thì mới nhận.
MIN_POSE_DISTANCE_PX = 55.0
# ... VÀ bàn cờ phải ĐỨNG YÊN: góc dịch chuyển dưới bấy nhiêu pixel so với khung ngay trước đó.
# Vì sao bắt buộc: nhận khung ngay khi thấy bàn cờ thì ảnh dính nhòe chuyển động, sai số chiếu lại
# đều ~0.55 px ở MỌI ảnh (lẽ ra 0.1–0.3) và bộ giải bù phần dư vào méo tiếp tuyến -> p1 = -0.043,
# lớn gấp 10 lần giá trị vật lý hợp lý (đo 2026-09-30).
STILL_PX = 0.8
# Phân nhóm độ nghiêng bàn cờ (góc giữa pháp tuyến bàn cờ và trục ngắm, độ) + số khung tối thiểu
# mỗi nhóm. Bàn cờ chỉ cầm gần song song mặt cảm biến thì tiêu cự và hệ số méo KHÔNG tách bạch
# được: đo 2026-09-30, bộ 20 khung thiếu nghiêng mạnh cho fx nhảy 4.3% chỉ vì thêm ràng buộc
# fx = fy, và méo tiếp tuyến p1 phồng lên -0.043 (giá trị vật lý < 0.005).
TILT_BUCKETS = ((0.0, 15.0, 'phang'), (15.0, 30.0, 'vua'), (30.0, 90.0, 'manh'))
MIN_PER_BUCKET = (2, 5, 6)
SUBPIX_CRITERIA = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
# Nghiêng quá thì ô bàn cờ bị nén, tinh chỉnh góc dưới pixel mất chính xác và màn hình LCD cũng
# đổi tương phản theo góc nhìn. Đo 2026-10-01: nghiêng 9° -> lệch 0.47 px, 28° -> 0.75,
# 55–71° -> 0.96–1.74.
MAX_TILT_DEG = 50.0
# Mô hình méo: CHỈ k1, k2 (ép k3 = 0). Webcam méo nhẹ nên k3 không cần, mà thêm nó vào thì đa thức
# bậc 5 khớp quá mức ở vùng ít dữ liệu: đo 2026-10-01, giữ k3 cho RMS nhỉnh hơn 0.014 px nhưng
# đường cong méo QUAY ĐẦU ở bán kính ~700 px — tức sai dấu ngay tại GÓC ẢNH (bán kính 764 px),
# đúng chỗ đặt marker hiệu chuẩn.
CALIB_FLAGS = cv2.CALIB_FIX_K3


def object_points(square_mm):
    """Tọa độ 3D các góc trong của bàn cờ (mặt phẳng z = 0), đơn vị mét."""
    pts = np.zeros((PATTERN[0] * PATTERN[1], 3), np.float32)
    pts[:, :2] = np.mgrid[0:PATTERN[0], 0:PATTERN[1]].T.reshape(-1, 2)
    return pts * (square_mm / 1000.0)


def subpix_window(corners):
    """
    Nửa cạnh cửa sổ tinh chỉnh góc, co theo khoảng cách góc NHỎ NHẤT trên ảnh.

    Để cố định 11 px thì khi bàn cờ nhìn nghiêng, một ô chỉ còn ~25 px mà cửa sổ 23x23 px đã nuốt
    gần trọn ô và trùm sang góc bên cạnh -> góc bị kéo lệch.
    """
    g = corners.reshape(PATTERN[1], PATTERN[0], 2)
    gap = min(np.linalg.norm(g[:, 1:] - g[:, :-1], axis=2).min(),
              np.linalg.norm(g[1:] - g[:-1], axis=2).min())
    return int(max(3, min(11, gap * 0.35)))


def find_corners(gray, fast=True):
    """Góc bàn cờ đã tinh chỉnh tới dưới pixel, hoặc None."""
    flags = cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_NORMALIZE_IMAGE
    if fast:
        flags |= cv2.CALIB_CB_FAST_CHECK
    found, corners = cv2.findChessboardCorners(gray, PATTERN, flags=flags)
    if not found:
        return None
    win = subpix_window(corners)
    return cv2.cornerSubPix(gray, corners, (win, win), (-1, -1), SUBPIX_CRITERIA)


def board_tilt(corners, shape, square_mm):
    """
    Góc giữa pháp tuyến bàn cờ và trục ngắm (độ): 0 = cầm song song mặt cảm biến.

    Dùng K PHỎNG ĐOÁN (f ≈ 1.1·rộng ảnh) — chỉ cần phân loại độ nghiêng để hướng dẫn người chụp,
    không dùng cho phép hiệu chuẩn, nên sai vài phần trăm tiêu cự không ảnh hưởng.
    """
    h, w = shape
    f = 1.1 * w
    K = np.array([[f, 0.0, (w - 1) / 2], [0.0, f, (h - 1) / 2], [0.0, 0.0, 1.0]])
    ok, rvec, _ = cv2.solvePnP(object_points(square_mm), corners, K, None)
    if not ok:
        return 0.0
    normal = cv2.Rodrigues(rvec)[0] @ np.array([0.0, 0.0, 1.0])
    return float(np.degrees(np.arccos(min(1.0, abs(normal[2])))))


def tilt_counts(tilts):
    """Số khung trong từng nhóm độ nghiêng."""
    return [sum(1 for t in tilts if lo <= t < hi) for lo, hi, _ in TILT_BUCKETS]


def missing_region(grid):
    """Tên vùng khung hình còn thiếu, để nhắc người chụp đưa bàn cờ tới đó."""
    rows, cols = np.nonzero(~grid)
    if len(rows) == 0:
        return ''
    names = []
    if (cols <= 1).sum() > (cols >= 6).sum():
        names.append('TRAI')
    elif (cols >= 6).sum() > 0:
        names.append('PHAI')
    if (rows <= 1).sum() > (rows >= 4).sum():
        names.append('TREN')
    elif (rows >= 4).sum() > 0:
        names.append('DUOI')
    return ' '.join(names) or 'GIUA'


def advice(accepted, tilts, shape):
    """Một dòng nhắc việc còn thiếu: vùng khung hình nào, hay độ nghiêng nào."""
    _, grid = coverage(accepted, shape)
    counts = tilt_counts(tilts)
    short = [name for (_, _, name), c, need in zip(TILT_BUCKETS, counts, MIN_PER_BUCKET)
             if c < need]
    parts = [f'nghieng {"/".join(n for _, _, n in TILT_BUCKETS)}: '
             + '/'.join(str(c) for c in counts)]
    if short:
        parts.append(f'can them NGHIENG {short[-1].upper()}')
    region = missing_region(grid)
    if region:
        parts.append(f'con thieu goc {region}')
    return '  |  '.join(parts)


def pose_distance(corners, accepted):
    """Khoảng cách nhỏ nhất (pixel, trung bình trên các góc) tới các khung đã nhận."""
    if not accepted:
        return float('inf')
    c = corners.reshape(-1, 2)
    return min(float(np.mean(np.linalg.norm(c - a.reshape(-1, 2), axis=1))) for a in accepted)


def coverage(accepted, shape):
    """Tỉ lệ diện tích ảnh mà các góc đã quét qua (chia lưới 8x6 ô, đếm ô có góc)."""
    h, w = shape
    grid = np.zeros((6, 8), bool)
    for corners in accepted:
        for u, v in corners.reshape(-1, 2):
            grid[min(5, int(v / h * 6)), min(7, int(u / w * 8))] = True
    return grid.mean(), grid


def motion(corners, previous):
    """Góc bàn cờ dịch bao nhiêu pixel so với khung ngay trước (vô cùng nếu chưa có)."""
    if previous is None:
        return float('inf')
    return float(np.mean(np.linalg.norm(
        corners.reshape(-1, 2) - previous.reshape(-1, 2), axis=1)))


def draw_guide(frame, corners, accepted, tilts, wanted, state):
    """Ảnh hướng dẫn: lưới độ phủ, độ nghiêng khung hiện tại, việc còn thiếu."""
    view = frame.copy()
    h, w = view.shape[:2]
    _, grid = coverage(accepted, (h, w))
    for r in range(6):                       # tô các ô đã quét qua
        for c in range(8):
            if grid[r, c]:
                x0, y0 = int(c * w / 8), int(r * h / 6)
                cv2.rectangle(view, (x0 + 1, y0 + 1),
                              (int((c + 1) * w / 8) - 1, int((r + 1) * h / 6) - 1),
                              (0, 150, 0), 2)
    if corners is not None:
        cv2.drawChessboardCorners(view, PATTERN, corners, True)
    lines = [f'{len(accepted)}/{wanted} khung   {state}',
             advice(accepted, tilts, (h, w))]
    if corners is not None:
        lines.insert(1, f'nghieng hien tai {board_tilt(corners, (h, w), SQUARE_MM):.0f}°')
    for i, text in enumerate(lines):
        y = 30 + 26 * i
        cv2.putText(view, text, (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 4,
                    cv2.LINE_AA)
        cv2.putText(view, text, (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1,
                    cv2.LINE_AA)
    return view


def capture(cap, wanted, show, square_mm):
    """Thu `wanted` khung bàn cờ ở các tư thế khác nhau, mỗi khung phải ĐỨNG YÊN."""
    accepted, tilts, previous, last_report = [], [], None, 0.0
    # Xóa ảnh lượt trước: lượt mới ít khung hơn thì ảnh cũ còn sót lại, và `--from-dir` sau đó
    # trộn lẫn hai lượt (đã gặp 2026-10-01: 6 ảnh mới + 14 ảnh cũ nằm chung thư mục).
    for name in os.listdir(SHOT_DIR):
        if name.startswith('chessboard_') and name.endswith('.png'):
            os.remove(os.path.join(SHOT_DIR, name))
    title = 'hieu chuan noi tham so (q = dung)'
    if show:
        cv2.namedWindow(title, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(title, 960, 540)
    print(f'Can {wanted} khung. Moi tu the: dua toi cho roi GIU YEN ~1 giay '
          '— chi nhan khi ban co dung im.')
    print('Script se nhac con thieu gi (goc anh nao, do nghieng nao). Ctrl+C de dung som '
          '(toi thieu 10 khung).')
    while len(accepted) < wanted:
        ok, frame = cap.read()
        if not ok:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners = find_corners(gray)
        still = corners is not None and motion(corners, previous) < STILL_PX
        new_pose = corners is not None and pose_distance(corners, accepted) >= MIN_POSE_DISTANCE_PX
        tilt = board_tilt(corners, gray.shape, square_mm) if corners is not None else 0.0
        ok_tilt = corners is not None and tilt <= MAX_TILT_DEG
        state = ('chua thay ban co' if corners is None
                 else f'nghieng {tilt:.0f}° — QUA GAT, bot lai duoi {MAX_TILT_DEG:.0f}°'
                 if not ok_tilt
                 else 'da co tu the nay' if not new_pose
                 else 'dang rung - giu yen' if not still else 'nhan...')
        if still and new_pose and ok_tilt:
            accepted.append(corners)
            tilts.append(tilt)
            cov, _ = coverage(accepted, gray.shape)
            print(f'  nhan khung {len(accepted):2d}/{wanted}  nghieng {tilts[-1]:4.0f}°  '
                  f'phu {100 * cov:3.0f}%  |  {advice(accepted, tilts, gray.shape)}')
            cv2.imwrite(os.path.join(SHOT_DIR, f'chessboard_{len(accepted):02d}.png'), frame)
            previous = None
            if show:
                cv2.imshow(title, draw_guide(frame, corners, accepted, tilts, wanted, 'DA NHAN'))
                cv2.waitKey(1)
            time.sleep(0.3)      # tránh nhận liên tiếp cùng một tư thế
            continue
        previous = corners
        if time.monotonic() - last_report > 3.0:
            last_report = time.monotonic()
            print(f'  ...{state}  |  {advice(accepted, tilts, gray.shape)}')
        if show:
            cv2.imshow(title, draw_guide(frame, corners, accepted, tilts, wanted, state))
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    if tilts:
        counts = tilt_counts(tilts)
        print('  do nghieng thu duoc: ' + ', '.join(
            f'{name} {c}' for (_, _, name), c in zip(TILT_BUCKETS, counts)))
    return accepted


def calibrate(accepted, shape, square_mm, flags=0):
    """Chạy cv2.calibrateCamera, trả về (K, dist, rms, sai số từng khung)."""
    obj = [object_points(square_mm)] * len(accepted)
    h, w = shape
    rms, K, dist, rvecs, tvecs = cv2.calibrateCamera(obj, accepted, (w, h), None, None,
                                                     flags=flags)
    per_view = []
    for i, corners in enumerate(accepted):
        proj, _ = cv2.projectPoints(obj[i], rvecs[i], tvecs[i], K, dist)
        per_view.append(float(np.sqrt(np.mean(
            np.sum((proj.reshape(-1, 2) - corners.reshape(-1, 2)) ** 2, axis=1)))))
    return K, dist, rms, per_view


def flatness(accepted, square_mm):
    """
    (sai lệch trung bình px, bản đồ sai lệch theo GÓC BÀN CỜ, lệch mm ở góc tệ nhất).

    Bàn cờ PHẲNG nhìn từ camera lỗ kim bất kỳ luôn khớp ảnh qua một phép đồng dạng (homography)
    CHÍNH XÁC — không cần biết nội tham số. Nên phần dư của phép khớp đó đo trực tiếp độ cong của
    tấm bàn cờ, tách hẳn khỏi mọi thứ liên quan hiệu chuẩn. Trung bình theo CHỈ SỐ GÓC (không phải
    vị trí trên ảnh) thì méo ống kính bị triệt tiêu, vì bàn cờ xuất hiện ở chỗ khác nhau mỗi khung.
    Đo 2026-09-30: khử méo ống kính chỉ giảm 1.64 -> 1.63 px, tức phần dư gần như hoàn toàn là
    bàn cờ cong; bản đồ chỉ đúng một góc tấm bìa vênh 1.4 mm.
    """
    grid = np.mgrid[0:PATTERN[0], 0:PATTERN[1]].T.reshape(-1, 2).astype(np.float32)
    residuals = []
    for corners in accepted:
        pts = corners.reshape(-1, 2)
        matrix, _ = cv2.findHomography(grid, pts, 0)
        if matrix is None:
            continue
        proj = cv2.perspectiveTransform(grid.reshape(-1, 1, 2), matrix).reshape(-1, 2)
        residuals.append(np.linalg.norm(pts - proj, axis=1))
    if not residuals:
        return 0.0, np.zeros((PATTERN[1], PATTERN[0])), 0.0
    res = np.array(residuals)
    per_corner = res.mean(0)
    # px -> mm: một ô 20 mm chiếm bao nhiêu px trên ảnh, quy đổi theo tỉ lệ đó.
    spacing = np.median([np.linalg.norm(c.reshape(-1, 2)[1] - c.reshape(-1, 2)[0])
                         for c in accepted])
    mm = per_corner.max() * square_mm / spacing
    return float(res.mean()), per_corner.reshape(PATTERN[1], PATTERN[0]), float(mm)


def distortion_curve(K, dist, shape):
    """
    (bán kính, dịch chuyển do méo) từ tâm méo ra tới GÓC ẢNH, và có đơn điệu hay không.

    Đa thức méo chỉ được ràng buộc ở những bán kính mà bàn cờ đã đi qua; ra ngoài đó nó ngoại suy
    tùy ý. Đổi dấu trên quãng này nghĩa là mô hình đang bịa ở rìa ảnh — nơi méo mạnh nhất và cũng
    là nơi đặt marker.
    """
    h, w = shape
    r_max = max(math.hypot(K[0, 2] - x, K[1, 2] - y) for x in (0, w - 1) for y in (0, h - 1))
    radii = np.arange(0.0, r_max + 1, 40.0)
    pts = np.array([[[K[0, 2] + r, K[1, 2]]] for r in radii], np.float32)
    undist = cv2.undistortPoints(pts, K, dist, P=K).reshape(-1, 2)
    shift = undist[:, 0] - K[0, 2] - radii
    # Hai kiểu hỏng, phân biệt theo ĐỘ LỚN chứ không theo dấu đạo hàm: méo nhích ngược lại vài
    # phần mười pixel ở đúng mép ngoài cùng là vô hại, còn ĐỔI DẤU (đang kéo vào lại hóa đẩy ra)
    # thì mô hình sai hẳn. Đo 2026-10-01: giữ k3 -> -6.1 px nhảy thành +6.9 px; bỏ k3 -> chỉ
    # nhích lại 0.27 px trên 40 px bán kính cuối.
    flipped = bool(shift.min() < -0.5 and shift.max() > 0.5)
    peak = int(np.argmax(np.abs(shift)))
    rebound = float(np.abs(shift[peak]) - np.abs(shift[peak:]).min())
    return radii, shift, (not flipped and rebound <= 1.0), rebound


def report(K, dist, rms, per_view, accepted, shape, square_mm, device, out):
    h, w = shape
    cov, grid = coverage(accepted, shape)
    print('\n== KET QUA')
    print(f'  do phan giai      {w} x {h}')
    print(f'  so khung dung     {len(accepted)}')
    print(f'  fx, fy            {K[0, 0]:.2f}, {K[1, 1]:.2f} px')
    print(f'  cx, cy            {K[0, 2]:.2f}, {K[1, 2]:.2f} px  '
          f'(tam anh: {(w - 1) / 2:.1f}, {(h - 1) / 2:.1f})')
    print(f'  goc nhin ngang    {2 * np.degrees(np.arctan(w / 2 / K[0, 0])):.1f}°')
    print(f'  meo k1 k2 p1 p2 k3  {" ".join(f"{d:+.4f}" for d in dist.reshape(-1)[:5])}')
    print(f'  sai so chieu lai   RMS {rms:.3f} px  '
          f'(tung khung: {min(per_view):.2f} – {max(per_view):.2f})')
    print(f'  phu khung hinh     {100 * cov:.0f}% (luoi 8x6)')
    for row in grid:
        print('      ' + ' '.join('#' if c else '.' for c in row))

    # Ép fx = fy rồi so: webcam có pixel VUÔNG nên fx phải bằng fy. Nếu ràng buộc đó gần như
    # không làm xấu RMS mà tiêu cự lại nhảy vài phần trăm, nghĩa là dữ liệu KHÔNG đủ tách bạch
    # tiêu cự / tâm ảnh / hệ số méo — con số in ra đẹp nhưng không tin được (đo 2026-09-30:
    # RMS 0.569 -> 0.572 mà fx tụt 1336 -> 1279).
    K_fix, _, rms_fix, _ = calibrate(accepted, shape, square_mm,
                                     CALIB_FLAGS | cv2.CALIB_FIX_ASPECT_RATIO)
    focal_shift = abs(K_fix[0, 0] - K[0, 0]) / K[0, 0]
    print(f'  ep fx = fy         RMS {rms_fix:.3f} (chenh {rms_fix - rms:+.3f}), '
          f'fx {K_fix[0, 0]:.1f} (lech {100 * focal_shift:.1f}%)')

    flat_px, flat_map, flat_mm = flatness(accepted, square_mm)
    print(f'  do phang ban co    lech {flat_px:.2f} px so voi mat phang ly tuong, '
          f'goc te nhat ~{flat_mm:.1f} mm')

    radii, shift, sane, rebound = distortion_curve(K, dist, shape)
    print(f'  meo o goc anh      {shift[-1]:+.2f} px tai ban kinh {radii[-1]:.0f} px '
          f'(nhich nguoc {rebound:.2f} px)')

    print('\n== DANH GIA')
    ok = True
    if rms > 0.8:
        print('  LOI  sai so chieu lai > 0.8 px -> ban co cong, anh nhoe, hoac o sai kich thuoc')
        ok = False
    elif rms > 0.4:
        print(f'  LOI  sai so chieu lai {rms:.3f} px — nhan goc duoi pixel dat 0.1–0.3 px khi '
              'ban co PHANG va DUNG YEN. Dan ban co len bia cung roi chup lai.')
        ok = False
    else:
        print(f'  OK   sai so chieu lai {rms:.3f} px')
    if rms_fix - rms < 0.02 and focal_shift > 0.01:
        print(f'  LOI  ep fx = fy gan nhu khong lam xau RMS ({rms_fix - rms:+.3f} px) nhung tieu '
              f'cu doi {100 * focal_shift:.1f}% -> du lieu chua tach bac duoc tieu cu voi meo. '
              'Can them tu the NGHIENG manh (~35–45°) va xa/gan khac nhau.')
        ok = False
    if flat_px > 0.5:
        print(f'  LOI  BAN CO KHONG PHANG: lech {flat_px:.2f} px (goc te nhat ~{flat_mm:.1f} mm). '
              'Phep thu nay KHONG lien quan hieu chuan — ban co phang thi phai < 0.3 px.')
        print('       Ban do lech tai tung goc ban co (px) — cho nao lon la cho do venh:')
        for row in flat_map:
            print('         ' + ' '.join(f'{v:4.1f}' for v in row))
        print('       Sua: BOI KEO KIN CA MAT SAU to giay roi dan len bia cung / tam mica, '
              'ep phang duoi chong sach vai tieng. Dan bang bang dinh 4 goc la KHONG du.')
        ok = False
    else:
        print(f'  OK   ban co phang (lech {flat_px:.2f} px)')
    if not sane:
        print(f'  LOI  duong cong meo khong on dinh toi goc anh (nhich nguoc {rebound:.2f} px) '
              '-> mo hinh dang bia o ria. Dua ban co ra sat 4 GOC khung hinh roi chup lai.')
        ok = False
    else:
        print(f'  OK   duong cong meo on dinh toi goc anh ({shift[-1]:+.2f} px)')
    tangential = max(abs(dist.reshape(-1)[2]), abs(dist.reshape(-1)[3]))
    if tangential > 0.01:
        print(f'  LOI  meo tiep tuyen |p| = {tangential:.4f} — gia tri vat ly thuong < 0.005. '
              'Lon the nay la no dang HUT sai so he thong (ban co cong / anh nhoe).')
        ok = False
    else:
        print(f'  OK   meo tiep tuyen |p| = {tangential:.4f}')
    if cov < 0.6:
        print(f'  CANH BAO moi phu {100 * cov:.0f}% khung hinh -> he so meo o RIA anh chua duoc '
              'rang buoc. Dua ban co ra sat 4 goc anh roi chay lai.')
        ok = False
    else:
        print(f'  OK   phu {100 * cov:.0f}% khung hinh')
    if abs(K[0, 0] - K[1, 1]) / K[0, 0] > 0.02:
        print(f'  CANH BAO fx va fy lech {100 * abs(K[0, 0] - K[1, 1]) / K[0, 0]:.1f}% '
              '-> bat thuong voi webcam pixel vuong')
    print('  ' + ('=> DUNG DUOC' if ok else '=> NEN HIEU CHUAN LAI'))

    data = {'camera': {'K': K.tolist(), 'dist': dist.reshape(-1).tolist()},
            'meta': {'device': device, 'width': int(w), 'height': int(h),
                     'pattern': list(PATTERN), 'square_mm': square_mm,
                     'views': len(accepted), 'rms_px': float(rms),
                     'coverage': float(cov),
                     'date': time.strftime('%Y-%m-%d %H:%M')}}
    with open(out, 'w') as f:
        yaml.safe_dump(data, f, sort_keys=False)
    print(f'\nDa ghi {out}')
    print(f'Anh da dung: {SHOT_DIR}')


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--device', default='auto',
                    help='/dev/videoN, hoac "auto" (mac dinh) de tu tim theo ten')
    ap.add_argument('--views', type=int, default=20, help='so khung can thu (mac dinh 20)')
    ap.add_argument('--square', type=float, default=SQUARE_MM,
                    help='canh o ban co DO DUOC bang thuoc (mm)')
    ap.add_argument('--name', default='c270', help='ten camera, dung dat ten file ket qua')
    ap.add_argument('--show', action='store_true', help='hien cua so xem truc tiep')
    ap.add_argument('--from-dir', help='bo qua camera, hieu chuan lai tu thu muc anh da thu')
    ap.add_argument('--flat-check', action='store_true',
                    help='chi thu 6 khung va kiem tra ban co co PHANG khong (~30 giay)')
    args = ap.parse_args()
    args.device = probe.resolve_device(args.device)

    global SHOT_DIR
    SHOT_DIR = os.path.join(WS, 'datasets/real_camera/chessboard')
    os.makedirs(SHOT_DIR, exist_ok=True)
    os.makedirs(os.path.join(WS, 'calibration'), exist_ok=True)
    out = os.path.join(WS, 'calibration', f'{args.name}_intrinsics.yaml')

    if args.flat_check:
        # Kiểm tra độ phẳng cần rất ít khung (phép đồng dạng không cần nội tham số), nên chạy
        # trước cho nhanh: bàn cờ cong thì chụp đủ 16 tư thế cũng vứt đi.
        mode = probe.best_mjpg_mode(args.device)
        if mode is None:
            sys.exit('Khong doc duoc che do MJPG — camera da cam chua?')
        probe.lock_manual(args.device, log=lambda _: None)
        cap = probe.open_camera(args.device, mode[0], mode[1])
        probe.warm_up(cap)
        print('KIEM TRA DO PHANG: dua ban co qua 6 tu the NGHIENG khac nhau, moi tu the giu yen.')
        try:
            accepted = capture(cap, 6, args.show, args.square)
        except KeyboardInterrupt:
            print('\n(dung som)')
            accepted = []
        finally:
            cap.release()
            cv2.destroyAllWindows()
        if len(accepted) < 3:
            sys.exit('Can it nhat 3 khung de ket luan')
        flat_px, flat_map, flat_mm = flatness(accepted, args.square)
        print(f'\n== DO PHANG BAN CO: lech {flat_px:.2f} px, goc te nhat ~{flat_mm:.1f} mm')
        for row in flat_map:
            print('     ' + ' '.join(f'{v:4.1f}' for v in row))
        if flat_px > 0.5:
            print('  => CHUA PHANG. Dan lai roi kiem tra lai truoc khi chup du 16 tu the.')
        else:
            print('  => PHANG, chup duoc. Chay lai khong co --flat-check de hieu chuan that.')
        return

    if args.from_dir:
        accepted, shape = [], None
        for name in sorted(os.listdir(args.from_dir)):
            frame = cv2.imread(os.path.join(args.from_dir, name))
            if frame is None:
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            corners = find_corners(gray, fast=False)
            shape = gray.shape
            if corners is None:
                print(f'  bo qua {name}: khong thay ban co')
            else:
                accepted.append(corners)
        print(f'Dung {len(accepted)} anh trong {args.from_dir}')
    else:
        mode = probe.best_mjpg_mode(args.device)
        if mode is None:
            sys.exit('Khong doc duoc che do MJPG — camera da cam chua?')
        print(f'Che do: {mode[0]}x{mode[1]} @ {mode[2]:.0f} fps MJPG')
        probe.lock_manual(args.device)          # khoa phoi sang / can bang trang
        cap = probe.open_camera(args.device, mode[0], mode[1])
        probe.warm_up(cap)
        try:
            accepted = capture(cap, args.views, args.show, args.square)
        except KeyboardInterrupt:
            print('\n(dung som)')
        finally:
            cap.release()
            cv2.destroyAllWindows()
        shape = (mode[1], mode[0])

    if len(accepted) < 10:
        sys.exit(f'Chi co {len(accepted)} khung — can it nhat 10 de hieu chuan tin duoc')
    K, dist, rms, per_view = calibrate(accepted, shape, args.square, CALIB_FLAGS)
    print()
    report(K, dist, rms, per_view, accepted, shape, args.square, args.device, out)


if __name__ == '__main__':
    main()
