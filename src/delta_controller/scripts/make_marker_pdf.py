#!/usr/bin/env python3
"""
Tạo file PDF in marker ArUco hiệu chuẩn camera, đúng kích thước, từ scene.py.

    python3 src/delta_controller/scripts/make_marker_pdf.py          # bàn THẬT (Bước 10a)
    python3 src/delta_controller/scripts/make_marker_pdf.py --sim    # bố trí trong cảnh mô phỏng

Trang 1: hướng dẫn + sơ đồ bố trí + bảng tọa độ; các trang sau mỗi trang 2 marker (ô đen đúng
kích thước khai báo). Vẽ bằng vector nên in ở 100% là ra đúng kích thước thật.

⚠️ Bố trí THẬT không phải bố trí ảo nhân SCALE: bố trí ảo nhân 3 trải 810x870 mm, không vừa bàn
rộng 600 mm. Xem scene.REAL_CALIB_MARKERS và scene.real_calib_markers_virtual().
"""

import os
import sys

import cv2
from delta_controller.scene import (
    BIN_OUTER_HALF,
    BINS,
    CALIB_ARUCO_DICT,
    CALIB_MARKER_SIZE,
    CALIB_MARKERS,
    OBJECTS,
    REAL_CALIB_MARKER_SIZE,
    REAL_CALIB_MARKERS,
    real_calib_markers_virtual,
    REAL_OBJECT_AREA_X,
    REAL_OBJECT_AREA_Y,
    REAL_TABLE,
    SCALE,
    SIDE_CAMERA_GT_XYZ,
)
import matplotlib
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Circle, Rectangle
import matplotlib.pyplot as plt

A4 = (210.0, 297.0)                       # mm
DOCS = os.path.expanduser('~/ros2_closed_loop_ws/docs/calibration')


class Layout:
    """Một bố trí marker: tọa độ tâm, kích thước ô đen, tên file, cách vẽ sơ đồ."""

    def __init__(self, real):
        self.real = real
        self.markers = REAL_CALIB_MARKERS if real else CALIB_MARKERS
        self.size = 1000.0 * (REAL_CALIB_MARKER_SIZE if real else CALIB_MARKER_SIZE)
        self.module = self.size / 6.0     # 4x4 bit + viền đen 1 ô mỗi phía
        self.tile = self.size + 2 * self.module    # tấm có lề trắng 1 ô mỗi phía
        self.out = os.path.join(DOCS, 'aruco_markers_real_A4.pdf' if real
                                else 'aruco_markers_A4.pdf')
        self.diagram_scale = 1 / 4.0 if real else 1 / 3.0


