from delta_controller.joint_commander import JointCommander
import rclpy
from rclpy.node import Node


HELP_TEXT = """
Nhap gia tri 3 khop cach nhau boi dau cach hoac dau phay.
Vi du: 0.4 0.4 0.4   hoac   0.4, 0.2, 0.2

Lenh dac biet:
  home           -> dua ca 3 khop ve 0.0
  help           -> hien lai huong dan nay
  q / quit / exit -> thoat chuong trinh
"""


def parse_input(raw: str):
    parts = raw.replace(',', ' ').split()
    if len(parts) != 3:
        raise ValueError('Can nhap dung 3 gia tri, vi du: 0.4 0.4 0.4')
    return tuple(float(p) for p in parts)


def main(args=None):
    rclpy.init(args=args)
    node = Node('delta_manual_control')
    commander = JointCommander(node)

    print(HELP_TEXT)
    try:
        while rclpy.ok():
            try:
                raw = input('Nhap Chain1 Chain2 Chain3 > ').strip()
            except EOFError:
                break

            if not raw:
                continue

            command = raw.lower()
            if command in ('q', 'quit', 'exit'):
                break
            if command == 'help':
                print(HELP_TEXT)
                continue
            if command == 'home':
                commander.send(0.0, 0.0, 0.0)
                print('-> Da gui lenh home: (0.0, 0.0, 0.0)')
                continue

            try:
                j1, j2, j3 = parse_input(raw)
            except ValueError as e:
                print(f'Loi: {e}')
                continue

            commander.send(j1, j2, j3)
            print(f'-> Da gui: Chain1={j1}, Chain2={j2}, Chain3={j3}')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
