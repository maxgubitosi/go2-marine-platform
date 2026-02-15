#!/usr/bin/env python3
"""
Offline evaluation: compare real-time ArUco pose estimates with ground truth.

Reads a rosbag that contains:
  - /aruco/pose          (PoseStamped)  – real-time estimated marker in camera frame
  - /odom                (Odometry)     – Go2 position (x, y) in world
  - /imu/data            (Imu)          – Go2 orientation (roll, pitch, yaw)
  - /base_to_footprint_pose (PoseWithCovarianceStamped) – heave (trunk z)
  - /drone/pose          (Pose)         – drone position/orientation in world
  - /tf, /tf_static                     – for drone_base_link → camera_optical

Computes the ground-truth marker pose in camera frame using:
  1. Go2 trunk pose in world  (from odom + imu + heave)
  2. Marker = trunk + offset [0, 0, 0.091]
  3. Camera optical frame in world (from drone pose + URDF extrinsics)
  4. marker_in_cam = R_cam_world @ (marker_world - cam_world)

Then compares with the ArUco estimations and produces error metrics + plots.

Usage:
    python3 evaluate_realtime_aruco.py <path_to_rosbag> [--output-dir DIR]
"""
from __future__ import annotations

import argparse
import math
import sqlite3
import sys
from bisect import bisect_left
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

try:
    from rclpy.serialization import deserialize_message
    from geometry_msgs.msg import Pose, PoseStamped, PoseWithCovarianceStamped
    from nav_msgs.msg import Odometry
    from sensor_msgs.msg import Imu
except ImportError:
    print("ERROR: ROS 2 Python packages not found.")
    print("Run: source /opt/ros/humble/setup.bash")
    sys.exit(1)


# ══════════════════════════════════════════════════════════════════════
#  Constants – must match your simulation setup
# ══════════════════════════════════════════════════════════════════════

# Marker offset from Go2 trunk (platform height above trunk center)
MARKER_OFFSET_XYZ = np.array([0.0, 0.0, 0.091], dtype=np.float64)

# Drone camera extrinsics (base_link → camera_optical)
# These come from drone_camera.xacro and are combined into one transform.
BASE_TO_CAMLINK_XYZ = np.array([0.0, 0.0, -0.055], dtype=np.float64)
BASE_TO_CAMLINK_RPY = np.array([0.0, np.pi / 2.0, 0.0], dtype=np.float64)
CAMLINK_TO_OPT_XYZ = np.array([0.0, 0.0, 0.0], dtype=np.float64)
CAMLINK_TO_OPT_RPY = np.array([-np.pi / 2.0, 0.0, -np.pi / 2.0], dtype=np.float64)


# ══════════════════════════════════════════════════════════════════════
#  Math utilities
# ══════════════════════════════════════════════════════════════════════

def rpy_to_rotation_matrix(roll: float, pitch: float, yaw: float) -> np.ndarray:
    cr, sr = np.cos(roll), np.sin(roll)
    cp, sp = np.cos(pitch), np.sin(pitch)
    cy, sy = np.cos(yaw), np.sin(yaw)
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]], dtype=np.float64)
    Ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]], dtype=np.float64)
    Rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]], dtype=np.float64)
    return Rz @ Ry @ Rx


def rotation_matrix_to_euler(R: np.ndarray) -> Tuple[float, float, float]:
    sy = math.sqrt(R[0, 0] ** 2 + R[1, 0] ** 2)
    singular = sy < 1e-6
    if not singular:
        roll = math.atan2(R[2, 1], R[2, 2])
        pitch = math.atan2(-R[2, 0], sy)
        yaw = math.atan2(R[1, 0], R[0, 0])
    else:
        roll = math.atan2(-R[1, 2], R[1, 1])
        pitch = math.atan2(-R[2, 0], sy)
        yaw = 0.0
    return roll, pitch, yaw


def quaternion_to_euler(x: float, y: float, z: float, w: float) -> Tuple[float, float, float]:
    sinr_cosp = 2.0 * (w * x + y * z)
    cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
    roll = math.atan2(sinr_cosp, cosr_cosp)
    sinp = 2.0 * (w * y - z * x)
    pitch = math.copysign(math.pi / 2, sinp) if abs(sinp) >= 1 else math.asin(sinp)
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    yaw = math.atan2(siny_cosp, cosy_cosp)
    return roll, pitch, yaw


