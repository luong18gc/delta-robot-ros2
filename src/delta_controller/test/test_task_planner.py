"""Test lập kế hoạch lệnh cấp cao (cảnh ba lon, mỗi loại một khay riêng)."""

from delta_controller.delta_kinematics import inverse_kinematics
from delta_controller.gripper_logic import (
    ObjectState,
    PLATFORM_HALF_THICKNESS,
    select_graspable,
)
from delta_controller.scene import BIN_FLOOR_Z, BINS, CAN_HALF_HEIGHT, OBJECTS, TABLE_Z
from delta_controller.task_planner import (
    bin_of,
    check_reachable,
    check_table_spot,
    Grip,
    hover_point,
    in_own_bin,
    is_lifted,
    locate,
    Move,
    plan_goto,
    plan_pick,
    plan_pick_place,
    plan_place,
    plan_reset,
    plan_sort,
    plan_unload,
    Release,
    release_point,
    resolve_object,
    sight_blocked_by_bin,
    sort_order,
    table_release_point,
    TaskError,
    touch_point,
)
import pytest

# = cartesian_control safe_z_holding: đủ cao để lon đang mang vượt qua đầu lon đang đứng.
LIFT_Z = -0.112
RETREAT_Z = -0.16       # = safe_z
H = CAN_HALF_HEIGHT     # 0.0294
CENTER_Z = TABLE_Z + H  # -0.1906: tâm lon khi đứng trên bàn
TOUCH_Z = TABLE_Z + 2 * H + PLATFORM_HALF_THICKNESS      # -0.1582
DROP_Z = BIN_FLOOR_Z + 0.005 + 2 * H + PLATFORM_HALF_THICKNESS   # -0.1502
TABLE_DROP_Z = TABLE_Z + 0.005 + 2 * H + PLATFORM_HALF_THICKNESS  # -0.1532

ON_TABLE = {o.name: ObjectState((o.home_xy[0], o.home_xy[1], CENTER_Z), H) for o in OBJECTS}
HOME = {o.name: o.home_xy for o in OBJECTS}


def in_bin(name):
    """Lon nằm trong khay của chính nó."""
    x, y = BINS[name]
    return ObjectState((x, y, BIN_FLOOR_Z + H), H)


# ---------------------------------------------------------------- tra cứu

@pytest.mark.parametrize('text, name', [
    ('coca_can', 'coca_can'), ('COCA', 'coca_can'), ('do', 'coca_can'), ('coke', 'coca_can'),
    ('pepsi', 'pepsi_can'), ('lam', 'pepsi_can'),
    ('7up', 'sevenup_can'), (' SevenUp ', 'sevenup_can'), ('xanhla', 'sevenup_can'),
])
def test_resolve_object(text, name):
    assert resolve_object(text) == name


def test_resolve_unknown_object_lists_choices():
    with pytest.raises(TaskError, match='coca_can'):
        resolve_object('vang')


def test_bin_of_gives_each_can_its_own_bin():
    assert bin_of('coca_can') == BINS['coca_can']
    assert len({bin_of(o.name) for o in OBJECTS}) == 3
    with pytest.raises(TaskError):
        bin_of('khong_co')


# ---------------------------------------------------------------- điểm hình học

def test_touch_point_is_top_of_can_plus_platform_half():
    assert touch_point(ON_TABLE['coca_can']) == pytest.approx((*HOME['coca_can'], TOUCH_Z))


def test_touch_point_is_accepted_by_gripper_logic():
    for name, obj in ON_TABLE.items():
        assert select_graspable(touch_point(obj), ON_TABLE) == name


def test_hover_point_is_above_touch_point():
    assert hover_point(ON_TABLE['coca_can'])[2] == pytest.approx(TOUCH_Z + 0.02)


def test_release_point_is_own_bin_at_drop_height():
    for name, (x, y) in BINS.items():
        assert release_point(name, H) == pytest.approx((x, y, DROP_Z))


