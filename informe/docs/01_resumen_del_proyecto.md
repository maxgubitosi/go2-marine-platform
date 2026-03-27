# Resumen del proyecto

## Problema que resuelve

El proyecto construye un framework de simulacion para desarrollar y validar
estimacion de pose visual de un marcador ArUco sobre una plataforma marina en
movimiento, sin arriesgar hardware real. La plataforma se simula usando el
torso de un Unitree Go2, mientras una camara fija o la camara inferior de un
dron `sjtu_drone` observan el marcador.

## Objetivo de investigacion

Quedo confirmado por el usuario que el objetivo mas amplio de la investigacion
es construir un framework completo para poder probar aterrizaje de drones sobre
plataformas marinas.

Dentro de ese objetivo general, el trabajo de esta tesis cubre al menos estas
capacidades habilitantes:

- sintetizar una plataforma marina en movimiento usando el Go2;
- observar esa plataforma con una camara fija o un dron;
- estimar visualmente la pose relativa del marcador sobre la plataforma;
- comparar la estimacion contra ground truth en simulacion;
- empezar a contrastar el movimiento simulado con el comportamiento real del
  cuadrupedo en laboratorio.

En otras palabras, el aterrizaje autonomo aparece como aplicacion final del
framework, mientras que esta tesis desarrolla y valida la infraestructura
experimental y perceptiva necesaria para llegar a ese escenario.

## Alcance global confirmado por el usuario

Segun la aclaracion mas reciente del proyecto, la tesis completa no termina en
la simulacion. La historia real del trabajo fue:

1. levantar la simulacion del Unitree en ROS2 y Gazebo;
2. anexar una tabla con un marcador ArUco sobre el lomo del robot;
3. simular el movimiento de las olas usando el cuadrupedo;
4. agregar una camara fija para grabar y estimar los 6 grados de libertad;
5. repetir esa estimacion con un dron simulado;
6. llevar el cuadrupedo al laboratorio y reproducir la logica de movimiento en
   entorno real para compararla con la simulacion;
7. montar nuevamente un ArUco y una camara sostenida de forma aproximadamente
   fija para estimar la pose;
8. verificar si el movimiento propuesto correlaciona con el movimiento real,
   comparando consigna vs odometria publicada por el cuadrupedo.

Esto define una narrativa natural en dos fases:

- fase 1: construccion y validacion del framework en simulacion;
- fase 2: verificacion experimental de que el movimiento sintetizado y el
  comportamiento observado en el robot real guardan correlacion suficiente.

## Pipeline confirmado por el repo

1. `go2_tools/marine_platform_simulator.py` genera una `Pose` en
   `/body_pose` con roll, pitch y heave.
2. El cuerpo del Go2 adopta esa consigna postural a traves del stack externo
   del robot que el README identifica como `unitree-go2-ros2`.
3. Una fuente de imagen observa el marcador:
   - camara fija en `src/fixed_camera/`
   - camara bottom del dron en `src/sjtu_drone/`
4. Un nodo `aruco_detector` estima la pose del marcador en el frame optico de
   la camara y publica `/aruco/pose`.
5. Se graba un rosbag con imagenes, pose estimada y ground truth del simulador.
6. `aruco_relative_pose/scripts/evaluate_realtime_aruco.py` reconstruye el
   ground truth del marcador en el frame de la camara y compara estimacion vs
   referencia.

## Componentes principales

| Componente | Rol | Evidencia principal |
|---|---|---|
| `src/go2_tools/` | Genera oleaje sinusoidal o irregular y modo manual | `marine_platform_simulator.py`, `marine_manual_control.py` |
| `src/fixed_camera/` | Camara estatica en Gazebo + detector ArUco | `fixed_camera.launch.py`, `camera_controller.py`, `aruco_detector.py` |
| `src/sjtu_drone/` | Dron simulado, hover automatico y detector ArUco | `sjtu_drone_spawn.launch.py`, `drone_position_controller.py`, `aruco_detector.py` |
| `aruco_relative_pose/` | Evaluacion offline y analisis | `evaluate_realtime_aruco.py`, `analyze_pose_results.py` |
| `marine_robot_dataset/` | Extraccion de datasets sincronizados desde rosbag | `extract_dataset.py` |
| `informe/` | Informe de tesis en LaTeX | `main.TeX`, `bibliography.bib`, `figures/` |

