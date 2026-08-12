"""Recorta los clips de detección en simulación para que el marcador ocupe la caja.

Los renders de Gazebo salen con el 90% del cuadro en fondo gris plano: el robot
es del mismo gris que el piso y apenas se le adivinan las patas, así que lo
único que se lee es el marcador con la caja de detección y los ejes de pose.
Cada ventana está medida muestreando cuadros a lo largo de todo el clip:

- cámara fija (800x600, 56 cuadros a 3 fps): el contenido nunca sale de
  x[320,483] y[56,243], más las patas hasta y≈278. Ventana 220x260 con ~20 px
  de margen: el marcador pasa a ocupar el 70% del ancho.
- dron (1066x600, ~290 cuadros a 15 fps): el marcador con sus ejes oscila en
  x[420,695] y[130,345]. Ventana 400x340 con ~30 px de margen para el oleaje:
  el marcador pasa del 16% al 44% del ancho.

El escalado a 2x no agrega detalle, pero hace el remuestreo una sola vez y con
lanczos, en vez de dejárselo al navegador.

Como todos los scripts de recorte del deck: escribe archivos nuevos, nunca pisa
el original.

Uso:
    python3 defensa/scripts/crop_sim_deteccion.py     # desde la raíz del repo
"""
import subprocess
from pathlib import Path

MEDIA = Path("defensa/web/assets/media")

# origen -> (destino, (ancho, alto, x, y), (ancho_out, alto_out))
CLIPS = {
    "sim_01_camara_fija_deteccion.mp4": (
        "sim_01_camara_fija_deteccion_zoom.mp4", (220, 260, 296, 44), (550, 650)),
    "sim_02_dron_deteccion.mp4": (
        "sim_02_dron_deteccion_zoom.mp4", (400, 340, 370, 85), (800, 680)),
}

for src, (dst, (w, h, x, y), out) in CLIPS.items():
    dst = MEDIA / dst
    subprocess.run(
        [
            "ffmpeg", "-v", "error", "-y", "-i", str(MEDIA / src),
            "-vf", f"crop={w}:{h}:{x}:{y},scale={out[0]}:{out[1]}:flags=lanczos",
            "-an",
            "-c:v", "libx264", "-crf", "23", "-preset", "slow",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(dst),
        ],
        check=True,
    )
    print(f"{dst}  {out[0]}x{out[1]}  {dst.stat().st_size // 1024} KB")
