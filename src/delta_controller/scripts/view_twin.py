#!/usr/bin/env python3
"""
Xem TỌA ĐỘ Ở CẢ HAI THẾ GIỚI cùng lúc: bàn thật và cảnh mô phỏng (Bước 10b).

    python3 src/delta_controller/scripts/view_twin.py

Chạy kèm `ros2 launch delta_controller digital_twin.launch.py`. Cửa sổ gồm hai phần: ảnh camera
thật đã chú thích ở trên, và bảng đối chiếu ở dưới. Dịch một lon trên bàn thì **cả ba cột cùng
đổi**, nên nhìn là thấy ngay chuỗi thật -> ảo đang hoạt động.

Ba cột của bảng, cùng một vật nhìn từ ba chỗ khác nhau:

- **BÀN THẬT** — camera đo được, tính bằng milimét trên mặt bàn.
- **CẢNH ẢO** — cũng là số đó chia cho `scene.SCALE`, tức tọa độ mà khối điều khiển thật sự dùng.
- **GAZEBO** — vị trí lon ảo ĐANG nằm trong mô phỏng, đọc từ odometry. Đây là đối chứng độc lập:
  nó cho biết lệnh ghi vào mô phỏng đã tới nơi chưa.

Cột cuối là khoảng cách giữa CẢNH ẢO và GAZEBO. Số này bình thường dưới 2 mm thật; nó chỉ lớn khi
bản sao số đang CỐ Ý không ghi — lon bị cờ tin cậy nghi ngờ, hoặc cú nhảy chưa đủ khung xác nhận.
Nói cách khác, cột này không phải sai số của phép đo mà là **chỗ nhìn thấy các lớp lọc làm việc**.
"""

import argparse
import sys
import threading

import _workspace  # noqa: F401
import cv2
from cv_bridge import CvBridge
from delta_controller.color_detector import COLOR_CLASSES
from delta_controller.scene import OBJECTS, SCALE
from nav_msgs.msg import Odometry
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection3DArray

FONT = cv2.FONT_HERSHEY_SIMPLEX
ROW_H = 34
HEAD_H = 30
PAD = 10


class TwinView(Node):
    """Gom ảnh camera, ước lượng của camera và trạng thái Gazebo vào một chỗ."""

    def __init__(self):
        super().__init__('delta_twin_view')
        self._bridge = CvBridge()
        self._lock = threading.Lock()
        self._frame = None
        self._camera = {}        # tên vật -> (x, y) mét ảo, camera đo được
        self._score = {}
        self._gazebo = {}        # tên vật -> (x, y) mét ảo, vị trí trong mô phỏng
        self.create_subscription(Image, '/vision/debug_image', self._on_image, 1)
        self.create_subscription(Detection3DArray, '/vision/objects', self._on_objects, 10)
        for o in OBJECTS:
            self.create_subscription(
                Odometry, f'/objects/{o.name}/odometry', self._make_odom(o.name), 10)

    def _on_image(self, msg):
        frame = self._bridge.imgmsg_to_cv2(msg, 'bgr8')
        with self._lock:
            self._frame = frame

    def _on_objects(self, msg):
        with self._lock:
            self._camera.clear()
            self._score.clear()
            for d in msg.detections:
                p = d.bbox.center.position
                self._camera[d.id] = (p.x, p.y)
                self._score[d.id] = d.results[0].hypothesis.score if d.results else 0.0

    def _make_odom(self, name):
        def cb(msg):
            p = msg.pose.pose.position
            with self._lock:
                self._gazebo[name] = (p.x, p.y)
        return cb

    def snapshot(self):
        with self._lock:
            return (None if self._frame is None else self._frame.copy(),
                    dict(self._camera), dict(self._score), dict(self._gazebo))


def _text(img, s, xy, color=(235, 235, 235), scale=0.55, bold=1):
    cv2.putText(img, s, xy, FONT, scale, (0, 0, 0), bold + 3, cv2.LINE_AA)
    cv2.putText(img, s, xy, FONT, scale, color, bold, cv2.LINE_AA)


