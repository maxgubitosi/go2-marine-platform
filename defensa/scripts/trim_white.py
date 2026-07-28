"""Recorta el margen blanco de una imagen sobre fondo claro.

Varios renders del informe vienen con mucho aire blanco alrededor. Sobre el
fondo claro del deck ese aire no se ve como margen sino como una caja vacía,
y obliga a agrandar la imagen para que el contenido se lea.

Busca el recuadro de pixeles que se apartan del blanco más que TOL y deja un
borde de PAD px para que el recorte no quede pegado al contenido.
"""
import sys

import numpy as np
from PIL import Image

SRC, DST = sys.argv[1], sys.argv[2]
TOL = int(sys.argv[3]) if len(sys.argv) > 3 else 12
PAD = int(sys.argv[4]) if len(sys.argv) > 4 else 8

img = Image.open(SRC).convert("RGB")
a = np.asarray(img).astype(np.int16)

ink = (255 - a).max(axis=2) > TOL
rows, cols = np.where(ink)
if rows.size == 0:
    raise SystemExit(f"{SRC}: todo el cuadro es blanco, no hay nada que recortar")

top = max(0, rows.min() - PAD)
bottom = min(img.height, rows.max() + 1 + PAD)
left = max(0, cols.min() - PAD)
right = min(img.width, cols.max() + 1 + PAD)

out = img.crop((left, top, right, bottom))
out.save(DST, quality=92, optimize=True)

print(f"{DST}  {img.width}x{img.height} -> {out.width}x{out.height}")
