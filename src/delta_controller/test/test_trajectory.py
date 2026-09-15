"""Test sinh quỹ đạo và động học thuận (FK)."""

import itertools
import math

from delta_controller.delta_kinematics import (
    DeltaGeometry,
    forward_kinematics,
    inverse_kinematics,
    UnreachableError,
)
from delta_controller.trajectory import (
    min_jerk,
    plan_path,
    safe_waypoints,
    sample_segment,
    segment_duration,
)
import pytest


# ---------------------------------------------------------------- FK

def test_fk_home():
    """Theta = 0 <=> platform tại (0, 0, -0.1405) (URDF làm tròn 4 chữ số)."""
    assert forward_kinematics(0.0, 0.0, 0.0) == pytest.approx((0.0, 0.0, -0.1405), abs=1e-6)


def test_fk_inverts_ik_over_workspace():
    """Vòng IK -> FK phải trả về đúng điểm ban đầu trên cả lưới không gian làm việc."""
    grid = itertools.product(
        [i / 100 for i in range(-10, 11, 2)],
        [i / 100 for i in range(-10, 11, 2)],
        [-i / 100 for i in range(11, 24)],
    )
    checked = 0
    for point in grid:
        try:
            thetas = inverse_kinematics(*point)
        except UnreachableError:
            continue
        assert forward_kinematics(*thetas) == pytest.approx(point, abs=1e-9)
        checked += 1
    assert checked > 500


def test_fk_rejects_non_intersecting_spheres():
    """Thanh chống re=0.05 ngắn hơn bán kính đường tròn qua 3 tâm (~0.09): không lắp ráp được."""
    short_forearm = DeltaGeometry(re=0.05)
    with pytest.raises(UnreachableError):
        forward_kinematics(0.0, 0.0, 0.0, short_forearm)


# ---------------------------------------------------------------- biên dạng bậc 5

def test_min_jerk_boundaries():
    assert min_jerk(0.0) == 0.0
    assert min_jerk(1.0) == pytest.approx(1.0)
    assert min_jerk(0.5) == pytest.approx(0.5)


def test_min_jerk_zero_velocity_at_ends_and_monotonic():
    h = 1e-6
    assert (min_jerk(h) - min_jerk(0.0)) / h == pytest.approx(0.0, abs=1e-4)
    assert (min_jerk(1.0) - min_jerk(1.0 - h)) / h == pytest.approx(0.0, abs=1e-4)
    values = [min_jerk(k / 100) for k in range(101)]
    assert all(b >= a for a, b in zip(values, values[1:]))


def test_peak_speed_matches_request():
    start, goal, speed, rate = (0.0, 0.0, -0.15), (0.06, 0.0, -0.15), 0.05, 1000.0
    assert segment_duration(start, goal, speed) == pytest.approx(1.875 * 0.06 / 0.05)
    points = [start] + sample_segment(start, goal, speed, rate)
    peak = max(math.dist(a, b) for a, b in zip(points, points[1:])) * rate
    assert peak == pytest.approx(speed, rel=1e-3)


# ---------------------------------------------------------------- đoạn thẳng

def test_segment_is_straight_and_ends_at_goal():
    start, goal = (0.0, 0.0, -0.14), (0.05, -0.03, -0.18)
    points = sample_segment(start, goal, 0.05, 50.0)
    assert points[-1] == pytest.approx(goal, abs=1e-12)
    direction = [b - a for a, b in zip(start, goal)]
    length = math.dist(start, goal)
    for p in points:
        offset = [c - a for a, c in zip(start, p)]
        along = sum(o * d for o, d in zip(offset, direction)) / length
        assert 0.0 <= along <= length + 1e-12
        perpendicular = math.sqrt(max(0.0, sum(o * o for o in offset) - along * along))
        assert perpendicular == pytest.approx(0.0, abs=1e-9)


def test_zero_length_segment_returns_goal():
    assert sample_segment((0, 0, -0.15), (0, 0, -0.15), 0.05, 50.0) == [(0, 0, -0.15)]


# ---------------------------------------------------------------- đường an toàn

SAFE_Z = -0.16


def test_safe_path_lifts_moves_and_descends():
    start, goal = (0.0, 0.0, -0.205), (0.06, 0.0, -0.185)
    assert safe_waypoints(start, goal, SAFE_Z) == [
        start, (0.0, 0.0, SAFE_Z), (0.06, 0.0, SAFE_Z), goal,
    ]


def test_safe_path_is_direct_when_both_above_safe_height():
    start, goal = (0.0, 0.0, -0.14), (0.05, 0.02, -0.15)
    assert safe_waypoints(start, goal, SAFE_Z) == [start, goal]


def test_safe_path_from_high_start_goes_down_diagonally_to_above_goal():
    start, goal = (0.0, 0.0, -0.14), (0.06, 0.0, -0.185)
    assert safe_waypoints(start, goal, SAFE_Z) == [start, (0.06, 0.0, SAFE_Z), goal]


@pytest.mark.parametrize('start, goal', [
    ((0.0, 0.0, -0.205), (0.06, 0.0, -0.185)),
    ((0.06, 0.0, -0.185), (-0.03, 0.052, -0.185)),
    ((0.0, 0.0, -0.14), (-0.03, -0.052, -0.19)),
])
def test_safe_plan_never_crosses_below_safe_height_between_xy(start, goal):
    """Chỉ được thấp hơn safe_z khi đang ở ngay trên điểm đầu hoặc điểm cuối (theo XY)."""
    plan = plan_path(safe_waypoints(start, goal, SAFE_Z), 0.05, 50.0)
    for (x, y, z), _ in plan:
        if z < SAFE_Z - 1e-9:
            above_start = math.hypot(x - start[0], y - start[1]) < 1e-9
            above_goal = math.hypot(x - goal[0], y - goal[1]) < 1e-9
            assert above_start or above_goal


def test_plan_contains_ik_for_every_point():
    plan = plan_path([(0.0, 0.0, -0.14), (0.03, 0.0, -0.17)], 0.05, 50.0)
    for xyz, thetas in plan:
        assert thetas == inverse_kinematics(*xyz)


def test_plan_rejects_path_leaving_workspace():
    """Hai đầu đều tới được nhưng đường thẳng đi qua vùng quá cao gần đế thì phải bị từ chối."""
    start, goal = (0.1, 0.0, -0.12), (-0.1, 0.0, -0.12)
    via = (0.0, 0.0, -0.09)  # z = -0.09 ở tâm là ngoài tầm với
    for p in (start, goal):
        inverse_kinematics(*p)
    with pytest.raises(UnreachableError):
        plan_path([start, via, goal], 0.05, 50.0)
