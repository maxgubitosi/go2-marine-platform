"""Recorta la foto del montaje del laboratorio para la lámina de los tres montajes.

La foto sale del celular en vertical, 960x1280. Entera trae casi 300 px de piso
vacío por debajo del robot y, a los costados, medio taller: las estanterías de la
izquierda y la mesa blanca de la derecha. La lámina necesita dos cosas, la cámara
arriba del trípode y el robot con el marcador abajo, así que la ventana se cierra
sobre esas dos y deja apenas el piso suficiente para que se lea como foto real.

La relación de aspecto se mantiene en 3:4 a propósito: la lámina pone las tres
figuras al mismo alto y deriva el ancho de la proporción, así que cambiarla acá
descuadra la fila entera. Ver `.serie.cols.montajes` en css/style.css.

Referencias sobre la imagen ya enderezada por EXIF:
  cámara del trípode   x 440-500   y 105-135
  mástil               x 455       y 135-790
  robot con el ArUco   x 285-680   y 815-985
  piso vacío                       y 985-1280
"""
import sys

from PIL import Image, ImageOps

SRC = sys.argv[1] if len(sys.argv) > 1 else "defensa/web/assets/img/lab_montaje_camara_raw.jpg"
DST = sys.argv[2] if len(sys.argv) > 2 else "defensa/web/assets/img/lab_montaje_camara.jpg"

# left, top, right, bottom · 720x960, que es 3:4 exacto
BOX = (118, 70, 838, 1030)

img = ImageOps.exif_transpose(Image.open(SRC)).convert("RGB").crop(BOX)
assert abs(img.width / img.height - 0.75) < 1e-3, f"la ventana no es 3:4: {img.size}"
img.save(DST, quality=88, optimize=True)

print(f"{DST}  {img.width}x{img.height}  ({img.width / img.height:.3f})")
