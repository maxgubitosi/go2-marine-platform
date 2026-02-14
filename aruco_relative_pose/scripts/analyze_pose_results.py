#!/usr/bin/env python3
"""Analyze ArUco pose estimation results vs ground truth.

Reads the CSV output from estimate_relative_pose.py and generates:
- Summary statistics (mean/std/max errors)
- Time-series plots: estimated vs GT for position and orientation
- Error distribution histograms
- Scatter plots (estimated vs GT)

Usage:
    python3 aruco_relative_pose/scripts/analyze_pose_results.py \
        --csv aruco_relative_pose/outputs/marine_sim_20260207_155320_aruco_pose.csv

    # Save plots to disk instead of showing:
    python3 aruco_relative_pose/scripts/analyze_pose_results.py \
        --csv aruco_relative_pose/outputs/marine_sim_20260207_155320_aruco_pose.csv \
        --save-dir aruco_relative_pose/outputs/analysis
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import matplotlib
    matplotlib.use("Agg")  # non-interactive by default; overridden if --show
    import matplotlib.pyplot as plt
except ImportError as exc:
    raise SystemExit("matplotlib not installed. Run: pip3 install matplotlib") from exc


def load_and_filter(csv_path: Path) -> pd.DataFrame:
    """Load CSV and keep only detected frames with valid GT."""
    df = pd.read_csv(csv_path)
    total = len(df)
    df = df[df["detected"] == True].copy()
    detected = len(df)

    gt_cols = ["gt_cam_marker_x", "gt_cam_marker_y", "gt_cam_marker_z"]
    has_gt = df[gt_cols].notna().all(axis=1)
    df = df[has_gt].copy()
    with_gt = len(df)

    print(f"Total frames:    {total}")
    print(f"Detected:        {detected} ({100*detected/total:.1f}%)")
    print(f"With GT:         {with_gt}")
    return df


def print_summary(df: pd.DataFrame) -> None:
    """Print error statistics table."""
    print("\n" + "=" * 65)
    print("  ERROR SUMMARY (estimated - ground truth, camera frame)")
    print("=" * 65)

    # Position errors
    df["err_x"] = df["tvec_x"] - df["gt_cam_marker_x"]
    df["err_y"] = df["tvec_y"] - df["gt_cam_marker_y"]
    df["err_z"] = df["tvec_z"] - df["gt_cam_marker_z"]
    df["err_pos"] = np.sqrt(df["err_x"]**2 + df["err_y"]**2 + df["err_z"]**2)

    print(f"\n{'':>20s} {'Mean':>10s} {'Std':>10s} {'|Max|':>10s} {'Median':>10s}")
    print("-" * 65)
    for name, col in [("ΔX (m)", "err_x"), ("ΔY (m)", "err_y"),
                       ("ΔZ (m)", "err_z"), ("‖ΔPos‖ (m)", "err_pos")]:
        vals = df[col]
        print(f"{name:>20s} {vals.mean():>+10.4f} {vals.std():>10.4f} "
              f"{vals.abs().max():>10.4f} {vals.median():>+10.4f}")

    # Orientation errors (already in CSV)
    print()
    for name, col_rad, col_deg in [
        ("ΔRoll", "roll_err_rad", "roll_err_deg"),
        ("ΔPitch", "pitch_err_rad", "pitch_err_deg"),
        ("ΔYaw", "yaw_err_rad", "yaw_err_deg"),
    ]:
        if col_deg in df.columns and df[col_deg].notna().any():
            vals = df[col_deg].dropna()
            print(f"{name + ' (°)':>20s} {vals.mean():>+10.3f} {vals.std():>10.3f} "
                  f"{vals.abs().max():>10.3f} {vals.median():>+10.3f}")

    # Reprojection error
    if "reproj_error_px" in df.columns:
        rp = df["reproj_error_px"].dropna()
        print(f"\n{'Reproj (px)':>20s} {rp.mean():>+10.3f} {rp.std():>10.3f} "
              f"{rp.abs().max():>10.3f} {rp.median():>+10.3f}")

    print("=" * 65)


def plot_position_timeseries(df: pd.DataFrame, save_dir: Path | None) -> plt.Figure:
    """Plot estimated vs GT position over time."""
    fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)
    fig.suptitle("Position: Estimated vs Ground Truth (camera frame)", fontsize=14)

    idx = np.arange(len(df))
    labels = [("X", "tvec_x", "gt_cam_marker_x"),
              ("Y", "tvec_y", "gt_cam_marker_y"),
              ("Z", "tvec_z", "gt_cam_marker_z")]

    for ax, (name, est_col, gt_col) in zip(axes, labels):
        ax.plot(idx, df[est_col].values, "b-", linewidth=0.8, alpha=0.9, label="Estimado")
        ax.plot(idx, df[gt_col].values, "r--", linewidth=0.8, alpha=0.9, label="Ground Truth")
        ax.set_ylabel(f"{name} (m)")
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(True, alpha=0.3)

    axes[-1].set_xlabel("Frame")
    fig.tight_layout()

    if save_dir:
        fig.savefig(save_dir / "position_timeseries.png", dpi=150)
        print(f"  Saved: {save_dir / 'position_timeseries.png'}")
    return fig


def plot_orientation_timeseries(df: pd.DataFrame, save_dir: Path | None) -> plt.Figure:
    """Plot estimated vs GT orientation over time."""
    fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)
    fig.suptitle("Orientation: Estimated vs Ground Truth (camera frame)", fontsize=14)

    idx = np.arange(len(df))
    labels = [("Roll", "roll_wrapped", "gt_cam_marker_roll_wrapped"),
              ("Pitch", "pitch_wrapped", "gt_cam_marker_pitch_wrapped"),
              ("Yaw", "yaw_wrapped", "gt_cam_marker_yaw_wrapped")]

    for ax, (name, est_col, gt_col) in zip(axes, labels):
        est = np.degrees(df[est_col].values)
        gt = np.degrees(df[gt_col].values)
        ax.plot(idx, est, "b-", linewidth=0.8, alpha=0.9, label="Estimado")
        ax.plot(idx, gt, "r--", linewidth=0.8, alpha=0.9, label="Ground Truth")
        ax.set_ylabel(f"{name} (°)")
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(True, alpha=0.3)

    axes[-1].set_xlabel("Frame")
    fig.tight_layout()

    if save_dir:
        fig.savefig(save_dir / "orientation_timeseries.png", dpi=150)
        print(f"  Saved: {save_dir / 'orientation_timeseries.png'}")
    return fig


def plot_position_errors(df: pd.DataFrame, save_dir: Path | None) -> plt.Figure:
    """Plot position error timeseries + histogram."""
    df["err_x"] = df["tvec_x"] - df["gt_cam_marker_x"]
    df["err_y"] = df["tvec_y"] - df["gt_cam_marker_y"]
    df["err_z"] = df["tvec_z"] - df["gt_cam_marker_z"]
    df["err_pos"] = np.sqrt(df["err_x"]**2 + df["err_y"]**2 + df["err_z"]**2)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle("Position Errors (estimated - GT)", fontsize=14)

    idx = np.arange(len(df))

    # Time series
    for col, label, color in [("err_x", "ΔX", "tab:blue"),
                                ("err_y", "ΔY", "tab:orange"),
                                ("err_z", "ΔZ", "tab:green")]:
        axes[0, 0].plot(idx, df[col].values, color=color, linewidth=0.7, alpha=0.8, label=label)
    axes[0, 0].axhline(0, color="k", linewidth=0.5)
    axes[0, 0].set_ylabel("Error (m)")
    axes[0, 0].set_xlabel("Frame")
    axes[0, 0].legend(fontsize=8)
    axes[0, 0].set_title("Per-axis errors")
    axes[0, 0].grid(True, alpha=0.3)

    # Norm error
    axes[0, 1].plot(idx, df["err_pos"].values, "k-", linewidth=0.7)
    axes[0, 1].set_ylabel("‖Error‖ (m)")
    axes[0, 1].set_xlabel("Frame")
    axes[0, 1].set_title(f"Euclidean error (mean={df['err_pos'].mean():.4f} m)")
    axes[0, 1].grid(True, alpha=0.3)

    # Histogram per axis
    bins = 30
    for col, label, color in [("err_x", "ΔX", "tab:blue"),
                                ("err_y", "ΔY", "tab:orange"),
                                ("err_z", "ΔZ", "tab:green")]:
        axes[1, 0].hist(df[col].values, bins=bins, alpha=0.5, label=label, color=color)
    axes[1, 0].set_xlabel("Error (m)")
    axes[1, 0].set_ylabel("Count")
    axes[1, 0].set_title("Error distribution")
    axes[1, 0].legend(fontsize=8)

    # Histogram norm
    axes[1, 1].hist(df["err_pos"].values, bins=bins, color="gray", alpha=0.7)
    axes[1, 1].set_xlabel("‖Error‖ (m)")
    axes[1, 1].set_ylabel("Count")
    axes[1, 1].set_title("Euclidean error distribution")

    fig.tight_layout()

    if save_dir:
        fig.savefig(save_dir / "position_errors.png", dpi=150)
        print(f"  Saved: {save_dir / 'position_errors.png'}")
    return fig


def plot_orientation_errors(df: pd.DataFrame, save_dir: Path | None) -> plt.Figure:
    """Plot orientation error timeseries + histogram."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle("Orientation Errors (estimated - GT)", fontsize=14)

    idx = np.arange(len(df))

    # Time series
    for col, label, color in [("roll_err_deg", "ΔRoll", "tab:blue"),
                                ("pitch_err_deg", "ΔPitch", "tab:orange"),
                                ("yaw_err_deg", "ΔYaw", "tab:green")]:
        if col in df.columns:
            axes[0, 0].plot(idx, df[col].values, color=color, linewidth=0.7, alpha=0.8, label=label)
    axes[0, 0].axhline(0, color="k", linewidth=0.5)
    axes[0, 0].set_ylabel("Error (°)")
    axes[0, 0].set_xlabel("Frame")
    axes[0, 0].legend(fontsize=8)
    axes[0, 0].set_title("Per-axis angular errors")
    axes[0, 0].grid(True, alpha=0.3)

    # Total angular error
    if all(c in df.columns for c in ["roll_err_deg", "pitch_err_deg", "yaw_err_deg"]):
        total_ang = np.sqrt(df["roll_err_deg"]**2 + df["pitch_err_deg"]**2 + df["yaw_err_deg"]**2)
        axes[0, 1].plot(idx, total_ang.values, "k-", linewidth=0.7)
        axes[0, 1].set_ylabel("‖Error‖ (°)")
        axes[0, 1].set_xlabel("Frame")
        axes[0, 1].set_title(f"Total angular error (mean={total_ang.mean():.2f}°)")
        axes[0, 1].grid(True, alpha=0.3)

    # Histograms
    bins = 30
    for col, label, color in [("roll_err_deg", "ΔRoll", "tab:blue"),
                                ("pitch_err_deg", "ΔPitch", "tab:orange"),
                                ("yaw_err_deg", "ΔYaw", "tab:green")]:
        if col in df.columns:
            axes[1, 0].hist(df[col].dropna().values, bins=bins, alpha=0.5, label=label, color=color)
    axes[1, 0].set_xlabel("Error (°)")
    axes[1, 0].set_ylabel("Count")
    axes[1, 0].set_title("Angular error distribution")
    axes[1, 0].legend(fontsize=8)

    if all(c in df.columns for c in ["roll_err_deg", "pitch_err_deg", "yaw_err_deg"]):
        axes[1, 1].hist(total_ang.dropna().values, bins=bins, color="gray", alpha=0.7)
        axes[1, 1].set_xlabel("‖Error‖ (°)")
        axes[1, 1].set_ylabel("Count")
        axes[1, 1].set_title("Total angular error distribution")

    fig.tight_layout()

    if save_dir:
        fig.savefig(save_dir / "orientation_errors.png", dpi=150)
        print(f"  Saved: {save_dir / 'orientation_errors.png'}")
    return fig