## Parametros y hechos tecnicos ya confirmados

### Simulador marino

- Nodo: `marine_platform_simulator`
- Topic principal: `/body_pose`
- Frecuencia base: `rate_hz = 20.0`
- Frecuencia de onda default: `wave_frequency = 0.1 Hz`
- Limites default:
  - roll: `+-15 deg`
  - pitch: `+-10 deg`
  - heave: `+-0.10 m`
- Patrones implementados:
  - `sinusoidal`
  - `irregular`
- Suavizado exponencial:
  - parametro `smoothing_factor = 0.95`

### Justificacion del recorte a roll, pitch y heave

El framework no intenta reproducir la dinamica completa de una embarcacion en
seis grados de libertad. En esta tesis se priorizan `roll`, `pitch` y `heave`
por una razon metodologica y perceptiva:

- son las componentes que mas afectan la orientacion aparente del marcador y la
  distancia relativa camara-objetivo;
- en el setup actual la observacion visual se concentra en un marcador montado
  sobre el torso del Go2;
- la simulacion mantiene anuladas las componentes horizontales `x` e `y` y
  tambien `yaw`, para aislar las perturbaciones visuales mas relevantes en esta
  primera etapa del framework.

Esto no implica que surge, sway o yaw sean irrelevantes para el problema final
de aterrizaje sobre plataformas marinas. Implica, mas bien, que en el alcance
actual de la tesis se adopta una simplificacion deliberada para validar primero
la cadena simulacion-percepcion-evaluacion sobre el subconjunto de movimientos
que mas directamente alteran la pose observada del marcador.

### Marcador y deteccion visual

- Diccionario: `DICT_6X6_250`
- ID objetivo: `0`
- Lado del marcador: `0.50 m`
- Salidas del detector:
  - `/aruco/pose`
  - `/aruco/detection`
  - `/aruco/debug_image`
- La pose se estima en el frame optico de la camara.

### Camara fija

- Launch: `src/fixed_camera/launch/fixed_camera.launch.py`
- Resolucion del sensor en URDF: `640x480`
- FOV horizontal: `1.396 rad`
- Update rate del sensor: `30 Hz`
- Altura default de spawn: `2.0 m`
- `camera_controller.py` publica `world -> camera_base_link` y `/fixed_camera/pose`
- El script de evaluacion usa posicion optica fija `z = 1.955 m`, consistente
  con el offset del URDF entre `camera_base_link` y `camera_link`.

### SJTU drone

- Launch: `src/sjtu_drone/sjtu_drone_bringup/launch/sjtu_drone_spawn.launch.py`
- Resolucion de la camara bottom: `640x360`
- FOV horizontal de bottom cam: `1.047 rad`
- Update rate de bottom cam: `15 Hz`
- Spawn default del dron:
  - `x = 2.0`
  - `y = 0.0`
  - `z = 0.08`
- Hover target del controlador:
  - `x = 0.5`
  - `y = 0.0`
  - `z = 3.0`
- `drone_position_controller.py`:
  - manda takeoff automatico
  - activa position control
  - republica `/drone/pose`

### Evaluacion offline

- Script principal: `aruco_relative_pose/scripts/evaluate_realtime_aruco.py`
- Fuentes usadas para reconstruir GT del Go2:
  - `/odom`
  - `/imu/data`
  - `/base_to_footprint_pose`
- Offset del marcador respecto del trunk:
  - `[0.0, 0.0, 0.091] m`
- Offset default de spawn del Go2 en el mundo:
  - `world_init_x = 0.40 m`
  - `world_init_y = 0.0 m`

## Cosas importantes para el informe

- El sistema separa claramente percepcion online y evaluacion offline.
- La estimacion online no usa informacion privilegiada del simulador.
- La parte del Go2 real ya forma parte del alcance global de la tesis segun lo
  confirmado por el usuario, pero en esta branch todavia no tenemos evidencia
  tecnica suficiente para redactarla en detalle.
- La reconstruccion exacta del control postural del Go2 depende de un repositorio
  externo no incluido en este checkout.
