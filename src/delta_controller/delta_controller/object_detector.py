"""
Nhận dạng vật theo kiến trúc TÁCH NỀN TRƯỚC – PHÂN LOẠI SAU (chuẩn bị Bước 10b).

Khác với `color_detector.py` (lọc ngưỡng màu trên TOÀN ảnh rồi coi mỗi màu là một vật), module
này làm ngược lại:

  1. Tách vật khỏi nền: nền là mặt bàn — tối và KHÔNG có sắc màu. Mọi thứ đủ sáng hoặc đủ bão hòa
     đều là vật. Nhờ vậy nắp nhôm bạc và chữ trắng in trên vỏ lon VẪN thuộc về vật.
  2. Mỗi vùng liên thông = một vật.
  3. Phân loại từng vật theo sắc màu chiếm ưu thế TRONG CHÍNH VÙNG ĐÓ.

Lý do đổi (đo trên 4 ảnh lon thật, 2026-09-30):
  - Logo Pepsi và logo 7Up đều có mảng ĐỎ (683–893 px và 314–884 px, so với 7347–8651 px của lon
    Coca). Lọc màu toàn ảnh rồi gộp sẽ nhập ba mảng này thành một "vật đỏ", tâm khối lệch ~9 px
    (~5 mm thật); khi trên bàn không có lon Coca thì vẫn báo thấy một vật đỏ KHÔNG TỒN TẠI.
  - Tỉ lệ pixel thực sự có màu của một lon dao động 49–84% tùy hướng xoay và ánh sáng, nên không
    dùng được làm thước đo che khuất. Diện tích vùng vật (kể cả nắp bạc, chữ trắng) mới ổn định.
  - Mặt bàn đen đo được S trung bình 20–38 và 0.0% pixel vượt S = 90 ở cả 4 ảnh -> tách nền sạch.

Module thuần Python + OpenCV, không phụ thuộc ROS.
"""

from dataclasses import dataclass

import cv2
from delta_controller.color_detector import color_mask
import numpy as np

# Pixel được coi là "có sắc màu" (dùng cho cả tách nền lẫn phân loại).
SAT_MIN = 80
# Vật phải sáng hơn nền chừng này (cộng vào ngưỡng Otsu tính riêng cho từng ảnh).
VALUE_MARGIN = 10
# Vùng nhỏ hơn thì coi là nhiễu (px).
MIN_AREA = 500
# Vùng phải có ít nhất chừng này pixel có màu mới được coi là vật (loại nền sáng lọt vào).
MIN_COLOR_FRACTION = 0.25
# Phân loại phải thắng rõ mới nhận.
MIN_CONFIDENCE = 0.5

_CLOSE_KERNEL = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
_OPEN_KERNEL = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))


@dataclass(frozen=True)
class ObjectDetection:
    """Một vật tìm thấy trên ảnh (tọa độ pixel: u sang phải, v xuống dưới)."""

    color: str            # lớp màu chiếm ưu thế trong vùng
    centroid: tuple       # (u, v) tâm khối của TOÀN vùng vật, kể cả nắp bạc và chữ trắng
    area: int             # số pixel của vùng vật
    bbox: tuple           # (x, y, w, h)
    # tỉ lệ pixel có sắc màu trong vùng — chỉ để chẩn đoán, KHÔNG dùng làm cờ che khuất
    color_fraction: float
    confidence: float     # tỉ lệ pixel màu thuộc về lớp thắng (0–1)
    # Số pixel của vùng trên TỪNG HÀNG trong khung bao (dài h). Đủ để đếm diện tích phía trên một
    # hàng bất kỳ mà không phải giữ cả mặt nạ — dùng để bỏ ẢNH PHẢN CHIẾU ra khỏi phép tính tỉ lệ
    # nhìn thấy trên mặt bàn bóng. Rỗng khi bộ nhận dạng không cung cấp.
    row_counts: tuple = ()
    # Mặt nạ của vùng, cắt theo khung bao (uint8 0/255). Chỉ dùng khi phải TÁCH vùng gộp, nên
    # None với vùng bình thường. Cắt theo khung bao nên tốn vài chục KB, không phải cả khung hình.
    crop_mask: object = None


