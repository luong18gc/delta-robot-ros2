"""
Mô phỏng gắp–thả: robot delta 3-DOF + bàn, vật, khay + giác hút ảo.

ros2 launch delta_controller pick_place.launch.py
Sau đó ở terminal khác: ros2 run delta_controller cartesian_control
"""

import os

from ament_index_python.packages import get_package_share_directory
from delta_controller.scene import OBJECTS
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

# Danh sách vật lấy từ delta_controller/scene.py; phải khớp với
# closed_loop_description/urdf/3dof_delta.gripper.xacro và worlds/delta_objects_world.sdf.


def generate_launch_description():
    bringup = get_package_share_directory('closed_loop_bringup')

    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(bringup, 'launch', '3dof_delta.launch.py')),
        launch_arguments={'world_name': 'delta_objects_world'}.items(),
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
            'use_sim_time': True,
        }],
    )

    return LaunchDescription([simulation, gripper_bridge, gripper])
