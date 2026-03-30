# Checklist para la ultima visita al laboratorio

Este documento esta pensado como guia operativa. La idea es simple: si juntas
este material, despues podemos cerrar la parte de laboratorio del informe sin
huecos grandes.

## Objetivo del dia

Salir del laboratorio con evidencia suficiente para completar:

- la descripcion final del setup real;
- la figura del montaje de laboratorio;
- la comparacion temporal entre movimiento esperado, comando y respuesta;
- una discusion honesta del pasaje de simulacion a laboratorio;
- al menos una corrida real util que permita escribir resultados sin inventar.

## Lo minimo que no puede faltar

Si el tiempo se complica, priorizar esto:

1. una foto clara del setup completo;
2. una foto del ArUco montado en el lomo;
3. una foto de la camara mostrando que se uso un solo lado de la stereo;
4. una captura o archivo de la calibracion intrinseca usada;
5. una corrida real de 60 s con la consigna sinusoidal de referencia;
6. una segunda corrida real de 60 s igual a la anterior para repeticion;
7. un rosbag que guarde al menos referencia, comando, estado del robot e
   imagenes;
8. una nota escrita con todos los parametros y observaciones del ensayo.

## Configuracion de referencia a replicar

Para que el relato simulacion -> laboratorio quede prolijo, conviene usar la
misma configuracion base del simulador marino:

- `rate_hz = 20.0`
- `wave_frequency = 0.1`
- `max_roll_deg = 15.0`
- `max_pitch_deg = 10.0`
- `max_heave_m = 0.1`
- `phase_offset_pitch = 1.0`
- `phase_offset_heave = 1.5`
- `smoothing_factor = 0.95`
- `wave_pattern = sinusoidal`

Si en el robot real ajustan algo por seguridad o porque la plataforma no
responde igual, no pasa nada, pero hay que dejarlo anotado.

## Antes de arrancar

1. Confirmar que el ArUco este bien pegado y plano sobre el lomo.
2. Medir o anotar el lado fisico del ArUco en metros.
3. Confirmar que la camara usada sea siempre el mismo lado de la stereo.
4. Guardar o fotografiar la calibracion intrinseca usada.
5. Verificar los topics de imagen y `camera_info` del lado elegido.
6. Verificar que la corrida se hara con el pipeline real de
   `marine_platform_simulator` en `mode=real`, o anotar cualquier variante.
7. Confirmar que se van a registrar `debug_state`, el comando API y al menos
   una senal fuerte de estado del robot.
8. Verificar que la hora del sistema y los timestamps ROS sean consistentes.

## Topics minimos para grabar en el rosbag

Si cambia algun nombre exacto, anotalo. Lo importante es guardar este tipo de
senal:

- `/marine_platform/debug_state`
- `/api/sport/request`
- `/sportmodestate`
- `/lowstate`
- `/utlidar/robot_odom`
- `/tf`
- `/tf_static`
- `/stereo_camera/image_raw`
- `/stereo_camera/camera_info`

Muy recomendados si estan disponibles:

- `/aruco/pose`
- `/aruco/detection`
- `/aruco/debug_image`
- `/imu/data` o la IMU equivalente del robot

Si el detector ArUco no corre en tiempo real, no es grave. Lo importante es no
irte sin la imagen cruda y `camera_info`, porque despues podemos reprocesar.

## Corridas obligatorias

### Corrida 0. Verificacion estatica

Duracion sugerida: `15-20 s`

Objetivo:

- chequear foco, exposicion, encuadre y deteccion del ArUco;
- tener una referencia de ruido visual con el robot quieto;
- verificar que el bag realmente guarda todo.

Nombre sugerido:

- `lab_static_ref_01`

### Corrida 1. Referencia real principal

Duracion sugerida: `60 s`

Objetivo:

- reproducir la consigna sinusoidal de referencia;
- obtener la corrida principal para la figura `objetivo -> comando -> respuesta`;
- dejar una corrida base para resultados.

Nombre sugerido:

- `lab_real_ref_01`

### Corrida 2. Repeticion de referencia

Duracion sugerida: `60 s`

Objetivo:

- mostrar que la respuesta no depende de una sola toma;
- tener material por si la corrida principal sale mal;
- poder hablar de repetibilidad minima.

