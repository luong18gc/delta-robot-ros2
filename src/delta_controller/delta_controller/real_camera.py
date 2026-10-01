"""
Ngoại tham số của camera THẬT từ marker ArUco trên bàn (Bước 10a, thuần Python).

Marker dán cố định trên bàn và luôn nằm trong khung hình, nên mỗi khung ảnh đều tự giải lại được
camera đang ở đâu. Đó là lý do module này tách khỏi `calibrate_camera_node` (node ROS, chạy MỘT
LẦN rồi lưu file cho camera mô phỏng): với camera thật, hiệu chuẩn một lần là một thiết kế dễ vỡ.

Đo 2026-10-01 (camera lùi 0.90 m, cao 0.545 m, quy về không gian ảo chia SCALE):

    camera xoay  0.5°  -> vị trí vật sai  3.9 mm ảo
    camera xoay  1°    -> sai  7.7 mm  (dung sai giác hút 12 mm)
    camera xoay  2°    -> sai 15.6 mm  -> HỎNG
    camera tịnh tiến 20 mm -> sai 6.7 mm

Giá kẹp bàn bị chạm tay hay siết lỏng dần là lệch 1–2° như chơi, mà hỏng kiểu đó **không có dấu
hiệu gì** — chỉ thấy robot gắp trượt. Nhận ArUco mất 3.8 ms, PnP dưới 1 ms (đo trên C270
1280x720), so với 12–16 ms xử lý thị giác: trả 25% CPU để không bao giờ phải lo chuyện đó.

QUY ƯỚC TỈ LỆ: toàn bộ module làm việc trong HỆ ẢO. Tọa độ marker đưa vào PnP là tọa độ thật chia
SCALE (xem `scene.real_calib_markers_virtual`), nên CameraModel trả về dùng thẳng được với
`pixel_to_plane`, hình bóng dự đoán, khay và `TABLE_Z` sẵn có — không phải đổi đơn vị ở đâu cả.
"""

from dataclasses import dataclass

import cv2
from delta_controller.camera_model import CameraModel, estimate_pose, marker_center
from delta_controller.scene import (
    CALIB_ARUCO_DICT,
    real_calib_markers_virtual,
    SCALE,
    TABLE_Z,
)
import numpy as np

# Cần ít nhất bấy nhiêu marker mới giải được tư thế. PnP cần 4 điểm; lấy dư 1 để còn phát hiện
# được nghiệm sai qua sai số chiếu lại.
MIN_MARKERS = 5
# Sai số chiếu lại trên mức này coi như hỏng (nhận nhầm marker, tọa độ dán sai, nội tham số sai).
MAX_RMS_PX = 2.0
# Trọng số làm trơn theo khung: tư thế mới chỉ được chiếm bấy nhiêu. Camera đứng yên nên làm trơn
# mạnh vẫn bám kịp khi giá đỡ xê dịch từ từ, mà bớt được nhiễu PnP từng khung.
SMOOTH = 0.15


def aruco_detector():
    """
    (từ điển, tham số) để nhận marker.

    ⚠️ OpenCV 4.6 trên máy: phải dùng `DetectorParameters_create()`; gọi kiểu mới
    `DetectorParameters()` gây segfault khi vào `detectMarkers` (gặp 2026-09-28).
    """
    dictionary = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, CALIB_ARUCO_DICT))
    params = cv2.aruco.DetectorParameters_create()
    params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_CONTOUR
    return dictionary, params


def detect_marker_centers(gray, detector=None, markers=None):
    """
    {id marker -> (u, v) tâm trên ảnh}, chỉ giữ các id có trong bố trí đã biết.

    Tâm lấy bằng GIAO HAI ĐƯỜNG CHÉO chứ không phải trung bình 4 góc: phép chiếu phối cảnh bảo
    toàn giao điểm đường chéo, còn trung bình 4 góc thì lệch khi nhìn xiên.
    """
    known = real_calib_markers_virtual() if markers is None else markers
    dictionary, params = detector if detector is not None else aruco_detector()
    corners, ids, _ = cv2.aruco.detectMarkers(gray, dictionary, parameters=params)
    if ids is None:
        return {}
    return {int(i): marker_center(c) for c, i in zip(corners, ids.flatten())
            if int(i) in known}


