"""Recorta la captura de Gazebo para dejar solo el visor 3D.

`docs/media/gazebo_go2.png` (1920x1048) es una captura de pantalla completa:
trae la barra de menú, el árbol de modelos a la izquierda y la barra de estado
abajo. En una slide todo ese chrome distrae y además delata que es una captura
de pantalla en vez de leerse como "la escena simulada".

La ventana elegida encuadra al robot dejando algo de grilla alrededor (la grilla
es lo que hace que se lea como simulación y no como foto).
"""
import sys

from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else "docs/media/gazebo_go2.png"
DST = sys.argv[2] if len(sys.argv) > 2 else "defensa/web/assets/img/sim_gazebo_go2.png"

BOX = (400, 115, 1600, 865)  # left, top, right, bottom
OUT_W = 1000

img = Image.open(SRC).convert("RGB").crop(BOX)
img = img.resize((OUT_W, round(img.height * OUT_W / img.width)), Image.LANCZOS)
img.save(DST, optimize=True)

print(f"{DST}  {img.width}x{img.height}")
