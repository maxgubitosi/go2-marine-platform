"""Recorta paneles de las figuras de error para que la letra se lea en el deck.

Las figuras originales traen grillas de paneles (2x2 el caso base, 2x3 el caso
con dron) y mostradas enteras a media lámina la letra de los ejes queda en ~6 px,
que es exactamente lo que los mentores marcaron en la devolución del 10-08.

En vez de regenerarlas (los rosbags no están en este checkout), se recortan los
paneles que sostienen lo que se dice en voz alta y se muestran a media lámina
cada uno, donde vuelven a escala legible. Las figuras completas siguen en el
backup de histogramas.

Como todos los scripts de recorte del deck: escribe archivos nuevos, nunca pisa
el original. Los cortes son los cuadrantes exactos de la grilla de matplotlib.

Uso:
    python3 defensa/scripts/crop_sim_error_panels.py    # desde la raíz
"""
import subprocess
from pathlib import Path

IMG = Path("defensa/web/assets/img")

# origen -> {destino: (w, h, x, y)}
CORTES = {
    # caso base, grilla 2x2 de 1782x1274: cuadrantes inferiores
    "sim_fixed_error_hist.png": {
        "sim_fixed_error_hist_dz.png":   (891, 637, 0,   637),
        "sim_fixed_error_hist_norm.png": (891, 637, 891, 637),
    },
    # caso dron, grilla 2x3 de 1998x1238: los dos angulares que la consigna
    # excita (fila inferior, columnas 1 y 2)
    "sim_drone_error_hist.png": {
        "sim_drone_error_hist_droll.png":  (666, 619, 0,   619),
        # 640 y no 666: el tercio exacto arrastra los números del eje y del
        # panel vecino por el borde derecho
        "sim_drone_error_hist_dpitch.png": (640, 619, 666, 619),
    },
}

for src, paneles in CORTES.items():
    for nombre, (w, h, x, y) in paneles.items():
        dst = IMG / nombre
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", str(IMG / src),
             "-vf", f"crop={w}:{h}:{x}:{y}", str(dst)],
            check=True)
        print(f"{dst}  {w}x{h}")
