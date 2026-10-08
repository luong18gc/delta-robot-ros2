#!/usr/bin/env python3
"""
Sinh `delta_conveyor_world.sdf` = cảnh lon hiện tại + BĂNG CHUYỀN (Bước 10d).

    python3 src/delta_controller/scripts/make_conveyor_world.py
    colcon build --packages-select closed_loop_description

Kích thước băng lấy từ `scene.REAL_BELT_*`. Đo lại trên băng ĐÃ LẮP rồi sửa ba hằng số đó và chạy
lại script này — không sửa tay vào file SDF, vì sửa tay thì hệ ảo và `scene.py` sẽ lệch nhau mà
không ai báo.

Vì sao tạo world RIÊNG thay vì thêm băng vào `delta_cans_world.sdf`: world đó là cơ sở của toàn bộ
số liệu Chương 7 khóa luận. Thêm vật vào đó là mọi kết quả cũ không tái hiện được nữa. Đây cũng là
cách dự án đã làm khi chuyển từ cảnh khối vuông sang cảnh lon.
"""

import os
import sys

import _workspace  # noqa: F401
from delta_controller import scene as s

WORLDS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      '..', '..', 'closed_loop_description', 'worlds')
SOURCE = os.path.normpath(os.path.join(WORLDS, 'delta_cans_world.sdf'))
TARGET = os.path.normpath(os.path.join(WORLDS, 'delta_conveyor_world.sdf'))
BASE_Z = 1.0        # base_link của robot nằm ở world z = 1.0


def belt_model():
    """Khối SDF của băng chuyền, sinh từ scene.REAL_BELT_*."""
    table_top = s.TABLE_Z + BASE_Z
    cx, cy = s.BELT_CENTER
    zc = table_top + s.BELT_HEIGHT / 2
    radius = s.BELT_HEIGHT / 2          # đỉnh con lăn trùng mặt băng, không nhô lên cản vật
    half = s.BELT_LENGTH / 2
    box = f'<box><size>{s.BELT_WIDTH:.5f} {s.BELT_LENGTH:.5f} {s.BELT_HEIGHT:.5f}</size></box>'
    roller = (f'<cylinder><radius>{radius:.5f}</radius>'
              f'<length>{s.BELT_WIDTH:.5f}</length></cylinder>')
    return f"""    <!-- BANG CHUYEN — ban sao hinh hoc bang tai THAT, thu nho {s.SCALE:.0f} lan.
         SINH TU DONG boi scripts/make_conveyor_world.py; dung sua tay.

         TINH, KHONG chuyen dong, va do la chu y: lon ao dich vi CAMERA noi lon that dich, khong
         phai vi mat bang ao day no. Cho mat bang ao chay thi ma sat se danh nhau voi lenh dat
         pose cua ban sao so. Bang ao chi can la MAT DO dung cao do — thieu no thi lon ao roi
         xuong mat ban va ban sao so sai dung bang chieu cao bang chia cho ti le. -->
    <model name="conveyor">
      <static>true</static>
      <link name="link">
        <collision name="belt_collision">
          <pose>{cx:.5f} {cy:.5f} {zc:.5f} 0 0 0</pose>
          <geometry>{box}</geometry>
        </collision>
        <visual name="belt_visual">
          <pose>{cx:.5f} {cy:.5f} {zc:.5f} 0 0 0</pose>
          <geometry>{box}</geometry>
          <material>
            <ambient>0.02 0.05 0.03 1</ambient>
            <diffuse>0.04 0.10 0.06 1</diffuse>
            <specular>0.01 0.01 0.01 1</specular>
          </material>
        </visual>
        <!-- Hai con lan: chi de nhin ra day la bang tai trong video bao ve. -->
        <visual name="roller_load">
          <pose>{cx:.5f} {cy + half:.5f} {zc:.5f} 0 1.5708 0</pose>
          <geometry>{roller}</geometry>
          <material><ambient>0.15 0.15 0.15 1</ambient>
            <diffuse>0.25 0.25 0.25 1</diffuse></material>
        </visual>
        <visual name="roller_pick">
          <pose>{cx:.5f} {cy - half:.5f} {zc:.5f} 0 1.5708 0</pose>
          <geometry>{roller}</geometry>
          <material><ambient>0.15 0.15 0.15 1</ambient>
            <diffuse>0.25 0.25 0.25 1</diffuse></material>
        </visual>
      </link>
    </model>
"""


def main():
    """Chèn mô hình băng chuyền vào bản sao của cảnh lon."""
    world = open(SOURCE, encoding='utf-8').read()
    anchor = '    <model name="work_table">'
    if anchor not in world:
        raise SystemExit(f'Khong tim thay "{anchor}" trong {SOURCE}')
    index = world.index(anchor)
    open(TARGET, 'w', encoding='utf-8').write(world[:index] + belt_model() + '\n' + world[index:])
    print(f'Da ghi {TARGET}')
    print(f'  bang ao: {s.BELT_WIDTH * 1000:.1f} x {s.BELT_LENGTH * 1000:.1f} x '
          f'{s.BELT_HEIGHT * 1000:.1f} mm, tam ({s.BELT_CENTER[0] * 1000:+.1f}, '
          f'{s.BELT_CENTER[1] * 1000:+.1f}), mat bang z = {s.BELT_TOP_Z:.4f}')
    print('  chay tiep: colcon build --packages-select closed_loop_description')
    return 0


if __name__ == '__main__':
    sys.exit(main())
