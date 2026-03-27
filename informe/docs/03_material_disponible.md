# Material disponible para escribir

## Figuras ya disponibles dentro del informe

En `informe/figures/` hoy existen:

- `setup/logoudesa.jpg`
- `setup/unitree-aruco.png`
- `setup/drone-unitree-aruco.png`
- `images/aruco_id0_dict_6x6_250.png`
- `images/aruco_detection_frame.png`

Estas figuras ya alcanzan para sostener:

- descripcion del setup simulado;
- presentacion del marcador;
- ejemplo de deteccion en tiempo real.

## Assets reutilizables fuera de `informe/`

En `docs/media/` hay material que probablemente podamos migrar o reutilizar en
el informe:

- `unitree-aruco.png`
- `drone-unitree-aruco.png`
- `aruco_detection_realtime.gif`
- `aruco_detection_frame.png`
- `position_timeseries.png`
- `orientation_timeseries.png`
- `position_errors.png`
- `scatter_est_vs_gt.png`
- `drone_position_est_vs_gt.png`
- `drone_orientation_est_vs_gt.png`
- `drone_error_histograms.png`

## Resultados ya respaldados por outputs

Existe un analisis escrito en:

- `aruco_relative_pose/outputs/analysis/sjtu_drone_analysis.md`

Ese archivo documenta al menos dos corridas del caso `sjtu_drone` y reporta,
entre otras cosas:

- error euclidiano medio de posicion del orden de `0.068 m` y `0.078 m`;
- error relativo medio de posicion del orden de `2.5%` a `2.9%`;
- muy buena precision en yaw;
- mayor dispersion en roll y pitch;
- ausencia de drift acumulativo apreciable.

Esto es material util para la subseccion experimental de simulacion, siempre que
ustedes confirmen:

- que esas son las corridas que quieren mostrar;
- que no hubo corridas mejores o mas representativas;
- que los numeros de ese analisis forman parte de la narrativa final.

## Material que no encontre en el repo

- rosbags crudos versionados;
- datasets extraidos versionados;
- plots equivalentes para el caso de camara fija;
- tablas finales listas para LaTeX;
- esquema/diagrama del pipeline ya dibujado;
- explicacion escrita de por que se eligieron esos bags concretos.

## Candidatos concretos para la seccion de experimentacion

### Setup

- imagen del Go2 con ArUco;
- imagen del dron sobre la plataforma;
- tabla corta con configuracion de cada fuente de camara.

### Resultados

- serie temporal posicion estimada vs GT;
- serie temporal orientacion estimada vs GT;
- histogramas de error;
- tabla resumen con media, desvio, P95 y maximo.

### Texto que conviene agregar cuando lo validemos

- criterio de seleccion de las corridas;
- duracion de cada experimento;
- intensidad del oleaje usada en cada caso;
- frecuencia de deteccion efectiva del sistema;
- limitaciones observadas en profundidad y orientacion.
