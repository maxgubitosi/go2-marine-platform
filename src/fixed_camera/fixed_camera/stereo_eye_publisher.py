#!/usr/bin/env python3
"""
Stereo Eye Publisher — Publishes one eye of the 3D USB stereo camera as ROS2 topics.

Opens the stereo camera (side-by-side 3840×1080), crops the selected eye
(1920×1080), and publishes:
    /stereo_camera/image_raw    (sensor_msgs/Image)      — BGR8 image
    /stereo_camera/camera_info  (sensor_msgs/CameraInfo)  — calibrated intrinsics

Parameters:
    device          : Camera device path (default: /dev/video2)
    eye             : "left" or "right" (default: left)
    fps             : Target FPS (default: 30)
    full_width      : Full stereo frame width (default: 3840)
    full_height     : Full stereo frame height (default: 1080)
    config_path     : Path to stereo_camera/config.yaml for intrinsics
"""
from __future__ import annotations

import os
from pathlib import Path

import cv2
import numpy as np
import rclpy
import yaml
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo, Image


class StereoEyePublisher(Node):
    def __init__(self) -> None:
        super().__init__("stereo_eye_publisher")

        # ── Parameters ────────────────────────────────────────────
        self.declare_parameter("device", "/dev/video2")
        self.declare_parameter("eye", "left")
        self.declare_parameter("fps", 30)
        self.declare_parameter("full_width", 3840)
        self.declare_parameter("full_height", 1080)
        # Default: look for config.yaml relative to workspace
        default_config = str(
            Path(__file__).resolve().parents[3] / "stereo_camera" / "config.yaml"
        )
        self.declare_parameter("config_path", default_config)

        self.device = self.get_parameter("device").value
        self.eye = self.get_parameter("eye").value
        self.fps = self.get_parameter("fps").value
        self.full_w = self.get_parameter("full_width").value
        self.full_h = self.get_parameter("full_height").value
        config_path = self.get_parameter("config_path").value

        self.eye_w = self.full_w // 2
        self.eye_h = self.full_h

        # ── Load intrinsics from config ───────────────────────────
        self.camera_matrix = None
        self.dist_coeffs = None
        self._load_intrinsics(config_path)

        # ── Publishers ────────────────────────────────────────────
        self.pub_image = self.create_publisher(
            Image, "/stereo_camera/image_raw", 10
        )
        self.pub_info = self.create_publisher(
            CameraInfo, "/stereo_camera/camera_info", 10
        )

        # ── Open camera ──────────────────────────────────────────
        dev_index = int(self.device.replace("/dev/video", ""))
        self.cap = cv2.VideoCapture(dev_index, cv2.CAP_V4L2)
        if not self.cap.isOpened():
            self.get_logger().fatal(f"Cannot open camera {self.device}")
            raise SystemExit(1)

        fourcc = cv2.VideoWriter_fourcc(*"MJPG")
        self.cap.set(cv2.CAP_PROP_FOURCC, fourcc)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.full_w)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.full_h)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)

        actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        if actual_w != self.full_w:
            self.eye_w = actual_w // 2
            self.eye_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.get_logger().warn(
                f"Actual resolution: {actual_w}×{self.eye_h}, eye: {self.eye_w}×{self.eye_h}"
            )

        # ── Timer for capture loop ───────────────────────────────
        period = 1.0 / self.fps
        self.timer = self.create_timer(period, self._timer_callback)
        self.frame_count = 0

        self.get_logger().info(
            f"StereoEyePublisher started — device={self.device} eye={self.eye} "
            f"resolution={self.eye_w}×{self.eye_h} fps={self.fps}"
        )

    def _load_intrinsics(self, config_path: str) -> None:
        """Load camera intrinsics from stereo_camera/config.yaml."""
        try:
            with open(config_path, "r") as f:
                cfg = yaml.safe_load(f)
            intr = cfg.get("intrinsics", {})
            if intr.get("matrix") is not None and intr.get("dist_coeffs") is not None:
                self.camera_matrix = np.array(intr["matrix"], dtype=np.float64)
                self.dist_coeffs = np.array(
                    intr["dist_coeffs"], dtype=np.float64
                ).flatten()
                self.get_logger().info(
                    f"Intrinsics loaded: fx={self.camera_matrix[0,0]:.2f} "
                    f"fy={self.camera_matrix[1,1]:.2f} "
                    f"cx={self.camera_matrix[0,2]:.2f} "
                    f"cy={self.camera_matrix[1,2]:.2f} "
                    f"dist=[{', '.join(f'{d:.4f}' for d in self.dist_coeffs)}]"
                )
            else:
                self.get_logger().warn(
                    f"No calibration data in {config_path} — publishing zero intrinsics"
                )
        except Exception as e:
            self.get_logger().warn(f"Could not load config: {e}")

    def _build_camera_info(self, stamp) -> CameraInfo:
        """Build CameraInfo message from loaded intrinsics."""
        msg = CameraInfo()
        msg.header.stamp = stamp
        msg.header.frame_id = "stereo_camera_optical"
        msg.width = self.eye_w
        msg.height = self.eye_h
        msg.distortion_model = "plumb_bob"

        if self.camera_matrix is not None:
            K = self.camera_matrix
            msg.k = [
                K[0, 0], K[0, 1], K[0, 2],
                K[1, 0], K[1, 1], K[1, 2],
                K[2, 0], K[2, 1], K[2, 2],
            ]
            D = self.dist_coeffs
            msg.d = [float(d) for d in D]
            # P = [fx 0 cx 0; 0 fy cy 0; 0 0 1 0]
            msg.p = [
                K[0, 0], 0.0, K[0, 2], 0.0,
                0.0, K[1, 1], K[1, 2], 0.0,
                0.0, 0.0, 1.0, 0.0,
            ]
            # R = identity
            msg.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]

        return msg

    def _crop_eye(self, frame: np.ndarray) -> np.ndarray:
        if self.eye == "left":
            return frame[:, : self.eye_w]
        else:
            return frame[:, self.eye_w :]

    def _timer_callback(self) -> None:
        ret, frame = self.cap.read()
        if not ret:
            self.get_logger().warn("Failed to read frame")
            return

        eye_img = self._crop_eye(frame)
        stamp = self.get_clock().now().to_msg()

        # Publish Image (BGR8)
        img_msg = Image()
        img_msg.header.stamp = stamp
        img_msg.header.frame_id = "stereo_camera_optical"
        img_msg.height = eye_img.shape[0]
        img_msg.width = eye_img.shape[1]
        img_msg.encoding = "bgr8"
        img_msg.is_bigendian = 0
        img_msg.step = eye_img.shape[1] * 3
        img_msg.data = bytes(np.ascontiguousarray(eye_img).data)
        self.pub_image.publish(img_msg)

        # Publish CameraInfo
        info_msg = self._build_camera_info(stamp)
        self.pub_info.publish(info_msg)

        self.frame_count += 1
        if self.frame_count % (self.fps * 5) == 0:
            self.get_logger().info(f"Published {self.frame_count} frames")

    def destroy_node(self) -> None:
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = StereoEyePublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
