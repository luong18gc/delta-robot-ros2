#!/usr/bin/env python3
"""
Chụp ảnh MẶT BÀN TRỐNG làm chuẩn trừ nền cho node thị giác thật (Bước 10a).

    python3 src/delta_controller/scripts/capture_table_reference.py

Dọn hết vật khỏi bàn (ĐỂ NGUYÊN marker), ngắm cửa sổ cho chắc rồi bấm PHÍM CÁCH. Ảnh lưu vào
`calibration/table_reference.png`; `real_vision_node` tự nạp khi khởi động.

Vì sao cần: ngưỡng cố định không bền với ánh sáng. Đo 2026-10-07 trên cùng bố trí, cùng bộ ngưỡng,
ban ngày mặt bàn sáng lên và ÁM MÀU nên lọt vào mặt nạ; thắp một đèn thì bàn quá tối, S hóa nhiễu
và gần như CẢ MẶT BÀN lọt vào. So với ảnh bàn trống thì vân bàn, ám màu, chỗ sáng chỗ tối đều có y
hệt trong ảnh chuẩn nên tự triệt tiêu: trên cảnh không đổi, mặt nạ mới báo 0.00% khung trong khi
cách lấy ngưỡng báo 12.06%.

⚠️ ĐỔI ÁNH SÁNG LÀ PHẢI CHỤP LẠI. Bật thêm đèn, kéo rèm, hay trời tối đi đều làm ảnh chuẩn hết
đúng — đó là cái giá của phương pháp này.
⚠️ Camera xê dịch cũng phải chụp lại: ảnh chuẩn gắn với đúng góc nhìn lúc chụp.
"""

import argparse
import os
import sys

import _workspace  # noqa: F401
import cv2
from delta_controller import usb_camera
import numpy as np


WS = '/home/luong18gc/ros2_closed_loop_ws'
DEFAULT_OUT = f'{WS}/calibration/table_reference.png'
FRAMES = 20


def main():
    """Chụp ảnh bàn trống và ghi ra file."""
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--device', default='auto')
    ap.add_argument('--out', default=DEFAULT_OUT)
    ap.add_argument('--frames', type=int, default=FRAMES)
    args = ap.parse_args()

    device = usb_camera.resolve_device(args.device)
    mode = usb_camera.best_mjpg_mode(device)
    usb_camera.lock_manual(device, log=lambda _: None)
    cap = usb_camera.open_camera(device, mode[0], mode[1])
    usb_camera.warm_up(cap)

    title = 'anh nen - CACH de chup, q de huy'
    cv2.namedWindow(title, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(title, 1100, 620)
    print('DON HET VAT KHOI BAN (de nguyen marker) roi bam PHIM CACH. q = huy.')
    while True:
        ok, frame = cap.read()
        if not ok:
            continue
        view = frame.copy()
        text = 'DON HET VAT KHOI BAN roi bam CACH   (q = huy)'
        cv2.putText(view, text, (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 0, 0), 4,
                    cv2.LINE_AA)
        cv2.putText(view, text, (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 220, 220), 1,
                    cv2.LINE_AA)
        cv2.imshow(title, view)
        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), 27):
            cap.release()
            cv2.destroyAllWindows()
            print('Da huy, khong ghi gi.')
            return 1
        if key in (ord(' '), 13):
            break

    shots = []
    while len(shots) < args.frames:
        ok, frame = cap.read()
        if ok:
            shots.append(frame)
    cap.release()
    cv2.destroyAllWindows()
    # Trung vị nhiều khung: nhiễu cảm biến không được phép đi vào chính cái chuẩn.
    ref = np.median(np.array(shots), axis=0).astype(np.uint8)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    cv2.imwrite(args.out, ref)
    spread = float(np.median(np.std(np.array(shots, float), axis=0)))
    print(f'Da ghi {args.out}  ({len(shots)} khung, nhieu {spread:.1f} muc xam)')
    print('Chay lai moi khi doi anh sang hoac xe dich camera.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
