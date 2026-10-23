"""
Nối `ConveyorCycle` (logic thuần) với thế giới ROS: băng tải, camera, robot, bản sao số.

Tách khỏi `conveyor_cycle.py` có chủ đích. Mọi quyết định "khi nào chạy băng, khi nào giao quyền
cho mô phỏng, khi nào nhận lại" nằm bên kia và test được không cần phần cứng; file này chỉ làm cái
việc tẻ nhạt là gọi dịch vụ và phát topic. Hỏng ở đây là hỏng dây nối, hỏng ở kia là hỏng suy luận
— hai loại lỗi rất khác nhau, nên để lẫn vào một chỗ thì tốn công tìm.
"""

import threading
import time

from delta_controller.conveyor_cycle import ConveyorCycle, DANG_GAP
from delta_controller.task_planner import object_states
from rclpy.qos import DurabilityPolicy, QoSProfile
from std_msgs.msg import String
from std_srvs.srv import Trigger

TICK_SEC = 0.3          # nhịp máy trạng thái; camera 10 Hz nên nhanh hơn cũng chẳng biết thêm gì
# Nhịp BÁM phải nhanh hơn hẳn nhịp quyết định. `servo_step` nhích một đoạn cỡ `max_speed/rate_hz`
# = 1 mm ảo mỗi lần gọi; gọi nó theo nhịp máy trạng thái (0,3 s) thì robot đi 3,3 mm/s và giật
# từng nấc 1 mm. Hai nhịp này không liên quan gì nhau: một bên hỏi "giờ phải làm gì", bên kia chỉ
# kéo robot về phía đích cho mượt.
SERVO_HZ = 50.0
SERVICE_WAIT = 2.0


class ConveyorError(RuntimeError):
    """Không chạy được vòng băng tải (thiếu node băng tải, thiếu camera...)."""


