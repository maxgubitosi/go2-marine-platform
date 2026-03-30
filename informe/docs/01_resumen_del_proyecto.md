# Resumen del proyecto

## Problema que resuelve

El proyecto construye un framework para desarrollar y validar estimacion de
pose visual sobre una plataforma marina en movimiento sin depender, en una
primera etapa, de ensayos de aterrizaje con hardware costoso. La plataforma se
sintetiza usando el torso de un Unitree Go2, mientras una camara fija o la
camara inferior de un dron `sjtu_drone` observan un marcador ArUco montado
sobre el robot.

## Objetivo de investigacion

Quedo confirmado por el usuario que el objetivo mas amplio de la investigacion
es construir un framework completo para poder probar aterrizaje de drones sobre
plataformas marinas.

Dentro de ese objetivo general, la tesis cubre estas capacidades habilitantes:

- sintetizar una plataforma marina en movimiento usando el Go2;
- observar esa plataforma con una camara fija o un dron;
- estimar visualmente la pose relativa del marcador;
- comparar la estimacion contra ground truth en simulacion;
- trasladar parte del pipeline al laboratorio para verificar si el movimiento
  propuesto reaparece de forma coherente en el robot real.

En otras palabras, el aterrizaje autonomo aparece como objetivo final del
framework, mientras que esta tesis desarrolla y valida la infraestructura
experimental y perceptiva necesaria para llegar a ese escenario.

## Alcance global confirmado por el usuario

La historia real del trabajo fue:

1. levantar la simulacion del Unitree en ROS2 y Gazebo;
2. anexar una tabla con un marcador ArUco sobre el lomo del robot;
3. simular el movimiento de las olas usando el cuadrupedo;
4. agregar una camara fija para grabar y estimar los 6 grados de libertad;
5. repetir esa estimacion con un dron simulado;
6. llevar el cuadrupedo al laboratorio y reproducir la logica de movimiento en
   entorno real para compararla con la simulacion;
7. montar nuevamente un ArUco y una camara en configuracion aproximadamente
   fija para estimar la pose;
8. verificar si el movimiento propuesto correlaciona con el movimiento real,
   comparando la referencia esperada, el comando efectivo y las senales de
   estado publicadas por el cuadrupedo.

Esto define una narrativa natural en dos fases:

- fase 1: construccion y validacion del framework en simulacion;
- fase 2: verificacion experimental del pasaje a laboratorio.

## Pipeline confirmado por el checkout principal

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

## Pipeline de laboratorio confirmado por la implementacion real

1. `go2_tools/marine_platform_simulator.py` corre en `mode=real` y conserva la
   misma logica fisica del movimiento objetivo, pero ya no publica una `Pose`
   para Gazebo: envia comandos `Euler()` al Go2 mediante `unitree_sdk2py`.
2. La referencia esperada queda registrada en `/marine_platform/debug_state`.
3. El comando efectivamente transmitido al robot aparece en
   `/api/sport/request`, filtrando `api_id = 1007`.
4. La respuesta del robot se observa principalmente en:
   - `/sportmodestate`
   - `/lowstate`
   - `/utlidar/robot_odom`
5. La parte visual del laboratorio se apoya en:
   - `src/fixed_camera/launch/lab_real.launch.py`
   - `src/fixed_camera/fixed_camera/stereo_eye_publisher.py`
   - `/stereo_camera/image_raw`
   - `/stereo_camera/camera_info`
   - `/aruco/pose`
   - `/aruco/detection`
   - `/aruco/debug_image`

## Componentes principales

