# Metodologia en simulacion - guia detallada

## Objetivo de este documento

Este documento baja a detalle que deberia contar la subseccion
`Metodologia en simulacion`, que partes estan bien respaldadas por el repo y
que partes conviene aclarar antes de profundizar la escritura final.

## Funcion narrativa

La simulacion no aparece solo como una comodidad tecnica. Es el lugar donde se
puede:

- controlar el movimiento de la plataforma;
- observar ese movimiento desde una o mas camaras;
- registrar todas las senales relevantes;
- comparar la estimacion visual con un ground truth reconstruible.

Eso es exactamente lo que justifica a la simulacion como base del framework.

Operativamente, las corridas se registraron como rosbags de un minuto. Esa
unidad de trabajo conviene explicitarla en el informe porque ordena tanto la
descripcion metodologica como la posterior comparacion experimental.

Tambien conviene dejar explicitado el rol de cada escenario visual:

- `fixed_camera` funciona como caso base metodologico para introducir el setup,
  porque elimina el movimiento propio del sensor y deja mas aislado el efecto
  del oleaje sobre la observacion;
- `sjtu_drone` entra como extension fuerte del framework, porque agrega una
  camara movil y acerca el problema al escenario futuro de aterrizaje.

## Subestructura recomendada

### 1. Introduccion de la etapa de simulacion

Esta apertura deberia explicar tres cosas:

1. por que la simulacion fue el primer entorno de trabajo;
2. que componentes del framework quedaron cubiertos ahi;
3. por que ese entorno permite separar percepcion online de evaluacion offline.

### 2. Generacion del movimiento marino

#### Lo que hoy esta confirmado por codigo

- El nodo principal es `marine_platform_simulator`.
- Publica una `Pose` en `/body_pose`.
- Corre con un `rate_hz` default de 20 Hz.
- Simula `roll`, `pitch` y `heave`.
- Tiene patron `sinusoidal` y patron `irregular`.
- Usa parametros `wave_frequency`, `max_roll_deg`, `max_pitch_deg`,
  `max_heave_m`, `phase_offset_pitch`, `phase_offset_heave` y
  `smoothing_factor`.
- El suavizado es un filtro exponencial de primer orden.
- Existe un modo manual por `/marine_platform/manual_cmd`.
- El nodo publica `Vector3` en `/marine_platform/debug_state`.

#### Lo que conviene explicar mejor en el informe

- por que el movimiento se sintetiza como una pose objetivo del torso y no como
  una fuerza aplicada a un casco marino;
- por que se fijan `x`, `y` y `yaw` en esta etapa;
- que aporta el patron sinusoidal como caso base;
- para que sirvio el modo manual dentro del desarrollo y la depuracion;
- por que el filtro de suavizado mejora la plausibilidad del movimiento.
- en que se diferencia el patron `irregular` del `sinusoidal`.
- que hiperparametros se variaron a lo largo del desarrollo y como impactan en
  la severidad o el caracter del movimiento.

#### Decision ya confirmada

- El patron `irregular` se llego a correr durante el desarrollo, pero el caso
  de referencia del informe va a ser el `sinusoidal`.
- Entonces conviene explicar el `irregular` en terminos metodologicos: rompe la
  periodicidad estricta del caso simple mediante suma de componentes
  sinusoidales, expone al detector a perturbaciones menos regulares y sirvio
  para exploracion y pruebas.
- Tambien conviene explicar por que no quedo como caso principal:
  no estuvo calibrado como modelo fisico de mar y resultaba menos conveniente
  como base reproducible para comparar estimacion y ground truth.

#### Hiperparametros que merecen explicacion explicita

- `wave_frequency`: define la velocidad temporal del oleaje sintetizado.
- `max_roll_deg`, `max_pitch_deg`, `max_heave_m`: fijan la amplitud maxima de
  cada componente y, por lo tanto, la severidad del movimiento.
- `phase_offset_pitch`, `phase_offset_heave`: modifican el desacople temporal
  entre ejes y evitan una oscilacion perfectamente sincronizada.
- `smoothing_factor`: regula cuan brusca o cuan suave resulta la transicion
  entre consignas consecutivas.

En la redaccion final conviene explicar estos parametros no solo como knobs del
simulador, sino como decisiones metodologicas que alteran la dificultad del
problema visual.

#### Configuracion de referencia ya acordada

Para el informe, la configuracion de referencia va a ser la que se usa para
correr la simulacion en el repositorio. Eso permite describir una base
metodologica concreta antes de entrar en variantes.

Con lo relevado en `marine_platform_simulator.py`, esa configuracion base es:

- `rate_hz = 20.0`
- `wave_frequency = 0.1 Hz`
- `max_roll_deg = 15.0`
- `max_pitch_deg = 10.0`
- `max_heave_m = 0.1`
- `phase_offset_pitch = 1.0`
- `phase_offset_heave = 1.5`
- `smoothing_factor = 0.95`

Si mas adelante aparecen corridas finales con otra parametrizacion, esta lista
puede refinarse, pero por ahora conviene tomar estos valores como referencia
editorial y tecnica.

#### Lo que conviene no sobreafirmar

- El README de `go2_tools` todavia menciona `/go2/pose_rphz_cmd`, pero el nodo
  real publica `/body_pose`. Hay que sostener la version consistente con el
  codigo y, si hace falta, mencionar que hubo una nomenclatura anterior.

#### Figura sugerida

- esquema del nodo `marine_platform_simulator` con parametros, modos de
  operacion y publicaciones.

### 3. Control postural del Go2 en simulacion

#### Lo que hoy esta respaldado

- El simulador no mueve el mundo ni una plataforma externa: publica una pose
  deseada del cuerpo.
- La idea general del pipeline es que el Go2 materializa esa pose con su cadena
  articular.
