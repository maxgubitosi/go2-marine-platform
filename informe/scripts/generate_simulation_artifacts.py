#!/usr/bin/env python3
"""Generate thesis-ready simulation metrics and figures.

This script consolidates the official simulation bags used in the thesis:
- one fixed-camera baseline (`marine_sim_*`)
- two or more SJTU drone runs (`sjtu_drone_sim_*`)

It can reuse existing realtime evaluation CSVs or regenerate them by calling
`aruco_relative_pose/scripts/evaluate_realtime_aruco.py`.
"""

from __future__ import annotations

import argparse
import importlib.util
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

MPL_CONFIG_DIR = Path("/tmp") / "gazebo_no_seas_malo_mplconfig"
MPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CONFIG_DIR))

try:
    import yaml
except ImportError:  # pragma: no cover - fallback handled below
    yaml = None

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


REPO_ROOT = Path(__file__).resolve().parents[2]
EVAL_SCRIPT = REPO_ROOT / "aruco_relative_pose" / "scripts" / "evaluate_realtime_aruco.py"
DEFAULT_OUT_DIR = REPO_ROOT / "informe" / "figures" / "results"
DEFAULT_WORLD_INIT_X = 0.40
DEFAULT_WORLD_INIT_Y = 0.0
ROLLING_WINDOW_SAMPLES = 11
WINDOW_COUNT = 5


@dataclass
class RunSpec:
    bag_path: Path
    role: str
    source: str
    display_label: str
    manifest: dict[str, Any] | None = None

    @property
    def bag_name(self) -> str:
        return self.bag_path.name

    @property
    def eval_dir(self) -> Path:
        return REPO_ROOT / "aruco_relative_pose" / "outputs" / f"{self.bag_name}_realtime_eval"

    @property
    def csv_path(self) -> Path:
        return self.eval_dir / "realtime_aruco_evaluation.csv"

    @property
    def manifest_path(self) -> Path:
        return self.bag_path / "experiment_manifest.yaml"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate thesis simulation artifacts")
    parser.add_argument(
        "--fixed-bag",
        type=Path,
        default=REPO_ROOT / "rosbags" / "marine_sim_20260216_175945",
        help="Baseline fixed-camera rosbag",
    )
    parser.add_argument(
        "--drone-bag-a",
        type=Path,
        default=REPO_ROOT / "rosbags" / "sjtu_drone_sim_20260216_164654",
        help="Legacy primary SJTU drone rosbag",
    )
    parser.add_argument(
        "--drone-bag-b",
        type=Path,
        default=REPO_ROOT / "rosbags" / "sjtu_drone_sim_20260216_180434",
        help="Legacy repeated SJTU drone rosbag",
    )
    parser.add_argument(
        "--drone-bags",
        type=Path,
        nargs="+",
        default=None,
        help="Comparable SJTU drone bags used for the report",
    )
    parser.add_argument(
        "--primary-run",
        default="median",
        help="Primary drone run: 'median', a role such as 'r1', or an exact bag name",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Directory where thesis-ready figures and CSV summaries will be written",
    )
    parser.add_argument(
        "--force-eval",
        action="store_true",
        help="Regenerate realtime evaluation CSVs even if they already exist",
    )
    parser.add_argument(
        "--world-init-x",
        type=float,
        default=None,
        help="Optional Go2 spawn X override passed to the evaluator",
    )
    parser.add_argument(
        "--world-init-y",
        type=float,
        default=None,
        help="Optional Go2 spawn Y override passed to the evaluator",
    )
    return parser.parse_args()


