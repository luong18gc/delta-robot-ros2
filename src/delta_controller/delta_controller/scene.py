"""
Mô tả cảnh phía ROS (thuần Python): vật, khay, marker hiệu chuẩn — trong hệ tọa độ robot.

Nguồn duy nhất cho launch, gripper_node, task_planner và khối thị giác. Phía Gazebo vẫn phải khớp
thủ công với closed_loop_description/worlds/*.sdf và urdf/3dof_delta.gripper.xacro.

BẢN SAO SỐ THEO TỈ LỆ (Bước 10b, chốt 2026-09-30)
-------------------------------------------------
Vật thật là lon nước ngọt 320 ml: **Ø 57.5 mm, cao 147 mm**. Lon thật KHÔNG gắp được: vùng làm
việc của robot chỉ cao ~120 mm (bàn z = -0.22, trần ≈ -0.10) nên đỉnh lon rơi đúng vào trần, gắp
tới nơi cũng không nhấc lên được. Vì vậy cảnh ảo là bản thu nhỏ theo **SCALE = 3.0**, giữ nguyên
tỉ lệ hình dạng:

    kích thước ảo = kích thước thật / SCALE      vị trí ảo = vị trí thật / SCALE

Hệ quả (đã kiểm tra tầm với): lon ảo Ø 19.2 mm cao 49 mm; vùng làm việc thật Ø 58 cm (vừa bàn
60x120 cm); dung sai giác hút 12 mm ảo <=> 36 mm thật.

⚠️ Vì sao 3.0 chứ không phải 2.5 (đo 2026-09-29): robot phải NHẤC LON QUA ĐẦU lon khác khi mang
tới khay. Điều kiện: tool0 >= đỉnh lon đứng + nửa bề dày platform + chiều cao lon. Với k = 2.5
(lon cao 58.8 mm) cần tool0 >= -0.0994, VƯỢT trần vùng làm việc (-0.10) -> không thể, lon đang
mang chồng 30.6 mm vào lon đang đứng và ĐÁNH ĐỔ nó. Với k = 3.0 (lon cao 49 mm) chỉ cần
tool0 >= -0.119, khả thi.

Tỉ lệ KHÔNG làm sai số ảo xấu đi: camera phủ vùng rộng gấp SCALE lần (mm/pixel xấu đi bấy nhiêu)
nhưng sai số lại chia cho SCALE khi quy về không gian ảo -> hai hiệu ứng triệt tiêu.
"""

from dataclasses import dataclass, replace

# Tỉ lệ bản sao số: kích thước/vị trí THẬT chia cho giá trị này ra kích thước/vị trí ẢO.
SCALE = 3.0

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
    # Khối nhựa một màu = 1.0. Lon thì nắp nhôm bạc, vành chữ trắng và vành logo không mang màu.
    # Thiếu hệ số này thì mọi lon đều bị cờ tin cậy coi là "bị che" và hệ thống từ chối gắp.
    # Đo bằng scripts/measure_color_fraction.py (9 vị trí trong tầm với, 2026-09-29):
    # coca 0.67–0.80, pepsi 0.56–0.71, 7up 0.55–0.71. Tỉ lệ KHÔNG phải hằng số vì phép đóng hình
    # thái học (kernel 5 px) lấp một phần vành nhãn: lon càng ở XA camera, hình càng nhỏ, vành
    # càng bị lấp nhiều -> tỉ lệ màu càng cao. Lấy giá trị NHỎ NHẤT đo được để lon lành lặn không
    # bao giờ bị từ chối; đổi lại cờ tin cậy chỉ bắt được mức che > ~25%.
    color_fraction: float = 1.0
    # Khoảng từ ĐỈNH vật xuống tới mép trên của phần MANG MÀU (m). Lon có nắp nhôm bạc dày 2 mm
    # nên mép trên của vùng màu thấp hơn đỉnh lon bấy nhiêu; không trừ phần này thì phép khớp mép
    # trên (dùng cho vật trong khay) bị lệch hệ thống — đo 2026-09-29: sai 11–15 mm.
    color_top_margin: float = 0.0


# ---------------------------------------------------------------- cảnh hiện tại: ba lon
# Lon ảo: Ø 0.023, cao 0.0588 (= kích thước thật / SCALE). Vị trí xuất phát nằm phía -X (gần
# camera), đều trong tầm với ở độ cao gắp (tool0 z = -0.1582 -> r_max ≈ 0.119).
# Phải khớp worlds/delta_cans_world.sdf.
CAN_HALF_HEIGHT = REAL_CAN_HEIGHT / 2 / SCALE      # 0.0294
CAN_HALF_WIDTH = REAL_CAN_DIAMETER / 2 / SCALE     # 0.0115

