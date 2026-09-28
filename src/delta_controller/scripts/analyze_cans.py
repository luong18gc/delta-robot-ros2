#!/usr/bin/env python3
"""
Đo ảnh lon nước thật để chuẩn bị Bước 10b: màu, nắp bạc, lóa, và thử phép tách nền.

    python3 src/delta_controller/scripts/analyze_cans.py ~/Documents/*.jpeg

In ra, cho từng ảnh:
  1. Diện tích mặt nạ của BỘ NHẬN DẠNG HIỆN TẠI cho từng lớp màu (đỏ/lục/lam) — để thấy
     mảng đỏ trên lon Pepsi/7Up có bị gộp chung với lon Coca không.
  2. Kết quả TÁCH NỀN rồi phân loại từng vật (kiến trúc đề xuất cho lon thật): mỗi vùng
     liên thông là một lon, phân loại theo sắc màu chiếm ưu thế trong chính vùng đó.
  3. Với mỗi lon: tỉ lệ pixel thực sự có màu, tỉ lệ nắp bạc / chữ trắng, tỉ lệ lóa.
"""

import os
import sys

import cv2
import numpy as np

# Ngưỡng của bộ nhận dạng hiện tại (color_detector.COLOR_CLASSES), lặp lại ở đây để script
# chạy được độc lập, không cần PYTHONPATH.
CLASSES = {
    'do':   (((0, 100, 40), (8, 255, 255)), ((172, 100, 40), (180, 255, 255))),
    'luc':  (((45, 90, 40), (85, 255, 255)),),
    'lam':  (((95, 90, 40), (125, 255, 255)),),
}
WIDTH = 768            # thu nhỏ cho nhanh, tỉ lệ diện tích không đổi
SAT_MIN = 80           # pixel "có màu" để tách vật khỏi nền xám/đen
MIN_AREA = 1500        # px, ở ảnh đã thu nhỏ — nhỏ hơn coi là nhiễu
SILVER_S_MAX = 60      # nắp nhôm / chữ trắng: bão hòa thấp
SILVER_V_MIN = 120
GLARE_V_MIN = 235      # lóa: gần trắng


def masks_current(hsv):
    """Mặt nạ của bộ nhận dạng hiện tại, chưa lọc hình thái học."""
    out = {}
    for name, ranges in CLASSES.items():
        m = np.zeros(hsv.shape[:2], np.uint8)
        for lo, hi in ranges:
            m |= cv2.inRange(hsv, np.array(lo, np.uint8), np.array(hi, np.uint8))
        out[name] = m
    return out


def classify(hsv, mask):
    """Sắc màu chiếm ưu thế trong một vùng -> tên lớp màu."""
    px = hsv[mask > 0]
    px = px[px[:, 1] >= SAT_MIN]
    if len(px) == 0:
        return '?', 0
    best, count = '?', 0
    for name, ranges in CLASSES.items():
        n = 0
        for lo, hi in ranges:
            n += int(np.count_nonzero((px[:, 0] >= lo[0]) & (px[:, 0] <= hi[0])))
        if n > count:
            best, count = name, n
    return best, count


def analyse(path):
    img = cv2.imread(path)
    if img is None:
        print(f'{path}: KHONG DOC DUOC')
        return
    scale = WIDTH / img.shape[1]
    img = cv2.resize(img, (WIDTH, int(img.shape[0] * scale)))
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    total = img.shape[0] * img.shape[1]
    print(f'\n=== {os.path.basename(path)}  ({img.shape[1]}x{img.shape[0]} sau thu nho) ===')

    # --- 1. bo nhan dang HIEN TAI: moi lop mau gop toan anh
    print('  [1] Bo nhan dang HIEN TAI (gop moi manh cung mau toan anh):')
    for name, m in masks_current(hsv).items():
        n, lab, stats, cent = cv2.connectedComponentsWithStats(
            cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)), 8)
        big = [i for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] >= 200]
        area = int(m.sum() // 255)
        xs = [f'({cent[i][0]:.0f},{cent[i][1]:.0f})={stats[i, cv2.CC_STAT_AREA]}px'
              for i in sorted(big, key=lambda i: -stats[i, cv2.CC_STAT_AREA])[:4]]
        print(f'      {name:4s}: {area:6d} px ({100*area/total:4.1f}%), '
              f'{len(big):2d} manh >=200px  {" ".join(xs)}')

    # --- 2. tach nen roi phan loai tung vat (kien truc de xuat)
    sat = cv2.inRange(hsv, np.array((0, SAT_MIN, 50), np.uint8),
                      np.array((180, 255, 255), np.uint8))
    sat = cv2.morphologyEx(sat, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    sat = cv2.morphologyEx(sat, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, lab, stats, cent = cv2.connectedComponentsWithStats(sat, 8)
    objs = sorted([i for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] >= MIN_AREA],
                  key=lambda i: cent[i][0])
    print(f'  [2] Tach nen roi phan loai tung vat: tim thay {len(objs)} vung')
    for i in objs:
        m = (lab == i).astype(np.uint8)
        x, y, w, h, area = stats[i, :5]
        name, colour_px = classify(hsv, m)
        px = hsv[m > 0]
        silver = int(np.count_nonzero((px[:, 1] < SILVER_S_MAX) & (px[:, 2] > SILVER_V_MIN)))
        glare = int(np.count_nonzero(px[:, 2] > GLARE_V_MIN))
        hue = px[px[:, 1] >= SAT_MIN][:, 0]
        print(f'      vat tai ({cent[i][0]:4.0f},{cent[i][1]:4.0f}) {w:3d}x{h:3d}px '
              f'-> {name:4s} | dien tich {area:6d} | ti le co mau {100*colour_px/area:4.1f}% '
              f'| bac/trang {100*silver/area:4.1f}% | loa {100*glare/area:4.1f}% '
              f'| H trung vi {np.median(hue) if len(hue) else -1:.0f}')

    # --- 3. nen ban
    dark = hsv[(hsv[:, :, 2] < 110) & (hsv[:, :, 1] < 80)]
    if len(dark):
        print(f'  [3] Mat ban (pixel toi, it bao hoa): {len(dark)} px, '
              f'S trung binh {dark[:, 1].mean():.0f}, V trung binh {dark[:, 2].mean():.0f}, '
              f'ti le S>90: {100*np.mean(dark[:, 1] > 90):.1f}%')


def main():
    paths = sys.argv[1:]
    if not paths:
        paths = [os.path.expanduser(f'~/Documents/{n}') for n in
                 ('IewGCbs4.jpeg', 'PlXx-yyr.jpeg', 'pN0z1QXe.jpeg', 'xIe9oq_L.jpeg')]
    for p in paths:
        analyse(p)


if __name__ == '__main__':
    main()