def test_carried_can_clears_bin_wall_and_standing_cans():
    """
    Lon đang mang phải vượt qua cả thành khay LẪN đầu lon đang đứng trên bàn.

    Bỏ điều kiện thứ hai thì lon mang qua sẽ húc đổ lon đứng — đã gặp với k = 2.5 (đo 2026-09-29).
    """
    bottom = LIFT_Z - PLATFORM_HALF_THICKNESS - 2 * H
    assert bottom > -0.205, 'khong vuot duoc thanh khay'
    assert bottom > TABLE_Z + 2 * H, 'khong vuot duoc dau lon dang dung'


# ---------------------------------------------------------------- trạng thái cảnh

def test_locate_distinguishes_own_bin_from_wrong_bin():
    assert locate('coca_can', ON_TABLE['coca_can'], '') == 'tren ban'
    assert locate('coca_can', in_bin('coca_can'), '') == 'khay coca_can'
    assert locate('coca_can', in_bin('pepsi_can'), '') == 'khay la pepsi_can'
    assert locate('coca_can', ON_TABLE['coca_can'], 'coca_can') == 'dang giu'


def test_in_own_bin():
    assert in_own_bin('coca_can', in_bin('coca_can'))
    assert not in_own_bin('coca_can', in_bin('sevenup_can'))
    assert not in_own_bin('coca_can', ON_TABLE['coca_can'])


def test_is_lifted():
    assert not is_lifted(ON_TABLE['coca_can'], TABLE_Z)
    lifted = ObjectState((*HOME['coca_can'], CENTER_Z + 0.047), H)
    assert is_lifted(lifted, TABLE_Z)


# ---------------------------------------------------------------- kế hoạch

def test_goto_hovers_above_object():
    [move] = plan_goto('pepsi_can', ON_TABLE)
    assert move.safe and move.goal == pytest.approx(hover_point(ON_TABLE['pepsi_can']))


def test_pick_sequence():
    actions = plan_pick('coca_can', ON_TABLE, '', LIFT_Z)
    assert [type(a) for a in actions] == [Move, Grip, Move]
    down, grip, up = actions
    assert down.safe and down.goal == pytest.approx((*HOME['coca_can'], TOUCH_Z))
    assert grip.expected == 'coca_can'
    assert not up.safe and up.goal == pytest.approx((*HOME['coca_can'], LIFT_Z))


def test_pick_uses_actual_pushed_position():
    pushed = dict(ON_TABLE, coca_can=ObjectState(
        (HOME['coca_can'][0] + 0.012, HOME['coca_can'][1] + 0.004, CENTER_Z), H))
    assert plan_pick('coca_can', pushed, '', LIFT_Z)[0].goal[:2] == pytest.approx(
        (HOME['coca_can'][0] + 0.012, HOME['coca_can'][1] + 0.004))


def test_pick_while_holding_is_rejected():
    with pytest.raises(TaskError, match='Dang giu'):
        plan_pick('coca_can', ON_TABLE, 'pepsi_can', LIFT_Z)


def test_pick_unknown_position_is_rejected():
    with pytest.raises(TaskError, match='Chua nhan'):
        plan_pick('coca_can', {}, '', LIFT_Z)


def test_place_goes_to_own_bin():
    actions = plan_place('coca_can', ON_TABLE, RETREAT_Z)
    assert [type(a) for a in actions] == [Move, Release, Move]
    assert actions[0].safe and actions[0].goal == pytest.approx(release_point('coca_can', H))
    # điểm nhả (-0.1502) đã cao hơn safe_z (-0.16) nên "lùi lên" giữ nguyên cao độ
    assert not actions[2].safe
    assert actions[2].goal[2] == pytest.approx(max(RETREAT_Z, DROP_Z))


def test_place_rejects_bin_taken_by_another_can_and_empty_gripper():
    objects = dict(ON_TABLE, pepsi_can=in_bin('coca_can'))
    with pytest.raises(TaskError, match='dang co pepsi_can'):
        plan_place('coca_can', objects, RETREAT_Z)
    with pytest.raises(TaskError, match='Khong giu'):
        plan_place('', ON_TABLE, RETREAT_Z)


