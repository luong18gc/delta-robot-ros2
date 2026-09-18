#!/usr/bin/env python3
"""
Đo tỉ lệ gắp–thả thành công (Bước 9): camera so với vị trí thật, trên cùng các bố trí ngẫu nhiên.

Chạy khi mô phỏng đang chạy (ros2 launch delta_controller pick_place.launch.py):
    python3 src/delta_controller/scripts/run_pick_place_trials.py \
        [số_lượt] [seed] [camera,ground_truth]
Mỗi lượt: đặt 3 vật ngẫu nhiên (tầm với, không chồng khay/nhau) bằng /world/<w>/set_pose ->
`don` -> chấm bằng vị trí thật (vật nằm trong ô khác nhau) -> `reset` -> chấm (vật về chỗ cũ
≤ 10 mm).
Ghi docs/results/pick_place_trials.json + .md.
"""

import json
import math
import os
import random
import subprocess
import sys
import threading
import time

from delta_controller.cartesian_control_node import CartesianController, HOME_XYZ
from delta_controller.delta_kinematics import inverse_kinematics, UnreachableError
from delta_controller.gripper_logic import PLATFORM_HALF_THICKNESS
from delta_controller.scene import OBJECTS, TABLE_Z
from delta_controller.task_executor import TaskExecutor
from delta_controller.task_planner import check_table_spot, locate, TaskError
import rclpy
from rclpy.executors import SingleThreadedExecutor

WS = os.path.expanduser('~/ros2_closed_loop_ws')
REST_EXTRA = {'blue_sphere': 0.0005}
MODES = ('camera', 'ground_truth')


def random_layout(rng):
    """3 vị trí trên bàn: robot gắp được, không chồng khay, cách nhau ≥ 45 mm."""
    layout = {}
    while len(layout) < len(OBJECTS):
        obj = OBJECTS[len(layout)]
        x, y = rng.uniform(-0.09, 0.10), rng.uniform(-0.10, 0.10)
        try:
            inverse_kinematics(x, y, TABLE_Z + 2 * obj.half_height + PLATFORM_HALF_THICKNESS)
            check_table_spot(obj.name, (x, y), {})
        except (UnreachableError, TaskError):
            continue
        if any(math.hypot(x - px, y - py) < 0.045 for px, py in layout.values()):
            continue
        layout[obj.name] = (round(x, 4), round(y, 4))
    return layout


def set_pose(name, x, y, z):
    req = f'name: "{name}", position: {{x: {x}, y: {y}, z: {z + 1.0}}}'
    subprocess.run(['gz', 'service', '-s', '/world/delta_world/set_pose', '--reqtype',
                    'gz.msgs.Pose', '--reptype', 'gz.msgs.Boolean', '--timeout', '2000',
                    '--req', req], check=True, capture_output=True)


def truth(node):
    """Vị trí thật (odometry Gazebo), không phụ thuộc chế độ đang chạy."""
    return node.object_states()


def run_trial(node, mode, layout, logs):
    for obj in OBJECTS:
        x, y = layout[obj.name]
        set_pose(obj.name, x, y, TABLE_Z + obj.half_height + REST_EXTRA.get(obj.name, 0.0))
    time.sleep(1.0)
    node.object_source = mode
    ex = TaskExecutor(node, log=logs.append)
    result = {'mode': mode, 'layout': layout}

    t0 = time.monotonic()
    try:
        ex.sort()
        result['sort_error'] = None
    except (TaskError, RuntimeError, UnreachableError) as e:
        result['sort_error'] = str(e)
    result['sort_sec'] = time.monotonic() - t0
    gt = truth(node)
    slots = {n: locate(n, o, '') for n, o in gt.items()}
    in_slot = [n for n, w in slots.items() if w.startswith('o ')]
    result['sorted'] = len(in_slot)
    result['distinct_slots'] = len({slots[n] for n in in_slot}) == len(in_slot)
    result['slots'] = slots

    held = node.held_object
    if held:   # gắp được nhưng hỏng giữa chừng: nhả ra để lượt reset chạy được
        node.call_gripper(release=True)
    t0 = time.monotonic()
    try:
        ex.reset()
        result['reset_error'] = None
    except (TaskError, RuntimeError, UnreachableError) as e:
        result['reset_error'] = str(e)
    result['reset_sec'] = time.monotonic() - t0
    gt = truth(node)
    home_err = {o.name: 1000 * math.hypot(gt[o.name].center[0] - o.home_xy[0],
                                          gt[o.name].center[1] - o.home_xy[1]) for o in OBJECTS}
    result['home_error_mm'] = home_err
    result['reset_ok'] = sum(e <= 10.0 for e in home_err.values())
    if node.held_object:
        node.call_gripper(release=True)
    node.move(HOME_XYZ, safe=True)
    return result


