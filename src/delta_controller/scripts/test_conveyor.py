#!/usr/bin/env python3
"""
Dò đấu nối băng tải: nói chuyện thẳng với Arduino, không qua Serial Monitor.

    python3 src/delta_controller/scripts/test_conveyor.py

Chạy một chuỗi phép thử và hỏi bạn băng phản ứng thế nào. Mục đích là tách bạch BA câu hỏi mà
triệu chứng "băng chạy mãi" gộp lại làm một:

1. Arduino có chạy đúng chương trình không -> xem nó có trả lời không
2. Chân PWM có điều khiển được băng không  -> cho tốc độ 0 rồi 255, hỏi bạn có khác không
3. Lưới an toàn hết hạn có chạy không      -> ngừng gửi lệnh, đợi, hỏi băng có tự dừng không

Không đoán gì về nhãn chân của module; chỉ hỏi những điều quan sát được bằng mắt.
"""

import argparse
import glob
import sys
import time

import serial

BAUD = 115200


def ask(question):
    """Hỏi có/không; trả về True/False."""
    while True:
        answer = input(f'   {question} [c/k] ').strip().lower()
        if answer in ('c', 'co', 'có', 'y', 'yes'):
            return True
        if answer in ('k', 'khong', 'không', 'n', 'no'):
            return False


def talk(port, command, wait=0.35):
    """Gửi lệnh, trả về những gì Arduino nói lại."""
    port.reset_input_buffer()
    port.write(command.encode())
    time.sleep(wait)
    return port.read(port.in_waiting or 1).decode(errors='replace').strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--port', default='auto')
    args = ap.parse_args()

    port_name = args.port
    if port_name == 'auto':
        found = sorted(glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*'))
        if not found:
            raise SystemExit('Khong thay cong serial nao. Da cam Arduino chua?')
        port_name = found[0]
    print(f'Cong: {port_name}')

    with serial.Serial(port_name, BAUD, timeout=0.3) as port:
        print('Cho Arduino khoi dong lai (no tu reset khi mo cong)...')
        time.sleep(2.5)
        port.reset_input_buffer()

        print('\n[1] Arduino co chay dung chuong trinh khong?')
        reply = talk(port, '?')
        if not reply:
            print('   KHONG tra loi gi.')
            print('   -> Chua nap chuong trinh, hoac nap vao board khac, hoac sai toc do baud.')
            return 1
        print(f'   Arduino tra loi: "{reply}"  -> chuong trinh DANG CHAY, giao tiep OK')

        print('\n[2] Chan PWM co dieu khien duoc bang khong?')
        talk(port, 'S')
        time.sleep(0.5)
        running_while_stopped = ask('Bang co DANG CHAY khong (dang le phai dung)?')
        if running_while_stopped:
            print('   -> Chan tren D9 KHONG dieu khien duoc bang.')
            print('      Bang chay du lenh da bao dung, nghia la mach luon duoc cho phep:')
            print('      hoac day tin hieu khong nam dung chan cho phep, hoac module ghim cung.')
            print('      PHEP THU TIEP: rut day o chan 9, roi rut day o chan 8, xem cai nao dung.')
            return 1
        print('   -> Lenh dung co tac dung. Tot.')

        talk(port, 'V60')
        talk(port, 'R')
        time.sleep(1.2)
        slow = ask('Bang dang chay CHAM phai khong?')
        talk(port, 'V255')
        time.sleep(1.2)
        fast = ask('Bay gio no co chay NHANH HON han khong?')
        talk(port, 'S')
        if slow and fast:
            print('   -> Dieu khien toc do chay dung.')
        else:
            print('   -> Toc do khong doi: chan PWM dang bi ghim o muc cao,')
            print('      hoac day dang cam vao chan chi bat/tat chu khong nhan PWM.')

        print('\n[3] Luoi an toan het han co hoat dong khong?')
        talk(port, 'R')
        print('   Da cho chay. Bay gio NGUNG gui lenh trong 4 giay...')
        time.sleep(4.0)
        leftover = port.read(port.in_waiting or 1).decode(errors='replace').strip()
        stopped = ask('Bang da TU DUNG chua?')
        if stopped:
            print(f'   -> Luoi an toan chay dung. Arduino bao: "{leftover}"')
        else:
            print('   -> Bang KHONG tu dung. Xem lai muc [2]: chan PWM chua dieu khien duoc.')
        talk(port, 'S')

    print('\nXong. Gui ket qua nay cho tro ly de biet buoc tiep theo.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
