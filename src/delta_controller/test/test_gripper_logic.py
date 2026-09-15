"""Test logic chọn vật cho giác hút."""

from delta_controller.gripper_logic import (
    grasp_offsets,
    GraspTolerance,
    NoGraspableObject,
    ObjectState,
    PLATFORM_HALF_THICKNESS,
    select_graspable,
)
import pytest

# Vật trong delta_objects_world (hệ robot): cao 0.03, tâm z = -0.205, đỉnh z = -0.19.
OBJECTS = {
    'red_box': ObjectState((0.06, 0.0, -0.205), 0.015),
    'green_cylinder': ObjectState((-0.03, 0.052, -0.205), 0.015),
    'blue_sphere': ObjectState((-0.03, -0.052, -0.205), 0.015),
}
TOUCH_Z = -0.19 + PLATFORM_HALF_THICKNESS   # tool0 z khi mặt dưới platform chạm đỉnh vật


def test_offsets_when_touching_top():
    xy, gap = grasp_offsets((0.06, 0.0, TOUCH_Z), OBJECTS['red_box'])
    assert xy == pytest.approx(0.0)
    assert gap == pytest.approx(0.0, abs=1e-12)


@pytest.mark.parametrize('name', list(OBJECTS))
def test_selects_object_directly_below(name):
    cx, cy, _ = OBJECTS[name].center
    assert select_graspable((cx, cy, TOUCH_Z), OBJECTS) == name


def test_accepts_small_offsets_within_tolerance():
    tol = GraspTolerance()
    tool = (0.06 + 0.8 * tol.max_xy_offset, 0.0, TOUCH_Z + 0.8 * tol.max_gap)
    assert select_graspable(tool, OBJECTS, tol) == 'red_box'


def test_accepts_platform_slightly_sunk_into_object():
    """Ép xuống vật động làm platform lún vài mm (đã đo ở 6.1) — vẫn phải hút được."""
    assert select_graspable((0.06, 0.0, TOUCH_Z - 0.003), OBJECTS) == 'red_box'


def test_rejects_when_too_high():
    with pytest.raises(NoGraspableObject, match='red_box'):
        select_graspable((0.06, 0.0, TOUCH_Z + 0.02), OBJECTS)


def test_rejects_when_beside_object():
    with pytest.raises(NoGraspableObject):
        select_graspable((0.06, 0.03, TOUCH_Z), OBJECTS)


def test_hint_points_to_touch_height_above_nearest_object():
    with pytest.raises(NoGraspableObject) as info:
        select_graspable((-0.028, 0.05, -0.16), OBJECTS)
    assert 'green_cylinder' in str(info.value)
    assert f'{TOUCH_Z:.4f}' in str(info.value)


def test_uses_actual_object_position_after_it_was_pushed():
    pushed = dict(OBJECTS, red_box=ObjectState((0.072, 0.0, -0.205), 0.015))
    assert select_graspable((0.072, 0.0, TOUCH_Z), pushed) == 'red_box'
    with pytest.raises(NoGraspableObject):
        select_graspable((0.06 - 0.013, 0.0, TOUCH_Z), pushed)


def test_no_objects_known():
    with pytest.raises(NoGraspableObject):
        select_graspable((0.0, 0.0, -0.15), {})