def plot_scatter(df: pd.DataFrame, save_dir: Path | None) -> plt.Figure:
    """Scatter: estimated vs GT for each axis."""
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    fig.suptitle("Estimated vs Ground Truth (ideal = diagonal)", fontsize=14)

    pos_pairs = [("tvec_x", "gt_cam_marker_x", "X (m)"),
                 ("tvec_y", "gt_cam_marker_y", "Y (m)"),
                 ("tvec_z", "gt_cam_marker_z", "Z (m)")]

    for ax, (est, gt, label) in zip(axes[0], pos_pairs):
        ax.scatter(df[gt].values, df[est].values, s=4, alpha=0.5)
        lims = [min(df[gt].min(), df[est].min()), max(df[gt].max(), df[est].max())]
        margin = (lims[1] - lims[0]) * 0.05
        lims = [lims[0] - margin, lims[1] + margin]
        ax.plot(lims, lims, "r--", linewidth=0.8, label="Ideal")
        ax.set_xlabel(f"GT {label}")
        ax.set_ylabel(f"Est {label}")
        ax.set_aspect("equal")
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)

    ori_pairs = [("roll_wrapped", "gt_cam_marker_roll_wrapped", "Roll (rad)"),
                 ("pitch_wrapped", "gt_cam_marker_pitch_wrapped", "Pitch (rad)"),
                 ("yaw_wrapped", "gt_cam_marker_yaw_wrapped", "Yaw (rad)")]

    for ax, (est, gt, label) in zip(axes[1], ori_pairs):
        ax.scatter(df[gt].values, df[est].values, s=4, alpha=0.5, color="tab:orange")
        lims = [min(df[gt].min(), df[est].min()), max(df[gt].max(), df[est].max())]
        margin = (lims[1] - lims[0]) * 0.05
        lims = [lims[0] - margin, lims[1] + margin]
        ax.plot(lims, lims, "r--", linewidth=0.8, label="Ideal")
        ax.set_xlabel(f"GT {label}")
        ax.set_ylabel(f"Est {label}")
        ax.set_aspect("equal")
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)

    fig.tight_layout()

    if save_dir:
        fig.savefig(save_dir / "scatter_est_vs_gt.png", dpi=150)
        print(f"  Saved: {save_dir / 'scatter_est_vs_gt.png'}")
    return fig


