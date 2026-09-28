"""
Mô tả cảnh phía ROS (thuần Python): vật, khay, marker hiệu chuẩn — trong hệ tọa độ robot.

Nguồn duy nhất cho launch, gripper_node, task_planner và khối thị giác. Phía Gazebo vẫn phải khớp
thủ công với closed_loop_description/worlds/*.sdf và urdf/3dof_delta.gripper.xacro.

BẢN SAO SỐ THEO TỈ LỆ (Bước 10b, chốt 2026-09-30)
-------------------------------------------------
Vật thật là lon nước ngọt 320 ml: **Ø 57.5 mm, cao 147 mm**. Lon thật KHÔNG gắp được: vùng làm
việc của robot chỉ cao ~120 mm (bàn z = -0.22, trần ≈ -0.10) nên đỉnh lon rơi đúng vào trần, gắp
tới nơi cũng không nhấc lên được. Vì vậy cảnh ảo là bản thu nhỏ theo **SCALE = 2.5**, giữ nguyên
tỉ lệ hình dạng:

    kích thước ảo = kích thước thật / SCALE      vị trí ảo = vị trí thật / SCALE

Hệ quả (đã kiểm tra tầm với): lon ảo Ø 23 mm cao 58.8 mm; vùng làm việc thật Ø 48 cm (vừa bàn
60x120 cm); dung sai giác hút 12 mm ảo <=> 30 mm thật.

Tỉ lệ KHÔNG làm sai số ảo xấu đi: camera phủ vùng rộng gấp SCALE lần (mm/pixel xấu đi bấy nhiêu)
nhưng sai số lại chia cho SCALE khi quy về không gian ảo -> hai hiệu ứng triệt tiêu.
"""

from dataclasses import dataclass

# Tỉ lệ bản sao số: kích thước/vị trí THẬT chia cho giá trị này ra kích thước/vị trí ẢO.
SCALE = 2.5

# Kích thước lon THẬT (m) — dùng cho khối thị giác khi chạy với camera thật ở Bước 10b.
REAL_CAN_DIAMETER = 0.0575
REAL_CAN_HEIGHT = 0.147


def real_to_virtual(xy):
    """Đổi tọa độ (x, y) đo trên bàn THẬT sang tọa độ trong cảnh ảo."""
    return (xy[0] / SCALE, xy[1] / SCALE)


def virtual_to_real(xy):
    """Đổi tọa độ (x, y) trong cảnh ảo sang tọa độ trên bàn THẬT."""
    return (xy[0] * SCALE, xy[1] * SCALE)


@dataclass(frozen=True)
class SceneObject:
    """
    Vật gắp được.

    name: tên model Gazebo; half_height, half_width: NỬA kích thước trong cảnh ẢO (m);
    aliases: tên tắt khi nhập lệnh; home_xy: vị trí ban đầu (khớp <pose> trong world);
    color: lớp màu để camera phân loại (khóa trong color_detector.COLOR_CLASSES);
    shape: 'box' | 'cylinder' | 'sphere' — để dự đoán hình bóng trên ảnh.
    """

    name: str
    half_height: float
    aliases: tuple
    home_xy: tuple
    color: str
    shape: str
    half_width: float
    # Tỉ lệ DANH NGHĨA của hình bóng thực sự mang màu của vật, khi vật KHÔNG bị che.
    # Khối nhựa một màu = 1.0. Lon thì nắp nhôm bạc, vành chữ trắng và vành logo không mang màu
    # nên chỉ còn ~0.4 (đo trên ảnh mô phỏng 2026-09-30). Thiếu hệ số này thì mọi lon đều bị cờ
    # tin cậy coi là "bị che" và hệ thống từ chối gắp.
    color_fraction: float = 1.0


# ---------------------------------------------------------------- cảnh hiện tại: ba lon
# Lon ảo: Ø 0.023, cao 0.0588 (= kích thước thật / SCALE). Vị trí xuất phát nằm phía -X (gần
# camera), đều trong tầm với ở độ cao gắp (tool0 z = -0.1582 -> r_max ≈ 0.119).
# Phải khớp worlds/delta_cans_world.sdf.
CAN_HALF_HEIGHT = REAL_CAN_HEIGHT / 2 / SCALE      # 0.0294
CAN_HALF_WIDTH = REAL_CAN_DIAMETER / 2 / SCALE     # 0.0115

OBJECTS = (
    SceneObject('coca_can', CAN_HALF_HEIGHT, ('coca', 'cocacola', 'coke', 'do', 'red'),
                (-0.085, 0.0), 'red', 'cylinder', CAN_HALF_WIDTH, 0.43),
    SceneObject('pepsi_can', CAN_HALF_HEIGHT, ('pepsi', 'lam', 'xanhduong', 'blue'),
                (-0.045, 0.075), 'blue', 'cylinder', CAN_HALF_WIDTH, 0.39),
    SceneObject('sevenup_can', CAN_HALF_HEIGHT, ('7up', 'sevenup', 'luc', 'xanhla', 'green'),
                (-0.045, -0.075), 'green', 'cylinder', CAN_HALF_WIDTH, 0.39),
)

# Mặt bàn (hệ robot).
TABLE_Z = -0.22