def main():
    trials = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 2026
    modes = tuple(sys.argv[3].split(',')) if len(sys.argv) > 3 else MODES
    rng = random.Random(seed)
    layouts = [random_layout(rng) for _ in range(trials)]

    rclpy.init()
    node = CartesianController()
    executor = SingleThreadedExecutor()
    executor.add_node(node)
    spin_thread = threading.Thread(target=executor.spin, daemon=True)
    spin_thread.start()
    if not node.wait_for_connection(10.0):
        print('Khong ket noi duoc mo phong')
        return

    results = []
    for mode in modes:
        for i, layout in enumerate(layouts):
            logs = []
            r = run_trial(node, mode, layout, logs)
            r['trial'] = i
            r['log'] = logs
            results.append(r)
            print(f"[{mode:12s}] luot {i}: don {r['sorted']}/3 "
                  f"({'loi: ' + r['sort_error'] if r['sort_error'] else 'ok'}), "
                  f"reset {r['reset_ok']}/3 "
                  f"({'loi: ' + r['reset_error'] if r['reset_error'] else 'ok'}), "
                  f"{r['sort_sec']:.0f}+{r['reset_sec']:.0f} s", flush=True)

    out = os.path.join(WS, 'docs', 'results')
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'pick_place_trials.json'), 'w') as f:
        json.dump({'seed': seed, 'results': results}, f, indent=1, ensure_ascii=False)
    lines = ['# Gắp–thả dựa trên camera so với vị trí thật (Bước 9)', '',
             f'{trials} bố trí ngẫu nhiên (seed {seed}), mỗi lượt `don` rồi `reset`. Chấm bằng vị '
             'trí thật (odometry Gazebo): `don` thành công khi vật nằm trong một ô riêng; `reset` '
             'thành công khi vật về chỗ cũ lệch ≤ 10 mm.', '',
             '| Chế độ | Vật vào ô | Lượt `don` trọn vẹn | Vật về chỗ cũ | Lượt `reset` trọn vẹn '
             '| Thời gian TB don + reset (s) |', '|---|---|---|---|---|---|']
    for mode in modes:
        rs = [r for r in results if r['mode'] == mode]
        lines.append(
            f"| {mode} | {sum(r['sorted'] for r in rs)}/{3 * len(rs)} | "
            f"{sum(r['sorted'] == 3 and r['distinct_slots'] for r in rs)}/{len(rs)} | "
            f"{sum(r['reset_ok'] for r in rs)}/{3 * len(rs)} | "
            f"{sum(r['reset_ok'] == 3 for r in rs)}/{len(rs)} | "
            f"{sum(r['sort_sec'] for r in rs) / len(rs):.0f} + "
            f"{sum(r['reset_sec'] for r in rs) / len(rs):.0f} |")
    lines += ['', '## Lỗi gặp phải', '']
    for r in results:
        for key in ('sort_error', 'reset_error'):
            if r[key]:
                lines.append(f"- [{r['mode']}] lượt {r['trial']} `{key[:-6]}`: {r[key]}")
    with open(os.path.join(out, 'pick_place_trials.md'), 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    # Dừng executor và chờ luồng spin kết thúc trước khi hủy node (tránh "terminate called
    # without an active exception" — lỗi đã gặp ở cartesian_control).
    executor.shutdown()
    spin_thread.join(timeout=2.0)
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
