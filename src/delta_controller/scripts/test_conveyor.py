#!/usr/bin/env python3
"""
Dò đấu nối băng tải: nói chuyện thẳng với Arduino, không qua Serial Monitor.

    python3 src/delta_controller/scripts/test_conveyor.py

Chạy một chuỗi phép thử và hỏi bạn băng phản ứng thế nào. Mục đích là tách bạch BA câu hỏi mà
triệu chứng "băng chạy mãi" gộp lại làm một:

1. Arduino có chạy đúng chương trình không -> xem nó có trả lời không
2. Chân NÀO thật sự cho phép mạch chạy     -> thả nổi từng chân, hỏi bạn băng có dừng không
3. PWM có đổi được tốc độ không            -> cho 40 rồi 255, hỏi bạn nhanh chậm thế nào

Phép dò ở bước 2 THẢ NỔI chân chứ không kéo xuống mức thấp, nên an toàn kể cả khi chân đó hóa ra
đang nối vào ngõ ra 5V của module — và không phải rút dây rồi cắm lại (rất dễ nhầm chỗ).

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

        print('\n[2] Chan nao thuc su cho phep mach chay?')
        talk(port, 'B')
        talk(port, 'S')
        time.sleep(0.6)
        d9_controls = not ask('Bang co DANG CHAY khong (da ra lenh dung)?')
        if d9_controls:
            print('   -> D9 khong che duoc mach. Tot, dung nhu thiet ke.')
        else:
            print('   -> D9 KHONG khong che duoc. Thu tha noi D8...')
            talk(port, 'A')
            time.sleep(0.8)
            d8_controls = ask('Bay gio bang da DUNG chua?')
            talk(port, 'B')
            if d8_controls:
                print('   => CHAN D8 moi la chan CHO PHEP, khong phai D9.')
                print('      Hai day dang cam nguoc vai tro. Cach sua: DOI CHO hai day o Arduino')
                print('      (day dang o chan 8 chuyen sang chan 9 va nguoc lai).')
            else:
                print('   => Ca D8 lan D9 deu khong khong che duoc mach.')
                print('      Chan cho phep cua module dang bi ghim cung len 5V, hoac day tin hieu')
                print('      khong nam tren chan cho phep. Phai xem lai dau noi tren module.')

        print('\n[3] Toc do co doi duoc khong?')
        talk(port, 'B')
        talk(port, 'V40')
        talk(port, 'R')
        time.sleep(1.5)
        slow = ask('Bang dang chay CHAM phai khong?')
        talk(port, 'V255')
        time.sleep(1.5)
        fast = ask('Bay gio co chay NHANH HON han khong?')
        talk(port, 'S')
        if slow and fast:
            print('   -> PWM tren D9 dieu khien toc do dung chieu.')
        elif not slow and fast:
            print('   -> NGUOC CHIEU: so nho lai chay nhanh. D9 dang cam vao chan DIEU HUONG')
            print('      chu khong phai chan cho phep; chan con lai bi ghim muc cao.')
        else:
            print('   -> Toc do khong doi: D9 khong nhan PWM (bi ghim, hoac la chan so).')

    print('\nXong. Gui ket qua nay cho tro ly de biet buoc tiep theo.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
