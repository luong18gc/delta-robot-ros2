"""Kiểm thử máy trạng thái vòng băng tải → gắp (không cần ROS, không cần phần cứng)."""

from delta_controller.conveyor_cycle import (
    CHO_LON, ConveyorCycle, DANG_CHAY, DANG_GAP, DUNG_BANG, NHA_QUYEN,
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


def test_bat_dau_o_cho_lon():
    assert ConveyorCycle().state == CHO_LON


def test_ban_trong_thi_khong_chay_bang():
    action = ConveyorCycle().step(0.0, {})
    assert action.belt is False and action.pick is None


def test_dat_lon_vao_dau_nap_thi_cho_bang_chay():
    cycle = ConveyorCycle()
    action = cycle.step(0.0, loading_end())
    assert action.belt is True
    assert cycle.state == DANG_CHAY and cycle.target == CAN


def test_lon_toi_noi_thi_dung_bang():
    cycle = ConveyorCycle()
    cycle.step(0.0, loading_end())
    action = cycle.step(1.0, at_pick())
    assert action.belt is False and cycle.state == DUNG_BANG


def test_khong_gap_ngay_ma_cho_lon_dung_han():
    cycle = ConveyorCycle()
    cycle.step(0.0, loading_end())
    cycle.step(1.0, at_pick())
    assert cycle.step(1.2, at_pick()).pick is None          # chưa đủ settle_sec
    assert cycle.step(5.0, at_pick()).pick == CAN


def test_lon_dat_san_o_cuoi_bang_thi_khong_chay_bang():
    cycle = ConveyorCycle()
    action = cycle.step(0.0, at_pick())
    assert action.belt is False and cycle.state == DUNG_BANG


def test_het_gio_thi_dung_bang_va_bao():
    cycle = ConveyorCycle()
    cycle.step(0.0, loading_end())
    action = cycle.step(cycle.timeout_sec + 1.0, loading_end())
    assert action.belt is False and 'HET GIO' in action.message
    assert cycle.state == CHO_LON


def test_mat_dau_thoang_qua_thi_van_chay():
    cycle = ConveyorCycle()
    cycle.step(0.0, loading_end())
    action = cycle.step(1.0, {})
    assert action.belt is None and cycle.state == DANG_CHAY


def test_lon_score_0_khong_duoc_tinh():
    """Ước lượng không tin cậy thì coi như không thấy — không khởi động băng theo số liệu xấu."""
    cycle = ConveyorCycle()
    action = cycle.step(0.0, on_belt_at(BELT_CENTER[1] - 0.03, score=0.0))
    assert action.belt is False and cycle.state == CHO_LON


def test_dong_bang_lon_tu_luc_giao_cho_mo_phong():
    cycle = ConveyorCycle()
    cycle.step(0.0, loading_end())
    cycle.step(1.0, at_pick())
    action = cycle.step(5.0, at_pick())
    assert action.frozen == (CAN,) and cycle.state == DANG_GAP


def test_van_dong_bang_trong_suot_luc_giu_vat():
    cycle = ConveyorCycle()
    cycle.step(0.0, loading_end())
    cycle.step(1.0, at_pick())
    cycle.step(5.0, at_pick())
    action = cycle.step(6.0, {}, holding=CAN)
    assert action.frozen == (CAN,) and cycle.state == DANG_GAP


def test_tha_xong_thi_sang_nha_quyen_va_van_dong_bang():
    cycle = ConveyorCycle()
    cycle.step(0.0, loading_end())
    cycle.step(1.0, at_pick())
    cycle.step(5.0, at_pick())
    action = cycle.step(6.0, at_pick(), holding='')
    assert cycle.state == NHA_QUYEN and action.frozen == (CAN,)


def test_lon_that_con_tren_bang_thi_khong_nhan_lai_quyen():
    """Đây là bất biến quan trọng nhất: camera không được kéo lon ảo từ khay về lại băng."""
    cycle = ConveyorCycle()
    cycle.step(0.0, loading_end())
    cycle.step(1.0, at_pick())
    cycle.step(5.0, at_pick())
    cycle.step(6.0, at_pick(), holding='')
    for t in range(7, 30):
        action = cycle.step(float(t), at_pick())
        assert action.frozen == (CAN,), 'van phai dong bang khi lon that con tren bang'
        assert cycle.state == NHA_QUYEN


def test_nhac_lon_that_ra_thi_nhan_lai_quyen_sau_vai_khung():
    cycle = ConveyorCycle()
    cycle.step(0.0, loading_end())
    cycle.step(1.0, at_pick())
    cycle.step(5.0, at_pick())
    cycle.step(6.0, at_pick(), holding='')
    for i in range(cycle.confirm_frames - 1):
        assert cycle.step(7.0 + i, {}).frozen == (CAN,)      # chưa đủ khung xác nhận
    action = cycle.step(20.0, {})
    assert action.frozen == () and cycle.state == CHO_LON and cycle.target is None


def test_lon_thoang_an_roi_hien_lai_thi_khong_nhan_lai_quyen():
    """Tay người lướt ngang che lon một khung không được tính là 'đã nhấc ra'."""
    cycle = ConveyorCycle()
    cycle.step(0.0, loading_end())
    cycle.step(1.0, at_pick())
    cycle.step(5.0, at_pick())
    cycle.step(6.0, at_pick(), holding='')
    cycle.step(7.0, {})
    cycle.step(8.0, {})
    cycle.step(9.0, at_pick())                  # lon hiện lại -> đếm lại từ đầu
    for i in range(cycle.confirm_frames - 1):
        assert cycle.step(10.0 + i, {}).frozen == (CAN,)
    assert cycle.step(20.0, {}).frozen == ()


def test_lon_ngoai_bang_khong_khoi_dong_vong():
    """Lon đứng trên BÀN (không phải trên băng) không được coi là lon chờ chuyển."""
    cycle = ConveyorCycle()
    far = {CAN: (BELT_CENTER[0] + 0.2, BELT_CENTER[1], Z, 1.0)}
    assert cycle.step(0.0, far).belt is False
    assert cycle.state == CHO_LON


def test_mot_vong_tron_ven_roi_quay_lai_dau():
    cycle = ConveyorCycle()
    cycle.step(0.0, loading_end())
    cycle.step(1.0, at_pick())
    cycle.step(5.0, at_pick())
    cycle.step(6.0, at_pick(), holding=CAN)
    cycle.step(7.0, {}, holding='')
    for i in range(cycle.confirm_frames):
        cycle.step(8.0 + i, {})
    assert cycle.state == CHO_LON
    assert cycle.step(20.0, loading_end()).belt is True      # sẵn sàng lon kế tiếp
