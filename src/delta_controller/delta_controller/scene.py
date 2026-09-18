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
    home_xy: vị trí ban đầu trên bàn (khớp <pose> trong world) — dùng cho lay_ra / reset;
    color: màu vật, để bộ nhận dạng camera biết mảng màu nào là vật nào;
    shape, half_width: hình dạng và nửa bề rộng, để dự đoán hình bóng vật trên ảnh.
    """

    name: str
    half_height: float
    aliases: tuple
    home_xy: tuple
    color: str   # lớp màu để camera nhận dạng (khóa trong color_detector.COLOR_CLASSES)
    shape: str   # 'box' | 'cylinder' | 'sphere' — để dự đoán hình bóng trên ảnh (Bước 8.5)
    half_width: float   # nửa cạnh hộp / bán kính trụ, cầu (m)


OBJECTS = (
    SceneObject('red_box', 0.015, ('red', 'box', 'do', 'hop', 'hop_do'), (0.06, 0.0), 'red',
                'box', 0.015),
    SceneObject('green_cylinder', 0.015, ('green', 'cylinder', 'xanhla', 'tru', 'tru_xanh'),
                (-0.03, 0.052), 'green', 'cylinder', 0.015),
    SceneObject('blue_sphere', 0.015, ('blue', 'sphere', 'xanhduong', 'cau', 'cau_xanh'),
                (-0.03, -0.052), 'blue', 'sphere', 0.015),
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

# ---------------------------------------------------------------- hiệu chuẩn camera (Bước 8.3)
# Marker ArUco (từ điển DICT_4X4_50) dán phẳng trên mặt bàn, vị trí biết trước trong hệ robot.
# Camera nhận dạng số hiệu marker -> cặp điểm 3D (ở đây) <-> 2D (trên ảnh) -> solvePnP ra vị trí và
# hướng camera. Dùng TÂM marker (không dùng góc) nên không phụ thuộc chiều dán marker.
# Phải khớp với model `calib_markers` trong worlds/delta_objects_world.sdf.
CALIB_ARUCO_DICT = 'DICT_4X4_50'
CALIB_MARKER_SIZE = 0.05         # cạnh ô vuông đen (m)
CALIB_MARKER_THICKNESS = 0.001   # marker là tấm dày 1 mm đặt trên mặt bàn
CALIB_MARKER_Z = TABLE_Z + CALIB_MARKER_THICKNESS
CALIB_MARKERS = {
    0: (-0.130, 0.075),
    1: (-0.130, -0.075),
    2: (-0.025, 0.145),
    3: (-0.025, -0.145),
    4: (0.140, 0.085),
    5: (0.140, -0.085),
}

# Pose THẬT của camera mô phỏng (hệ robot = world - (0, 0, 1)), trích từ model `side_camera` trong
# world. CHỈ dùng để ĐÁNH GIÁ kết quả hiệu chuẩn — hệ thống không được dùng giá trị này
# để điều khiển.
SIDE_CAMERA_GT_XYZ = (-0.40, 0.0, 0.03)
SIDE_CAMERA_GT_RPY = (0.0, 0.558599, 0.0)

# Tư thế quan sát (Bước 9): trước khi đọc vị trí vật từ camera, robot đưa platform lên cao ở giữa
# để không che tầm nhìn. Đo 2026-09-18: hộp đỏ tại x = 120 mm, robot ở home -> bị platform che
# (score 0, sai 17 mm); platform ở z -0.105…-0.11 -> score 0.99, sai 0.3 mm.
OBSERVE_XYZ = (0.0, 0.0, -0.11)
