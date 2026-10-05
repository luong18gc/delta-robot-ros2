"""Test ngoại tham số camera thật bằng ảnh marker DỰNG LẠI từ tư thế biết trước đáp án."""

import math

import cv2
from delta_controller.camera_model import CameraModel
from delta_controller.real_camera import (
    detect_marker_centers,
    estimate_extrinsics,
    MIN_MARKERS,
    PoseTracker,
)
from delta_controller.scene import (
    CALIB_ARUCO_DICT,
    REAL_CALIB_MARKER_SIZE,
    real_calib_markers_virtual,
    SCALE,
    TABLE_Z,
)
import numpy as np
import pytest

W, H = 1280, 720
K = np.array([[1417.4, 0.0, 610.9], [0.0, 1418.1, 382.4], [0.0, 0.0, 1.0]])
DIST = np.array([0.1178, -0.2765, 0.0027, -0.0008, 0.0])
HALF = REAL_CALIB_MARKER_SIZE / 2 / SCALE      # nửa cạnh marker trong hệ ẢO
TILE = HALF * 1.34                             # kèm lề trắng ~1 ô module mỗi phía


def camera_at(back=0.90, height=0.545, target=0.14):
    """
    Dựng CameraModel nhìn xuống bàn; `back`, `height`, `target` tính bằng mét THẬT.

    ⚠️ `height` là độ cao TRÊN MẶT BÀN, mà mặt bàn trong hệ ảo nằm ở TABLE_Z = -0.22 chứ không
    phải 0 — nên phải cộng TABLE_Z, không chỉ chia SCALE.
    """
    c = np.array([-back / SCALE, 0.0, TABLE_Z + height / SCALE])
    table = np.array([target / SCALE, 0.0, TABLE_Z])
    fwd = table - c
    fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, [0.0, 0.0, 1.0])
    right /= np.linalg.norm(right)
    R = np.vstack([right, np.cross(fwd, right), fwd])
    return CameraModel(K=K, dist=DIST, rvec=cv2.Rodrigues(R)[0].reshape(3), tvec=(-R @ c))


def render(model, markers=None, size=240):
    """Ảnh xám dựng lại: dán hình marker ArUco lên mặt bàn rồi chiếu qua `model`."""
    layout = real_calib_markers_virtual() if markers is None else markers
    dictionary = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, CALIB_ARUCO_DICT))
    frame = np.full((H, W), 40, np.uint8)       # mặt bàn đen nhám
    for marker_id, (x, y) in layout.items():
        bits = cv2.aruco.drawMarker(dictionary, marker_id, size)
        pad = int(size / 6)
        tile = np.full((size + 2 * pad, size + 2 * pad), 255, np.uint8)
        tile[pad:pad + size, pad:pad + size] = bits
        world = np.array([[x - TILE, y + TILE, TABLE_Z], [x + TILE, y + TILE, TABLE_Z],
                          [x + TILE, y - TILE, TABLE_Z], [x - TILE, y - TILE, TABLE_Z]])
        uv = model.project(world).astype(np.float32)
        n = tile.shape[0]
        src = np.array([[0, 0], [n, 0], [n, n], [0, n]], np.float32)
        warp = cv2.warpPerspective(tile, cv2.getPerspectiveTransform(src, uv), (W, H),
                                   borderValue=0)
        frame[warp > 0] = warp[warp > 0]
    return frame


def test_renders_all_six_markers():
    """Ảnh dựng lại phải nhận đủ 6 marker — nếu không thì mọi test sau vô nghĩa."""
    centers = detect_marker_centers(render(camera_at()))
    assert sorted(centers) == [0, 1, 2, 3, 4, 5]


def test_recovers_known_camera_pose():
    """Tư thế giải ra phải khớp tư thế đã dùng để dựng ảnh."""
    truth = camera_at()
    found = estimate_extrinsics(detect_marker_centers(render(truth)), K, DIST)
    assert found.ok
    assert found.rms_px < 1.0
    # So với hình học giá đỡ THẬT, không so với chính `truth.position()`: so với chính nó thì
    # một sai quy ước (vd. quên mặt bàn ở TABLE_Z) vẫn pass vì cả hai vế cùng sai.
    x, y, z = found.position_real_mm()
    assert abs(x + 900) < 5 and abs(y) < 5, f'vi tri ngang lech: ({x:.0f}, {y:.0f})'
    assert abs(z - 545) < 5, f'chieu cao tren mat ban {z:.0f} mm, phai la 545'
    axis = np.degrees(np.arccos(np.clip(
        found.model.optical_axis() @ truth.optical_axis(), -1, 1)))
    assert axis < 0.3, f'huong nhin lech {axis:.2f}°'


def test_pixel_to_table_position_is_accurate():
    """Phép đo thực sự dùng: pixel -> vị trí trên bàn, sai số quy về hệ ảo."""
    truth = camera_at()
    found = estimate_extrinsics(detect_marker_centers(render(truth)), K, DIST)
    worst = 0.0
    for x_mm in (0, 140, 280):            # vùng đặt lon THẬT
        for y_mm in (-190, 0, 190):
            point = (x_mm / 1000 / SCALE, y_mm / 1000 / SCALE, TABLE_Z)
            u, v = truth.project([point])[0]
            got = found.model.pixel_to_plane(u, v, TABLE_Z)
            worst = max(worst, 1000 * np.linalg.norm(np.array(got[:2]) - np.array(point[:2])))
    assert worst < 1.0, f'sai so lon nhat {worst:.2f} mm ao'


def test_tilt_matches_the_mount():
    """Góc chúc đo được phải khớp hình học giá đỡ (lùi 0.90 m, cao 0.545 m)."""
    found = estimate_extrinsics(detect_marker_centers(render(camera_at())), K, DIST)
    expected = math.degrees(math.atan2(0.545 - 0.0, 0.90 + 0.14))
    assert abs(found.tilt_deg() - expected) < 1.0


def test_too_few_markers_is_refused():
    layout = {i: xy for i, xy in real_calib_markers_virtual().items() if i < 3}
    centers = detect_marker_centers(render(camera_at(), layout), markers=layout)
    assert len(centers) < MIN_MARKERS
    with pytest.raises(ValueError, match='PnP can it nhat 4'):
        estimate_extrinsics(centers, K, DIST, markers=layout)


def test_tracker_keeps_pose_when_markers_are_hidden():
    """Marker bị che tạm thời thì giữ nguyên tư thế cũ, không được văng ra lỗi."""
    tracker = PoseTracker(K, DIST)
    good = render(camera_at())
    assert tracker.update(good) is not None
    before = np.array(tracker.model.position())
    assert tracker.update(np.full((H, W), 40, np.uint8)) is None     # không thấy marker nào
    assert tracker.ready and tracker.skipped == 1
    assert np.allclose(before, tracker.model.position())


def test_tracker_follows_a_camera_that_moved():
    """Giá đỡ xê dịch -> tư thế phải bám theo sau một số khung, không kẹt ở chỗ cũ."""
    tracker = PoseTracker(K, DIST)
    for _ in range(5):
        tracker.update(render(camera_at(back=0.90)))
    moved = camera_at(back=0.86)          # lùi ít hơn 40 mm thật
    frame = render(moved)
    for _ in range(60):
        tracker.update(frame)
    error_mm = 1000 * SCALE * np.linalg.norm(
        np.array(tracker.model.position()) - np.array(moved.position()))
    assert error_mm < 5.0, f'con lech {error_mm:.1f} mm sau khi camera doi cho'
