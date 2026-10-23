#!/usr/bin/env python3
"""
Sinh hình cho Chương 4–6 của khóa luận bản 2.

    python3 docs/tools/make_thesis_figures_ch456.py

Số liệu lấy từ các phép đo đã ghi trong tài liệu dự án, khai báo tập trung ở đầu tệp để hình và
bảng trong bài không bao giờ nói hai con số khác nhau.
"""

import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.patches as patches                               # noqa: E402
import matplotlib.pyplot as plt                                    # noqa: E402
import numpy as np                                                 # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'figures')
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9})
INK, ACC, WARN, OK, MUTED = '#1f2933', '#2563eb', '#dc2626', '#059669', '#9aa5b1'

# (nhãn, sai số TRƯỚC, sai số SAU, đơn vị, cách khắc phục)
REDUCTIONS = [
    ('Vật trong khay\n(mô phỏng)', 13.4, 1.0, 'khớp mép trên'),
    ('Vật trên bàn,\nmặt nạ màu', 28.0, 1.8, 'khớp mép đáy'),
    ('Vật trên bàn thật,\nbàn phản chiếu', 11.4, 4.5, 'khớp mép trên'),
    ('Vật đứng trên\nbăng tải', 76.0, 1.0, 'giả thuyết mặt đỡ'),
    ('Nhiễu vị trí\n(camera thật)', 13.8, 0.9, 'trừ ảnh nền'),
    ('Thời điểm ra lệnh hút', 47.0, 2.0, 'chờ vị trí đo được'),
    ('Vật ở vùng xa\nbị bàn máy che', 17.0, 0.3, 'tư thế quan sát'),
]


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'  {name}')


def giam_sai_so():
    """Biểu đồ trước–sau của bảy phép khắc phục sai số lớn nhất."""
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    y = np.arange(len(REDUCTIONS))[::-1]
    before = [r[1] for r in REDUCTIONS]
    after = [r[2] for r in REDUCTIONS]
    ax.barh(y + 0.19, before, height=0.34, color='#fecaca', edgecolor=WARN, lw=1.1,
            label='trước khi khắc phục')
    ax.barh(y - 0.19, after, height=0.34, color='#bbf7d0', edgecolor=OK, lw=1.1,
            label='sau khi khắc phục')
    for i, (lbl, b, a, how) in zip(y, REDUCTIONS):
        ax.text(b + 1.4, i + 0.19, f'{b:.1f}'.replace('.', ','), va='center', fontsize=8,
                color=WARN)
        ax.text(a + 1.4, i - 0.19, f'{a:.1f}'.replace('.', ','), va='center', fontsize=8,
                color=OK)
        ax.text(86, i, how, va='center', ha='left', fontsize=7.5, color=MUTED, style='italic')
    ax.axvline(12, color=ACC, lw=1.6, ls='--')
    ax.text(13.0, 2.6, 'dung sai cơ cấu hút\n12 mm', fontsize=8, color=ACC, va='center')
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in REDUCTIONS], fontsize=8)
    ax.set_xlabel('sai số (mm, hệ ảo)')
    ax.set_xlim(0, 112)
    ax.set_title('Bảy phép khắc phục sai số, đo trước và sau', fontsize=10.5, color=INK)
    ax.legend(loc='lower right', fontsize=8, framealpha=0.95)
    ax.grid(axis='x', alpha=0.25, lw=0.5)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    save(fig, 'kl456_giam_sai_so.png')