Nombre sugerido:

- `lab_real_ref_02`

## Corridas recomendadas si el tiempo alcanza

### Corrida 3. Tercera repeticion

Duracion sugerida: `60 s`

Nombre sugerido:

- `lab_real_ref_03`

### Corrida 4. Variante mas suave

Solo si el robot responde bien y no complica la jornada.

Objetivo:

- tener un caso real mas limpio para comparar amplitud y seguimiento.

Nombre sugerido:

- `lab_real_soft_01`

### Corrida 5. Variante mas exigente

Solo si es seguro y no arriesga la toma principal.

Objetivo:

- explorar si la respuesta se deteriora al exigir mas amplitud o frecuencia.

Nombre sugerido:

- `lab_real_strong_01`

### Corrida 6. Heave dedicado

Solo si es seguro y si quieren cerrar el hueco que hoy queda en la evidencia
real versionada.

Objetivo:

- registrar una prueba donde exista componente vertical dinamica efectiva;
- poder discutir heave real sin confundir altura absoluta del tronco con heave
  oscilatorio.

Nombre sugerido:

- `lab_real_heave_01`

## Fotos y videos obligatorios

Estas imagenes te cierran varias figuras del informe de una vez:

1. foto general del setup desde un lateral o diagonal;
2. foto cenital o semicenital mostrando la geometria camara-Go2-ArUco;
3. primer plano del ArUco en el lomo;
4. primer plano de la camara stereo, marcando que se uso un solo lado;
5. si podes, una captura del frame con deteccion y ejes dibujados;
6. un video corto del ensayo real, aunque sea con celular.

## Medidas y notas que hay que anotar en el momento

No confiar en la memoria. Guardar en un txt o notas del celu:

- fecha y hora de cada corrida;
- nombre exacto del rosbag;
- lado de la stereo usado;
- resolucion de imagen usada;
- distancia aproximada camara-ArUco;
- altura aproximada de la camara respecto del robot;
- tamano fisico del ArUco;
- si la camara estaba montada, apoyada o sostenida y con que tipo de soporte;
- si hubo recalibracion o se uso una calibracion previa;
- cualquier problema visible: blur, cambio de luz, perdida de deteccion,
  desalineacion, vibracion, retraso, saturacion.

## Verificaciones despues de cada corrida

Antes de grabar la siguiente:

1. correr `ros2 bag info <bag>`;
2. chequear que el bag tenga imagenes;
3. chequear que el bag tenga `/marine_platform/debug_state`;
4. chequear que el bag tenga `/api/sport/request`;
5. chequear que el bag tenga al menos una de estas:
   `/sportmodestate`, `/lowstate`, `/utlidar/robot_odom`;
6. chequear que el bag tenga `camera_info`;
7. guardar una nota corta de si esa corrida sirve o no.

No te vayas del laboratorio sin abrir al menos un bag y confirmar que realmente
quedo grabado lo importante.

## Que material desbloquea cada parte del informe

- Foto general del setup:
  figura del montaje real y descripcion fina del laboratorio.
- Foto del ArUco y de la camara:
  parrafo de instrumentacion y pasaje de simulacion a entorno real.
- Calibracion guardada:
  justificacion metodologica de la estimacion visual en laboratorio.
- Corridas `ref_01` y `ref_02`:
  figura `objetivo -> comando -> respuesta` y subseccion de resultados reales.
- Corrida estatica:
  comentario sobre ruido base y chequeo de deteccion.
- Corrida `heave_01`, si existe:
  permite sostener o descartar una discusion especifica sobre heave real.
- Video corto:
  apoyo visual para defensa, anexos o figura comparativa.

## Si solo podes hacer una cosa extra

Hacer una tercera corrida de referencia y sacar mejores fotos del setup. Eso
vale mucho mas para el informe que abrir diez variantes de parametros.

## Entregable ideal al volver

Idealmente deberias volver con:

- `2-3` rosbags buenos de referencia;
- `1` rosbag estatico de chequeo;
- `4-6` fotos utiles;
- `1` video corto;
- `1` archivo o captura de calibracion;
- `1` nota con parametros y observaciones por corrida.

Con eso deberiamos poder cerrar la parte de laboratorio del informe sin tener
que inventar nada importante.