@dataclass(frozen=True)
class Extrinsics:
    """Kết quả ước lượng tư thế camera cho một khung ảnh."""

    model: CameraModel
    rms_px: float
    marker_ids: tuple
    errors_px: tuple

    @property
    def ok(self):
        return len(self.marker_ids) >= MIN_MARKERS and self.rms_px <= MAX_RMS_PX

    def position_real_mm(self):
        """Vị trí camera quy về bàn THẬT (mm) — để đối chiếu với thước đo."""
        return tuple(1000.0 * SCALE * c for c in self.model.position())

    def tilt_deg(self):
        """Góc chúc xuống của trục ngắm (độ)."""
        return float(np.degrees(np.arcsin(-self.model.optical_axis()[2])))


def estimate_extrinsics(centers, K, dist, markers=None, z=TABLE_Z):
    """
    Tư thế camera trong HỆ ẢO từ các tâm marker đã nhận.

    `centers`: {id -> (u, v)}. `z`: cao độ mặt phẳng chứa marker trong hệ ảo (mặt bàn). Giấy in
    dày ~0.1 mm thật = 0.03 mm ảo nên bỏ qua được.
    """
    known = real_calib_markers_virtual() if markers is None else markers
    ids = sorted(set(centers) & set(known))
    if len(ids) < 4:
        raise ValueError(f'Chi thay {len(ids)} marker, PnP can it nhat 4')
    obj = [(*known[i], z) for i in ids]
    img = [centers[i] for i in ids]
    result = estimate_pose(obj, img, K, dist)
    return Extrinsics(model=result.model, rms_px=result.rms_px, marker_ids=tuple(ids),
                      errors_px=result.errors_px)


class PoseTracker:
    """
    Giữ tư thế camera, cập nhật từ từng khung ảnh và làm trơn.

    Khung nào không đủ marker hoặc sai số chiếu lại quá lớn thì BỎ QUA, giữ nguyên tư thế cũ —
    tay người thò vào che marker một lúc không làm hỏng gì. Làm trơn theo cấp số nhân: camera
    đứng yên nên nhiễu PnP từng khung bị dập xuống, mà giá đỡ xê dịch từ từ thì vẫn bám kịp.
    """

    def __init__(self, K, dist, markers=None, smooth=SMOOTH, z=TABLE_Z):
        self.K = np.asarray(K, float)
        self.dist = np.asarray(dist, float)
        self.markers = real_calib_markers_virtual() if markers is None else markers
        self.smooth = smooth
        self.z = z
        self.model = None          # CameraModel đã làm trơn, None khi chưa khóa được lần nào
        self.last = None           # Extrinsics của khung gần nhất dùng được
        self.updates = 0
        self.skipped = 0

    def update(self, gray, detector=None):
        """Cập nhật từ một khung ảnh xám. Trả về Extrinsics vừa dùng, hoặc None nếu bỏ qua."""
        centers = detect_marker_centers(gray, detector, self.markers)
        if len(centers) < MIN_MARKERS:
            self.skipped += 1
            return None
        try:
            current = estimate_extrinsics(centers, self.K, self.dist, self.markers, self.z)
        except (ValueError, cv2.error):
            self.skipped += 1
            return None
        if not current.ok:
            self.skipped += 1
            return None
        self._blend(current.model)
        self.last = current
        self.updates += 1
        return current

    def _blend(self, new):
        if self.model is None:
            self.model = new
            return
        a = self.smooth
        self.model = CameraModel(
            K=self.K, dist=self.dist,
            rvec=(1 - a) * np.asarray(self.model.rvec, float) + a * np.asarray(new.rvec, float),
            tvec=(1 - a) * np.asarray(self.model.tvec, float) + a * np.asarray(new.tvec, float))

    @property
    def ready(self):
        return self.model is not None
