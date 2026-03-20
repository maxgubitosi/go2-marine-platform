#!/usr/bin/env python3
import argparse
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message


def quat_to_rpy(x, y, z, w):
    t0 = 2.0 * (w * x + y * z)
    t1 = 1.0 - 2.0 * (x * x + y * y)
    roll = math.atan2(t0, t1)
    t2 = 2.0 * (w * y - z * x)
    t2 = 1.0 if t2 > 1.0 else t2
    t2 = -1.0 if t2 < -1.0 else t2
    pitch = math.asin(t2)
    t3 = 2.0 * (w * z + x * y)
    t4 = 1.0 - 2.0 * (y * y + z * z)
    yaw = math.atan2(t3, t4)
    return roll, pitch, yaw


def corr(a, b):
    a = np.asarray(a)
    b = np.asarray(b)
    if len(a) < 3 or len(b) < 3:
        return np.nan
    if np.std(a) < 1e-12 or np.std(b) < 1e-12:
        return np.nan
    return float(np.corrcoef(a, b)[0, 1])


def nearest_indices(src_t, dst_t):
    src_t = np.asarray(src_t)
    dst_t = np.asarray(dst_t)
    idx = np.searchsorted(dst_t, src_t)
    idx = np.clip(idx, 1, len(dst_t) - 1)
    left = idx - 1
    right = idx
    return np.where(np.abs(dst_t[left] - src_t) <= np.abs(dst_t[right] - src_t), left, right)


def lag_curve(cmd_t, cmd_v, real_t, real_v, lag_min=-3.0, lag_max=3.0, step=0.05):
    cmd_t = np.asarray(cmd_t)
    cmd_v = np.asarray(cmd_v)
    real_t = np.asarray(real_t)
    real_v = np.asarray(real_v)
    lags = np.arange(lag_min, lag_max + 1e-9, step)
    corrs = []
    for lag in lags:
        shifted = cmd_t + lag
        lo = max(shifted.min(), real_t.min())
        hi = min(shifted.max(), real_t.max())
        mask = (shifted >= lo) & (shifted <= hi)
        if mask.sum() < 30:
            corrs.append(np.nan)
            continue
        sample_real = np.interp(shifted[mask], real_t, real_v)
        corrs.append(corr(cmd_v[mask], sample_real))
    return lags, np.array(corrs)


