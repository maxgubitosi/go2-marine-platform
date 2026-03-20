#!/usr/bin/env python3
"""
ArUco Detector Node – Real-time marker pose estimation.

Subscribes to the camera image, detects an ArUco marker (DICT_6X6_250
id 0 by default) and publishes the marker pose **in the camera optical frame**.

No ground-truth or robot model knowledge is used here.  Error analysis is
done offline from a recorded rosbag.

Published topics:
    /aruco/pose          (geometry_msgs/PoseStamped) – marker in camera frame
    /aruco/detection     (std_msgs/Bool)             – detection flag
    /aruco/debug_image   (sensor_msgs/Image)         – annotated image (optional)
"""
from __future__ import annotations

import math

import cv2
import numpy as np
import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo, Image
from std_msgs.msg import Bool

# ── ArUco dictionary name → OpenCV constant ──────────────────────────
ARUCO_DICTS = {
    "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
    "DICT_4X4_100": cv2.aruco.DICT_4X4_100,
    "DICT_4X4_250": cv2.aruco.DICT_4X4_250,
    "DICT_4X4_1000": cv2.aruco.DICT_4X4_1000,
    "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
    "DICT_5X5_100": cv2.aruco.DICT_5X5_100,
    "DICT_5X5_250": cv2.aruco.DICT_5X5_250,
    "DICT_5X5_1000": cv2.aruco.DICT_5X5_1000,
    "DICT_6X6_50": cv2.aruco.DICT_6X6_50,
    "DICT_6X6_100": cv2.aruco.DICT_6X6_100,
    "DICT_6X6_250": cv2.aruco.DICT_6X6_250,
    "DICT_6X6_1000": cv2.aruco.DICT_6X6_1000,
    "DICT_7X7_50": cv2.aruco.DICT_7X7_50,
    "DICT_7X7_100": cv2.aruco.DICT_7X7_100,
    "DICT_7X7_250": cv2.aruco.DICT_7X7_250,
    "DICT_7X7_1000": cv2.aruco.DICT_7X7_1000,
    "DICT_ARUCO_ORIGINAL": cv2.aruco.DICT_ARUCO_ORIGINAL,
}