# ---------------------------------------------------------------- ba khay phân loại
# MỖI LOẠI LON MỘT KHAY RIÊNG -> nhiệm vụ là PHÂN LOẠI THEO CHỦNG LOẠI, không phải xếp vào ô trống
# bất kỳ. Lòng khay 45x45 mm cho lon Ø 23 mm; thành dày 3 mm cao 15 mm; đáy cao hơn mặt bàn 3 mm.
# ⚠️ Ba khay màu XÁM TRUNG TÍNH trong world: khay màu đỏ/lục/lam sẽ bị camera nhận nhầm là lon.
BINS = {
    'coca_can': (0.075, -0.075),
    'pepsi_can': (0.075, 0.0),
    'sevenup_can': (0.075, 0.075),
}
BIN_INNER_HALF = 0.0225
BIN_OUTER_HALF = 0.0255
BIN_FLOOR_Z = -0.217
BIN_WALL_TOP_Z = -0.205


@dataclass(frozen=True)
class BinLayout:
    """Hình học khay, gom lại để khối thị giác dùng được cho cả cảnh cũ lẫn cảnh mới."""

    centers: tuple      # ((x, y), ...) tâm các khay
    inner_half: float   # nửa bề rộng lòng khay
    outer_half: float   # nửa bề rộng tính cả thành
    floor_z: float      # cao độ mặt đáy khay


BIN_LAYOUT = BinLayout(tuple(BINS.values()), BIN_INNER_HALF, BIN_OUTER_HALF, BIN_FLOOR_Z)

# Khoảng rơi từ đáy vật tới bề mặt (đáy khay / mặt bàn) lúc nhả (m).
DROP_GAP = 0.005

# Đặt vật ra bàn: tâm cách tâm vật khác >= MIN_SEPARATION và mép vật cách thành ngoài khay
# >= BIN_CLEARANCE.
MIN_SEPARATION = 0.035
OBJECT_HALF_WIDTH = CAN_HALF_WIDTH
BIN_CLEARANCE = 0.005

# ---------------------------------------------------------------- hiệu chuẩn camera (Bước 8.3)
# Marker ArUco (DICT_4X4_50) dán phẳng trên mặt bàn, vị trí biết trước trong hệ robot.
# Phải khớp model `calib_markers` trong world.
# ⚠️ Ở Bước 10b với bàn thật, marker KHÔNG đặt theo (tọa độ ảo x SCALE): bố trí đó rộng
# 675x725 mm, không vừa bàn 60x120 cm. Sẽ định nghĩa bố trí thật riêng, rồi áp SCALE ở phần mềm.
CALIB_ARUCO_DICT = 'DICT_4X4_50'
CALIB_MARKER_SIZE = 0.05
CALIB_MARKER_THICKNESS = 0.001
CALIB_MARKER_Z = TABLE_Z + CALIB_MARKER_THICKNESS
CALIB_MARKERS = {
    0: (-0.130, 0.075),
    1: (-0.130, -0.075),
    2: (-0.025, 0.145),
    3: (-0.025, -0.145),
    4: (0.140, 0.085),
    5: (0.140, -0.085),
}

# Pose THẬT của camera mô phỏng (hệ robot). CHỈ dùng để ĐÁNH GIÁ hiệu chuẩn.
SIDE_CAMERA_GT_XYZ = (-0.40, 0.0, 0.03)
SIDE_CAMERA_GT_RPY = (0.0, 0.558599, 0.0)

# Tư thế quan sát (Bước 9): trước khi đọc vị trí vật từ camera, robot nâng platform lên cao ở giữa
# để không che tầm nhìn.
OBSERVE_XYZ = (0.0, 0.0, -0.11)

# ---------------------------------------------------------------- cảnh CŨ (ba khối vuông)
# Giữ lại vì: (a) worlds/delta_objects_world.sdf vẫn dùng để tái lập kết quả Bước 6–9;
# (b) mọi ảnh mẫu trong test/data/ và bộ dữ liệu datasets/vision_eval/ đều chụp ở cảnh này, nên
# các test dùng ảnh đó phải mô tả đúng hình học cũ. KHÔNG dùng cho cảnh lon.
LEGACY_OBJECTS = (
    SceneObject('red_box', 0.015, ('red', 'box', 'do', 'hop', 'hop_do'), (0.06, 0.0), 'red',
                'box', 0.015),
    SceneObject('green_cylinder', 0.015, ('green', 'cylinder', 'xanhla', 'tru', 'tru_xanh'),
                (-0.03, 0.052), 'green', 'cylinder', 0.015),
    SceneObject('blue_sphere', 0.015, ('blue', 'sphere', 'xanhduong', 'cau', 'cau_xanh'),
                (-0.03, -0.052), 'blue', 'sphere', 0.015),
)
LEGACY_BIN_CENTER = (0.0375, 0.065)
LEGACY_BIN_INNER_HALF = 0.035
LEGACY_BIN_OUTER_HALF = 0.038
LEGACY_BIN_SLOTS = {
    'A': (0.0205, 0.048),
    'B': (0.0545, 0.048),
    'C': (0.0205, 0.082),
}


# Hình học khay của cảnh cũ — dùng khi phân tích ảnh/bộ dữ liệu chụp ở thế giới khối vuông.
LEGACY_BIN_LAYOUT = BinLayout((LEGACY_BIN_CENTER,), LEGACY_BIN_INNER_HALF,
                              LEGACY_BIN_OUTER_HALF, BIN_FLOOR_Z)
