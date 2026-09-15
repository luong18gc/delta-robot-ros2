"""
Mô tả cảnh gắp–thả phía ROS (thuần Python): vật, khay và các ô thả, trong hệ tọa độ robot.

Nguồn duy nhất cho launch, gripper_node và task_planner. Phía Gazebo vẫn phải khớp thủ công với
closed_loop_description/worlds/delta_objects_world.sdf và urdf/3dof_delta.gripper.xacro.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SceneObject:
    """
    Vật gắp được.

    name: tên model Gazebo; half_height: nửa chiều cao (m); aliases: tên tắt khi nhập lệnh;
    home_xy: vị trí ban đầu trên bàn (khớp <pose> trong world) — dùng cho lay_ra / reset.
    """

    name: str
    half_height: float
    aliases: tuple
    home_xy: tuple


OBJECTS = (
    SceneObject('red_box', 0.015, ('red', 'box', 'do', 'hop', 'hop_do'), (0.06, 0.0)),
    SceneObject('green_cylinder', 0.015, ('green', 'cylinder', 'xanhla', 'tru', 'tru_xanh'),
                (-0.03, 0.052)),
    SceneObject('blue_sphere', 0.015, ('blue', 'sphere', 'xanhduong', 'cau', 'cau_xanh'),
                (-0.03, -0.052)),
)

# Mặt bàn (hệ robot).
TABLE_Z = -0.22

# Khay drop_bin (hệ robot): tâm, nửa bề rộng lòng khay, nửa bề rộng ngoài (tính cả thành),
# cao độ mặt đáy.
BIN_CENTER = (0.0375, 0.065)
BIN_INNER_HALF = 0.035
BIN_OUTER_HALF = 0.038
BIN_FLOOR_Z = -0.217

# Tâm các ô thả (x, y). Cách nhau >= 3.4 cm để vật 3 cm không chồng lên nhau.
BIN_SLOTS = {
    'A': (0.0205, 0.048),
    'B': (0.0545, 0.048),
    'C': (0.0205, 0.082),
}

# Khoảng rơi từ đáy vật tới bề mặt (đáy khay / mặt bàn) lúc nhả (m).
DROP_GAP = 0.005

# Đặt vật ra bàn: tâm cách tâm vật khác >= MIN_SEPARATION (vật 3 cm -> khe >= 5 mm) và mép vật
# cách thành ngoài khay >= BIN_CLEARANCE.
MIN_SEPARATION = 0.035
OBJECT_HALF_WIDTH = 0.015
BIN_CLEARANCE = 0.005
