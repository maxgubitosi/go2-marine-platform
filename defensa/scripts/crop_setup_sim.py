"""Recorta la vista del Go2 con el marcador en Gazebo para que quede en 3:4,
la misma relación que la foto del montaje de laboratorio.

Va en el slide "Del simulador al robot real", donde las dos imágenes se muestran
una al lado de la otra con una flecha en el medio. Para que la flecha se lea como
correspondencia y no como una comparación desprolija, los dos paneles tienen que
medir exactamente lo mismo, y eso sale solo si las relaciones de aspecto
coinciden: la foto del lab es 1200x1600 (0,75) una vez aplicada su orientación
EXIF, así que este recorte apunta al mismo número.

El original es casi cuadrado (259x243), de modo que el recorte se lleva un 30%
del ancho. El robot con el marcador vive en x[51,187], que entra cómodo en la
caja elegida con unos 20 px de aire a cada lado.

Uso:
    python3 defensa/scripts/crop_setup_sim.py

Escribe un archivo nuevo: nunca pisa el original.
"""

from PIL import Image

SRC = "defensa/web/assets/img/sim_contexto_go2.png"
DST = "defensa/web/assets/img/sim_setup_gazebo.png"

BOX = (29, 1, 209, 241)   # 180x240
RATIO = 0.75              # 3:4, igual que lab_go2_aruco_tripode_a.jpg

img = Image.open(SRC).convert("RGB").crop(BOX)
ratio = img.width / img.height
assert abs(ratio - RATIO) < 1e-3, f"relación {ratio:.4f}, se esperaba {RATIO}"
img.save(DST, optimize=True)
print(f"{DST}  {img.width}x{img.height}  ratio {ratio:.4f}")