class ArucoDetector(Node):
    """Lightweight real-time ArUco detector."""

    def __init__(self) -> None:
        super().__init__("aruco_detector")

        # ── Parameters ────────────────────────────────────────────────
        self.declare_parameter("dictionary", "DICT_6X6_250")
        self.declare_parameter("target_id", 0)
        self.declare_parameter("marker_length_m", 0.50)
        self.declare_parameter("publish_debug_image", True)
        self.declare_parameter("image_topic", "/fixed_camera/image_raw")
        self.declare_parameter("camera_info_topic", "/fixed_camera/camera_info")

        dict_name = self.get_parameter("dictionary").value
        self.target_id = self.get_parameter("target_id").value
        self.marker_length = self.get_parameter("marker_length_m").value
        self.publish_debug = self.get_parameter("publish_debug_image").value
        image_topic = self.get_parameter("image_topic").value
        camera_info_topic = self.get_parameter("camera_info_topic").value

        # ── Build ArUco detector ──────────────────────────────────────
        if dict_name not in ARUCO_DICTS:
            self.get_logger().fatal(f"Unknown ArUco dictionary: {dict_name}")
            raise SystemExit(1)

        dictionary = cv2.aruco.getPredefinedDictionary(ARUCO_DICTS[dict_name])
        parameters = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(dictionary, parameters)

        # ── Camera intrinsics (filled from CameraInfo) ────────────────
        self.camera_matrix: np.ndarray | None = None
        self.dist_coeffs: np.ndarray | None = None

        # ── ROS plumbing ──────────────────────────────────────────────
        self.sub_image = self.create_subscription(
            Image, image_topic, self.image_callback, 10
        )
        self.sub_caminfo = self.create_subscription(
            CameraInfo, camera_info_topic, self.caminfo_callback, 10
        )

        self.pub_pose = self.create_publisher(PoseStamped, "/aruco/pose", 10)
        self.pub_detection = self.create_publisher(Bool, "/aruco/detection", 10)
        if self.publish_debug:
            self.pub_debug = self.create_publisher(Image, "/aruco/debug_image", 10)

        self.get_logger().info(
            f"ArucoDetector started – dict={dict_name}  id={self.target_id}  "
            f"side={self.marker_length}m  debug_img={self.publish_debug}"
        )

    # ── CameraInfo callback ──────────────────────────────────────────
    def caminfo_callback(self, msg: CameraInfo) -> None:
        if self.camera_matrix is not None:
            return  # already set
        self.camera_matrix = np.array(msg.k, dtype=np.float64).reshape(3, 3)
        self.dist_coeffs = np.array(msg.d, dtype=np.float64).reshape(-1, 1)
        self.get_logger().info(
            f"Camera intrinsics received: fx={self.camera_matrix[0,0]:.2f}  "
            f"fy={self.camera_matrix[1,1]:.2f}  cx={self.camera_matrix[0,2]:.1f}  "
            f"cy={self.camera_matrix[1,2]:.1f}"
        )

    # ── Image callback (main pipeline) ───────────────────────────────
    def image_callback(self, msg: Image) -> None:
        if self.camera_matrix is None:
            return  # no calibration yet

        # Convert ROS Image → OpenCV BGR
        try:
            img_array = np.frombuffer(msg.data, dtype=np.uint8).reshape(
                msg.height, msg.width, -1
            )
            if msg.encoding == "rgb8":
                cv_image = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            elif msg.encoding == "bgr8":
                cv_image = img_array.copy()
            elif msg.encoding == "mono8":
                cv_image = cv2.cvtColor(
                    img_array.reshape(msg.height, msg.width), cv2.COLOR_GRAY2BGR
                )
            else:
                cv_image = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        except Exception as e:
            self.get_logger().warn(f"Image conversion error: {e}")
            return
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

        # Detect markers
        corners, ids, _ = self.detector.detectMarkers(gray)

        detected = False
        if ids is not None and len(ids) > 0:
            ids_flat = ids.flatten().tolist()
            if self.target_id in ids_flat:
                idx = ids_flat.index(self.target_id)
                corner = corners[idx]

                # Pose estimation via solvePnP (estimatePoseSingleMarkers
                # was removed in OpenCV 4.8+)
                half = self.marker_length / 2.0
                obj_pts = np.array([
                    [-half,  half, 0],
                    [ half,  half, 0],
                    [ half, -half, 0],
                    [-half, -half, 0],
                ], dtype=np.float32)
                img_pts = corner.reshape(4, 2)
                _, rvec, tvec = cv2.solvePnP(
                    obj_pts, img_pts, self.camera_matrix, self.dist_coeffs
                )

                # Build PoseStamped (marker in camera optical frame)
                pose_msg = PoseStamped()
                pose_msg.header = msg.header  # same stamp & frame
                pose_msg.pose.position.x = float(tvec[0, 0])
                pose_msg.pose.position.y = float(tvec[1, 0])
                pose_msg.pose.position.z = float(tvec[2, 0])

                # Rodrigues → rotation matrix → quaternion
                R, _ = cv2.Rodrigues(rvec)
                qx, qy, qz, qw = self._rotation_matrix_to_quaternion(R)
                pose_msg.pose.orientation.x = qx
                pose_msg.pose.orientation.y = qy
                pose_msg.pose.orientation.z = qz
                pose_msg.pose.orientation.w = qw

                self.pub_pose.publish(pose_msg)
                detected = True

                # Debug image
                if self.publish_debug:
                    cv2.aruco.drawDetectedMarkers(
                        cv_image, corners, ids
                    )
                    cv2.drawFrameAxes(
                        cv_image,
                        self.camera_matrix,
                        self.dist_coeffs,
                        rvec,
                        tvec,
                        self.marker_length * 0.5,
                    )

        # Always publish detection flag
        det_msg = Bool()
        det_msg.data = detected
        self.pub_detection.publish(det_msg)

        # Publish debug image (even if no detection, so we can see the raw feed)
        if self.publish_debug:
            try:
                # Convert BGR→RGB for rqt_image_view compatibility
                cv_rgb = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
                cv_out = np.ascontiguousarray(cv_rgb)
                debug_msg = Image()
                debug_msg.header = msg.header
                debug_msg.height = cv_out.shape[0]
                debug_msg.width = cv_out.shape[1]
                debug_msg.encoding = "rgb8"
                debug_msg.is_bigendian = 0
                debug_msg.step = cv_out.shape[1] * 3
                debug_msg.data = bytes(cv_out.data)
                self.pub_debug.publish(debug_msg)
            except Exception as e:
                self.get_logger().warn(f"Debug image publish error: {e}")

    # ── Helpers ───────────────────────────────────────────────────────
    @staticmethod
    def _rotation_matrix_to_quaternion(R: np.ndarray):
        """Convert a 3×3 rotation matrix to quaternion (x, y, z, w)."""
        trace = R[0, 0] + R[1, 1] + R[2, 2]
        if trace > 0:
            s = 0.5 / math.sqrt(trace + 1.0)
            w = 0.25 / s
            x = (R[2, 1] - R[1, 2]) * s
            y = (R[0, 2] - R[2, 0]) * s
            z = (R[1, 0] - R[0, 1]) * s
        elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
            s = 2.0 * math.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2])
            w = (R[2, 1] - R[1, 2]) / s
            x = 0.25 * s
            y = (R[0, 1] + R[1, 0]) / s
            z = (R[0, 2] + R[2, 0]) / s
        elif R[1, 1] > R[2, 2]:
            s = 2.0 * math.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2])
            w = (R[0, 2] - R[2, 0]) / s
            x = (R[0, 1] + R[1, 0]) / s
            y = 0.25 * s
            z = (R[1, 2] + R[2, 1]) / s
        else:
            s = 2.0 * math.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1])
            w = (R[1, 0] - R[0, 1]) / s
            x = (R[0, 2] + R[2, 0]) / s
            y = (R[1, 2] + R[2, 1]) / s
            z = 0.25 * s
        return float(x), float(y), float(z), float(w)


def main(args=None):
    rclpy.init(args=args)
    node = ArucoDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