def foreground_mask(hsv, roi=None):
    """
    Mặt nạ "không phải mặt bàn".

    Nền (mặt bàn) tối và không có sắc màu, nên vật = đủ bão hòa HOẶC đủ sáng. Ngưỡng độ sáng tính
    bằng Otsu riêng cho từng ảnh để không phụ thuộc mức chiếu sáng cụ thể. `roi` (mặt nạ 0/255)
    giới hạn vùng xét — ở hệ thật nên truyền vùng mặt bàn, tránh nền sáng ngoài bàn lọt vào.
    """
    value = hsv[:, :, 2]
    sample = value[roi > 0] if roi is not None else value.reshape(-1)
    level, _ = cv2.threshold(sample, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    mask = ((hsv[:, :, 1] >= SAT_MIN) | (value >= level + VALUE_MARGIN)).astype(np.uint8) * 255
    if roi is not None:
        mask &= roi
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, _CLOSE_KERNEL)
    return cv2.morphologyEx(mask, cv2.MORPH_OPEN, _OPEN_KERNEL)


# Pixel khác ảnh tham chiếu quá mức này (mức xám, lấy kênh lệch nhiều nhất) thì coi là VẬT.
# 30 là mức an toàn so với nhiễu cảm biến của C270 (σ ≈ 2–3 mức xám, đo 2026-09-29).
REFERENCE_DIFF = 30


def foreground_from_reference(bgr, reference, roi=None, diff_min=REFERENCE_DIFF):
    """
    Mặt nạ "khác mặt bàn trống", so với ảnh tham chiếu chụp khi bàn không có vật.

    Vì sao cần, thay cho cách lấy ngưỡng: ngưỡng cố định không bền với ánh sáng. Đo 2026-10-07
    trên cùng bố trí, cùng bộ ngưỡng: ban ngày mặt bàn sáng lên và ÁM MÀU nên lọt vào mặt nạ; thắp
    một đèn thì bàn quá tối, S = (max-min)/max hóa nhiễu và gần như CẢ MẶT BÀN lọt vào. Hai kiểu
    hỏng ngược nhau, không bộ ngưỡng nào thỏa mãn cả hai; quét phơi sáng 80–2600 và gain 0–100 đều
    không cứu được.

    So với ảnh tham chiếu thì câu hỏi đổi từ "pixel này sáng/đậm màu bao nhiêu" thành "pixel này có
    giống mặt bàn lúc trống không" — vân bàn, ám màu, chỗ sáng chỗ tối đều có y hệt trong tham
    chiếu nên tự triệt tiêu.

    ⚠️ KHÔNG xóa được ẢNH PHẢN CHIẾU của vật trên mặt bàn bóng: phản chiếu chỉ xuất hiện khi có
    vật nên nó cũng "khác bàn trống". Phản chiếu luôn nằm DƯỚI chân vật, nên chỗ dựa phải là mép
    TRÊN của hình bóng.
    ⚠️ Đổi ánh sáng là phải chụp lại tham chiếu.
    """
    diff = cv2.absdiff(bgr.astype(np.int16), reference.astype(np.int16)).max(axis=2)
    mask = (diff >= diff_min).astype(np.uint8) * 255
    if roi is not None:
        mask &= roi
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, _CLOSE_KERNEL)
    return cv2.morphologyEx(mask, cv2.MORPH_OPEN, _OPEN_KERNEL)


def classify_region(hsv, mask, color_classes):
    """Phân loại vùng theo sắc màu chiếm ưu thế: (tên lớp, độ chắc chắn, tỉ lệ có màu)."""
    pixels = hsv[mask > 0]
    if len(pixels) == 0:
        return None, 0.0, 0.0
    coloured = pixels[pixels[:, 1] >= SAT_MIN]
    fraction = len(coloured) / len(pixels)
    if len(coloured) == 0:
        return None, 0.0, 0.0
    counts = {}
    for name, cls in color_classes.items():
        n = 0
        for lo, hi in cls.ranges:
            n += int(np.count_nonzero((coloured[:, 0] >= lo[0]) & (coloured[:, 0] <= hi[0])
                                      & (coloured[:, 2] >= lo[2])))
        counts[name] = n
    best = max(counts, key=counts.get)
    total = sum(counts.values())
    return best, (counts[best] / total if total else 0.0), fraction


