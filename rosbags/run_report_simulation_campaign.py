#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import os
import shlex
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required to run the simulation campaign.") from exc


REPO_ROOT = Path(__file__).resolve().parents[1]
ROSBAGS_DIR = REPO_ROOT / "rosbags"
LOGS_DIR = ROSBAGS_DIR / "logs"
INSTALL_SETUP = REPO_ROOT / "install" / "setup.bash"
DEFAULT_CONFIG = ROSBAGS_DIR / "report_sim_campaign.yaml"
WAIT_FOR_TOPIC = ROSBAGS_DIR / "wait_for_topic.py"
WAIT_FOR_DRONE_READY = ROSBAGS_DIR / "wait_for_drone_ready.py"
ROS_LOG_DIR = Path("/tmp") / "gazebo_no_seas_malo_ros_logs"

COMMON_TOPICS = [
    "/tf",
    "/tf_static",
    "/clock",
    "/joint_states",
    "/odom",
    "/cmd_vel",
    "/imu/data",
    "/body_pose",
    "/marine_platform/debug_state",
    "/base_to_footprint_pose",
    "/parameter_events",
    "/aruco/pose",
    "/aruco/detection",
    "/aruco/debug_image",
]

FIXED_TOPICS = COMMON_TOPICS + [
    "/fixed_camera/camera/image_raw",
    "/fixed_camera/camera/camera_info",
    "/fixed_camera/pose",
]

DRONE_TOPICS = COMMON_TOPICS + [
    "/drone/bottom/image_raw",
    "/drone/bottom/camera_info",
    "/drone/gt_pose",
    "/drone/gt_vel",
    "/drone/state",
    "/drone/cmd_mode",
    "/drone/pose",
    "/drone/odom",
    "/drone/cmd_vel",
    "/drone/posctrl",
    "/drone/takeoff",
    "/drone/land",
    "/drone/imu",
    "/drone/sonar",
]


@dataclass
class ManagedProcess:
    name: str
    popen: subprocess.Popen[str]
    log_path: Path
    command: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a comparable simulation campaign for the report.")
    parser.add_argument("--scenario", choices=["fixed", "drone"], required=True)
    parser.add_argument("--role", required=True, help="Bag role, for example ref, r1, r2, r3 or smoke")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--out-dir", type=Path, default=ROSBAGS_DIR)
    parser.add_argument("--allow-dirty", action="store_true", help="Allow running even if git has uncommitted changes")
    parser.add_argument("--duration-sec", type=float, default=None, help="Override measurement duration from the profile")
    parser.add_argument("--warmup-sec", type=float, default=None, help="Override fixed-camera warmup from the profile")
    return parser.parse_args()


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def shell_quote(path: Path | str) -> str:
    return shlex.quote(str(path))


def ros_shell_command(command: str) -> list[str]:
    return [
        "/bin/bash",
        "-lc",
        (
            f"export ROS_LOG_DIR={shell_quote(ROS_LOG_DIR)} && "
            f"source /opt/ros/humble/setup.bash && "
            f"source {shell_quote(INSTALL_SETUP)} && "
            f"{command}"
        ),
    ]


def run_checked(command: str, timeout: float | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ros_shell_command(command),
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def ensure_environment() -> None:
    if not INSTALL_SETUP.exists():
        raise SystemExit(f"Workspace setup file not found: {INSTALL_SETUP}")
    if not WAIT_FOR_TOPIC.exists():
        raise SystemExit(f"Missing helper script: {WAIT_FOR_TOPIC}")
    if not WAIT_FOR_DRONE_READY.exists():
        raise SystemExit(f"Missing helper script: {WAIT_FOR_DRONE_READY}")
    ROS_LOG_DIR.mkdir(parents=True, exist_ok=True)


def git_info() -> tuple[str, bool]:
    commit = (
        subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        ).stdout.strip()
        or "unknown"
    )
    dirty = bool(
        subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        ).stdout.strip()
    )
    return commit, dirty


def launch_managed(name: str, command: str, log_path: Path) -> ManagedProcess:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_handle = log_path.open("w", encoding="utf-8")
    popen = subprocess.Popen(
        ros_shell_command(command),
        cwd=REPO_ROOT,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
        preexec_fn=os.setsid,
    )
    return ManagedProcess(name=name, popen=popen, log_path=log_path, command=command)


def terminate_process(proc: ManagedProcess, timeout: float = 10.0) -> None:
    if proc.popen.poll() is not None:
        return
    try:
        os.killpg(proc.popen.pid, signal.SIGINT)
        proc.popen.wait(timeout=timeout)
    except Exception:
        try:
            os.killpg(proc.popen.pid, signal.SIGTERM)
            proc.popen.wait(timeout=5.0)
        except Exception:
            try:
                os.killpg(proc.popen.pid, signal.SIGKILL)
            except Exception:
                pass


