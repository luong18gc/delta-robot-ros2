"""Kiểm thử máy trạng thái vòng băng tải → gắp (không cần ROS, không cần phần cứng)."""

from delta_controller.conveyor_cycle import (
    BAM_LON, CHO_LON, ConveyorCycle, DANG_CHAY, DANG_GAP, DUNG_BANG, hover_point, NHA_QUYEN,
)
from delta_controller.scene import BELT_CENTER, BELT_PICK_XY, BELT_TOP_Z, OBJECTS

CAN = OBJECTS[0].name
Z = BELT_TOP_Z + OBJECTS[0].half_height


def on_belt_at(y, name=CAN, score=1.0):
    """Một lon đứng trên băng tại tọa độ y (hệ ảo)."""
    return {name: (BELT_CENTER[0], y, Z, score)}


def loading_end():
    """Lon vừa được đặt ở đầu nạp."""
    return on_belt_at(BELT_CENTER[1] - 0.03)


def at_pick():
    """Lon đã tới điểm gắp."""
    return on_belt_at(BELT_PICK_XY[1])


def tool_over(cans, name=CAN):
    """tool0 đang ở đúng điểm bám trên nắp lon."""
    x, y, z, _ = cans[name]
    return hover_point(name, x, y, z)


def running(cycle=None, t=0.0):
    """Đưa máy trạng thái tới DANG_CHAY: thấy lon, đầu hút đã vào vị trí, băng đã chạy."""
    cycle = cycle or ConveyorCycle()
    cans = loading_end()
    cycle.step(t, cans)                                   # -> BAM_LON
    cycle.step(t, cans, tool=tool_over(cans))             # -> DANG_CHAY
    return cycle


def picking(cycle=None, t=5.0):
    """Đưa tới DANG_GAP: lon đã tới điểm gắp, đã đứng yên, đã giao quyền cho mô phỏng."""
    cycle = running(cycle)
    cycle.step(1.0, at_pick(), tool=tool_over(at_pick()))      # -> DUNG_BANG
    cycle.step(t, at_pick(), tool=tool_over(at_pick()))        # -> DANG_GAP
    return cycle


def released(cycle=None):
    """Đưa tới NHA_QUYEN: robot đã thả lon vào khay."""
    cycle = picking(cycle)
    cycle.step(6.0, at_pick(), holding='')
    return cycle


# ---------------------------------------------------------------- khởi đầu

def test_bat_dau_o_cho_lon():
    assert ConveyorCycle().state == CHO_LON


def test_ban_trong_thi_khong_chay_bang():
    action = ConveyorCycle().step(0.0, {})
    assert action.belt is False and action.pick is None and action.track is None


def test_lon_score_0_khong_duoc_tinh():
    """Ước lượng không tin cậy thì coi như không thấy — không khởi động theo số liệu xấu."""
    cycle = ConveyorCycle()
    action = cycle.step(0.0, on_belt_at(BELT_CENTER[1] - 0.03, score=0.0))
    assert action.belt is False and cycle.state == CHO_LON


def test_lon_ngoai_bang_khong_khoi_dong_vong():
    """Lon đứng trên BÀN (không phải trên băng) không được coi là lon chờ chuyển."""
    cycle = ConveyorCycle()
    far = {CAN: (BELT_CENTER[0] + 0.2, BELT_CENTER[1], Z, 1.0)}
    assert cycle.step(0.0, far).belt is False
    assert cycle.state == CHO_LON


# ---------------------------------------------------------------- bám lon

def test_thay_lon_thi_dua_dau_hut_toi_truoc_chu_chua_chay_bang():
    cycle = ConveyorCycle()
    action = cycle.step(0.0, loading_end())
    assert cycle.state == BAM_LON
    assert action.belt is False, 'chua duoc chay bang khi dau hut chua vao vi tri'
    assert action.track is not None


def test_diem_bam_nam_tren_nap_lon():
    cycle = ConveyorCycle()
    action = cycle.step(0.0, loading_end())
    x, y, z, _ = loading_end()[CAN]
    assert action.track[:2] == (x, y)
    assert action.track[2] > z + OBJECTS[0].half_height, 'phai cao hon nap lon'


def test_dau_hut_chua_toi_thi_van_chua_chay_bang():
    cycle = ConveyorCycle()
    cans = loading_end()
    cycle.step(0.0, cans)
    far = (0.0, 0.0, -0.11)                     # robot còn ở tư thế quan sát
    action = cycle.step(0.1, cans, tool=far)
    assert action.belt is False and cycle.state == BAM_LON


def test_dau_hut_vao_vi_tri_thi_cho_bang_chay():
    cycle = ConveyorCycle()
    cans = loading_end()
    cycle.step(0.0, cans)
    action = cycle.step(0.1, cans, tool=tool_over(cans))
    assert action.belt is True and cycle.state == DANG_CHAY


def test_bam_theo_lon_trong_suot_hanh_trinh():
    """Điểm bám phải đi theo lon, không đứng yên một chỗ."""
    cycle = running()
    seen = []
    for i in range(5):
        cans = on_belt_at(BELT_CENTER[1] - 0.03 + 0.004 * i)
        action = cycle.step(1.0 + i, cans, tool=tool_over(cans))
        seen.append(action.track[1])
    assert seen == sorted(seen) and seen[0] < seen[-1], 'diem bam phai di theo lon'


