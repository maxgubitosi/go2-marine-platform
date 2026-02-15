#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_drone = get_package_share_directory('drone')
    
    urdf_file = os.path.join(pkg_drone, 'urdf', 'drone_camera.xacro')
    config_file = os.path.join(pkg_drone, 'config', 'drone_params.yaml')
    aruco_config = os.path.join(pkg_drone, 'config', 'aruco_detector_params.yaml')
    
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation clock'
    )
    
    robot_description_content = ParameterValue(
        Command(['xacro ', urdf_file]),
        value_type=str
    )
    
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='drone_robot_state_publisher',
        output='screen',
        parameters=[
            {
                'robot_description': robot_description_content,
                'use_sim_time': use_sim_time,
                'frame_prefix': ''
            }
        ],
        remappings=[
            ('/robot_description', '/drone/robot_description')
        ]
    )
    
    spawn_drone = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        name='spawn_drone',
        output='screen',
        arguments=[
            '-entity', 'drone',
            '-topic', '/drone/robot_description',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '2.0',
        ],
        parameters=[{'use_sim_time': use_sim_time}]
    )
    
    drone_controller = Node(
        package='drone',
        executable='drone_controller',
        name='drone_controller',
        output='screen',
        parameters=[config_file, {'use_sim_time': use_sim_time}]
    )

    aruco_detector = Node(
        package='drone',
        executable='aruco_detector',
        name='aruco_detector',
        output='screen',
        parameters=[aruco_config, {'use_sim_time': use_sim_time}]
    )
    
    static_tf_world_odom = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_tf_world_odom',
        arguments=['0', '0', '0', '0', '0', '0', 'world', 'odom'],
        parameters=[{'use_sim_time': use_sim_time}]
    )
    
    return LaunchDescription([
        declare_use_sim_time,
        static_tf_world_odom,
        robot_state_publisher,
        spawn_drone,
        drone_controller,
        aruco_detector,
    ])
