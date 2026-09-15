"""Test lập kế hoạch lệnh cấp cao."""

from delta_controller.delta_kinematics import inverse_kinematics
from delta_controller.gripper_logic import (
    ObjectState,
    PLATFORM_HALF_THICKNESS,
    select_graspable,
)
from delta_controller.scene import BIN_FLOOR_Z, BIN_SLOTS
from delta_controller.task_planner import (
    check_reachable,
    first_free_slot,
    Grip,
    hover_point,
    is_lifted,
    locate,
    Move,
    plan_goto,
    plan_pick,
    plan_pick_place,
    plan_place,
    plan_sort,
    Release,
    release_point,
    resolve_object,
    resolve_slot,
    TaskError,
    touch_point,
)
import pytest

LIFT_Z = -0.14
RETREAT_Z = -0.16
TABLE_Z = -0.22

ON_TABLE = {
    'red_box': ObjectState((0.06, 0.0, -0.205), 0.015),
    'green_cylinder': ObjectState((-0.03, 0.052, -0.205), 0.015),
    'blue_sphere': ObjectState((-0.03, -0.052, -0.205), 0.015),
}


def in_slot(slot):
    x, y = BIN_SLOTS[slot]
    return ObjectState((x, y, BIN_FLOOR_Z + 0.015), 0.015)


# ---------------------------------------------------------------- tra cứu

@pytest.mark.parametrize('text, name', [
    ('red_box', 'red_box'), ('RED', 'red_box'), ('do', 'red_box'),
    ('xanhla', 'green_cylinder'), ('tru', 'green_cylinder'),
    ('cau', 'blue_sphere'), (' Blue_Sphere ', 'blue_sphere'),
])
def test_resolve_object(text, name):
    assert resolve_object(text) == name


def test_resolve_unknown_object_lists_choices():
    with pytest.raises(TaskError, match='red_box'):
        resolve_object('vang')


def test_resolve_slot():
    assert resolve_slot('b') == 'B'
    with pytest.raises(TaskError):
        resolve_slot('D')


# ---------------------------------------------------------------- điểm hình học

def test_touch_point_matches_measured_grip_height():
    """6.3 đã kiểm chứng trên Gazebo: chạm đỉnh vật cao 3 cm khi tool0 z = -0.187."""
    assert touch_point(ON_TABLE['red_box']) == pytest.approx((0.06, 0.0, -0.187))


def test_touch_point_is_accepted_by_gripper_logic():
    for name, obj in ON_TABLE.items():
        assert select_graspable(touch_point(obj), ON_TABLE) == name


def test_hover_point_is_above_touch_point():
    assert hover_point(ON_TABLE['red_box'])[2] == pytest.approx(-0.187 + 0.02)


def test_release_point_matches_verified_slot_height():
    """6.3: thả tại tool0 z = -0.179 thì đáy vật cách đáy khay ~5 mm."""
    for slot, (x, y) in BIN_SLOTS.items():
        assert release_point(slot, 0.015) == pytest.approx((x, y, -0.179))


# ---------------------------------------------------------------- trạng thái cảnh

def test_locate():
    assert locate('red_box', ON_TABLE['red_box'], '') == 'tren ban'
    assert locate('red_box', in_slot('B'), '') == 'o B'
    assert locate('red_box', ON_TABLE['red_box'], 'red_box') == 'dang giu'


def test_first_free_slot_skips_occupied():
    objects = dict(ON_TABLE, red_box=in_slot('A'))
    assert first_free_slot(objects, '') == 'B'


def test_full_bin_raises():
    objects = {'red_box': in_slot('A'), 'green_cylinder': in_slot('B'),
               'blue_sphere': in_slot('C')}
    with pytest.raises(TaskError, match='day'):
        first_free_slot(objects, '')


def test_is_lifted():
    assert not is_lifted(ON_TABLE['red_box'], TABLE_Z)
    lifted = ObjectState((0.06, 0.0, -0.205 + 0.047), 0.015)
    assert is_lifted(lifted, TABLE_Z)


