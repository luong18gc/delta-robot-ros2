#!/usr/bin/env python3
"""
Tạo file PDF in marker ArUco hiệu chuẩn camera THẬT (Bước 10), đúng kích thước, từ scene.py.

    python3 src/delta_controller/scripts/make_marker_pdf.py
Ghi docs/calibration/aruco_markers_A4.pdf: trang 1 hướng dẫn + sơ đồ bố trí, trang 2–4 mỗi trang
2 marker (ô đen đúng CALIB_MARKER_SIZE), vẽ vector nên in 100% là đúng kích thước.
"""

import os

import cv2
from delta_controller.scene import (
    BIN_CENTER,
    BIN_OUTER_HALF,
    CALIB_ARUCO_DICT,
    CALIB_MARKER_SIZE,
    CALIB_MARKERS,
    OBJECTS,
    SIDE_CAMERA_GT_XYZ,
)
import matplotlib
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Circle, Rectangle
import matplotlib.pyplot as plt

A4 = (210.0, 297.0)                       # mm
SIZE = CALIB_MARKER_SIZE * 1000.0         # ô đen (mm)
MODULE = SIZE / 6.0                       # 4x4 bit + viền đen 1 ô mỗi phía
TILE = SIZE + 2 * MODULE                  # tấm có lề trắng 1 ô mỗi phía
OUT = os.path.expanduser('~/ros2_closed_loop_ws/docs/calibration/aruco_markers_A4.pdf')


