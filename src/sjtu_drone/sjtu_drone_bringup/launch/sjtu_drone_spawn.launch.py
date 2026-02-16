#!/usr/bin/env python3
"""
Launch file para spawnar el sjtu_drone en un Gazebo ya corriendo.
NO lanza un nuevo servidor Gazebo — asume que go2_config/gazebo.launch.py ya está corriendo.

Uso:
    ros2 launch sjtu_drone_bringup sjtu_drone_spawn.launch.py
    ros2 launch sjtu_drone_bringup sjtu_drone_spawn.launch.py aruco:=false
    ros2 launch sjtu_drone_bringup sjtu_drone_spawn.launch.py spawn_x:=3.0
"""

import os

import yaml
import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # ── Paths ─────────────────────────────────────────────────────────
    pkg_sjtu_bringup = get_package_share_directory('sjtu_drone_bringup')
    pkg_sjtu_desc = get_package_share_directory('sjtu_drone_description')

    drone_yaml = os.path.join(pkg_sjtu_bringup, 'config', 'drone.yaml')
    position_params = os.path.join(pkg_sjtu_bringup, 'config', 'drone_position_params.yaml')
    aruco_params = os.path.join(pkg_sjtu_bringup, 'config', 'aruco_detector_params.yaml')
    xacro_file = os.path.join(pkg_sjtu_desc, 'urdf', 'sjtu_drone.urdf.xacro')

    # ── Launch arguments ──────────────────────────────────────────────
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    aruco_arg = LaunchConfiguration('aruco')
    spawn_x = LaunchConfiguration('spawn_x')
    spawn_y = LaunchConfiguration('spawn_y')
    spawn_z = LaunchConfiguration('spawn_z')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time', default_value='true',
        description='Use simulation clock'
    )
    declare_aruco = DeclareLaunchArgument(
        'aruco', default_value='true',
        description='Launch ArUco detector node'
    )
    declare_spawn_x = DeclareLaunchArgument(
        'spawn_x', default_value='2.0',
        description='Drone spawn X position (offset to avoid collision with robot)'
    )
    declare_spawn_y = DeclareLaunchArgument(
        'spawn_y', default_value='0.0',
        description='Drone spawn Y position'
    )
    declare_spawn_z = DeclareLaunchArgument(
        'spawn_z', default_value='0.08',
        description='Drone spawn Z position (just above ground, takeoff is automatic)'
    )

    # ── Process xacro → URDF ─────────────────────────────────────────
    robot_description_config = xacro.process_file(
        xacro_file,
        mappings={'params_path': drone_yaml}
    )
    robot_desc = robot_description_config.toxml()

    # Read namespace from yaml
    with open(drone_yaml, 'r') as f:
        yaml_dict = yaml.safe_load(f)
    model_ns = yaml_dict.get('namespace', '/drone').lstrip('/')

    # ── Nodes ─────────────────────────────────────────────────────────

    # Robot State Publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='drone_robot_state_publisher',
        namespace=model_ns,
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'robot_description': robot_desc,
            'frame_prefix': model_ns + '/',
        }],
    )

    # Joint State Publisher
    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='drone_joint_state_publisher',
        namespace=model_ns,
        output='screen',
    )

    # Spawn del sjtu_drone en el Gazebo existente
    spawn_drone = Node(
        package='sjtu_drone_bringup',
        executable='spawn_drone',
        arguments=[robot_desc, model_ns, spawn_x, spawn_y, spawn_z],
        output='screen',
    )

    # Static TF: world → drone/odom
    static_tf_world_odom = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_tf_drone_odom',
        arguments=['0', '0', '0', '0', '0', '0', 'world', f'{model_ns}/odom'],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
    )

    # Controlador de posición (takeoff automático + hover)
    drone_position_controller = Node(
        package='sjtu_drone_control',
        executable='drone_position_controller',
        name='drone_position_controller',
        output='screen',
        parameters=[position_params, {'use_sim_time': use_sim_time}],
    )

    # Detector ArUco (cámara bottom del sjtu_drone)
    aruco_detector = Node(
        package='sjtu_drone_control',
        executable='aruco_detector',
        name='aruco_detector',
        output='screen',
        parameters=[aruco_params, {'use_sim_time': use_sim_time}],
        condition=IfCondition(aruco_arg),
    )

    return LaunchDescription([
        declare_use_sim_time,
        declare_aruco,
        declare_spawn_x,
        declare_spawn_y,
        declare_spawn_z,
        static_tf_world_odom,
        robot_state_publisher,
        joint_state_publisher,
        spawn_drone,
        drone_position_controller,
        aruco_detector,
    ])
