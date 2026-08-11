"""Recorta dos paneles del histograma de error del caso base, para el deck.

La figura original (sim_fixed_error_hist.png, 1782x1274) trae los cuatro paneles
en una grilla de 2x2. Mostrada entera en media lámina, la letra de los ejes
queda en ~6 px y no se lee ni de cerca, que es exactamente lo que los mentores
marcaron en la devolución del 10-08.

En vez de regenerarla (los rosbags no están en este checkout), se recortan los
dos paneles que sostienen lo que se dice en voz alta: ΔZ (el heave concentra la
dispersión) y ||Δpos|| (5,8 cm de media, 8,5 de P95). Mostrados a media lámina
cada uno quedan al 65% de su escala nativa y la letra vuelve a leerse. La
figura completa con los cuatro ejes sigue en el backup de histogramas.

Como todos los scripts de recorte del deck: escribe archivos nuevos, nunca pisa
el original. Los cortes son los cuadrantes exactos de la grilla de matplotlib.

Uso:
    python3 defensa/scripts/crop_sim_error_panels.py    # desde la raíz
"""
import subprocess
from pathlib import Path

IMG = Path("defensa/web/assets/img")
SRC = IMG / "sim_fixed_error_hist.png"

# panel -> (w, h, x, y): cuadrantes inferiores de la grilla 2x2 de 1782x1274
PANELES = {
    "sim_fixed_error_hist_dz.png":   (891, 637, 0,   637),
    "sim_fixed_error_hist_norm.png": (891, 637, 891, 637),
}

for nombre, (w, h, x, y) in PANELES.items():
    dst = IMG / nombre
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(SRC),
         "-vf", f"crop={w}:{h}:{x}:{y}", str(dst)],
        check=True)
    print(f"{dst}  {w}x{h}")