def new_page():
    fig = plt.figure(figsize=(A4[0] / 25.4, A4[1] / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, A4[0])
    ax.set_ylim(0, A4[1])
    ax.set_aspect('equal')
    ax.axis('off')
    return fig, ax


def draw_marker(ax, marker_id, cx, cy, dictionary):
    bits = cv2.aruco.drawMarker(dictionary, marker_id, 6)   # 6x6: 0 = đen, 255 = trắng
    x0, y0 = cx - SIZE / 2, cy - SIZE / 2
    for r in range(6):
        for c in range(6):
            if bits[r, c] == 0:
                ax.add_patch(Rectangle((x0 + c * MODULE, y0 + (5 - r) * MODULE),
                                       MODULE, MODULE, color='black', lw=0))
    ax.add_patch(Rectangle((cx - TILE / 2, cy - TILE / 2), TILE, TILE, fill=False,
                           ls=(0, (3, 2)), lw=0.6, ec='0.4'))
    for d in (-1, 1):   # dấu căn tâm ngoài đường cắt
        near, far = TILE / 2 + 3, TILE / 2 + 12
        ax.plot([cx + d * near, cx + d * far], [cy, cy], color='black', lw=0.6)
        ax.plot([cx, cx], [cy + d * near, cy + d * far], color='black', lw=0.6)


def scale_bar(ax, x, y):
    ax.plot([x, x + 100], [y, y], color='black', lw=0.8)
    for k in range(0, 101, 10):
        h = 3 if k % 50 == 0 else 1.5
        ax.plot([x + k, x + k], [y, y + h], color='black', lw=0.6)
    ax.text(x + 50, y - 4, 'Thước kiểm tra: đo phải đúng 100 mm (ô đen marker đúng '
            f'{SIZE:.0f} mm)', ha='center', va='top', fontsize=7)


def page_instructions(pdf):
    fig, ax = new_page()
    ax.text(105, 283, 'MARKER HIỆU CHUẨN CAMERA — ĐỒ ÁN ROBOT DELTA', ha='center',
            fontsize=13, weight='bold')
    ax.text(105, 276, f'ArUco {CALIB_ARUCO_DICT}, ô đen {SIZE:.0f} mm, 6 marker (ID 0–5)',
            ha='center', fontsize=9)
    steps = [
        '1. In trang 2–4 ở tỉ lệ 100% ("Actual size", TẮT "Fit to page"). '
        'Đo thước dưới mỗi trang: phải đúng 100 mm.',
        '2. Cắt từng marker theo đường nét đứt (giữ nguyên lề trắng quanh ô đen — bắt buộc để '
        'nhận dạng).',
        '3. Trên mặt bàn: đánh dấu điểm O (ngay dưới tâm đế robot ảo) và kẻ trục X, Y như sơ đồ.',
        '4. Dán tâm mỗi marker đúng tọa độ trong bảng (đo từ O theo trục X, Y). Xoay chiều nào '
        'cũng được.',
        '5. Đặt camera phía −X (sau lưng trục X), nhìn xiên xuống vùng giữa, thấy đủ 6 marker.',
        '6. Dán phẳng, không nhăn; sai 1 mm khi dán ≈ sai ~1 mm vị trí vật.',
    ]
    for i, line in enumerate(steps):
        ax.text(15, 266 - 6.5 * i, line, fontsize=7.2, va='top', wrap=True)

    # Sơ đồ bố trí, tỉ lệ 1:3 (1 mm giấy = 3 mm thật)
    s = 1 / 3.0
    ox, oy = 105, 142      # điểm O trên giấy
    ax.text(105, 214, 'Sơ đồ bố trí (nhìn từ trên xuống, tỉ lệ 1:3)', ha='center', fontsize=9,
            weight='bold')
    ax.add_patch(Rectangle((ox - 200 * s, oy - 200 * s), 400 * s, 400 * s, fill=False,
                           ec='0.6', lw=0.8))
    ax.text(ox + 200 * s - 2, oy - 200 * s + 2, 'bàn 40×40 cm', ha='right', fontsize=6,
            color='0.4')

    def P(x_mm, y_mm):   # trục X robot hướng LÊN trên giấy, Y hướng sang TRÁI
        return ox - y_mm * s, oy + x_mm * s

    ax.add_patch(Circle(P(0, 0), 96 * s, fill=False, ls=':', ec='tab:green', lw=0.8))
    ax.text(*P(-60, 70), 'vùng robot\ngắp được', fontsize=5.5, color='tab:green', ha='center')
    bx, by = P(1000 * (BIN_CENTER[0] + BIN_OUTER_HALF), 1000 * (BIN_CENTER[1] + BIN_OUTER_HALF))
    ax.add_patch(Rectangle((bx, by - 2000 * BIN_OUTER_HALF * s), 2000 * BIN_OUTER_HALF * s,
                           2000 * BIN_OUTER_HALF * s, fill=False, ec='darkorange', lw=0.8))
    ax.text(*P(1000 * BIN_CENTER[0], 1000 * BIN_CENTER[1]), 'khay', fontsize=6,
            color='darkorange', ha='center', va='center')
    for obj in OBJECTS:
        ax.add_patch(Circle(P(1000 * obj.home_xy[0], 1000 * obj.home_xy[1]), 15 * s,
                            color={'red': 'tab:red', 'green': 'tab:green',
                                   'blue': 'tab:blue'}[obj.color], alpha=0.6))
    for marker_id, (x, y) in CALIB_MARKERS.items():
        px, py = P(1000 * x, 1000 * y)
        ax.add_patch(Rectangle((px - TILE * s / 2, py - TILE * s / 2), TILE * s, TILE * s,
                               color='black'))
        ax.text(px, py, str(marker_id), color='white', ha='center', va='center', fontsize=8,
                weight='bold')
    ax.annotate('', xy=P(170, 0), xytext=P(0, 0),
                arrowprops={'arrowstyle': '->', 'lw': 1.2, 'color': 'tab:red'})
    ax.text(*P(175, 0), '+X (hướng ra chân 1 robot)', color='tab:red', fontsize=6.5,
            ha='center', va='bottom')
    ax.annotate('', xy=P(0, 170), xytext=P(0, 0),
                arrowprops={'arrowstyle': '->', 'lw': 1.2, 'color': 'tab:blue'})
    ax.text(*P(0, 120), '+Y', color='tab:blue', fontsize=7, ha='center', va='bottom')
    ax.plot(*P(0, 0), 'k+', ms=8)
    ax.text(*P(-8, -8), 'O', fontsize=8, weight='bold', ha='left', va='top')
    cam_x = 1000 * SIDE_CAMERA_GT_XYZ[0]
    ax.text(ox, oy - 200 * s - 3, f'▼ camera đặt phía này, ngoài mép bàn (X ≈ {cam_x:.0f} mm), '
            'nhìn xiên xuống', ha='center', va='top', fontsize=6.5)

    # Bảng tọa độ
    ax.text(15, 50, 'Tọa độ TÂM marker (mm, tính từ O):', fontsize=8, weight='bold')
    for i, (marker_id, (x, y)) in enumerate(CALIB_MARKERS.items()):
        col, row = i % 3, i // 3
        ax.text(15 + 62 * col, 43 - 6 * row,
                f'ID {marker_id}:  X = {1000 * x:+.0f},  Y = {1000 * y:+.0f}', fontsize=8,
                family='DejaVu Sans Mono')
    ax.text(15, 24, 'Tọa độ này phải khớp scene.CALIB_MARKERS trong code '
            '(src/delta_controller/delta_controller/scene.py).', fontsize=6.5, color='0.35')
    pdf.savefig(fig)
    plt.close(fig)


def page_markers(pdf, ids, dictionary, page_no):
    fig, ax = new_page()
    for (marker_id, cy) in zip(ids, (210, 90)):
        x, y = CALIB_MARKERS[marker_id]
        draw_marker(ax, marker_id, 105, cy, dictionary)
        ax.text(105, cy + TILE / 2 + 16, f'ID {marker_id}', ha='center', fontsize=12,
                weight='bold')
        ax.text(105, cy - TILE / 2 - 16, f'Dán TÂM marker tại X = {1000 * x:+.0f} mm, '
                f'Y = {1000 * y:+.0f} mm', ha='center', fontsize=8.5)
    scale_bar(ax, 55, 18)
    ax.text(200, 5, f'trang {page_no}', ha='right', fontsize=6, color='0.5')
    pdf.savefig(fig)
    plt.close(fig)


def main():
    matplotlib.rcParams['pdf.fonttype'] = 42   # nhúng font TrueType -> tiếng Việt hiển thị đúng
    dictionary = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, CALIB_ARUCO_DICT))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    ids = sorted(CALIB_MARKERS)
    with PdfPages(OUT) as pdf:
        page_instructions(pdf)
        for k in range(0, len(ids), 2):
            page_markers(pdf, ids[k:k + 2], dictionary, 2 + k // 2)
    print(f'Da ghi {OUT}')


if __name__ == '__main__':
    main()
