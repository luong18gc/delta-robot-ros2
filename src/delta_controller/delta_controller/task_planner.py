"""
Lập kế hoạch lệnh cấp cao cho robot delta (thuần Python, không phụ thuộc ROS).

Lệnh cấp cao ("nhặt hộp đỏ", "thả vào ô A") được chia thành chuỗi thao tác cơ bản mà node
thực thi lần lượt: Move (đi tới điểm), Grip (hút), Release (nhả). Kế hoạch dựa trên vị trí
THẬT của vật đo từ mô phỏng, nên vẫn đúng khi vật đã bị đẩy lệch.
"""

from dataclasses import dataclass
import math

from delta_controller.delta_kinematics import inverse_kinematics, UnreachableError
from delta_controller.gripper_logic import ObjectState, PLATFORM_HALF_THICKNESS
from delta_controller.scene import (
    BIN_CLEARANCE,
    BIN_FLOOR_Z,
    BIN_INNER_HALF,
    BIN_OUTER_HALF,
    BINS,
    DROP_GAP,
    MIN_SEPARATION,
    OBJECT_HALF_WIDTH,
    OBJECTS,
    TABLE_Z,
)

# Độ cao lơ lửng trên đỉnh vật cho lệnh goto (m).
HOVER_CLEARANCE = 0.02
# Vật được coi là đã nhấc lên nếu cao hơn mặt khay/bàn thêm giá trị này (m).
LIFTED_MARGIN = 0.01


class TaskError(Exception):
    """Lệnh cấp cao không thực hiện được (tên vật sai, ô đã đầy, ngoài tầm với...)."""


@dataclass(frozen=True)
class Move:
    goal: tuple
    safe: bool
    label: str


@dataclass(frozen=True)
class Grip:
    expected: str
    label: str


@dataclass(frozen=True)
class Release:
    label: str


# ---------------------------------------------------------------- tra cứu

def resolve_object(text):
    """Đổi tên nhập vào (tên model hoặc tên tắt, không phân biệt hoa thường) thành tên model."""
    key = text.strip().lower()
    for obj in OBJECTS:
        if key == obj.name or key in obj.aliases:
            return obj.name
    names = ', '.join(f'{o.name} ({"/".join(o.aliases[:2])})' for o in OBJECTS)
    raise TaskError(f'Khong biet vat "{text}". Cac vat: {names}')


def bin_of(name):
    """Khay dành riêng cho loại vật này. Mỗi loại một khay -> không phải chọn ô."""
    if name not in BINS:
        raise TaskError(f'Khong co khay cho {name}')
    return BINS[name]


def half_height_of(name):
    return next(o.half_height for o in OBJECTS if o.name == name)


def touch_point(obj):
    """Tâm tool0 khi mặt dưới platform vừa chạm đỉnh vật."""
    return (obj.center[0], obj.center[1], obj.top_z + PLATFORM_HALF_THICKNESS)


def hover_point(obj):
    x, y, z = touch_point(obj)
    return (x, y, z + HOVER_CLEARANCE)


def _release_z(surface_z, half_height):
    return surface_z + DROP_GAP + 2.0 * half_height + PLATFORM_HALF_THICKNESS


def release_point(name, half_height):
    """Tâm tool0 để đáy vật đang giữ cách đáy KHAY CỦA NÓ một khoảng DROP_GAP."""
    x, y = bin_of(name)
    return (x, y, _release_z(BIN_FLOOR_Z, half_height))


def table_release_point(x, y, half_height):
    """Tâm tool0 để đáy vật đang giữ cách mặt bàn DROP_GAP tại (x, y)."""
    return (x, y, _release_z(TABLE_Z, half_height))


def home_xy_of(name):
    return next(o.home_xy for o in OBJECTS if o.name == name)