# ---------------------------------------------------------------- kế hoạch

def test_goto_hovers_above_object():
    [move] = plan_goto('green_cylinder', ON_TABLE)
    assert move.safe and move.goal == pytest.approx(hover_point(ON_TABLE['green_cylinder']))


def test_pick_sequence():
    actions = plan_pick('red_box', ON_TABLE, '', LIFT_Z)
    assert [type(a) for a in actions] == [Move, Grip, Move]
    down, grip, up = actions
    assert down.safe and down.goal == pytest.approx((0.06, 0.0, -0.187))
    assert grip.expected == 'red_box'
    assert not up.safe and up.goal == pytest.approx((0.06, 0.0, LIFT_Z))


def test_pick_uses_actual_pushed_position():
    pushed = dict(ON_TABLE, red_box=ObjectState((0.072, 0.004, -0.205), 0.015))
    assert plan_pick('red_box', pushed, '', LIFT_Z)[0].goal[:2] == pytest.approx((0.072, 0.004))


def test_pick_while_holding_is_rejected():
    with pytest.raises(TaskError, match='Dang giu'):
        plan_pick('red_box', ON_TABLE, 'blue_sphere', LIFT_Z)


def test_pick_unknown_position_is_rejected():
    with pytest.raises(TaskError, match='Chua nhan'):
        plan_pick('red_box', {}, '', LIFT_Z)


def test_place_sequence():
    actions = plan_place('red_box', 'C', ON_TABLE, RETREAT_Z)
    assert [type(a) for a in actions] == [Move, Release, Move]
    assert actions[0].safe and actions[0].goal == pytest.approx(release_point('C', 0.015))
    assert not actions[2].safe and actions[2].goal[2] == pytest.approx(RETREAT_Z)


def test_place_rejects_occupied_slot_and_empty_gripper():
    objects = dict(ON_TABLE, green_cylinder=in_slot('A'))
    with pytest.raises(TaskError, match='da co vat'):
        plan_place('red_box', 'A', objects, RETREAT_Z)
    with pytest.raises(TaskError, match='Khong giu'):
        plan_place('', 'A', ON_TABLE, RETREAT_Z)


def test_pick_place_rejects_object_already_in_bin():
    objects = dict(ON_TABLE, red_box=in_slot('A'))
    with pytest.raises(TaskError, match='trong khay'):
        plan_pick_place('red_box', 'B', objects, '', LIFT_Z, RETREAT_Z)


def test_sort_moves_every_table_object_to_distinct_free_slots():
    objects = dict(ON_TABLE, green_cylinder=in_slot('B'))
    actions = plan_sort(objects, '', LIFT_Z, RETREAT_Z)
    grips = [a.expected for a in actions if isinstance(a, Grip)]
    assert grips == ['red_box', 'blue_sphere']
    drops = [a.goal[:2] for a in actions if isinstance(a, Move) and a.label.startswith('Mang')]
    assert drops == [pytest.approx(BIN_SLOTS['A']), pytest.approx(BIN_SLOTS['C'])]


def test_sort_with_nothing_on_table():
    objects = {'red_box': in_slot('A')}
    with pytest.raises(TaskError, match='Khong con'):
        plan_sort(objects, '', LIFT_Z, RETREAT_Z)


def test_full_sort_plan_is_reachable():
    actions = plan_sort(ON_TABLE, '', LIFT_Z, RETREAT_Z)
    check_reachable(actions)
    for a in actions:
        if isinstance(a, Move):
            inverse_kinematics(*a.goal)


def test_check_reachable_rejects_far_object():
    far = {'red_box': ObjectState((0.2, 0.0, -0.205), 0.015)}
    with pytest.raises(TaskError, match='ngoai tam voi'):
        check_reachable(plan_pick('red_box', far, '', LIFT_Z))


def test_platform_half_thickness_consistent():
    assert PLATFORM_HALF_THICKNESS == pytest.approx(0.003)
