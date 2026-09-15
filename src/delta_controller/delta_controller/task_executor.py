"""
Thực thi lệnh cấp cao trên CartesianController: lập kế hoạch -> chạy từng thao tác -> kiểm chứng.

Mỗi lệnh lập lại kế hoạch từ vị trí vật đo được ngay lúc đó, và kiểm tra kết quả bằng vị trí
thật của vật sau khi làm (đã nhấc lên chưa, đã nằm đúng ô chưa) thay vì tin là đã thành công.
"""

import math
import time

from delta_controller.scene import OBJECTS
from delta_controller.task_planner import (
    check_reachable,
    first_free_slot,
    Grip,
    home_xy_of,
    locate,
    Move,
    occupied_slots,
    plan_goto,
    plan_pick,
    plan_place,
    plan_place_on_table,
    plan_reset,
    plan_unload,
    Release,
    TaskError,
)

SETTLE_SEC = 0.8
LIFT_CHECK = 0.01
# Vật đặt ra bàn được coi là đúng chỗ nếu lệch không quá giá trị này (m).
PLACE_TOLERANCE = 0.01
OBJECTS_WAIT_SEC = 3.0


class TaskExecutor:
    """Chạy lệnh goto / pick / place / pickplace / sort / unload / reset qua node điều khiển."""

    def __init__(self, node, log=print):
        self._node = node
        self._log = log

    # ------------------------------------------------------------------ lệnh

    def objects_report(self):
        objects = self._objects()
        held = self._node.held_object
        lines = []
        for name, obj in objects.items():
            x, y, z = obj.center
            lines.append(f'{name:15s} ({x:+.4f}, {y:+.4f}, {z:+.4f})  {locate(name, obj, held)}')
        return lines

    def goto(self, name):
        self._run(plan_goto(name, self._objects()))

    def pick(self, name):
        node = self._node
        objects = self._objects()
        actions = plan_pick(name, objects, node.held_object, node.safe_z_holding)
        start_z = objects[name].center[2]
        self._run(actions)
        time.sleep(SETTLE_SEC)
        now = self._objects()[name].center[2]
        lifted_mm = 1000 * (now - start_z)
        if now - start_z < LIFT_CHECK:
            raise TaskError(f'Kiem chung that bai: {name} chi nhac len {lifted_mm:.1f} mm')
        self._log(f'   ✓ {name} da duoc nhac len {lifted_mm:.0f} mm')

    def place(self, slot=None):
        node = self._node
        held = node.held_object
        objects = self._objects()
        others = {n: o for n, o in objects.items() if n != held}
        slot = slot or first_free_slot(others, held)
        actions = plan_place(held, slot, others, node.safe_z)
        self._run(actions)
        time.sleep(SETTLE_SEC)
        where = locate(held, self._objects()[held], '')
        if where != f'o {slot}':
            raise TaskError(f'Kiem chung that bai: {held} dang "{where}", khong phai o {slot}')
        self._log(f'   ✓ {held} nam trong o {slot}')

    def pick_place(self, name, slot=None):
        objects = self._objects()
        if name in objects:
            where = locate(name, objects[name], self._node.held_object)
            if where.startswith('o '):
                raise TaskError(f'{name} da nam trong khay ({where})')
        # Kiểm tra ô TRƯỚC khi nhặt, để không phải cầm vật mà không có chỗ thả.
        others = {n: o for n, o in objects.items() if n != name}
        if slot is None:
            first_free_slot(others, '')
        elif slot in occupied_slots(others, ''):
            raise TaskError(f'O {slot} da co vat')
        self.pick(name)
        self.place(slot)

    def unload(self, name, xy=None):
        """Lấy vật từ khay ra, đặt lên bàn tại xy (mặc định vị trí ban đầu), rồi kiểm chứng."""
        node = self._node
        objects = self._objects()
        # Lập kế hoạch đầy đủ trước để các kiểm tra (vật có trong khay, chỗ đặt trống, tầm với)
        # báo lỗi TRƯỚC khi robot nhặt vật.
        check_reachable(plan_unload(name, objects, node.held_object,
                                    node.safe_z_holding, node.safe_z, xy))
        target = xy if xy is not None else home_xy_of(name)

        self.pick(name)
        others = {n: o for n, o in self._objects().items() if n != name}
        self._run(plan_place_on_table(name, target, others, node.safe_z))
        time.sleep(SETTLE_SEC)
        obj = self._objects()[name]
        error = math.hypot(obj.center[0] - target[0], obj.center[1] - target[1])
        where = locate(name, obj, '')
        if where != 'tren ban' or error > PLACE_TOLERANCE:
            raise TaskError(f'Kiem chung that bai: {name} dang "{where}", '
                            f'lech {error * 1000:.1f} mm so voi diem dat')
        self._log(f'   ✓ {name} nam tren ban tai ({obj.center[0]:+.4f}, {obj.center[1]:+.4f}), '
                  f'lech {error * 1000:.1f} mm')

    def reset(self):
        """Lấy lần lượt mọi vật trong khay ra, đặt về vị trí ban đầu."""
        node = self._node
        check_reachable(plan_reset(self._objects(), node.held_object,
                                   node.safe_z_holding, node.safe_z))
        done = []
        while True:
            objects = self._objects()
            todo = [o.name for o in OBJECTS
                    if o.name in objects and locate(o.name, objects[o.name], '') != 'tren ban']
            if not todo:
                break
            name = todo[0]
            self._log(f'== Lay {name} ra ({len(done) + 1}/{len(done) + len(todo)})')
            self.unload(name)
            done.append(name)
        self._log(f'== Da dua ve vi tri ban dau: {", ".join(done)}')

    def sort(self):
        """Dọn lần lượt từng vật còn trên bàn vào ô trống; lập lại kế hoạch sau mỗi vật."""
        done = []
        while True:
            objects = self._objects()
            held = self._node.held_object
            if held:
                raise TaskError(f'Dang giu {held}, hay place/release truoc')
            todo = [n for n, o in objects.items() if locate(n, o, held) == 'tren ban']
            if not todo:
                break
            name = todo[0]
            self._log(f'== Don {name} ({len(done) + 1}/{len(done) + len(todo)})')
            self.pick_place(name)
            done.append(name)
        if not done:
            raise TaskError('Khong con vat nao tren ban')
        self._log(f'== Da don xong: {", ".join(done)}')

    # ------------------------------------------------------------------ thực thi

    def _objects(self):
        """
        Vị trí thật của TẤT CẢ vật trong scene, chờ tối đa OBJECTS_WAIT_SEC.

        Không chờ thì lệnh gõ ngay sau khi node khởi động thấy danh sách rỗng và hiểu nhầm là
        "không còn vật nào trên bàn" (đã gặp khi chạy kịch bản thử).
        """
        deadline = time.monotonic() + OBJECTS_WAIT_SEC
        while True:
            objects = self._node.object_states()
            missing = [o.name for o in OBJECTS if o.name not in objects]
            if not missing:
                return objects
            if time.monotonic() > deadline:
                raise TaskError(f'Chua nhan duoc vi tri {", ".join(missing)} '
                                f'(da chay pick_place.launch.py chua?)')
            time.sleep(0.05)

    def _run(self, actions):
        check_reachable(actions)
        node = self._node
        for i, action in enumerate(actions, 1):
            self._log(f'  [{i}/{len(actions)}] {action.label}')
            if isinstance(action, Move):
                node.move(action.goal, safe=action.safe)
            elif isinstance(action, Grip):
                success, message = node.call_gripper(release=False)
                if not success:
                    raise TaskError(f'Hut that bai: {message}')
                if action.expected not in message:
                    node.call_gripper(release=True)
                    raise TaskError(f'Hut nham vat ({message}), da nha ra')
            elif isinstance(action, Release):
                success, message = node.call_gripper(release=True)
                if not success:
                    raise TaskError(f'Nha that bai: {message}')