def wait_for_topic(topic: str, type_name: str, timeout: float) -> None:
    command = f"{shell_quote(sys.executable)} {shell_quote(WAIT_FOR_TOPIC)} {shell_quote(topic)} {shell_quote(type_name)} --timeout {timeout}"
    result = run_checked(command, timeout=timeout + 10.0)
    if result.returncode != 0:
        raise RuntimeError(f"Timed out waiting for {topic} ({type_name}). stderr={result.stderr.strip()}")


def wait_for_drone_ready(profile: dict[str, Any]) -> None:
    drone_cfg = profile["sjtu_drone"]
    command = (
        f"{shell_quote(sys.executable)} {shell_quote(WAIT_FOR_DRONE_READY)} "
        f"--target-x {drone_cfg['target_x']} "
        f"--target-y {drone_cfg['target_y']} "
        f"--target-z {drone_cfg['target_z']} "
        f"--horizontal-tol {drone_cfg['readiness_horizontal_tol_m']} "
        f"--vertical-tol {drone_cfg['readiness_vertical_tol_m']} "
        f"--stable-for {drone_cfg['readiness_hold_sec']} "
        f"--timeout {drone_cfg['readiness_timeout_sec']} "
        f"--detection-freshness {drone_cfg['detection_freshness_sec']}"
    )
    result = run_checked(command, timeout=float(drone_cfg["readiness_timeout_sec"]) + 15.0)
    if result.returncode != 0:
        raise RuntimeError(f"Drone did not reach readiness. stderr={result.stderr.strip()}")


def parse_bag_topic_counts(metadata_path: Path) -> dict[str, int]:
    data = load_yaml(metadata_path)
    topics = data["rosbag2_bagfile_information"]["topics_with_message_count"]
    counts: dict[str, int] = {}
    for entry in topics:
        meta = entry["topic_metadata"]
        counts[meta["name"]] = int(entry["message_count"])
    return counts


def build_bag_name(scenario: str, role: str) -> str:
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = "marine_sim" if scenario == "fixed" else "sjtu_drone_sim"
    return f"{prefix}_{timestamp}_report_v2_{role}"


def required_topics_for_scenario(scenario: str) -> list[str]:
    if scenario == "fixed":
        return [
            "/fixed_camera/camera/image_raw",
            "/fixed_camera/camera/camera_info",
            "/fixed_camera/pose",
            "/aruco/pose",
            "/body_pose",
        ]
    return [
        "/drone/bottom/image_raw",
        "/drone/gt_pose",
        "/drone/state",
        "/drone/cmd_mode",
        "/aruco/pose",
        "/body_pose",
    ]


def scenario_source(scenario: str) -> str:
    return "fixed_camera" if scenario == "fixed" else "sjtu_drone"


