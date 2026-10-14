#!/usr/bin/env python3
"""
Sinh hình minh họa cho Chương 3 và Chương 4 của khóa luận bản 2.

    python3 docs/tools/make_thesis_figures_ch34.py

Mọi hình vẽ từ HẰNG SỐ THẬT trong mã nguồn (`scene.py`, `gripper_logic.py`, `vision_estimation.py`)
chứ không phác tay, nên hình luôn khớp con số viết trong bài. Sửa một hằng số rồi chạy lại là hình
tự đúng theo — không có chuyện hình nói một đằng, bảng nói một nẻo.

Tên tệp bắt đầu bằng `kl34_` để không lẫn với hình của Chương 1–2 (`kl_`).
"""

import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.patches as patches                               # noqa: E402
import matplotlib.pyplot as plt                                    # noqa: E402
import numpy as np                                                 # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'src', 'delta_controller'))
OUT = os.path.join(HERE, '..', 'figures')

from delta_controller import scene                                 # noqa: E402
from delta_controller.gripper_logic import GraspTolerance        # noqa: E402
from delta_controller.vision_estimation import VISIBLE_MAX, VISIBLE_MIN   # noqa: E402

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9})
INK, ACC, WARN, OK = '#1f2933', '#2563eb', '#dc2626', '#059669'
MUTED = '#9aa5b1'


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'  {name}')


# ------------------------------------------------------------------ Chương 3
def mach_kin():
    """Vì sao mạch kín phải đóng lúc chạy: cây URDF + mối hàn."""
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.4, 3.3))
    for ax in (a, b):
        ax.set_xlim(-1.25, 1.25)
        ax.set_ylim(-0.35, 2.5)
        ax.axis('off')
    # cây URDF
    a.set_title('Mô hình URDF: chỉ mô tả được CÂY', fontsize=9.5, color=INK)
    a.plot([0], [2.2], 'o', ms=9, color=INK)
    a.text(0, 2.38, 'đế', ha='center', fontsize=8.5, color=INK)
    for i, x in enumerate((-0.85, 0, 0.85)):
        a.plot([0, x], [2.2, 1.5], '-', lw=1.6, color=INK)
        a.plot([x], [1.5], 'o', ms=7, color=INK)
        a.plot([x, x], [1.5, 0.7], '-', lw=1.6, color=INK)
        a.plot([x], [0.7], 'o', ms=7, color=INK)
        a.text(x, 0.45, f'đầu chân {i + 1}', ha='center', fontsize=8, color=INK)
    a.text(0, -0.15, 'ba nhánh RỜI NHAU — bàn máy không thuộc nhánh nào',
           ha='center', fontsize=8.5, color=WARN)
    # dong mach luc chay
    b.set_title('Lúc chạy: hàn bằng khớp tháo rời được', fontsize=9.5, color=INK)
    b.plot([0], [2.2], 'o', ms=9, color=INK)
    for x in (-0.85, 0, 0.85):
        b.plot([0, x], [2.2, 1.5], '-', lw=1.6, color=INK)
        b.plot([x, x], [1.5, 0.7], '-', lw=1.6, color=INK)
        b.plot([x], [1.5], 'o', ms=7, color=INK)
        b.plot([x, 0], [0.7, 0.3], '--', lw=1.8, color=ACC)
    b.add_patch(patches.Rectangle((-0.42, 0.14), 0.84, 0.32, fc='#dbeafe', ec=ACC, lw=1.4))
    b.text(0, 0.3, 'bàn máy', ha='center', va='center', fontsize=8.5, color=INK)
    b.text(0, -0.15, f'{3} mối hàn đóng mạch, tạo lúc khởi động mô phỏng',
           ha='center', fontsize=8.5, color=ACC)
    save(fig, 'kl34_mach_kin.png')


