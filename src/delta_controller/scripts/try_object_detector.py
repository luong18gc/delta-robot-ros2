#!/usr/bin/env python3
"""
Chạy thử object_detector.py (kiến trúc tách nền trước) trên ảnh lon thật và trên ảnh mô phỏng.

    python3 src/delta_controller/scripts/try_object_detector.py              # 4 anh ~/Documents
    python3 src/delta_controller/scripts/try_object_detector.py a.jpg b.png

Với mỗi ảnh, in ra từng vật tìm được: lớp màu, tâm khối, diện tích, độ chắc chắn phân loại và
tỉ lệ pixel có màu. Ghi kèm ảnh chú thích `<ten>_objects.png` cạnh ảnh gốc để xem bằng mắt.

So sánh với bộ nhận dạng cũ (`color_detector.detect_objects`) để thấy khác biệt.
"""

import os
import sys

import cv2

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from delta_controller.color_detector import COLOR_CLASSES, detect_color   # noqa: E402
from delta_controller.object_detector import detect_objects, draw_objects  # noqa: E402

DEFAULT = [os.path.expanduser(f'~/Documents/{n}') for n in
           ('IewGCbs4.jpeg', 'PlXx-yyr.jpeg', 'pN0z1QXe.jpeg', 'xIe9oq_L.jpeg')]
WIDTH = 768


def run(path):
    bgr = cv2.imread(path)
    if bgr is None:
        print(f'{path}: KHONG DOC DUOC')
        return
    if bgr.shape[1] > WIDTH:
        scale = WIDTH / bgr.shape[1]
        bgr = cv2.resize(bgr, (WIDTH, int(bgr.shape[0] * scale)))
    print(f'\n=== {os.path.basename(path)} ({bgr.shape[1]}x{bgr.shape[0]}) ===')

    print('  CU  (loc mau toan anh, moi mau = 1 vat):')
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    for name, cls in COLOR_CLASSES.items():
        d = detect_color(hsv, cls)
        if d:
            print(f'      {name:6s} tam ({d.centroid[0]:6.1f},{d.centroid[1]:6.1f})  '
                  f'{d.area:6d} px  {d.pieces} manh')
        else:
            print(f'      {name:6s} khong thay')

    print('  MOI (tach nen truoc, phan loai tung vat):')
    objects = detect_objects(bgr, COLOR_CLASSES)
    if not objects:
        print('      khong thay vat nao')
    for d in objects:
        print(f'      {d.color:6s} tam ({d.centroid[0]:6.1f},{d.centroid[1]:6.1f})  '
              f'{d.area:6d} px  chac chan {100 * d.confidence:5.1f}%  '
              f'co mau {100 * d.color_fraction:5.1f}%  bbox {d.bbox}')

    out = os.path.splitext(path)[0] + '_objects.png'
    cv2.imwrite(out, draw_objects(bgr, objects, COLOR_CLASSES))
    print(f'      -> anh chu thich: {out}')


def main():
    for path in (sys.argv[1:] or DEFAULT):
        run(path)


if __name__ == '__main__':
    main()
