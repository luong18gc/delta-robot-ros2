import time

from std_msgs.msg import Float64


class JointCommander:
    """Đóng gói việc publish lệnh vị trí cho 3 khớp chủ động của robot delta."""

    CHAIN_TOPICS = {
        1: '/delta_3dof/Chain1_1/cmd_pos',
        2: '/delta_3dof/Chain2_1/cmd_pos',
        3: '/delta_3dof/Chain3_1/cmd_pos',
    }

    def __init__(self, node):
        self._publishers = {
            chain_id: node.create_publisher(Float64, topic, 10)
            for chain_id, topic in self.CHAIN_TOPICS.items()
        }

    def all_connected(self) -> bool:
        """Kiểm tra cả 3 topic đã có subscriber (bridge Gazebo) chưa."""
        return all(pub.get_subscription_count() > 0 for pub in self._publishers.values())

    def wait_for_connection(self, timeout_sec: float = 5.0) -> bool:
        """
        Chờ bridge Gazebo subscribe cả 3 topic.

        Lệnh publish khi discovery chưa xong sẽ bị mất (topic không lưu lịch sử).
        """
        deadline = time.monotonic() + timeout_sec
        while not self.all_connected():
            if time.monotonic() > deadline:
                return False
            time.sleep(0.05)
        return True

    def send(self, j1: float, j2: float, j3: float) -> None:
        """Gửi lệnh vị trí tới cả 3 khớp cùng lúc."""
        values = {1: j1, 2: j2, 3: j3}
        for chain_id, value in values.items():
            msg = Float64()
            msg.data = value
            self._publishers[chain_id].publish(msg)