def bo_tri_canh():
    """Bố trí cảnh nhìn từ trên xuống: robot, băng tải, ba khay, camera."""
    fig, ax = plt.subplots(figsize=(6.6, 5.4))
    mm = 1000.0

    def box(cx, cy, w, h, fc, ec, label, lw=1.3, ls='-'):
        ax.add_patch(patches.Rectangle(((cx - w / 2) * mm, (cy - h / 2) * mm), w * mm, h * mm,
                                       fc=fc, ec=ec, lw=lw, ls=ls, zorder=2))
        if label:
            ax.text(cx * mm, cy * mm, label, ha='center', va='center', fontsize=8, color=INK,
                    zorder=3)

    # vung lam viec cua robot o do cao gap
    ax.add_patch(plt.Circle((0, 0), 119, fc='#f1f5f9', ec=MUTED, ls='--', lw=1.2, zorder=0))
    ax.text(34, -128, 'tầm với ở cao độ gắp (r = 119 mm)', ha='center', fontsize=7.5,
            color=MUTED)
    ax.plot([0], [0], '+', ms=12, color=INK, zorder=4)
    ax.text(4, -9, 'gốc robot', fontsize=8, color=INK)

    # bang tai
    box(scene.BELT_CENTER[0], scene.BELT_CENTER[1], scene.BELT_WIDTH, scene.BELT_LENGTH,
        '#fef3c7', '#d97706', '')
    ax.text((scene.BELT_CENTER[0] + scene.BELT_WIDTH / 2) * mm + 5,
            (scene.BELT_CENTER[1] - scene.BELT_LENGTH / 2) * mm + 8,
            'băng tải', ha='left', fontsize=8.5, color='#b45309')
    ax.plot([scene.BELT_PICK_XY[0] * mm], [scene.BELT_PICK_XY[1] * mm], 'o', ms=8, color=WARN,
            zorder=5)
    ax.annotate('điểm gắp', (scene.BELT_PICK_XY[0] * mm, scene.BELT_PICK_XY[1] * mm),
                textcoords='offset points', xytext=(16, 6), fontsize=8, color=WARN)
    ax.arrow(scene.BELT_CENTER[0] * mm, (scene.BELT_CENTER[1] - 0.030) * mm, 0, 42,
             head_width=5, head_length=6, fc='#b45309', ec='#b45309', zorder=4, alpha=0.8)

    # ba khay
    for i, (name, (bx, by)) in enumerate(scene.BINS.items()):
        short = name.replace('_can', '')
        side = 2 * scene.BIN_LAYOUT.inner_half
        box(bx, by, side, side, '#e5e7eb', '#6b7280', short)
    ax.text(list(scene.BINS.values())[0][0] * mm, 122, 'ba khay phân loại',
            ha='center', va='center', fontsize=8.5, color='#4b5563')

    # huong camera
    ax.annotate('', xy=(-100, 0), xytext=(-168, 0),
                arrowprops=dict(arrowstyle='-|>', color=ACC, lw=1.8))
    ax.text(-172, 8, 'camera', ha='center', va='bottom', fontsize=8.5, color=ACC)
    ax.text(-172, -16, 'đặt xa,\nchúc 46°', ha='center', va='top', fontsize=7.5, color=ACC)

    ax.set_xlim(-200, 150)
    ax.set_ylim(-150, 150)
    ax.set_aspect('equal')
    ax.set_xlabel('x (mm, hệ ảo)')
    ax.set_ylabel('y (mm, hệ ảo)')
    ax.grid(alpha=0.25, lw=0.5)
    ax.set_title('Bố trí cảnh mô phỏng, nhìn từ trên xuống', fontsize=10, color=INK)
    save(fig, 'kl34_bo_tri_canh.png')