def test_pick_place_rejects_object_already_in_bin():
    objects = dict(ON_TABLE, coca_can=in_bin('coca_can'))
    with pytest.raises(TaskError, match='trong khay'):
        plan_pick_place('coca_can', objects, '', LIFT_Z, RETREAT_Z)


def test_sort_sends_every_can_to_its_own_bin():
    actions = plan_sort(ON_TABLE, '', LIFT_Z, RETREAT_Z)
    grips = [a.expected for a in actions if isinstance(a, Grip)]
    assert grips == [o.name for o in OBJECTS]
    drops = [a.goal[:2] for a in actions if isinstance(a, Move) and a.label.startswith('Mang')]
    assert drops == [pytest.approx(BINS[o.name]) for o in OBJECTS]


def test_sort_skips_cans_already_in_a_bin():
    objects = dict(ON_TABLE, pepsi_can=in_bin('pepsi_can'))
    grips = [a.expected for a in plan_sort(objects, '', LIFT_Z, RETREAT_Z)
             if isinstance(a, Grip)]
    assert grips == ['coca_can', 'sevenup_can']


def test_sort_with_nothing_on_table():
    objects = {'coca_can': in_bin('coca_can')}
    with pytest.raises(TaskError, match='Khong con'):
        plan_sort(objects, '', LIFT_Z, RETREAT_Z)


def test_full_sort_plan_is_reachable():
    actions = plan_sort(ON_TABLE, '', LIFT_Z, RETREAT_Z)
    check_reachable(actions)
    for a in actions:
        if isinstance(a, Move):
            inverse_kinematics(*a.goal)


def test_check_reachable_rejects_far_object():
    far = {'coca_can': ObjectState((0.2, 0.0, CENTER_Z), H)}
    with pytest.raises(TaskError, match='ngoai tam voi'):
        check_reachable(plan_pick('coca_can', far, '', LIFT_Z))


def test_platform_half_thickness_consistent():
    assert PLATFORM_HALF_THICKNESS == pytest.approx(0.003)


# ---------------------------------------------------------------- lấy ra / reset

IN_BIN = {o.name: in_bin(o.name) for o in OBJECTS}


def test_table_release_point_height():
    """Mặt bàn -0.22 + khe 5 mm + lon 58.8 mm + nửa platform 3 mm."""
    assert (table_release_point(*HOME['coca_can'], H)
            == pytest.approx((*HOME['coca_can'], TABLE_DROP_Z)))


def test_home_positions_are_valid_table_spots():
    for obj in OBJECTS:
        check_table_spot(obj.name, obj.home_xy, {})
        inverse_kinematics(*table_release_point(*obj.home_xy, obj.half_height))


@pytest.mark.parametrize('xy', list(BINS.values()) + [(-0.06, 0.0 + 0.03)])
def test_table_spot_rejects_bin_footprint(xy):
    with pytest.raises(TaskError, match='khay'):
        check_table_spot('coca_can', xy, {})


def test_table_spot_rejects_near_other_object_but_ignores_itself():
    objects = dict(ON_TABLE)
    with pytest.raises(TaskError, match='qua gan pepsi_can'):
        check_table_spot('coca_can', (HOME['pepsi_can'][0], HOME['pepsi_can'][1] - 0.02),
                         objects)
    check_table_spot('coca_can', HOME['coca_can'], objects)  # chính nó: không tính


def test_unload_sequence_goes_to_home_by_default():
    actions = plan_unload('coca_can', IN_BIN, '', LIFT_Z, RETREAT_Z)
    assert [type(a) for a in actions] == [Move, Grip, Move, Move, Release, Move]
    assert actions[0].goal == pytest.approx(touch_point(IN_BIN['coca_can']))
    assert actions[3].safe
    assert actions[3].goal == pytest.approx((*HOME['coca_can'], TABLE_DROP_Z))


def test_unload_to_custom_spot():
    actions = plan_unload('coca_can', IN_BIN, '', LIFT_Z, RETREAT_Z, xy=(0.02, -0.095))
    assert actions[3].goal == pytest.approx((0.02, -0.095, TABLE_DROP_Z))


