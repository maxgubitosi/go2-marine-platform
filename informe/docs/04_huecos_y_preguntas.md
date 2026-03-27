# Huecos detectados y preguntas para completar el informe

## Inconsistencias o puntos a validar antes de escribir mas

1. `unitree-go2-ros2` no esta presente en `src/` en este checkout, pero el
   README y el metodo dependen de ese stack para explicar como `/body_pose`
   termina moviendo el torso del Go2.
2. `src/fixed_camera/config/aruco_detector_params.yaml` apunta a
   `/fixed_camera/camera/image_raw` y `/fixed_camera/camera/camera_info`,
   mientras que el README y el codigo del detector usan por defecto
   `/fixed_camera/image_raw` y `/fixed_camera/camera_info`.
3. `fixed_camera.launch.py` recibe `height:=...` para el spawn en Gazebo, pero
   `camera_controller.py` sigue leyendo `position_z` desde YAML con default `2.0`.
   Si alguna vez cambiaron la altura por launch argument, la pose publicada por
   el controlador pudo quedar desalineada con el spawn real.
4. `marine_robot_dataset/extract_dataset.py` escucha `/drone/camera/image_raw`,
   pero los scripts y launch actuales del dron trabajan con
   `/drone/bottom/image_raw`. Esto parece legado o una etapa anterior del
   proyecto.
5. Los scripts de grabacion incluyen `/marine_motion`, pero ese topic no aparece
   en los nodos revisados.
6. Solo encontre analisis versionado para `sjtu_drone`. No encontre resultados
   guardados del caso `fixed_camera`.
7. La bibliografia actual solo contiene dos entradas de OpenCV. Falta respaldo
   bibliografico para la parte marina y para control/cinematica del cuadrupedo.

## Alcance ya aclarado por el usuario

Quedo confirmado que la tesis debe contar una progresion completa:

1. construccion del entorno de simulacion;
2. evaluacion visual en simulacion con camara fija;
3. evaluacion visual en simulacion con dron;
4. validacion en laboratorio del movimiento propuesto;
5. estimacion visual en entorno real con camara sostenida en posicion fija;
6. comparacion entre movimiento propuesto y odometria real del cuadrupedo.

Esto reduce una duda importante: la historia del informe deberia ser
principalmente cronologica, no solo una descripcion estatica del pipeline final.

## Preguntas sobre el alcance de la tesis

1. Ya quedo claro que el objetivo macro es habilitar pruebas de aterrizaje de
   drones en plataformas marinas. Dentro de ese objetivo, cual queres destacar
   mas como aporte inmediato de la tesis:
   framework de simulacion, estimacion visual, o correlacion simulacion-real?
2. La parte del dron debe presentarse como extension natural del caso de camara
   fija o como segundo escenario experimental con entidad propia?
3. El cierre de la tesis va a estar mas apoyado en la calidad de la estimacion
   visual o en la validacion del movimiento marino sintetizado como paso previo
   al aterrizaje?

## Preguntas sobre el pipeline del Go2

4. Tenes en otra branch o repo el fork `unitree-go2-ros2` que realmente usan?
   Si si, necesito ese material para validar todo lo que hoy el metodo afirma
   sobre CHAMP, IK, `quadruped_controller_node` y `state_estimation_node`.
5. El offset del marcador respecto del trunk (`0.091 m`) esta confirmado por el
   modelo real que usaron o fue un ajuste del script de evaluacion?
6. El Go2 efectivamente se spawneaba siempre con `world_init_x = 0.40 m` en las
   corridas usadas para el informe, o eso cambio entre sesiones?
7. El patron `irregular` se uso en experimentos reales del trabajo o quedo solo
   como herramienta de testing y debugging?

## Preguntas sobre las camaras y topics

8. En la camara fija, cuales eran los topics reales que usaban en las corridas:
   `/fixed_camera/image_raw`, `/fixed_camera/camera_info`, o la variante con
   `/fixed_camera/camera/...`?
9. Alguna vez corrieron la camara fija a otra altura distinta de `2.0 m`? Si si,
   necesito saber como garantizaban coherencia entre el spawn y la pose
   publicada.
10. El script `marine_robot_dataset` pertenece a una etapa anterior con otra
    nomenclatura de topics, o sigue siendo parte del workflow real del proyecto?

## Preguntas sobre experimentacion y resultados

11. Que experimentos quieren mostrar si o si en el informe?
12. Tienen resultados comparables entre `fixed_camera` y `sjtu_drone`, o el
    caso fuerte del informe termina siendo solo `sjtu_drone`?
13. Las bolsas analizadas en `sjtu_drone_analysis.md` son las definitivas o solo
    ejemplos preliminares?
14. Tienen mas analisis, notebooks, CSVs o capturas que no hayan quedado
    versionados en el repo?
15. Como definieron las condiciones de oleaje usadas en cada corrida:
    amplitud, frecuencia, tiempo de estabilizacion, duracion total?
16. Midieron tasa de deteccion, frames perdidos o reprojection error en los
    experimentos que quieren reportar?

## Preguntas sobre narrativa y decisiones de proyecto

17. Hubo cambios de enfoque importantes durante la tesis que quieran contar,
    por ejemplo pasar de dataset offline a evaluacion realtime, o de camara fija
    a dron?
18. Hubo decisiones que tomaron por limitaciones practicas y que valga la pena
    dejar explicitadas, como problemas de calibracion, drift del dron, o limites
    del simulador?
19. Hay cosas que hicieron y quieren que aparezcan aunque hoy no esten en el
    codigo, por ejemplo pruebas descartadas, comparaciones que no funcionaron o
    hallazgos cualitativos?

## Preguntas sobre la parte real

20. Que existe exactamente en la branch `real`: deteccion, bags, videos, tablas,
    pruebas de laboratorio, o una integracion parcial?
21. El movimiento "propuesto" que quieren correlacionar con el real es
    especificamente la consigna publicada a `/body_pose`, o alguna otra señal
    intermedia?
22. Para esa correlacion, compararon amplitud y frecuencia, series temporales
    alineadas, correlacion estadistica, o solo inspeccion visual?
23. La camara del laboratorio estaba calibrada formalmente o fue una camara
    fija ad hoc para validar cualitativamente la pose?
24. Quieren que en esta etapa dejemos solo placeholders para la parte real, o ya
    conviene relevar esa branch y preparar la futura subseccion?

## Preguntas sobre figuras, tablas y material externo

25. Tienen diagramas, capturas, fotos de laboratorio o tablas fuera del repo que
    quieran incorporar al informe?
26. Tienen alguna figura favorita que consideren "obligatoria" para defender la
    tesis?
27. Quieren que produzca yo los plots finales en formato para LaTeX a partir de
    los scripts existentes, o primero prefieren validar que corridas usar?

## Bibliografia pendiente minima

Antes de cerrar el marco teorico necesito, como minimo, una referencia para cada
uno de estos bloques:

- movimiento marino y 6 GDL;
- cinematica/control postural de cuadrupedos;
- si quieren, una referencia de pose estimation con fiduciales mas alla de la
  documentacion de OpenCV.

Si ustedes ya tienen papers o fuentes "canonicas" para estas partes, pasamelas y
las integro en la bibliografia del informe.