def write_manifest(
    bag_dir: Path,
    bag_name: str,
    args: argparse.Namespace,
    profile: dict[str, Any],
    commit: str,
    dirty: bool,
    commands: dict[str, str],
    topic_counts: dict[str, int],
    log_paths: dict[str, str],
) -> None:
    common = profile["common"]
    marine = profile["marine_motion"]
    scenario_cfg = profile["fixed_camera"] if args.scenario == "fixed" else profile["sjtu_drone"]
    required = required_topics_for_scenario(args.scenario)
    missing = [topic for topic in required if topic not in topic_counts]

    manifest = {
        "profile_name": profile["profile_name"],
        "bag_name": bag_name,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "scenario": scenario_source(args.scenario),
        "role": args.role,
        "git": {
            "commit": commit,
            "dirty": dirty,
        },
        "experiment": {
            "world_init_x": float(common["world_init_x"]),
            "world_init_y": float(common["world_init_y"]),
            "measurement_duration_sec": float(args.duration_sec or common["measurement_duration_sec"]),
            "min_marine_warmup_sec": float(args.warmup_sec or common["min_marine_warmup_sec"]),
            "marine_motion": marine,
            "scenario_config": scenario_cfg,
            "acceptance": profile["acceptance"][scenario_source(args.scenario)],
        },
        "recording": {
            "topics": FIXED_TOPICS if args.scenario == "fixed" else DRONE_TOPICS,
            "commands": commands,
            "logs": log_paths,
        },
        "bag_validation": {
            "required_topics": required,
            "missing_topics": missing,
            "topic_message_counts": topic_counts,
        },
    }
    (bag_dir / "experiment_manifest.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    ensure_environment()
    profile = load_yaml(args.config)
    commit, dirty = git_info()
    if dirty and not args.allow_dirty:
        raise SystemExit("Git worktree is dirty. Commit or rerun with --allow-dirty.")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    bag_name = build_bag_name(args.scenario, args.role)
    bag_dir = args.out_dir / bag_name
    measurement_duration = float(args.duration_sec or profile["common"]["measurement_duration_sec"])
    warmup_duration = float(args.warmup_sec or profile["common"]["min_marine_warmup_sec"])

    processes: list[ManagedProcess] = []
    commands: dict[str, str] = {}

    common = profile["common"]
    marine = profile["marine_motion"]
    try:
        gazebo_cmd = (
            "ros2 launch go2_config gazebo.launch.py "
            f"rviz:=false gui:=False world_init_x:={common['world_init_x']} world_init_y:={common['world_init_y']}"
        )
        commands["gazebo"] = gazebo_cmd
        processes.append(launch_managed("gazebo", gazebo_cmd, LOGS_DIR / f"{bag_name}_gazebo.log"))
        wait_for_topic("/clock", "rosgraph_msgs/msg/Clock", timeout=90.0)

        marine_cmd = (
            "ros2 run go2_tools marine_platform_simulator --ros-args "
            f"-p rate_hz:={marine['rate_hz']} "
            f"-p wave_pattern:={marine['wave_pattern']} "
            f"-p wave_frequency:={marine['wave_frequency']} "
            f"-p max_roll_deg:={marine['max_roll_deg']} "
            f"-p max_pitch_deg:={marine['max_pitch_deg']} "
            f"-p max_heave_m:={marine['max_heave_m']} "
            f"-p phase_offset_pitch:={marine['phase_offset_pitch']} "
            f"-p phase_offset_heave:={marine['phase_offset_heave']} "
            f"-p smoothing_factor:={marine['smoothing_factor']}"
        )
        commands["marine_platform_simulator"] = marine_cmd
        processes.append(
            launch_managed("marine_platform_simulator", marine_cmd, LOGS_DIR / f"{bag_name}_marine.log")
        )
        wait_for_topic("/body_pose", "geometry_msgs/msg/Pose", timeout=30.0)

        if args.scenario == "fixed":
            fixed_cfg = profile["fixed_camera"]
            scenario_cmd = (
                "ros2 launch fixed_camera fixed_camera.launch.py "
                f"height:={fixed_cfg['height_m']}"
            )
            commands["scenario"] = scenario_cmd
            processes.append(launch_managed("fixed_camera", scenario_cmd, LOGS_DIR / f"{bag_name}_fixed.log"))
            wait_for_topic("/fixed_camera/camera/image_raw", "sensor_msgs/msg/Image", timeout=45.0)
            wait_for_topic("/fixed_camera/pose", "geometry_msgs/msg/PoseStamped", timeout=20.0)
            time.sleep(warmup_duration)
            wait_for_topic("/aruco/pose", "geometry_msgs/msg/PoseStamped", timeout=30.0)
            topics = FIXED_TOPICS
        else:
            drone_cfg = profile["sjtu_drone"]
            scenario_cmd = (
                "ros2 launch sjtu_drone_bringup sjtu_drone_spawn.launch.py "
                f"spawn_x:={drone_cfg['spawn_x']} "
                f"spawn_y:={drone_cfg['spawn_y']} "
                f"spawn_z:={drone_cfg['spawn_z']} "
                f"target_x:={drone_cfg['target_x']} "
                f"target_y:={drone_cfg['target_y']} "
                f"target_z:={drone_cfg['target_z']} "
                f"target_yaw:={drone_cfg['target_yaw']} "
                f"hover_delay_sec:={drone_cfg['hover_delay_sec']}"
            )
            commands["scenario"] = scenario_cmd
            processes.append(launch_managed("sjtu_drone", scenario_cmd, LOGS_DIR / f"{bag_name}_drone.log"))
            wait_for_topic("/drone/bottom/image_raw", "sensor_msgs/msg/Image", timeout=60.0)
            wait_for_topic("/drone/state", "std_msgs/msg/Int8", timeout=30.0)
            wait_for_drone_ready(profile)
            topics = DRONE_TOPICS

        bag_cmd = "ros2 bag record " + " ".join(shell_quote(topic) for topic in topics) + f" -o {shell_quote(bag_dir)}"
        commands["rosbag_record"] = bag_cmd
        bag_proc = launch_managed("rosbag_record", bag_cmd, LOGS_DIR / f"{bag_name}_record.log")
        processes.append(bag_proc)
        time.sleep(measurement_duration)
        terminate_process(bag_proc, timeout=20.0)

    finally:
        for proc in reversed(processes):
            terminate_process(proc)

    metadata_path = bag_dir / "metadata.yaml"
    if not metadata_path.exists():
        raise SystemExit(f"Recording finished but metadata.yaml is missing: {metadata_path}")

    topic_counts = parse_bag_topic_counts(metadata_path)
    write_manifest(
        bag_dir=bag_dir,
        bag_name=bag_name,
        args=args,
        profile=profile,
        commit=commit,
        dirty=dirty,
        commands=commands,
        topic_counts=topic_counts,
        log_paths={proc.name: str(proc.log_path) for proc in processes},
    )

    print(bag_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