| Componente | Rol | Evidencia principal |
|---|---|---|
| `src/go2_tools/` | Genera oleaje sinusoidal o irregular y modo manual | `marine_platform_simulator.py`, `marine_manual_control.py` |
| `src/fixed_camera/` | Camara estatica en Gazebo y pipeline visual real de laboratorio | `fixed_camera.launch.py`, `lab_real.launch.py`, `camera_controller.py`, `aruco_detector.py`, `stereo_eye_publisher.py` |
| `src/sjtu_drone/` | Dron simulado, hover automatico y detector ArUco | `sjtu_drone_spawn.launch.py`, `drone_position_controller.py`, `aruco_detector.py` |
| `aruco_relative_pose/` | Evaluacion offline y analisis | `evaluate_realtime_aruco.py`, `analyze_pose_results.py` |
| `marine_robot_dataset/` | Extraccion de datasets sincronizados desde rosbag | `extract_dataset.py` |
| `stereo_camera/` | Calibracion y configuracion del setup visual real | `config.yaml`, `calibration_result.yaml`, scripts de preview/capture/calibration |
| `informe/` | Informe de tesis en LaTeX | `main.TeX`, `bibliography.bib`, `figures/` |

## Parametros y hechos tecnicos ya confirmados

### Simulador marino

- Nodo: `marine_platform_simulator`
- Topic principal en simulacion: `/body_pose`
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

### Marcador y deteccion visual

- Diccionario: `DICT_6X6_250`
- ID objetivo: `0`
- Lado del marcador en simulacion: `0.50 m`
- Lado del marcador en la configuracion ejecutable del laboratorio: `0.20 m`
  `pendiente de confirmacion final por inconsistencia entre materiales`
- Salidas del detector:
  - `/aruco/pose`
  - `/aruco/detection`
  - `/aruco/debug_image`
- La pose se estima en el frame optico de la camara.

### Camara fija en simulacion

- Launch: `src/fixed_camera/launch/fixed_camera.launch.py`
- Resolucion del sensor en URDF: `640x480`
- FOV horizontal: `1.396 rad`
- Update rate del sensor: `30 Hz`
- Altura default de spawn: `2.0 m`
- `camera_controller.py` publica `world -> camera_base_link` y
  `/fixed_camera/pose`
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

### Evaluacion offline en simulacion

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

### Laboratorio real

- Launch visual: `src/fixed_camera/launch/lab_real.launch.py`
- Sensor: camara estereo side-by-side usada como monocular
- Resolucion por ojo: `1920x1080`
- Ojo usado en las pruebas versionadas: `left`
- Calibracion formal guardada en:
  `stereo_camera/calibration/calibration_result.yaml`
- Error RMS de reproyeccion: `0.221355 px`
- Imagenes de calibracion usadas: `20`
- Bag de referencia relevado:
  `lab_real_20260320_125002_movimiento_full_v3`
- Duracion del bag de referencia: `59.73 s`
- Cadena principal de comparacion:
  `debug_state -> api/sport/request -> sportmodestate / lowstate / robot_odom`
- Fidelidad del camino de comando:
  - correlacion roll/API: `0.999887`
  - correlacion pitch/API: `0.999909`
  - delay medio: `4.98 ms`
- Respuesta real del robot:
  - correlacion a mejor lag en roll: `~0.9695` con `~0.35 s`
  - correlacion a mejor lag en pitch: `~0.9680` con `~0.60 s`
  - sin heave dinamico efectivo en la corrida versionada

## Cosas importantes para el informe

- El sistema separa claramente percepcion online y evaluacion offline.
- La estimacion online no usa informacion privilegiada del simulador.
- La parte del Go2 real ya quedo suficientemente relevada como para escribir
  setup, metodologia y una primera seccion experimental de laboratorio.
- La evidencia real hoy sostiene mejor la reproduccion del movimiento y la
  comparacion comando-respuesta que una evaluacion estadistica cerrada de la
  pose visual real.
- La reconstruccion exacta del control postural del Go2 depende de un
  repositorio externo no incluido en este checkout.
- El principal punto tecnico todavia a confirmar es el tamano fisico final del
  ArUco usado en laboratorio: `0.20 m` o `0.50 m`.
