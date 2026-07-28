"""Convierte el logo UdeSA (JPG azul sobre blanco) a PNG con alfa real.

Modelo: cada pixel es C = a*F + (1-a)*255 (mezcla del trazo F contra papel blanco).
De ahi a = 1 - min(r,g,b)/255, y F = (C - (1-a)*255) / a.
Recupera exacto el color del trazo incluso en los bordes antialiaseados,
cosa que un simple "chroma key de blanco" no hace.
"""
import sys
import numpy as np
from PIL import Image

SRC, DST, WIDTH = sys.argv[1], sys.argv[2], int(sys.argv[3])

img = Image.open(SRC).convert("RGB")
c = np.asarray(img).astype(np.float32)

a = 1.0 - c.min(axis=2) / 255.0
a[a < 0.02] = 0.0                      # ruido JPEG en el blanco -> transparente puro

a3 = a[..., None]
with np.errstate(divide="ignore", invalid="ignore"):
    f = np.where(a3 > 0, (c - (1.0 - a3) * 255.0) / np.maximum(a3, 1e-6), 0.0)
f = np.clip(f, 0, 255)

out = np.dstack([f, a * 255.0]).astype(np.uint8)
rgba = Image.fromarray(out, "RGBA")

bbox = rgba.getchannel("A").getbbox()  # recorta el margen blanco del original
if bbox:
    rgba = rgba.crop(bbox)

h = round(rgba.height * WIDTH / rgba.width)
rgba = rgba.resize((WIDTH, h), Image.LANCZOS)
rgba.save(DST, optimize=True)

px = np.asarray(rgba)
op = px[..., 3] > 8
print(f"{DST}  {rgba.width}x{rgba.height}")
print(f"  opacos: {op.mean():.1%}   color medio del trazo: {tuple(px[..., :3][op].mean(axis=0).round().astype(int))}")
print(f"  esquina (0,0) alfa={px[0, 0, 3]}   centro alfa={px[h // 2, WIDTH // 2, 3]}")
