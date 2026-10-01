#!/usr/bin/env python3
"""
Hiện bàn cờ hiệu chuẩn TOÀN MÀN HÌNH, để dùng màn hình thay cho bàn cờ in (Bước 10a).

    python3 src/delta_controller/scripts/show_chessboard.py          # hiện, in co o ra terminal
    python3 src/delta_controller/scripts/show_chessboard.py --square-px 90

Vì sao dùng màn hình: mặt kính màn hình phẳng tới phần mười milimét, trong khi giấy dán lên bìa
cứng đo được vênh 0.8–1.8 mm (2026-09-30/10-01) — và chính độ vênh đó là nguồn sai số lớn nhất khi
hiệu chuẩn, vì nhìn nghiêng 45° thì 1 mm vênh thành hơn 2 pixel. Đổi lại phải CẦM CAMERA di chuyển
quanh màn hình thay vì cầm bàn cờ; C270 nhỏ nhẹ nên còn dễ hơn.

Script tự đọc kích thước màn hình từ `xrandr` và in ra sẵn giá trị `--square` phải truyền cho
calibrate_intrinsics.py, nên không cần đo thước. (Cỡ ô KHÔNG ảnh hưởng nội tham số — kiểm chứng
2026-10-01: đổi --square từ 10 lên 35 mm thì fx, fy, cx, cy, độ méo và RMS không đổi chữ số nào —
nó chỉ quy đổi khoảng cách báo cáo ra milimét.)

⚠️ Giảm độ sáng màn hình xuống ~50%: màn hình sáng quá thì camera bị cháy sáng ở vùng ô trắng,
mép ô nhòe ra và nhận góc kém chính xác.
⚠️ Đừng nghiêng quá 45°: tinh thể lỏng đổi tương phản theo góc nhìn, nghiêng gắt thì ô trắng và ô
đen xám lại gần bằng nhau.
"""

import argparse
import re
import subprocess

import cv2
import numpy as np

COLS, ROWS = 10, 7          # giống chessboard_A4.pdf -> 9x6 góc trong
TITLE = 'ban co hieu chuan - bam q de thoat'


def screen_geometry():
    """
    (rộng px, cao px, mm mỗi pixel) của màn hình chính, đọc từ `xrandr`.

    Lấy từ hệ thống thay vì bắt người dùng đo thước trên màn hình: xrandr báo cả độ phân giải lẫn
    kích thước vật lý, nên cạnh ô tính ra chính xác hơn đo tay nhiều.
    """
    try:
        out = subprocess.run(['xrandr'], capture_output=True, text=True).stdout
    except FileNotFoundError:
        return None
    for line in out.splitlines():
        m = re.search(r' connected.* (\d+)x(\d+)\+\d+\+\d+.* (\d+)mm x (\d+)mm', line)
        if m:
            w_px, h_px, w_mm, h_mm = (int(g) for g in m.groups())
            return w_px, h_px, w_mm / w_px
    return None


def board_image(width, height, square_px):
    """Ảnh bàn cờ căn giữa trên nền trắng, mỗi ô `square_px` pixel màn hình."""
    img = np.full((height, width), 255, np.uint8)
    bw, bh = COLS * square_px, ROWS * square_px
    x0, y0 = (width - bw) // 2, (height - bh) // 2
    for r in range(ROWS):
        for c in range(COLS):
            if (r + c) % 2 == 0:
                img[y0 + r * square_px:y0 + (r + 1) * square_px,
                    x0 + c * square_px:x0 + (c + 1) * square_px] = 0
    return img


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--square-px', type=int, default=0,
                    help='canh mot o tinh bang pixel man hinh (mac dinh: tu chon cho vua)')
    ap.add_argument('--width', type=int, default=0)
    ap.add_argument('--height', type=int, default=0)
    args = ap.parse_args()

    geom = screen_geometry()
    width = args.width or (geom[0] if geom else 1920)
    height = args.height or (geom[1] if geom else 1080)
    # Ô càng to thì nhận góc càng chính xác và đứng càng xa được -> lấy lớn nhất mà vẫn chừa lề.
    square_px = args.square_px or int(min(width * 0.92 / COLS, height * 0.92 / ROWS))
    img = board_image(width, height, square_px)
    cv2.namedWindow(TITLE, cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(TITLE, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    print(f'Ban co {COLS}x{ROWS} o ({COLS - 1}x{ROWS - 1} goc trong), '
          f'moi o {square_px} pixel man hinh.')
    if geom:
        square_mm = square_px * geom[2]
        print(f'Man hinh {width}x{height}, 1 pixel = {geom[2]:.4f} mm '
              f'-> canh o = {square_mm:.2f} mm')
        square_arg = f'--square {square_mm:.2f}'
    else:
        print('Khong doc duoc kich thuoc man hinh -> lay thuoc do canh mot o den '
              '(do 5 o roi chia 5).')
        square_arg = '--square <so_mm_do_duoc>'
    print('1. Giam do sang man hinh xuong ~50%.')
    print('2. Mo terminal khac va chay:')
    print('     python3 src/delta_controller/scripts/calibrate_intrinsics.py '
          f'--show --views 16 {square_arg}')
    print('3. CAM CAMERA tren tay, di chuyen quanh man hinh theo 16 tu the trong')
    print('   docs/calibration/huong_dan_chup_ban_co.pdf (nghieng toi da 45°).')
    print('Bam q tren cua so ban co de thoat.')
    while True:
        cv2.imshow(TITLE, img)
        if cv2.waitKey(50) & 0xFF in (ord('q'), 27):
            break
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
