# Metodologia en laboratorio - guia detallada

## Objetivo de este documento

Este documento consolida lo que ya quedo confirmado sobre la parte de
laboratorio y ordena como deberia contarse en el informe. Ya no funciona como
lista de huecos grandes, sino como apoyo para mantener consistencia entre
setup, metodologia y experimentacion real.

## Funcion narrativa

La etapa de laboratorio no debe presentarse como una replica exacta de Gazebo.
Su valor metodologico es otro:

- mostrar que el movimiento sintetizado puede trasladarse a un Go2 real;
- explicitar que adaptaciones fueron necesarias al salir de simulacion;
- verificar si la cadena referencia -> comando -> respuesta del robot conserva
  coherencia fisica;
- dejar preparada la observacion visual real con ArUco y camara calibrada.

En este bloque se pierde ground truth perfecto, pero se gana validacion fisica
del pipeline.

## Implementacion real ya confirmada

### 1. Generacion del movimiento

- `marine_platform_simulator.py` incorpora `mode=real`
- en `sim` publica `Pose` en `/body_pose`
- en `real` envia comandos `Euler()` via `unitree_sdk2py`
- la referencia esperada queda en `/marine_platform/debug_state`
- el comando efectivo aparece en `/api/sport/request`, filtrando
  `api_id = 1007`

La continuidad con simulacion existe a nivel metodologico, no como identidad
literal de topics.

### 2. Setup visual

- el ArUco se monta sobre el lomo del Go2
- la vision real usa una camara estereo side-by-side en `/dev/video2`
- frame completo: `3840x1080`
- por ojo: `1920x1080`
- en las pruebas versionadas se usa `selected_eye: left`
- los topics visuales principales son:
  - `/stereo_camera/image_raw`
  - `/stereo_camera/camera_info`
  - `/aruco/pose`
  - `/aruco/detection`
  - `/aruco/debug_image`

### 3. Calibracion

- hubo calibracion formal con checkerboard
- resultado guardado en
  `stereo_camera/calibration/calibration_result.yaml`
- `20` imagenes usadas
- RMS de reproyeccion: `0.221355 px`
- intrinsecos principales:
  - `fx = 600.9731`
  - `fy = 598.8189`
  - `cx = 970.6993`
  - `cy = 527.9427`

### 4. Launch y registro

- el launch visual real es `src/fixed_camera/launch/lab_real.launch.py`
- levanta:
  - `stereo_eye_publisher`
  - `aruco_detector`
  - `camera_controller`
  - un TF estatico `world -> odom`
- existe ademas un pipeline operativo con:
  - `run_marine_real.sh`
  - `rosbags/record_lab_real.sh`

### 5. Senales de comparacion

La comparacion fuerte del laboratorio no fue solo contra odometria. Las senales
versionadas mas importantes son:

- referencia esperada: `/marine_platform/debug_state`
- comando efectivo: `/api/sport/request`
- estado real principal: `/sportmodestate`
- estado real alternativo: `/lowstate`
- odometria adicional: `/utlidar/robot_odom`

## Subestructura recomendada para el informe

### 1. Introduccion del pasaje a laboratorio

Esta apertura deberia explicar:

- por que no alcanzaba con la simulacion;
- que partes del framework se quisieron contrastar en el Go2 real;
- por que al salir de Gazebo cambia la naturaleza de la validacion.

La idea fuerte es que el laboratorio no responde "cuanto error hay contra
ground truth", sino "que tan bien se transmite y reproduce el movimiento
propuesto en el sistema fisico".

### 2. Reproduccion del movimiento en el Go2 real

#### Que conviene contar

- que la idea fisica del movimiento se conserva respecto de simulacion;
- que la implementacion cambia de una `Pose` en Gazebo a comandos Euler via
  SDK2;
- que `debug_state` y `api/sport/request` separan referencia y actuacion;
- que el robot se analiza despues a partir de sus propios estados internos.

#### Punto narrativo clave

La continuidad entre simulacion y laboratorio no pasa por reutilizar el mismo
topic, sino por conservar la misma clase de movimiento objetivo sobre el torso
del robot.

### 3. Estimacion visual con camara en configuracion cuasi fija

#### Que conviene contar

- que el ArUco se pego sobre el lomo;
- que se uso una camara estereo como monocular;
- que se calibro formalmente antes de usarla;
- que el launch real encapsulo todo el setup visual;
- que la camara se mantuvo en una posicion aproximadamente fija sobre la escena,
  aunque sin la idealizacion perfecta del caso simulado.

#### Consecuencia editorial

Este setup debe narrarse como una aproximacion experimental controlada al caso
`fixed_camera`, no como una copia exacta del escenario de Gazebo.

### 4. Comparacion entre movimiento esperado, comando y respuesta del robot

#### Que conviene contar

- que la comparacion se arma como cadena:
  `debug_state -> api/sport/request -> sportmodestate/lowstate/robot_odom`
- que las frecuencias son distintas y por eso hace falta alinear temporalmente
  las series;
- que el analisis busca separar:
  - fidelidad del camino de comando
  - fidelidad de la respuesta fisica del robot

#### Lectura metodologica correcta

La pregunta ya no es si el robot coincide punto a punto con un ground truth
perfecto, sino si la dinamica solicitada reaparece de forma coherente en sus
senales internas y puede sostener el uso del framework como banco de pruebas.

## Lo que ya puede sostenerse con evidencia versionada

- existe un bag real de referencia:
  `lab_real_20260320_125002_movimiento_full_v3`
- dura `59.73 s`
- contiene suficiente informacion para reconstruir la cadena de senales
  principal
- el camino de comando queda validado con correlaciones `~0.9999`
- la respuesta del robot sigue la consigna con alta correlacion al compensar
  lag:
  - roll: `~0.9695` con `~0.35 s`
  - pitch: `~0.9680` con `~0.60 s`
- en esa corrida no hubo heave dinamico efectivo

## Lo que todavia conviene confirmar

1. tamano fisico final del ArUco real:
   `0.20 m` o `0.50 m`
2. si la camara quedo montada en soporte fijo, en soporte improvisado o en una
   condicion intermedia que convenga describir con mas precision
3. si se va a reportar o no una evaluacion cuantitativa final de `/aruco/pose`
   en laboratorio

## Riesgos a evitar

- escribir esta parte como si hubiera un ground truth equivalente al de Gazebo;
- reducir el contraste real a "consigna vs odom", porque la evidencia
  versionada es mas rica que eso;
- prometer una validacion visual real mas cerrada de la que hoy esta respaldada;
- ocultar que el pasaje a laboratorio exigio una implementacion propia.

## Figuras que conviene producir

1. foto o esquema del setup real completo;
2. frame de la deteccion ArUco en laboratorio;
3. comparacion temporal entre `debug_state`, `api/sport/request` y
   `sportmodestate`;
4. curva de correlacion en funcion del lag;
5. si se usa, grafico que explique por que el eje `z` real no equivale
   directamente a heave dinamico en la corrida versionada.