OBJECTS = (
    SceneObject('coca_can', CAN_HALF_HEIGHT, ('coca', 'cocacola', 'coke', 'do', 'red'),
                (0.06, -0.075), 'red', 'cylinder', CAN_HALF_WIDTH, 0.66, 0.0017),
    SceneObject('pepsi_can', CAN_HALF_HEIGHT, ('pepsi', 'lam', 'xanhduong', 'blue'),
                (0.09, 0.0), 'blue', 'cylinder', CAN_HALF_WIDTH, 0.55, 0.0017),
    SceneObject('sevenup_can', CAN_HALF_HEIGHT, ('7up', 'sevenup', 'luc', 'xanhla', 'green'),
                (0.06, 0.075), 'green', 'cylinder', CAN_HALF_WIDTH, 0.55, 0.0017),
)

# Mặt bàn (hệ robot).
TABLE_Z = -0.22

# ---------------------------------------------------------------- ba khay phân loại
# MỖI LOẠI LON MỘT KHAY RIÊNG -> nhiệm vụ là PHÂN LOẠI THEO CHỦNG LOẠI, không phải xếp vào ô trống
# bất kỳ. Lòng khay 45x45 mm cho lon Ø 23 mm; thành dày 3 mm cao 15 mm; đáy cao hơn mặt bàn 3 mm.
# ⚠️ Ba khay màu XÁM TRUNG TÍNH trong world: khay màu đỏ/lục/lam sẽ bị camera nhận nhầm là lon.
# ⚠️ KHAY đặt phía -X (PHÍA CAMERA), LON đặt phía +X. Tia nhìn từ camera tới khay chỉ quét khoảng
# x từ -0.40 tới -0.06 nên KHÔNG BAO GIỜ đi qua robot. Hai bố trí sai đã thử (đo 2026-09-29):
# khay xếp theo trục Y tại x = +0.075 -> khay giữa nằm sau thân robot, ước lượng sai 18–33 mm;
# khay xếp theo trục X tại y = -0.08 -> ba khay nằm gần cùng hướng nhìn, lon trong khay che nhau,
# sai 7–18 mm.
BINS = {
    'coca_can': (-0.06, -0.075),
    'pepsi_can': (-0.06, 0.0),
    'sevenup_can': (-0.06, 0.075),
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


# ---------------------------------------------------------------- bàn THẬT (Bước 10a/10b)
# Bàn thật 600 x 1200 mm, camera nhìn từ phía -X. Trên bàn thật CHỈ có lon và marker: ba khay là
# vật ẢO, robot chỉ thao tác trong mô phỏng.
REAL_TABLE = (0.600, 1.200)     # (bề rộng theo Y, chiều dài theo X)

# Vùng đặt lon THẬT. Quy về ảo (chia SCALE) phải nằm trong tầm với ở độ cao gắp (r <= 0.119).
# ⚠️ Đo lại 2026-10-06 TỪ TƯ THẾ CAMERA THẬT (lùi 553, cao 628, chúc 46.1°) chứ không từ hình học
# dự kiến ban đầu (lùi 900, cao 545): giá đỡ thật gần và dốc hơn nên phần XA của bàn trượt khỏi mép
# trên khung hình. Quét toàn bàn, đòi cả ĐÁY lẫn ĐỈNH lon nằm trong khung với lề 25 px, được
# x −100…+240, y ±300 — và lệch (ở x = +220 chỉ còn y ≥ +60 vì camera hơi xoay). Lấy vùng vuông
# nằm gọn bên trong. Bộ cũ x 0…280 làm ĐỈNH lon bị cắt ở x = 260 và mọi phép đo ra rỗng.
REAL_OBJECT_AREA_X = (-0.060, 0.160)    # ảo: -0.020 .. 0.053
REAL_OBJECT_AREA_Y = (-0.180, 0.180)    # ảo: -0.060 .. 0.060
# Góc xa nhất quy về ảo là r = 103 mm, còn dư so với tầm với 119 mm ở độ cao gắp.

# Marker trên bàn THẬT — bao quanh vùng đặt lon, cách mép bàn >= 10 mm.
# ⚠️ KHÔNG phải CALIB_MARKERS nhân SCALE: bố trí ảo nhân 3 trải 810 x 870 mm, không vừa bàn rộng
# 600 mm. Bố trí thật được chọn riêng; phần mềm quy về hệ ảo bằng cách CHIA SCALE.
REAL_CALIB_MARKER_SIZE = 0.060          # ô đen 60 mm (ảo 20 mm) — camera cách ~0.7 m thấy rõ
REAL_CALIB_MARKERS = {
    0: (-0.080, 0.250),
    1: (-0.080, -0.250),
    2: (0.160, 0.250),
    3: (0.160, -0.250),
    4: (0.400, 0.230),
    5: (0.400, -0.230),
}


# Lon THẬT dùng bộ nhận dạng TÁCH NỀN TRƯỚC (object_detector), nên mặt nạ thu được CHÍNH LÀ hình
# bóng vật — tỉ lệ màu danh nghĩa bằng 1, không phải hệ số phải đi đo.
#
# Trước đó thử dùng nhận dạng theo màu cho lon thật và phải khai hệ số riêng (coca 0.55, pepsi
# 0.27, 7up 0.15) vì lon thật mang màu thành VÀNH chứ không phải thân đặc như lon ảo. Cách đó
# hỏng ở chỗ sâu hơn: mặt nạ màu không phải hình bóng, nên mép đáy không phải đáy lon. Đo
# 2026-10-05 trên lon đứng YÊN: nhận theo màu cho lon 7Up tỉ lệ cao/rộng 0.93 (lon thật là 2.5)
# và ước lượng nhảy 48 mm giữa hai khung; tách nền trước cho 2.65 và diện tích ba lon xấp xỉ bằng
# nhau (22 240 / 22 261 / 28 449 px) đúng như ba vật cùng kích thước.
REAL_OBJECTS = tuple(replace(o, color_fraction=1.0, color_top_margin=0.0) for o in OBJECTS)

# Vùng ẢNH đáng xét, cho theo tọa độ bàn THẬT (mm): bao trọn bố trí marker và vùng đặt lon, chừa
# lề. Mọi thứ ngoài vùng này (tường, sàn nhà, mép bàn) bị loại bằng HÌNH HỌC — không phụ thuộc màu
# sắc hay ánh sáng. Đo 2026-10-05: tường + sàn chiếm 18% khung hình; hôm đó vô hại (S = 57 < 90)
# nhưng ở lab tường từng bị nhận là vật xanh lá (S ≈ 113), nên không thể trông vào may mắn.
# ⚠️ Vùng xét phải nằm GỌN TRONG mặt bàn, và KHÔNG suy ra được từ bề rộng bàn: trục X kẻ trên bàn
# không song song với mép bàn, nên đường y = hằng số vẫn cắt qua mép dù |y| < 300. Đo 2026-10-06:
# ±310 rồi ±280 đều còn với ra nền gạch sáng, dải nền đó NỐI LIỀN với lon Coca thành một vùng
# bbox phủ gần hết khung hình, tỉ lệ nhìn thấy vọt lên 3.74 và mọi ước lượng bị loại.
REAL_ROI_X = (-120.0, 240.0)
REAL_ROI_Y = (-230.0, 230.0)


def real_roi_virtual():
    """4 góc vùng đáng xét, quy về hệ ảo (m)."""
    return tuple((x / 1000.0 / SCALE, y / 1000.0 / SCALE)
                 for x in REAL_ROI_X for y in REAL_ROI_Y)


def real_calib_markers_virtual():
    """
    Tọa độ marker THẬT quy về hệ ẢO (chia SCALE) — đây là thứ đưa vào PnP khi hiệu chuẩn.

    Vì sao chia SCALE ngay ở bước hiệu chuẩn thay vì chia kết quả về sau: thu nhỏ TOÀN BỘ thế giới
    k lần chỉ làm vectơ tịnh tiến của camera chia cho k, còn ma trận nội tham số, hệ số méo và
    phép chiếu thì không đổi. Nên PnP nhận tọa độ ảo sẽ trả về một camera "ảo", và cả khối thị
    giác sẵn có (pixel_to_plane, hình bóng dự đoán, khay, mặt bàn z = TABLE_Z) chạy nguyên vẹn
    trong hệ ảo, KHÔNG phải sửa chỗ nào. Đổi lại vị trí camera in ra nhỏ hơn thật k lần — chỉ ảnh
    hưởng lúc báo cáo, không ảnh hưởng phép đo.
    """
    return {i: (x / SCALE, y / SCALE) for i, (x, y) in REAL_CALIB_MARKERS.items()}
