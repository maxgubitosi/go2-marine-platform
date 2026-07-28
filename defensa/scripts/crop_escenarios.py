"""Recorta las dos capturas del slide "Escenarios de observación" a una misma
relación de aspecto 3:2.

El problema que resuelve: los originales vienen con relaciones distintas
(640x480 = 1,33 y 702x454 = 1,55). Como en el slide van en dos columnas de igual
ancho y la caja de imagen toma su altura de la relación del archivo, cualquier
diferencia se traduce en dos cajas de distinto alto, la más alta desborda el
cuerpo del slide y lo que se derrama se superpone con el párrafo de cierre.

Los dos recortes salen exactamente en 1,5000, así que en columnas iguales las dos
cajas miden lo mismo sin necesidad de object-fit ni de fijar alturas a mano.

Las cajas se eligieron para no perder nada de la escena: en las dos hay bastante
fondo muerto (cielo gris arriba en la del dron, gris oscuro por todos lados en la
de la cámara fija), que es justamente lo que se descarta.

Uso:
    python3 defensa/scripts/crop_escenarios.py

Escribe archivos nuevos: nunca pisa los originales.
"""

from PIL import Image

DST_DIR = "defensa/web/assets/img"

# (origen, destino, caja de recorte, contenido que la caja tiene que respetar)
JOBS = [
    (
        # El cuadro crudo de la cámara fija, que es lo que el sensor realmente ve.
        # Casi todo el encuadre es fondo vacío: el robot ocupa 128x155 de 640x480
        # y encima queda arriba a la izquierda del centro, así que la caja lo
        # centra y se queda con el 22% del área original.
        "defensa/media/fotos_sim/01_frame_camara_fija_raw.png",
        "sim_escenario_fija.png",
        (164, 33, 479, 243),        # 315x210
        "marcador en x[257,385] y[60,187] y las patas hasta y=215, centrados",
    ),
    (
        "defensa/web/assets/img/sim_contexto_dron.png",
        "sim_escenario_dron.png",
        (59, 105, 509, 405),        # 450x300
        "dron en y[127,144], Go2 en x[168,236] y[287,330], cono hasta y=386",
    ),
]

for src, dst, box, keep in JOBS:
    img = Image.open(src).convert("RGB").crop(box)
    ratio = img.width / img.height
    assert abs(ratio - 1.5) < 1e-3, f"{dst}: relación {ratio:.4f}, se esperaba 1,5"
    img.save(f"{DST_DIR}/{dst}", optimize=True)
    print(f"{dst}  {img.width}x{img.height}  ratio {ratio:.4f}  (conserva: {keep})")