def may_trang_thai():
    """Máy trạng thái vòng băng tải và chỗ bàn giao quyền vị trí."""
    fig, ax = plt.subplots(figsize=(8.0, 3.4))
    states = [('CHỜ VẬT', 'chưa có vật\ntrên băng'), ('BÁM VẬT', 'đầu hút lên\ntrên nắp vật'),
              ('ĐANG CHẠY', 'băng chạy,\nrobot bám theo'), ('DỪNG BĂNG', 'vật tới\nđiểm gắp'),
              ('ĐANG GẮP', 'hút và thả\nvào khay'), ('NHẢ QUYỀN', 'chờ tay người\nnhấc vật thật')]
    w, gap = 1.12, 0.26
    for i, (name, sub) in enumerate(states):
        x = i * (w + gap)
        frozen = i >= 4
        ax.add_patch(patches.FancyBboxPatch((x, 0.9), w, 0.72, boxstyle='round,pad=0.03',
                                            fc='#fef3c7' if frozen else '#dbeafe',
                                            ec='#b45309' if frozen else ACC, lw=1.4))
        ax.text(x + w / 2, 1.42, name, ha='center', fontsize=8.5, color=INK)
        ax.text(x + w / 2, 1.12, sub, ha='center', fontsize=7, color='#4b5563')
        if i:
            ax.annotate('', xy=(x - 0.02, 1.26), xytext=(x - gap + 0.02, 1.26),
                        arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.2))
    span = len(states) * (w + gap) - gap
    ax.annotate('', xy=(0.02, 0.72), xytext=(span - 0.02, 0.72),
                arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.2,
                                connectionstyle='arc3,rad=0.12'))
    ax.text(span / 2, 0.36, 'tay người đặt vật tiếp theo lên băng', ha='center', fontsize=8,
            color=INK)
    x0 = 4 * (w + gap)
    ax.add_patch(patches.FancyBboxPatch((x0 - 0.06, 1.74), 2 * w + gap + 0.12, 0.32,
                                        boxstyle='round,pad=0.02', fc='#fff7ed', ec='#b45309',
                                        lw=1.2, ls='--'))
    ax.text(x0 + w + gap / 2, 1.90, 'MÔ PHỎNG giữ quyền quyết định vị trí vật',
            ha='center', va='center', fontsize=8.5, color='#b45309')
    ax.text(span / 2, 2.25, 'Camera giữ quyền quyết định vị trí vật', ha='center', fontsize=8.5,
            color=ACC)
    ax.annotate('', xy=(x0 - 0.1, 2.18), xytext=(0.0, 2.18),
                arrowprops=dict(arrowstyle='-', color=ACC, lw=1.4))
    ax.set_xlim(-0.2, span + 0.2)
    ax.set_ylim(0.2, 2.45)
    ax.axis('off')
    save(fig, 'kl456_may_trang_thai.png')


def vong_kin():
    """Luồng thông tin của vòng khép kín hai chiều."""
    fig, ax = plt.subplots(figsize=(7.8, 3.0))
    boxes = [(0.1, 'VẬT THẬT\ntrên băng tải', '#fee2e2', WARN),
             (1.6, 'CAMERA\nC270', '#dbeafe', ACC),
             (3.1, 'KHỐI THỊ GIÁC\nđịnh vị + cờ tin cậy', '#dbeafe', ACC),
             (4.9, 'BẢN SAO SỐ\nvật ảo trong Gazebo', '#dcfce7', OK),
             (6.7, 'ROBOT ẢO\ngắp và phân loại', '#dcfce7', OK)]
    for x, label, fc, ec in boxes:
        ax.add_patch(patches.FancyBboxPatch((x, 1.15), 1.35, 0.72, boxstyle='round,pad=0.03',
                                            fc=fc, ec=ec, lw=1.4))
        ax.text(x + 0.675, 1.51, label, ha='center', va='center', fontsize=8, color=INK)
    for a, b in zip(boxes, boxes[1:]):
        ax.annotate('', xy=(b[0] - 0.03, 1.51), xytext=(a[0] + 1.38, 1.51),
                    arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.3))
    ax.text(4.0, 1.98, 'chiều thuận: thế giới thật → mô hình số  (bóng số)', ha='center',
            fontsize=8.5, color=ACC)
    ax.annotate('', xy=(0.6, 0.72), xytext=(7.3, 0.72),
                arrowprops=dict(arrowstyle='-|>', color='#b45309', lw=1.6,
                                connectionstyle='arc3,rad=0.1'))
    ax.text(4.0, 0.28, 'chiều ngược: mô phỏng RA LỆNH dừng băng tải thật  (bản sao số đầy đủ)',
            ha='center', fontsize=8.5, color='#b45309')
    ax.set_xlim(-0.1, 8.3)
    ax.set_ylim(0.05, 2.25)
    ax.axis('off')
    save(fig, 'kl456_vong_kin.png')


def main():
    os.makedirs(OUT, exist_ok=True)
    print('Sinh hình Chương 4–6:')
    for fn in (giam_sai_so, may_trang_thai, vong_kin):
        fn()
    print('Xong.')


if __name__ == '__main__':
    sys.exit(main())
