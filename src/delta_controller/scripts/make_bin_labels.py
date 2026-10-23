#!/usr/bin/env python3
"""
Sinh ảnh nhãn dán mặt trước ba khay phân loại trong mô phỏng.

    python3 src/delta_controller/scripts/make_bin_labels.py

VÌ SAO CẦN: ba khay trông giống hệt nhau nên khi xem mô phỏng không thể biết robot đang thả vào
ĐÚNG khay của loại đó hay chỉ thả vào một ô trống bất kỳ. Dán nhãn làm điều đó hiện ra ngay trong
hình ảnh, không cần giải thích.

⚠️ NHÃN PHẢI KHÔNG MANG MÀU BÃO HÒA. Khay cố ý để xám trung tính vì khay màu sẽ bị khâu nhận dạng
hiểu nhầm là vật (world cũ từng có khay cam với H ≈ 20, nằm sát ngưỡng lớp màu đỏ). Nhãn dùng chữ
TRẮNG trên nền XÁM ĐẬM: độ bão hòa gần 0 nên ngưỡng S ≥ 90 loại nó ngay, dù nó nằm ngay cạnh vật
thật trong khung hình.
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', '..', 'closed_loop_description', 'materials', 'textures')

# Tỉ lệ khớp tấm nhãn trong world: rộng 45 mm, cao 12 mm.
WIDTH, HEIGHT = 600, 160
BACKGROUND = (38, 38, 42)       # xám đậm, cùng tông thành khay
TEXT = (245, 245, 245)          # trắng ngà
BORDER = (120, 120, 126)

LABELS = (('coca', 'COCA'), ('pepsi', 'PEPSI'), ('sevenup', '7UP'))
FONTS = (
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
)


def load_font(size):
    for path in FONTS:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def make_label(text):
    """Ảnh nhãn: chữ trắng, nền xám đậm, viền mảnh cho rõ mép tấm."""
    img = Image.new('RGB', (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(img)
    draw.rectangle([2, 2, WIDTH - 3, HEIGHT - 3], outline=BORDER, width=3)
    # Chọn cỡ chữ lớn nhất còn vừa khung, thay vì đoán một cỡ cố định cho mọi nhãn: "7UP" ngắn
    # hơn "PEPSI" nhiều nên cùng một cỡ sẽ cho ba nhãn to nhỏ khác nhau một cách lộn xộn.
    for size in range(140, 20, -2):
        font = load_font(size)
        box = draw.textbbox((0, 0), text, font=font)
        if box[2] - box[0] <= WIDTH - 60 and box[3] - box[1] <= HEIGHT - 40:
            break
    box = draw.textbbox((0, 0), text, font=font)
    draw.text(((WIDTH - (box[2] - box[0])) / 2 - box[0],
               (HEIGHT - (box[3] - box[1])) / 2 - box[1]), text, font=font, fill=TEXT)
    return img


def main():
    os.makedirs(OUT, exist_ok=True)
    import colorsys
    print('Sinh nhãn khay:')
    for key, text in LABELS:
        img = make_label(text)
        path = os.path.join(OUT, f'bin_label_{key}.png')
        img.save(path)
        # Kiểm luôn độ bão hòa lớn nhất — đây là ràng buộc an toàn, không phải phép làm đẹp.
        small = img.resize((60, 16))
        worst = max(colorsys.rgb_to_hsv(*(c / 255 for c in px))[1]
                    for px in small.getdata())
        flag = 'OK' if worst * 255 < 90 else 'CANH BAO: co the bi nhan nham la vat'
        print(f'  {os.path.basename(path):22s} "{text}"  S lon nhat '
              f'{worst * 255:5.1f}/255  {flag}')
    print(f'Đã ghi vào {os.path.normpath(OUT)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
