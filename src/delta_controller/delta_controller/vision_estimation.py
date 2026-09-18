"""
Ước lượng vị trí vật từ kết quả nhận dạng, có xét che khuất (Bước 8.5) — thuần Python + OpenCV.

Bước 8.4 cho thấy sai số lớn đều do vật bị che MỘT PHẦN: tâm khối là tâm phần nhìn thấy nên lệch
theo phần bị che. Hai cải tiến, cùng dựa trên việc DỰ ĐOÁN hình bóng vật trên ảnh:

  Hình bóng dự đoán = bao lồi (convex hull) của ảnh các điểm trên bề mặt vật (vật lồi -> bao lồi
  của hình chiếu chính là hình bóng), tính bằng mô hình camera đã hiệu chuẩn.

  (a) Tỉ lệ nhìn thấy = diện tích nhìn thấy / diện tích hình bóng dự đoán. Nhỏ -> vật bị che,
      vị trí kém tin cậy (cờ `reliable`). Chạm mép ảnh cũng là bị che.
  (b) Vật trong khay: thành khay che nửa dưới nhưng MẶT TRÊN luôn lộ (camera nhìn xuống 32°). Tìm
      (x, y) để mép trên của hình bóng dự đoán trùng mép trên quan sát được và tâm ngang trùng
      tâm ngang quan sát được: 2 phương trình, 2 ẩn, giải bằng Newton (Jacobian số).
"""

from dataclasses import dataclass
import math

import cv2
from delta_controller.scene import BIN_CENTER, BIN_FLOOR_Z, BIN_INNER_HALF, BIN_OUTER_HALF, TABLE_Z
import numpy as np

# Tỉ lệ nhìn thấy tối thiểu để tin vị trí tâm khối. Trên bộ dữ liệu 8.4: 0.85 bỏ sót 1/29 ước lượng
# tệ (> 5 mm), 0.90 bỏ sót 0/29 (báo nhầm 12/143 thay vì 10/143). Bước 9 gặp đúng ca bị bỏ sót:
# hộp đỏ bị trụ xanh đứng trước che ~15% -> lệch 8 mm -> hút lệch tâm -> đè thành khay, trượt
# sang ô khác.
VISIBLE_MIN = 0.90
# Ước lượng thô cách thành ngoài khay tới mức này thì thử giả thuyết "vật trong khay" (m).
BIN_SEARCH_MARGIN = 0.03
_NEWTON_STEP = 1e-4         # bước sai phân để tính Jacobian (m)


@dataclass(frozen=True)
class ObjectEstimate:
    position: tuple         # (x, y, z) tâm vật, hệ robot (m)
    method: str             # 'centroid' (tâm khối) | 'top_edge' (khớp mép trên, vật trong khay)
    visible_fraction: float
    cut_by_border: bool
    reliable: bool


# ---------------------------------------------------------------- hình học vật

