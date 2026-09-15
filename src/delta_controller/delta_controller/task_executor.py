"""
Thực thi lệnh cấp cao trên CartesianController: lập kế hoạch -> chạy từng thao tác -> kiểm chứng.

Mỗi lệnh lập lại kế hoạch từ vị trí vật đo được ngay lúc đó, và kiểm tra kết quả bằng vị trí
thật của vật sau khi làm (đã nhấc lên chưa, đã nằm đúng ô chưa) thay vì tin là đã thành công.
"""

import time

from delta_controller.task_planner import (
    check_reachable,
    first_free_slot,
    Grip,
    locate,
    Move,
    occupied_slots,
    plan_goto,
    plan_pick,
    plan_place,
    Release,
    TaskError,
)

SETTLE_SEC = 0.8
LIFT_CHECK = 0.01


class TaskExecutor:
    """Chạy lệnh goto / pick / place / pickplace / sort qua node điều khiển."""

    def __init__(self, node, log=print):
        self._node = node
        self._log = log

    # ------------------------------------------------------------------ lệnh

    def objects_report(self):
        objects = self._node.object_states()
        if not objects:
            raise TaskError('Chua nhan duoc vi tri vat (da chay pick_place.launch.py chua?)')
        held = self._node.held_object
        lines = []
        for name, obj in objects.items():
            x, y, z = obj.center
            lines.append(f'{name:15s} ({x:+.4f}, {y:+.4f}, {z:+.4f})  {locate(name, obj, held)}')
        return lines

    def goto(self, name):
        self._run(plan_goto(name, self._node.object_states()))

    def pick(self, name):
        node = self._node
        objects = node.object_states()
        actions = plan_pick(name, objects, node.held_object, node.safe_z_holding)
        start_z = objects[name].center[2]
        self._run(actions)
        time.sleep(SETTLE_SEC)
        now = node.object_states()[name].center[2]
        lifted_mm = 1000 * (now - start_z)
        if now - start_z < LIFT_CHECK:
            raise TaskError(f'Kiem chung that bai: {name} chi nhac len {lifted_mm:.1f} mm')
        self._log(f'   ✓ {name} da duoc nhac len {lifted_mm:.0f} mm')

    def place(self, slot=None):
        node = self._node
        held = node.held_object
        objects = node.object_states()
        others = {n: o for n, o in objects.items() if n != held}
        slot = slot or first_free_slot(others, held)
        actions = plan_place(held, slot, others, node.safe_z)
        self._run(actions)
        time.sleep(SETTLE_SEC)
        where = locate(held, node.object_states()[held], '')
        if where != f'o {slot}':
            raise TaskError(f'Kiem chung that bai: {held} dang "{where}", khong phai o {slot}')
        self._log(f'   ✓ {held} nam trong o {slot}')

    def pick_place(self, name, slot=None):
        objects = self._node.object_states()
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

    def sort(self):
        """Dọn lần lượt từng vật còn trên bàn vào ô trống; lập lại kế hoạch sau mỗi vật."""
        done = []
        while True:
            objects = self._node.object_states()
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
