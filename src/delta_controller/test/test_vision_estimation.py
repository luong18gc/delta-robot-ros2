"""Test ước lượng vị trí có xét che khuất: hình bóng dự đoán, khớp mép trên, cờ tin cậy."""

import math
import os

import cv2
from delta_controller.camera_model import camera_model_from_gazebo_pose
from delta_controller.color_detector import detect_objects
from delta_controller.scene import (
    BIN_FLOOR_Z,
    OBJECTS,
    SIDE_CAMERA_GT_RPY,
    SIDE_CAMERA_GT_XYZ,
    TABLE_Z,
)
from delta_controller.vision_estimation import (
    estimate_object,
    fit_top_edge,
    silhouette_features,
    surface_points,
)
import numpy as np
import pytest

K = np.array([[772.548, 0.0, 320.0], [0.0, 772.548, 240.0], [0.0, 0.0, 1.0]])
CAMERA = camera_model_from_gazebo_pose(K, SIDE_CAMERA_GT_XYZ, SIDE_CAMERA_GT_RPY)
DATA = os.path.join(os.path.dirname(__file__), 'data')
BY_NAME = {o.name: o for o in OBJECTS}


def estimate_in(image_name, object_name):
    img = cv2.imread(os.path.join(DATA, image_name))
    obj = BY_NAME[object_name]
    return estimate_object(detect_objects(img)[obj.color], CAMERA, obj, img.shape)


def error_mm(est, truth_xy):
    return 1000 * math.hypot(est.position[0] - truth_xy[0], est.position[1] - truth_xy[1])


@pytest.mark.parametrize('obj', OBJECTS, ids=lambda o: o.name)
def test_surface_points_span_object_size(obj):
    pts = surface_points(obj, (0.0, 0.0, 0.0))
    assert pts[:, 2].max() == pytest.approx(obj.half_height, abs=1e-3)
    assert np.abs(pts[:, :2]).max() <= obj.half_width * math.sqrt(2) + 1e-9


def test_silhouette_moves_up_in_image_when_object_is_farther():
    obj = BY_NAME['red_box']
    _, _, v_near = silhouette_features(CAMERA, obj, (0.0, 0.0, -0.205))
    _, _, v_far = silhouette_features(CAMERA, obj, (0.05, 0.0, -0.205))
    assert v_far < v_near


def test_fit_top_edge_recovers_position_from_exact_features():
    obj = BY_NAME['green_cylinder']
    truth = (0.03, 0.06, BIN_FLOOR_Z + obj.half_height)
    _, u, v_top = silhouette_features(CAMERA, obj, truth)
    fit = fit_top_edge(CAMERA, obj, u, v_top, truth[2], (truth[0] + 0.02, truth[1] - 0.01))
    assert fit == pytest.approx(truth[:2], abs=1e-6)


def test_unoccluded_object_is_fully_visible_and_reliable():
    """Ảnh lúc khởi động: 3 vật không bị che -> tỉ lệ nhìn thấy ~1, tin cậy, sai số < 2 mm."""
    for obj in OBJECTS:
        est = estimate_in('side_camera_home.png', obj.name)
        assert est.method == 'centroid'
        assert est.visible_fraction == pytest.approx(1.0, abs=0.1)
        assert est.reliable
        assert error_mm(est, obj.home_xy) < 2.0
        assert est.position[2] == pytest.approx(TABLE_Z + obj.half_height)


def test_object_in_bin_uses_top_edge():
    """Hộp đỏ ở ô A: tâm khối lệch ~20 mm; khớp mép trên phải về < 2 mm."""
    est = estimate_in('side_camera_red_in_bin.png', 'red_box')
    assert est.method == 'top_edge'
    assert est.reliable
    assert error_mm(est, (0.0205, 0.048)) < 2.0
    assert est.position[2] == pytest.approx(BIN_FLOOR_Z + 0.015)


def test_object_behind_platform_is_flagged():
    """Hộp đỏ ở x = 120 mm, sau platform: nửa trên bị che -> sai lớn, phải gắn không tin cậy."""
    est = estimate_in('side_camera_red_behind_platform.png', 'red_box')
    assert error_mm(est, (0.12, 0.0)) > 10.0
    assert est.visible_fraction < 0.85
    assert not est.reliable
