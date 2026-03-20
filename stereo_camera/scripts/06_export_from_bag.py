#!/usr/bin/env python3
"""
06_export_from_bag.py — Export video + CSV from a recorded rosbag.

Reads a ROS2 bag (SQLite3 .db3) and extracts:
  1. Video MP4 from /aruco/debug_image (with detection overlay)
  2. CSV with ArUco pose from /aruco/pose  (timestamp, x, y, z, roll, pitch, yaw, detected)
  3. CSV with marine commands from /marine_platform/debug_state (timestamp, roll_cmd, pitch_cmd, heave_cmd)
  4. Merged CSV with closest-match correlation between aruco poses and marine commands

Usage:
    python3 scripts/06_export_from_bag.py /path/to/rosbag_dir
    python3 scripts/06_export_from_bag.py /path/to/rosbag_dir --no-video
"""
from __future__ import annotations

import argparse
import csv
import math
import sqlite3
import struct
import sys
from pathlib import Path

import cv2
import numpy as np
import yaml


def read_bag_metadata(bag_dir: Path) -> dict:
    """Read metadata.yaml from a rosbag directory."""
    meta_path = bag_dir / "metadata.yaml"
    if not meta_path.exists():
        print(f"ERROR: No metadata.yaml in {bag_dir}")
        sys.exit(1)
    with open(meta_path, "r") as f:
        return yaml.safe_load(f)


def find_db3(bag_dir: Path) -> Path:
    """Find the .db3 file in a rosbag directory."""
    db3_files = list(bag_dir.glob("*.db3"))
    if not db3_files:
        print(f"ERROR: No .db3 file in {bag_dir}")
        sys.exit(1)
    return db3_files[0]


def get_topic_id_map(conn: sqlite3.Connection) -> dict[str, int]:
    """Get mapping of topic name → topic id from the bag."""
    cursor = conn.execute("SELECT id, name FROM topics")
    return {name: tid for tid, name in cursor.fetchall()}


def iter_messages(conn: sqlite3.Connection, topic_id: int):
    """Iterate over messages for a given topic id, ordered by timestamp."""
    cursor = conn.execute(
        "SELECT timestamp, data FROM messages WHERE topic_id = ? ORDER BY timestamp",
        (topic_id,),
    )
    for ts, data in cursor:
        yield ts, data


# ═══ CDR deserialization helpers (minimal, for known message types) ═══

def deserialize_image(data: bytes) -> tuple[int, int, str, bytes] | None:
    """Deserialize sensor_msgs/Image from CDR. Returns (width, height, encoding, pixels)."""
    try:
        # CDR header (4 bytes) + stamp (8+4) + frame_id (4+N) ...
        offset = 4  # skip CDR encapsulation header

        # header.stamp.sec (int32) + header.stamp.nanosec (uint32)
        sec = struct.unpack_from("<i", data, offset)[0]
        offset += 4
        nsec = struct.unpack_from("<I", data, offset)[0]
        offset += 4

        # header.frame_id (string: uint32 length + chars + null + padding)
        frame_len = struct.unpack_from("<I", data, offset)[0]
        offset += 4 + frame_len
        # Align to 4 bytes
        offset = (offset + 3) & ~3

        # height, width (uint32 each)
        height = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        width = struct.unpack_from("<I", data, offset)[0]
        offset += 4

        # encoding (string)
        enc_len = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        encoding = data[offset : offset + enc_len - 1].decode("utf-8")
        offset += enc_len
        offset = (offset + 3) & ~3

        # is_bigendian (uint8) + padding
        offset += 1
        offset = (offset + 3) & ~3

        # step (uint32)
        step = struct.unpack_from("<I", data, offset)[0]
        offset += 4

        # data (sequence<uint8>: uint32 length + bytes)
        data_len = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        pixels = data[offset : offset + data_len]

        return width, height, encoding, pixels
    except Exception:
        return None


def deserialize_pose_stamped(data: bytes) -> tuple[float, ...] | None:
    """Deserialize geometry_msgs/PoseStamped. Returns (sec, nsec, x,y,z, qx,qy,qz,qw)."""
    try:
        offset = 4  # CDR header

        sec = struct.unpack_from("<i", data, offset)[0]
        offset += 4
        nsec = struct.unpack_from("<I", data, offset)[0]
        offset += 4

        # frame_id string
        frame_len = struct.unpack_from("<I", data, offset)[0]
        offset += 4 + frame_len
        offset = (offset + 7) & ~7  # align to 8 for float64

        # pose.position (3 x float64)
        x, y, z = struct.unpack_from("<3d", data, offset)
        offset += 24

        # pose.orientation (4 x float64)
        qx, qy, qz, qw = struct.unpack_from("<4d", data, offset)

        return (sec, nsec, x, y, z, qx, qy, qz, qw)
    except Exception:
        return None