def test_unload_rejects_object_on_table():
    with pytest.raises(TaskError, match='tren ban'):
        plan_unload('coca_can', ON_TABLE, '', LIFT_Z, RETREAT_Z)


def test_unload_rejects_blocked_spot_before_picking():
    objects = dict(IN_BIN, pepsi_can=ObjectState(
        (HOME['coca_can'][0] + 0.005, HOME['coca_can'][1] + 0.005, CENTER_Z), H))
    with pytest.raises(TaskError, match='qua gan pepsi_can'):
        plan_unload('coca_can', objects, '', LIFT_Z, RETREAT_Z)


def test_reset_unloads_every_bin_object_to_its_home():
    actions = plan_reset(IN_BIN, '', LIFT_Z, RETREAT_Z)
    check_reachable(actions)
    grips = [a.expected for a in actions if isinstance(a, Grip)]
    assert grips == [o.name for o in OBJECTS]
    drops = [a.goal for a in actions if isinstance(a, Move) and a.label.startswith('Mang')]
    assert drops == [pytest.approx(table_release_point(*o.home_xy, H)) for o in OBJECTS]


def test_reset_skips_objects_already_on_table():
    objects = dict(IN_BIN, coca_can=ON_TABLE['coca_can'])
    grips = [a.expected for a in plan_reset(objects, '', LIFT_Z, RETREAT_Z)
             if isinstance(a, Grip)]
    assert grips == ['pepsi_can', 'sevenup_can']


def test_reset_with_empty_bin_or_holding():
    with pytest.raises(TaskError, match='Khong co vat nao trong khay'):
        plan_reset(ON_TABLE, '', LIFT_Z, RETREAT_Z)
    with pytest.raises(TaskError, match='Dang giu'):
        plan_reset(IN_BIN, 'coca_can', LIFT_Z, RETREAT_Z)


# ---------------------------------------------------------------- thứ tự có xét tầm nhìn

def _on_table(**spots):
    return {name: ObjectState((x, y, CENTER_Z), H) for name, (x, y) in spots.items()}


def test_sight_blocked_by_bin():
    """Khay nằm giữa camera và vật thì che; khay lệch sang bên thì không."""
    # khay sevenup ở (-0.06, 0.075); camera ở (-0.40, 0) -> tia tới (0.007, 0.072) quét qua nó
    assert sight_blocked_by_bin((0.0072, 0.072), 'sevenup_can')
    assert not sight_blocked_by_bin((0.0072, 0.072), 'coca_can')   # khay ở y = -0.075
    # vật nằm ngay trước khay (phía camera) thì tia chưa tới khay
    assert not sight_blocked_by_bin((-0.12, 0.075), 'sevenup_can')


def test_sort_order_picks_threatened_object_first():
    """Bố trí lượt 0 của thí nghiệm: khay 7up sẽ che lon coca -> coca phải đứng TRƯỚC 7up."""
    objects = _on_table(coca_can=(0.0072, 0.072), pepsi_can=(0.0242, 0.0113),
                        sevenup_can=(0.0488, 0.0536))
    for names in (['pepsi_can', 'sevenup_can', 'coca_can'],
                  ['sevenup_can', 'pepsi_can', 'coca_can'],
                  ['coca_can', 'pepsi_can', 'sevenup_can']):
        order = sort_order(names, objects)
        assert sorted(order) == sorted(names)
        assert order.index('coca_can') < order.index('sevenup_can'), order


def test_sort_order_keeps_input_order_when_nothing_is_threatened():
    objects = _on_table(coca_can=(0.09, -0.06), pepsi_can=(0.09, 0.0), sevenup_can=(0.09, 0.06))
    names = ['sevenup_can', 'coca_can', 'pepsi_can']
    assert sort_order(names, objects) == names


def test_plan_sort_follows_visibility_order():
    objects = _on_table(coca_can=(0.0072, 0.072), pepsi_can=(0.0242, 0.0113),
                        sevenup_can=(0.0488, 0.0536))
    grips = [a.expected for a in plan_sort(objects, '', LIFT_Z, RETREAT_Z)
             if isinstance(a, Grip)]
    assert grips.index('coca_can') < grips.index('sevenup_can')
