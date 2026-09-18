"""
Đánh giá sai số thị giác offline trên bộ dữ liệu (Bước 8.4) — thuần Python + OpenCV.

Tái hiện đúng chuỗi xử lý của node `vision`: nhận dạng màu -> vision_estimation.estimate_object
(tâm khối + tia nhìn; khớp mép trên cho vật trong khay; tỉ lệ nhìn thấy -> cờ tin cậy). So với vị
trí thật (odometry Gazebo) theo phương ngang (x, y) — đại lượng mà robot cần để gắp.
use_top_edge=False tái hiện cách của Bước 8.3/8.4 (chỉ tâm khối) để so sánh trước/sau.

Nhiễu loạn để thử độ bền (camera mô phỏng thực tế KHÔNG có nhiễu, xem Bước 8.3):
  noise_sigma — nhiễu Gauss cộng vào từng kênh màu (mức xám 0–255)
  brightness  — nhân độ sáng (mô phỏng thay đổi ánh sáng), cắt về [0, 255]
"""

from dataclasses import dataclass, field
import json
import math
import os

import cv2
from delta_controller.color_detector import detect_objects
from delta_controller.scene import OBJECTS
from delta_controller.vision_estimation import estimate_object
import numpy as np

COLOR_OF = {o.name: o.color for o in OBJECTS}


@dataclass(frozen=True)
class Sample:
    image_path: str
    scenario: str
    meta: dict
    ground_truth: dict    # tên vật -> (x, y, z) hệ robot


@dataclass(frozen=True)
class Record:
    image: str
    scenario: str
    name: str
    ground_truth: tuple
    estimate: tuple = None        # None nếu không nhận dạng được
    meta: dict = field(default_factory=dict)
    method: str = None            # 'centroid' | 'top_edge'
    visible_fraction: float = None
    reliable: bool = None

    @property
    def detected(self):
        return self.estimate is not None

    @property
    def error_xy(self):
        """Sai số ngang (m); None nếu không nhận dạng được."""
        if self.estimate is None:
            return None
        return math.hypot(self.estimate[0] - self.ground_truth[0],
                          self.estimate[1] - self.ground_truth[1])


def load_dataset(directory):
    with open(os.path.join(directory, 'labels.json')) as f:
        data = json.load(f)
    return [Sample(image_path=os.path.join(directory, s['image']), scenario=s['scenario'],
                   meta={k: v for k, v in s.items()
                         if k not in ('image', 'scenario', 'ground_truth')},
                   ground_truth={k: tuple(v) for k, v in s['ground_truth'].items()})
            for s in data['samples']]


def perturb(bgr, noise_sigma=0.0, brightness=1.0, seed=0):
    """Ảnh sau khi đổi độ sáng rồi cộng nhiễu Gauss (tất định theo seed)."""
    img = bgr.astype(np.float32) * brightness
    if noise_sigma > 0:
        img += np.random.default_rng(seed).normal(0.0, noise_sigma, img.shape)
    return np.clip(img, 0, 255).astype(np.uint8)


def estimate_positions(bgr, camera, use_top_edge=True):
    """Tên vật -> ObjectEstimate trong hệ robot, cho các vật nhận dạng được."""
    found = detect_objects(bgr)
    return {o.name: estimate_object(found[o.color], camera, o, bgr.shape, use_top_edge)
            for o in OBJECTS if o.color in found}


def evaluated_objects(sample):
    """Vật cần chấm điểm trong mẫu: vật vừa bị dời / vật bị che, không lặp lại vật đứng yên."""
    name = sample.meta.get('moved') or sample.meta.get('target')
    return [name] if name else list(sample.ground_truth)


def evaluate(samples, camera, noise_sigma=0.0, brightness=1.0, use_top_edge=True):
    records = []
    for i, sample in enumerate(samples):
        bgr = cv2.imread(sample.image_path)
        if bgr is None:
            raise FileNotFoundError(sample.image_path)
        estimates = estimate_positions(perturb(bgr, noise_sigma, brightness, seed=i), camera,
                                       use_top_edge)
        for name in evaluated_objects(sample):
            est = estimates.get(name)
            records.append(Record(
                image=os.path.basename(sample.image_path), scenario=sample.scenario, name=name,
                ground_truth=sample.ground_truth[name], meta=sample.meta,
                estimate=None if est is None else est.position,
                method=None if est is None else est.method,
                visible_fraction=None if est is None else est.visible_fraction,
                reliable=None if est is None else est.reliable))
    return records


def summarize(records):
    """Thống kê sai số ngang (mm) và tỉ lệ nhận dạng."""
    errors = np.array([r.error_xy for r in records if r.detected]) * 1000.0
    n = len(records)
    if len(errors) == 0:
        return {'n': n, 'detection_rate': 0.0}
    return {
        'n': n,
        'detection_rate': len(errors) / n if n else 0.0,
        'mean_mm': float(errors.mean()),
        'median_mm': float(np.median(errors)),
        'rms_mm': float(np.sqrt(np.mean(errors ** 2))),
        'p95_mm': float(np.percentile(errors, 95)),
        'max_mm': float(errors.max()),
    }


def bias(records):
    """Sai số trung bình có dấu (dx, dy) mm — độ lệch hệ thống."""
    d = np.array([(r.estimate[0] - r.ground_truth[0], r.estimate[1] - r.ground_truth[1])
                  for r in records if r.detected]) * 1000.0
    return (float(d[:, 0].mean()), float(d[:, 1].mean())) if len(d) else (float('nan'),) * 2


def flag_quality(records, bad_mm=5.0):
    """
    Cờ tin cậy có bắt đúng các ước lượng tệ không (sai số > bad_mm).

    recall: tỉ lệ ước lượng tệ bị gắn "không tin cậy";
    false_alarm: tỉ lệ ước lượng tốt bị gắn nhầm.
    """
    det = [r for r in records if r.detected]
    bad = [r for r in det if r.error_xy * 1000 > bad_mm]
    good = [r for r in det if r.error_xy * 1000 <= bad_mm]
    return {
        'bad': len(bad), 'good': len(good),
        'recall': sum(not r.reliable for r in bad) / len(bad) if bad else float('nan'),
        'false_alarm': sum(not r.reliable for r in good) / len(good) if good else float('nan'),
        'reliable_max_mm': max((r.error_xy * 1000 for r in det if r.reliable),
                               default=float('nan')),
    }
