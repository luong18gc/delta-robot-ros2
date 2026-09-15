"""
Động học ngược (IK) closed-form cho robot delta quay 3-DOF.

Module thuần Python, không phụ thuộc ROS, để test được bằng pytest mà không cần Gazebo.

Hệ trục: gốc O tại tâm base_link, X hướng ra chân 1, Z hướng lên (platform có z < 0).
theta_i = 0 <=> cánh tay trên nằm ngang hướng ra ngoài; theta_i tăng -> cánh tay hạ xuống.
"""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class DeltaGeometry:
    """Thông số hình học (mét), trích từ 3dof_delta.urdf.xacro."""

    f: float = 0.0417     # bán kính đế (origin joint ChainN_1)
    e: float = 0.0276     # bán kính platform (origin joint ChainN_cl_A)
    rf: float = 0.0758    # chiều dài cánh tay trên (origin joint ChainN_top_A)
    re: float = 0.1668    # chiều dài thanh chống (origin ChainN_tip_joint)
    joint_lower: float = -1.0297442586766543
    joint_upper: float = 1.4311699866353502


DEFAULT_GEOMETRY = DeltaGeometry()

# Góc pha của 3 chân: 0°, 120°, 240°
LEG_ANGLES = (0.0, 2.0 * math.pi / 3.0, 4.0 * math.pi / 3.0)

_EPS = 1e-9


class UnreachableError(ValueError):
    """Điểm (x, y, z) nằm ngoài không gian làm việc hoặc cần góc khớp vượt giới hạn."""


def _to_leg_frame(x, y, z, phi):
    """Quay điểm (x, y, z) về hệ tọa độ cục bộ của chân có góc pha phi."""
    c, s = math.cos(phi), math.sin(phi)
    return x * c + y * s, -x * s + y * c, z


def _in_limits(theta, geometry):
    return geometry.joint_lower - _EPS <= theta <= geometry.joint_upper + _EPS


def solve_leg(x, y, z, phi, geometry=DEFAULT_GEOMETRY):
    """
    Giải góc khớp chủ động của một chân.

    Ràng buộc: |khuỷu tay - khớp platform| = re, dẫn tới
        A*cos(theta) + B*sin(theta) + C = 0
    giải bằng phép thế Weierstrass t = tan(theta/2):
        (C - A)*t^2 + 2*B*t + (A + C) = 0
    """
    g = geometry
    xi, yi, zi = _to_leg_frame(x, y, z, phi)

    a = (xi + g.e) - g.f
    k = a * a + yi * yi + zi * zi + g.rf * g.rf - g.re * g.re

    A = -2.0 * g.rf * a
    B = 2.0 * g.rf * zi
    C = k

    quad = C - A
    if abs(quad) < _EPS:
        # Suy biến thành phương trình bậc nhất 2*B*t + (A + C) = 0.
        if abs(B) < _EPS:
            raise UnreachableError(f'Phương trình suy biến tại chân phi={phi:.3f}')
        roots_t = [-(A + C) / (2.0 * B)]
    else:
        disc = A * A + B * B - C * C
        if disc < 0.0:
            raise UnreachableError(
                f'Điểm ({x:.4f}, {y:.4f}, {z:.4f}) ngoài tầm với của chân phi={phi:.3f}')
        sq = math.sqrt(disc)
        roots_t = [(-B + sq) / quad, (-B - sq) / quad]

    # Chọn nhánh "khuỷu ra ngoài" (liên tục với home pose) thay vì "nghiệm nằm trong giới hạn":
    # xét riêng một chân vẫn có điểm mà cả 2 nghiệm đều trong giới hạn (vd. x=-0.09, z=-0.02),
    # dù quét lưới cho thấy các điểm đó luôn nằm ngoài tầm với của chân khác.
    # Khuỷu nằm phía ngoài đường nối vai -> khớp platform <=> đạo hàm của ràng buộc
    #     d/dtheta (A*cos + B*sin) = -A*sin(theta) + B*cos(theta) <= 0
    # (tại home: theta=0 -> B = 2*rf*z < 0 ✓). Hai nghiệm luôn có dấu đạo hàm ngược nhau.
    thetas = [2.0 * math.atan(t) for t in roots_t]
    theta = min(thetas, key=lambda th: -A * math.sin(th) + B * math.cos(th))
    # Trường hợp bậc nhất: nghiệm khuỷu-ngoài có thể là t -> vô cùng (theta = pi).
    elbow_out = -A * math.sin(theta) + B * math.cos(theta) <= _EPS

    if not elbow_out or not _in_limits(theta, g):
        raise UnreachableError(
            f'Điểm ({x:.4f}, {y:.4f}, {z:.4f}) cần góc {theta:.4f} '
            f'vượt giới hạn khớp [{g.joint_lower:.4f}, {g.joint_upper:.4f}] '
            f'của chân phi={phi:.3f}')
    return theta


