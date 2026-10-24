"""
Máy trạng thái cho vòng BĂNG TẢI → GẮP: thuần Python, không phụ thuộc ROS nên test được.

Vòng làm việc (yêu cầu của giảng viên hướng dẫn, 2026-10-09):

    CHO_LON ─► BAM_LON ─► DANG_CHAY ─► DUNG_BANG ─► DANG_GAP ─► NHA_QUYEN ─┐
       ▲        robot tới   băng chạy,   lon tới nơi,  hút & thả  chờ tay người│
       │        trên đầu    robot BÁM    robot chờ     vào khay   nhấc lon thật│
       │        lon         theo lon     trên đầu lon                          │
       └──────────────────────── tay đặt lon mới lên băng ────────────────────┘

VÌ SAO ROBOT BÁM THEO LON thay vì đứng chờ ở cuối băng: đầu hút luôn ở ngay trên nắp lon trong
suốt hành trình, nên lúc băng dừng là hút được NGAY, không mất thêm quãng đi tới. Đó cũng là bước
đệm cho gắp-khi-đang-chạy sau này: cơ chế đã sẵn, chỉ còn bỏ bước dừng băng.

VÌ SAO CÓ TRẠNG THÁI `NHA_QUYEN` — đây là chỗ khó duy nhất của cả vòng.

Khi robot ảo đã gắp lon và bỏ vào khay, LON THẬT VẪN CÒN NẰM TRÊN BĂNG. Bản sao số thì bám camera,
nên nếu không làm gì nó sẽ giật lon ảo từ trong khay về lại mặt băng — tức là xóa sạch việc robot
vừa làm, 10 lần mỗi giây. Vậy sau khi gắp, quyền quyết định vị trí lon phải TẠM CHUYỂN sang mô
phỏng, rồi chỉ nhận lại khi thế giới thật đã đồng bộ (tay người đã nhấc lon ra khỏi băng).

Thầy diễn đạt là "tắt cam thực tế". Thực hiện thì chính xác hơn một chút: không tắt camera (còn
phải nhìn để biết lon thật đã được nhấc đi chưa), mà là ĐÓNG BĂNG riêng lon đó trong bản sao số.

Hai bất biến mà máy trạng thái này bảo đảm:

1. Không bao giờ có hai nguồn cùng ghi vị trí một lon. Lon đang gắp thì chỉ mô phỏng ghi; lon trên
   băng thì chỉ camera ghi.
2. Không nhận lon mới khi LON VỪA GẮP chưa được dọn khỏi băng. Ràng buộc này chỉ áp cho đúng lon
   đó, không phải cho cả mặt băng: ĐẶT NHIỀU LON CÙNG LÚC LÀ HỢP LỆ. Lon gần điểm gắp nhất được
   xử lý trước, các lon sau chờ tới lượt; khi băng dừng để gắp thì chúng cũng dừng theo nên không
   ảnh hưởng gì. Điều kiện duy nhất là các lon phải KHÁC MÀU (giả định "mỗi màu một vật" của khối
   thị giác) và cách nhau ít nhất `scene.REAL_MIN_PITCH_ON_BELT` = 80 mm thật để hình bóng của
   chúng không chồng nhau trong ảnh.
"""

from dataclasses import dataclass, field
import math

from delta_controller.scene import BELT_PICK_XY, OBJECTS, OBSERVE_XYZ, on_belt, SCALE

CHO_LON = 'CHO_LON'
BAM_LON = 'BAM_LON'
DANG_CHAY = 'DANG_CHAY'
DUNG_BANG = 'DUNG_BANG'
DANG_GAP = 'DANG_GAP'
NHA_QUYEN = 'NHA_QUYEN'

# Lon coi là "đã tới" khi còn cách điểm gắp chừng này theo Y. Đo 2026-10-14: băng chạy 16 mm/s
# thật và lon chỉ trôi 3 mm sau khi dừng, nên không cần pha giảm tốc, và ngưỡng rộng tay vẫn đủ.
ARRIVE_TOL = 0.008            # m ảo = 24 mm thật
# Chờ lon đứng hẳn sau khi băng dừng. Trôi có 3 mm nên đây là dư ra cho chắc.
SETTLE_SEC = 1.0
# Băng dài 230 mm thật, chạy 16 mm/s -> hết băng mất ~14 s. Quá mức này là có chuyện: lon kẹt, dây
# trượt, hoặc không ai đặt lon. Thà dừng và nói ra còn hơn chạy mãi.
TRAVEL_TIMEOUT_SEC = 40.0
# Lon biến mất khỏi camera thoáng qua (tay người lướt ngang, một khung nhiễu) thì KHÔNG kết luận
# gì. Giống tinh thần CONFIRM_FRAMES của digital_twin: đừng tin một khung.
CONFIRM_FRAMES = 5
# Chờ bấy nhiêu giây không thấy lon nào thì đưa robot về tư thế quan sát. Sau khi thả lon vào
# khay, robot đứng ngay trên khay và có thể CHE lon kế tiếp trên băng; nếu cứ đứng đó mà chờ thì
# hệ thống chờ mãi một thứ chính nó đang che. Đây là kiểu bế tắc chỉ xuất hiện khi có nhiều lon.
STEP_ASIDE_SEC = 2.0
# Khe giữa đáy platform và nắp lon lúc bám. Đủ xa để không chạm lon khi ước lượng lệch vài mm,
# đủ gần để lúc hút chỉ phải hạ một đoạn ngắn.
HOVER = 0.02                  # m ảo = 60 mm thật
PLATFORM_HALF_THICKNESS = 0.003
# Robot coi là "đã tới trên đầu lon" khi cách điểm bám chừng này — chưa tới thì chưa cho băng chạy.
TRACK_TOL = 0.004             # m ảo = 12 mm thật
_HALF_HEIGHT = {o.name: o.half_height for o in OBJECTS}