def cua_so_hut():
    """Cửa sổ dung sai của giác hút: lệch ngang và khe đứng."""
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    mm = 1000.0
    tol = GraspTolerance()
    lat, g0, g1 = tol.max_xy_offset * mm, tol.min_gap * mm, tol.max_gap * mm
    ax.add_patch(patches.Rectangle((-lat, g0), 2 * lat, g1 - g0,
                                   fc='#d1fae5', ec=OK, lw=1.6, zorder=2))
    ax.text(0, (g0 + g1) / 2, 'HÚT ĐƯỢC', ha='center', va='center', fontsize=10,
            color='#065f46', zorder=3)
    ax.axhline(0, color=INK, lw=1.2)
    ax.text(lat + 2, 0.3, 'đỉnh vật', fontsize=8, color=INK)
    ax.axvline(0, color=MUTED, lw=0.9, ls='--')
    for x, y, txt, col in (
            (lat + 9, 3, 'lệch ngang quá lớn', WARN),
            (0, g1 + 3.2, 'đầu hút còn cao quá', WARN),
            (0, g0 - 3.6, 'đã ấn vào vật', WARN)):
        ax.text(x, y, txt, ha='center', fontsize=8, color=col)
    ax.set_xlim(-26, 26)
    ax.set_ylim(-8, 12)
    ax.set_xlabel('lệch ngang giữa tâm đầu hút và tâm vật (mm, hệ ảo)')
    ax.set_ylabel('khe (mm)')
    ax.grid(alpha=0.25, lw=0.5)
    ax.set_title(f'Cửa sổ cho phép hút: lệch ngang ≤ {lat:.0f} mm, '
                 f'khe trong [{g0:+.0f}; {g1:+.0f}] mm', fontsize=9.5, color=INK)
    save(fig, 'kl34_cua_so_hut.png')


# ------------------------------------------------------------------ Chương 4
def mo_hinh_camera():
    """Mô hình camera lỗ kim và phép chiếu ngược ra mặt phẳng đã biết cao độ."""
    fig, ax = plt.subplots(figsize=(7.0, 3.8))
    cam = np.array([-2.6, 2.1])
    ax.plot(*cam, 'o', ms=9, color=ACC)
    ax.text(cam[0], cam[1] + 0.22, 'tâm camera', ha='center', fontsize=8.5, color=ACC)
    # mat phang anh
    u = np.array([0.72, -0.58])
    u = u / np.linalg.norm(u)
    n = np.array([-u[1], u[0]])
    c = cam + u * 1.15
    ax.plot(*zip(c - n * 0.72, c + n * 0.72), '-', lw=2.2, color=ACC)
    ax.text(*(c + n * 0.86), 'mặt phẳng ảnh', fontsize=8, color=ACC)
    # mat ban va vat
    ax.plot([-3.4, 3.4], [0, 0], '-', lw=2.0, color=INK)
    ax.text(3.3, 0.12, 'mặt bàn  z = const', ha='right', fontsize=8.5, color=INK)
    obj = np.array([1.5, 0.0])
    ax.add_patch(patches.Rectangle((obj[0] - 0.17, 0), 0.34, 0.82, fc='#fecaca', ec=WARN, lw=1.4))
    ax.text(obj[0], 0.95, 'vật', ha='center', fontsize=8.5, color=WARN)
    # tia
    for tgt, col, ls in ((np.array([1.5, 0.82]), WARN, '-'), (obj, INK, '--')):
        d = tgt - cam
        ax.annotate('', xy=tuple(cam + d * 1.0), xytext=tuple(cam),
                    arrowprops=dict(arrowstyle='-|>', color=col, lw=1.5, ls=ls))
    ax.text(-0.75, 1.45, 'tia qua điểm ảnh', fontsize=8, color=WARN, rotation=-16)
    ax.text(-0.3, 0.52, 'giao với mặt phẳng đã biết z\n→ tọa độ 3D', fontsize=8, color=INK)
    ax.set_xlim(-3.5, 3.5)
    ax.set_ylim(-0.5, 2.6)
    ax.axis('off')
    ax.set_title('Từ điểm ảnh về tọa độ thế giới: giao tia với mặt phẳng đã biết cao độ',
                 fontsize=10, color=INK)
    save(fig, 'kl34_mo_hinh_camera.png')


