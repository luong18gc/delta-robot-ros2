#!/usr/bin/env python3
"""
Phân tích sai số thị giác trên bộ dữ liệu (Bước 8.4) -> bảng số + hình cho báo cáo.

    python3 src/delta_controller/scripts/evaluate_vision.py [dataset] [calibration.yaml]
Mặc định: ~/ros2_closed_loop_ws/datasets/vision_eval,
          ~/ros2_closed_loop_ws/calibration/side_camera.yaml
Ghi: docs/results/vision_eval.md, docs/results/vision_eval.csv, docs/figures/vision_*.png
"""

import csv
import os
import sys

import cv2
from delta_controller.camera_model import CameraModel
from delta_controller.color_detector import detect_objects
from delta_controller.delta_kinematics import inverse_kinematics, UnreachableError
from delta_controller.gripper_logic import PLATFORM_HALF_THICKNESS
from delta_controller.scene import (
    BIN_CENTER,
    BIN_OUTER_HALF,
    CALIB_MARKER_SIZE,
    CALIB_MARKERS,
    OBJECTS,
)
from delta_controller.vision_eval import bias, COLOR_OF, evaluate, load_dataset, summarize
import matplotlib
import matplotlib.pyplot as plt
import yaml

WS = os.path.expanduser('~/ros2_closed_loop_ws')
NOISE_LEVELS = (0, 5, 10, 20, 30, 40, 60)
BRIGHTNESS_LEVELS = (0.2, 0.3, 0.5, 0.7, 1.0, 1.3, 1.6, 2.0)
LABEL = {'red_box': 'Hộp đỏ', 'green_cylinder': 'Trụ xanh lá', 'blue_sphere': 'Cầu xanh dương'}


def touches_border(record, samples_by_image):
    """Vật bị cắt ở mép ảnh (khung bao chạm mép) -> tâm phần nhìn thấy bị lệch."""
    img = cv2.imread(samples_by_image[record.image])
    det = detect_objects(img).get(COLOR_OF[record.name])
    if det is None:
        return False
    x, y, w, h = det.bbox
    H, W = img.shape[:2]
    return x <= 0 or y <= 0 or x + w >= W or y + h >= H


def graspable(record):
    """Robot với tới điểm chạm đỉnh vật (theo vị trí thật) không."""
    half = {o.name: o.half_height for o in OBJECTS}[record.name]
    x, y, z = record.ground_truth
    try:
        inverse_kinematics(x, y, z + half + PLATFORM_HALF_THICKNESS)
        return True
    except UnreachableError:
        return False


def fmt(stats):
    if 'mean_mm' not in stats:
        return f"| {stats['n']} | {100 * stats['detection_rate']:.1f}% | – | – | – | – | – |"
    return (f"| {stats['n']} | {100 * stats['detection_rate']:.1f}% | {stats['mean_mm']:.2f} | "
            f"{stats['median_mm']:.2f} | {stats['rms_mm']:.2f} | {stats['p95_mm']:.2f} | "
            f"{stats['max_mm']:.2f} |")


def header(first_column):
    return [f'| {first_column} | Số mẫu | Nhận dạng được | TB (mm) | Trung vị | RMS | P95 | Max |',
            '|---|---|---|---|---|---|---|---|']


