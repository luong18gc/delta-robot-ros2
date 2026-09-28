"""
Mô phỏng ba LON + ba KHAY phân loại (Bước 10b), bản sao số theo tỉ lệ k = 2.5.

ros2 launch delta_controller cans_world.launch.py             # co cua so Gazebo
ros2 launch delta_controller cans_world.launch.py gui:=false  # khong cua so

Launch này CHƯA nối giác hút và node thị giác — nó mới dựng thế giới và bắc cầu hai thứ cần để
nhìn và để đo:
  /side_camera/image, /side_camera/camera_info   — ảnh camera mô phỏng
  /objects/<lon>/odometry                        — vị trí THẬT của từng lon (đáp án để chấm điểm)

Còn thiếu, làm ở bước sau khi đã kiểm chứng thế giới chạy đúng:
  - `3dof_delta.gripper.xacro` mới có DetachableJoint cho red_box/green_cylinder/blue_sphere,
    chưa có cho ba lon -> chưa gắp được trong thế giới này.
  - `scene.py` còn mô tả ba khối vuông và khay 3 ô -> node `vision`, `gripper`, bộ lập kế hoạch
    chưa dùng được với lon.
Muốn gắp–thả như Bước 6–9 thì dùng `pick_place.launch.py` (thế giới khối vuông) — thế giới đó
giữ nguyên, mọi kết quả đã đo vẫn tái lập được.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

# Tên model trong worlds/delta_cans_world.sdf.
CANS = ('coca_can', 'pepsi_can', 'sevenup_can')


def generate_launch_description():
    bringup = get_package_share_directory('closed_loop_bringup')

    gui_arg = DeclareLaunchArgument(
        'gui', default_value='true',
        description='false = chay Gazebo khong cua so (nhanh hon khi co camera mo phong)')

    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(bringup, 'launch', '3dof_delta.launch.py')),
        launch_arguments={
            'world_name': 'delta_cans_world',
            'gui': LaunchConfiguration('gui'),
        }.items(),
    )

    bridge_args = [f'/objects/{name}/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry'
                   for name in CANS]
    bridge_args += [
        '/side_camera/image@sensor_msgs/msg/Image[gz.msgs.Image',
        '/side_camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
    ]
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='cans_bridge',
        arguments=bridge_args,
        output='screen',
    )

    return LaunchDescription([gui_arg, simulation, bridge])
