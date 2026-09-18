#!/usr/bin/env python3
"""
Sinh ảnh marker ArUco và khối SDF `calib_markers` cho world, từ bố trí trong scene.py.

Chạy từ thư mục src/delta_controller:
    python3 scripts/make_calib_markers.py
Ghi ảnh vào closed_loop_description/materials/textures/aruco_<id>.png và in khối SDF để dán vào
worlds/delta_objects_world.sdf.
"""

import os

import cv2
from delta_controller.scene import (
    CALIB_ARUCO_DICT,
    CALIB_MARKER_SIZE,
    CALIB_MARKER_THICKNESS,
    CALIB_MARKERS,
    TABLE_Z,
)
import numpy as np

MODULES = 6          # marker 4x4 bit + viền đen 1 ô mỗi phía
QUIET = 1            # lề trắng 1 ô mỗi phía (bắt buộc để nhận dạng được viền đen)
PX_PER_MODULE = 64

HERE = os.path.dirname(os.path.abspath(__file__))
TEXTURES = os.path.join(HERE, '..', '..', 'closed_loop_description', 'materials', 'textures')


def main():
    os.makedirs(TEXTURES, exist_ok=True)
    dictionary = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, CALIB_ARUCO_DICT))
    side = MODULES * PX_PER_MODULE
    for marker_id in CALIB_MARKERS:
        marker = cv2.aruco.drawMarker(dictionary, marker_id, side)
        img = np.full((side + 2 * QUIET * PX_PER_MODULE,) * 2, 255, np.uint8)
        o = QUIET * PX_PER_MODULE
        img[o:o + side, o:o + side] = marker
        cv2.imwrite(os.path.join(TEXTURES, f'aruco_{marker_id}.png'), img)

    tile = CALIB_MARKER_SIZE * (MODULES + 2 * QUIET) / MODULES
    z = TABLE_Z + CALIB_MARKER_THICKNESS / 2.0 + 1.0     # world = robot + 1.0
    lines = [
        '    <!-- Marker ArUco hiệu chuẩn camera (Bước 8.3), sinh bởi',
        '         delta_controller/scripts/make_calib_markers.py từ scene.CALIB_MARKERS.',
        f'         {CALIB_ARUCO_DICT}, ô đen {CALIB_MARKER_SIZE * 1000:.0f} mm, tấm '
        f'{tile * 1000:.1f} mm (có lề trắng), dày {CALIB_MARKER_THICKNESS * 1000:.0f} mm.',
        '         Chỉ có visual (không va chạm). -->',
        '    <model name="calib_markers">',
        '      <static>true</static>',
        '      <link name="link">',
    ]
    for marker_id, (x, y) in CALIB_MARKERS.items():
        lines += [
            f'        <visual name="aruco_{marker_id}">',
            f'          <pose>{x} {y} {z:.4f} 0 0 0</pose>',
            f'          <geometry><box><size>{tile:.5f} {tile:.5f} '
            f'{CALIB_MARKER_THICKNESS}</size></box></geometry>',
            '          <material>',
            '            <ambient>1 1 1 1</ambient><diffuse>1 1 1 1</diffuse>'
            '<specular>0 0 0 1</specular>',
            '            <pbr><metal>',
            '              <albedo_map>model://closed_loop_description/materials/textures/'
            f'aruco_{marker_id}.png</albedo_map>',
            '              <roughness>1.0</roughness><metalness>0.0</metalness>',
            '            </metal></pbr>',
            '          </material>',
            '        </visual>',
        ]
    lines += ['      </link>', '    </model>']
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