def extract_data(bag_dir: Path):
    reader = rosbag2_py.SequentialReader()
    reader.open(
        rosbag2_py.StorageOptions(uri=str(bag_dir), storage_id="sqlite3"),
        rosbag2_py.ConverterOptions(input_serialization_format="cdr", output_serialization_format="cdr"),
    )

    topic_types = {item.name: item.type for item in reader.get_all_topics_and_types()}
    msg_cls = {name: get_message(type_name) for name, type_name in topic_types.items()}

    targets = {
        "/marine_platform/debug_state",
        "/api/sport/request",
        "/sportmodestate",
        "/lowstate",
        "/utlidar/robot_odom",
    }

    data = {
        "debug_t": [],
        "debug_roll": [],
        "debug_pitch": [],
        "debug_z": [],
        "api_t": [],
        "api_x": [],
        "api_y": [],
        "api_z": [],
        "sport_t": [],
        "sport_roll": [],
        "sport_pitch": [],
        "sport_z": [],
        "foot_fl_z_body": [],
        "foot_fr_z_body": [],
        "foot_rl_z_body": [],
        "foot_rr_z_body": [],
        "low_t": [],
        "low_roll": [],
        "low_pitch": [],
        "odom_t": [],
        "odom_roll": [],
        "odom_pitch": [],
        "odom_z": [],
        "gait": [],
    }

    while reader.has_next():
        topic, raw, stamp = reader.read_next()
        if topic not in targets:
            continue
        if topic not in msg_cls:
            continue
        try:
            msg = deserialize_message(raw, msg_cls[topic])
        except Exception:
            continue

        t = stamp * 1e-9
        if topic == "/marine_platform/debug_state":
            data["debug_t"].append(t)
            data["debug_roll"].append(float(msg.x))
            data["debug_pitch"].append(float(msg.y))
            data["debug_z"].append(float(msg.z))
        elif topic == "/api/sport/request":
            if int(msg.header.identity.api_id) != 1007:
                continue
            try:
                p = json.loads(msg.parameter)
            except Exception:
                continue
            data["api_t"].append(t)
            data["api_x"].append(float(p.get("x", np.nan)))
            data["api_y"].append(float(p.get("y", np.nan)))
            data["api_z"].append(float(p.get("z", np.nan)))
        elif topic == "/sportmodestate":
            data["sport_t"].append(t)
            data["sport_roll"].append(float(msg.imu_state.rpy[0]) * 180.0 / math.pi)
            data["sport_pitch"].append(float(msg.imu_state.rpy[1]) * 180.0 / math.pi)
            data["sport_z"].append(float(msg.position[2]))
            fp = np.array(msg.foot_position_body, dtype=float)
            if fp.size >= 12:
                data["foot_fl_z_body"].append(float(fp[2]))
                data["foot_fr_z_body"].append(float(fp[5]))
                data["foot_rl_z_body"].append(float(fp[8]))
                data["foot_rr_z_body"].append(float(fp[11]))
            data["gait"].append(int(msg.gait_type))
        elif topic == "/lowstate":
            data["low_t"].append(t)
            data["low_roll"].append(float(msg.imu_state.rpy[0]) * 180.0 / math.pi)
            data["low_pitch"].append(float(msg.imu_state.rpy[1]) * 180.0 / math.pi)
        elif topic == "/utlidar/robot_odom":
            q = msg.pose.pose.orientation
            roll, pitch, _ = quat_to_rpy(q.x, q.y, q.z, q.w)
            data["odom_t"].append(t)
            data["odom_roll"].append(roll * 180.0 / math.pi)
            data["odom_pitch"].append(pitch * 180.0 / math.pi)
            data["odom_z"].append(float(msg.pose.pose.position.z))

    for k, v in data.items():
        data[k] = np.array(v, dtype=float)
    return data


def save_plot_1_timeseries(data, out_dir: Path):
    t0 = data["debug_t"][0]
    td = data["debug_t"] - t0
    ts = data["sport_t"] - t0

    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    axes[0].plot(td, data["debug_roll"], label="cmd roll (debug)", linewidth=2)
    axes[0].plot(ts, data["sport_roll"], label="real roll (sport)", alpha=0.8)
    axes[0].set_ylabel("Roll [deg]")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    axes[1].plot(td, data["debug_pitch"], label="cmd pitch (debug)", linewidth=2)
    axes[1].plot(ts, data["sport_pitch"], label="real pitch (sport)", alpha=0.8)
    axes[1].set_ylabel("Pitch [deg]")
    axes[1].set_xlabel("Time [s]")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()

    fig.suptitle("Comando vs movimiento real (SportModeState)")
    fig.tight_layout()
    fig.savefig(out_dir / "plot_01_timeseries_cmd_vs_real.png", dpi=160)
    plt.close(fig)


def save_plot_2_api_fidelity(data, out_dir: Path):
    idx = nearest_indices(data["debug_t"], data["api_t"])
    cmd_roll_rad = np.deg2rad(data["debug_roll"])
    cmd_pitch_rad = np.deg2rad(data["debug_pitch"])
    api_x = data["api_x"][idx]
    api_y = data["api_y"][idx]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].scatter(cmd_roll_rad, api_x, s=18, alpha=0.7)
    mn = min(cmd_roll_rad.min(), api_x.min())
    mx = max(cmd_roll_rad.max(), api_x.max())
    axes[0].plot([mn, mx], [mn, mx], "r--", linewidth=1)
    axes[0].set_title(f"x vs roll(rad), corr={corr(cmd_roll_rad, api_x):.4f}")
    axes[0].set_xlabel("roll esperado [rad]")
    axes[0].set_ylabel("x API [rad]")
    axes[0].grid(True, alpha=0.3)

    axes[1].scatter(cmd_pitch_rad, api_y, s=18, alpha=0.7)
    mn = min(cmd_pitch_rad.min(), api_y.min())
    mx = max(cmd_pitch_rad.max(), api_y.max())
    axes[1].plot([mn, mx], [mn, mx], "r--", linewidth=1)
    axes[1].set_title(f"y vs pitch(rad), corr={corr(cmd_pitch_rad, api_y):.4f}")
    axes[1].set_xlabel("pitch esperado [rad]")
    axes[1].set_ylabel("y API [rad]")
    axes[1].grid(True, alpha=0.3)

    fig.suptitle("Fidelidad comando debug → /api/sport/request")
    fig.tight_layout()
    fig.savefig(out_dir / "plot_02_api_fidelity.png", dpi=160)
    plt.close(fig)


