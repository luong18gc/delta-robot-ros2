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
                   min_color_fraction=MIN_COLOR_FRACTION, min_confidence=MIN_CONFIDENCE):
    """
    Tìm mọi vật trên ảnh và phân loại từng vật.

    Trả về danh sách ObjectDetection, sắp theo diện tích giảm dần. Một màu có thể ứng với NHIỀU
    vật (khác hẳn `color_detector`), nên hàm này dùng được cho cảnh có hai lon cùng loại.
    """
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask = foreground_mask(hsv, roi)
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    found = []
    for i in range(1, count):
        area = int(stats[i, cv2.CC_STAT_AREA])
        if area < min_area:
            continue
        region = (labels == i).astype(np.uint8)
        name, confidence, fraction = classify_region(hsv, region, color_classes)
        if name is None or fraction < min_color_fraction or confidence < min_confidence:
            continue
        found.append(ObjectDetection(
            color=name,
            centroid=(float(centroids[i][0]), float(centroids[i][1])),
            area=area,
            bbox=tuple(int(v) for v in stats[i, :4]),
            color_fraction=float(fraction),
            confidence=float(confidence)))
    return sorted(found, key=lambda d: -d.area)


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