def plot_reproj_error(df: pd.DataFrame, save_dir: Path | None) -> plt.Figure:
    """Plot reprojection error over time."""
    if "reproj_error_px" not in df.columns or df["reproj_error_px"].isna().all():
        return None

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    fig.suptitle("Reprojection Error", fontsize=14)

    rp = df["reproj_error_px"].values
    idx = np.arange(len(df))

    axes[0].plot(idx, rp, "b-", linewidth=0.7)
    axes[0].set_xlabel("Frame")
    axes[0].set_ylabel("Reproj error (px)")
    axes[0].set_title(f"Over time (mean={np.nanmean(rp):.3f} px)")
    axes[0].grid(True, alpha=0.3)

    axes[1].hist(rp[~np.isnan(rp)], bins=30, color="steelblue", alpha=0.7)
    axes[1].set_xlabel("Reproj error (px)")
    axes[1].set_ylabel("Count")
    axes[1].set_title("Distribution")

    fig.tight_layout()

    if save_dir:
        fig.savefig(save_dir / "reproj_error.png", dpi=150)
        print(f"  Saved: {save_dir / 'reproj_error.png'}")
    return fig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze ArUco pose estimation results")
    parser.add_argument("--csv", required=True, help="CSV from estimate_relative_pose.py")
    parser.add_argument("--save-dir", default=None,
                        help="Directory to save plots (default: show interactively)")
    parser.add_argument("--show", action="store_true",
                        help="Show plots interactively (in addition to saving)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise SystemExit(f"No existe: {csv_path}")

    df = load_and_filter(csv_path)
    if len(df) == 0:
        raise SystemExit("No hay frames detectados con GT válido.")

    print_summary(df)

    save_dir = Path(args.save_dir) if args.save_dir else None
    if save_dir:
        save_dir.mkdir(parents=True, exist_ok=True)
        print(f"\nSaving plots to: {save_dir}")

    if args.show:
        matplotlib.use("TkAgg")
        import importlib
        importlib.reload(plt)

    figs = []
    figs.append(plot_position_timeseries(df, save_dir))
    figs.append(plot_orientation_timeseries(df, save_dir))
    figs.append(plot_position_errors(df, save_dir))
    figs.append(plot_orientation_errors(df, save_dir))
    figs.append(plot_scatter(df, save_dir))
    figs.append(plot_reproj_error(df, save_dir))

    if args.show:
        plt.show()

    if save_dir:
        print(f"\n✅ All plots saved to: {save_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
