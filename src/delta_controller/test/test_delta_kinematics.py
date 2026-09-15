"""Test động học ngược robot delta — kiểm chứng bằng dữ liệu đã biết và ràng buộc hình học."""

import math

from delta_controller.delta_kinematics import (
    DEFAULT_GEOMETRY,
    elbow_position,
    inverse_kinematics,
    LEG_ANGLES,
    platform_joint_position,
    solve_leg,
    UnreachableError,
)
import pytest

G = DEFAULT_GEOMETRY
HOME = (0.0, 0.0, -0.1405)

# Các điểm trong không gian làm việc (m), rải đều theo X, Y, Z.
WORKSPACE_POINTS = [
    (0.0, 0.0, -0.12),
    (0.0, 0.0, -0.18),
    (0.03, 0.0, -0.15),
    (-0.03, 0.0, -0.15),
    (0.0, 0.03, -0.15),
    (0.02, -0.02, -0.16),
    (-0.025, 0.015, -0.13),
]


def _distance(p, q):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(p, q)))


def test_home_position_gives_zero_angles():
    """Home pose trong URDF: theta = 0 <=> platform tại (0, 0, -0.1405)."""
    # -0.1405 là giá trị làm tròn 4 chữ số từ URDF, nên sai số góc cỡ 1e-6 rad.
    for theta in inverse_kinematics(*HOME):
        assert theta == pytest.approx(0.0, abs=1e-5)


@pytest.mark.parametrize('point', [HOME] + WORKSPACE_POINTS)
def test_forearm_length_constraint(point):
    """Mỗi chân: khoảng cách khuỷu tay -> khớp platform phải đúng bằng re."""
    thetas = inverse_kinematics(*point)
    for theta, phi in zip(thetas, LEG_ANGLES):
        elbow = elbow_position(theta, phi)
        joint = platform_joint_position(*point, phi)
        assert _distance(elbow, joint) == pytest.approx(G.re, abs=1e-9)


@pytest.mark.parametrize('point', [HOME] + WORKSPACE_POINTS)
def test_solution_within_joint_limits(point):
    for theta in inverse_kinematics(*point):
        assert G.joint_lower <= theta <= G.joint_upper


@pytest.mark.parametrize('z', [-0.11, -0.14, -0.17, -0.20])
def test_point_on_z_axis_gives_equal_angles(z):
    """Đối xứng: platform nằm trên trục Z thì 3 góc bằng nhau."""
    t1, t2, t3 = inverse_kinematics(0.0, 0.0, z)
    assert t1 == pytest.approx(t2, abs=1e-12)
    assert t2 == pytest.approx(t3, abs=1e-12)


def test_lower_platform_needs_larger_angle():
    """Theta tăng -> cánh tay hạ xuống -> platform xuống thấp hơn."""
    upper = inverse_kinematics(0.0, 0.0, -0.13)[0]
    lower = inverse_kinematics(0.0, 0.0, -0.17)[0]
    assert lower > upper


def test_120_degree_rotation_permutes_legs():
    """Quay điểm 120° quanh Z thì góc các chân hoán vị vòng: chân 1 -> chân 2."""
    x, y, z = 0.02, -0.01, -0.15
    c, s = math.cos(LEG_ANGLES[1]), math.sin(LEG_ANGLES[1])
    t1, t2, t3 = inverse_kinematics(x, y, z)
    r1, r2, r3 = inverse_kinematics(x * c - y * s, x * s + y * c, z)
    assert (r2, r3, r1) == pytest.approx((t1, t2, t3), abs=1e-12)


def _elbow_side(theta, x, z):
    """Tích có hướng (vai->khớp platform) x (vai->khuỷu) ở mặt phẳng chân 1; > 0: khuỷu-ngoài."""
    ex, _, ez = elbow_position(theta, 0.0)
    px, _, pz = platform_joint_position(x, 0.0, z, 0.0)
    return (px - G.f) * ez - pz * (ex - G.f)


def test_home_is_elbow_out():
    assert _elbow_side(0.0, *HOME[::2]) > 0.0


def test_picks_elbow_out_when_both_roots_within_limits():
    """Tại (x=-0.09, z=-0.02) chân 1 có 2 nghiệm ~-1.020 và ~0.641, đều trong giới hạn khớp."""
    x, z = -0.09, -0.02
    theta = solve_leg(x, 0.0, z, 0.0)
    assert theta == pytest.approx(0.6406606753931479, abs=1e-9)
    assert _elbow_side(theta, x, z) > 0.0
    assert _elbow_side(-1.0202809482342774, x, z) < 0.0


@pytest.mark.parametrize('point', [
    (0.0, 0.0, -0.5),     # quá xa, vượt tổng chiều dài rf + re
    (0.3, 0.0, -0.1),     # quá xa theo phương ngang
    (0.0, 0.0, 0.05),     # phía trên đế
])
def test_unreachable_point_raises(point):
    with pytest.raises(UnreachableError):
        inverse_kinematics(*point)