- La reconstruccion del ground truth posterior usa `odom`, `imu/data` y
  `base_to_footprint_pose`.
- El README del proyecto y la metodologia actual dependen del fork
  `unitree-go2-ros2`.

#### Punto critico

El fork `unitree-go2-ros2` no esta en este checkout. Entonces la explicacion de
como `/body_pose` termina en movimiento articular puede sostenerse a nivel
arquitectonico, pero los detalles internos del controlador deberian revisarse
contra esa branch o repo antes de afirmarlos con total seguridad.

#### Lo que conviene explicar mejor

- que significa que el Go2 opere como plataforma marina sintetica;
- como una pose deseada del torso se traduce en una postura del robot;
- por que esta decision preserva consistencia con TF, odometria e IMU;
- por que el ground truth del marcador no es exactamente igual a la pose del
  torso y requiere sumar offsets.

#### Figura sugerida

- esquema del paso `/body_pose` -> controlador del Go2 -> movimiento articular
  -> pose observable del torso y del marcador.

### 4. Estimacion visual en simulacion

#### Lo que hoy esta confirmado por codigo y configs

- Hay dos fuentes de imagen: `fixed_camera` y `sjtu_drone`.
- En ambos casos se usa un nodo `aruco_detector`.
- El detector usa `DICT_6X6_250`, `target_id=0` y `marker_length_m=0.50`.
- Publica `/aruco/pose`, `/aruco/detection` y `/aruco/debug_image`.
- El caso `fixed_camera` modela una camara estatica.
- El caso `sjtu_drone` agrega movimiento propio del sensor.
- El dron se spawnea con offset horizontal, envia `takeoff` automatico y luego
  activa `position control` para mantener un hover nominal.

#### Decision ya confirmada

- `fixed_camera` va a quedar en el informe principalmente para explicar el
  setup base.
- `sjtu_drone` va a llevar el peso metodologico mas fuerte como extension del
  sistema.

#### Inconsistencias a aclarar

- `fixed_camera/aruco_detector_params.yaml` usa
  `/fixed_camera/camera/image_raw` y `/fixed_camera/camera/camera_info`,
  mientras que el nodo por default espera `/fixed_camera/image_raw` y
  `/fixed_camera/camera_info`.
- `fixed_camera.launch.py` permite `height:=...` para el spawn, pero
  `camera_controller.py` sigue leyendo `position_z` desde YAML con default 2.0.
  Eso puede generar desalineacion entre la camara spawneada y la pose publicada
  si se cambio la altura por launch argument.

#### Lo que conviene explicar mejor

- por que la camara fija funciona como caso base visual;
- por que el dron no es "otro experimento cualquiera", sino una extension del
  problema con sensor movil;
- que se estima exactamente en `/aruco/pose`;
- por que el detector no usa conocimiento del simulador durante la corrida.

#### Punto ya aclarado

- En `fixed_camera`, los topics correctos a tomar como referencia del trabajo
  son `/fixed_camera/image_raw` y `/fixed_camera/camera_info`.
- La variante con `/fixed_camera/camera/...` conviene tratarla como una
  inconsistencia heredada de configuracion o de una etapa anterior.

#### Figura sugerida

- comparacion entre `fixed_camera` y `sjtu_drone`, incluyendo altura nominal,
  topicos de imagen y frame de salida de la estimacion.

### 5. Registro y evaluacion offline

#### Lo que hoy esta confirmado

- Existen scripts de grabacion para `marine_sim_*` y `sjtu_drone_sim_*`.
- La evaluacion offline se hace con
  `aruco_relative_pose/scripts/evaluate_realtime_aruco.py`.
- Ese script compara la estimacion guardada en rosbag con ground truth
  reconstruido a partir de `odom`, `imu/data`, `base_to_footprint_pose` y, en
  el caso del dron, su pose.
- El README de `aruco_relative_pose` deja explicito que el offset default
  `world_init_x` es 0.40 m.
- Ya existe al menos un analisis guardado para `sjtu_drone`.
- Las corridas se grabaron como rosbags de un minuto.

#### Inconsistencias o puntos delicados

- Los scripts de grabacion todavia incluyen `/marine_motion`, topic que no
  aparecio en los nodos revisados.
- `marine_robot_dataset` arrastra nomenclaturas de topics mas viejas y necesita
  revisarse antes de usarlo como fuente textual fuerte en el informe.
- No aparecieron analisis versionados del caso `fixed_camera`, por lo que hay
  que confirmar si ese caso tendra resultados cuantitativos o si quedara sobre
  todo como parte del setup metodologico.

#### Lo que conviene explicar mejor

- la separacion entre percepcion online y evaluacion offline;
- por que esa separacion evita contaminar la medicion con informacion
  privilegiada;
- que archivos o artefactos salen de cada corrida;
- que variables alimentan luego la seccion de experimentacion.

#### Figura sugerida

- pipeline completo desde Gazebo hasta los CSV y plots de evaluacion.

## Decision editorial importante

En esta seccion conviene priorizar el caso `simulacion -> registro -> evaluacion`
como hilo principal. El dron y la camara fija pueden entrar como dos fuentes de
imagen dentro del mismo pipeline, en vez de aparecer como mundos separados.
Ademas, conviene presentar a `fixed_camera` como plataforma de arranque y a
`sjtu_drone` como el escenario que empuja el framework hacia el objetivo final
de aterrizaje.

## Preguntas abiertas mas importantes para simulacion

1. Que configuraciones de amplitud, frecuencia y otros hiperparametros quieren
   reportar como corridas principales?
2. Tenes el fork `unitree-go2-ros2` para validar fino la parte del controlador?
3. Si hubo cambios de altura en `fixed_camera`, cuales fueron y en que corridas
   se usaron?
