"""Test bộ nhận dạng TÁCH NỀN TRƯỚC: trừ nền theo ảnh bàn trống."""

import cv2
from delta_controller import object_detector
import numpy as np


def test_tru_nen_tham_chieu_chi_bat_cai_da_doi():
    """Trừ nền chỉ báo chỗ KHÁC ảnh chuẩn — nền có vân, có ám màu cũng không lọt."""
    rng = np.random.default_rng(7)
    # Nền "mặt bàn": tối, có vân, ám màu đỏ — đúng kiểu làm cách lấy ngưỡng hỏng. Pixel tối có
    # S = (max-min)/max rất nhiễu, nên nhánh bão hòa của foreground_mask vớ phải cả mặt bàn.
    table = (rng.integers(0, 40, (240, 320, 3)) + np.array([25, 26, 38])).astype(np.uint8)
    reference = table.copy()
    frame = table.copy()
    cv2.rectangle(frame, (120, 80), (170, 190), (40, 40, 220), -1)   # một "lon" đỏ

    nothing = object_detector.foreground_from_reference(reference, reference)
    assert nothing.max() == 0, 'canh khong doi ma van bao co vat'

    mask = object_detector.foreground_from_reference(frame, reference)
    ys, xs = np.nonzero(mask)
    assert 115 <= xs.min() <= 125 and 165 <= xs.max() <= 175
    assert 75 <= ys.min() <= 85 and 185 <= ys.max() <= 195
    # Cách lấy ngưỡng trên chính cảnh này báo nhầm rất nhiều nền.
    old = object_detector.foreground_mask(cv2.cvtColor(frame, cv2.COLOR_BGR2HSV))
    assert (old > 0).mean() > 5 * (mask > 0).mean()


def test_tru_nen_bo_qua_nhieu_cam_bien():
    """Nhiễu cảm biến vài mức xám không được thành vật."""
    rng = np.random.default_rng(11)
    reference = np.full((200, 200, 3), 60, np.uint8)
    noisy = np.clip(reference.astype(np.int16)
                    + rng.normal(0, 3, reference.shape), 0, 255).astype(np.uint8)
    assert object_detector.foreground_from_reference(noisy, reference).max() == 0
