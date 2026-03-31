#!/usr/bin/env python3
"""Compara los patrones `sinusoidal` e `irregular` del marine_platform_simulator.

Replica `generate_wave_motion` en `src/go2_tools/go2_tools/marine_platform_simulator.py`
(sin suavizado: solo la consigna objetivo generada por cada modo).

Uso:
  python3 informe/scripts/plot_marine_wave_patterns_compare.py
"""
from __future__ import annotations

import argparse
import math
import os
from pathlib import Path

_mpl_cfg = Path(__file__).resolve().parent / ".mplconfig"
_mpl_cfg.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_mpl_cfg))

import numpy as np

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def sinusoidal(t: np.ndarray, omega: float, max_r: float, max_p: float, max_h: float, kp: float, kh: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    roll = max_r * np.sin(omega * t)
    pitch = max_p * np.sin(omega * t * kp + math.pi / 3.0)
    heave = max_h * np.sin(omega * t * kh)
    return roll, pitch, heave


def irregular(t: np.ndarray, omega: float, max_r: float, max_p: float, max_h: float, kp: float, kh: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    roll = (
        max_r * 0.6 * np.sin(omega * t)
        + max_r * 0.3 * np.sin(omega * t * 1.3 + math.pi / 4.0)
        + max_r * 0.1 * np.sin(omega * t * 2.1 + math.pi / 2.0)
    )
    pitch = (
        max_p * 0.7 * np.sin(omega * t * kp + math.pi / 3.0)
        + max_p * 0.2 * np.sin(omega * t * 0.8 + math.pi)
        + max_p * 0.1 * np.sin(omega * t * 1.7)
    )
    heave = (
        max_h * 0.8 * np.sin(omega * t * kh)
        + max_h * 0.2 * np.sin(omega * t * 1.4 + math.pi / 6.0)
    )
    return roll, pitch, heave


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, default=Path("informe/figures/images/fig_method_wave_patterns.png"))
    p.add_argument("--duration", type=float, default=35.0)
    p.add_argument("--wave-frequency", type=float, default=0.1)
    p.add_argument("--max-roll-deg", type=float, default=15.0)
    p.add_argument("--max-pitch-deg", type=float, default=10.0)
    p.add_argument("--max-heave-m", type=float, default=0.1)
    p.add_argument("--phase-offset-pitch", type=float, default=1.0)
    p.add_argument("--phase-offset-heave", type=float, default=1.5)
    args = p.parse_args()

    omega = 2 * math.pi * args.wave_frequency
    dt = 0.05
    n = int(args.duration / dt)
    t = np.arange(n, dtype=np.float64) * dt

    rs, ps, hs = sinusoidal(
        t, omega, args.max_roll_deg, args.max_pitch_deg, args.max_heave_m, args.phase_offset_pitch, args.phase_offset_heave
    )
    ri, pi, hi = irregular(
        t, omega, args.max_roll_deg, args.max_pitch_deg, args.max_heave_m, args.phase_offset_pitch, args.phase_offset_heave
    )

    fig, axes = plt.subplots(3, 1, figsize=(10.0, 7.2), sharex=True)
    _labelpad_y = 12
    _labelpad_x = 10

    def plot_cmp(ax, y_s: np.ndarray, y_i: np.ndarray, ylab: str, unit: str) -> None:
        ax.plot(t, y_s, color="#1f77b4", linestyle="-", linewidth=1.3, label="sinusoidal")
        ax.plot(t, y_i, color="#ff7f0e", linestyle="-", linewidth=1.2, label="irregular")
        ax.set_ylabel(f"{ylab} [{unit}]", labelpad=_labelpad_y)
        ax.tick_params(axis="y", pad=6)
        ax.grid(True, alpha=0.35)
        ax.legend(loc="upper right", fontsize=8)

    plot_cmp(axes[0], rs, ri, "Roll", "°")
    plot_cmp(axes[1], ps, pi, "Pitch", "°")
    plot_cmp(axes[2], hs, hi, "Heave", "m")
    axes[2].set_xlabel("Tiempo [s]", labelpad=_labelpad_x)
    axes[2].tick_params(axis="x", pad=6)

    fig.subplots_adjust(
        left=0.12,
        right=0.98,
        top=0.89,
        bottom=0.12,
        hspace=0.42,
    )
    fig.suptitle(
        "Consigna objetivo: patrón sinusoidal vs irregular (sin filtro de suavizado)",
        fontsize=11,
        y=0.97,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=160, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    print(f"Saved {args.out}")


if __name__ == "__main__":
    main()
