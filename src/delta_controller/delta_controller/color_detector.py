"""
Nhận dạng vật theo màu trên ảnh camera (thuần Python + OpenCV, không phụ thuộc ROS).

Quy trình cho mỗi lớp màu:
  1. BGR -> HSV: tách sắc độ (H) khỏi độ sáng (V), nên vật trong bóng đổ vẫn giữ nguyên H.
  2. Phân ngưỡng H/S/V -> mặt nạ nhị phân. Ngưỡng S loại mặt bàn (S ~77) và đáy khay (S ~20);
     ngưỡng H tách đỏ (0) khỏi khay cam (20) và platform vàng (29).
  3. Lọc hình thái học: mở (xóa nhiễu hạt) rồi đóng (lấp lỗ nhỏ).
  4. Tìm các vùng liên thông, bỏ vùng nhỏ hơn min_blob_area.
  5. Mỗi màu ứng với đúng một vật, nên GỘP mọi vùng còn lại (vật bị cánh tay/platform cắt thành
     nhiều mảnh vẫn là một vật) và lấy tâm khối (moment bậc 0/1) của phần nhìn thấy.

Số liệu HSV đo trên ảnh camera mô phỏng (Bước 8.2):
  hộp đỏ trong bóng H 0, S 174, V 95 | trụ xanh lá H 68, S 155 | cầu xanh dương H 108, S 164
  khay cam H 20, S 165 | platform vàng H 29, S 159 | bàn H 17, S 77 | đáy khay S ~20
(OpenCV: H trong [0, 180), S và V trong [0, 255].)
"""

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class ColorClass:
    """Một lớp màu: danh sách khoảng HSV (đỏ cần 2 khoảng vì nằm ở hai đầu vòng màu)."""

    name: str
    ranges: tuple   # ((h_lo, s_lo, v_lo), (h_hi, s_hi, v_hi)), ...
    bgr: tuple      # màu vẽ khung trên ảnh chú thích


COLOR_CLASSES = {
    'red': ColorClass('red', (((0, 100, 40), (8, 255, 255)),
                              ((172, 100, 40), (180, 255, 255))), (0, 0, 255)),
    'green': ColorClass('green', (((45, 90, 40), (85, 255, 255)),), (0, 200, 0)),
    'blue': ColorClass('blue', (((95, 90, 40), (125, 255, 255)),), (255, 80, 0)),
}

MIN_BLOB_AREA = 30      # px — mảnh nhỏ hơn coi là nhiễu
MIN_OBJECT_AREA = 80    # px — tổng diện tích nhìn thấy tối thiểu để báo là thấy vật
_OPEN_KERNEL = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
_CLOSE_KERNEL = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))


@dataclass(frozen=True)
class Detection:
    """Kết quả nhận dạng một vật trên ảnh (tọa độ pixel: u sang phải, v xuống dưới)."""

    color: str
    centroid: tuple   # (u, v) tâm khối phần nhìn thấy
    area: int         # số pixel nhìn thấy
    bbox: tuple       # (x, y, w, h) khung bao mọi mảnh
    pieces: int       # số mảnh (> 1 khi bị che cắt đôi)


def color_mask(hsv, color_class):
    """Mặt nạ nhị phân (0/255) của một lớp màu, đã lọc hình thái học."""
    mask = np.zeros(hsv.shape[:2], np.uint8)
    for lo, hi in color_class.ranges:
        mask |= cv2.inRange(hsv, np.array(lo, np.uint8), np.array(hi, np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, _OPEN_KERNEL)
    return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, _CLOSE_KERNEL)


def detect_color(hsv, color_class, min_blob_area=MIN_BLOB_AREA, min_object_area=MIN_OBJECT_AREA):
    """Trả về Detection của lớp màu, hoặc None nếu không thấy đủ pixel."""
    mask = color_mask(hsv, color_class)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    keep = [i for i in range(1, count) if stats[i, cv2.CC_STAT_AREA] >= min_blob_area]
    if not keep:
        return None
    selected = np.isin(labels, keep)
    area = int(selected.sum())
    if area < min_object_area:
        return None
    vs, us = np.nonzero(selected)
    x, y = int(us.min()), int(vs.min())
    return Detection(
        color=color_class.name,
        centroid=(float(us.mean()), float(vs.mean())),
        area=area,
        bbox=(x, y, int(us.max()) - x + 1, int(vs.max()) - y + 1),
        pieces=len(keep),
    )


def detect_objects(bgr, classes=COLOR_CLASSES):
    """Nhận dạng mọi lớp màu trên ảnh BGR. Trả về dict tên màu -> Detection (chỉ màu thấy được)."""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    found = {}
    for name, color_class in classes.items():
        detection = detect_color(hsv, color_class)
        if detection is not None:
            found[name] = detection
    return found


def draw_detections(bgr, detections, labels=None, classes=COLOR_CLASSES):
    """Ảnh chú thích: khung bao, dấu tâm và nhãn cho từng vật. labels: màu -> tên hiển thị."""
    out = bgr.copy()
    for color, det in detections.items():
        bgr_color = classes[color].bgr
        x, y, w, h = det.bbox
        cv2.rectangle(out, (x, y), (x + w - 1, y + h - 1), bgr_color, 1)
        u, v = int(round(det.centroid[0])), int(round(det.centroid[1]))
        cv2.drawMarker(out, (u, v), (255, 255, 255), cv2.MARKER_CROSS, 10, 2)
        cv2.drawMarker(out, (u, v), bgr_color, cv2.MARKER_CROSS, 10, 1)
        text = (labels or {}).get(color, color)
        text += f' ({u},{v})' + (f' x{det.pieces}' if det.pieces > 1 else '')
        cv2.putText(out, text, (x, max(12, y - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                    (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(out, text, (x, max(12, y - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                    (255, 255, 255), 1, cv2.LINE_AA)
    return out
