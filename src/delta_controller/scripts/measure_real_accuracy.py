#!/usr/bin/env python3
"""
Đo SAI SỐ THẬT của khối thị giác camera thật, so với vị trí biết trước (Bước 10a).

    python3 src/delta_controller/scripts/measure_real_accuracy.py

Cửa sổ camera VẼ SẴN vòng tròn vào đúng chỗ phải đặt từng lon (chiếu điểm đích qua mô hình camera),
nên không cần căn bằng mắt: đặt lon vào vòng tròn mang tên nó, bấm PHÍM CÁCH, script chụp nhiều
khung, lấy TRUNG VỊ rồi so với vị trí đúng. Cuối cùng in bảng sai số để đối chiếu với 1.13 mm của
mô phỏng.

Ba lon đổi chỗ cho nhau qua các lượt, nên mỗi lon được đo ở mọi điểm mà chỉ cần ít lần đặt.

Phím: PHÍM CÁCH = đã đặt xong, đo lượt này. `s` = bỏ qua lượt. `q` = dừng và xem kết quả.

⚠️ Vòng tròn trên màn hình vẽ theo ngoại tham số ĐANG đo được, nên nó chỉ đúng khi hiệu chuẩn đúng
— đó cũng chính là thứ đang được kiểm tra. Nếu muốn độc lập hoàn toàn thì đánh dấu bằng thước lên
mặt bàn rồi đặt lon theo dấu, vòng tròn chỉ để tham khảo.
"""

import argparse
import collections
import sys

import _workspace  # noqa: F401
import cv2
from delta_controller import usb_camera
from delta_controller.color_detector import COLOR_CLASSES
from delta_controller.object_detector import detect_by_color
from delta_controller.real_camera import aruco_detector, PoseTracker, table_roi_mask
from delta_controller.scene import (
    REAL_CAN_HEIGHT,
    REAL_OBJECTS,
    REAL_ROI_X,
    REAL_ROI_Y,
    SCALE,
    TABLE_Z,
)
from delta_controller.vision_estimation import estimate_object
import numpy as np
import yaml

WS = '/home/luong18gc/ros2_closed_loop_ws'
INTRINSICS = f'{WS}/calibration/c270_intrinsics.yaml'
FRAMES = 15
# Hai lon phải cách nhau ít nhất bấy nhiêu mm, và một lon không được nằm sát đường nhìn từ camera
# tới lon khác (nếu không nó che mất lon phía sau).
MIN_GAP_MM = 120.0
SIGHT_CLEAR_MM = 90.0
# Lề pixel đòi hỏi quanh ĐÁY và ĐỈNH lon khi chiếu lên ảnh.
EDGE_MARGIN_PX = 30


def feasible_points(camera, shape, step=10.0):
    """
    Các điểm (mm thật) đặt lon được: cả đáy lẫn ĐỈNH lon nằm trong khung và trong vùng xét.

    Tính TỪ TƯ THẾ CAMERA ĐANG ĐO ĐƯỢC chứ không từ hằng số: vùng dùng được phụ thuộc camera đặt
    ở đâu, mà hằng số trong scene.py được chọn theo hình học DỰ KIẾN. Giá đỡ thật gần và dốc hơn
    nên bộ điểm cũ đưa đỉnh lon ra ngoài mép trên khung hình, và mọi phép đo trả về rỗng
    (2026-10-06).
    """
    h, w = shape[:2]
    top_z = TABLE_Z + REAL_CAN_HEIGHT / SCALE
    good = []
    xs = np.arange(REAL_ROI_X[0] + 20, REAL_ROI_X[1] - 19, step)
    ys = np.arange(REAL_ROI_Y[0] + 20, REAL_ROI_Y[1] - 19, step)
    for x in xs:
        for y in ys:
            vx, vy = x / 1000.0 / SCALE, y / 1000.0 / SCALE
            uv = camera.project([(vx, vy, TABLE_Z), (vx, vy, top_z)])
            if all(EDGE_MARGIN_PX < u < w - EDGE_MARGIN_PX
                   and EDGE_MARGIN_PX < v < h - EDGE_MARGIN_PX for u, v in uv):
                good.append((float(x), float(y)))
    return good


def _hides(a, b, eye):
    """Lon ở `a` có nằm chắn đường nhìn từ `eye` tới lon ở `b` không (nhìn từ trên)."""
    a, b, eye = np.array(a), np.array(b), np.array(eye)
    if np.linalg.norm(a - eye) >= np.linalg.norm(b - eye):
        return False                      # a ở xa hơn thì không che được b
    d = b - eye
    t = np.clip(np.dot(a - eye, d) / np.dot(d, d), 0.0, 1.0)
    return float(np.linalg.norm(eye + t * d - a)) < SIGHT_CLEAR_MM


