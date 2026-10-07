#!/usr/bin/env python3
"""
Đo SAI SỐ THẬT của khối thị giác camera thật, so với vị trí biết trước (Bước 10a).

    python3 src/delta_controller/scripts/measure_real_accuracy.py

Cửa sổ camera VẼ SẴN vòng tròn vào đúng chỗ phải đặt từng lon (chiếu điểm đích qua mô hình camera),
nên không cần căn bằng mắt: đặt lon vào vòng tròn mang tên nó, bấm PHÍM CÁCH, script chụp nhiều
khung, lấy TRUNG VỊ rồi so với vị trí đúng. Cuối cùng in bảng sai số để đối chiếu với 1.13 mm của
mô phỏng.

Ba lon đổi chỗ cho nhau qua các lượt, nên mỗi lon được đo ở mọi điểm mà chỉ cần ít lần đặt.

⚠️ ĐẶT TÂM ĐÁY LON TRÙNG DẤU, không phải mép lon — thứ hệ thống ước lượng là TÂM lon. Đặt mép
vào dấu thì mọi phép đo lệch thêm đúng một bán kính lon (28.75 mm thật ≈ 9.6 mm ảo), và lệch đó
trông y hệt một sai số hệ thống của khối thị giác. Nhìn từ trên xuống, mép đáy lon phải bao quanh
dấu đều nhau.

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
from delta_controller.vision_estimation import estimate_object, fit_top_edge
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


def preview(cap, tracker, detector, objects, truth, title, label, reference):
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
        found = detect_by_color(frame, COLOR_CLASSES, roi=roi, reference=reference)
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
        text = f'{label}  TAM DAY lon trung dau   ' + (
            'CACH=do  s=bo qua  q=dung' if not missing else 'THIEU: ' + ', '.join(missing))
        cv2.putText(view, text, (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 0, 0), 4,
                    cv2.LINE_AA)
        cv2.putText(view, text, (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.62,
                    (0, 220, 0) if not missing else (0, 160, 255), 1, cv2.LINE_AA)
        cv2.imshow(title, view)
        key = cv2.waitKey(1) & 0xFF
        if key in (ord(' '), 13, ord('s'), ord('q'), 27):
            return {13: ' ', 27: 'q'}.get(key, chr(key))


def both_fits(det, camera, obj, shape):
    """
    ((x, y) khớp MÉP ĐÁY, (x, y) khớp MÉP TRÊN) — cùng một lần nhận dạng, mm thật.

    Đo cả hai để số liệu tự chọn: mặt bàn phản chiếu lon, và ảnh phản chiếu chỉ nằm PHÍA DƯỚI
    chân lon, nên nó làm phình mép đáy mà không chạm tới mép trên. Mép trên của hình bóng là vành
    miệng lon — đặc trưng hình học sạch. (Kết luận cũ "mép trên không dùng được" là cho mặt nạ
    MÀU, nơi mép trên là mép vành màu bị nắp bạc làm nhòe — không áp dụng cho hình bóng.)
    """
    est = estimate_object(det, camera, obj, shape)
    bottom = np.array(est.position[:2]) * 1000 * SCALE
    u, _ = det.centroid
    bx, by, bw, bh = det.bbox
    z = TABLE_Z + obj.half_height
    # Xuất phát từ ƯỚC LƯỢNG MÉP ĐÁY, không phải từ tâm khối: tâm khối bị ảnh phản chiếu kéo xuống
    # nên điểm xuất phát lệch, và Newton phân kỳ. Đo 2026-10-07: với điểm xuất phát tâm khối, mọi
    # lon đặt tại (-70,-160) đều cho CÙNG một đáp án sai (+88.7, -28.7) bất kể là lon nào — dấu
    # hiệu của bộ giải rơi vào nghiệm lạ, không phải của phép đo.
    start = tuple(est.position[:2])
    fit = fit_top_edge(camera, obj, u, by - 0.5, z, start)
    top = np.array(fit) * 1000 * SCALE if fit is not None else None
    return est, bottom, top


def capture_reference(cap, tracker, detector, title, frames=20):
    """
    Chụp ảnh MẶT BÀN TRỐNG làm chuẩn để trừ nền; trả về ảnh, hoặc None nếu người dùng bỏ qua.

    Lấy TRUNG VỊ nhiều khung để nhiễu cảm biến không lọt vào chính cái chuẩn.
    """
    print('\nDON HET LON KHOI BAN (de nguyen marker), roi bam PHIM CACH de chup anh nen.')
    print('  r = bo qua, dung cach lay nguong cu')
    while True:
        ok, frame = cap.read()
        if not ok:
            continue
        tracker.update(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), detector)
        view = frame.copy()
        text = 'DON HET LON KHOI BAN roi bam CACH   (r = bo qua)'
        cv2.putText(view, text, (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 0, 0), 4,
                    cv2.LINE_AA)
        cv2.putText(view, text, (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 220, 220), 1,
                    cv2.LINE_AA)
        cv2.imshow(title, view)
        key = cv2.waitKey(1) & 0xFF
        if key in (ord('r'), ord('q'), 27):
            print('  -> bo qua anh nen.')
            return None
        if key in (ord(' '), 13):
            break
    shots = []
    while len(shots) < frames:
        ok, frame = cap.read()
        if ok:
            shots.append(frame)
    ref = np.median(np.array(shots), axis=0).astype(np.uint8)
    print(f'  -> da chup anh nen ({len(shots)} khung). Dat lon tro lai ban.')
    return ref


def measure(cap, tracker, detector, objects, frames, reference):
    """{tên lon: ((x,y) mép đáy, (x,y) mép trên)} — trung vị qua `frames` khung."""
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
        for color, det in detect_by_color(frame, COLOR_CLASSES, roi=roi,
                                          reference=reference).items():
            obj = objects.get(color)
            if obj is None:
                continue
            est, bottom, top = both_fits(det, tracker.model, obj, frame.shape)
            if est.reliable and top is not None:
                seen[obj.name].append((bottom, top))
        if len(seen) == len(objects) and min(len(v) for v in seen.values()) >= frames:
            break
    return {n: (np.median([b for b, _ in v], axis=0), np.median([t for _, t in v], axis=0))
            for n, v in seen.items() if len(v) >= 3}


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

    reference = capture_reference(cap, tracker, detector, title)

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
        key = preview(cap, tracker, detector, objects, truth, title, label, reference)
        if key == 'q':
            break
        if key == 's':
            print('   (bo qua)')
            continue
        got = measure(cap, tracker, detector, objects, args.frames, reference)
        for n in names:
            if n not in got:
                print(f'   {n}: KHONG DO DUOC (bi che? ngoai vung xet?)')
                continue
            bottom, top = got[n]
            eb = bottom - np.array(truth[n])
            et = top - np.array(truth[n])
            rows.append((n, truth[n], eb, et))
            print(f'   {n:12s} day {np.linalg.norm(eb):5.1f} mm '
                  f'({eb[0]:+5.1f},{eb[1]:+5.1f})  |  tren {np.linalg.norm(et):5.1f} mm '
                  f'({et[0]:+5.1f},{et[1]:+5.1f})')
    cv2.destroyAllWindows()
    cap.release()

    if not rows:
        return 1
    print('\n== KET QUA  (mm AO; mo phong dat 1.13 mm, dung sai giac hut 12 mm)')
    for idx, label in ((2, 'KHOP MEP DAY'), (3, 'KHOP MEP TREN')):
        print(f'\n  {label}')
        print('    vat          so diem   TB     lon nhat   lech he thong X / Y (mm that)')
        for n in names:
            mine = [r for r in rows if r[0] == n]
            if not mine:
                continue
            e = np.array([r[idx] for r in mine])
            d = np.linalg.norm(e, axis=1) / SCALE
            print(f'    {n:12s} {len(mine):5d}   {d.mean():6.2f}   {d.max():6.2f}      '
                  f'{e[:, 0].mean():+6.1f} / {e[:, 1].mean():+5.1f}')
        allerr = np.linalg.norm(np.array([r[idx] for r in rows]), axis=1) / SCALE
        print(f'    CHUNG: TB {allerr.mean():.2f} mm ao, lon nhat {allerr.max():.2f} mm '
              f'({len(rows)} phep do)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