def khop_mep():
    """Vì sao khớp mép TRÊN chứ không mép đáy khi mặt bàn phản chiếu."""
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 3.6), sharey=True)
    for ax, title, reflect in ((a, 'Mặt bàn KHÔNG phản chiếu', False),
                               (b, 'Mặt bàn PHẢN CHIẾU (thực tế)', True)):
        ax.set_title(title, fontsize=9.5, color=INK)
        ax.add_patch(patches.Rectangle((-0.5, 0), 1.0, 2.4, fc='#fecaca', ec=WARN, lw=1.5))
        ax.plot([-1.6, 1.6], [0, 0], '-', lw=1.8, color=INK)
        if reflect:
            ax.add_patch(patches.Rectangle((-0.5, -0.95), 1.0, 0.95,
                                           fc='#fee2e2', ec=WARN, lw=1.0, ls=':', alpha=0.85))
            ax.text(0, -0.5, 'ảnh phản chiếu', ha='center', fontsize=7.5, color=WARN)
        low = -0.95 if reflect else 0.0
        ax.annotate('', xy=(0.95, 2.4), xytext=(0.95, low),
                    arrowprops=dict(arrowstyle='<->', color=MUTED, lw=1.2))
        ax.text(1.02, (2.4 + low) / 2, 'khung bao\nđo được', fontsize=7.5, color=MUTED)
        ax.axhline(2.4, color=OK, lw=1.8)
        ax.text(-1.55, 2.52, 'mép TRÊN: miệng lon — luôn đúng', fontsize=8, color=OK)
        ax.axhline(low, color=WARN if reflect else OK, lw=1.8, ls='--')
        ax.text(-1.55, low - 0.33,
                'mép đáy: lệch −33 mm' if reflect else 'mép đáy: chỗ lon chạm bàn',
                fontsize=8, color=WARN if reflect else OK)
        ax.set_xlim(-1.6, 1.6)
        ax.set_ylim(-1.5, 3.0)
        ax.axis('off')
    save(fig, 'kl34_khop_mep.png')


def lop_phong_ve():
    """Bốn lớp phòng vệ và loại lỗi mỗi lớp bắt được."""
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    rows = [
        ('Hình học', 'vị trí ngoài vùng đặt vật', 'dây điện, mép bàn, sàn nhà', '#dbeafe', ACC),
        ('Hình dáng', 'bề rộng/chiều cao sai so với\nhình bóng dự đoán',
         'bàn tay, mảnh logo,\nhai vật dính liền', '#dcfce7', OK),
        ('Tỉ lệ nhìn thấy',
         'ngoài [%s; %s]' % (f'{VISIBLE_MIN:.2f}'.replace('.', ','),
                             f'{VISIBLE_MAX:.2f}'.replace('.', ',')),
         'vật bị che một phần', '#fef3c7', '#b45309'),
        ('Xác nhận nhiều khung', 'nhảy xa chưa trụ lại', 'nhiễu thoáng qua', '#fee2e2', WARN),
    ]
    for i, (name, test, catches, fc, ec) in enumerate(rows):
        y = len(rows) - 1 - i
        ax.add_patch(patches.FancyBboxPatch((0.02, y + 0.12), 1.26, 0.76,
                                            boxstyle='round,pad=0.02', fc=fc, ec=ec, lw=1.3))
        ax.text(0.65, y + 0.5, name, ha='center', va='center', fontsize=9, color=INK)
        ax.text(1.42, y + 0.5, test, va='center', fontsize=8, color=INK)
        ax.text(3.05, y + 0.5, catches, va='center', fontsize=8, color='#4b5563')
    ax.text(0.65, len(rows) + 0.22, 'Lớp', ha='center', fontsize=9, color=INK)
    ax.text(1.42, len(rows) + 0.22, 'Hỏi gì', fontsize=9, color=INK)
    ax.text(3.05, len(rows) + 0.22, 'Bắt được loại lỗi nào', fontsize=9, color=INK)
    ax.set_xlim(0, 4.6)
    ax.set_ylim(0, len(rows) + 0.6)
    ax.axis('off')
    save(fig, 'kl34_lop_phong_ve.png')


def main():
    os.makedirs(OUT, exist_ok=True)
    print('Sinh hình Chương 3–4:')
    for fn in (mach_kin, bo_tri_canh, cua_so_hut, mo_hinh_camera, khop_mep, lop_phong_ve):
        fn()
    print('Xong.')


if __name__ == '__main__':
    main()