def test_mat_dau_lon_luc_dang_bam_thi_quay_lai_cho():
    cycle = ConveyorCycle()
    cycle.step(0.0, loading_end())
    action = cycle.step(0.1, {})
    assert cycle.state == CHO_LON and action.belt is False


# ---------------------------------------------------------------- tới nơi và gắp

def test_lon_toi_noi_thi_dung_bang():
    cycle = running()
    action = cycle.step(1.0, at_pick(), tool=tool_over(at_pick()))
    assert action.belt is False and cycle.state == DUNG_BANG


def test_khong_gap_ngay_ma_cho_lon_dung_han():
    cycle = running()
    cycle.step(1.0, at_pick(), tool=tool_over(at_pick()))
    assert cycle.step(1.2, at_pick()).pick is None          # chưa đủ settle_sec
    assert cycle.step(5.0, at_pick()).pick == CAN


def test_lon_dat_san_o_cuoi_bang_thi_khong_chay_bang():
    cycle = ConveyorCycle()
    cans = at_pick()
    cycle.step(0.0, cans)
    action = cycle.step(0.1, cans, tool=tool_over(cans))
    assert action.belt is False and cycle.state == DUNG_BANG


def test_het_gio_thi_dung_bang_va_bao():
    cycle = running()
    action = cycle.step(cycle.timeout_sec + 1.0, loading_end())
    assert action.belt is False and 'HET GIO' in action.message
    assert cycle.state == CHO_LON


def test_mat_dau_thoang_qua_thi_van_chay():
    cycle = running()
    action = cycle.step(1.0, {})
    assert action.belt is None and cycle.state == DANG_CHAY


# ---------------------------------------------------------------- giao và nhận quyền

def test_dong_bang_lon_tu_luc_giao_cho_mo_phong():
    cycle = picking()
    assert cycle.state == DANG_GAP


def test_van_dong_bang_trong_suot_luc_giu_vat():
    cycle = picking()
    action = cycle.step(6.0, {}, holding=CAN)
    assert action.frozen == (CAN,) and cycle.state == DANG_GAP


def test_tha_xong_thi_sang_nha_quyen_va_van_dong_bang():
    cycle = released()
    assert cycle.state == NHA_QUYEN
    assert cycle.step(7.0, at_pick()).frozen == (CAN,)


def test_lon_that_con_tren_bang_thi_khong_nhan_lai_quyen():
    """Bất biến quan trọng nhất: camera không được kéo lon ảo từ khay về lại băng."""
    cycle = released()
    for t in range(7, 30):
        action = cycle.step(float(t), at_pick())
        assert action.frozen == (CAN,), 'van phai dong bang khi lon that con tren bang'
        assert cycle.state == NHA_QUYEN


def test_nhac_lon_that_ra_thi_nhan_lai_quyen_sau_vai_khung():
    cycle = released()
    for i in range(cycle.confirm_frames - 1):
        assert cycle.step(7.0 + i, {}).frozen == (CAN,)      # chưa đủ khung xác nhận
    action = cycle.step(20.0, {})
    assert action.frozen == () and cycle.state == CHO_LON and cycle.target is None


def test_lon_thoang_an_roi_hien_lai_thi_khong_nhan_lai_quyen():
    """Tay người lướt ngang che lon một khung không được tính là 'đã nhấc ra'."""
    cycle = released()
    cycle.step(7.0, {})
    cycle.step(8.0, {})
    cycle.step(9.0, at_pick())                  # lon hiện lại -> đếm lại từ đầu
    for i in range(cycle.confirm_frames - 1):
        assert cycle.step(10.0 + i, {}).frozen == (CAN,)
    assert cycle.step(20.0, {}).frozen == ()


def test_mot_vong_tron_ven_roi_quay_lai_dau():
    cycle = released()
    for i in range(cycle.confirm_frames):
        cycle.step(8.0 + i, {})
    assert cycle.state == CHO_LON
    assert cycle.step(20.0, loading_end()).track is not None     # sẵn sàng lon kế tiếp


def test_vung_dat_lon_loai_day_dong_co_nhung_giu_mat_bang():
    """Lọc hình học: dây động cơ ngoài vùng bị loại, cả mặt băng vẫn nằm trong vùng."""
    from delta_controller.scene import (
        BELT_LENGTH, BELT_WIDTH, in_object_area, SCALE,
    )

    def at_real(x_mm, y_mm):
        return in_object_area(x_mm / 1000.0 / SCALE, y_mm / 1000.0 / SCALE)

    assert not at_real(-173, 123), 'day dong co mau cam phai bi loai'
    assert at_real(88, 95), 'lon that tren bang phai duoc giu'
    assert in_object_area(*BELT_PICK_XY), 'diem gap phai nam trong vung'
    for sx in (-1, 1):
        for sy in (-1, 1):
            corner = (BELT_CENTER[0] + sx * BELT_WIDTH / 2,
                      BELT_CENTER[1] + sy * BELT_LENGTH / 2)
            assert in_object_area(*corner), f'goc mat bang {corner} phai nam trong vung'
