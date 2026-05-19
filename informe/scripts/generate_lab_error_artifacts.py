#!/usr/bin/env python3
"""Generate the lab command-vs-response error distribution figure.

This script consumes a physical-lab rosbag2 bag and computes, per attitude
axis (roll, pitch), the residual error between the marine reference command
and the real attitude of the Go2, *after compensating the optimal physical
lag* of the platform. It then renders per-axis error histograms in the same
style as the drone error figure of the simulation chapter
(``plot_drone_error_hist``).

Only standard ROS2 message types are needed:
- ``/marine_platform/debug_state`` (geometry_msgs/Vector3): expected command,
  ``x`` = roll [deg], ``y`` = pitch [deg].
- ``/utlidar/robot_odom`` (nav_msgs/Odometry): real body pose; the orientation
  quaternion is converted to roll/pitch. The lab movement reports verify that
  this odom attitude tracks ``/sportmodestate`` and ``/lowstate`` rpy.

Default bag is R5 (``lab_real_20260424_114454_robot_min``), the control run of
section 6.2.4 and the only lab bag in the checkout that still ships its ``.db3``
with the real-state telemetry recorded at full rate.

Run with the ``whisper_env`` interpreter (numpy + matplotlib + rosbags):
    /Users/maxi/miniforge3/envs/whisper_env/bin/python \
        informe/scripts/generate_lab_error_artifacts.py
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np

MPL_CONFIG_DIR = Path("/tmp") / "gazebo_no_seas_malo_mplconfig"
MPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CONFIG_DIR))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BAG = (
    REPO_ROOT
    / "informe"
    / "refs"
    / "lab_bundle_for_informe"
    / "rosbags"
    / "lab_real_20260424_114454_robot_min"
)
DEFAULT_OUT = REPO_ROOT / "informe" / "figures" / "results" / "lab_error_hist.png"

CMD_TOPIC = "/marine_platform/debug_state"
REAL_TOPIC = "/utlidar/robot_odom"

GRID_HZ = 50.0
LAG_WINDOW_S = 3.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bag", type=Path, default=DEFAULT_BAG, help="rosbag2 bag directory")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output PNG path")
    return parser.parse_args()


def quaternion_to_roll_pitch_deg(qx, qy, qz, qw):
    """Convert quaternion arrays to roll/pitch in degrees (ZYX convention)."""
    roll = np.degrees(np.arctan2(2.0 * (qw * qx + qy * qz), 1.0 - 2.0 * (qx * qx + qy * qy)))
    pitch = np.degrees(np.arcsin(np.clip(2.0 * (qw * qy - qz * qx), -1.0, 1.0)))
    return roll, pitch


def read_bag(bag: Path):
    """Return (cmd_t, cmd_roll, cmd_pitch, real_t, real_roll, real_pitch)."""
    typestore = get_typestore(Stores.ROS2_HUMBLE)
    cmd_t, cmd_roll, cmd_pitch = [], [], []
    real_t, quats = [], []
    with Reader(bag) as reader:
        topics = {conn.topic for conn in reader.connections}
        for required in (CMD_TOPIC, REAL_TOPIC):
            if required not in topics:
                raise SystemExit(f"Bag {bag.name} is missing required topic {required}")
        for conn, t_ns, raw in reader.messages():
            if conn.topic == CMD_TOPIC:
                msg = typestore.deserialize_cdr(raw, conn.msgtype)
                cmd_t.append(t_ns / 1e9)
                cmd_roll.append(msg.x)
                cmd_pitch.append(msg.y)
            elif conn.topic == REAL_TOPIC:
                msg = typestore.deserialize_cdr(raw, conn.msgtype)
                o = msg.pose.pose.orientation
                real_t.append(t_ns / 1e9)
                quats.append((o.x, o.y, o.z, o.w))
    quats = np.asarray(quats)
    real_roll, real_pitch = quaternion_to_roll_pitch_deg(*quats.T)
    return (
        np.asarray(cmd_t),
        np.asarray(cmd_roll),
        np.asarray(cmd_pitch),
        np.asarray(real_t),
        real_roll,
        real_pitch,
    )


def axis_metrics(cmd_t, cmd_v, real_t, real_v, grid):
    """Lag-sweep one axis and return its error metrics.

    The real attitude is modelled as ``real(t) ~ gain * cmd(t - lag)``. We sweep
    the lag, keep the value that maximises Pearson correlation, and compute the
    residual ``e(t) = real(t) - cmd(t - lag*)`` only where the shifted command
    stays inside the recorded command interval (no extrapolation).
    """
    real_on_grid = np.interp(grid, real_t, real_v)
    lags = np.arange(-LAG_WINDOW_S, LAG_WINDOW_S + 1e-9, 1.0 / GRID_HZ)

    best_corr, best_lag = -np.inf, 0.0
    for lag in lags:
        src = grid - lag
        mask = (src >= cmd_t[0]) & (src <= cmd_t[-1])
        if mask.sum() < 50:
            continue
        shifted = np.interp(src[mask], cmd_t, cmd_v)
        corr = np.corrcoef(shifted, real_on_grid[mask])[0, 1]
        if corr > best_corr:
            best_corr, best_lag = corr, lag

    # Residual after compensating the optimal lag.
    src = grid - best_lag
    mask = (src >= cmd_t[0]) & (src <= cmd_t[-1])
    shifted = np.interp(src[mask], cmd_t, cmd_v)
    real_masked = real_on_grid[mask]
    err = real_masked - shifted

    # Raw residual (no lag compensation), for context.
    err0 = np.interp(grid, real_t, real_v) - np.interp(grid, cmd_t, cmd_v)

    return {
        "lag_s": best_lag,
        "corr": best_corr,
        "gain": float(np.std(real_masked) / np.std(shifted)),
        "residual": err,
        "mean": float(np.mean(err)),
        "std": float(np.std(err)),
        "mae": float(np.mean(np.abs(err))),
        "rmse": float(np.sqrt(np.mean(err**2))),
        "mae_raw": float(np.mean(np.abs(err0))),
        "rmse_raw": float(np.sqrt(np.mean(err0**2))),
    }


def plot_error_hist(metrics: dict[str, dict], out_path: Path) -> None:
    """Per-axis error histograms, mirroring ``plot_drone_error_hist``."""
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 3.8))
    series = [
        ("roll", "ΔRoll (°)", "#9467bd"),
        ("pitch", "ΔPitch (°)", "#8c564b"),
    ]
    for ax, (axis, label, color) in zip(axes.flat, series):
        data = metrics[axis]["residual"]
        ax.hist(data, bins=35, color=color, alpha=0.8, edgecolor="white")
        ax.axvline(0.0, color="black", linewidth=0.9)
        ax.axvline(metrics[axis]["mean"], color="#d62728", linestyle="--", linewidth=1.2)
        ax.set_title(label)
        ax.set_xlabel("Error residual (°)")
        ax.grid(True, alpha=0.18)
    axes[0].set_ylabel("Frecuencia")

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    cmd_t, cmd_roll, cmd_pitch, real_t, real_roll, real_pitch = read_bag(args.bag)

    t0 = max(cmd_t[0], real_t[0])
    t1 = min(cmd_t[-1], real_t[-1])
    grid = np.arange(t0, t1, 1.0 / GRID_HZ)

    metrics = {
        "roll": axis_metrics(cmd_t, cmd_roll, real_t, real_roll, grid),
        "pitch": axis_metrics(cmd_t, cmd_pitch, real_t, real_pitch, grid),
    }

    print(f"Bag: {args.bag.name}")
    print(f"Command samples: {cmd_t.size}  |  real-state samples: {real_t.size}")
    for axis in ("roll", "pitch"):
        m = metrics[axis]
        print(
            f"  {axis:5s}  lag*={m['lag_s']:+.2f}s  corr={m['corr']:.3f}  gain={m['gain']:.3f}"
            f"  | residual mean={m['mean']:+.2f}° std={m['std']:.2f}°"
            f"  range=[{m['residual'].min():+.2f}, {m['residual'].max():+.2f}]°"
            f"  | MAE={m['mae']:.2f}° RMSE={m['rmse']:.2f}°"
        )

    plot_error_hist(metrics, args.out)
    print(f"Figure written to {args.out}")


if __name__ == "__main__":
    main()
