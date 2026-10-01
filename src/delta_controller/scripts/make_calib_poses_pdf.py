#!/usr/bin/env python3
"""
Tạo bảng hướng dẫn 16 tư thế cầm bàn cờ khi hiệu chuẩn nội tham số (Bước 10a).

    python3 src/delta_controller/scripts/make_calib_poses_pdf.py

Ghi docs/calibration/huong_dan_chup_ban_co.pdf. Mỗi ô là ẢNH DỰNG LẠI đúng như camera sẽ nhìn
thấy ở tư thế đó — chiếu bàn cờ thật (10x7 ô, cạnh 20 mm) qua mô hình camera C270, nên người chụp
chỉ cần cầm sao cho hình trên màn hình giống hình trong bảng.

Vì sao cần bảng này: mô tả bằng lời ("nghiêng 35° sang trái") rất khó hình dung, mà chụp sai thì
phải làm lại cả lượt. Sai lầm hay gặp nhất là để bàn cờ NẰM TRÊN BÀN rồi đẩy đi đẩy lại: mọi khung
có cùng một hướng, bộ giải không tách được tiêu cự khỏi khoảng cách (đo 2026-09-30: 20 khung đều
nghiêng 47–49°, fx nhảy 4.3%, méo tiếp tuyến p1 = -0.043).
"""

import math
import os

import cv2
import matplotlib
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import numpy as np

A4 = (210.0, 297.0)                       # mm
OUT = os.path.expanduser('~/ros2_closed_loop_ws/docs/calibration/huong_dan_chup_ban_co.pdf')

W, H = 1280, 720                          # khung hình C270
F = 1278.9                                # tiêu cự đo được (bản ép fx = fy)
CX, CY = (W - 1) / 2, (H - 1) / 2
COLS, ROWS, SQUARE = 10, 7, 0.020         # bàn cờ trong chessboard_A4.pdf
BOARD = (COLS * SQUARE, ROWS * SQUARE)    # 200 x 140 mm
MARGIN = 0.012                            # lề trắng quanh bàn cờ (m)

# (tên, xoay quanh trục DỌC của bàn cờ, xoay quanh trục NGANG, xoay trong mặt phẳng, u, v, Z)
# Góc dương: trục dọc -> cạnh TRÁI tiến về phía camera; trục ngang -> mép TRÊN ngả ra sau.
POSES = [
    ('huong thang, giua', 0, 0, 0, 0.50, 0.50, 0.45),
    ('huong thang, lai gan', 0, 0, 0, 0.50, 0.50, 0.33),
    ('huong thang, lui xa', 0, 0, 0, 0.50, 0.50, 0.62),
    ('xoay 45° trong mp + nghieng 20°', 20, 0, 45, 0.50, 0.50, 0.45),

    ('canh TRAI toi truoc 27°', 27, 0, 0, 0.30, 0.35, 0.45),
    ('canh TRAI toi truoc 45°', 45, 0, 0, 0.28, 0.65, 0.45),
    ('canh PHAI toi truoc 27°', -27, 0, 0, 0.70, 0.35, 0.45),
    ('canh PHAI toi truoc 45°', -45, 0, 0, 0.72, 0.65, 0.45),

    ('mep TREN nga ra sau 27°', 0, 27, 0, 0.35, 0.28, 0.45),
    ('mep TREN nga ra sau 45°', 0, 45, 0, 0.65, 0.28, 0.45),
    ('mep TREN cui toi 27°', 0, -27, 0, 0.35, 0.72, 0.45),
    ('mep TREN cui toi 45°', 0, -45, 0, 0.65, 0.72, 0.45),

    ('TRAI 35° + TREN nga 25°', 35, 25, 0, 0.22, 0.30, 0.42),
    ('PHAI 35° + TREN nga 25°', -35, 25, 0, 0.78, 0.30, 0.42),
    ('TRAI 35° + TREN cui 25°', 35, -25, 0, 0.22, 0.70, 0.42),
    ('PHAI 35° + TREN cui 25°', -35, -25, 0, 0.78, 0.70, 0.42),
]


def board_bitmap(px_per_square=26):
    """Ảnh bàn cờ (có lề trắng) để dán vào khung hình."""
    m = int(round(MARGIN / SQUARE * px_per_square))
    img = np.full((ROWS * px_per_square + 2 * m, COLS * px_per_square + 2 * m), 255, np.uint8)
    for r in range(ROWS):
        for c in range(COLS):
            if (r + c) % 2 == 0:
                img[m + r * px_per_square:m + (r + 1) * px_per_square,
                    m + c * px_per_square:m + (c + 1) * px_per_square] = 0
    return img


