"""Recorta la captura de Gazebo del Go2 con la plataforma y el marcador montados.

La captura sale de Gazebo en 606x503 y el robot ocupa poco menos de la mitad del
ancho: el resto es piso y grilla. En la lámina va apareada con la foto del
laboratorio, donde el robot llena el cuadro, y con el original la pareja quedaba
despareja (el mismo robot se leía la mitad de grande de un lado que del otro).

Medido sobre la captura, el robot con la plataforma vive en x[178,466] y[183,373].
La ventana es 400x300, el 4:3 de la caja de la lámina para que no haya recorte
extra al mostrarla, centrada en ese contenido y con ~55 px de aire por lado.
Deja arriba un tramo del eje azul del mundo, que es lo que dice que es una
escena simulada y no una foto.

El escalado a 800x600 no agrega detalle (la ventana real son 400x300), pero hace
el remuestreo una sola vez y con lanczos en vez de dejárselo al navegador, que
la muestra a ~590 px de ancho a 1080p.

Uso:
    python3 defensa/scripts/crop_montaje_aruco_sim.py     # desde la raíz del repo
"""
import sys

from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else "docs/media/montaje_aruco_sim.png"
DST = sys.argv[2] if len(sys.argv) > 2 else "defensa/web/assets/img/sim_montaje_aruco.png"

BOX = (122, 128, 522, 428)  # left, top, right, bottom
OUT_W = 800

img = Image.open(SRC).convert("RGB").crop(BOX)
img = img.resize((OUT_W, round(img.height * OUT_W / img.width)), Image.LANCZOS)
img.save(DST, optimize=True)

print(f"{DST}  {img.width}x{img.height}")
