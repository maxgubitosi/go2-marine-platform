#!/usr/bin/env python3
"""
Offline evaluation: compare real-time ArUco pose estimates with ground truth.

Supports two camera sources:
  • fixed_camera  – static camera mounted at a known world position
                    (rosbags: marine_sim_*)
  • sjtu_drone    – bottom camera of the SJTU drone (moves with the drone)
                    (rosbags: sjtu_drone_sim_*)

The camera source is auto-detected from the rosbag name prefix, or can be
forced via --camera-source.

Reads a rosbag that contains:
  common:
    /aruco/pose                   (PoseStamped)  – ArUco estimate (cam frame)
    /odom                         (Odometry)     – Go2 x,y in world
    /imu/data                     (Imu)          – Go2 orientation
    /base_to_footprint_pose       (PoseWithCov)  – Go2 trunk z (heave)

  fixed_camera bags:
    /drone/pose                   (Pose)         – fixed-camera "drone" pose

  sjtu_drone bags:
    /drone/pose                   (PoseStamped)  – estimated drone pose
    /drone/gt_pose                (Pose)         – ground-truth drone pose

Computes the ground-truth marker pose in camera frame using:
  1. Go2 trunk pose in world  (from odom + imu + heave)
  2. Marker = trunk + offset [0, 0, 0.091]
  3. Camera optical frame in world (from camera source transforms)
  4. marker_in_cam = R_cam_world @ (marker_world - cam_world)

Usage:
    # Fixed camera (auto-detected from bag name):
    python3 evaluate_realtime_aruco.py rosbags/marine_sim_20260215_190303

    # SJTU drone (auto-detected from bag name):
    python3 evaluate_realtime_aruco.py rosbags/sjtu_drone_sim_20260216_180434

    # Force camera source:
    python3 evaluate_realtime_aruco.py rosbags/some_bag --camera-source sjtu_drone
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

# ── Fixed-camera extrinsics (camera_base_link → optical) ────────────
# From src/fixed_camera/urdf/fixed_camera.xacro
FIXED_BASE_TO_CAMLINK_XYZ = np.array([0.0, 0.0, -0.055], dtype=np.float64)
FIXED_BASE_TO_CAMLINK_RPY = np.array([0.0, np.pi / 2.0, 0.0], dtype=np.float64)
FIXED_CAMLINK_TO_OPT_XYZ  = np.array([0.0, 0.0, 0.0], dtype=np.float64)
FIXED_CAMLINK_TO_OPT_RPY  = np.array([-np.pi / 2.0, 0.0, -np.pi / 2.0], dtype=np.float64)

# ── SJTU drone extrinsics (base_link → bottom_cam_link → optical) ───
# From src/sjtu_drone/sjtu_drone_description/urdf/sjtu_drone.urdf.xacro
SJTU_BASE_TO_CAMLINK_XYZ = np.array([0.0, 0.0, 0.0], dtype=np.float64)
SJTU_BASE_TO_CAMLINK_RPY = np.array([0.0, np.pi / 2.0, 0.0], dtype=np.float64)
SJTU_CAMLINK_TO_OPT_XYZ  = np.array([0.0, 0.0, 0.0], dtype=np.float64)
SJTU_CAMLINK_TO_OPT_RPY  = np.array([-np.pi / 2.0, 0.0, -np.pi / 2.0], dtype=np.float64)

# ── Go2 spawn offset ────────────────────────────────────────────────
# La odometría de pata de CHAMP siempre arranca en (0,0) sin importar
# dónde se spawneó el Go2 en Gazebo.  En nuestra simulación el Go2 se
# spawnea en world_init_x = 0.40 m (ver bringup launch), así que ese
# es el default.  Sobreescribir con --world-init-x si fuera distinto.
WORLD_INIT_X: float = 0.40
WORLD_INIT_Y: float = 0.0

# ── Fixed-camera mode ───────────────────────────────────────────────
# Position is: spawn_z(=2.0) + camera_joint_z(-0.045) = 1.955 m
USE_FIXED_CAMERA: bool = False
FIXED_CAM_POS: np.ndarray = np.array([0.0, 0.0, 1.955], dtype=np.float64)

# ── Camera source ───────────────────────────────────────────────────
CAMERA_SOURCES = ("fixed_camera", "sjtu_drone")


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

def compute_base_to_optical(
    base_to_camlink_xyz: np.ndarray,
    base_to_camlink_rpy: np.ndarray,
    camlink_to_opt_xyz: np.ndarray,
    camlink_to_opt_rpy: np.ndarray,
):
    """Return (R_base_opt, t_base_opt) from URDF extrinsics."""
    R_bl_cl = rpy_to_rotation_matrix(*base_to_camlink_rpy)
    R_cl_opt = rpy_to_rotation_matrix(*camlink_to_opt_rpy)
    R_base_opt = R_bl_cl @ R_cl_opt
    t_base_opt = base_to_camlink_xyz + R_bl_cl @ camlink_to_opt_xyz
    return R_base_opt, t_base_opt


def detect_camera_source(rosbag_name: str) -> str:
    """Auto-detect camera source from rosbag directory name.

    Returns 'fixed_camera' for marine_sim_* bags and
    'sjtu_drone' for sjtu_drone_sim_* bags.
    """
    name = rosbag_name.lower()
    if name.startswith("sjtu_drone"):
        return "sjtu_drone"
    if name.startswith("marine_sim"):
        return "fixed_camera"
    # Fallback: look at keywords
    if "sjtu" in name or "drone_sim" in name:
        return "sjtu_drone"
    return "fixed_camera"


def get_extrinsics_for_source(source: str):
    """Return (base_to_cam_xyz, base_to_cam_rpy, cam_to_opt_xyz, cam_to_opt_rpy)."""
    if source == "sjtu_drone":
        return (SJTU_BASE_TO_CAMLINK_XYZ, SJTU_BASE_TO_CAMLINK_RPY,
                SJTU_CAMLINK_TO_OPT_XYZ, SJTU_CAMLINK_TO_OPT_RPY)
    else:  # fixed_camera
        return (FIXED_BASE_TO_CAMLINK_XYZ, FIXED_BASE_TO_CAMLINK_RPY,
                FIXED_CAMLINK_TO_OPT_XYZ, FIXED_CAMLINK_TO_OPT_RPY)


# ══════════════════════════════════════════════════════════════════════
#  Main evaluation
# ══════════════════════════════════════════════════════════════════════

def evaluate(
    rosbag_path: Path,
    output_dir: Path,
    world_init_x: float = 0.0,
    world_init_y: float = 0.0,
    camera_source: str = "fixed_camera",
    fixed_cam_pos: Optional[np.ndarray] = None,
):
    print(f"Reading rosbag: {rosbag_path}")
    print(f"  Camera source: {camera_source.upper()}")
    if world_init_x != 0.0 or world_init_y != 0.0:
        print(f"  Go2 spawn offset: world_init_x={world_init_x:.3f} m, world_init_y={world_init_y:.3f} m")

    is_fixed = (camera_source == "fixed_camera")
    is_sjtu  = (camera_source == "sjtu_drone")

    if is_fixed:
        _cam_pos = fixed_cam_pos if fixed_cam_pos is not None else FIXED_CAM_POS
        print(f"  Camera mode: FIXED at world {_cam_pos.tolist()}")
    else:
        print(f"  Camera mode: SJTU DRONE (from /drone/pose PoseStamped)")

    # 1) Read all topics
    aruco_msgs = extract_messages(rosbag_path, "/aruco/pose", PoseStamped)
    odom_msgs = extract_messages(rosbag_path, "/odom", Odometry)
    imu_msgs = extract_messages(rosbag_path, "/imu/data", Imu)
    heave_msgs = extract_messages(rosbag_path, "/base_to_footprint_pose", PoseWithCovarianceStamped)

    # /drone/pose type differs between bags:
    #   fixed_camera → geometry_msgs/Pose
    #   sjtu_drone   → geometry_msgs/PoseStamped
    if is_sjtu:
        drone_msgs = extract_messages(rosbag_path, "/drone/pose", PoseStamped)
        drone_gt_msgs = extract_messages(rosbag_path, "/drone/gt_pose", Pose)
    else:
        drone_msgs = extract_messages(rosbag_path, "/drone/pose", Pose)
        drone_gt_msgs = []

    print(f"  /aruco/pose:              {len(aruco_msgs)} messages")
    print(f"  /odom:                    {len(odom_msgs)} messages")
    print(f"  /imu/data:                {len(imu_msgs)} messages")
    print(f"  /base_to_footprint_pose:  {len(heave_msgs)} messages")
    print(f"  /drone/pose:              {len(drone_msgs)} messages"
          f" ({'PoseStamped' if is_sjtu else 'Pose'})")
    if drone_gt_msgs:
        print(f"  /drone/gt_pose:           {len(drone_gt_msgs)} messages")

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

    # For SJTU drone, /drone/pose is PoseStamped → extract .pose (Pose)
    # For fixed camera, /drone/pose is already Pose
    if is_sjtu:
        drone_dict = {ts: msg.pose for ts, msg in drone_msgs}  # PoseStamped → .pose
    else:
        drone_dict = {ts: msg for ts, msg in drone_msgs}       # already Pose
    drone_ts = sorted(drone_dict.keys())

    # SJTU drone also has /drone/gt_pose (Pose) for GT drone position
    drone_gt_dict = {ts: msg for ts, msg in drone_gt_msgs} if drone_gt_msgs else {}
    drone_gt_ts = sorted(drone_gt_dict.keys())

    # 3) Pre-compute static transforms using source-specific extrinsics
    extrinsics = get_extrinsics_for_source(camera_source)
    R_base_opt, t_base_opt = compute_base_to_optical(*extrinsics)

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
        # NOTE: CHAMP leg odometry starts at (0,0) regardless of the Gazebo
        # spawn position (world_init_x / world_init_y).  Add the spawn offset
        # so the trunk position is expressed in the true world frame.
        trunk_x = world_init_x + odom_msg.pose.pose.position.x
        trunk_y = world_init_y + odom_msg.pose.pose.position.y

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
        if is_fixed:
            # Images come from the fixed_camera node (static, not on the drone).
            _cam_pos = fixed_cam_pos if fixed_cam_pos is not None else FIXED_CAM_POS
            R_w_opt = R_base_opt.copy()
            t_w_opt = _cam_pos.copy()
            drone_pos = _cam_pos.copy()
        elif is_sjtu:
            # SJTU drone: prefer /drone/gt_pose for GT accuracy, fallback to
            # /drone/pose (PoseStamped.pose, already extracted above).
            _use_gt = bool(drone_gt_ts)
            if _use_gt:
                dgt_idx = find_closest(drone_gt_ts, aruco_ts, threshold_ns)
                if dgt_idx is not None:
                    dm = drone_gt_dict[drone_gt_ts[dgt_idx]]
                else:
                    _use_gt = False

            if not _use_gt:
                # Fallback to /drone/pose (PoseStamped.pose)
                if drone_ts:
                    dp_idx = find_closest(drone_ts, aruco_ts, threshold_ns)
                    if dp_idx is not None:
                        dm = drone_dict[drone_ts[dp_idx]]
                    else:
                        skipped += 1
                        continue
                else:
                    skipped += 1
                    continue

            drone_pos = np.array([dm.position.x, dm.position.y, dm.position.z], dtype=np.float64)
            dq = dm.orientation
            R_w_drone = quaternion_to_rotation_matrix(dq.x, dq.y, dq.z, dq.w)

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
            "camera_source": camera_source,
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
    print(f"  POSITION ERROR SUMMARY – {camera_source} (marker in camera frame)")
    print("=" * 60)
    for axis in ["x", "y", "z"]:
        col = f"err_{axis}"
        print(f"  Δ{axis.upper()}: mean={df[col].mean():.4f}m  std={df[col].std():.4f}m  "
              f"abs_mean={df[col].abs().mean():.4f}m  max={df[col].abs().max():.4f}m")
    print(f"  ‖Δpos‖: mean={df['err_pos'].mean():.4f}m  std={df['err_pos'].std():.4f}m  "
          f"max={df['err_pos'].max():.4f}m")

    print("\n" + "=" * 60)
    print(f"  ORIENTATION ERROR SUMMARY – {camera_source}")
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
        source_label = camera_source.replace('_', ' ').title()
        fig.suptitle(f"Real-time ArUco Pose Evaluation ({source_label})", fontsize=14, fontweight="bold")

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
        fig2.suptitle(f"Orientation: Estimated vs GT ({source_label})", fontsize=14, fontweight="bold")

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
        fig3.suptitle(f"Error Distributions ({source_label})", fontsize=14, fontweight="bold")

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
    parser = argparse.ArgumentParser(
        description="Evaluate real-time ArUco pose vs GT from rosbag",
        epilog=(
            "Camera source is auto-detected from the bag name:\n"
            "  marine_sim_*       → fixed_camera\n"
            "  sjtu_drone_sim_*   → sjtu_drone\n"
            "Override with --camera-source if needed."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("rosbag", type=str, help="Path to the rosbag directory")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Output directory (default: aruco_relative_pose/outputs/<bag_name>_realtime_eval)")
    parser.add_argument(
        "--camera-source", type=str, default="auto",
        choices=["auto", "fixed_camera", "sjtu_drone"],
        help=(
            "Camera source: fixed_camera (static 640×480), sjtu_drone "
            "(moving 640×360 bottom cam), or auto (detect from bag name). "
            "Default: auto"
        ),
    )
    parser.add_argument(
        "--world-init-x", type=float, default=WORLD_INIT_X,
        help=(
            "Go2 spawn X offset in Gazebo world frame (metres). "
            "CHAMP leg odometry starts at 0 regardless of the spawn position. "
            "(default: %(default)s)"
        ),
    )
    parser.add_argument(
        "--world-init-y", type=float, default=WORLD_INIT_Y,
        help="Go2 spawn Y offset (metres). (default: %(default)s)",
    )
    # Legacy flag kept for backwards compatibility
    parser.add_argument(
        "--fixed-camera", action="store_true", default=False,
        help="(Deprecated) Use --camera-source fixed_camera instead.",
    )
    parser.add_argument(
        "--cam-pos", type=float, nargs=3, default=None,
        metavar=("X", "Y", "Z"),
        help=(
            "Fixed camera optical-frame world position [x y z] in metres. "
            "Only used with fixed_camera source. "
            f"Default: {FIXED_CAM_POS.tolist()}"
        ),
    )
    return parser.parse_args()


def main():
    args = parse_args()
    rosbag_path = Path(args.rosbag)
    if not rosbag_path.exists():
        print(f"ERROR: Rosbag not found: {rosbag_path}")
        sys.exit(1)

    # Determine camera source
    if args.camera_source != "auto":
        camera_source = args.camera_source
    elif args.fixed_camera:
        # Legacy --fixed-camera flag
        camera_source = "fixed_camera"
    else:
        camera_source = detect_camera_source(rosbag_path.name)
        print(f"Auto-detected camera source: {camera_source} (from bag name '{rosbag_path.name}')")

    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        bag_name = rosbag_path.name
        output_dir = Path("aruco_relative_pose/outputs") / f"{bag_name}_realtime_eval"

    fixed_cam_pos = np.array(args.cam_pos, dtype=np.float64) if args.cam_pos else None

    evaluate(
        rosbag_path,
        output_dir,
        world_init_x=args.world_init_x,
        world_init_y=args.world_init_y,
        camera_source=camera_source,
        fixed_cam_pos=fixed_cam_pos,
    )


if __name__ == "__main__":
    main()
