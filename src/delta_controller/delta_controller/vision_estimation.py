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

from dataclasses import dataclass, replace
import math

import cv2
from delta_controller.scene import BIN_LAYOUT, TABLE_Z
import numpy as np

# Tỉ lệ nhìn thấy tối thiểu để tin vị trí tâm khối. Trên bộ dữ liệu 8.4: 0.85 bỏ sót 1/29 ước lượng
# tệ (> 5 mm), 0.90 bỏ sót 0/29 (báo nhầm 12/143 thay vì 10/143). Bước 9 gặp đúng ca bị bỏ sót:
# hộp đỏ bị trụ xanh đứng trước che ~15% -> lệch 8 mm -> hút lệch tâm -> đè thành khay, trượt
# sang ô khác.
VISIBLE_MIN = 0.90
# ... và tối đa. Hình bóng đo được LỚN HƠN HẲN dự đoán thì thứ đang nhìn không phải vật đó: hai vật
# dính liền pixel, hoặc một thứ khác lọt vào khung mang đúng lớp màu. Gặp thật 2026-10-07 khi chạy
# bản sao số: BÀN TAY người với vào dời lon ngả đỏ cam nên rơi vào lớp màu của lon Coca, lon ảo
# nhảy 294 mm rồi quay về. Chặn dưới không bắt được vì nó chỉ hỏi tỉ lệ có TỤT hay không.
# 1.30 chừa chỗ cho phản chiếu còn sót và sai số hình bóng (đo 0.99–1.02 khi lon lành lặn).
VISIBLE_MAX = 1.30
# Bề rộng và chiều cao của hình bóng ĐO ĐƯỢC được phép lệch bao nhiêu so với hình bóng DỰ ĐOÁN.
# Đây là kiểm tra HÌNH DÁNG, và nó bắt được thứ mà tỉ lệ diện tích không bao giờ bắt được: phép
# khớp chỉ khớp MÉP TRÊN và TÂM NGANG, nên bề rộng và chiều cao là thông tin ĐỘC LẬP, không bị
# phép khớp tự điều chỉnh cho khớp. Tỉ lệ diện tích thì tự chuẩn hóa (vùng to hơn -> khớp đẩy vật
# lại gần camera -> hình bóng dự đoán cũng to hơn -> tỉ lệ vẫn ~1 dù vị trí sai hàng trăm mm).
# Gặp thật 2026-10-07 khi chạy bản sao số: VÀNH LOGO ĐỎ của lon 7Up tách thành vùng riêng, được
# phân loại là đỏ, và `detect_by_color` lấy vùng đỏ lớn nhất -> lon Coca "dịch chuyển tức thời"
# sang chỗ lon 7Up, score vẫn 1.00. Vành logo rộng mà thấp nên lệch chiều cao bắt được ngay.
SHAPE_TOLERANCE = 0.35
# Chiều cao thì KHÔNG đối xứng: ảnh phản chiếu nằm dưới chân vật vẫn ở trong khung bao, nên vật
# lành lặn đo được CAO HƠN dự đoán 16–28% (đo 2026-10-07). Nới rộng phía trên để lon thật không bị
# loại oan, nhưng giữ chặt phía dưới — vì "thấp hơn hẳn" chính là dấu hiệu của vành logo bị tách
# ra thành vùng riêng (mảnh rộng bằng lon nhưng chỉ cao bằng 1/4).
HEIGHT_MIN, HEIGHT_MAX = 0.65, 1.60
# Ước lượng thô cách thành ngoài khay tới mức này thì thử giả thuyết "vật trong khay" (m).
BIN_SEARCH_MARGIN = 0.03
# Vật CAO hơn rộng bấy nhiêu lần thì khớp MÉP ĐÁY thay vì dùng tâm khối.
# Trước đây tiêu chí là `color_fraction < 0.9` — suy luận vòng vo: lấy mức độ nhiều màu để đoán
# hình dáng. Đúng tình cờ với lon ảo (nhiều màu VÀ cao), sai hẳn khi mặt nạ là HÌNH BÓNG thật
# (nhận dạng tách nền trước): lúc đó tỉ lệ màu bằng 1 mà vật vẫn cao. Tiêu chí đúng là hình dáng:
# hình trụ cao thì tâm khối hình bóng bị kéo lên (nhìn xiên thấy cả mặt trên), còn mép đáy thì tì
# trên mặt bàn nên là đặc trưng đáng tin.
TALL_RATIO = 1.5
_NEWTON_STEP = 1e-4         # bước sai phân để tính Jacobian (m)