class ConveyorRunner:
    """Chạy vòng băng tải → gắp trên node `cartesian_control`."""

    def __init__(self, node, log=print):
        self._node = node
        self._log = log
        self.cycle = ConveyorCycle()
        self._run_client = node.create_client(Trigger, '/conveyor/run')
        self._stop_client = node.create_client(Trigger, '/conveyor/stop')
        latched = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self._frozen_pub = node.create_publisher(String, '/twin/frozen', latched)
        self._belt_sent = None          # trạng thái băng đã gửi, để không gửi lại mỗi nhịp
        self._frozen_sent = None
        self._stop_asked = False        # có ai đó yêu cầu dừng từ bên ngoài

    # ------------------------------------------------------------------ dây nối

    def _call(self, client, what):
        if not client.wait_for_service(timeout_sec=SERVICE_WAIT):
            raise ConveyorError(
                f'Khong thay dich vu {what}. Chay node bang tai: '
                f'ros2 run delta_controller conveyor')
        done = threading.Event()
        future = client.call_async(Trigger.Request())
        future.add_done_callback(lambda _: done.set())
        if not done.wait(SERVICE_WAIT + 3.0):
            raise ConveyorError(f'Dich vu {what} khong tra loi')
        result = future.result()
        if not result.success:
            raise ConveyorError(f'{what}: {result.message}')

    def _set_belt(self, want):
        if want is None or want == self._belt_sent:
            return
        self._call(self._run_client if want else self._stop_client,
                   '/conveyor/run' if want else '/conveyor/stop')
        self._belt_sent = want

    def _set_frozen(self, names):
        """
        Công bố lon nào do mô phỏng nắm quyền vị trí.

        Phát mỗi khi ĐỔI, trên topic latched: node bản sao số khởi động lại giữa chừng vẫn nhận
        được danh sách hiện hành, thay vì tưởng không lon nào bị đóng băng rồi kéo lon trong khay
        về lại mặt băng.
        """
        names = tuple(sorted(names))
        if names == self._frozen_sent:
            return
        self._frozen_pub.publish(String(data=','.join(names)))
        self._frozen_sent = names

    # ------------------------------------------------------------------ vòng chạy

    def request_stop(self):
        """
        Yêu cầu dừng vòng từ luồng khác — dùng cho nút Dừng trên giao diện.

        REPL dừng bằng Ctrl+C, nhưng tín hiệu đó chỉ tới được luồng chính nên một nút bấm không
        gửi được. Đặt cờ rồi để chính vòng chạy tự thoát: nó sẽ đi qua khối dọn dẹp như thường,
        nên băng vẫn được dừng và quyền vị trí vẫn được trả lại.
        """
        self._stop_asked = True

    def run(self, rounds=None):
        """
        Chạy tới khi xong `rounds` lon (None = chạy mãi, Ctrl+C để dừng).

        Dừng kiểu nào cũng DỪNG BĂNG và TRẢ LẠI QUYỀN. Thoát mà để băng chạy là nguy hiểm; thoát
        mà còn đóng băng thì lon ảo đứng im vĩnh viễn và không ai đoán ra vì sao.
        """
        done = 0
        last_message = None
        track = None
        next_tick = 0.0
        self._stop_asked = False
        self._log('Vong bang tai. Dat MOT lon len dau nap.')
        try:
            while (rounds is None or done < rounds) and not self._stop_asked:
                now = time.monotonic()
                if now >= next_tick:
                    next_tick = now + TICK_SEC
                    before = self.cycle.state
                    action = self.cycle.step(now, self._node.latest_vision(),
                                             self._node.held_object,
                                             tool=self._node.current_position())
                    self._set_belt(action.belt)
                    self._set_frozen(action.frozen)
                    # Giữ điểm bám cũ khi khung này không thấy lon: một khung nhiễu không phải lý
                    # do để thả robot đứng lại giữa chừng.
                    if action.track is not None:
                        track = action.track
                    if action.message and action.message != last_message:
                        self._log(f'[{self.cycle.state}] {action.message}')
                        last_message = action.message
                    if action.pick:
                        # Trả điểm lệnh bám về trước khi gắp: `move` xuất phát từ vị trí ĐO ĐƯỢC,
                        # còn điểm lệnh bám là chỗ robot đang được kéo tới — để lẫn thì quỹ đạo
                        # gắp bắt đầu từ một điểm không ai đang ở.
                        self._node.servo_reset()
                        track = None
                        # Đưa luôn chỗ vừa nhìn thấy cho bộ gắp. Không có bước này thì nó tự quan
                        # sát lại: robot đang đứng ngay trên nắp lon lại chạy ra tư thế quan sát
                        # rồi mò về — thừa một quãng đi, và thừa cả rủi ro lon xê dịch lúc đó.
                        self._hand_over_observation()
                        self._node.task_executor.pick_place(action.pick)
                        next_tick = time.monotonic()
                    if before == DANG_GAP and self.cycle.state != DANG_GAP:
                        done += 1
                if track is not None and self._node.servo_step(track) is None:
                    self._log('Canh bao: diem bam ngoai tam voi, robot dung tai cho.')
                    track = None
                time.sleep(1.0 / SERVO_HZ)
        except KeyboardInterrupt:
            self._log('\nDung vong bang tai.')
        finally:
            if self._stop_asked:
                self._log('Da dung vong bang tai theo yeu cau.')
            self._safe_stop()
        return done

    def _hand_over_observation(self):
        """Chuyển kết quả nhìn thấy mới nhất cho `task_executor`, để nó khỏi quan sát lại."""
        seen = {name: (x, y, z) for name, (x, y, z, score) in self._node.latest_vision().items()
                if score > 0.0}
        if seen:
            self._node.task_executor.use_observation(object_states(seen))

    def _safe_stop(self):
        try:
            self._set_belt(False)
        except ConveyorError as err:                 # noqa: BLE001 — đang dọn dẹp, báo rồi đi tiếp
            self._log(f'Canh bao: khong dung duoc bang ({err})')
        self._node.servo_reset()
        self._frozen_sent = None
        self._frozen_pub.publish(String(data=''))
        self._log('Bang da dung, quyen vi tri da tra lai cho camera.')
