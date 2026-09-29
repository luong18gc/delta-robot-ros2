#!/usr/bin/env python3
"""
Gửi một chuỗi lệnh vào REPL `cartesian_control` rồi in kết quả — để chạy thử tự động.

    python3 src/delta_controller/scripts/drive_repl.py don reset
    python3 src/delta_controller/scripts/drive_repl.py "nguon that" vat "chuyen coca"

Cần mô phỏng đang chạy (ros2 launch delta_controller pick_place.launch.py).

⚠️ Dấu nhắc `Nhap lenh > ` KHÔNG có ký tự xuống dòng, nên đọc stdout theo DÒNG sẽ treo. Phải đọc
theo byte (os.read, không chặn) và đặt PYTHONUNBUFFERED=1 cho tiến trình con.
"""

import argparse
import os
import subprocess
import sys
import time

# Lệnh dọn/đặt lại chạy lâu (mỗi vật một vòng quan sát + gắp + thả).
SLOW_COMMANDS = {'don', 'sort', 'reset'}
SLOW_WAIT = 400.0
DEFAULT_WAIT = 60.0
START_WAIT = 10.0


def drain(proc, seconds):
    """Đọc mọi thứ tiến trình con in ra trong `seconds` giây và chuyển tiếp ra stdout."""
    os.set_blocking(proc.stdout.fileno(), False)
    end = time.time() + seconds
    while time.time() < end:
        try:
            chunk = os.read(proc.stdout.fileno(), 65536)
        except BlockingIOError:
            chunk = b''
        if chunk:
            sys.stdout.write(chunk.decode('utf-8', 'replace'))
            sys.stdout.flush()
        else:
            time.sleep(0.2)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('commands', nargs='*', default=['vat'],
                    help='cac lenh REPL, moi lenh mot doi so')
    ap.add_argument('--wait', type=float, default=DEFAULT_WAIT, help='giay cho moi lenh thuong')
    ap.add_argument('--slow-wait', type=float, default=SLOW_WAIT, help='giay cho don/reset')
    args = ap.parse_args()

    env = dict(os.environ, PYTHONUNBUFFERED='1')
    proc = subprocess.Popen(['ros2', 'run', 'delta_controller', 'cartesian_control'],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, env=env)
    try:
        drain(proc, START_WAIT)
        for command in args.commands:
            sys.stdout.write(f'\n>>> {command}\n')
            sys.stdout.flush()
            proc.stdin.write((command + '\n').encode())
            proc.stdin.flush()
            drain(proc, args.slow_wait if command in SLOW_COMMANDS else args.wait)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == '__main__':
    main()