def new_page():
    fig = plt.figure(figsize=(A4[0] / 25.4, A4[1] / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, A4[0])
    ax.set_ylim(0, A4[1])
    ax.set_aspect('equal')
    ax.axis('off')
    return fig, ax


def draw_marker(ax, lay, marker_id, cx, cy, dictionary):
    bits = cv2.aruco.drawMarker(dictionary, marker_id, 6)   # 6x6: 0 = đen, 255 = trắng
    x0, y0 = cx - lay.size / 2, cy - lay.size / 2
    for r in range(6):
        for c in range(6):
            if bits[r, c] == 0:
                ax.add_patch(Rectangle((x0 + c * lay.module, y0 + (5 - r) * lay.module),
                                       lay.module, lay.module, color='black', lw=0))
    ax.add_patch(Rectangle((cx - lay.tile / 2, cy - lay.tile / 2), lay.tile, lay.tile,
                           fill=False, ls=(0, (3, 2)), lw=0.6, ec='0.4'))
    for d in (-1, 1):   # dấu căn tâm, nằm ngoài đường cắt
        near, far = lay.tile / 2 + 3, lay.tile / 2 + 12
        ax.plot([cx + d * near, cx + d * far], [cy, cy], color='black', lw=0.6)
        ax.plot([cx, cx], [cy + d * near, cy + d * far], color='black', lw=0.6)


def scale_bar(ax, lay, x, y):
    ax.plot([x, x + 100], [y, y], color='black', lw=0.8)
    for k in range(0, 101, 10):
        h = 3 if k % 50 == 0 else 1.5
        ax.plot([x + k, x + k], [y, y + h], color='black', lw=0.6)
    ax.text(x + 50, y - 4, 'Thước kiểm tra: đo phải đúng 100 mm (ô đen marker đúng '
            f'{lay.size:.0f} mm)', ha='center', va='top', fontsize=7)


def diagram_sim(ax, lay, P, s):
    """Sơ đồ cảnh MÔ PHỎNG: vùng gắp được, ba khay, ba lon ở chỗ xuất phát."""
    ax.add_patch(Circle(P(0, 0), 119 * s, fill=False, ls=':', ec='tab:green', lw=0.8))
    ax.text(*P(-75, 75), 'vùng robot\ngắp được', fontsize=5.5, color='tab:green', ha='center')
    for name, (bx, by) in BINS.items():
        half = 1000 * BIN_OUTER_HALF
        px, py = P(1000 * bx + half, 1000 * by + half)
        ax.add_patch(Rectangle((px, py - 2 * half * s), 2 * half * s, 2 * half * s,
                               fill=False, ec='darkorange', lw=0.8))
    ax.text(*P(1000 * list(BINS.values())[0][0], 0), 'khay', fontsize=6, color='darkorange',
            ha='center', va='center')
    for obj in OBJECTS:
        ax.add_patch(Circle(P(1000 * obj.home_xy[0], 1000 * obj.home_xy[1]),
                            1000 * obj.half_width * s,
                            color={'red': 'tab:red', 'green': 'tab:green',
                                   'blue': 'tab:blue'}[obj.color], alpha=0.6))


def diagram_real(ax, lay, P, s):
    """Sơ đồ bàn THẬT: mép bàn, vùng đặt lon."""
    half_w = 1000 * REAL_TABLE[0] / 2
    x0, x1 = 1000 * REAL_OBJECT_AREA_X[0], 1000 * REAL_OBJECT_AREA_X[1]
    y0, y1 = 1000 * REAL_OBJECT_AREA_Y[0], 1000 * REAL_OBJECT_AREA_Y[1]
    px, py = P(-200, half_w)
    ax.add_patch(Rectangle((px, py), 2 * half_w * s, 700 * s, fill=False, ec='0.6', lw=0.8))
    ax.text(*P(480, 0), f'mép bàn (rộng {2 * half_w:.0f} mm)', fontsize=6, color='0.45',
            ha='center')
    px, py = P(x0, y1)
    ax.add_patch(Rectangle((px, py), (y1 - y0) * s, (x1 - x0) * s, fill=False,
                           ec='tab:green', ls=':', lw=1.0))
    ax.text(*P((x0 + x1) / 2, (y0 + y1) / 2), 'vùng đặt lon\n(quy về ảo: trong tầm với)',
            fontsize=5.8, color='tab:green', ha='center', va='center')


def page_instructions(pdf, lay):
    fig, ax = new_page()
    where = 'BÀN THẬT' if lay.real else 'CẢNH MÔ PHỎNG'
    ax.text(105, 283, f'MARKER HIỆU CHUẨN CAMERA — {where}', ha='center', fontsize=13,
            weight='bold')
    ax.text(105, 276, f'ArUco {CALIB_ARUCO_DICT}, ô đen {lay.size:.0f} mm, '
            f'{len(lay.markers)} marker (ID {min(lay.markers)}–{max(lay.markers)})',
            ha='center', fontsize=9)
    steps = [
        '1. In các trang sau ở tỉ lệ 100% ("Actual size", TẮT "Fit to page"). '
        'Đo thước dưới mỗi trang: phải đúng 100 mm.',
        '2. Cắt từng marker theo đường nét đứt (GIỮ NGUYÊN lề trắng quanh ô đen — bắt buộc để '
        'nhận dạng được).',
        '3. Trên mặt bàn: đánh dấu điểm O và kẻ trục X, Y như sơ đồ. +X hướng ra XA camera, '
        '+Y sang trái khi đứng ở chỗ camera nhìn vào.',
        '4. Dán tâm mỗi marker đúng tọa độ trong bảng (đo từ O theo trục X, Y). Marker xoay '
        'chiều nào cũng được, miễn nằm phẳng.',
        '5. Đặt camera phía −X, nhìn xiên xuống, trong khung hình thấy đủ marker và cả vùng '
        'đặt lon.',
        '6. Dán phẳng, không nhăn, không cong mép: dán lệch 1 mm là sai vị trí vật ~1 mm.',
    ]
    for i, line in enumerate(steps):
        ax.text(15, 266 - 6.5 * i, line, fontsize=7.2, va='top', wrap=True)

    s = lay.diagram_scale
    ox, oy = 105, 145      # điểm O trên giấy
    ax.text(105, 218, f'Sơ đồ bố trí (nhìn từ trên xuống, tỉ lệ 1:{1 / s:.0f})', ha='center',
            fontsize=9, weight='bold')

    def P(x_mm, y_mm):   # trục X hướng LÊN trên giấy, Y hướng sang TRÁI
        return ox - y_mm * s, oy + x_mm * s

    (diagram_real if lay.real else diagram_sim)(ax, lay, P, s)

    for marker_id, (x, y) in lay.markers.items():
        px, py = P(1000 * x, 1000 * y)
        ax.add_patch(Rectangle((px - lay.tile * s / 2, py - lay.tile * s / 2),
                               lay.tile * s, lay.tile * s, color='black'))
        ax.text(px, py, str(marker_id), color='white', ha='center', va='center', fontsize=7,
                weight='bold')
    ax.annotate('', xy=P(170, 0), xytext=P(0, 0),
                arrowprops={'arrowstyle': '->', 'lw': 1.2, 'color': 'tab:red'})
    ax.text(*P(178, 0), '+X', color='tab:red', fontsize=7, ha='center', va='bottom')
    ax.annotate('', xy=P(0, 150), xytext=P(0, 0),
                arrowprops={'arrowstyle': '->', 'lw': 1.2, 'color': 'tab:blue'})
    ax.text(*P(0, 158), '+Y', color='tab:blue', fontsize=7, ha='center', va='bottom')
    ax.plot(*P(0, 0), 'k+', ms=8)
    ax.text(*P(-10, -10), 'O', fontsize=8, weight='bold', ha='left', va='top')
    cam = 1000 * SIDE_CAMERA_GT_XYZ[0] * (SCALE if lay.real else 1)
    ax.text(ox, 88, f'▼ camera đặt phía này (X âm, gợi ý X ≈ {cam:.0f} mm), nhìn xiên xuống',
            ha='center', va='top', fontsize=6.5)

    # Bảng tọa độ
    ax.text(15, 74, 'Tọa độ TÂM marker, đo từ O (mm):', fontsize=8, weight='bold')
    virtual = real_calib_markers_virtual() if lay.real else None
    for row, (marker_id, (x, y)) in enumerate(sorted(lay.markers.items())):
        text = f'ID {marker_id}:  X = {1000 * x:+5.0f},  Y = {1000 * y:+5.0f}'
        if virtual:
            vx, vy = virtual[marker_id]
            text += f'      ->  ao ({1000 * vx:+6.1f}, {1000 * vy:+6.1f})'
        ax.text(15, 67 - 6 * row, text, fontsize=7.5, family='DejaVu Sans Mono')
    if lay.real:
        note = (f'Cột "ảo" = cột thật chia SCALE = {SCALE:.1f}. ĐÂY mới là số đưa vào PnP khi '
                'hiệu chuẩn, nhờ vậy cả khối thị giác chạy nguyên trong hệ ảo.')
    else:
        note = 'Tọa độ này phải khớp scene.CALIB_MARKERS trong code.'
    ax.text(15, 67 - 6 * len(lay.markers) - 4, note, fontsize=6.5, color='0.35', wrap=True)
    pdf.savefig(fig)
    plt.close(fig)


def page_markers(pdf, lay, ids, dictionary, page_no):
    fig, ax = new_page()
    for (marker_id, cy) in zip(ids, (205, 85)):
        x, y = lay.markers[marker_id]
        draw_marker(ax, lay, marker_id, 105, cy, dictionary)
        ax.text(105, cy + lay.tile / 2 + 14, f'ID {marker_id}', ha='center', fontsize=12,
                weight='bold')
        ax.text(105, cy - lay.tile / 2 - 14, f'Dán TÂM marker tại X = {1000 * x:+.0f} mm, '
                f'Y = {1000 * y:+.0f} mm', ha='center', fontsize=8.5)
    scale_bar(ax, lay, 55, 16)
    ax.text(200, 5, f'trang {page_no}', ha='right', fontsize=6, color='0.5')
    pdf.savefig(fig)
    plt.close(fig)


def main():
    lay = Layout(real='--sim' not in sys.argv)
    matplotlib.rcParams['pdf.fonttype'] = 42   # nhúng font TrueType -> tiếng Việt hiển thị đúng
    dictionary = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, CALIB_ARUCO_DICT))
    os.makedirs(DOCS, exist_ok=True)
    ids = sorted(lay.markers)
    with PdfPages(lay.out) as pdf:
        page_instructions(pdf, lay)
        for k in range(0, len(ids), 2):
            page_markers(pdf, lay, ids[k:k + 2], dictionary, 2 + k // 2)
    print(f'Da ghi {lay.out}')


if __name__ == '__main__':
    main()