@dataclass(frozen=True)
class ObjectEstimate:
    position: tuple         # (x, y, z) tâm vật, hệ robot (m)
    method: str             # 'centroid' | 'bottom_edge' | 'top_edge_table' | 'top_edge' (khay)
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
        # 16 điểm/vành là đủ cho BAO LỒI của hình trụ (48 điểm chỉ tốn thời gian:
        # mỗi lần khớp Newton phải dựng hình bóng vài chục lần).
        a = np.linspace(0, 2 * math.pi, 16, endpoint=False)
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


def silhouette_size(camera, obj, center):
    """(bề rộng, chiều cao) của khung bao hình bóng dự đoán, tính bằng pixel."""
    hull = silhouette(camera, obj, center)
    return (float(hull[:, 0].max() - hull[:, 0].min()),
            float(hull[:, 1].max() - hull[:, 1].min()))


def shape_matches(detection, camera, obj, center, tolerance=SHAPE_TOLERANCE):
    """
    Khung bao đo được có đúng CỠ hình bóng dự đoán tại `center` không.

    Vì sao phép kiểm tra này bắt được thứ tỉ lệ diện tích không bắt được: phép khớp chỉ khớp MÉP
    TRÊN và TÂM NGANG, nên bề rộng và chiều cao là thông tin ĐỘC LẬP — phép khớp không tự điều
    chỉnh để chúng khớp. Tỉ lệ diện tích thì tự chuẩn hóa: vùng to hơn làm phép khớp đẩy vật lại
    gần camera, mà ở gần thì hình bóng dự đoán cũng to hơn, nên tỉ lệ vẫn ~1 dù vị trí sai hàng
    trăm milimét.
    """
    _, _, w, h = detection.bbox
    pw, ph = silhouette_size(camera, obj, center)
    if pw <= 0 or ph <= 0:
        return False
    return (abs(w / pw - 1.0) <= tolerance
            and HEIGHT_MIN <= h / ph <= HEIGHT_MAX)


def silhouette_bottom(camera, obj, center):
    """(u trọng tâm, v mép DƯỚI) của hình bóng dự đoán."""
    hull = silhouette(camera, obj, center)
    m = cv2.moments(hull)
    return m['m10'] / m['m00'], float(hull[:, 1].max())


# ---------------------------------------------------------------- ước lượng

def near_bin(x, y, margin=BIN_SEARCH_MARGIN, bins=BIN_LAYOUT):
    """Gần BẤT KỲ khay nào (từ Bước 10b mỗi loại vật có một khay riêng)."""
    reach = bins.outer_half + margin
    return any(abs(x - bx) < reach and abs(y - by) < reach for bx, by in bins.centers)


def color_shape(obj):
    """
    (Vật đại diện phần MANG MÀU, độ lệch tâm theo z).

    Đỉnh lon là nắp nhôm bạc nên mép trên của vùng màu thấp hơn đỉnh hình bóng. So mép trên của
    cả hình bóng với mép trên của vùng màu gây lệch hệ thống, càng ra rìa ảnh càng lớn.
    """
    margin = getattr(obj, 'color_top_margin', 0.0)
    if margin <= 0.0:
        return obj, 0.0
    return replace(obj, half_height=obj.half_height - margin / 2), -margin / 2