def save_plot_3_lag(data, out_dir: Path):
    lags_roll, c_roll = lag_curve(data["debug_t"], data["debug_roll"], data["sport_t"], data["sport_roll"])
    lags_pitch, c_pitch = lag_curve(data["debug_t"], data["debug_pitch"], data["sport_t"], data["sport_pitch"])

    best_r = np.nanargmax(np.abs(c_roll))
    best_p = np.nanargmax(np.abs(c_pitch))

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(lags_roll, c_roll, label=f"roll (best lag={lags_roll[best_r]:.2f}s, corr={c_roll[best_r]:.3f})")
    ax.plot(lags_pitch, c_pitch, label=f"pitch (best lag={lags_pitch[best_p]:.2f}s, corr={c_pitch[best_p]:.3f})")
    ax.axvline(0.0, color="k", linestyle="--", linewidth=1)
    ax.set_xlabel("Lag aplicado a comando [s]")
    ax.set_ylabel("Correlación")
    ax.set_title("Curva de correlación comando-real vs lag")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "plot_03_lag_correlation.png", dpi=160)
    plt.close(fig)


def save_plot_4_gait(data, out_dir: Path):
    gait = data["gait"].astype(int)
    vals, counts = np.unique(gait, return_counts=True)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(vals.astype(str), counts)
    ax.set_xlabel("gait_type")
    ax.set_ylabel("Muestras")
    ax.set_title("Distribución gait_type en /sportmodestate")
    ax.grid(True, alpha=0.25, axis="y")
    fig.tight_layout()
    fig.savefig(out_dir / "plot_04_gait_distribution.png", dpi=160)
    plt.close(fig)


