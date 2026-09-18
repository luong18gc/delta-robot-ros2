"""
Mô phỏng gắp–thả: robot delta 3-DOF + bàn, vật, khay + giác hút ảo + camera + nhận dạng màu.

ros2 launch delta_controller pick_place.launch.py            # co cua so Gazebo
ros2 launch delta_controller pick_place.launch.py gui:=false  # khong cua so Gazebo
Xem ảnh nhận dạng: ros2 run rqt_image_view rqt_image_view /vision/debug_image
Điều khiển:        ros2 run delta_controller cartesian_control
"""

import os

from ament_index_python.packages import get_package_share_directory
from delta_controller.scene import OBJECTS
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

# Danh sách vật lấy từ delta_controller/scene.py; phải khớp với
# closed_loop_description/urdf/3dof_delta.gripper.xacro và worlds/delta_objects_world.sdf.


def generate_launch_description():
    bringup = get_package_share_directory('closed_loop_bringup')

    gui_arg = DeclareLaunchArgument(
        'gui', default_value='true',
        description='false = chay Gazebo khong cua so (nhanh hon khi co camera mo phong)')

    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(bringup, 'launch', '3dof_delta.launch.py')),
        launch_arguments={
            'world_name': 'delta_objects_world',
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
    # Camera nhìn xiên (Bước 8): ảnh + nội tham số từ Gazebo sang ROS.
    bridge_args += [
        '/side_camera/image@sensor_msgs/msg/Image[gz.msgs.Image',
        '/side_camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
    ]
    gripper_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='gripper_bridge',
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
            # KHÔNG bật use_sim_time: node sẽ nhận /clock (Gazebo phát mỗi bước mô phỏng,
            # ~2000 Hz) và ăn trọn 1 nhân CPU (đã đo 103% -> 0.3%). Node chỉ dùng đồng hồ thật.
        }],
    )

    # Nhận dạng vật theo màu từ camera (Bước 8.2): /vision/detections, /vision/debug_image.
    vision = Node(
        package='delta_controller',
        executable='vision',
        output='screen',
    )

    return LaunchDescription([gui_arg, simulation, gripper_bridge, gripper, vision])