def choose_points(camera, shape, eye):
    """Hai bộ ba điểm trải rộng trong vùng dùng được, không lon nào che lon nào."""
    good = feasible_points(camera, shape)
    if len(good) < 20:
        raise SystemExit('Vung dat lon qua hep — chinh camera cho thay nhieu mat ban hon.')
    pts = np.array(good)
    x0, x1 = np.percentile(pts[:, 0], [12, 88])
    y0, y1 = np.percentile(pts[:, 1], [12, 88])
    xm, ym = pts[:, 0].mean(), pts[:, 1].mean()

    def snap(target):
        return tuple(pts[np.argmin(np.linalg.norm(pts - np.array(target), axis=1))])

    layouts = [[(x0, y1), (xm, ym), (x1, y0)], [(x0, y0), (xm, y1), (x1, ym)]]
    sets = []
    for want in layouts:
        trio = [snap(t) for t in want]
        ok = all(np.linalg.norm(np.array(a) - np.array(b)) >= MIN_GAP_MM
                 and not _hides(a, b, eye) and not _hides(b, a, eye)
                 for i, a in enumerate(trio) for b in trio[i + 1:])
        if not ok:                        # lùi về bộ ba trải theo đường chéo khác
            trio = [snap((x0, ym)), snap((xm, y0)), snap((x1, y1))]
        sets.append(tuple(trio))
    return tuple(sets)


def to_pixel(camera, x_mm, y_mm):
    """Điểm trên bàn THẬT (mm) -> pixel, qua hệ ảo."""
    uv = camera.project([(x_mm / 1000.0 / SCALE, y_mm / 1000.0 / SCALE, TABLE_Z)])
    return int(round(uv[0][0])), int(round(uv[0][1]))