def save_plot_5_heave(data, out_dir: Path):
    t0 = data["debug_t"][0]
    td = data["debug_t"] - t0
    ts = data["sport_t"] - t0
    to = data["odom_t"] - t0

    idx_api = nearest_indices(data["debug_t"], data["api_t"])
    api_z_sync = data["api_z"][idx_api]
    sport_z_sync = np.interp(data["debug_t"], data["sport_t"], data["sport_z"])
    odom_z_sync = np.interp(data["debug_t"], data["odom_t"], data["odom_z"])

    # z_cmd = 0 representa altura nominal, no altura absoluta 0 m del tronco.
    # Tomamos referencia de altura nominal como mediana de los primeros 5 s.
    init_mask_s = ts <= 5.0
    init_mask_o = to <= 5.0
    z_ref_sport = float(np.median(data["sport_z"][init_mask_s])) if np.any(init_mask_s) else float(np.median(data["sport_z"]))
    z_ref_odom = float(np.median(data["odom_z"][init_mask_o])) if np.any(init_mask_o) else float(np.median(data["odom_z"]))

    sport_dz = data["sport_z"] - z_ref_sport
    odom_dz = data["odom_z"] - z_ref_odom
    sport_dz_sync = np.interp(data["debug_t"], data["sport_t"], sport_dz)
    odom_dz_sync = np.interp(data["debug_t"], data["odom_t"], odom_dz)

    rmse_sport_dyn = np.sqrt(np.mean((sport_dz_sync - data["debug_z"]) ** 2))
    rmse_odom_dyn = np.sqrt(np.mean((odom_dz_sync - data["debug_z"]) ** 2))

    # Suavizado liviano para leer tendencia dinámica en mm
    def smooth(y, win=151):
        y = np.asarray(y)
        if len(y) < win:
            return y
        kernel = np.ones(win) / win
        return np.convolve(y, kernel, mode="same")

    cmd_z_mm = data["debug_z"] * 1000.0
    api_z_mm = api_z_sync * 1000.0
    sport_dz_mm = sport_dz * 1000.0
    odom_dz_mm = odom_dz * 1000.0

    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    axes[0].plot(td, cmd_z_mm, label="z esperado (debug)", linewidth=2)
    axes[0].plot(td, api_z_mm, label="z enviado API", alpha=0.85)
    axes[0].set_ylabel("z comando [mm]")
    axes[0].set_ylim(-1.0, 1.0)
    axes[0].set_title("Comando de heave (este ensayo: 0 mm)")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    axes[1].plot(ts, data["sport_z"], label="z real sport.position[2]", alpha=0.85)
    axes[1].plot(to, data["odom_z"], label="z real odom.pose.position.z", alpha=0.85)
    axes[1].axhline(z_ref_sport, linestyle="--", linewidth=1.5, label=f"z ref sport={z_ref_sport:.4f} m")
    axes[1].axhline(z_ref_odom, linestyle=":", linewidth=1.5, label=f"z ref odom={z_ref_odom:.4f} m")
    axes[1].set_ylabel("z real [m]")
    axes[1].set_title("Heave real absoluto del tronco (base_link)")
    zmin = float(min(np.min(data["sport_z"]), np.min(data["odom_z"])))
    zmax = float(max(np.max(data["sport_z"]), np.max(data["odom_z"])))
    pad = max(0.0005, 0.1 * (zmax - zmin))
    axes[1].set_ylim(zmin - pad, zmax + pad)
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()

    axes[2].plot(ts, sport_dz_mm, label="Δz tronco sport", alpha=0.35)
    axes[2].plot(to, odom_dz_mm, label="Δz tronco odom", alpha=0.35)
    axes[2].plot(ts, smooth(sport_dz_mm), linewidth=2.0, label="Δz sport suavizado")
    axes[2].plot(to, smooth(odom_dz_mm), linewidth=2.0, label="Δz odom suavizado")
    axes[2].plot(td, cmd_z_mm, "--", linewidth=1.5, label="Δz esperado")
    axes[2].axhline(0.0, color="k", linestyle=":", linewidth=1.0)
    axes[2].set_ylabel("Δz [mm]")
    axes[2].set_title(
        f"Dinámica heave del tronco (sin offset) | RMSE dyn sport={rmse_sport_dyn*1000:.2f} mm, odom={rmse_odom_dyn*1000:.2f} mm"
    )
    axes[2].grid(True, alpha=0.3)
    axes[2].legend(ncol=2, fontsize=9)
    axes[2].set_xlabel("Time [s]")

    fig.suptitle("Comparación de Heave/Z")
    fig.tight_layout()
    fig.savefig(out_dir / "plot_05_heave_z_comparison.png", dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("bag_dir", help="Ruta a carpeta del bag")
    parser.add_argument("--out-dir", default=None, help="Carpeta salida PNG (default: bag_dir)")
    args = parser.parse_args()

    bag_dir = Path(args.bag_dir).resolve()
    out_dir = Path(args.out_dir).resolve() if args.out_dir else bag_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    data = extract_data(bag_dir)

    required = ["debug_t", "api_t", "sport_t"]
    for k in required:
        if len(data[k]) == 0:
            raise RuntimeError(f"Falta señal requerida para graficar: {k}")

    save_plot_1_timeseries(data, out_dir)
    save_plot_2_api_fidelity(data, out_dir)
    save_plot_3_lag(data, out_dir)
    save_plot_5_heave(data, out_dir)
    if len(data["gait"]) > 0:
        save_plot_4_gait(data, out_dir)

    print("Gráficos generados en:", out_dir)
    print(" - plot_01_timeseries_cmd_vs_real.png")
    print(" - plot_02_api_fidelity.png")
    print(" - plot_03_lag_correlation.png")
    print(" - plot_05_heave_z_comparison.png")
    if len(data["gait"]) > 0:
        print(" - plot_04_gait_distribution.png")


if __name__ == "__main__":
    main()