def load_eval_module() -> Any:
    spec = importlib.util.spec_from_file_location("evaluate_realtime_aruco", EVAL_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load evaluator from {EVAL_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required to read manifests and metadata.")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def parse_metadata_duration_seconds(metadata_path: Path) -> float:
    text = metadata_path.read_text(encoding="utf-8")
    if yaml is not None:
        data = yaml.safe_load(text)
        return data["rosbag2_bagfile_information"]["duration"]["nanoseconds"] / 1e9

    match = re.search(r"duration:\s*\n\s*nanoseconds:\s*(\d+)", text)
    if not match:
        raise RuntimeError(f"Could not parse duration from {metadata_path}")
    return int(match.group(1)) / 1e9


def load_manifest_if_present(bag_path: Path) -> dict[str, Any] | None:
    manifest_path = bag_path / "experiment_manifest.yaml"
    if manifest_path.exists():
        return load_yaml(manifest_path)
    return None


def infer_source(bag_name: str) -> str:
    return "sjtu_drone" if bag_name.startswith("sjtu_drone") else "fixed_camera"


def infer_role(manifest: dict[str, Any] | None, bag_name: str, fallback: str) -> str:
    if manifest and manifest.get("role"):
        return str(manifest["role"])
    if "report_v2_" in bag_name:
        return bag_name.split("report_v2_", 1)[1]
    return fallback


def display_label_for_role(role: str, index: int | None = None) -> str:
    lower = role.lower()
    if lower == "ref":
        return "Referencia"
    if lower == "smoke":
        return "Smoke"
    if lower.startswith("r") and lower[1:].isdigit():
        return lower.upper()
    if lower == "fixed_baseline":
        return "Baseline"
    if lower == "drone_a":
        return "Dron A"
    if lower == "drone_b":
        return "Dron B"
    if index is not None:
        return f"Dron {index}"
    return role


def build_run_specs(args: argparse.Namespace) -> list[RunSpec]:
    runs: list[RunSpec] = []

    fixed_manifest = load_manifest_if_present(args.fixed_bag)
    fixed_role = infer_role(fixed_manifest, args.fixed_bag.name, "fixed_baseline")
    fixed_source = scenario_source_from_manifest_or_name(fixed_manifest, args.fixed_bag.name)
    runs.append(
        RunSpec(
            bag_path=args.fixed_bag,
            role=fixed_role,
            source=fixed_source,
            display_label="Baseline fijo",
            manifest=fixed_manifest,
        )
    )

    drone_paths = args.drone_bags if args.drone_bags is not None else [args.drone_bag_a, args.drone_bag_b]
    for idx, bag_path in enumerate(drone_paths, start=1):
        manifest = load_manifest_if_present(bag_path)
        fallback_role = f"drone_{idx}"
        role = infer_role(manifest, bag_path.name, fallback_role)
        source = scenario_source_from_manifest_or_name(manifest, bag_path.name)
        runs.append(
            RunSpec(
                bag_path=bag_path,
                role=role,
                source=source,
                display_label=display_label_for_role(role, index=idx),
                manifest=manifest,
            )
        )
    return runs


def scenario_source_from_manifest_or_name(manifest: dict[str, Any] | None, bag_name: str) -> str:
    if manifest and manifest.get("scenario"):
        return str(manifest["scenario"])
    return infer_source(bag_name)


def resolve_world_init(run: RunSpec, args: argparse.Namespace) -> tuple[float, float]:
    if args.world_init_x is not None or args.world_init_y is not None:
        return (
            float(args.world_init_x if args.world_init_x is not None else DEFAULT_WORLD_INIT_X),
            float(args.world_init_y if args.world_init_y is not None else DEFAULT_WORLD_INIT_Y),
        )
    if run.manifest:
        experiment = run.manifest.get("experiment", {})
        return (
            float(experiment.get("world_init_x", DEFAULT_WORLD_INIT_X)),
            float(experiment.get("world_init_y", DEFAULT_WORLD_INIT_Y)),
        )
    return DEFAULT_WORLD_INIT_X, DEFAULT_WORLD_INIT_Y


def ensure_evaluation(run: RunSpec, eval_module: Any, force_eval: bool, args: argparse.Namespace) -> pd.DataFrame:
    if force_eval or not run.csv_path.exists():
        world_init_x, world_init_y = resolve_world_init(run, args)
        run.eval_dir.mkdir(parents=True, exist_ok=True)
        eval_module.evaluate(
            run.bag_path,
            run.eval_dir,
            world_init_x=world_init_x,
            world_init_y=world_init_y,
            camera_source=run.source,
        )
    return pd.read_csv(run.csv_path)


def compute_window_summary(df: pd.DataFrame, window_count: int = WINDOW_COUNT) -> pd.DataFrame:
    t_min = float(df["t_rel"].min())
    t_max = float(df["t_rel"].max())
    edges = np.linspace(t_min, t_max, window_count + 1)
    rows: list[dict[str, float | int]] = []
    for idx in range(window_count):
        start = edges[idx]
        end = edges[idx + 1]
        if idx == window_count - 1:
            mask = (df["t_rel"] >= start) & (df["t_rel"] <= end)
        else:
            mask = (df["t_rel"] >= start) & (df["t_rel"] < end)
        window = df.loc[mask].copy()
        if window.empty:
            rows.append(
                {
                    "window_index": idx + 1,
                    "t_start_s": start,
                    "t_end_s": end,
                    "sample_count": 0,
                    "mean_err_pos_m": np.nan,
                    "std_err_pos_m": np.nan,
                    "mean_err_x_m": np.nan,
                    "mean_err_y_m": np.nan,
                    "mean_err_z_m": np.nan,
                    "std_err_roll_deg": np.nan,
                }
            )
            continue
        rows.append(
            {
                "window_index": idx + 1,
                "t_start_s": start,
                "t_end_s": end,
                "sample_count": int(len(window)),
                "mean_err_pos_m": float(window["err_pos"].mean()),
                "std_err_pos_m": float(window["err_pos"].std()),
                "mean_err_x_m": float(window["err_x"].mean()),
                "mean_err_y_m": float(window["err_y"].mean()),
                "mean_err_z_m": float(window["err_z"].mean()),
                "std_err_roll_deg": float(window["err_roll_deg"].std()),
            }
        )
    return pd.DataFrame(rows)


def stable_axis(df: pd.DataFrame) -> str:
    stds = {
        "roll": float(df["err_roll_deg"].std()),
        "pitch": float(df["err_pitch_deg"].std()),
        "yaw": float(df["err_yaw_deg"].std()),
    }
    return min(stds, key=stds.get)


def synthetic_observation(df: pd.DataFrame) -> str:
    axis = stable_axis(df)
    err_mean = float(df["err_pos"].mean())
    z_std = float(df["err_z"].std())
    if axis == "yaw":
        return (
            f"Yaw es la componente angular mas estable; el error medio de posicion queda en "
            f"{err_mean:.3f} m y la mayor dispersion aparece en Z ({z_std:.3f} m)."
        )
    return f"La componente angular mas estable es {axis}; el error medio de posicion queda en {err_mean:.3f} m."


def build_metrics_row(run: RunSpec, df: pd.DataFrame, duration_s: float, world_init_x: float, world_init_y: float) -> dict[str, object]:
    slope_mm_s = float(np.polyfit(df["t_rel"], df["err_pos"], 1)[0] * 1000.0)
    return {
        "role": run.role,
        "display_label": run.display_label,
        "bag_name": run.bag_name,
        "source": run.source,
        "duration_s": duration_s,
        "sample_count": int(len(df)),
        "detection_rate_hz": float(len(df) / duration_s),
        "mean_err_pos_m": float(df["err_pos"].mean()),
        "std_err_pos_m": float(df["err_pos"].std()),
        "p95_err_pos_m": float(df["err_pos"].quantile(0.95)),
        "mean_err_x_m": float(df["err_x"].mean()),
        "mean_err_y_m": float(df["err_y"].mean()),
        "mean_err_z_m": float(df["err_z"].mean()),
        "std_err_roll_deg": float(df["err_roll_deg"].std()),
        "std_err_pitch_deg": float(df["err_pitch_deg"].std()),
        "std_err_yaw_deg": float(df["err_yaw_deg"].std()),
        "stable_axis": stable_axis(df),
        "slope_err_pos_mm_s": slope_mm_s,
        "world_init_x": world_init_x,
        "world_init_y": world_init_y,
        "observation": synthetic_observation(df),
    }


def save_metrics_summary(rows: list[dict[str, object]], out_dir: Path) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    fixed_df = df[df["source"] == "fixed_camera"].copy()
    drone_df = df[df["source"] == "sjtu_drone"].copy().sort_values("role")
    df = pd.concat([fixed_df, drone_df], ignore_index=True)
    csv_path = out_dir / "simulation_metrics_summary.csv"
    df.to_csv(csv_path, index=False)
    return df


def plot_position_vs_gt(df: pd.DataFrame, title: str, out_path: Path) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(10.2, 7.4), sharex=True)
    t = df["t_rel"].to_numpy()
    for ax, axis in zip(axes, ["x", "y", "z"]):
        ax.plot(t, df[f"est_{axis}"], color="#1f77b4", linewidth=1.2, label="Estimado")
        ax.plot(t, df[f"gt_{axis}"], color="#d62728", linestyle="--", linewidth=1.1, label="Ground truth")
        ax.set_ylabel(f"{axis.upper()} (m)")
        ax.grid(True, alpha=0.25)
        ax.legend(loc="upper right", fontsize=8)
    axes[-1].set_xlabel("Tiempo (s)")
    fig.suptitle(title, fontsize=13)
    fig.tight_layout()
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_orientation_vs_gt(df: pd.DataFrame, title: str, out_path: Path) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(10.2, 7.4), sharex=True)
    t = df["t_rel"].to_numpy()
    for ax, axis in zip(axes, ["roll", "pitch", "yaw"]):
        ax.plot(t, np.degrees(df[f"est_{axis}"]), color="#1f77b4", linewidth=1.2, label="Estimado")
        ax.plot(t, np.degrees(df[f"gt_{axis}"]), color="#d62728", linestyle="--", linewidth=1.1, label="Ground truth")
        ax.set_ylabel(f"{axis.capitalize()} (°)")
        ax.grid(True, alpha=0.25)
        ax.legend(loc="upper right", fontsize=8)
    axes[-1].set_xlabel("Tiempo (s)")
    fig.suptitle(title, fontsize=13)
    fig.tight_layout()
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_fixed_error_hist(df: pd.DataFrame, out_path: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(10.0, 7.2))
    series = [
        ("err_x", "ΔX (m)", "#1f77b4"),
        ("err_y", "ΔY (m)", "#ff7f0e"),
        ("err_z", "ΔZ (m)", "#2ca02c"),
        ("err_pos", "||Δpos|| (m)", "#4d4d4d"),
    ]
    for ax, (col, label, color) in zip(axes.flat, series):
        ax.hist(df[col], bins=35, color=color, alpha=0.8, edgecolor="white")
        if col != "err_pos":
            ax.axvline(0.0, color="black", linewidth=0.9)
        ax.axvline(float(df[col].mean()), color="#d62728", linestyle="--", linewidth=1.2)
        ax.set_title(label)
        ax.grid(True, alpha=0.18)
    fig.suptitle("Distribucion de errores del caso base con camara fija", fontsize=13)
    fig.tight_layout()
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_drone_error_hist(df: pd.DataFrame, out_path: Path) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(11.2, 7.0))
    series = [
        ("err_x", "ΔX (m)", "#1f77b4"),
        ("err_y", "ΔY (m)", "#ff7f0e"),
        ("err_z", "ΔZ (m)", "#2ca02c"),
        ("err_roll_deg", "ΔRoll (°)", "#9467bd"),
        ("err_pitch_deg", "ΔPitch (°)", "#8c564b"),
        ("err_yaw_deg", "ΔYaw (°)", "#17becf"),
    ]
    for ax, (col, label, color) in zip(axes.flat, series):
        ax.hist(df[col], bins=35, color=color, alpha=0.8, edgecolor="white")
        ax.axvline(0.0, color="black", linewidth=0.9)
        ax.axvline(float(df[col].mean()), color="#d62728", linestyle="--", linewidth=1.2)
        ax.set_title(label)
        ax.grid(True, alpha=0.18)
    fig.suptitle("Distribucion de errores de la corrida principal con dron", fontsize=13)
    fig.tight_layout()
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_run_comparison(metrics_df: pd.DataFrame, out_path: Path) -> None:
    drone_df = metrics_df[metrics_df["source"] == "sjtu_drone"].copy().sort_values("role")
    labels = drone_df["display_label"].tolist()
    x = np.arange(len(labels))

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.8))

    pos_metrics = ["mean_err_pos_m", "p95_err_pos_m", "std_err_pos_m"]
    pos_titles = ["Media", "P95", "Std"]
    width = 0.22
    for idx, (col, title) in enumerate(zip(pos_metrics, pos_titles)):
        axes[0].bar(x + (idx - 1) * width, drone_df[col], width=width, label=title)
    axes[0].set_xticks(x, labels)
    axes[0].set_ylabel("Metros")
    axes[0].set_title("Metricas de error de posicion")
    axes[0].legend(fontsize=8)
    axes[0].grid(True, axis="y", alpha=0.2)

    ang_metrics = ["std_err_roll_deg", "std_err_pitch_deg", "std_err_yaw_deg"]
    ang_titles = ["σ roll", "σ pitch", "σ yaw"]
    for idx, (col, title) in enumerate(zip(ang_metrics, ang_titles)):
        axes[1].bar(x + (idx - 1) * width, drone_df[col], width=width, label=title)
    axes[1].set_xticks(x, labels)
    axes[1].set_ylabel("Grados")
    axes[1].set_title("Dispersion angular")
    axes[1].legend(fontsize=8)
    axes[1].grid(True, axis="y", alpha=0.2)

    fig.suptitle("Comparacion entre las corridas del escenario con dron", fontsize=13)
    fig.tight_layout()
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_error_time(df: pd.DataFrame, window_df: pd.DataFrame, out_path: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(10.4, 7.0), sharex=False)

    rolling = df["err_pos"].rolling(window=ROLLING_WINDOW_SAMPLES, center=True, min_periods=1).mean()
    axes[0].plot(df["t_rel"], df["err_pos"], color="#9e9e9e", linewidth=0.9, alpha=0.75, label="||Δpos||")
    axes[0].plot(df["t_rel"], rolling, color="#1f77b4", linewidth=1.8, label="Media movil")
    axes[0].set_ylabel("Error (m)")
    axes[0].set_title("Error euclidiano de posicion a lo largo del tiempo")
    axes[0].legend(fontsize=8)
    axes[0].grid(True, alpha=0.22)

    centers = 0.5 * (window_df["t_start_s"] + window_df["t_end_s"])
    widths = window_df["t_end_s"] - window_df["t_start_s"]
    axes[1].bar(
        centers,
        window_df["mean_err_pos_m"],
        width=widths * 0.84,
        yerr=window_df["std_err_pos_m"],
        color="#4e79a7",
        alpha=0.85,
        capsize=4,
    )
    axes[1].set_xlabel("Tiempo (s)")
    axes[1].set_ylabel("Error medio por ventana (m)")
    axes[1].set_title("Promedio de ||Δpos|| por cinco ventanas temporales")
    axes[1].grid(True, axis="y", alpha=0.22)

    fig.suptitle("Estabilidad temporal del error en la corrida principal", fontsize=13)
    fig.tight_layout()
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def ensure_runs_exist(runs: list[RunSpec]) -> None:
    for run in runs:
        if not run.bag_path.exists():
            raise FileNotFoundError(f"Rosbag not found: {run.bag_path}")
        metadata = run.bag_path / "metadata.yaml"
        if not metadata.exists():
            raise FileNotFoundError(f"metadata.yaml not found for {run.bag_path}")