def preview(cap, tracker, detector, objects, truth, title, label):
    """
    Hiện ảnh trực tiếp kèm vòng tròn ĐÍCH cho từng lon; trả về phím người dùng bấm.

    Vẽ đích bằng cách chiếu điểm thật qua mô hình camera, nên người đặt lon không phải căn bằng mắt
    hay đo lại bằng thước mỗi lượt.
    """
    colors = {o.name: o for o in objects.values()}
    while True:
        ok, frame = cap.read()
        if not ok:
            continue
        tracker.update(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), detector)
        if not tracker.ready:
            cv2.putText(frame, 'chua khoa duoc tu the camera', (12, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 160, 255), 2)
            cv2.imshow(title, frame)
            if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
                return 'q'
            continue
        camera = tracker.model
        roi = table_roi_mask(camera, frame.shape)
        found = detect_by_color(frame, COLOR_CLASSES, roi=roi)
        view = frame.copy()
        for name, (tx, ty) in truth.items():
            u, v = to_pixel(camera, tx, ty)
            bgr = COLOR_CLASSES[colors[name].color].bgr
            cv2.circle(view, (u, v), 26, bgr, 2)
            cv2.drawMarker(view, (u, v), bgr, cv2.MARKER_CROSS, 18, 1)
            cv2.putText(view, name.split('_')[0], (u - 24, v - 32),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 4, cv2.LINE_AA)
            cv2.putText(view, name.split('_')[0], (u - 24, v - 32),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, bgr, 1, cv2.LINE_AA)
        for color, det in found.items():            # vật đang nhận ra: khung bao + tâm
            x, y, w, h = det.bbox
            cv2.rectangle(view, (x, y), (x + w, y + h), COLOR_CLASSES[color].bgr, 1)
        missing = [n.split('_')[0] for n, o in colors.items() if o.color not in found]
        text = f'{label}   ' + ('CACH=do   s=bo qua   q=dung' if not missing
                                else 'THIEU: ' + ', '.join(missing))
        cv2.putText(view, text, (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 0, 0), 4,
                    cv2.LINE_AA)
        cv2.putText(view, text, (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.62,
                    (0, 220, 0) if not missing else (0, 160, 255), 1, cv2.LINE_AA)
        cv2.imshow(title, view)
        key = cv2.waitKey(1) & 0xFF
        if key in (ord(' '), 13, ord('s'), ord('q'), 27):
            return {13: ' ', 27: 'q'}.get(key, chr(key))


def measure(cap, tracker, detector, objects, frames):
    """{tên lon: (x, y) mm thật} — trung vị qua `frames` khung."""
    seen = collections.defaultdict(list)
    tries = 0
    while min([len(v) for v in seen.values()] or [0]) < frames and tries < frames * 8:
        tries += 1
        ok, frame = cap.read()
        if not ok:
            continue
        tracker.update(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), detector)
        if not tracker.ready:
            continue
        roi = table_roi_mask(tracker.model, frame.shape)
        for color, det in detect_by_color(frame, COLOR_CLASSES, roi=roi).items():
            obj = objects.get(color)
            if obj is None:
                continue
            est = estimate_object(det, tracker.model, obj, frame.shape)
            if est.reliable:
                seen[obj.name].append(np.array(est.position[:2]) * 1000 * SCALE)
        if len(seen) == len(objects) and min(len(v) for v in seen.values()) >= frames:
            break
    return {n: np.median(np.array(v), axis=0) for n, v in seen.items() if len(v) >= 3}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--device', default='auto')
    ap.add_argument('--intrinsics', default=INTRINSICS)
    ap.add_argument('--frames', type=int, default=FRAMES)
    args = ap.parse_args()

    with open(args.intrinsics) as f:
        data = yaml.safe_load(f)
    K = np.array(data['camera']['K'], float)
    dist = np.array(data['camera']['dist'], float)
    device = usb_camera.resolve_device(args.device)
    mode = usb_camera.best_mjpg_mode(device)
    usb_camera.lock_manual(device, log=lambda _: None)
    cap = usb_camera.open_camera(device, mode[0], mode[1])
    usb_camera.warm_up(cap)
    tracker = PoseTracker(K, dist)
    detector = aruco_detector()
    objects = {o.color: o for o in REAL_OBJECTS}
    names = [o.name for o in REAL_OBJECTS]

    title = 'do sai so - CACH de do, s bo qua, q dung'
    cv2.namedWindow(title, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(title, 1100, 620)
    print('Dat moi lon vao VONG TRON mang ten no tren cua so, roi bam PHIM CACH.')
    print('  s = bo qua luot,  q = dung va xem ket qua\n')

    # Khóa tư thế camera trước, rồi mới chọn điểm đo theo đúng tư thế đó.
    print('Dang khoa tu the camera tu marker...')
    for _ in range(80):
        ok, frame = cap.read()
        if ok:
            tracker.update(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), detector)
        if tracker.ready and tracker.updates >= 10:
            break
    if not tracker.ready:
        raise SystemExit('Khong khoa duoc tu the — co thay du marker khong? Dung view_camera.py.')
    eye = tracker.last.position_real_mm()[:2]
    point_sets = choose_points(tracker.model, frame.shape, eye)
    cx, cy, cz = tracker.last.position_real_mm()
    print(f'camera: lui {-cx:.0f} mm, cao {cz:.0f} mm, chuc {tracker.last.tilt_deg():.1f}°')
    print('Diem do TU TINH theo tu the nay — danh dau bang but chi len ban:')
    for i, pts in enumerate(point_sets, 1):
        print(f'   bo {i}: ' + ', '.join(f'({x:+5.0f},{y:+5.0f})' for x, y in pts))

    rows = []
    rounds = [({names[i]: pts[(i + turn) % len(pts)] for i in range(len(names))})
              for pts in point_sets for turn in range(len(names))]
    stop = False
    for k, truth in enumerate(rounds, 1):
        if stop:
            break
        label = f'luot {k}/{len(rounds)}'
        print(f'--- {label}: ' + ', '.join(
            f'{n.split("_")[0]} ({truth[n][0]:+.0f},{truth[n][1]:+.0f})' for n in names))
        key = preview(cap, tracker, detector, objects, truth, title, label)
        if key == 'q':
            break
        if key == 's':
            print('   (bo qua)')
            continue
        got = measure(cap, tracker, detector, objects, args.frames)
        for n in names:
            if n not in got:
                print(f'   {n}: KHONG DO DUOC (bi che? ngoai vung xet?)')
                continue
            err = got[n] - np.array(truth[n])
            rows.append((n, truth[n], got[n], err))
            print(f'   {n:12s} do duoc ({got[n][0]:+6.0f},{got[n][1]:+6.0f})  '
                  f'lech ({err[0]:+5.1f},{err[1]:+5.1f}) = {np.linalg.norm(err):5.1f} mm that'
                  f'  -> {np.linalg.norm(err) / SCALE:4.2f} mm ao')
    cv2.destroyAllWindows()
    cap.release()

    if not rows:
        return 1
    print('\n== KET QUA')
    print('vat            so diem   TB (mm ao)   lon nhat   lech he thong X / Y (mm that)')
    for n in names:
        mine = [r for r in rows if r[0] == n]
        if not mine:
            continue
        e = np.array([r[3] for r in mine])
        d = np.linalg.norm(e, axis=1) / SCALE
        print(f'  {n:12s} {len(mine):5d}      {d.mean():6.2f}      {d.max():6.2f}      '
              f'{e[:, 0].mean():+6.1f} / {e[:, 1].mean():+5.1f}')
    allerr = np.linalg.norm(np.array([r[3] for r in rows]), axis=1) / SCALE
    print(f'\n  CHUNG: TB {allerr.mean():.2f} mm ao, lon nhat {allerr.max():.2f} mm '
          f'({len(rows)} phep do)')
    print('  (mo phong dat 1.13 mm; dung sai giac hut 12 mm)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