def quaternion_to_rotation_matrix(x: float, y: float, z: float, w: float) -> np.ndarray:
    R = np.array([
        [1 - 2*(y*y + z*z), 2*(x*y - z*w),     2*(x*z + y*w)],
        [2*(x*y + z*w),     1 - 2*(x*x + z*z), 2*(y*z - x*w)],
        [2*(x*z - y*w),     2*(y*z + x*w),     1 - 2*(x*x + y*y)],
    ], dtype=np.float64)
    return R


def wrap_angle(a: float) -> float:
    return (a + np.pi) % (2 * np.pi) - np.pi


# ══════════════════════════════════════════════════════════════════════
#  Rosbag reader (SQLite3 format)
# ══════════════════════════════════════════════════════════════════════

def extract_messages(rosbag_path: Path, topic_name: str, message_type):
    db_path = list(rosbag_path.glob("*.db3"))[0]
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM topics WHERE name=?", (topic_name,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return []

    topic_id = result[0]
    cursor.execute(
        "SELECT timestamp, data FROM messages WHERE topic_id=? ORDER BY timestamp",
        (topic_id,),
    )

    messages = []
    for timestamp, data in cursor.fetchall():
        try:
            msg = deserialize_message(data, message_type)
            messages.append((timestamp, msg))
        except Exception:
            pass
    conn.close()
    return messages


def find_closest(sorted_ts: List[int], target: int, threshold_ns: int = 100_000_000):
    idx = bisect_left(sorted_ts, target)
    best_idx, best_diff = None, float("inf")
    for c in [idx - 1, idx]:
        if 0 <= c < len(sorted_ts):
            d = abs(sorted_ts[c] - target)
            if d < best_diff:
                best_diff = d
                best_idx = c
    return best_idx if best_diff <= threshold_ns else None


# ══════════════════════════════════════════════════════════════════════
#  Pre-compute static transforms
# ══════════════════════════════════════════════════════════════════════

def compute_base_to_optical():
    """Return (R_base_opt, t_base_opt) from URDF extrinsics."""
    R_bl_cl = rpy_to_rotation_matrix(*BASE_TO_CAMLINK_RPY)
    R_cl_opt = rpy_to_rotation_matrix(*CAMLINK_TO_OPT_RPY)
    R_base_opt = R_bl_cl @ R_cl_opt
    t_base_opt = BASE_TO_CAMLINK_XYZ + R_bl_cl @ CAMLINK_TO_OPT_XYZ
    return R_base_opt, t_base_opt


# ══════════════════════════════════════════════════════════════════════
#  Main evaluation
# ══════════════════════════════════════════════════════════════════════

