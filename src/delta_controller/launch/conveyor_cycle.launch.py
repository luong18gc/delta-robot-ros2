"""
Cả hệ thống trong một lệnh: mô phỏng + camera thật + bản sao số + BĂNG TẢI.

    ros2 launch delta_controller conveyor_cycle.launch.py

Rồi ở cửa sổ khác:

    ros2 run delta_controller cartesian_control
    Nhap lenh > bang            # chạy vòng băng tải -> gắp, Ctrl+C để dừng

Chỉ là `digital_twin.launch.py` cộng thêm node băng tải. Tách ra làm hai file để chạy được bản sao
số KHÔNG cần cắm Arduino — lúc hiệu chuẩn, lúc đo sai số, lúc chỉ muốn xem lon ảo đi theo lon thật
thì băng tải chỉ tổ vướng.

⚠️ Điều kiện như `digital_twin.launch.py` (ảnh nền, nội tham số, 6 marker trong khung), thêm:
Arduino phải cắm vào máy và đã nạp `docs/bang_chuyen/conveyor_arduino/`.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    share = get_package_share_directory('delta_controller')
    gui_arg = DeclareLaunchArgument('gui', default_value='true')
    port_arg = DeclareLaunchArgument(
        'port', default_value='auto',
        description='cong serial cua Arduino bang tai, vd /dev/ttyUSB0')
    speed_arg = DeclareLaunchArgument(
        'speed', default_value='255',
        description='PWM 0-255. Do 2026-10-14: 255 cho 16 mm/s that, da het kha nang dong co.')

    twin = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(share, 'launch', 'digital_twin.launch.py')),
        launch_arguments={'gui': LaunchConfiguration('gui')}.items(),
    )

    conveyor = Node(
        package='delta_controller',
        executable='conveyor',
        output='screen',
        parameters=[{
            'port': LaunchConfiguration('port'),
            'speed': LaunchConfiguration('speed'),
        }],
    )

    return LaunchDescription([gui_arg, port_arg, speed_arg, twin, conveyor])
