"""
BẢN SAO SỐ (Bước 10b): camera THẬT nhìn lon THẬT -> lon ẢO trong Gazebo đi theo.

    ros2 launch delta_controller digital_twin.launch.py

Khác `pick_place.launch.py` ở ba chỗ:

1. Chạy `real_vision` (camera C270 thật) chứ KHÔNG chạy `vision` (camera mô phỏng). Hai node cùng
   phát `/vision/objects` thì kết quả lẫn lộn — chỉ được chạy đúng một.
2. Thêm cầu nối DỊCH VỤ `/world/delta_world/set_pose`. Gọi `gz service` bằng tiến trình con mất
   ~0.37 s mỗi lần (đo khi thu bộ dữ liệu 8.4), tức 3 lon đã hơn một giây — không theo kịp camera
   10 Hz. Qua cầu nối thì nó là dịch vụ ROS bình thường.
3. Thêm `digital_twin` — node chép vị trí sang Gazebo.

⚠️ Phải có `calibration/table_reference.png` (chụp bằng scripts/capture_table_reference.py) và
`calibration/c270_intrinsics.yaml`, và 6 marker phải nằm trong khung hình.
"""

import os

from ament_index_python.packages import get_package_share_directory
from delta_controller.scene import OBJECTS
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

WORLD = 'delta_world'          # tên world bên trong delta_cans_world.sdf (giữ nguyên từ repo gốc)


def generate_launch_description():
    """Mô phỏng + giác hút + camera thật + chép vị trí sang Gazebo."""
    bringup = get_package_share_directory('closed_loop_bringup')

    gui_arg = DeclareLaunchArgument(
        'gui', default_value='true',
        description='false = chay Gazebo khong cua so')

    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(bringup, 'launch', '3dof_delta.launch.py')),
        launch_arguments={
            'world_name': 'delta_cans_world',
            'gui': LaunchConfiguration('gui'),
        }.items(),
    )

    bridge_args = []
    for name in (o.name for o in OBJECTS):
        prefix = f'/delta_3dof/gripper/{name}'
        bridge_args += [
            f'{prefix}/attach@std_msgs/msg/Empty]gz.msgs.Empty',
            f'{prefix}/detach@std_msgs/msg/Empty]gz.msgs.Empty',
            f'{prefix}/state@std_msgs/msg/String[gz.msgs.StringMsg',
            f'/objects/{name}/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry',
        ]
    # Dịch vụ đặt lại vị trí model — đường để bản sao số ghi vào Gazebo.
    bridge_args += [f'/world/{WORLD}/set_pose@ros_gz_interfaces/srv/SetEntityPose']

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='twin_bridge',
        arguments=bridge_args,
        output='screen',
    )

    gripper = Node(
        package='delta_controller',
        executable='gripper',
        output='screen',
        parameters=[{
            'objects': [o.name for o in OBJECTS],
            'object_half_heights': [o.half_height for o in OBJECTS],
        }],
    )

    real_vision = Node(
        package='delta_controller',
        executable='real_vision',
        output='screen',
    )

    twin = Node(
        package='delta_controller',
        executable='digital_twin',
        output='screen',
        parameters=[{'world': WORLD}],
    )

    return LaunchDescription([gui_arg, simulation, bridge, gripper, real_vision, twin])
