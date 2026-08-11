"""Recorta el clip de detección en simulación para que el marcador ocupe la caja.

El render de Gazebo sale en 800x600 y el 94% del cuadro es fondo gris plano: el
robot es del mismo gris que el piso y apenas se le adivinan las patas, así que
lo único que se lee es el marcador con la caja de detección y los ejes de pose.
Medido sobre todo el clip (56 cuadros a 3 fps), ese contenido nunca sale de
x[320,483] y[56,243], más las patas que bajan hasta y≈278: una ventana de
163x222 dentro de 800x600.

La ventana elegida es 220x260, medida sobre cuadros con grilla en cuatro
momentos del clip: el marcador con sus ejes vive en x[318,492] y, con las patas,
y[65,290]. Con ~20 px de margen queda centrado en todas las posiciones del
oleaje y el marcador pasa a ocupar el 70% del ancho, contra el 45% del recorte
anterior, que dejaba un tercio del cuadro muerto a la derecha.

El escalado a 550x650 no agrega detalle, pero hace el remuestreo una sola vez y
con lanczos, en vez de dejárselo al navegador.

Uso:
    python3 defensa/scripts/crop_sim_deteccion.py     # desde la raíz del repo
"""
import subprocess
import sys
from pathlib import Path

MEDIA = Path("defensa/web/assets/media")
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else MEDIA / "sim_01_camara_fija_deteccion.mp4"
DST = Path(sys.argv[2]) if len(sys.argv) > 2 else MEDIA / "sim_01_camara_fija_deteccion_zoom.mp4"

CROP = (220, 260, 296, 44)  # ancho, alto, x, y
OUT = (550, 650)

w, h, x, y = CROP
subprocess.run(
    [
        "ffmpeg", "-v", "error", "-y", "-i", str(SRC),
        "-vf", f"crop={w}:{h}:{x}:{y},scale={OUT[0]}:{OUT[1]}:flags=lanczos",
        "-an",
        "-c:v", "libx264", "-crf", "23", "-preset", "slow",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(DST),
    ],
    check=True,
)

print(f"{DST}  {OUT[0]}x{OUT[1]}  {DST.stat().st_size // 1024} KB")
