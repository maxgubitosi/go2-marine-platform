"""Saca de la corrida de laboratorio el cuadro de la deteccion para la lamina 14.

La lamina afirma que el detector engancha sobre el robot real, no sobre una
textura de Gazebo, asi que la figura tiene que ser un cuadro de la camara del
laboratorio con el dibujo de la deteccion encima: contorno verde, esquina de
origen en rojo y el identificador.

La fuente es `lab_01_camara_fija_deteccion.mp4`, que es la salida del pipeline
visual ya anotada. Viene a ~1,1 fps, o sea 67 cuadros para casi un minuto, asi
que el cuadro se elige por numero y no por tiempo: con `-ss` en segundos ffmpeg
cae en otro cuadro segun como redondee.

Por que el 36: es donde la hoja entra entera y el robot tambien. En los
primeros el operador esta mas cerca y en los ultimos el robot ya se corrio y
queda cortado arriba.

Por que la ventana va rotada. El operador esta parado justo arriba del robot y
en el cuadro crudo se le ve una sandalia. Con un recorte recto no hay forma de
sacarla sin comerle la cabeza al robot: el robot llega hasta x=751 y la
sandalia arranca en x=680, o sea que se superponen en x, y en y estan pegadas
(sandalia hasta 325, robot desde 310). Rotando 9,5 grados el borde superior de
la ventana pasa por debajo de la sandalia y por encima del robot, que es lo que
un recorte alineado a los ejes no puede hacer. De paso el cuerpo del robot
queda horizontal, que se lee mejor proyectado.

El angulo y el centro salen del rectangulo que marco Maximo sobre la lamina.
"""
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else "defensa/web/assets/media/lab_01_camara_fija_deteccion.mp4"
DST = sys.argv[2] if len(sys.argv) > 2 else "defensa/web/assets/img/lab_aruco_deteccion.png"

CUADRO = 36
ANGULO = 9.50           # grados, antihorario
CENTRO = (530.0, 442.0)  # sobre el cuadro crudo de 1280x720
ANCHO, ALTO = 480, 288   # 5:3, la misma proporcion que tenia el recorte recto

tmp = Path(DST).with_suffix(".raw.png")
subprocess.run(
    ["ffmpeg", "-loglevel", "error", "-i", SRC,
     "-vf", rf"select='eq(n\,{CUADRO})'", "-frames:v", "1", "-y", str(tmp)],
    check=True,
)

img = Image.open(tmp).convert("RGB")
assert img.size == (1280, 720), f"el cuadro no es 1280x720: {img.size}"

# Rotar y recortar en un solo paso de remuestreo: rotar sobre el centro de la
# ventana deja la ventana alineada a los ejes y el crop despues no interpola.
img = img.rotate(ANGULO, resample=Image.BICUBIC, center=CENTRO)
cx, cy = CENTRO
img = img.crop((round(cx - ANCHO / 2), round(cy - ALTO / 2),
                round(cx + ANCHO / 2), round(cy + ALTO / 2)))
assert abs(img.width / img.height - 5 / 3) < 1e-2, f"la ventana no es 5:3: {img.size}"
img.save(DST, optimize=True)
tmp.unlink()

print(f"{DST}  {img.width}x{img.height}  ({img.width / img.height:.3f})")
