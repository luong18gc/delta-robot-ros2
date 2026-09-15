"""
Sinh quỹ đạo Descartes cho platform robot delta (thuần Python, không phụ thuộc ROS).

- Đoạn thẳng với biên dạng vận tốc bậc 5 (minimum-jerk): vị trí, vận tốc, gia tốc đều bằng 0
  ở hai đầu -> robot khởi động/dừng êm, PID bám tốt hơn so với nhảy thẳng tới đích.
- Đường đi an toàn: nâng lên độ cao an toàn -> đi ngang -> hạ xuống, để platform không quét
  trúng vật trên bàn.
"""

import math

from delta_controller.delta_kinematics import inverse_kinematics, UnreachableError

# Hệ số vận tốc đỉnh của biên dạng bậc 5: v_max = 1.875 * L / T
_QUINTIC_PEAK = 1.875
_POINT_TOL = 1e-6


def min_jerk(tau):
    """Tỉ lệ quãng đường s(tau) = 10 tau^3 - 15 tau^4 + 6 tau^5, với tau trong [0, 1]."""
    tau = min(max(tau, 0.0), 1.0)
    return tau ** 3 * (10.0 - 15.0 * tau + 6.0 * tau * tau)


def segment_duration(start, goal, max_speed):
    """Thời gian [s] để đi hết đoạn thẳng sao cho vận tốc đỉnh đúng bằng max_speed [m/s]."""
    if max_speed <= 0.0:
        raise ValueError('max_speed phai > 0')
    return _QUINTIC_PEAK * math.dist(start, goal) / max_speed


def sample_segment(start, goal, max_speed, rate_hz):
    """
    Lấy mẫu đoạn thẳng start -> goal theo thời gian, tần số rate_hz.

    Trả về danh sách điểm, KHÔNG gồm start, luôn kết thúc đúng tại goal.
    """
    duration = segment_duration(start, goal, max_speed)
    steps = max(1, math.ceil(duration * rate_hz))
    points = []
    for k in range(1, steps + 1):
        s = min_jerk(k / steps)
        points.append(tuple(a + (b - a) * s for a, b in zip(start, goal)))
    return points


def safe_waypoints(start, goal, safe_z):
    """
    Các điểm mốc nâng -> ngang -> hạ, sao cho cả đường đi không xuống thấp hơn safe_z.

    Nếu start và goal đều cao hơn safe_z thì đi thẳng (đoạn thẳng giữa hai điểm trên mặt
    phẳng z = safe_z cũng nằm trên mặt phẳng đó). Z hướng lên nên "cao hơn" nghĩa là z lớn hơn.
    """
    sx, sy, sz = start
    gx, gy, gz = goal
    points = [
        tuple(start),
        (sx, sy, max(sz, safe_z)),
        (gx, gy, max(gz, safe_z)),
        tuple(goal),
    ]
    waypoints = [points[0]]
    for p in points[1:]:
        if math.dist(p, waypoints[-1]) > _POINT_TOL:
            waypoints.append(p)
    return waypoints


def plan_path(waypoints, max_speed, rate_hz):
    """
    Nối các điểm mốc bằng đoạn thẳng, trả về danh sách (xyz, thetas) đã giải IK sẵn.

    Giải IK cho TOÀN BỘ quỹ đạo trước khi chạy: nếu một điểm giữa đường ngoài tầm với thì
    ném UnreachableError ngay, robot chưa di chuyển.
    """
    plan = []
    for start, goal in zip(waypoints, waypoints[1:]):
        for p in sample_segment(start, goal, max_speed, rate_hz):
            try:
                plan.append((p, inverse_kinematics(*p)))
            except UnreachableError as e:
                raise UnreachableError(
                    f'Quy dao di qua diem ngoai tam voi ({p[0]:.4f}, {p[1]:.4f}, {p[2]:.4f}): {e}'
                ) from e
    return plan