def evaluate(rosbag_path: Path, output_dir: Path):
    print(f"Reading rosbag: {rosbag_path}")

    # 1) Read all topics
    aruco_msgs = extract_messages(rosbag_path, "/aruco/pose", PoseStamped)
    odom_msgs = extract_messages(rosbag_path, "/odom", Odometry)
    imu_msgs = extract_messages(rosbag_path, "/imu/data", Imu)
    heave_msgs = extract_messages(rosbag_path, "/base_to_footprint_pose", PoseWithCovarianceStamped)
    drone_msgs = extract_messages(rosbag_path, "/drone/pose", Pose)

    print(f"  /aruco/pose:              {len(aruco_msgs)} messages")
    print(f"  /odom:                    {len(odom_msgs)} messages")
    print(f"  /imu/data:                {len(imu_msgs)} messages")
    print(f"  /base_to_footprint_pose:  {len(heave_msgs)} messages")
    print(f"  /drone/pose:              {len(drone_msgs)} messages")

    if not aruco_msgs:
        print("ERROR: No /aruco/pose messages found in rosbag.")
        print("Make sure the aruco_detector node was running during recording.")
        sys.exit(1)

    if not odom_msgs:
        print("ERROR: No /odom messages. Cannot compute GT.")
        sys.exit(1)

    # 2) Index GT sources for fast lookup
    odom_dict = {ts: msg for ts, msg in odom_msgs}
    odom_ts = sorted(odom_dict.keys())

    imu_dict = {ts: msg for ts, msg in imu_msgs}
    imu_ts = sorted(imu_dict.keys())

    heave_dict = {}
    if heave_msgs:
        heave_dict = {ts: msg.pose.pose.position.z for ts, msg in heave_msgs}
    heave_ts = sorted(heave_dict.keys())

    drone_dict = {ts: msg for ts, msg in drone_msgs}
    drone_ts = sorted(drone_dict.keys())

    # 3) Pre-compute static transforms
    R_base_opt, t_base_opt = compute_base_to_optical()

    # 4) For each ArUco estimation, find the closest GT and drone pose
    threshold_ns = 100_000_000  # 100ms

    records = []
    matched = 0
    skipped = 0

    for aruco_ts, aruco_msg in aruco_msgs:
        # Estimated pose (marker in camera optical frame)
        est_x = aruco_msg.pose.position.x
        est_y = aruco_msg.pose.position.y
        est_z = aruco_msg.pose.position.z
        q = aruco_msg.pose.orientation
        est_R = quaternion_to_rotation_matrix(q.x, q.y, q.z, q.w)
        est_roll, est_pitch, est_yaw = rotation_matrix_to_euler(est_R)

        # Find closest odom
        odom_idx = find_closest(odom_ts, aruco_ts, threshold_ns)
        if odom_idx is None:
            skipped += 1
            continue
        odom_msg = odom_dict[odom_ts[odom_idx]]

        # Find closest IMU
        imu_idx = find_closest(imu_ts, aruco_ts, threshold_ns)
        if imu_idx is None:
            skipped += 1
            continue
        imu_msg = imu_dict[imu_ts[imu_idx]]

        # Go2 trunk pose in world
        trunk_x = odom_msg.pose.pose.position.x
        trunk_y = odom_msg.pose.pose.position.y

        # Heave (trunk z)
        if heave_ts:
            heave_idx = find_closest(heave_ts, aruco_ts, threshold_ns)
            if heave_idx is not None:
                trunk_z = heave_dict[heave_ts[heave_idx]]
            else:
                skipped += 1
                continue
        else:
            trunk_z = odom_msg.pose.pose.position.z

        # Trunk orientation from IMU
        io = imu_msg.orientation
        trunk_roll, trunk_pitch, trunk_yaw = quaternion_to_euler(io.x, io.y, io.z, io.w)

        # Marker in world = trunk + rotated offset
        R_w_trunk = rpy_to_rotation_matrix(trunk_roll, trunk_pitch, trunk_yaw)
        t_w_trunk = np.array([trunk_x, trunk_y, trunk_z], dtype=np.float64)
        t_w_marker = t_w_trunk + R_w_trunk @ MARKER_OFFSET_XYZ
        R_w_marker = R_w_trunk  # marker orientation = trunk orientation

        # Drone pose in world
        if drone_ts:
            drone_idx = find_closest(drone_ts, aruco_ts, threshold_ns)
            if drone_idx is not None:
                dm = drone_dict[drone_ts[drone_idx]]
                drone_pos = np.array([dm.position.x, dm.position.y, dm.position.z], dtype=np.float64)
                dq = dm.orientation
                R_w_drone = quaternion_to_rotation_matrix(dq.x, dq.y, dq.z, dq.w)
            else:
                skipped += 1
                continue
        else:
            # Fallback: fixed drone pose (for older rosbags without /drone/pose)
            drone_pos = np.array([0.0, 0.0, 2.0], dtype=np.float64)
            R_w_drone = np.eye(3)

        # Camera optical frame in world
        R_w_opt = R_w_drone @ R_base_opt
        t_w_opt = drone_pos + R_w_drone @ t_base_opt

        # GT: marker in camera optical frame
        R_opt_w = R_w_opt.T
        gt_t_cam_marker = R_opt_w @ (t_w_marker - t_w_opt)
        gt_R_cam_marker = R_opt_w @ R_w_marker
        gt_roll, gt_pitch, gt_yaw = rotation_matrix_to_euler(gt_R_cam_marker)

        # Errors
        err_x = est_x - gt_t_cam_marker[0]
        err_y = est_y - gt_t_cam_marker[1]
        err_z = est_z - gt_t_cam_marker[2]
        err_pos = math.sqrt(err_x**2 + err_y**2 + err_z**2)

        err_roll = wrap_angle(est_roll - gt_roll)
        err_pitch = wrap_angle(est_pitch - gt_pitch)
        err_yaw = wrap_angle(est_yaw - gt_yaw)

        records.append({
            "timestamp_ns": aruco_ts,
            "timestamp_s": aruco_ts / 1e9,
            # Estimated
            "est_x": est_x,
            "est_y": est_y,
            "est_z": est_z,
            "est_roll": est_roll,
            "est_pitch": est_pitch,
            "est_yaw": est_yaw,
            # Ground truth
            "gt_x": gt_t_cam_marker[0],
            "gt_y": gt_t_cam_marker[1],
            "gt_z": gt_t_cam_marker[2],
            "gt_roll": gt_roll,
            "gt_pitch": gt_pitch,
            "gt_yaw": gt_yaw,
            # Errors
            "err_x": err_x,
            "err_y": err_y,
            "err_z": err_z,
            "err_pos": err_pos,
            "err_roll_rad": err_roll,
            "err_pitch_rad": err_pitch,
            "err_yaw_rad": err_yaw,
            "err_roll_deg": math.degrees(err_roll),
            "err_pitch_deg": math.degrees(err_pitch),
            "err_yaw_deg": math.degrees(err_yaw),
            # Raw GT sources (for debugging)
            "trunk_x": trunk_x,
            "trunk_y": trunk_y,
            "trunk_z": trunk_z,
            "trunk_roll": trunk_roll,
            "trunk_pitch": trunk_pitch,
            "trunk_yaw": trunk_yaw,
            "drone_x": drone_pos[0],
            "drone_y": drone_pos[1],
            "drone_z": drone_pos[2],
        })
        matched += 1

    print(f"\nMatched: {matched}   Skipped: {skipped}")

    if not records:
        print("ERROR: No matched records. Cannot evaluate.")
        sys.exit(1)

    df = pd.DataFrame(records)
    df["t_rel"] = df["timestamp_s"] - df["timestamp_s"].iloc[0]

    # ── Save CSV ──────────────────────────────────────────────────────
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "realtime_aruco_evaluation.csv"
    df.to_csv(csv_path, index=False)
    print(f"CSV saved: {csv_path}  ({len(df)} rows)")

    # ── Print summary ─────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  POSITION ERROR SUMMARY (marker in camera frame)")
    print("=" * 60)
    for axis in ["x", "y", "z"]:
        col = f"err_{axis}"
        print(f"  Δ{axis.upper()}: mean={df[col].mean():.4f}m  std={df[col].std():.4f}m  "
              f"abs_mean={df[col].abs().mean():.4f}m  max={df[col].abs().max():.4f}m")
    print(f"  ‖Δpos‖: mean={df['err_pos'].mean():.4f}m  std={df['err_pos'].std():.4f}m  "
          f"max={df['err_pos'].max():.4f}m")

    print("\n" + "=" * 60)
    print("  ORIENTATION ERROR SUMMARY")
    print("=" * 60)
    for axis in ["roll", "pitch", "yaw"]:
        col = f"err_{axis}_deg"
        print(f"  Δ{axis}: mean={df[col].mean():.2f}°  std={df[col].std():.2f}°  "
              f"abs_mean={df[col].abs().mean():.2f}°  max={df[col].abs().max():.2f}°")

    # ── Plots ─────────────────────────────────────────────────────────
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(3, 2, figsize=(16, 14))
        fig.suptitle("Real-time ArUco Pose Evaluation", fontsize=14, fontweight="bold")

        t = df["t_rel"]

        # Position: estimated vs GT
        for i, axis in enumerate(["x", "y", "z"]):
            ax = axes[i, 0]
            ax.plot(t, df[f"est_{axis}"], "b-", alpha=0.7, linewidth=0.8, label="Estimated")
            ax.plot(t, df[f"gt_{axis}"], "r--", alpha=0.7, linewidth=0.8, label="Ground Truth")
            ax.set_ylabel(f"{axis.upper()} (m)")
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
            ax.set_title(f"Position {axis.upper()}: Estimated vs GT")

        # Position error
        for i, axis in enumerate(["x", "y", "z"]):
            ax = axes[i, 1]
            col = f"err_{axis}"
            ax.plot(t, df[col], "g-", alpha=0.7, linewidth=0.8)
            ax.axhline(y=0, color="k", linewidth=0.5)
            ax.axhline(y=df[col].mean(), color="r", linewidth=1, linestyle="--",
                       label=f"mean={df[col].mean():.3f}m")
            ax.set_ylabel(f"Δ{axis.upper()} (m)")
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
            ax.set_title(f"Position Error {axis.upper()}")

        axes[-1, 0].set_xlabel("Time (s)")
        axes[-1, 1].set_xlabel("Time (s)")
        plt.tight_layout()
        pos_path = output_dir / "position_est_vs_gt.png"
        plt.savefig(pos_path, dpi=150)
        plt.close()
        print(f"Plot saved: {pos_path}")

        # Orientation plots
        fig2, axes2 = plt.subplots(3, 2, figsize=(16, 14))
        fig2.suptitle("Orientation: Estimated vs GT", fontsize=14, fontweight="bold")

        for i, axis in enumerate(["roll", "pitch", "yaw"]):
            ax = axes2[i, 0]
            ax.plot(t, np.degrees(df[f"est_{axis}"]), "b-", alpha=0.7, linewidth=0.8, label="Estimated")
            ax.plot(t, np.degrees(df[f"gt_{axis}"]), "r--", alpha=0.7, linewidth=0.8, label="Ground Truth")
            ax.set_ylabel(f"{axis} (°)")
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
            ax.set_title(f"{axis.capitalize()}: Estimated vs GT")

            ax2 = axes2[i, 1]
            col = f"err_{axis}_deg"
            ax2.plot(t, df[col], "g-", alpha=0.7, linewidth=0.8)
            ax2.axhline(y=0, color="k", linewidth=0.5)
            ax2.axhline(y=df[col].mean(), color="r", linewidth=1, linestyle="--",
                        label=f"mean={df[col].mean():.1f}°")
            ax2.set_ylabel(f"Δ{axis} (°)")
            ax2.legend(fontsize=8)
            ax2.grid(True, alpha=0.3)
            ax2.set_title(f"{axis.capitalize()} Error")

        axes2[-1, 0].set_xlabel("Time (s)")
        axes2[-1, 1].set_xlabel("Time (s)")
        plt.tight_layout()
        ori_path = output_dir / "orientation_est_vs_gt.png"
        plt.savefig(ori_path, dpi=150)
        plt.close()
        print(f"Plot saved: {ori_path}")

        # Error distribution histograms
        fig3, axes3 = plt.subplots(2, 3, figsize=(16, 8))
        fig3.suptitle("Error Distributions", fontsize=14, fontweight="bold")

        for i, axis in enumerate(["x", "y", "z"]):
            ax = axes3[0, i]
            ax.hist(df[f"err_{axis}"], bins=50, alpha=0.7, edgecolor="black", linewidth=0.5)
            ax.axvline(x=0, color="k", linewidth=1)
            ax.axvline(x=df[f"err_{axis}"].mean(), color="r", linewidth=1.5, linestyle="--")
            ax.set_xlabel(f"Δ{axis.upper()} (m)")
            ax.set_title(f"Position error {axis.upper()}")

        for i, axis in enumerate(["roll", "pitch", "yaw"]):
            ax = axes3[1, i]
            ax.hist(df[f"err_{axis}_deg"], bins=50, alpha=0.7, edgecolor="black", linewidth=0.5)
            ax.axvline(x=0, color="k", linewidth=1)
            ax.axvline(x=df[f"err_{axis}_deg"].mean(), color="r", linewidth=1.5, linestyle="--")
            ax.set_xlabel(f"Δ{axis} (°)")
            ax.set_title(f"Orientation error {axis}")

        plt.tight_layout()
        hist_path = output_dir / "error_histograms.png"
        plt.savefig(hist_path, dpi=150)
        plt.close()
        print(f"Plot saved: {hist_path}")

    except ImportError:
        print("matplotlib not available – skipping plots.")

    print(f"\nDone. All results in: {output_dir}")


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate real-time ArUco pose vs GT from rosbag")
    parser.add_argument("rosbag", type=str, help="Path to the rosbag directory")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Output directory (default: aruco_relative_pose/outputs/<bag_name>_evaluation)")
    return parser.parse_args()


def main():
    args = parse_args()
    rosbag_path = Path(args.rosbag)
    if not rosbag_path.exists():
        print(f"ERROR: Rosbag not found: {rosbag_path}")
        sys.exit(1)

    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        bag_name = rosbag_path.name
        output_dir = Path("aruco_relative_pose/outputs") / f"{bag_name}_realtime_eval"

    evaluate(rosbag_path, output_dir)


if __name__ == "__main__":
    main()