def check_table_spot(name, xy, objects):
    """
    Kiểm tra đặt vật name xuống bàn tại xy có an toàn không.

    Từ chối nếu vật chạm khay (tính cả thành) hoặc quá gần tâm vật khác. Ném TaskError.
    """
    x, y = xy
    reach = BIN_OUTER_HALF + OBJECT_HALF_WIDTH + BIN_CLEARANCE
    for bin_name, (bx, by) in BINS.items():
        if abs(x - bx) < reach and abs(y - by) < reach:
            raise TaskError(f'Diem ({x:.4f}, {y:.4f}) chong len khay {bin_name}')
    for other, obj in objects.items():
        if other == name:
            continue
        distance = math.hypot(x - obj.center[0], y - obj.center[1])
        if distance < MIN_SEPARATION:
            raise TaskError(
                f'Diem ({x:.4f}, {y:.4f}) qua gan {other} ({distance * 1000:.0f} mm, '
                f'can >= {MIN_SEPARATION * 1000:.0f} mm)')


# ---------------------------------------------------------------- trạng thái cảnh

def locate(name, obj, held):
    """
    Mô tả vị trí vật.

    Trả về 'dang giu', 'khay <loại>' (đúng khay của nó), 'khay la <loại>' (nằm nhầm khay),
    hoặc 'tren ban'.
    """
    if name == held:
        return 'dang giu'
    for bin_name, (bx, by) in BINS.items():
        if inside_bin_region(obj.center[0], obj.center[1], bin_name):
            return f'khay {bin_name}' if bin_name == name else f'khay la {bin_name}'
    return 'tren ban'


def inside_bin_region(x, y, bin_name=None):
    """Điểm (x, y) nằm trong lòng một khay (hoặc đúng khay bin_name nếu có chỉ định)."""
    targets = [BINS[bin_name]] if bin_name else list(BINS.values())
    return any(abs(x - bx) < BIN_INNER_HALF and abs(y - by) < BIN_INNER_HALF
               for bx, by in targets)


def in_bin(obj):
    return inside_bin_region(obj.center[0], obj.center[1])


def in_own_bin(name, obj):
    """Vật đã nằm đúng khay dành cho nó chưa."""
    return inside_bin_region(obj.center[0], obj.center[1], name)


def is_lifted(obj, surface_z):
    """Vật đã rời bề mặt (bàn hoặc đáy khay) chưa."""
    return obj.center[2] - obj.half_height > surface_z + LIFTED_MARGIN


# ---------------------------------------------------------------- kế hoạch

def _require_object(name, objects):
    if name not in objects:
        raise TaskError(f'Chua nhan duoc vi tri {name} (da chay pick_place.launch.py chua?)')
    return objects[name]


def plan_goto(name, objects):
    obj = _require_object(name, objects)
    return [Move(hover_point(obj), safe=True, label=f'Di toi tren {name}')]


def plan_pick(name, objects, held, lift_z):
    """Hạ xuống chạm đỉnh vật -> hút -> nhấc thẳng lên độ cao lift_z."""
    if held:
        raise TaskError(f'Dang giu {held}, hay place/release truoc')
    obj = _require_object(name, objects)
    tx, ty, tz = touch_point(obj)
    if lift_z < tz:
        raise TaskError(f'Do cao nhac {lift_z} thap hon diem cham {tz:.4f}')
    return [
        Move((tx, ty, tz), safe=True, label=f'Ha xuong cham dinh {name}'),
        Grip(expected=name, label=f'Hut {name}'),
        Move((tx, ty, lift_z), safe=False, label=f'Nhac {name} len'),
    ]


def plan_place(held, objects, retreat_z):
    """Mang vật tới ĐÚNG KHAY CỦA NÓ -> nhả -> lùi thẳng lên độ cao retreat_z."""
    if not held:
        raise TaskError('Khong giu vat nao de tha')
    for other, obj in objects.items():
        if other != held and in_own_bin(held, obj):
            raise TaskError(f'Khay {held} dang co {other}')
    return _drop(held, release_point(held, half_height_of(held)), retreat_z, f'khay {held}')