def render(vertical_deg, horizontal_deg, spin_deg, u_frac, v_frac, z):
    """(ảnh khung hình, độ nghiêng so với trục ngắm) cho một tư thế."""
    ry = cv2.Rodrigues(np.array([0.0, math.radians(vertical_deg), 0.0]))[0]
    rx = cv2.Rodrigues(np.array([math.radians(horizontal_deg), 0.0, 0.0]))[0]
    rz = cv2.Rodrigues(np.array([0.0, 0.0, math.radians(spin_deg)]))[0]
    R = ry @ rx @ rz
    u, v = u_frac * W, v_frac * H
    t = np.array([(u - CX) * z / F, (v - CY) * z / F, z])

    hw, hh = BOARD[0] / 2 + MARGIN, BOARD[1] / 2 + MARGIN
    corners = np.array([[-hw, -hh, 0], [hw, -hh, 0], [hw, hh, 0], [-hw, hh, 0]], float)
    cam = corners @ R.T + t
    uv = np.stack([F * cam[:, 0] / cam[:, 2] + CX, F * cam[:, 1] / cam[:, 2] + CY], axis=1)

    bitmap = board_bitmap()
    bh, bw = bitmap.shape
    src = np.array([[0, 0], [bw, 0], [bw, bh], [0, bh]], np.float32)
    matrix = cv2.getPerspectiveTransform(src, uv.astype(np.float32))
    frame = cv2.warpPerspective(bitmap, matrix, (W, H), borderValue=60)
    normal = R @ np.array([0.0, 0.0, 1.0])
    return frame, math.degrees(math.acos(min(1.0, abs(normal[2]))))


def main():
    matplotlib.rcParams['pdf.fonttype'] = 42
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    frames = [render(*p[1:]) for p in POSES]

    fig = plt.figure(figsize=(A4[0] / 25.4, A4[1] / 25.4))
    fig.subplots_adjust(0, 0, 1, 1)
    head = fig.add_axes([0, 0.80, 1, 0.20])
    head.axis('off')
    head.text(0.5, 0.90, 'HIEU CHUAN NOI THAM SO — 16 TU THE CAM BAN CO', ha='center',
              fontsize=13, weight='bold')
    head.text(0.5, 0.78, 'Cam ban co sao cho hinh tren man hinh GIONG hinh trong o.',
              ha='center', fontsize=9)
    rules = [
        '1. CAM TREN TAY, dung de ban co nam tren ban. De tren ban thi moi khung cung mot huong,',
        '    va bo giai KHONG tach duoc tieu cu voi khoang cach — day la loi hay gap nhat.',
        '2. Dan ban co len BIA CUNG. Giay cong la sai so di thang vao ket qua.',
        '3. Moi tu the: dua toi cho roi GIU YEN ~1 giay, cho script bao "nhan khung N/16"',
        '    roi moi doi tu the. Dang di chuyen thi no khong nhan.',
        '4. Chup du 16 o theo thu tu; script tu nhac con thieu goc anh nao / do nghieng nao.',
        '5. Khoang cach 33–62 cm. Gan duoi 30 cm thi C270 mo (lay net co dinh).',
    ]
    for i, line in enumerate(rules):
        head.text(0.045, 0.64 - 0.093 * i, line, fontsize=8, va='top', family='DejaVu Sans')

    for i, ((name, *_), (frame, tilt)) in enumerate(zip(POSES, frames)):
        r, c = divmod(i, 4)
        ax = fig.add_axes([0.035 + 0.2425 * c, 0.655 - 0.185 * r, 0.215, 0.125])
        ax.imshow(frame, cmap='gray', vmin=0, vmax=255)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_edgecolor('0.3')
        ax.set_title(f'{i + 1}. {name}', fontsize=6.6, pad=2.5)
        ax.set_xlabel(f'nghieng {tilt:.0f}°', fontsize=6, labelpad=1.5)

    tilts = [t for _, t in frames]
    groups = (sum(t < 15 for t in tilts), sum(15 <= t < 30 for t in tilts),
              sum(t >= 30 for t in tilts))
    foot = fig.add_axes([0, 0, 1, 0.072])
    foot.axis('off')
    foot.text(0.5, 0.80, 'Lenh:  python3 src/delta_controller/scripts/'
              'calibrate_intrinsics.py --show --views 16',
              ha='center', fontsize=8.5, family='DejaVu Sans Mono')
    foot.text(0.5, 0.45, f'Bo 16 tu the nay cho: phang {groups[0]} khung, nghieng vua '
              f'{groups[1]}, nghieng manh {groups[2]} — dat yeu cau toi thieu 2 / 5 / 6.',
              ha='center', fontsize=7.5)
    foot.text(0.5, 0.13, 'Anh trong bang duoc DUNG LAI qua mo hinh camera C270 da hieu chuan '
              '(f = 1279 px, 1280x720).', ha='center', fontsize=6.5, color='0.4')

    with PdfPages(OUT) as pdf:
        pdf.savefig(fig)
    plt.close(fig)
    print(f'Da ghi {OUT}')
    print(f'  phang {groups[0]} | nghieng vua {groups[1]} | nghieng manh {groups[2]}')


if __name__ == '__main__':
    main()
