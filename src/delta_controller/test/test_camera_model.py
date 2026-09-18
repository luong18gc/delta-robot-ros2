"""Test mô hình camera: PnP, đổi pixel -> tọa độ robot, tâm marker, lưu/đọc."""

import math
import os

import cv2
from delta_controller.camera_model import (
    camera_model_from_gazebo_pose,
    CameraModel,
    estimate_pose,
    marker_center,
)
from delta_controller.scene import (
    CALIB_ARUCO_DICT,
    CALIB_MARKER_Z,
    CALIB_MARKERS,
    SIDE_CAMERA_GT_RPY,
    SIDE_CAMERA_GT_XYZ,
    TABLE_Z,
)
import numpy as np
import pytest

K = np.array([[772.548, 0.0, 320.0], [0.0, 772.548, 240.0], [0.0, 0.0, 1.0]])
GT = camera_model_from_gazebo_pose(K, SIDE_CAMERA_GT_XYZ, SIDE_CAMERA_GT_RPY)
MARKER_POINTS = np.array([(x, y, CALIB_MARKER_Z) for x, y in CALIB_MARKERS.values()])
DATA = os.path.join(os.path.dirname(__file__), 'data')


def test_ground_truth_camera_position_and_view_direction():
    assert GT.position() == pytest.approx(SIDE_CAMERA_GT_XYZ, abs=1e-9)
    axis = GT.optical_axis()
    assert math.degrees(math.asin(-axis[2])) == pytest.approx(32.0, abs=0.1)   # nhìn xuống 32°
    assert axis[0] > 0.8                                                        # nhìn về phía +X


def test_ground_truth_projects_object_where_detector_found_it():
    """Bước 8.3: chiếu tâm thật hộp đỏ rơi cách tâm nhận dạng (319.4, 172.6) < 1.5 px."""
    uv = GT.project([(0.06, 0.0, -0.205)])[0]
    assert uv == pytest.approx((319.4, 172.6), abs=1.5)


def test_pnp_recovers_pose_from_exact_points():
    result = estimate_pose(MARKER_POINTS, GT.project(MARKER_POINTS), K, np.zeros(5))
    assert result.rms_px < 1e-6
    assert result.model.position() == pytest.approx(GT.position(), abs=1e-6)


def test_pnp_with_pixel_noise_stays_within_few_mm():
    rng = np.random.default_rng(1)
    image = GT.project(MARKER_POINTS) + rng.normal(0, 0.3, (len(MARKER_POINTS), 2))
    result = estimate_pose(MARKER_POINTS, image, K, np.zeros(5))
    assert np.linalg.norm(result.model.position() - GT.position()) < 0.005
    assert result.rms_px < 0.6


def test_pnp_needs_four_points():
    with pytest.raises(ValueError):
        estimate_pose(MARKER_POINTS[:3], GT.project(MARKER_POINTS[:3]), K, np.zeros(5))


@pytest.mark.parametrize('point', [
    (0.06, 0.0, -0.205), (-0.03, 0.052, -0.205), (0.1, -0.08, -0.22),
])
def test_pixel_to_plane_inverts_projection(point):
    u, v = GT.project([point])[0]
    assert GT.pixel_to_plane(u, v, point[2]) == pytest.approx(point, abs=1e-9)


def test_wrong_plane_gives_centimetre_error():
    """Tâm vật (z -0.205) mà lại giao với mặt bàn (z -0.22): sai số ~12 mm theo hướng nhìn."""
    u, v = GT.project([(0.06, 0.0, -0.205)])[0]
    x, y, _ = GT.pixel_to_plane(u, v, TABLE_Z)
    error = math.hypot(x - 0.06, y - 0.0)
    assert 0.010 < error < 0.030


def test_marker_center_is_projection_of_true_center():
    """Giao điểm đường chéo = ảnh của tâm; trung bình 4 góc thì lệch khi nhìn xiên."""
    x, y = CALIB_MARKERS[0]
    h = 0.025
    corners = GT.project([(x - h, y - h, CALIB_MARKER_Z), (x + h, y - h, CALIB_MARKER_Z),
                          (x + h, y + h, CALIB_MARKER_Z), (x - h, y + h, CALIB_MARKER_Z)])
    true_center = GT.project([(x, y, CALIB_MARKER_Z)])[0]
    assert marker_center(corners) == pytest.approx(tuple(true_center), abs=1e-6)
    assert np.linalg.norm(corners.mean(axis=0) - true_center) > 0.05


def test_dict_round_trip():
    again = CameraModel.from_dict(GT.to_dict())
    assert again.project(MARKER_POINTS) == pytest.approx(GT.project(MARKER_POINTS))


def test_calibration_on_real_simulated_frame():
    """Ảnh thật từ camera mô phỏng có 6 marker: PnP phải ra đúng vị trí camera trong vài mm."""
    img = cv2.imread(os.path.join(DATA, 'side_camera_markers.png'), cv2.IMREAD_GRAYSCALE)
    dictionary = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, CALIB_ARUCO_DICT))
    corners, ids, _ = cv2.aruco.detectMarkers(img, dictionary)
    assert sorted(ids.flatten()) == sorted(CALIB_MARKERS)
    obj = [(*CALIB_MARKERS[int(i)], CALIB_MARKER_Z) for i in ids.flatten()]
    img_pts = [marker_center(c) for c in corners]
    result = estimate_pose(obj, img_pts, K, np.zeros(5))
    assert result.rms_px < 1.0
    assert np.linalg.norm(result.model.position() - GT.position()) < 0.005
    cos_angle = float(np.dot(result.model.optical_axis(), GT.optical_axis()))
    assert math.degrees(math.acos(min(1.0, cos_angle))) < 0.5
