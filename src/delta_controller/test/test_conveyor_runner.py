"""Kiểm thử lớp nối vòng băng tải với ROS, bằng node giả (không cần ROS chạy)."""

from delta_controller import conveyor_runner as cr


class FakeNode:
    """Node giả: chỉ có những gì ConveyorRunner dùng tới."""

    def __init__(self, source='camera'):
        self.object_source = source
        self.held_object = ''
        self.servo_calls = []

    def create_client(self, *_args, **_kwargs):
        return object()

    def create_publisher(self, *_args, **_kwargs):
        return object()

    def latest_vision(self):
        return {}

    def current_position(self):
        return (0.0, 0.0, -0.11)

    def servo_step(self, goal):
        self.servo_calls.append(goal)
        return goal

    def servo_reset(self):
        pass


def test_khi_gap_thi_doc_the_gioi_ao():
    """
    Robot gắp VẬT ẢO, nên trong lúc gắp phải đọc vị trí từ thế giới ảo.

    Nếu vẫn đọc camera thì khâu kiểm chứng sau khi thả sẽ hỏi camera "vật vào khay chưa", mà camera
    nhìn thấy vật THẬT còn trên băng -> báo thất bại và cả vòng dừng lại.
    """
    node = FakeNode(source='camera')
    runner = cr.ConveyorRunner(node, log=lambda _: None)
    with runner._acting_on_simulation():
        assert node.object_source == 'ground_truth'
    assert node.object_source == 'camera', 'phai tra lai nguon cu'


def test_tra_lai_nguon_ca_khi_co_loi():
    node = FakeNode(source='camera')
    runner = cr.ConveyorRunner(node, log=lambda _: None)
    try:
        with runner._acting_on_simulation():
            raise RuntimeError('gap hong')
    except RuntimeError:
        pass
    assert node.object_source == 'camera'


def test_giu_nguyen_neu_von_da_la_the_gioi_that():
    node = FakeNode(source='ground_truth')
    runner = cr.ConveyorRunner(node, log=lambda _: None)
    with runner._acting_on_simulation():
        assert node.object_source == 'ground_truth'
    assert node.object_source == 'ground_truth'