def plan_place_on_table(held, xy, objects, retreat_z):
    """Mang vật đang giữ tới (x, y) trên bàn -> nhả -> lùi lên."""
    if not held:
        raise TaskError('Khong giu vat nao de dat')
    check_table_spot(held, xy, objects)
    x, y = xy
    return _drop(held, table_release_point(x, y, half_height_of(held)), retreat_z,
                 f'ban ({x:.4f}, {y:.4f})')


def _drop(held, point, retreat_z, where):
    rx, ry, rz = point
    return [
        Move((rx, ry, rz), safe=True, label=f'Mang {held} toi {where}'),
        Release(label=f'Nha {held}'),
        Move((rx, ry, max(retreat_z, rz)), safe=False, label='Lui len'),
    ]


def plan_unload(name, objects, held, lift_z, retreat_z, xy=None):
    """Lấy vật name từ khay ra, đặt lên bàn tại xy (mặc định: vị trí ban đầu của vật)."""
    obj = _require_object(name, objects)
    where = locate(name, obj, held)
    if where == 'tren ban':
        raise TaskError(f'{name} dang nam tren ban, khong o trong khay')
    target = xy if xy is not None else home_xy_of(name)
    others = _without(objects, name)
    check_table_spot(name, target, others)  # kiểm tra TRƯỚC khi nhặt
    return (plan_pick(name, objects, held, lift_z)
            + plan_place_on_table(name, target, others, retreat_z))


def plan_reset(objects, held, lift_z, retreat_z):
    """Lấy mọi vật trong khay ra, đặt về vị trí ban đầu (theo thứ tự scene.OBJECTS)."""
    if held:
        raise TaskError(f'Dang giu {held}, hay place/release truoc')
    todo = [o.name for o in OBJECTS
            if o.name in objects and locate(o.name, objects[o.name], held) != 'tren ban']
    if not todo:
        raise TaskError('Khong co vat nao trong khay')
    actions = []
    # Mô phỏng cảnh sau từng vật để vật sau kiểm tra chỗ đặt với vị trí MỚI của vật trước.
    scene = dict(objects)
    for name in todo:
        actions += plan_unload(name, scene, '', lift_z, retreat_z)
        hx, hy = home_xy_of(name)
        scene[name] = ObjectState((hx, hy, TABLE_Z + scene[name].half_height),
                                  scene[name].half_height)
    return actions


def plan_pick_place(name, objects, held, lift_z, retreat_z):
    """Nhặt vật rồi thả vào đúng khay của loại đó."""
    if name in objects and locate(name, objects[name], held).startswith('khay '):
        raise TaskError(f'{name} da nam trong khay ({locate(name, objects[name], held)})')
    return (plan_pick(name, objects, held, lift_z)
            + plan_place(name, _without(objects, name), retreat_z))


def plan_sort(objects, held, lift_z, retreat_z):
    """Phân loại: mọi vật còn trên bàn về ĐÚNG khay của loại đó, theo thứ tự scene.OBJECTS."""
    if held:
        raise TaskError(f'Dang giu {held}, hay place/release truoc')
    actions = []
    todo = [o.name for o in OBJECTS
            if o.name in objects and locate(o.name, objects[o.name], held) == 'tren ban']
    if not todo:
        raise TaskError('Khong con vat nao tren ban')
    for name in todo:
        actions += plan_pick(name, objects, '', lift_z)
        actions += plan_place(name, _without(objects, name), retreat_z)
    return actions


def _without(objects, name):
    return {n: o for n, o in objects.items() if n != name}


def check_reachable(actions):
    """Kiểm tra IK mọi điểm đích TRƯỚC khi chạy (tránh bỏ dở giữa chừng khi đang giữ vật)."""
    for action in actions:
        if isinstance(action, Move):
            try:
                inverse_kinematics(*action.goal)
            except UnreachableError as e:
                raise TaskError(f'{action.label}: diem {action.goal} ngoai tam voi ({e})') from e


def object_states(centers):
    """Đổi dict tên -> tâm (x, y, z) thành dict tên -> ObjectState theo scene.OBJECTS."""
    return {n: ObjectState(c, half_height_of(n)) for n, c in centers.items()
            if any(o.name == n for o in OBJECTS)}
