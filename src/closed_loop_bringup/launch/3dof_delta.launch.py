import os
from os import pathsep
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
)
from launch.substitutions import (
    LaunchConfiguration,
    PathJoinSubstitution,
    PythonExpression,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro


def generate_launch_description():
    closed_loop_description = get_package_share_directory("closed_loop_description")

    model_arg = DeclareLaunchArgument(
        name="model",
        default_value=os.path.join(closed_loop_description, "urdf", "3dof_delta.urdf.xacro"),
        description="Absolute path to robot urdf file",
    )

    world_name_arg = DeclareLaunchArgument(name="world_name", default_value="delta_world")

    # gui:=false -> chỉ chạy server Gazebo (không cửa sổ). Dùng khi có camera mô phỏng: trên máy
    # render bằng GPU tích hợp, cửa sổ Gazebo + camera tranh GPU làm tốc độ mô phỏng tụt ~0.35.
    gui_arg = DeclareLaunchArgument(
        name="gui",
        default_value="true",
        description="false = run the Gazebo server without the GUI window",
    )

    world_path = PathJoinSubstitution(
        [
            closed_loop_description,
            "worlds",
            PythonExpression(
                expression=["'", LaunchConfiguration("world_name"), "'", " + '.sdf'"]
            ),
        ]
    )

    model_path = str(Path(closed_loop_description).parent.resolve())
    model_path += pathsep + os.path.join(closed_loop_description, "meshes")

    gazebo_resource_path = SetEnvironmentVariable("GZ_SIM_RESOURCE_PATH", model_path)

    robot_description_content = xacro.process_file(
        os.path.join(closed_loop_description, "urdf", "3dof_delta.urdf.xacro")
    ).toxml()

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{"robot_description": robot_description_content, "use_sim_time": True}],
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(get_package_share_directory("ros_gz_sim"), "launch"),
                "/gz_sim.launch.py",
            ]
        ),
        launch_arguments={
            "gz_args": PythonExpression(
                [
                    "' ", world_path, " -v 4 -r' + ('' if '",
                    LaunchConfiguration("gui"), "'.lower() == 'true' else ' -s')",
                ]
            )
        }.items(),
    )

    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-topic",
            "robot_description",
            "-name",
            "delta_3dof",
        ],
    )

    # Gazebo publishes only the actuated joints (the URDF JointStatePublisher is filtered),
    # mimicking real encoders. Bridge that back to ROS as /joint_states_raw, throttled below.
    gz_joint_state_topic = "/world/delta_world/model/delta_3dof/joint_state"

    gz_ros2_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
            "/delta_3dof/Chain1_1/cmd_pos@std_msgs/msg/Float64]gz.msgs.Double",
            "/delta_3dof/Chain2_1/cmd_pos@std_msgs/msg/Float64]gz.msgs.Double",
            "/delta_3dof/Chain3_1/cmd_pos@std_msgs/msg/Float64]gz.msgs.Double",
            gz_joint_state_topic + "@sensor_msgs/msg/JointState[gz.msgs.Model",
        ],
        remappings=[(gz_joint_state_topic, "/joint_states_raw")],
    )

    # Gazebo JointStatePublisher (gz-sim8) publishes on EVERY physics step (~2000 Hz at 0.5 ms) and
    # has no update_rate option, so every Python subscriber would process thousands of messages per
    # second. Throttle to 100 Hz (the Cartesian control loop runs at 50 Hz) in C++ topic_tools.
    # (/clock has the same rate: do not give Python nodes use_sim_time unless they need it.)
    joint_state_throttle = Node(
        package="topic_tools",
        executable="throttle",
        name="joint_state_throttle",
        # Jazzy's throttle reads the mode from argv only ("Throttle type is missing" with params).
        arguments=["messages", "/joint_states_raw", "100.0", "/joint_states"],
    )

    return LaunchDescription(
        [
            model_arg,
            world_name_arg,
            gui_arg,
            robot_state_publisher_node,
            gazebo_resource_path,
            gazebo,
            gz_spawn_entity,
            gz_ros2_bridge,
            joint_state_throttle,
        ]
    )
