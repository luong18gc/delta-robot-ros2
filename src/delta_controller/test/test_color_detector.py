"""Test nhận dạng vật theo màu: ảnh tổng hợp (biết trước đáp án) + ảnh thật từ camera mô phỏng."""

import os

import cv2
from delta_controller.color_detector import (
    COLOR_CLASSES,
    detect_color,
    detect_objects,
    draw_detections,
)
from delta_controller.scene import OBJECTS
import numpy as np
import pytest

DATA = os.path.join(os.path.dirname(__file__), 'data')


def hsv_to_bgr(h, s, v):
    return tuple(int(c) for c in cv2.cvtColor(np.uint8([[[h, s, v]]]), cv2.COLOR_HSV2BGR)[0, 0])


# Màu đo trên ảnh camera mô phỏng (xem docstring color_detector).
TABLE = hsv_to_bgr(17, 77, 165)
TABLE_SHADOW = hsv_to_bgr(17, 78, 75)
RED_SHADOW = hsv_to_bgr(0, 174, 95)
GREEN = hsv_to_bgr(68, 155, 147)
BLUE = hsv_to_bgr(108, 164, 195)
BIN_ORANGE = hsv_to_bgr(20, 165, 173)
PLATFORM_YELLOW = hsv_to_bgr(29, 159, 178)


def scene_image():
    # Vẽ từ xa tới gần như trong ảnh thật: khay và platform phía sau, trụ xanh đứng trước khay.
    img = np.full((480, 640, 3), TABLE, np.uint8)
    cv2.rectangle(img, (250, 100), (400, 180), TABLE_SHADOW, -1)       # bóng robot
    cv2.rectangle(img, (150, 200), (270, 235), BIN_ORANGE, -1)         # thành khay
    cv2.rectangle(img, (280, 118), (360, 132), PLATFORM_YELLOW, -1)    # platform
    cv2.rectangle(img, (300, 140), (339, 199), RED_SHADOW, -1)         # hộp đỏ trong bóng
    cv2.circle(img, (228, 245), 25, GREEN, -1)
    cv2.circle(img, (411, 245), 26, BLUE, -1)
    return img


def test_every_scene_object_has_a_color_class():
    for obj in OBJECTS:
        assert obj.color in COLOR_CLASSES


def test_detects_three_objects_at_drawn_centres():
    found = detect_objects(scene_image())
    assert set(found) == {'red', 'green', 'blue'}
    assert found['red'].centroid == pytest.approx((319.5, 169.5), abs=0.5)
    assert found['green'].centroid == pytest.approx((228, 245), abs=0.5)
    assert found['blue'].centroid == pytest.approx((411, 245), abs=0.5)


def test_bin_platform_and_table_are_not_detected():
    img = np.full((480, 640, 3), TABLE, np.uint8)
    cv2.rectangle(img, (150, 200), (270, 235), BIN_ORANGE, -1)
    cv2.rectangle(img, (280, 118), (360, 132), PLATFORM_YELLOW, -1)
    cv2.rectangle(img, (400, 300), (500, 400), TABLE_SHADOW, -1)
    assert detect_objects(img) == {}


def test_red_in_deep_shadow_is_still_red():
    img = np.full((100, 100, 3), TABLE_SHADOW, np.uint8)
    cv2.rectangle(img, (30, 30), (69, 69), hsv_to_bgr(0, 174, 60), -1)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    assert detect_color(hsv, COLOR_CLASSES['red']) is not None


def test_red_across_hue_wraparound():
    """Đỏ nằm ở hai đầu vòng màu (H ~ 0 và ~ 178): cả hai nửa phải gộp thành một vật."""
    img = np.full((100, 200, 3), TABLE, np.uint8)
    cv2.rectangle(img, (40, 30), (99, 69), hsv_to_bgr(2, 180, 150), -1)
    cv2.rectangle(img, (100, 30), (159, 69), hsv_to_bgr(177, 180, 150), -1)
    det = detect_objects(img)['red']
    assert det.pieces == 1
    assert det.centroid == pytest.approx((99.5, 49.5), abs=0.5)


def test_occluded_object_split_in_two_is_one_detection():
    img = scene_image()
    cv2.rectangle(img, (300, 165), (339, 172), (60, 60, 60), -1)   # thanh xám cắt ngang hộp đỏ
    det = detect_objects(img)['red']
    assert det.pieces == 2
    assert det.centroid[0] == pytest.approx(319.5, abs=0.5)


def test_noise_speck_is_ignored():
    img = np.full((100, 100, 3), TABLE, np.uint8)
    cv2.rectangle(img, (10, 10), (13, 13), GREEN, -1)   # 16 px
    assert detect_objects(img) == {}


def test_sensor_noise_moves_centroid_less_than_a_pixel():
    """Camera mô phỏng có nhiễu Gauss sigma 0.007 (~1.8 mức xám)."""
    rng = np.random.default_rng(0)
    img = scene_image().astype(np.float32)
    noisy = np.clip(img + rng.normal(0, 1.8, img.shape), 0, 255).astype(np.uint8)
    clean = detect_objects(img.astype(np.uint8))
    found = detect_objects(noisy)
    for color in clean:
        assert found[color].centroid == pytest.approx(clean[color].centroid, abs=1.0)


def test_draw_detections_returns_same_size_image():
    img = scene_image()
    out = draw_detections(img, detect_objects(img), labels={'red': 'red_box'})
    assert out.shape == img.shape
    assert not np.array_equal(out, img)


# ---------------------------------------------------------------- ảnh thật từ camera mô phỏng

def load(name):
    img = cv2.imread(os.path.join(DATA, name))
    assert img is not None, name
    return img


def inside(det, x0, y0, x1, y1):
    u, v = det.centroid
    return x0 <= u <= x1 and y0 <= v <= y1


def test_real_frame_home():
    """Ảnh lúc khởi động: 3 vật trên bàn, hộp đỏ nằm trong bóng robot."""
    found = detect_objects(load('side_camera_home.png'))
    assert set(found) == {'red', 'green', 'blue'}
    assert inside(found['red'], 297, 143, 343, 203)
    assert inside(found['green'], 200, 210, 256, 282)
    assert inside(found['blue'], 385, 219, 438, 272)
    assert all(d.pieces == 1 for d in found.values())


def test_real_frame_holding_red():
    """Robot đang giữ hộp đỏ phía trên: hộp đỏ lên cao trong ảnh, vẫn thấy được."""
    found = detect_objects(load('side_camera_holding_red.png'))
    assert set(found) == {'red', 'green', 'blue'}
    assert found['red'].centroid[1] < 140


def test_real_frame_platform_over_bin():
    """Platform hạ vào khay: cả 3 vật bị che cắt thành mảnh nhưng vẫn nhận dạng được."""
    found = detect_objects(load('side_camera_occluded_in_bin.png'))
    assert set(found) == {'red', 'green', 'blue'}
    for det in found.values():
        assert inside(det, 150, 140, 280, 240)   # đều nằm trong vùng khay