def nearest_bin(x, y, bins=BIN_LAYOUT):
    """Tâm khay gần (x, y) nhất — điểm xuất phát tốt cho phép khớp mép trên."""
    return min(bins.centers, key=lambda c: (x - c[0]) ** 2 + (y - c[1]) ** 2)


def inside_bin(x, y, bins=BIN_LAYOUT):
    """Nằm trong lòng BẤT KỲ khay nào."""
    return any(abs(x - bx) < bins.inner_half and abs(y - by) < bins.inner_half
               for bx, by in bins.centers)


def clamp_into_bin(x, y, obj, bins=BIN_LAYOUT):
    """
    Kéo (x, y) về vùng mà tâm vật CÓ THỂ nằm khi vật ở trong khay.

    Vật đứng trong khay thì tâm nó cách tâm khay không quá (nửa lòng khay − nửa bề rộng vật) —
    với khay 45 mm và lon Ø 23 mm là 11 mm. Đây là ràng buộc hình học cứng, dùng để chặn nghiệm
    Newton đi lạc thay vì vứt bỏ nghiệm rồi rơi về tâm khối thô (sai 22 mm).
    """
    cx, cy = nearest_bin(x, y, bins)
    reach = max(0.0, bins.inner_half - obj.half_width)
    return (min(max(x, cx - reach), cx + reach), min(max(y, cy - reach), cy + reach))


def _newton_fit(residual, start_xy, iterations=8):
    """Newton 2 ẩn cho hàm dư 2 chiều; None nếu phân kỳ."""
    p = np.array(start_xy, float)
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
        if np.linalg.norm(step) < 1e-6:      # 1 µm — chặt hơn mức cần thiết rồi
            return tuple(p)
    return None


def fit_bottom_edge(camera, obj, u_obs, v_bottom_obs, z_center, start_xy, iterations=8):
    """
    Newton: tìm (x, y) để (u trọng tâm, v mép DƯỚI) của hình bóng khớp quan sát.

    Dùng cho vật đứng trên bàn có bề mặt NHIỀU MÀU (lon: nắp bạc, vành chữ trắng): tâm khối của
    vùng MÀU nằm lệch xuống dưới so với tâm hình bóng — đo trên mô phỏng 2026-09-30 là 32 px,
    tương đương 28 mm, quá lớn so với dung sai. Mép dưới thì không bị lệch vì thân lon có màu
    xuống tới tận đáy, và đáy lon tì trên mặt bàn nên là đặc trưng hình học chắc chắn.
    """
    def residual(q):
        u, v_bottom = silhouette_bottom(camera, obj, (q[0], q[1], z_center))
        return np.array([u - u_obs, v_bottom - v_bottom_obs])

    return _newton_fit(residual, start_xy, iterations)


def fit_top_edge(camera, obj, u_obs, v_top_obs, z_center, start_xy, iterations=8):
    """Newton: tìm (x, y) để (u trọng tâm, v mép trên) dự đoán khớp quan sát; None nếu phân kỳ."""
    def residual(q):
        _, u, v_top = silhouette_features(camera, obj, (q[0], q[1], z_center))
        return np.array([u - u_obs, v_top - v_top_obs])

    return _newton_fit(residual, start_xy, iterations)


def touches_border(detection, image_shape):
    x, y, w, h = detection.bbox
    height, width = image_shape[:2]
    return x <= 0 or y <= 0 or x + w >= width or y + h >= height


