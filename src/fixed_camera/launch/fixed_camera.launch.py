#!/usr/bin/env python3
"""
Launch file para la cámara fija.

Spawnea una cámara estática en Gazebo mirando hacia abajo.
No se mueve — queda fija en la posición configurada.

Uso:
    ros2 launch fixed_camera fixed_camera.launch.py
    ros2 launch fixed_camera fixed_camera.launch.py aruco:=false
    ros2 launch fixed_camera fixed_camera.launch.py height:=3.0
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg = get_package_share_directory('fixed_camera')

    urdf_file = os.path.join(pkg, 'urdf', 'fixed_camera.xacro')
    config_file = os.path.join(pkg, 'config', 'fixed_camera_params.yaml')
    aruco_config = os.path.join(pkg, 'config', 'aruco_detector_params.yaml')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    aruco = LaunchConfiguration('aruco')
    height = LaunchConfiguration('height')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time', default_value='true',
        description='Use simulation clock'
    )

    declare_aruco = DeclareLaunchArgument(
        'aruco', default_value='true',
        description='Launch ArUco detector node'
    )

    declare_height = DeclareLaunchArgument(
        'height', default_value='2.0',
        description='Camera height (Z position)'
    )

    robot_description_content = ParameterValue(
        Command(['xacro ', urdf_file]),
        value_type=str
    )

    # Robot State Publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='camera_robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description_content,
            'use_sim_time': use_sim_time,
            'frame_prefix': ''
        }],
        remappings=[
            ('/robot_description', '/fixed_camera/robot_description')
        ]
    )

    # Spawn en Gazebo — posición fija, no se mueve
    spawn_camera = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        name='spawn_fixed_camera',
        output='screen',
        arguments=[
            '-entity', 'fixed_camera',
            '-topic', '/fixed_camera/robot_description',
            '-x', '0.0',
            '-y', '0.0',
            '-z', height,
        ],
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # Controlador (publica pose fija + TF estático)
    camera_controller = Node(
        package='fixed_camera',
        executable='camera_controller',
        name='camera_controller',
        output='screen',
        parameters=[config_file, {'use_sim_time': use_sim_time}]
    )

    # Detector ArUco (opcional)
    aruco_detector = Node(
        package='fixed_camera',
        executable='aruco_detector',
        name='aruco_detector',
        output='screen',
        parameters=[aruco_config, {'use_sim_time': use_sim_time}],
        condition=IfCondition(aruco)
    )

    # TF estático: world → odom
    static_tf_world_odom = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_tf_world_odom',
        arguments=['0', '0', '0', '0', '0', '0', 'world', 'odom'],
        parameters=[{'use_sim_time': use_sim_time}]
    )

    return LaunchDescription([
        declare_use_sim_time,
        declare_aruco,
        declare_height,
        static_tf_world_odom,
        robot_state_publisher,
        spawn_camera,
        camera_controller,
        aruco_detector,
    ])