def detect_objects(bgr, color_classes, roi=None, min_area=MIN_AREA,
                   min_color_fraction=MIN_COLOR_FRACTION, min_confidence=MIN_CONFIDENCE,
                   reference=None):
    """
    Tìm mọi vật trên ảnh và phân loại từng vật.

    Trả về danh sách ObjectDetection, sắp theo diện tích giảm dần. Một màu có thể ứng với NHIỀU
    vật (khác hẳn `color_detector`), nên hàm này dùng được cho cảnh có hai lon cùng loại.
    """
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask = (foreground_mask(hsv, roi) if reference is None
            else foreground_from_reference(bgr, reference, roi))
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    found = []
    for i in range(1, count):
        area = int(stats[i, cv2.CC_STAT_AREA])
        if area < min_area:
            continue
        region = (labels == i).astype(np.uint8)
        x, y, w, h = (int(v) for v in stats[i, :4])
        name, confidence, fraction = classify_region(hsv, region, color_classes)
        if name is None or fraction < min_color_fraction or confidence < min_confidence:
            continue
        found.append(ObjectDetection(
            color=name,
            centroid=(float(centroids[i][0]), float(centroids[i][1])),
            area=area,
            bbox=tuple(int(v) for v in stats[i, :4]),
            color_fraction=float(fraction),
            confidence=float(confidence),
            row_counts=tuple(
                int(c) for c in region[y:y + h, x:x + w].sum(axis=1, dtype=np.int32)),
            crop_mask=(region[y:y + h, x:x + w] * 255).astype(np.uint8)))
    return sorted(found, key=lambda d: -d.area)


# Hạt giống màu phải có bấy nhiêu pixel thì mới coi là một vật riêng trong vùng gộp.
SEED_MIN_AREA = 300


def _largest_blob(mask):
    """
    Chỉ giữ mảng liên thông LỚN NHẤT của một mặt nạ màu.

    Nhãn lon mang nhiều màu: logo Pepsi có mảng đỏ, lon 7Up có vành đỏ. Những mảng đó nằm TRÊN vật
    khác nhưng vẫn là "đỏ", nên nếu dùng chúng làm hạt giống thì phép gán theo khoảng cách sẽ kéo
    cả vùng quanh lon Pepsi về phía lon Coca (đo 2026-10-08: khung bao đỏ rộng 197 px thay vì 100).
    Trong cảnh này mỗi màu ứng với đúng một vật, nên mảng lớn nhất của màu đó chính là vật.

    ⚠️ Giả định "một màu = một vật" sẽ hỏng ở bước có nhiều vật cùng màu; khi đó phải chọn hạt
    giống theo cách khác (ví dụ mọi mảng đủ lớn và cách nhau quá một bề rộng vật).
    """
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if count <= 1:
        return mask
    biggest = max(range(1, count), key=lambda i: stats[i, cv2.CC_STAT_AREA])
    return np.where(labels == biggest, 255, 0).astype(np.uint8)


def _detection_from_mask(color, part, offset):
    """Dựng ObjectDetection từ một mặt nạ con; None nếu quá nhỏ."""
    area = int(cv2.countNonZero(part))
    if area < MIN_AREA:
        return None
    x, y, w, h = cv2.boundingRect(part)
    m = cv2.moments(part)
    if m['m00'] <= 0:
        return None
    crop = part[y:y + h, x:x + w]
    return ObjectDetection(
        color=color,
        centroid=(m['m10'] / m['m00'] + offset[0], m['m01'] / m['m00'] + offset[1]),
        area=area,
        bbox=(x + offset[0], y + offset[1], w, h),
        color_fraction=1.0,
        confidence=1.0,
        row_counts=tuple(int(c) for c in (crop > 0).sum(axis=1, dtype=np.int32)),
        crop_mask=crop.copy())