def deserialize_vector3(data: bytes) -> tuple[float, float, float] | None:
    """Deserialize geometry_msgs/Vector3. Returns (x, y, z)."""
    try:
        offset = 4  # CDR header
        x, y, z = struct.unpack_from("<3d", data, offset)
        return (x, y, z)
    except Exception:
        return None


def deserialize_bool(data: bytes) -> bool | None:
    """Deserialize std_msgs/Bool."""
    try:
        offset = 4
        return struct.unpack_from("<?", data, offset)[0]
    except Exception:
        return None


def quaternion_to_euler(qx, qy, qz, qw):
    """Convert quaternion to roll, pitch, yaw in degrees."""
    # Roll (x-axis rotation)
    sinr_cosp = 2.0 * (qw * qx + qy * qz)
    cosr_cosp = 1.0 - 2.0 * (qx * qx + qy * qy)
    roll = math.atan2(sinr_cosp, cosr_cosp)

    # Pitch (y-axis rotation)
    sinp = 2.0 * (qw * qy - qz * qx)
    if abs(sinp) >= 1:
        pitch = math.copysign(math.pi / 2, sinp)
    else:
        pitch = math.asin(sinp)

    # Yaw (z-axis rotation)
    siny_cosp = 2.0 * (qw * qz + qx * qy)
    cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
    yaw = math.atan2(siny_cosp, cosy_cosp)

    return math.degrees(roll), math.degrees(pitch), math.degrees(yaw)


def find_closest_index(timestamps: list[int], target: int, threshold_ns: int = 200_000_000) -> int | None:
    """Binary search for closest timestamp within threshold."""
    import bisect
    idx = bisect.bisect_left(timestamps, target)
    best = None
    best_diff = threshold_ns + 1
    for i in [idx - 1, idx]:
        if 0 <= i < len(timestamps):
            diff = abs(timestamps[i] - target)
            if diff < best_diff:
                best_diff = diff
                best = i
    return best if best_diff <= threshold_ns else None


