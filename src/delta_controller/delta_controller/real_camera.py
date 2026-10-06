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
    REAL_CALIB_MARKER_SIZE,
    real_calib_markers_virtual,
    REAL_CAN_HEIGHT,
    real_roi_virtual,
    SCALE,
    TABLE_Z,
)
import numpy as np

# Cần ít nhất bấy nhiêu marker mới giải được tư thế. PnP cần 4 điểm; lấy dư 1 để còn phát hiện
# được nghiệm sai qua sai số chiếu lại.
MIN_MARKERS = 5
# Sai số trên mức này coi như hỏng (nhận nhầm marker, tọa độ dán sai, nội tham số sai).
# ⚠️ Đo bằng MILIMÉT trong không gian ảo, không phải pixel: cùng một sai số pixel ứng với số
# milimét khác hẳn tùy camera đặt gần hay xa, và thứ quyết định gắp được hay không là milimét so
# với dung sai giác hút 12 mm. Bố trí thật 2026-10-05 cho RMS 3.25 px — nghe như hỏng, quy ra chỉ
# 0.93 mm ảo (mô phỏng đạt 1.13 mm). Ngưỡng 2 px cũ loại sạch mọi khung, node không chạy nổi.
MAX_RMS_MM = 3.0
# Khoét quanh mỗi marker bấy nhiêu lần cạnh marker. 1.5 là mức vừa: đủ trùm tờ giấy và viền trắng,
# chưa ăn vào lon đứng cạnh. Đo 2026-10-06: khoét 2.3 lần thì lon Coca hết dính vệt băng dính
# (tỉ lệ cao/rộng về đúng 2.57) nhưng tỉ lệ nhìn thấy tụt còn 0.85 vì đã cắt mất một phần lon —
# vá kiểu đó là giấu lỗi. Vệt băng dính trên bàn phải DỌN, không chữa bằng ngưỡng.
MARKER_CUTOUT = 1.5
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
    errors_mm: tuple          # sai số từng marker, MILIMÉT trong không gian ảo

    @property
    def rms_mm(self):
        return float(np.sqrt(np.mean(np.square(self.errors_mm))))

    @property
    def ok(self):
        return len(self.marker_ids) >= MIN_MARKERS and self.rms_mm <= MAX_RMS_MM

    def position_real_mm(self, table_z=TABLE_Z):
        """
        Vị trí camera trên bàn THẬT (mm): x, y so với gốc O; z so với MẶT BÀN.

        ⚠️ Không quy đổi thẳng `z_ảo × SCALE`: trong hệ ảo mặt bàn nằm ở TABLE_Z = -0.22 chứ
        không phải 0, nên làm vậy sẽ ra chiều cao ÂM và tưởng camera nằm dưới mặt bàn (đã gặp
        2026-10-05: báo -45 mm trong khi camera thật cao ~615 mm).
        """
        x, y, z = self.model.position()
        # float() tường minh: model.position() trả về numpy.float64, mà yaml.safe_dump không ghi
        # được kiểu đó (gặp 2026-10-05 khi lưu file hiệu chuẩn).
        return (float(1000.0 * SCALE * x), float(1000.0 * SCALE * y),
                float(1000.0 * SCALE * (z - table_z)))

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
    # Sai số quy ra milimét: bắn tia qua pixel đo được, cắt mặt bàn, so với chỗ marker PHẢI nằm.
    errors_mm = tuple(
        1000.0 * float(np.linalg.norm(
            np.array(result.model.pixel_to_plane(*centers[i], z)[:2]) - np.array(known[i])))
        for i in ids)
    return Extrinsics(model=result.model, rms_px=result.rms_px, marker_ids=tuple(ids),
                      errors_px=result.errors_px, errors_mm=errors_mm)


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


def marker_cutouts(camera, mask, margin=MARKER_CUTOUT):
    """
    Khoét 6 ô marker khỏi mặt nạ vùng xét.

    Giấy marker trắng nên LUÔN là "không phải mặt bàn"; lon đứng sát marker sẽ dính liền với nó
    thành một vùng, và hình bóng thu được phình ra vô nghĩa. Vị trí marker thì biết trước nên loại
    bằng hình học là chắc chắn nhất.
    """
    half = REAL_CALIB_MARKER_SIZE / 2 / SCALE * margin
    for x, y in real_calib_markers_virtual().values():
        corners = [(x - half, y - half), (x + half, y - half),
                   (x + half, y + half), (x - half, y + half)]
        uv = camera.project([(cx, cy, TABLE_Z) for cx, cy in corners]).astype(np.int32)
        cv2.fillConvexPoly(mask, uv.reshape(-1, 1, 2), 0)
    return mask


def table_roi_mask(camera, shape, height=REAL_CAN_HEIGHT / SCALE):
    """
    Mặt nạ 0/255 của vùng bàn đáng xét, chiếu qua mô hình camera.

    Lấy bao lồi của 4 góc vùng ở CẢ HAI cao độ — mặt bàn và đỉnh lon. Chỉ chiếu ở mặt bàn thì
    phần trên của lon (cao 147 mm thật) nằm cao hơn trong ảnh và bị cắt mất.
    """
    corners = real_roi_virtual()
    points = ([(x, y, TABLE_Z) for x, y in corners]
              + [(x, y, TABLE_Z + height) for x, y in corners])
    uv = camera.project(points).astype(np.float32)
    hull = cv2.convexHull(uv).reshape(-1, 1, 2).astype(np.int32)
    mask = np.zeros(shape[:2], np.uint8)
    cv2.fillConvexPoly(mask, hull, 255)
    return marker_cutouts(camera, mask)
