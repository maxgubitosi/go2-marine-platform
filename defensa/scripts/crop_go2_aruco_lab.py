"""Recorta la foto del Go2 con el marcador ArUco para la lámina que presenta el robot.

`lab_go2_aruco_tripode_a.jpg` viene del celular en vertical, pero guardado
apaisado con la rotación en el EXIF. Los navegadores la enderezan solos, así que
en la slide se veía bien, pero cualquier recorte hecho sobre los píxeles crudos
sale al revés: por eso lo primero es aplicar el EXIF y recién después cortar.

La foto entera trae media planta del laboratorio (un auto, las estanterías, el
otro cuadrúpedo sobre la colchoneta). Nada de eso es la lámina. La ventana se
queda con el robot y el marcador, más el piso justo para que se lea que es una
foto real y no un render, y corta antes del auto.
"""
import sys

from PIL import Image, ImageOps

SRC = sys.argv[1] if len(sys.argv) > 1 else "defensa/web/assets/img/lab_go2_aruco_tripode_a.jpg"
DST = sys.argv[2] if len(sys.argv) > 2 else "defensa/web/assets/img/lab_go2_aruco_crop.jpg"

BOX = (150, 880, 1120, 1600)  # left, top, right, bottom, sobre la imagen ya enderezada
OUT_W = 1000

img = ImageOps.exif_transpose(Image.open(SRC)).convert("RGB").crop(BOX)
img = img.resize((OUT_W, round(img.height * OUT_W / img.width)), Image.LANCZOS)
img.save(DST, quality=88, optimize=True)

print(f"{DST}  {img.width}x{img.height}")