def inverse_kinematics(x, y, z, geometry=DEFAULT_GEOMETRY):
    """Tính (theta1, theta2, theta3) [rad] để tâm platform tới (x, y, z) [m]."""
    return tuple(solve_leg(x, y, z, phi, geometry) for phi in LEG_ANGLES)


def forward_kinematics(theta1, theta2, theta3, geometry=DEFAULT_GEOMETRY):
    """
    Tính tâm platform (x, y, z) [m] từ 3 góc khớp [rad] — giao của 3 mặt cầu.

    Ràng buộc chân i: |P + e*u_i - E_i| = re, với E_i là khuỷu tay,
    u_i = (cos phi_i, sin phi_i, 0).
    Đặt C_i = E_i - e*u_i thì |P - C_i| = re: P là giao 3 mặt cầu tâm C_i, cùng bán kính re.
    Hai nghiệm đối xứng qua mặt phẳng chứa C_1, C_2, C_3; chọn nghiệm nằm DƯỚI (z nhỏ hơn).
    """
    g = geometry
    centers = []
    for theta, phi in zip((theta1, theta2, theta3), LEG_ANGLES):
        ex, ey, ez = elbow_position(theta, phi, g)
        centers.append((ex - g.e * math.cos(phi), ey - g.e * math.sin(phi), ez))
    c1, c2, c3 = centers

    # Hệ trục phụ (u, v, w) gốc C_1: u hướng C_1->C_2, v trong mặt phẳng 3 tâm, w pháp tuyến.
    d12 = _sub(c2, c1)
    d = _norm(d12)
    u = _scale(d12, 1.0 / d)
    d13 = _sub(c3, c1)
    i = _dot(u, d13)
    v_raw = _sub(d13, _scale(u, i))
    j = _norm(v_raw)
    if d < _EPS or j < _EPS:
        raise UnreachableError('Ba tâm mặt cầu thẳng hàng — cấu hình suy biến')
    v = _scale(v_raw, 1.0 / j)
    w = _cross(u, v)

    # Bán kính bằng nhau nên các số hạng re^2 triệt tiêu.
    pu = d / 2.0
    pv = (i * i + j * j - 2.0 * i * pu) / (2.0 * j)
    pw2 = g.re * g.re - pu * pu - pv * pv
    if pw2 < 0.0:
        raise UnreachableError('Góc khớp không lắp ráp được (3 mặt cầu không giao nhau)')
    pw = math.sqrt(pw2)

    base = _add(c1, _add(_scale(u, pu), _scale(v, pv)))
    p_plus = _add(base, _scale(w, pw))
    p_minus = _add(base, _scale(w, -pw))
    return min(p_plus, p_minus, key=lambda p: p[2])


def _add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _scale(a, k):
    return tuple(x * k for x in a)


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _norm(a):
    return math.sqrt(_dot(a, a))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def elbow_position(theta, phi, geometry=DEFAULT_GEOMETRY):
    """Tọa độ khuỷu tay (đầu cánh tay trên) của chân phi, trong hệ base."""
    g = geometry
    r = g.f + g.rf * math.cos(theta)
    return r * math.cos(phi), r * math.sin(phi), -g.rf * math.sin(theta)


def platform_joint_position(x, y, z, phi, geometry=DEFAULT_GEOMETRY):
    """Tọa độ điểm nối thanh chống trên platform của chân phi, trong hệ base."""
    return x + geometry.e * math.cos(phi), y + geometry.e * math.sin(phi), z