def main():
    matplotlib.use('Agg')
    dataset = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WS, 'datasets', 'vision_eval')
    calib = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        WS, 'calibration', 'side_camera.yaml')
    out_md = os.path.join(WS, 'docs', 'results', 'vision_eval.md')
    fig_dir = os.path.join(WS, 'docs', 'figures')
    os.makedirs(os.path.dirname(out_md), exist_ok=True)
    os.makedirs(fig_dir, exist_ok=True)

    with open(calib) as f:
        camera = CameraModel.from_dict(yaml.safe_load(f)['camera'])
    samples = load_dataset(dataset)
    by_image = {os.path.basename(s.image_path): s.image_path for s in samples}
    records = evaluate(samples, camera)
    cut = {id(r): touches_border(r, by_image) for r in records}

    lines = ['# Đánh giá sai số thị giác (Bước 8.4)', '',
             f'Bộ dữ liệu: `{dataset}` — {len(samples)} ảnh, {len(records)} lượt chấm vật.',
             'Sai số = khoảng cách **ngang** (x, y) giữa vị trí camera ước lượng và vị trí thật '
             f'(odometry Gazebo). Hiệu chuẩn: `{calib}`.', '', '## 1. Tổng hợp', '',
             *header('Nhóm')]

    def row(name, recs):
        lines.append(f'| {name} ' + fmt(summarize(recs)))

    grid = [r for r in records if r.scenario == 'grid']
    grid_in = [r for r in grid if not cut[id(r)]]
    row('Lưới — mọi điểm', grid)
    row('Lưới — vật **trọn trong ảnh**', grid_in)
    row('Lưới — vật **bị cắt mép ảnh**', [r for r in grid if cut[id(r)]])
    row('Lưới — **trong tầm với của robot**', [r for r in grid if graspable(r)])
    row('Lưới — trong tầm với, sai số ≤ 12 mm (dung sai giác hút)',
        [r for r in grid if graspable(r) and r.detected and r.error_xy <= 0.012])
    for obj in OBJECTS:
        row(f'Lưới trọn trong ảnh — {LABEL[obj.name]}', [r for r in grid_in if r.name == obj.name])
    row('Vật trong khay (mặt đáy cao hơn bàn 3 mm)', [r for r in records if r.scenario == 'bin'])
    bx, by = bias(grid_in)
    lines += ['', f'Độ lệch hệ thống (lưới, trọn trong ảnh): dx = {bx:+.2f} mm, '
              f'dy = {by:+.2f} mm.', '', '## 2. Bị platform che (robot lơ lửng phía trên vật)', '',
              *header('Khe platform – đỉnh vật (mm)')]
    occ = [r for r in records if r.scenario == 'occlusion']
    for gap in sorted({r.meta['gap_mm'] for r in occ}, reverse=True):
        lines.append(f'| {gap:.0f} ' + fmt(summarize([r for r in occ if r.meta['gap_mm'] == gap])))

    # ---------------------------------------------------------------- nhiễu và độ sáng
    grid_samples = [s for s in samples if s.scenario == 'grid']
    in_images = {r.image for r in grid_in}
    clean_samples = [s for s in grid_samples if os.path.basename(s.image_path) in in_images]
    noise_rows, bright_rows = [], []
    for sigma in NOISE_LEVELS:
        noise_rows.append((sigma, summarize(evaluate(clean_samples, camera, noise_sigma=sigma))))
    for scale in BRIGHTNESS_LEVELS:
        bright_rows.append((scale, summarize(evaluate(clean_samples, camera, brightness=scale))))
    lines += ['', '## 3. Độ bền với nhiễu Gauss (lưới, vật trọn trong ảnh)', '',
              *header('σ (mức xám)')]
    lines += [f'| {s} ' + fmt(st) for s, st in noise_rows]
    lines += ['', '## 4. Độ bền với thay đổi độ sáng (lưới, vật trọn trong ảnh)', '',
              *header('Hệ số sáng')]
    lines += [f'| {s} ' + fmt(st) for s, st in bright_rows]
    with open(out_md, 'w') as f:
        f.write('\n'.join(lines) + '\n')

    with open(os.path.join(WS, 'docs', 'results', 'vision_eval.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['image', 'scenario', 'object', 'gt_x', 'gt_y', 'est_x', 'est_y', 'error_mm',
                    'cut_by_border', 'meta'])
        for r in records:
            e = r.estimate or (None, None)
            w.writerow([r.image, r.scenario, r.name, r.ground_truth[0], r.ground_truth[1],
                        e[0], e[1], None if r.error_xy is None else r.error_xy * 1000,
                        cut[id(r)], r.meta])

    # ---------------------------------------------------------------- hình
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), constrained_layout=True)
    vmax = max(3.0, max((r.error_xy * 1000 for r in grid_in if r.detected), default=3.0))
    for ax, obj in zip(axes, OBJECTS):
        recs = [r for r in grid if r.name == obj.name]
        ok = [r for r in recs if r.detected and not cut[id(r)]]
        sc = ax.scatter([1000 * r.ground_truth[1] for r in ok],
                        [1000 * r.ground_truth[0] for r in ok],
                        c=[1000 * r.error_xy for r in ok], cmap='viridis', vmin=0, vmax=vmax, s=90)
        bad = [r for r in recs if not r.detected or cut[id(r)]]
        ax.scatter([1000 * r.ground_truth[1] for r in bad],
                   [1000 * r.ground_truth[0] for r in bad],
                   marker='x', color='crimson', s=60, label='bị cắt mép / không thấy')
        ax.add_patch(plt.Rectangle((1000 * (BIN_CENTER[1] - BIN_OUTER_HALF),
                                    1000 * (BIN_CENTER[0] - BIN_OUTER_HALF)),
                                   2000 * BIN_OUTER_HALF, 2000 * BIN_OUTER_HALF,
                                   fill=False, ec='darkorange', lw=1.5))
        for mx, my in CALIB_MARKERS.values():
            s = 1000 * CALIB_MARKER_SIZE
            ax.add_patch(plt.Rectangle((1000 * my - s / 2, 1000 * mx - s / 2), s, s,
                                       fill=False, ec='gray', ls='--'))
        ax.set_title(LABEL[obj.name])
        ax.set_xlabel('y robot (mm)')
        ax.set_ylabel('x robot (mm)  ↑ xa camera')
        ax.invert_xaxis()      # nhìn từ phía camera: +y bên trái
        ax.set_aspect('equal')
        ax.set_xlim(190, -190)
        ax.set_ylim(-190, 190)
        ax.grid(alpha=0.3)
    axes[0].legend(loc='lower left', fontsize=8)
    fig.colorbar(sc, ax=axes, label='sai số ngang (mm)', shrink=0.8)
    fig.savefig(os.path.join(fig_dir, 'vision_error_map.png'), dpi=130)

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.2), constrained_layout=True)
    for ax, rows, xlabel in ((a1, noise_rows, 'độ lệch chuẩn nhiễu σ (mức xám)'),
                             (a2, bright_rows, 'hệ số độ sáng')):
        xs = [x for x, _ in rows]
        ax.plot(xs, [st.get('mean_mm', float('nan')) for _, st in rows], 'o-', label='TB (mm)')
        ax.plot(xs, [st.get('p95_mm', float('nan')) for _, st in rows], 's--', label='P95 (mm)')
        ax.set_xlabel(xlabel)
        ax.set_ylabel('sai số ngang (mm)')
        ax.grid(alpha=0.3)
        ax2 = ax.twinx()
        ax2.plot(xs, [100 * st['detection_rate'] for _, st in rows], 'd:', color='crimson',
                 label='nhận dạng được (%)')
        ax2.set_ylabel('nhận dạng được (%)', color='crimson')
        ax2.set_ylim(0, 105)
        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax.legend(h1 + h2, l1 + l2, fontsize=8, loc='upper left')
    a1.set_title('Nhiễu Gauss')
    a2.set_title('Độ sáng')
    fig.savefig(os.path.join(fig_dir, 'vision_robustness.png'), dpi=130)
    print(open(out_md).read())


if __name__ == '__main__':
    main()
