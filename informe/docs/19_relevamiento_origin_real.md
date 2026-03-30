# Relevamiento de la branch `origin/real`

Este documento resume los hallazgos relevantes de la branch `origin/real` para
cerrar las partes de setup, metodologia y experimentacion de laboratorio del
informe.

## Alcance del relevamiento

Se revisaron especialmente estos archivos de `origin/real`:

- `PASOS_LAB_REAL.md`
- `README.md`
- `run_marine_real.sh`
- `rosbags/record_lab_real.sh`
- `rosbags/plot_movimiento_comparaciones.py`
- `rosbags/lab_real_20260320_125002_movimiento_full_v3/metadata.yaml`
- `rosbags/lab_real_20260320_125002_movimiento_full_v3/reporte_movimiento_completo.md`
- `src/fixed_camera/launch/lab_real.launch.py`
- `src/fixed_camera/fixed_camera/stereo_eye_publisher.py`
- `stereo_camera/README.md`
- `stereo_camera/config.yaml`
- `stereo_camera/calibration/calibration_result.yaml`
- `src/go2_tools/go2_tools/marine_platform_simulator.py`

## Hallazgos confirmados

### 1. El setup real tuvo un pipeline propio, no una traduccion trivial del caso simulado

La parte real no se implemento simplemente reusando el mismo launch de
simulacion con pequeños cambios. La branch `origin/real` agrega un pipeline
especifico para laboratorio que incluye:

- `run_marine_real.sh`
- `rosbags/record_lab_real.sh`
- `src/fixed_camera/launch/lab_real.launch.py`
- `src/fixed_camera/fixed_camera/stereo_eye_publisher.py`
- la carpeta `stereo_camera/` para calibracion, validacion y exportacion

Esto refuerza la idea de que el pasaje de simulacion a laboratorio fue una
adaptacion metodologica concreta y no solo un cambio de entorno.

### 2. El movimiento del Go2 real se genero con `marine_platform_simulator` en modo `real`

En la branch `origin/real`, `marine_platform_simulator.py` incorpora un
parametro `mode` con dos variantes:

- `sim`: publica `Pose` en `/body_pose`
- `real`: envia comandos Euler al Go2 via `unitree_sdk2py`

Por lo tanto, en laboratorio la continuidad con simulacion existe a nivel
conceptual, pero no a nivel de interface exacta. La consigna deja de ejecutarse
como un `Pose` publicado para Gazebo y pasa a materializarse como comandos
`Euler()` hacia el robot real.

### 3. El experimento real uso una camara estereo en modo monocular

La adquisicion visual real se implemento con una `3D USB Camera`
(`32e4:0035`) en `/dev/video2`, de tipo side-by-side:

- frame completo: `3840 x 1080`
- por ojo: `1920 x 1080`
- frame rate: `30 fps`

El nodo `stereo_eye_publisher.py` recorta uno de los dos ojos y publica:

- `/stereo_camera/image_raw`
- `/stereo_camera/camera_info`

La configuracion guardada en `stereo_camera/config.yaml` indica:

- `selected_eye: left`

### 4. Hubo calibracion formal de la camara

La branch real incluye un pipeline especifico de calibracion con checkerboard:

- `01_preview_stereo.py`
- `02_capture_calibration.py`
- `03_calibrate.py`
- `04_validate_calibration.py`
- `05_detect_aruco.py`

Segun `stereo_camera/calibration/calibration_result.yaml`, la calibracion usada
dio:

- resolucion: `1920 x 1080`
- `fx = 600.9731`
- `fy = 598.8189`
- `cx = 970.6993`
- `cy = 527.9427`
- distorsion: `[-0.0374, 0.0876, -0.0065, 0.0018, -0.0672]`
- error RMS de reproyeccion: `0.221355 px`
- imagenes usadas: `20`

Esto permite escribir la metodologia de laboratorio con mucha mas precision que
antes, porque ya no hace falta hablar de una calibracion generica o ad hoc.

### 5. El launch real de vision fue `lab_real.launch.py`

Ese launch levanta tres nodos:

- `stereo_eye_publisher`
- `aruco_detector`
- `camera_controller`

Tambien publica un TF estatico `world -> odom`.

Los topics visuales principales del caso real pasan a ser:

- `/stereo_camera/image_raw`
- `/stereo_camera/camera_info`
- `/aruco/pose`
- `/aruco/detection`
- `/aruco/debug_image`

### 6. La comparacion fuerte del laboratorio no fue solo contra `/odom`

El analisis guardado en
`rosbags/lab_real_20260320_125002_movimiento_full_v3/reporte_movimiento_completo.md`
usa varias señales:

- señal esperada: `/marine_platform/debug_state`
- comando efectivo: `/api/sport/request` filtrando `api_id = 1007`
- estado real principal: `/sportmodestate`
- estado real alternativo: `/lowstate`
- odometria: `/utlidar/robot_odom`

Esto cambia una parte importante del relato actual del informe: `odom` no fue
la unica referencia, sino una de varias señales de estado usadas para validar la
respuesta del robot.

### 7. La corrida real versionada tiene evidencia cuantitativa util

El bag `lab_real_20260320_125002_movimiento_full_v3` dura:

- `59.73 s`
- `159020` mensajes