def split_by_color(bgr, detection, color_classes, seed_min_area=SEED_MIN_AREA):
    """
    Tách một vùng GỘP thành các vùng con, mỗi vùng một lớp màu.

    Dùng khi hai vật đứng chạm nhau trong ảnh: phép tách nền chỉ thấy một vùng liên thông, phân
    loại cả vùng theo màu chiếm ưu thế, và **mất cả hai vật** — vật bị che thì đương nhiên, nhưng
    vật KHÔNG bị che cũng mất theo vì vùng gộp trượt phép kiểm tra kích thước.

    Cách làm: lấy điểm ảnh thuộc từng lớp màu làm **hạt giống**, rồi gán phần không mang màu (nắp
    bạc, vành nhãn, phần tối) cho hạt giống **GẦN NHẤT THEO KHOẢNG CÁCH**.

    ⚠️ Không dùng watershed, dù đó là công cụ quen tay cho bài này: watershed đi theo gradient độ
    sáng, mà vỏ lon kim loại có vệt lóa nên biên chạy loằng ngoằng sang cả vật bên cạnh. Đo
    2026-10-08 trên hai lon đứng cạnh nhau: mảnh thu được có khung bao rộng gấp đôi lon mà chỉ đặc
    0,53, và nó lấy mất ~30% điểm ảnh của lon bên cạnh. Phép gán theo khoảng cách cho biên THẲNG
    ĐỨNG, đúng với hình học hai hình trụ đứng cạnh nhau, và không phụ thuộc độ sáng.

    ⚠️ Chỉ gọi khi vùng ĐÃ TRƯỢT phép kiểm tra hình dáng. Gọi vô điều kiện thì vành logo đỏ trên
    lon 7Up cũng thành hạt giống và lon lành lặn bị xé làm đôi.
    """
    crop = detection.crop_mask
    if crop is None:
        return []
    x0, y0, w, h = detection.bbox
    hsv = cv2.cvtColor(bgr[y0:y0 + h, x0:x0 + w], cv2.COLOR_BGR2HSV)
    seed_of = np.zeros(crop.shape, np.int32)
    seeds = {}
    for index, (name, color_class) in enumerate(color_classes.items(), start=1):
        seed = cv2.bitwise_and(color_mask(hsv, color_class), crop)
        seed = cv2.morphologyEx(seed, cv2.MORPH_OPEN, _OPEN_KERNEL)
        seed = _largest_blob(seed)
        if cv2.countNonZero(seed) < seed_min_area:
            continue
        seed_of[seed > 0] = index
        seeds[index] = name
    if len(seeds) < 2:
        return []                               # chỉ một màu -> không phải vùng gộp
    # Khoảng cách tới hạt giống của TỪNG màu, rồi mỗi điểm ảnh về màu gần nhất.
    # ⚠️ Không dùng distanceTransformWithLabels với DIST_LABEL_CCOMP: nó đánh nhãn theo thành phần
    # liên thông của tập hạt giống, mà hai vật chạm nhau thì hạt giống hai màu cũng chạm nhau nên
    # gộp làm một — cả vùng về một màu (đã gặp 2026-10-08).
    best_distance = None
    assigned = np.zeros(crop.shape, np.int32)
    for index in seeds:
        src = np.where(seed_of == index, 0, 255).astype(np.uint8)
        distance = cv2.distanceTransform(src, cv2.DIST_L2, 3)
        if best_distance is None:
            best_distance, assigned[:] = distance, index
            continue
        closer = distance < best_distance
        assigned[closer] = index
        best_distance = np.minimum(best_distance, distance)
    parts = []
    for index, name in seeds.items():
        part = np.where((assigned == index) & (crop > 0), 255, 0).astype(np.uint8)
        found = _detection_from_mask(name, part, (x0, y0))
        if found is not None:
            parts.append(found)
    return parts


def detect_by_color(bgr, color_classes, **kwargs):
    """
    Màu -> vật LỚN NHẤT của màu đó, để thay thẳng cho color_detector.detect_objects.

    Khi cảnh có nhiều vật cùng màu (Bước 10c) thì dùng detect_objects và xử lý cả danh sách.
    """
    best = {}
    for d in detect_objects(bgr, color_classes, **kwargs):
        if d.color not in best:      # danh sách đã sắp theo diện tích giảm dần
            best[d.color] = d
    return best


def draw_objects(bgr, detections, color_classes):
    """Vẽ khung và nhãn lên bản sao của ảnh, phục vụ chẩn đoán."""
    vis = bgr.copy()
    for d in detections:
        x, y, w, h = d.bbox
        colour = color_classes[d.color].bgr if d.color in color_classes else (255, 255, 255)
        cv2.rectangle(vis, (x, y), (x + w, y + h), colour, 2)
        cv2.circle(vis, (int(d.centroid[0]), int(d.centroid[1])), 4, colour, -1)
        cv2.putText(vis, f'{d.color} {100 * d.confidence:.0f}%', (x, max(0, y - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, colour, 1, cv2.LINE_AA)
    return vis