def hover_point(name, x, y, z):
    """Chỗ tool0 phải tới để lơ lửng trên nắp lon có tâm tại (x, y, z) hệ ảo."""
    return (x, y, z + _HALF_HEIGHT[name] + PLATFORM_HALF_THICKNESS + HOVER)


@dataclass
class Action:
    """Việc cần làm sau một nhịp. `belt=None` nghĩa là để nguyên, không phải là tắt."""

    belt: bool = None
    pick: str = None
    frozen: tuple = ()
    track: tuple = None          # (x, y, z) tool0 phải bám tới; None = không bám
    message: str = ''


@dataclass
class ConveyorCycle:
    """
    Vòng băng tải → gắp. Gọi `step()` mỗi nhịp với vị trí lon camera đang thấy.

    Không tự làm gì cả: nó chỉ TRẢ VỀ việc cần làm. Nhờ vậy test được bằng cách gọi step() với
    các kịch bản dựng sẵn, không cần băng tải, không cần robot, không cần Gazebo.
    """

    pick_xy: tuple = BELT_PICK_XY
    arrive_tol: float = ARRIVE_TOL
    settle_sec: float = SETTLE_SEC
    timeout_sec: float = TRAVEL_TIMEOUT_SEC
    confirm_frames: int = CONFIRM_FRAMES

    state: str = CHO_LON
    target: str = None            # lon đang xử lý
    _cans: dict = field(default_factory=dict, repr=False)
    since: float = 0.0            # mốc thời gian vào trạng thái hiện tại
    _gone: int = field(default=0, repr=False)     # số khung liên tiếp không thấy lon trên băng

    # ------------------------------------------------------------------ tiện ích

    def _on_belt_cans(self, cans):
        """{tên -> (x, y)} những lon camera thấy RÕ và đang nằm trên mặt băng."""
        return {name: (x, y) for name, (x, y, _z, score) in cans.items()
                if score > 0.0 and on_belt(x, y)}

    def _hover_now(self):
        """Điểm bám trên nắp lon đang xử lý, hoặc None nếu khung này không thấy nó."""
        seen = self._cans.get(self.target)
        if seen is None or seen[3] <= 0.0:
            return None
        return hover_point(self.target, seen[0], seen[1], seen[2])

    def _arrived(self, y):
        """Lon đã tới điểm gắp chưa — xét theo Y vì băng chạy dọc Y."""
        return y >= self.pick_xy[1] - self.arrive_tol

    def _go(self, state, now):
        self.state, self.since, self._gone = state, now, 0

    # ------------------------------------------------------------------ một nhịp

    def abort(self, now):
        """Bỏ lượt đang làm, quay về chờ vật — dùng khi thao tác gắp thất bại."""
        self.target = None
        self._go(CHO_LON, now)

    def step(self, now, cans, holding='', tool=None):
        """
        Chạy một nhịp của vòng và trả về việc cần làm.

        `cans` = {tên -> (x, y, z, score)} hệ ảo; `holding` = lon giác hút đang giữ; `tool` = vị
        trí tool0 đo được, cần để biết robot đã tới trên đầu lon chưa.

        Trả về `Action`: băng chạy/dừng, điểm cần bám, có gắp lon nào không, lon nào phải đóng
        băng trong bản sao số, và một câu giải thích cho người xem.
        """
        self._cans = cans
        on_belt_now = self._on_belt_cans(cans)

        if self.state == CHO_LON:
            return self._cho_lon(now, on_belt_now)
        if self.state == BAM_LON:
            return self._bam_lon(now, on_belt_now, tool)
        if self.state == DANG_CHAY:
            return self._dang_chay(now, on_belt_now)
        if self.state == DUNG_BANG:
            return self._dung_bang(now, on_belt_now)
        if self.state == DANG_GAP:
            return self._dang_gap(now, holding)
        return self._nha_quyen(now, on_belt_now)

    def _cho_lon(self, now, on_belt_now):
        if not on_belt_now:
            if now - self.since > STEP_ASIDE_SEC:
                return Action(belt=False, track=OBSERVE_XYZ,
                              message='Khong thay lon nao — lui ve tu the quan sat de khoi che.')
            return Action(belt=False, message='Cho dat lon len bang.')
        # Lon gần nhất với điểm gắp đi trước — nếu có nhiều lon thì lon đầu hàng được xử lý.
        name, (_x, y) = max(on_belt_now.items(), key=lambda kv: kv[1][1])
        self.target = name
        self._go(BAM_LON, now)
        return Action(belt=False, track=self._hover_now(),
                      message=f'Dua dau hut len tren nap {name} truoc da.')

    def _bam_lon(self, now, on_belt_now, tool):
        """Đưa đầu hút lên trên nắp lon. Chưa tới nơi thì CHƯA cho băng chạy."""
        if self.target not in on_belt_now:
            self._go(CHO_LON, now)
            return Action(belt=False, message='Mat dau lon, quay lai cho.')
        hover = self._hover_now()
        if tool is None or hover is None:
            return Action(belt=False, track=hover, message='Dang dua dau hut toi...')
        gap = math.dist(tool, hover)
        if gap > TRACK_TOL:
            return Action(belt=False, track=hover,
                          message=f'Dang dua dau hut toi ({1000 * SCALE * gap:.0f} mm that nua).')
        if self._arrived(on_belt_now[self.target][1]):
            # Lon đã ở cuối băng sẵn: khỏi chạy băng.
            self._go(DUNG_BANG, now)
            return Action(belt=False, track=hover, message=f'{self.target} da o diem gap san.')
        self._go(DANG_CHAY, now)
        return Action(belt=True, track=hover,
                      message=f'Dau hut da vao vi tri. Cho bang chay, bam theo {self.target}.')

    def _dang_chay(self, now, on_belt_now):
        if now - self.since > self.timeout_sec:
            self._go(CHO_LON, now)
            return Action(belt=False,
                          message=f'HET GIO: {self.target} khong toi noi sau '
                                  f'{self.timeout_sec:.0f}s. Kiem tra lon ket hay day truot.')
        here = on_belt_now.get(self.target)
        if here is None:
            # Mất dấu thoáng qua thì cứ chạy tiếp, và GIỮ NGUYÊN điểm bám cũ thay vì thả robot về
            # đâu đó — một khung nhiễu không phải lý do để bỏ bám.
            return Action(message=f'Tam thoi khong thay {self.target}, van chay.')
        hover = self._hover_now()
        if self._arrived(here[1]):
            self._go(DUNG_BANG, now)
            return Action(belt=False, track=hover,
                          message=f'{self.target} da toi diem gap. Dung bang.')
        return Action(track=hover, message=f'Dang bam theo {self.target} tren bang.')

    def _dung_bang(self, now, on_belt_now):
        if now - self.since < self.settle_sec:
            return Action(belt=False, track=self._hover_now(), message='Cho lon dung han...')
        self._go(DANG_GAP, now)
        # Đóng băng TỪ ĐÂY, trước khi robot chạm vào: nếu đợi tới lúc nhấc lên mới đóng thì giữa
        # hai thời điểm đó camera vẫn ghi đè, và lon ảo bị kéo về băng ngay khi robot vừa nhấc.
        return Action(belt=False, pick=self.target, frozen=(self.target,),
                      message=f'Giao {self.target} cho mo phong. Bat dau gap.')

    def _dang_gap(self, now, holding):
        # Việc gắp do tầng trên chạy (nó chặn), nên tới đây là đã xong. Giữ đóng băng.
        if holding == self.target:
            return Action(belt=False, frozen=(self.target,),
                          message=f'Dang giu {self.target}.')
        self._go(NHA_QUYEN, now)
        return Action(belt=False, frozen=(self.target,),
                      message=f'Da tha {self.target} vao khay. Moi nhac lon THAT ra khoi bang.')

    def _nha_quyen(self, now, on_belt_now):
        if self.target in on_belt_now:
            self._gone = 0
            return Action(belt=False, frozen=(self.target,),
                          message=f'Lon THAT {self.target} van con tren bang — hay nhac ra.')
        self._gone += 1
        if self._gone < self.confirm_frames:
            return Action(belt=False, frozen=(self.target,),
                          message='Hinh nhu lon that da duoc nhac ra, dang xac nhan...')
        done = self.target
        self.target = None
        self._go(CHO_LON, now)
        # Thôi đóng băng: thế giới thật đã đồng bộ với mô phỏng, camera lại được quyền ghi.
        return Action(belt=False, message=f'Xong {done}. San sang nhan lon tiep theo.')
