"""
Mô hình camera lỗ kim (pinhole) và hiệu chuẩn ngoại tham số bằng PnP (thuần Python + OpenCV).

Quy ước: điểm X_r trong hệ robot -> hệ camera quang học X_c = R·X_r + t
(z_c nhìn tới, x_c sang phải ảnh, y_c xuống dưới ảnh).
Chiếu: [u, v, 1]ᵀ ~ K·X_c (sau méo ống kính).

Hai bài toán:
  • Hiệu chuẩn (biết K): các điểm 3D biết trước (tâm marker ArUco trên bàn) + ảnh của chúng
    -> tìm R, t (bài toán Perspective-n-Point). Điểm đồng phẳng -> dùng IPPE rồi tinh chỉnh LM.
  • Đổi pixel -> tọa độ robot: tia nhìn qua pixel (u, v) giao với mặt phẳng z = z0 đã biết.
    Vật nằm trên bàn nên biết độ cao tâm vật; chọn sai mặt phẳng (vd. mặt bàn thay vì tâm vật)
    gây sai số hệ thống ~12 mm với camera nhìn xiên 32° (đã tính ở Bước 8.3).
"""

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class CameraModel:
    """Nội tham số K, hệ số méo dist, ngoại tham số robot -> camera (rvec, tvec)."""

    K: np.ndarray
    dist: np.ndarray
    rvec: np.ndarray
    tvec: np.ndarray

    @property
    def R(self):
        return cv2.Rodrigues(np.asarray(self.rvec, float))[0]

    def position(self):
        """Tâm quang học của camera trong hệ robot: C = -Rᵀ t."""
        return (-self.R.T @ np.asarray(self.tvec, float).reshape(3)).reshape(3)

    def optical_axis(self):
        """Hướng nhìn (trục z_c) biểu diễn trong hệ robot."""
        return self.R.T @ np.array([0.0, 0.0, 1.0])

    def project(self, points):
        """Chiếu các điểm Nx3 (hệ robot) lên ảnh -> Nx2 pixel."""
        pts = np.asarray(points, float).reshape(-1, 1, 3)
        uv, _ = cv2.projectPoints(pts, np.asarray(self.rvec, float),
                                  np.asarray(self.tvec, float), self.K, self.dist)
        return uv.reshape(-1, 2)

    def ray(self, u, v):
        """Tia nhìn qua pixel (u, v): trả về (gốc = tâm camera, hướng đơn vị) trong hệ robot."""
        norm = cv2.undistortPoints(np.array([[[u, v]]], float), self.K, self.dist).reshape(2)
        d_cam = np.array([norm[0], norm[1], 1.0])
        d = self.R.T @ d_cam
        return self.position(), d / np.linalg.norm(d)

    def pixel_to_plane(self, u, v, z):
        """Giao tia nhìn qua (u, v) với mặt phẳng nằm ngang z = z (hệ robot) -> (x, y, z)."""
        origin, d = self.ray(u, v)
        if abs(d[2]) < 1e-9:
            raise ValueError('Tia nhìn song song với mặt phẳng')
        s = (z - origin[2]) / d[2]
        if s <= 0:
            raise ValueError('Mặt phẳng nằm phía sau camera')
        return tuple(origin + s * d)

    def to_dict(self):
        return {
            'K': np.asarray(self.K, float).tolist(),
            'dist': np.asarray(self.dist, float).reshape(-1).tolist(),
            'rvec': np.asarray(self.rvec, float).reshape(-1).tolist(),
            'tvec': np.asarray(self.tvec, float).reshape(-1).tolist(),
        }

    @classmethod
    def from_dict(cls, data):
        return cls(K=np.array(data['K'], float), dist=np.array(data['dist'], float),
                   rvec=np.array(data['rvec'], float), tvec=np.array(data['tvec'], float))


@dataclass(frozen=True)
class PnPResult:
    model: CameraModel
    rms_px: float            # sai số chiếu lại trung bình bình phương (pixel)
    errors_px: tuple         # sai số chiếu lại từng điểm (pixel)


def estimate_pose(object_points, image_points, K, dist):
    """
    Giải PnP: tìm R, t từ ≥ 4 cặp điểm 3D (hệ robot) <-> 2D (pixel).

    Dùng SQPnP (nghiệm tối ưu toàn cục, chạy được với điểm đồng phẳng) rồi tinh chỉnh
    Levenberg–Marquardt tối thiểu hóa sai số chiếu lại.

    Không dùng IPPE dù điểm đồng phẳng: trên ảnh thật từ camera mô phỏng, IPPE (OpenCV 4.6) trả
    nghiệm sai hoàn toàn (sai số chiếu lại 434 px) trong khi SQPnP/ITERATIVE cho 0.29 px.
    """
    obj = np.asarray(object_points, float).reshape(-1, 3)
    img = np.asarray(image_points, float).reshape(-1, 2)
    if len(obj) < 4:
        raise ValueError(f'Can it nhat 4 diem, chi co {len(obj)}')
    K = np.asarray(K, float)
    dist = np.asarray(dist, float)
    ok, rvec, tvec = cv2.solvePnP(obj, img, K, dist, flags=cv2.SOLVEPNP_SQPNP)
    if not ok:
        raise ValueError('solvePnP khong hoi tu')
    rvec, tvec = cv2.solvePnPRefineLM(obj, img, K, dist, rvec, tvec)
    model = CameraModel(K=K, dist=dist, rvec=rvec.reshape(3), tvec=tvec.reshape(3))
    errors = np.linalg.norm(model.project(obj) - img, axis=1)
    return PnPResult(model=model, rms_px=float(np.sqrt(np.mean(errors ** 2))),
                     errors_px=tuple(float(e) for e in errors))


def marker_center(corners):
    """
    Tâm marker trên ảnh = giao điểm hai đường chéo của 4 góc.

    Phép chiếu phối cảnh bảo toàn giao điểm đường chéo, nên đây đúng là ảnh của tâm marker;
    trung bình 4 góc thì KHÔNG (bị lệch khi nhìn xiên).
    """
    p = np.asarray(corners, float).reshape(4, 2)
    a = np.cross(np.append(p[0], 1.0), np.append(p[2], 1.0))   # đường chéo 0-2
    b = np.cross(np.append(p[1], 1.0), np.append(p[3], 1.0))   # đường chéo 1-3
    x = np.cross(a, b)
    return (float(x[0] / x[2]), float(x[1] / x[2]))


def camera_model_from_gazebo_pose(K, xyz, rpy):
    """
    Mô hình camera từ pose link camera trong Gazebo (hệ robot) — CHỈ để đánh giá (ground truth).

    Gazebo: camera nhìn theo +X của link, ảnh sang phải = -Y link, xuống dưới = -Z link.
    """
    roll, pitch, yaw = rpy
    R_link = cv2.Rodrigues(np.array([0.0, 0.0, yaw]))[0] @ \
        cv2.Rodrigues(np.array([0.0, pitch, 0.0]))[0] @ \
        cv2.Rodrigues(np.array([roll, 0.0, 0.0]))[0]
    R_opt = np.stack([-R_link[:, 1], -R_link[:, 2], R_link[:, 0]])   # hàng = trục quang học
    t = -R_opt @ np.asarray(xyz, float)
    return CameraModel(K=np.asarray(K, float), dist=np.zeros(5),
                       rvec=cv2.Rodrigues(R_opt)[0].reshape(3), tvec=t)
