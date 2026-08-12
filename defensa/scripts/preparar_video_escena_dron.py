"""Convierte el screencast de la escena del dron a un mp4 usable en el deck.

La grabacion cruda es un screencast de escritorio entero, 1366x768 en VP8 y casi
siete minutos. Dos cosas hay que arreglarle antes de que pueda entrar al repo:

1. Los primeros ~120 segundos son el escritorio con una terminal y una
   conversacion de trabajo a la vista. Eso no puede publicarse: el repo se sirve
   entero por GitHub Pages, asi que cualquier archivo commiteado queda accesible
   por URL. El corte arranca en el segundo 125, ya con Gazebo a pantalla
   completa; verificado cuadro por cuadro cada 12 s hasta el final.

2. Lo que interesa es el visor 3D, no la ventana. Recortando el visor se van la
   barra del escritorio, el titulo, los menus, el panel de World/Insert/Layers y
   la barra de estado con el Real Time Factor. Queda 1008x567, o sea 16:9
   exacto, que es la proporcion con la que el deck maqueta los videos. El borde
   derecho corta en 1350 y no en 1366: los ultimos pixeles son el marco de la
   ventana y entraban como una franja oscura.

Se queda con los dos primeros minutos del tramo util, que es donde el dron ya
esta estacionado sobre la plataforma y la escena no cambia mas.
"""
import subprocess
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else "defensa/Screencast from 12-08-26 13_58_25.webm"
DST = sys.argv[2] if len(sys.argv) > 2 else "defensa/web/assets/media/sim_06_dron_escena_exterior.mp4"

DESDE = 125          # segundos; antes de esto se ve el escritorio
DURACION = 120       # dos minutos, elegidos sobre el mp4 ya convertido
CROP = (1008, 567, 342, 136)  # w, h, x, y sobre el cuadro de 1366x768

w, h, x, y = CROP
subprocess.run(
    ["ffmpeg", "-loglevel", "error", "-ss", str(DESDE), "-t", str(DURACION), "-i", SRC,
     "-vf", f"crop={w}:{h}:{x}:{y}",
     "-an",                        # el screencast no trae audio, se explicita
     "-c:v", "libx264", "-crf", "23", "-preset", "slow",
     "-pix_fmt", "yuv420p",        # sin esto Safari no lo reproduce
     "-movflags", "+faststart",
     "-y", DST],
    check=True,
)

info = subprocess.run(
    ["ffprobe", "-v", "error", "-select_streams", "v:0",
     "-show_entries", "stream=width,height", "-show_entries", "format=duration,size",
     "-of", "csv=p=0", DST],
    capture_output=True, text=True, check=True,
).stdout.split()
print(f"{DST}  {' '.join(info)}")
