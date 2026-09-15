"""
Mô tả cảnh gắp–thả phía ROS (thuần Python): vật, khay và các ô thả, trong hệ tọa độ robot.

Nguồn duy nhất cho launch, gripper_node và task_planner. Phía Gazebo vẫn phải khớp thủ công với
closed_loop_description/worlds/delta_objects_world.sdf và urdf/3dof_delta.gripper.xacro.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SceneObject:
    """Vật gắp được: tên model Gazebo, nửa chiều cao (m), tên gọi tắt khi nhập lệnh."""

    name: str
    half_height: float
    aliases: tuple


OBJECTS = (
    SceneObject('red_box', 0.015, ('red', 'box', 'do', 'hop', 'hop_do')),
    SceneObject('green_cylinder', 0.015, ('green', 'cylinder', 'xanhla', 'tru', 'tru_xanh')),
    SceneObject('blue_sphere', 0.015, ('blue', 'sphere', 'xanhduong', 'cau', 'cau_xanh')),
)

# Khay drop_bin (hệ robot): tâm, nửa bề rộng lòng khay, cao độ mặt đáy.
BIN_CENTER = (0.0375, 0.065)
BIN_INNER_HALF = 0.035
BIN_FLOOR_Z = -0.217

# Tâm các ô thả (x, y). Cách nhau >= 3.4 cm để vật 3 cm không chồng lên nhau.
BIN_SLOTS = {
    'A': (0.0205, 0.048),
    'B': (0.0545, 0.048),
    'C': (0.0205, 0.082),
}

# Khoảng rơi từ đáy vật tới đáy khay lúc nhả (m).
DROP_GAP = 0.005
