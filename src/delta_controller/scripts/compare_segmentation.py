#!/usr/bin/env python3
"""
Sinh hình SO SÁNH hai cách tách vật khỏi nền, trên cùng một khung hình camera thật.

    # phải TẮT launch trước, vì real_vision đang giữ camera
    python3 src/delta_controller/scripts/compare_segmentation.py

Hai cách được so:

* **Ngưỡng cố định** — vật = đủ bão hòa HOẶC đủ sáng so với mặt bàn, ngưỡng độ sáng lấy bằng Otsu.
  Không cần chuẩn bị gì, nhưng phụ thuộc ánh sáng.
* **Trừ ảnh nền** — vật = khác ảnh mặt bàn trống quá một ngưỡng. Đại lượng được so là *sự thay
  đổi* nên không phụ thuộc mức sáng chung, đổi lại phải chụp trước ảnh nền và ảnh đó hỏng khi
  camera xê dịch.

Hình ra gồm ba khung cạnh nhau — ảnh gốc, mặt nạ ngưỡng, mặt nạ trừ nền — kèm tỉ lệ diện tích và
số vùng của mỗi cách. Con số đi kèm quan trọng ngang bức ảnh: nhìn mặt nạ thì thấy "có vẻ sạch
hơn", còn tỉ lệ diện tích mới nói được sạch hơn bao nhiêu.
"""

import argparse
import os
import sys

sys.path.insert(0, __file__.rsplit('/scripts/', 1)[0])

import cv2                                                         # noqa: E402
from delta_controller import usb_camera                            # noqa: E402
from delta_controller.object_detector import (                     # noqa: E402
    foreground_from_reference, foreground_mask, MIN_AREA,
)
import numpy as np                                                 # noqa: E402

WS = __file__.rsplit('/src/', 1)[0]
REFERENCE = os.path.join(WS, 'calibration', 'table_reference.png')
OUT = os.path.join(WS, 'docs', 'figures', 'foreground_comparison.png')
PANEL_W = 620


def stats(mask):
    """(tỉ lệ diện tích %, số vùng đủ lớn) của một mặt nạ."""
    count, _, info, _ = cv2.connectedComponentsWithStats((mask > 0).astype(np.uint8), 8)
    regions = sum(1 for i in range(1, count) if info[i][4] >= MIN_AREA)
    return 100.0 * float((mask > 0).sum()) / mask.size, regions


def panel(image, title, subtitle, color):
    """Một khung của hình: ảnh đã chuẩn hóa bề rộng, kèm tiêu đề và dòng số liệu."""
    scaled = cv2.resize(image, (PANEL_W, int(image.shape[0] * PANEL_W / image.shape[1])))
    if scaled.ndim == 2:
        scaled = cv2.cvtColor(scaled, cv2.COLOR_GRAY2BGR)
    head = np.full((62, PANEL_W, 3), 250, np.uint8)
    cv2.putText(head, title, (12, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.62, color, 2)
    cv2.putText(head, subtitle, (12, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (90, 90, 90), 1)
    return np.vstack([head, scaled])


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--image', help='dùng tệp ảnh thay vì chụp từ camera')
    ap.add_argument('--out', default=OUT)
    args = ap.parse_args()

    reference = cv2.imread(REFERENCE)
    if reference is None:
        raise SystemExit(f'Chua co anh nen {REFERENCE}. Chay capture_table_reference.py truoc.')

    if args.image:
        frame = cv2.imread(args.image)
        if frame is None:
            raise SystemExit(f'Khong doc duoc {args.image}')
    else:
        node, name = usb_camera.find_device()
        if node is None:
            raise SystemExit(f'Khong tim duoc camera: {name}')
        mode = usb_camera.best_mjpg_mode(node)
        usb_camera.lock_manual(node, log=lambda _: None)
        cap = usb_camera.open_camera(node, mode[0], mode[1])
        if not cap.isOpened():
            raise SystemExit(
                f'Khong mo duoc {node}. real_vision co dang giu camera khong? '
                f'Tat launch roi chay lai.')
        usb_camera.warm_up(cap)
        ok, frame = cap.read()
        cap.release()
        if not ok:
            raise SystemExit('Khong doc duoc khung hinh')
        print(f'Camera: {name} -> {node}, {frame.shape[1]}x{frame.shape[0]}')

    if frame.shape != reference.shape:
        raise SystemExit(f'Anh nen {reference.shape} khac khung hinh {frame.shape} — '
                         f'chup lai anh nen o cung do phan giai.')

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    by_threshold = foreground_mask(hsv)
    by_reference = foreground_from_reference(frame, reference)

    area_t, regions_t = stats(by_threshold)
    area_r, regions_r = stats(by_reference)
    print(f'\n{"cách tách":22s} {"diện tích mặt nạ":>18s} {"số vùng đủ lớn":>16s}')
    print(f'{"ngưỡng cố định":22s} {area_t:17.2f}% {regions_t:16d}')
    print(f'{"trừ ảnh nền":22s} {area_r:17.2f}% {regions_r:16d}')
    if regions_r and regions_t > regions_r:
        print(f'\n=> Ngưỡng cố định sinh thêm {regions_t - regions_r} vùng không phải vật.')

    view = np.hstack([
        panel(frame, 'ANH GOC', 'khung hinh tu camera that', (40, 40, 40)),
        panel(by_threshold, 'NGUONG CO DINH',
              f'{area_t:.1f}% dien tich, {regions_t} vung', (40, 40, 200)),
        panel(by_reference, 'TRU ANH NEN',
              f'{area_r:.1f}% dien tich, {regions_r} vung', (40, 150, 40)),
    ])
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    cv2.imwrite(args.out, view)
    print(f'Đã ghi {args.out}  ({view.shape[1]}x{view.shape[0]})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
