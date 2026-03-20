#!/usr/bin/env python3
"""
Launch file for lab real experiments with the stereo USB camera + ArUco detection.

Launches:
  1. stereo_eye_publisher — publishes one eye of stereo camera as ROS2 Image + CameraInfo
  2. aruco_detector       — detects ArUco marker and publishes pose + debug image
  3. camera_controller    — publishes static TF for the camera position (optional)

Does NOT launch Gazebo or any simulation nodes.

Usage:
    ros2 launch fixed_camera lab_real.launch.py
    ros2 launch fixed_camera lab_real.launch.py device:=/dev/video4
    ros2 launch fixed_camera lab_real.launch.py marker_length:=0.20 height:=2.5
"""

import os
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory("fixed_camera")
    config_file = os.path.join(pkg, "config", "fixed_camera_params.yaml")

    # Try to find stereo_camera config.yaml in workspace
    # This is the path when running from the workspace root
    workspace_dir = str(Path(pkg).parents[2])
    stereo_config = os.path.join(workspace_dir, "stereo_camera", "config.yaml")

    # ── Launch arguments ──────────────────────────────────────────
    device = LaunchConfiguration("device")
    eye = LaunchConfiguration("eye")
    fps = LaunchConfiguration("fps")
    marker_length = LaunchConfiguration("marker_length")
    height = LaunchConfiguration("height")

    declare_device = DeclareLaunchArgument(
        "device", default_value="/dev/video2",
        description="Camera device path",
    )
    declare_eye = DeclareLaunchArgument(
        "eye", default_value="left",
        description="Which eye to use: left or right",
    )
    declare_fps = DeclareLaunchArgument(
        "fps", default_value="30",
        description="Camera FPS",
    )
    declare_marker_length = DeclareLaunchArgument(
        "marker_length", default_value="0.20",
        description="ArUco marker side length in meters",
    )
    declare_height = DeclareLaunchArgument(
        "height", default_value="2.0",
        description="Camera height (Z position in meters)",
    )

    # ── 1. Stereo Eye Publisher ───────────────────────────────────
    stereo_eye_pub = Node(
        package="fixed_camera",
        executable="stereo_eye_publisher",
        name="stereo_eye_publisher",
        output="screen",
        parameters=[
            {
                "device": device,
                "eye": eye,
                "fps": fps,
                "full_width": 3840,
                "full_height": 1080,
                "config_path": stereo_config,
                "use_sim_time": False,
            }
        ],
    )

    # ── 2. ArUco Detector ────────────────────────────────────────
    aruco_detector = Node(
        package="fixed_camera",
        executable="aruco_detector",
        name="aruco_detector",
        output="screen",
        parameters=[
            {
                "dictionary": "DICT_6X6_250",
                "target_id": 0,
                "marker_length_m": marker_length,
                "publish_debug_image": True,
                "image_topic": "/stereo_camera/image_raw",
                "camera_info_topic": "/stereo_camera/camera_info",
                "use_sim_time": False,
            }
        ],
    )

    # ── 3. Camera Controller (static TF publisher) ──────────────
    camera_controller = Node(
        package="fixed_camera",
        executable="camera_controller",
        name="camera_controller",
        output="screen",
        parameters=[
            config_file,
            {
                "position_z": height,
                "use_sim_time": False,
            },
        ],
    )

    # ── 4. Static TF: world → odom ──────────────────────────────
    static_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="static_tf_world_odom",
        arguments=["0", "0", "0", "0", "0", "0", "world", "odom"],
        parameters=[{"use_sim_time": False}],
    )

    return LaunchDescription([
        declare_device,
        declare_eye,
        declare_fps,
        declare_marker_length,
        declare_height,
        static_tf,
        stereo_eye_pub,
        aruco_detector,
        camera_controller,
    ])