Disponibilidad de señales principales:

- `/marine_platform/debug_state`: `120` muestras (`~2.00 Hz`)
- `/api/sport/request`: `3126` mensajes totales
- `api_id=1007` Euler: `2968` (`~49.70 Hz`)
- `/sportmodestate`: `29671` (`~498.02 Hz`)
- `/lowstate`: `29788` (`~499.77 Hz`)
- `/utlidar/robot_odom`: `14461` (`~242.73 Hz`)

### 8. El camino de comando quedo validado con alta fidelidad

El reporte de laboratorio informa, para la comparacion
`/marine_platform/debug_state -> /api/sport/request`:

- pares comparados: `120`
- desfase temporal medio: `4.98 ms`
- desfase maximo: `10.18 ms`
- correlacion `x API vs roll esperado`: `0.999887`
- correlacion `y API vs pitch esperado`: `0.999909`
- RMSE `x-roll`: `0.00261 rad`
- RMSE `y-pitch`: `0.00188 rad`

Esto permite afirmar que el problema principal no estuvo en la publicacion del
comando, sino en la dinamica fisica del robot y en la interpretacion de la
respuesta.

### 9. La respuesta real del robot siguio al comando con retardo estable

El mismo reporte indica:

- rango real de roll: `-14.388° a 16.190°`
- rango real de pitch: `-11.532° a 11.455°`

Correlacion a lag cero:

- `debug_roll vs roll_real`: `~0.91`
- `debug_pitch vs pitch_real`: `~0.81`

Correlacion maxima con busqueda de lag en `±3 s`:

- roll: mejor lag `~0.35 s`, correlacion `~0.9695`
- pitch: mejor lag `~0.60 s`, correlacion `~0.9680`

Esto ofrece un resultado fuerte para la seccion experimental de laboratorio:
la respuesta real del cuerpo del robot fue altamente coherente con la consigna,
pero con retardo dinamico y reduccion de amplitud respecto del objetivo.

### 10. En esa corrida no hubo heave dinamico efectivo

El reporte explicita que en `movimiento_full_v3`:

- `debug_state.z = 0`
- `z` enviado por API = `0`

El `z` observado en estado real aparece como altura absoluta del tronco, no
como una oscilacion de heave comparable directamente con la consigna.

Esto es importante para el informe porque evita una interpretacion incorrecta:
esa corrida sirve muy bien para discutir `roll` y `pitch`, pero no para sostener
un resultado fuerte sobre heave dinamico.

### 11. El gait dominante fue estable durante casi toda la prueba

Segun el reporte:

- `gait_type = 9`: `29006` muestras
- `gait_type = 0`: `665` muestras

Esto puede usarse como dato de estabilidad del regimen de marcha durante la
corrida real.

## Impacto directo sobre el informe

### Metodologia en laboratorio

Deberia incorporar de manera explicita:

- que el movimiento real se genero con `marine_platform_simulator` en modo
  `real`, no solo con `/body_pose`;
- que el camino de actuacion paso por `unitree_sdk2py` y la API de Sport Mode;
- que la adquisicion visual uso una camara estereo side-by-side recortada a un
  solo ojo;
- que hubo calibracion formal con `20` imagenes y RMS `0.221 px`;
- que el launch real de vision fue `lab_real.launch.py`;
- que la grabacion real se hizo con `record_lab_real.sh`.

### Experimentos en laboratorio

Deberia incorporar de manera explicita:

- el bag `lab_real_20260320_125002_movimiento_full_v3` como corrida principal;
- la cadena `debug_state -> api/sport/request -> sportmodestate / lowstate /
  robot_odom`;
- la validacion del camino de comando con correlaciones `~0.9999`;
- la comparacion comando-respuesta real con correlaciones `~0.97` a mejor lag;
- la observacion de que `heave` no fue dinamico en esa corrida;
- la lectura de que el robot reproduce el movimiento con retardo fisico estable.

## Inconsistencias o puntos a confirmar

### 1. Tamano del ArUco real

Hay una inconsistencia clara entre materiales:

- `PASOS_LAB_REAL.md` menciona `0.50 m`
- `README.md` de `origin/real`, `lab_real.launch.py` y `stereo_camera/config.yaml`
  usan `0.20 m`

Como la configuracion ejecutable del setup real usa `0.20 m`, por ahora es el
valor que parece mejor respaldado para el informe, pero conviene confirmarlo con
ustedes antes de cerrar la redaccion final.

### 2. Camara completamente fija vs sostenida

La narrativa previa del informe hablaba de una camara "sostenida" por encima
del robot. La branch `origin/real` esta mas cerca de un montaje fijo:

- `camera_controller`
- `lab_real.launch.py`
- `stereo_camera.config.yaml` con `mounting.type = fixed`

La redaccion mas segura es hablar de una camara mantenida en posicion
aproximadamente fija sobre la escena, sin forzar una rigidez perfecta si eso no
refleja exactamente como se hizo la toma.

### 3. Continuidad con `/body_pose`

La continuidad conceptual con simulacion sigue siendo valida, pero la
implementacion real no usa exactamente el mismo canal de actuacion. Conviene que
el informe explique esta continuidad como continuidad metodologica del objetivo,
no como identidad literal de topics.
