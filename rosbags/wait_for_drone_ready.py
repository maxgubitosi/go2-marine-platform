#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import sys
import time

import rclpy
from geometry_msgs.msg import Pose
from rclpy.node import Node
from std_msgs.msg import Bool, Int8, String


class DroneReadyWaiter(Node):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__("wait_for_drone_ready")
        self.args = args
        self.last_state: int | None = None
        self.last_mode: str | None = None
        self.last_pose: Pose | None = None
        self.last_detection_true_monotonic: float | None = None
        self.stable_since_monotonic: float | None = None

        self.create_subscription(Int8, args.state_topic, self._state_cb, 10)
        self.create_subscription(Pose, args.gt_pose_topic, self._gt_pose_cb, 10)
        self.create_subscription(Bool, args.detection_topic, self._detection_cb, 10)
        self.create_subscription(String, args.cmd_mode_topic, self._mode_cb, 10)

    def _state_cb(self, msg: Int8) -> None:
        self.last_state = int(msg.data)

    def _gt_pose_cb(self, msg: Pose) -> None:
        self.last_pose = msg

    def _detection_cb(self, msg: Bool) -> None:
        if msg.data:
            self.last_detection_true_monotonic = time.monotonic()

    def _mode_cb(self, msg: String) -> None:
        self.last_mode = msg.data.strip().lower()

    def readiness_snapshot(self) -> tuple[bool, str]:
        if self.last_state is None:
            return False, "waiting_state"
        if self.last_pose is None:
            return False, "waiting_gt_pose"
        if self.last_state not in self.args.accepted_states:
            return False, f"state_{self.last_state}"
        if self.last_detection_true_monotonic is None:
            return False, "waiting_detection"

        detection_age = time.monotonic() - self.last_detection_true_monotonic
        if detection_age > self.args.detection_freshness:
            return False, f"detection_stale_{detection_age:.2f}s"

        dx = self.last_pose.position.x - self.args.target_x
        dy = self.last_pose.position.y - self.args.target_y
        dz = self.last_pose.position.z - self.args.target_z
        horizontal_error = math.hypot(dx, dy)
        vertical_error = abs(dz)

        if horizontal_error > self.args.horizontal_tol:
            return False, f"horizontal_error_{horizontal_error:.3f}m"
        if vertical_error > self.args.vertical_tol:
            return False, f"vertical_error_{vertical_error:.3f}m"
        return True, (
            f"ready state={self.last_state} mode={self.last_mode or 'unknown'} "
            f"h_err={horizontal_error:.3f}m v_err={vertical_error:.3f}m"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Wait until the SJTU drone is ready for comparable recording.")
    parser.add_argument("--state-topic", default="/drone/state")
    parser.add_argument("--gt-pose-topic", default="/drone/gt_pose")
    parser.add_argument("--detection-topic", default="/aruco/detection")
    parser.add_argument("--cmd-mode-topic", default="/drone/cmd_mode")
    parser.add_argument("--target-x", type=float, required=True)
    parser.add_argument("--target-y", type=float, required=True)
    parser.add_argument("--target-z", type=float, required=True)
    parser.add_argument("--horizontal-tol", type=float, default=0.10)
    parser.add_argument("--vertical-tol", type=float, default=0.15)
    parser.add_argument("--stable-for", type=float, default=3.0)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--detection-freshness", type=float, default=1.0)
    parser.add_argument("--accepted-states", default="1")
    args = parser.parse_args()
    args.accepted_states = {
        int(item.strip()) for item in str(args.accepted_states).split(",") if item.strip()
    }
    return args


def main() -> int:
    args = parse_args()
    rclpy.init()
    node = DroneReadyWaiter(args)
    deadline = time.monotonic() + args.timeout

    try:
        while time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
            ready, reason = node.readiness_snapshot()
            now = time.monotonic()
            if ready:
                if node.stable_since_monotonic is None:
                    node.stable_since_monotonic = now
                held = now - node.stable_since_monotonic
                if held >= args.stable_for:
                    print(reason)
                    return 0
            else:
                node.stable_since_monotonic = None
    finally:
        node.destroy_node()
        rclpy.shutdown()

    print("timeout")
    return 1


if __name__ == "__main__":
    sys.exit(main())
