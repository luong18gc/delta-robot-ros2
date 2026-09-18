"""Test chế độ camera của TaskExecutor bằng robot giả (không cần ROS/Gazebo)."""

from delta_controller import task_executor as te
from delta_controller.gripper_logic import ObjectState
from delta_controller.scene import BIN_FLOOR_Z, OBJECTS, OBSERVE_XYZ, TABLE_Z
from delta_controller.task_planner import inside_bin_region, TaskError
import pytest

HALF = {o.name: o.half_height for o in OBJECTS}


class FakeRobot:
    """Robot + camera giả: nhớ vị trí vật, nhả vật tại điểm đích cuối cùng."""

    def __init__(self, source='camera', hidden=()):
        self.object_source = source
        self.held_object = ''
        self.safe_z = -0.16
        self.safe_z_holding = -0.14
        self.moves = []
        self.observations = 0
        self.hidden = set(hidden)      # vật camera thấy nhưng không tin cậy
        self.world = {o.name: (o.home_xy[0], o.home_xy[1], TABLE_Z + o.half_height)
                      for o in OBJECTS}

    def move(self, goal, safe):
        self.moves.append(tuple(goal))

    def call_gripper(self, release):
        x, y, _ = self.moves[-1]
        if release:
            name = self.held_object
            surface = BIN_FLOOR_Z if inside_bin_region(x, y) else TABLE_Z
            self.world[name] = (x, y, surface + HALF[name])
            self.held_object = ''
            return True, f'Da nha {name}'
        name = min(self.world, key=lambda n: (self.world[n][0] - x) ** 2
                   + (self.world[n][1] - y) ** 2)
        self.held_object = name
        return True, f'Da hut {name}'

    def observe_camera(self, after):
        self.observations += 1
        seen = {n: ObjectState(c, HALF[n]) for n, c in self.world.items()
                if n != self.held_object and n not in self.hidden}
        return seen, {n: 0.0 for n in self.hidden}

    def object_states(self):
        states = {n: ObjectState(c, HALF[n]) for n, c in self.world.items()}
        if self.held_object:   # vật đang giữ treo dưới platform, đi theo điểm đích cuối cùng
            x, y, z = self.moves[-1]
            n = self.held_object
            states[n] = ObjectState((x, y, z - 0.003 - HALF[n]), HALF[n])
        return states


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(te.time, 'sleep', lambda s: None)


def test_camera_pick_observes_first_and_trusts_gripper():
    robot = FakeRobot()
    logs = []
    te.TaskExecutor(robot, log=logs.append).pick('red_box')
    assert robot.moves[0] == OBSERVE_XYZ
    assert robot.held_object == 'red_box'
    assert any('giac hut xac nhan' in line for line in logs)


def test_place_while_holding_reuses_pre_pick_observation():
    robot = FakeRobot()
    ex = te.TaskExecutor(robot, log=lambda s: None)
    ex.pick('red_box')
    before = robot.observations
    ex.place('A')
    # Không đi quan sát khi đang giữ vật; chỉ quan sát 1 lần sau khi thả để kiểm chứng.
    assert robot.observations == before + 1
    assert robot.held_object == ''


def test_sort_in_camera_mode_fills_three_slots():
    robot = FakeRobot()
    logs = []
    te.TaskExecutor(robot, log=logs.append).sort()
    assert all(inside_bin_region(x, y) for x, y, _ in robot.world.values())
    assert any('Da don xong' in line for line in logs)


def test_unclear_target_is_refused_before_moving_to_it():
    robot = FakeRobot(hidden={'red_box'})
    with pytest.raises(TaskError, match='khong tin cay'):
        te.TaskExecutor(robot, log=lambda s: None).pick('red_box')
    assert robot.moves == [OBSERVE_XYZ]
    assert robot.held_object == ''


def test_sort_skips_unclear_object_and_says_so():
    robot = FakeRobot(hidden={'blue_sphere'})
    logs = []
    te.TaskExecutor(robot, log=logs.append).sort()
    assert not inside_bin_region(*robot.world['blue_sphere'][:2])
    assert any('camera chua thay ro: blue_sphere' in line for line in logs)


def test_ground_truth_mode_never_observes():
    robot = FakeRobot(source='ground_truth')
    te.TaskExecutor(robot, log=lambda s: None).pick_place('green_cylinder', 'B')
    assert robot.observations == 0
    assert OBSERVE_XYZ not in robot.moves
