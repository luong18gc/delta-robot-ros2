#!/usr/bin/env python3
"""
Tạo file PDF in bảng cờ hiệu chuẩn NỘI tham số cho camera thật (Bước 10).

    python3 src/delta_controller/scripts/make_chessboard_pdf.py
Ghi docs/calibration/chessboard_A4.pdf: 1 trang A4, bảng cờ 10x7 ô (9x6 góc trong) cạnh ô
CHESSBOARD_SQUARE mm, vẽ vector nên in 100% (không "fit to page") là đúng kích thước.

Camera mô phỏng là camera lỗ kim lý tưởng (không méo); camera thật có méo ống kính nên phải
đo K và hệ số méo bằng bảng cờ trước khi chạy hiệu chuẩn ngoại tham số bằng marker ArUco.
"""

import os

import matplotlib
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt

A4 = (210.0, 297.0)          # mm
SQUARE = 20.0                # cạnh một ô (mm)
COLS, ROWS = 10, 7           # số ô -> góc trong = (COLS-1) x (ROWS-1) = 9 x 6
OUT = os.path.expanduser('~/ros2_closed_loop_ws/docs/calibration/chessboard_A4.pdf')

matplotlib.rcParams['pdf.fonttype'] = 42


def new_page():
    fig = plt.figure(figsize=(A4[0] / 25.4, A4[1] / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, A4[0])
    ax.set_ylim(0, A4[1])
    ax.set_aspect('equal')
    ax.axis('off')
    return fig, ax


def draw_board(ax, x0, y0):
    """Bảng cờ với ô (0, 0) ở góc dưới trái màu đen."""
    for r in range(ROWS):
        for c in range(COLS):
            if (r + c) % 2 == 0:
                ax.add_patch(Rectangle((x0 + c * SQUARE, y0 + r * SQUARE),
                                       SQUARE, SQUARE, color='black', lw=0))
    ax.add_patch(Rectangle((x0, y0), COLS * SQUARE, ROWS * SQUARE,
                           fill=False, lw=0.4, ec='0.5'))


def scale_bar(ax, x, y, length=100.0):
    """Thước kiểm tra tỉ lệ in: đo bằng thước thật phải đúng length mm."""
    ax.plot([x, x + length], [y, y], color='black', lw=1.0)
    for d in (0, length):
        ax.plot([x + d, x + d], [y - 2, y + 2], color='black', lw=1.0)
    for t in range(0, int(length) + 1, 10):
        ax.plot([x + t, x + t], [y, y + 1.5], color='black', lw=0.5)
    ax.text(x + length / 2, y + 3.5, f'{length:.0f} mm — do bằng thước để kiểm tra tỉ lệ in',
            ha='center', va='bottom', fontsize=7)


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with PdfPages(OUT) as pdf:
        fig, ax = new_page()
        ax.text(A4[0] / 2, 285, 'BẢNG CỜ HIỆU CHUẨN NỘI THAM SỐ CAMERA',
                ha='center', va='top', fontsize=13, weight='bold')
        ax.text(A4[0] / 2, 277,
                f'{COLS} x {ROWS} ô, cạnh ô {SQUARE:.0f} mm  →  '
                f'{COLS - 1} x {ROWS - 1} góc trong (dùng cho findChessboardCorners)',
                ha='center', va='top', fontsize=9)

        board_w, board_h = COLS * SQUARE, ROWS * SQUARE
        draw_board(ax, (A4[0] - board_w) / 2, 120)

        scale_bar(ax, (A4[0] - 100) / 2, 105)

        lines = [
            'CÁCH DÙNG',
            '1. In ở tỉ lệ 100% (KHÔNG chọn "fit to page" / "scale to fit"). In xong đo thanh'
            '   thước phía trên: phải đúng 100 mm, và cạnh một ô phải đúng '
            f'{SQUARE:.0f} mm.',
            '2. Dán phẳng lên một tấm bìa cứng hoặc mặt bàn — bảng cong sẽ làm sai kết quả.',
            '3. Chụp 15–25 ảnh bảng cờ ở nhiều tư thế: gần, xa, nghiêng trái/phải/trên/dưới,',
            '   và để bảng cờ chiếm cả các GÓC của khung hình (méo ống kính lớn nhất ở rìa).',
            '4. Khóa lấy nét thủ công TRƯỚC khi chụp, và giữ nguyên nét đó khi chạy hệ thống:',
            '   đổi nét là đổi tiêu cự, file hiệu chuẩn sẽ không còn đúng.',
            '',
            'Sau bước này mới hiệu chuẩn NGOẠI tham số bằng 6 marker ArUco',
            '(docs/calibration/aruco_markers_A4.pdf) để biết camera đứng ở đâu so với robot.',
        ]
        ax.text(18, 92, '\n'.join(lines), ha='left', va='top', fontsize=8.5, linespacing=1.6)
        pdf.savefig(fig)
        plt.close(fig)
    print(f'Đã ghi {OUT}')
    print(f'  bảng cờ {COLS}x{ROWS} ô, cạnh {SQUARE:.0f} mm, '
          f'{COLS - 1}x{ROWS - 1} góc trong, khổ {board_w:.0f}x{board_h:.0f} mm')


if __name__ == '__main__':
    main()
