#!/usr/bin/env python3
"""Grafica la consigna marina antes y despues del suavizado, para la lamina 10.

Existe una figura equivalente en el informe
(`informe/scripts/plot_marine_sinusoidal_reference.py`) y no se la reusa a
proposito: esa esta dimensionada para una pagina, donde se lee a 20 cm de los
ojos. Proyectada en un aula sale con los rotulos en dos o tres puntos.

La diferencia esta en la relacion entre el ancho del dibujo y el cuerpo de
letra. La figura ocupa unos 583 px en la lamina y se genera a 1400, o sea que
se muestra al 42 %: para que un rotulo se lea al piso tipografico del deck
(18,5 px) tiene que salir de aca a 44 px, que a 160 dpi son 20 pt. De ahi los
cuerpos grandes, que en pantalla parecen desproporcionados y proyectados no.

La figura es ancha y baja (2,2:1) porque en la lamina lo que escasea es el alto:
la columna da 583 px de ancho y unos 265 de alto. Con la proporcion de la figura
del informe habria que achicarla hasta 476 px de ancho y sobraria columna.

El modelo es el del nodo (`marine_platform_simulator.py`), con sus valores por
defecto: misma consigna y mismo filtro, para que la figura no pueda desmentir a
las ecuaciones de la lamina.

Lo que la figura tiene que dejar ver, y por eso los tres paneles y no uno:
  - la amplitud que pierde cada eje (85 % en roll y pitch, 74 % en heave);
  - que heave pierde mas por ir mas rapido, no por tener otro filtro;
  - el atraso de casi un segundo, que en un solo panel se ve pero no se compara.
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

# Paleta del deck (css/style.css)
INK = "#0f2a43"
INK_SOFT = "#4a6480"
INK_FAINT = "#8aa0b4"
SEA = "#0e6e8c"
LINE = "#cfdce4"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path,
                   default=Path("defensa/web/assets/img/method_consigna_suavizado.png"))
    p.add_argument("--duration", type=float, default=30.0)
    p.add_argument("--rate-hz", type=float, default=20.0)
    p.add_argument("--wave-frequency", type=float, default=0.1)
    p.add_argument("--max-roll-deg", type=float, default=15.0)
    p.add_argument("--max-pitch-deg", type=float, default=10.0)
    p.add_argument("--max-heave-m", type=float, default=0.1)
    p.add_argument("--rho-pitch", type=float, default=1.0)
    p.add_argument("--rho-heave", type=float, default=1.5)
    p.add_argument("--alpha", type=float, default=0.95)
    args = p.parse_args()

    omega = 2 * math.pi * args.wave_frequency
    dt = 1.0 / args.rate_hz
    t = np.arange(int(args.duration / dt), dtype=np.float64) * dt

    objetivo = {
        "roll": (args.max_roll_deg * np.sin(omega * t), "roll [°]"),
        "pitch": (args.max_pitch_deg * np.sin(omega * t * args.rho_pitch + math.pi / 3.0), "pitch [°]"),
        "heave": (args.max_heave_m * np.sin(omega * t * args.rho_heave), "heave [m]"),
    }

    def suavizar(x: np.ndarray) -> np.ndarray:
        y = np.empty_like(x)
        s = 0.0
        for i, v in enumerate(x):
            s = args.alpha * s + (1.0 - args.alpha) * float(v)
            y[i] = s
        return y

    CUERPO = 20  # pt a 160 dpi = 44 px; ver el docstring
    # Los ticks de Y van más chicos que el cuerpo: son tres etiquetas apiladas
    # en paneles de ~150 px y a 20 pt quedaban rozándose (corrección 15-08).
    TICKS_Y = 16
    plt.rcParams.update({
        "font.size": CUERPO,
        "axes.labelsize": CUERPO,
        "xtick.labelsize": CUERPO,
        "ytick.labelsize": TICKS_Y,
        "legend.fontsize": CUERPO,
        "axes.edgecolor": LINE,
        "axes.labelcolor": INK_SOFT,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "text.color": INK,
        "figure.facecolor": "none",
        "axes.facecolor": "none",
    })

    fig, axes = plt.subplots(3, 1, figsize=(8.75, 4.25), sharex=True)
    for ax, (nombre, (crudo, etiqueta)) in zip(axes, objetivo.items()):
        ax.plot(t, crudo, color=INK_FAINT, linestyle="--", linewidth=2.2, label="consigna")
        ax.plot(t, suavizar(crudo), color=SEA, linewidth=3.0, label="tras el filtro")
        # Horizontal y no rotado: con paneles bajos, tres rotulos verticales de
        # nueve caracteres se pisan entre si.
        ax.set_ylabel(etiqueta, rotation=0, ha="right", va="center", labelpad=14)
        ax.grid(True, color=LINE, alpha=0.7, linewidth=1.0)
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)
    axes[2].set_xlabel("tiempo [s]")

    fig.tight_layout(pad=0.3, h_pad=0.9, rect=(0, 0, 1, 0.88))
    # La leyenda va arriba de todo y no adentro de un panel: metida en el de
    # roll obligaba a estirarle el eje para no pisar la curva, y ese panel
    # terminaba con una escala distinta de la que le corresponde.
    manijas, rotulos = axes[0].get_legend_handles_labels()
    fig.legend(manijas, rotulos, loc="upper center", ncol=2, frameon=False,
               handlelength=1.8, columnspacing=2.0, bbox_to_anchor=(0.55, 1.0))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=160, transparent=True,
                bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)

    from PIL import Image
    im = Image.open(args.out)
    print(f"{args.out}  {im.width}x{im.height}  ({im.width / im.height:.3f})")


if __name__ == "__main__":
    main()