def main():
    parser = argparse.ArgumentParser(description="Export video + CSV from rosbag")
    parser.add_argument("bag_dir", type=str, help="Path to rosbag directory")
    parser.add_argument("--no-video", action="store_true", help="Skip video export")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory")
    args = parser.parse_args()

    bag_dir = Path(args.bag_dir)
    if not bag_dir.is_dir():
        print(f"ERROR: {bag_dir} is not a directory")
        sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else bag_dir / "exports"
    output_dir.mkdir(parents=True, exist_ok=True)

    db3_path = find_db3(bag_dir)
    conn = sqlite3.connect(str(db3_path))
    topic_map = get_topic_id_map(conn)

    print(f"═══ Export from rosbag ═══")
    print(f"  Bag: {bag_dir.name}")
    print(f"  DB3: {db3_path.name}")
    print(f"  Output: {output_dir}")
    print(f"  Topics found: {list(topic_map.keys())}")

    # ── 1. Export ArUco poses to CSV ─────────────────────────────
    aruco_csv = output_dir / "aruco_poses.csv"
    pose_topic_id = topic_map.get("/aruco/pose")
    det_topic_id = topic_map.get("/aruco/detection")

    # Build detection map: timestamp → bool
    detection_map = {}
    if det_topic_id:
        for ts, data in iter_messages(conn, det_topic_id):
            val = deserialize_bool(data)
            if val is not None:
                detection_map[ts] = val

    det_timestamps = sorted(detection_map.keys())

    pose_count = 0
    if pose_topic_id:
        with open(aruco_csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp_ns", "sec", "nsec",
                "x_m", "y_m", "z_m",
                "qx", "qy", "qz", "qw",
                "roll_deg", "pitch_deg", "yaw_deg",
                "distance_m",
            ])
            for ts, data in iter_messages(conn, pose_topic_id):
                result = deserialize_pose_stamped(data)
                if result is None:
                    continue
                sec, nsec, x, y, z, qx, qy, qz, qw = result
                roll, pitch, yaw = quaternion_to_euler(qx, qy, qz, qw)
                dist = math.sqrt(x * x + y * y + z * z)
                writer.writerow([
                    ts, sec, nsec,
                    f"{x:.6f}", f"{y:.6f}", f"{z:.6f}",
                    f"{qx:.6f}", f"{qy:.6f}", f"{qz:.6f}", f"{qw:.6f}",
                    f"{roll:.3f}", f"{pitch:.3f}", f"{yaw:.3f}",
                    f"{dist:.4f}",
                ])
                pose_count += 1
        print(f"  ✓ ArUco poses: {pose_count} rows → {aruco_csv.name}")
    else:
        print(f"  ✗ /aruco/pose not found in bag")

    # ── 2. Export marine commands to CSV ──────────────────────────
    marine_csv = output_dir / "marine_commands.csv"
    marine_topic_id = topic_map.get("/marine_platform/debug_state")

    marine_count = 0
    marine_timestamps = []
    if marine_topic_id:
        with open(marine_csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp_ns", "roll_cmd_deg", "pitch_cmd_deg", "heave_cmd_m",
            ])
            for ts, data in iter_messages(conn, marine_topic_id):
                result = deserialize_vector3(data)
                if result is None:
                    continue
                roll_cmd, pitch_cmd, heave_cmd = result
                writer.writerow([
                    ts, f"{roll_cmd:.4f}", f"{pitch_cmd:.4f}", f"{heave_cmd:.6f}",
                ])
                marine_timestamps.append(ts)
                marine_count += 1
        print(f"  ✓ Marine commands: {marine_count} rows → {marine_csv.name}")
    else:
        print(f"  ✗ /marine_platform/debug_state not found in bag")

    # ── 3. Export merged CSV (aruco + marine by closest timestamp) ──
    if pose_count > 0 and marine_count > 0:
        merged_csv = output_dir / "merged_aruco_marine.csv"
        # Re-read aruco CSV and marine data for merging
        aruco_rows = []
        with open(aruco_csv, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                aruco_rows.append(row)

        marine_rows = []
        with open(marine_csv, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                marine_rows.append(row)

        m_timestamps = [int(r["timestamp_ns"]) for r in marine_rows]

        with open(merged_csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp_ns",
                "aruco_x_m", "aruco_y_m", "aruco_z_m",
                "aruco_roll_deg", "aruco_pitch_deg", "aruco_yaw_deg",
                "aruco_distance_m",
                "cmd_roll_deg", "cmd_pitch_deg", "cmd_heave_m",
                "time_diff_ms",
            ])
            merged = 0
            for arow in aruco_rows:
                a_ts = int(arow["timestamp_ns"])
                idx = find_closest_index(m_timestamps, a_ts)
                if idx is not None:
                    mrow = marine_rows[idx]
                    diff_ms = abs(a_ts - m_timestamps[idx]) / 1e6
                    writer.writerow([
                        a_ts,
                        arow["x_m"], arow["y_m"], arow["z_m"],
                        arow["roll_deg"], arow["pitch_deg"], arow["yaw_deg"],
                        arow["distance_m"],
                        mrow["roll_cmd_deg"], mrow["pitch_cmd_deg"], mrow["heave_cmd_m"],
                        f"{diff_ms:.1f}",
                    ])
                    merged += 1
        print(f"  ✓ Merged CSV: {merged} rows → {merged_csv.name}")

    # ── 4. Export video from debug images ────────────────────────
    if not args.no_video:
        debug_topic_id = topic_map.get("/aruco/debug_image")
        if debug_topic_id:
            video_path = output_dir / "aruco_detection.mp4"
            video_writer = None
            frame_count = 0

            print(f"  Exporting video...")
            for ts, data in iter_messages(conn, debug_topic_id):
                result = deserialize_image(data)
                if result is None:
                    continue

                width, height, encoding, pixels = result
                try:
                    img = np.frombuffer(pixels, dtype=np.uint8).reshape(height, width, -1)
                    if encoding == "rgb8":
                        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                    elif encoding == "mono8":
                        img = cv2.cvtColor(
                            img.reshape(height, width), cv2.COLOR_GRAY2BGR
                        )
                except Exception:
                    continue

                if video_writer is None:
                    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                    video_writer = cv2.VideoWriter(
                        str(video_path), fourcc, 30.0, (width, height)
                    )

                video_writer.write(img)
                frame_count += 1

            if video_writer is not None:
                video_writer.release()
                print(f"  ✓ Video: {frame_count} frames → {video_path.name}")
            else:
                print(f"  ✗ No debug images could be decoded")
        else:
            print(f"  ✗ /aruco/debug_image not found in bag")

    conn.close()

    print(f"\n═══ Export complete ═══")
    print(f"  Output: {output_dir}")


if __name__ == "__main__":
    main()