def surface_points(obj, center):
    """Các điểm trên bề mặt vật (Nx3, hệ robot) có tâm tại center (x, y, z)."""
    cx, cy, cz = center
    w, h = obj.half_width, obj.half_height
    if obj.shape == 'box':
        pts = [(sx * w, sy * w, sz * h) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    elif obj.shape == 'cylinder':
        a = np.linspace(0, 2 * math.pi, 48, endpoint=False)
        ring = np.stack([w * np.cos(a), w * np.sin(a)], axis=1)
        pts = [(x, y, z) for z in (-h, h) for x, y in ring]
    elif obj.shape == 'sphere':
        n = 400   # điểm Fibonacci phủ đều mặt cầu
        k = np.arange(n) + 0.5
        phi = np.arccos(1 - 2 * k / n)
        theta = math.pi * (1 + 5 ** 0.5) * k
        pts = np.stack([np.sin(phi) * np.cos(theta), np.sin(phi) * np.sin(theta),
                        np.cos(phi)], axis=1) * w
    else:
        raise ValueError(f'Hinh dang la: {obj.shape}')
    return np.asarray(pts, float) + np.array([cx, cy, cz])


def silhouette(camera, obj, center):
    """Hình bóng dự đoán trên ảnh: đa giác bao lồi (Mx2, pixel)."""
    uv = camera.project(surface_points(obj, center)).astype(np.float32)
    return cv2.convexHull(uv).reshape(-1, 2)


def silhouette_features(camera, obj, center):
    """(diện tích, u trọng tâm, v mép trên) của hình bóng dự đoán."""
    hull = silhouette(camera, obj, center)
    m = cv2.moments(hull)
    return m['m00'], m['m10'] / m['m00'], float(hull[:, 1].min())


# ---------------------------------------------------------------- ước lượng

def near_bin(x, y, margin=BIN_SEARCH_MARGIN):
    reach = BIN_OUTER_HALF + margin
    return abs(x - BIN_CENTER[0]) < reach and abs(y - BIN_CENTER[1]) < reach


def inside_bin(x, y):
    return abs(x - BIN_CENTER[0]) < BIN_INNER_HALF and abs(y - BIN_CENTER[1]) < BIN_INNER_HALF


def fit_top_edge(camera, obj, u_obs, v_top_obs, z_center, start_xy, iterations=20):
    """Newton: tìm (x, y) để (u trọng tâm, v mép trên) dự đoán khớp quan sát; None nếu phân kỳ."""
    p = np.array(start_xy, float)

    def residual(q):
        _, u, v_top = silhouette_features(camera, obj, (q[0], q[1], z_center))
        return np.array([u - u_obs, v_top - v_top_obs])

    for _ in range(iterations):
        f = residual(p)
        J = np.empty((2, 2))
        for k in range(2):
            dq = np.zeros(2)
            dq[k] = _NEWTON_STEP
            J[:, k] = (residual(p + dq) - f) / _NEWTON_STEP
        try:
            step = np.linalg.solve(J, -f)
        except np.linalg.LinAlgError:
            return None
        p += step
        if np.linalg.norm(step) < 1e-7:
            return tuple(p)
    return None


def touches_border(detection, image_shape):
    x, y, w, h = detection.bbox
    height, width = image_shape[:2]
    return x <= 0 or y <= 0 or x + w >= width or y + h >= height


def estimate_object(detection, camera, obj, image_shape, use_top_edge=True):
    """
    Vị trí tâm vật từ một Detection.

    1. Tâm khối -> tia nhìn giao mặt phẳng tâm vật trên BÀN (cách của Bước 8.3).
    2. Nếu ước lượng đó gần khay: thử giả thuyết "trong khay" = khớp mép trên với tâm vật ở độ cao
       đáy khay; nhận nếu kết quả nằm trong lòng khay.
    3. Tỉ lệ nhìn thấy so với hình bóng dự đoán tại vị trí cuối -> cờ tin cậy.
    """
    u, v = detection.centroid
    table_center_z = TABLE_Z + obj.half_height
    x, y, _ = camera.pixel_to_plane(u, v, table_center_z)
    position, method = (x, y, table_center_z), 'centroid'

    if use_top_edge and near_bin(x, y):
        bin_center_z = BIN_FLOOR_Z + obj.half_height
        # Pixel trên cùng của mặt nạ có tâm ở hàng bbox y -> mép thật nằm ở khoảng y - 0.5.
        v_top_obs = detection.bbox[1] - 0.5
        fit = fit_top_edge(camera, obj, u, v_top_obs, bin_center_z, (x, y))
        if fit is not None and inside_bin(*fit):
            position, method = (fit[0], fit[1], bin_center_z), 'top_edge'

    area, _, _ = silhouette_features(camera, obj, position)
    visible = detection.area / area if area > 0 else 0.0
    cut = touches_border(detection, image_shape)
    reliable = not cut and (method == 'top_edge' or visible >= VISIBLE_MIN)
    return ObjectEstimate(position=tuple(float(c) for c in position), method=method,
                          visible_fraction=float(visible), cut_by_border=cut, reliable=reliable)