def best_detection(regions, camera, obj, image_shape, **kwargs):
    """
    Trong các vùng CÙNG MÀU, chọn vùng thật sự là vật — ưu tiên HÌNH DÁNG, không phải kích cỡ.

    Trả về (ước lượng, vùng đã chọn), hoặc (None, None) nếu không có vùng nào.

    Vì sao không lấy ngay vùng lớn nhất: chọn theo kích cỡ là quyết định TRƯỚC khi biết vùng nào
    hợp lệ, nên một vùng rác to hơn vật sẽ loại mất chính vật đó. Gặp thật 2026-10-08 sau khi
    camera bị dời: ảnh nền cũ sinh một vùng ma rộng gấp 2,6 lần lon; nó lớn hơn lon Coca thật nên
    được chọn rồi bị cờ loại, và lon Coca thật nằm ngay đó, hợp lệ, thì biến mất.

    Vùng lớn nhất vẫn được trả về khi KHÔNG vùng nào đạt, để tầng trên còn thấy có gì đó và báo
    "không tin được" thay vì im lặng như thể bàn trống.
    """
    best = fallback = None
    for region in regions:
        estimate = estimate_object(region, camera, obj, image_shape, **kwargs)
        if fallback is None or region.area > fallback[1].area:
            fallback = (estimate, region)
        if not estimate.reliable:
            continue
        if best is None or region.area > best[1].area:
            best = (estimate, region)
    chosen = best or fallback
    return chosen if chosen is not None else (None, None)


