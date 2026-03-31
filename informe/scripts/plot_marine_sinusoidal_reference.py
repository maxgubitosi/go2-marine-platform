#!/usr/bin/env python3
"""Genera la figura de señales sinusoidales de referencia del simulador marino.

Replica la lógica de `src/go2_tools/go2_tools/marine_platform_simulator.py`:
patrón `sinusoidal`, parámetros por defecto, y suavizado exponencial.

Uso:
  python3 informe/scripts/plot_marine_sinusoidal_reference.py
  python3 informe/scripts/plot_marine_sinusoidal_reference.py --out informe/figures/images/fig_method_motion_components.png
"""
from __future__ import annotations

import argparse
import math
import os
from pathlib import Path

# Cache de fuentes de Matplotlib dentro del repo (evita depender de ~/.matplotlib).
_mpl_cfg = Path(__file__).resolve().parent / ".mplconfig"
_mpl_cfg.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_mpl_cfg))

import numpy as np

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--out",
        type=Path,
        default=Path("informe/figures/images/fig_method_motion_components.png"),
    )
    p.add_argument("--duration", type=float, default=35.0, help="segundos")
    p.add_argument("--rate-hz", type=float, default=20.0)
    p.add_argument("--wave-frequency", type=float, default=0.1)
    p.add_argument("--max-roll-deg", type=float, default=15.0)
    p.add_argument("--max-pitch-deg", type=float, default=10.0)
    p.add_argument("--max-heave-m", type=float, default=0.1)
    p.add_argument("--phase-offset-pitch", type=float, default=1.0)
    p.add_argument("--phase-offset-heave", type=float, default=1.5)
    p.add_argument("--smoothing-factor", type=float, default=0.95)
    args = p.parse_args()

    wave_frequency = args.wave_frequency
    max_roll_deg = args.max_roll_deg
    max_pitch_deg = args.max_pitch_deg
    max_heave_m = args.max_heave_m
    phase_offset_pitch = args.phase_offset_pitch
    phase_offset_heave = args.phase_offset_heave
    smoothing_factor = args.smoothing_factor

    omega = 2 * math.pi * wave_frequency
    dt = 1.0 / args.rate_hz
    n = int(args.duration / dt)
    t = np.arange(n, dtype=np.float64) * dt

    roll_t = max_roll_deg * np.sin(omega * t)
    pitch_t = max_pitch_deg * np.sin(omega * t * phase_offset_pitch + math.pi / 3.0)
    heave_t = max_heave_m * np.sin(omega * t * phase_offset_heave)

    alpha = smoothing_factor
    def smooth_1d(target: np.ndarray) -> np.ndarray:
        out = np.zeros_like(target)
        s = 0.0
        for i in range(len(target)):
            s = alpha * s + (1.0 - alpha) * float(target[i])
            out[i] = s
        return out

    roll_s = smooth_1d(roll_t)
    pitch_s = smooth_1d(pitch_t)
    heave_s = smooth_1d(heave_t)

    fig, axes = plt.subplots(3, 1, figsize=(10.0, 7.5), sharex=True)
    _labelpad_y = 12
    _labelpad_x = 10

    def plot_pair(ax, t_arr, raw, sm, ylabel: str, unit: str) -> None:
        ax.plot(t_arr, raw, color="#888888", linestyle="--", linewidth=1.2, label="Objetivo (sin suavizar)")
        ax.plot(t_arr, sm, color="#1f77b4", linestyle="-", linewidth=1.4, label="Tras suavizado (publicado)")
        ax.set_ylabel(f"{ylabel} [{unit}]", labelpad=_labelpad_y)
        ax.tick_params(axis="y", pad=6)
        ax.grid(True, alpha=0.35)
        ax.legend(loc="upper right", fontsize=8)

    plot_pair(axes[0], t, roll_t, roll_s, "Roll", "°")
    plot_pair(axes[1], t, pitch_t, pitch_s, "Pitch", "°")
    plot_pair(axes[2], t, heave_t, heave_s, "Heave", "m")
    axes[2].set_xlabel("Tiempo [s]", labelpad=_labelpad_x)
    axes[2].tick_params(axis="x", pad=6)

    fig.subplots_adjust(
        left=0.12,
        right=0.98,
        top=0.91,
        bottom=0.12,
        hspace=0.42,
    )
    fig.suptitle("Consigna marinas de referencia (simulador)", fontsize=11, y=0.97)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=160, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    print(f"Saved {args.out}")


if __name__ == "__main__":
    main()