def panel(width, camera, score, gazebo):
    """Bảng đối chiếu tọa độ ba cột."""
    img = np.full((HEAD_H + ROW_H * len(OBJECTS) + 2 * PAD, width, 3), 28, np.uint8)
    cols = (PAD + 4, int(0.22 * width), int(0.45 * width), int(0.68 * width), int(0.87 * width))
    _text(img, 'VAT', (cols[0], PAD + 20), (150, 150, 150), 0.5)
    _text(img, 'BAN THAT (mm)', (cols[1], PAD + 20), (150, 200, 255), 0.5)
    _text(img, 'CANH AO (mm)', (cols[2], PAD + 20), (150, 255, 200), 0.5)
    _text(img, 'GAZEBO (mm ao)', (cols[3], PAD + 20), (255, 200, 150), 0.5)
    _text(img, 'LECH', (cols[4], PAD + 20), (150, 150, 150), 0.5)
    cv2.line(img, (PAD, PAD + 26), (width - PAD, PAD + 26), (70, 70, 70), 1)

    for i, o in enumerate(OBJECTS):
        y = PAD + HEAD_H + ROW_H * i + 22
        bgr = COLOR_CLASSES[o.color].bgr
        cv2.circle(img, (cols[0] + 7, y - 6), 7, bgr, -1)
        _text(img, o.name.split('_')[0], (cols[0] + 22, y), bgr, 0.58)

        cam = camera.get(o.name)
        gz = gazebo.get(o.name)
        trusted = score.get(o.name, 0.0) > 0.0
        if cam is None:
            _text(img, 'khong thay', (cols[1], y), (120, 120, 120), 0.55)
        else:
            tone = (235, 235, 235) if trusted else (120, 170, 255)
            _text(img, f'{cam[0] * 1000 * SCALE:+7.1f}  {cam[1] * 1000 * SCALE:+7.1f}',
                  (cols[1], y), tone, 0.55)
            _text(img, f'{cam[0] * 1000:+7.1f}  {cam[1] * 1000:+7.1f}', (cols[2], y), tone, 0.55)
            if not trusted:
                _text(img, 'KHONG TIN', (cols[2] + 150, y), (120, 170, 255), 0.45)
        if gz is None:
            _text(img, '--', (cols[3], y), (120, 120, 120), 0.55)
        else:
            _text(img, f'{gz[0] * 1000:+7.1f}  {gz[1] * 1000:+7.1f}', (cols[3], y),
                  (235, 235, 235), 0.55)
        if cam is not None and gz is not None:
            d = 1000.0 * SCALE * float(np.hypot(cam[0] - gz[0], cam[1] - gz[1]))
            _text(img, f'{d:5.1f} mm', (cols[4], y),
                  (235, 235, 235) if d < 10 else (120, 170, 255), 0.55)
    return img


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--width', type=int, default=1100, help='be rong cua so')
    args = ap.parse_args()

    rclpy.init()
    node = TwinView()
    spin = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin.start()

    title = 'toa do hai the gioi - q de thoat'
    cv2.namedWindow(title, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(title, args.width, int(args.width * 0.72))
    print('Dich mot lon tren ban -> ca ba cot cung doi. Bam q de thoat.')
    try:
        while True:
            frame, camera, score, gazebo = node.snapshot()
            if frame is None:
                blank = np.full((200, args.width, 3), 28, np.uint8)
                _text(blank, 'Dang cho /vision/debug_image ...', (PAD + 10, 110),
                      (150, 150, 150), 0.7)
                view = np.vstack([blank, panel(args.width, camera, score, gazebo)])
            else:
                h = int(frame.shape[0] * args.width / frame.shape[1])
                view = np.vstack([cv2.resize(frame, (args.width, h)),
                                  panel(args.width, camera, score, gazebo)])
            cv2.imshow(title, view)
            if cv2.waitKey(50) & 0xFF in (ord('q'), 27):
                break
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.try_shutdown()
    return 0


if __name__ == '__main__':
    sys.exit(main())