def estimate_object(detection, camera, obj, image_shape, use_top_edge=True,
                    bins=BIN_LAYOUT, reflective_table=False):
    """
    Vị trí tâm vật từ một Detection.

    1. Giả thuyết "đứng trên bàn": tâm khối -> tia nhìn giao mặt phẳng tâm vật; với vật nhiều màu
       thì khớp MÉP DƯỚI thay cho tâm khối.
    2. Nếu vị trí đó rơi vào LÒNG KHAY thì vật không thể đứng trên bàn ở đó -> giả thuyết "trong
       khay": khớp MÉP TRÊN ở cao độ đáy khay, kéo về vùng khả thi.
    3. Tỉ lệ nhìn thấy so với hình bóng dự đoán tại vị trí cuối -> cờ tin cậy.
    """
    u, v = detection.centroid
    table_center_z = TABLE_Z + obj.half_height
    x, y, _ = camera.pixel_to_plane(u, v, table_center_z)

    # --- Giả thuyết 1: vật ĐỨNG TRÊN BÀN ---------------------------------------------------
    position, method = (x, y, table_center_z), 'centroid'
    if obj.half_height >= TALL_RATIO * obj.half_width:
        # Vật cao (lon): tâm khối lệch khỏi hình chiếu tâm 3D — với mặt nạ MÀU thì lệch xuống
        # dưới 32 px ≈ 28 mm (phần trên là nắp bạc), với HÌNH BÓNG thì lệch lên trên (nhìn xiên
        # nên thấy cả mặt trên). Mép đáy thì tì trên mặt bàn nên không bị lệch kiểu nào.
        bx, by, bw, bh = detection.bbox
        if reflective_table:
            # Mặt bàn BÓNG: nó phản chiếu vật, và ảnh phản chiếu dính liền chân vật nên mép đáy
            # của mặt nạ không còn là chỗ vật chạm bàn. Đo trên bàn thật 2026-10-07 (18 phép đo,
            # đã trừ nền tham chiếu nên mặt nạ sạch): mép đáy lệch ĐỀU −31.7…−34.3 mm thật ở cả
            # ba lon, tức đúng chiều cao ảnh phản chiếu; mép trên 4.50 mm ảo, tệ nhất 6.31 —
            # trong dung sai giác hút 12 mm. Phản chiếu luôn nằm DƯỚI nên mép trên không dính.
            fit = fit_top_edge(camera, obj, u, by - 0.5, table_center_z, (x, y))
            if fit is not None:
                position, method = (fit[0], fit[1], table_center_z), 'top_edge_table'
        else:
            fit = fit_bottom_edge(camera, obj, u, by + bh - 0.5, table_center_z, (x, y))
            if fit is not None:
                position, method = (fit[0], fit[1], table_center_z), 'bottom_edge'

    # --- Giả thuyết 2: vật NẰM TRONG KHAY --------------------------------------------------
    # Chọn giả thuyết theo TÍNH KHẢ THI VẬT LÝ: không vật nào đứng được trên mặt bàn ở chỗ đang bị
    # khay chiếm chỗ. Nếu giả thuyết "trên bàn" rơi vào lòng khay thì vật phải đang ở TRONG khay.
    # (Đừng dùng "gần khay" làm điều kiện: vật đứng trên bàn CẠNH khay cũng gần khay.)
    if use_top_edge and inside_bin(position[0], position[1], bins=bins):
        # Thành khay che nửa dưới -> mép dưới không tin được. Khớp MÉP TRÊN (mặt trên luôn lộ vì
        # camera nhìn chếch xuống), tâm vật ở cao độ đáy khay. Xuất phát từ TÂM KHAY vì vật chắc
        # chắn nằm trong đó, còn ước lượng thô lệch hàng chục mm.
        bin_center_z = bins.floor_z + obj.half_height
        v_top_obs = detection.bbox[1] - 0.5       # pixel trên cùng có tâm ở hàng bbox y
        cobj, dz = color_shape(obj)               # mép trên thấy được là của phần MANG MÀU
        cx, cy = nearest_bin(position[0], position[1], bins)
        fit = fit_top_edge(camera, cobj, u, v_top_obs, bin_center_z + dz, (cx, cy))
        if fit is not None:
            # Kéo về vùng khả thi thay vì vứt bỏ: tâm vật trong khay cách tâm khay không quá
            # (nửa lòng khay − nửa bề rộng vật).
            fx, fy = clamp_into_bin(fit[0], fit[1], obj, bins)
            position, method = (fx, fy, bin_center_z), 'top_edge'
        else:
            # Không khớp được: lấy TÂM KHAY (sai số bị chặn bởi kích thước khay, vẫn tốt hơn tâm
            # khối thô ~22 mm) nhưng đánh dấu KHÔNG tin cậy để hệ điều khiển quan sát lại.
            position, method = (cx, cy, bin_center_z), 'bin_center'

    area, _, _ = silhouette_features(camera, obj, position)
    seen_area = detection.area
    if reflective_table and method == 'top_edge_table' and detection.row_counts:
        # Mặt bàn bóng: ẢNH PHẢN CHIẾU nằm dưới chân vật và vẫn ở trong mặt nạ, nên nó thổi phồng
        # tỉ lệ nhìn thấy (đo 2026-10-07: 1.08–1.29 thay vì ~1.00). Cờ che khuất báo khi tỉ lệ TỤT
        # dưới VISIBLE_MIN, nên xuất phát từ 1.2 nghĩa là phải bị che ~30% mới báo. Đã biết vị trí
        # vật nên biết chân vật đáng lẽ nằm ở hàng nào — chỉ đếm phần PHÍA TRÊN hàng đó.
        v_bottom = float(silhouette(camera, obj, position)[:, 1].max())
        top = detection.bbox[1]
        seen_area = sum(c for k, c in enumerate(detection.row_counts) if top + k <= v_bottom)
    # Chia cho tỉ lệ màu danh nghĩa: vật nhiều màu (lon có nắp bạc, chữ trắng) chỉ mang màu trên
    # một phần hình bóng, nên phải so với phần ĐÁNG LẼ thấy được chứ không so với cả hình bóng.
    expected = area * getattr(obj, 'color_fraction', 1.0)
    visible = seen_area / expected if expected > 0 else 0.0
    cut = touches_border(detection, image_shape)
    # Hình dáng: chỉ đòi hỏi khi vật đứng trên bàn. Vật trong khay bị thành khay che nửa dưới nên
    # khung bao đo được THẤP HƠN hình bóng đầy đủ — đúng như vậy mới phải.
    shape_ok = method == 'top_edge' or shape_matches(detection, camera, obj, position)
    reliable = (not cut and method != 'bin_center' and visible <= VISIBLE_MAX and shape_ok
                and (method == 'top_edge' or visible >= VISIBLE_MIN))
    return ObjectEstimate(position=tuple(float(c) for c in position), method=method,
                          visible_fraction=float(visible), cut_by_border=cut, reliable=reliable)