def choose_primary_role(drone_metrics: pd.DataFrame, requested: str) -> str:
    if requested == "median":
        ordered = drone_metrics.sort_values(["mean_err_pos_m", "bag_name"]).reset_index(drop=True)
        return str(ordered.iloc[len(ordered) // 2]["role"])
    if requested in set(drone_metrics["role"]):
        return requested
    if requested in set(drone_metrics["bag_name"]):
        return str(drone_metrics.loc[drone_metrics["bag_name"] == requested, "role"].iloc[0])
    raise ValueError(f"Unknown primary run selector: {requested}")


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    runs = build_run_specs(args)
    ensure_runs_exist(runs)

    eval_module = load_eval_module()

    metrics_rows: list[dict[str, object]] = []
    dataframes: dict[str, pd.DataFrame] = {}
    role_to_run: dict[str, RunSpec] = {}

    for run in runs:
        df = ensure_evaluation(
            run,
            eval_module=eval_module,
            force_eval=args.force_eval,
            args=args,
        )
        duration_s = parse_metadata_duration_seconds(run.bag_path / "metadata.yaml")
        world_init_x, world_init_y = resolve_world_init(run, args)
        dataframes[run.role] = df
        role_to_run[run.role] = run
        metrics_rows.append(build_metrics_row(run, df, duration_s, world_init_x, world_init_y))

    metrics_df = save_metrics_summary(metrics_rows, out_dir)
    drone_metrics = metrics_df[metrics_df["source"] == "sjtu_drone"].copy()
    primary_role = choose_primary_role(drone_metrics, args.primary_run)
    primary_df = dataframes[primary_role]
    primary_run = role_to_run[primary_role]

    temporal_df = compute_window_summary(primary_df, window_count=WINDOW_COUNT)
    temporal_df.insert(0, "role", primary_role)
    temporal_df.insert(1, "bag_name", primary_run.bag_name)
    temporal_df.to_csv(out_dir / "simulation_temporal_summary.csv", index=False)

    fixed_run = next(run for run in runs if run.source == "fixed_camera")
    plot_position_vs_gt(
        dataframes[fixed_run.role],
        "Posicion estimada vs ground truth en el caso base con camara fija",
        out_dir / "sim_fixed_position_vs_gt.png",
    )
    plot_fixed_error_hist(dataframes[fixed_run.role], out_dir / "sim_fixed_error_hist.png")

    plot_position_vs_gt(
        primary_df,
        f"Posicion estimada vs ground truth en la corrida principal del dron ({primary_run.display_label})",
        out_dir / "sim_drone_position_vs_gt.png",
    )
    plot_orientation_vs_gt(
        primary_df,
        f"Orientacion estimada vs ground truth en la corrida principal del dron ({primary_run.display_label})",
        out_dir / "sim_drone_orientation_vs_gt.png",
    )
    plot_drone_error_hist(primary_df, out_dir / "sim_drone_error_hist.png")
    plot_run_comparison(metrics_df, out_dir / "sim_drone_runs_comparison.png")
    plot_error_time(primary_df, temporal_df, out_dir / "sim_drone_error_time.png")

    print(f"Generated simulation artifacts in: {out_dir}")


if __name__ == "__main__":
    main()
