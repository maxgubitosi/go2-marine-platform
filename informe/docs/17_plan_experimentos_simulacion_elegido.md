# Plan elegido para Experimentos en simulacion

## Criterio general

Como criterio editorial y experimental, conviene mantener la experimentacion lo
mas simple y defendible posible:

- una configuracion de movimiento de referencia, que ya esta bien explicada en
  Metodologia;
- un caso base con `fixed_camera`, para mostrar el escenario visual mas limpio;
- dos corridas con `sjtu_drone`, para que el escenario fuerte tenga repeticion
  y no dependa de una sola bolsa.

No hace falta abrir demasiadas variantes de hiperparametros en esta etapa. Para
la tesis, es mas fuerte una historia clara y consistente que una bateria muy
grande de corridas poco integradas.

## Corridas que yo elegiria

### Corrida 1: baseline con `fixed_camera`

Objetivo:

- instalar el caso base visual;
- mostrar que con camara fija la variacion proviene del movimiento del Go2;
- dejar un punto de comparacion limpio antes de pasar al dron.

Configuracion:

- fuente de imagen: `fixed_camera`
- duracion: `60 s`
- movimiento: configuracion por defecto del simulador
- nombre sugerido de bolsa: `marine_sim_ref_fixed`

### Corrida 2: escenario fuerte con `sjtu_drone`

Objetivo:

- evaluar el pipeline en el caso que mas se parece al objetivo final del
  framework;
- cuantificar error con camara movil.

Configuracion:

- fuente de imagen: `sjtu_drone`
- duracion: `60 s`
- movimiento: configuracion por defecto del simulador
- nombre sugerido de bolsa: `sjtu_drone_sim_ref_a`

### Corrida 3: repeticion del caso `sjtu_drone`

Objetivo:

- mostrar que el comportamiento observado no depende de una sola ejecucion;
- sostener un comentario de estabilidad o variabilidad entre sesiones.

Configuracion:

- fuente de imagen: `sjtu_drone`
- duracion: `60 s`
- movimiento: configuracion por defecto del simulador
- nombre sugerido de bolsa: `sjtu_drone_sim_ref_b`

## Por que esta eleccion es coherente

Esta seleccion mantiene una sola variable metodologica fuerte por vez:

- primero se compara sensor fijo vs sensor movil;
- despues, dentro del caso movil, se observa repetibilidad.

Si ademas se cambian amplitudes, frecuencias o varios hyperparametros en la
misma tanda, el relato se vuelve mas dificil de leer y mas dificil de defender.
Eso se puede dejar para trabajo futuro o para una extension posterior del
analisis.

## Outputs minimos a generar por corrida

### Desde `evaluate_realtime_aruco.py`

Para cada rosbag conviene generar:

- `realtime_aruco_evaluation.csv`
- `position_est_vs_gt.png`
- `orientation_est_vs_gt.png`
- `error_histograms.png`

## Graficos que efectivamente pondria en el informe

### Figura 1. Baseline `fixed_camera`: posicion estimada vs ground truth

Archivo sugerido:

- `fixed_camera_position_est_vs_gt.png`

Que deberia mostrar:

- series temporales de `X`, `Y`, `Z` estimadas y GT.

Para que sirve:

- mostrar el comportamiento del baseline;
- dejar ver que con sensor fijo la estructura del movimiento es facil de seguir.

### Figura 2. Baseline `fixed_camera`: distribucion de errores

Archivo sugerido:

- `fixed_camera_error_histograms.png`

Que deberia mostrar:

- histogramas de error en posicion y, si queda claro, orientacion.

Para que sirve:

- resumir el baseline sin cargar de figuras el caso fijo.

### Figura 3. `sjtu_drone`: posicion estimada vs ground truth

Archivo sugerido:

- `sjtu_drone_ref_a_position_est_vs_gt.png`

Que deberia mostrar:

- series temporales de `X`, `Y`, `Z` estimadas y GT en la corrida principal.

Para que sirve:

- instalar el resultado fuerte del informe.

### Figura 4. `sjtu_drone`: orientacion estimada vs ground truth

Archivo sugerido:

- `sjtu_drone_ref_a_orientation_est_vs_gt.png`

Que deberia mostrar:

- series temporales de `roll`, `pitch`, `yaw` estimados y GT.

Para que sirve:

- dejar claro que `yaw` suele ser mas estable que `roll` y `pitch`.

### Figura 5. `sjtu_drone`: distribucion de errores

Archivo sugerido:

- `sjtu_drone_ref_a_error_histograms.png`

Que deberia mostrar:

- histogramas de error de posicion y orientacion de la corrida principal.

Para que sirve:

- condensar sesgo y dispersion sin saturar el texto con tablas largas.

### Figura 6. Comparacion entre corridas del dron

Archivo sugerido:

- `sjtu_drone_runs_comparison.png`

Este grafico hay que construirlo aparte a partir de los CSV o de las tablas
resumen. No sale listo del script actual.

Que deberia mostrar:

- media de `‖Δpos‖`
- `P95` de `‖Δpos‖`
- std de `Δroll`
- std de `Δpitch`
- std de `Δyaw`

Para que sirve:

- comparar las dos corridas fuertes de manera compacta;
- sostener visualmente si una fue mas ruidosa o mas estable.

### Figura 7. Estabilidad temporal del error del dron

Archivo sugerido:

- `sjtu_drone_ref_a_error_over_time.png`

Opciones validas:

- error euclidiano `‖Δpos‖` en funcion del tiempo;
- media de `‖Δpos‖` por ventanas temporales;
- si queres repetir el analisis, ambas corridas en el mismo grafico.

Para que sirve:

- apoyar la discusion sobre drift o ausencia de drift;
- mostrar si el error sube en tramos de mayor exigencia del movimiento.

## Tablas que si pondria

### Tabla 1. Resumen de corridas

Columnas sugeridas:

- corrida
- fuente de imagen
- duracion
- cantidad de muestras
- tasa de deteccion

### Tabla 2. Resumen cuantitativo del dron

Columnas sugeridas:

- corrida
- media de `‖Δpos‖`
- std de `‖Δpos‖`
- `P95` de `‖Δpos‖`
- max de `‖Δpos‖`
- media/std de `Δroll`
- media/std de `Δpitch`
- media/std de `Δyaw`

Esta tabla puede apoyarse directamente en el tipo de resumen que ya aparece en
`sjtu_drone_analysis.md`.

## Lo que no pondria salvo que quede especialmente fuerte

- `scatter_est_vs_gt.png`
- `reproj_error.png`
- demasiados plots del caso `fixed_camera`

No porque sean malos, sino porque no parecen centrales para la historia que
queremos contar.

## Orden sugerido de generacion

1. generar una corrida `fixed_camera` de referencia;
2. evaluarla con `evaluate_realtime_aruco.py`;
3. generar dos corridas `sjtu_drone`;
4. evaluarlas con `evaluate_realtime_aruco.py`;
5. exportar las cinco figuras principales;
6. construir el grafico comparativo entre corridas del dron;
7. armar las tablas resumen.

## Comandos orientativos

### Baseline `fixed_camera`

```bash
./rosbags/record_marine_simulation.sh 60
python3 aruco_relative_pose/scripts/evaluate_realtime_aruco.py rosbags/<bag_fixed>
```

### Caso fuerte `sjtu_drone`

```bash
./rosbags/record_sjtu_drone_simulation.sh 60 ref_a
python3 aruco_relative_pose/scripts/evaluate_realtime_aruco.py rosbags/<bag_drone_a>

./rosbags/record_sjtu_drone_simulation.sh 60 ref_b
python3 aruco_relative_pose/scripts/evaluate_realtime_aruco.py rosbags/<bag_drone_b>
```

## Traduccion a narrativa del informe

Si estas corridas se generan, la seccion `Experimentos en simulacion` puede
escribirse de forma muy limpia:

1. baseline con camara fija;
2. evaluacion principal con dron;
3. comparacion entre corridas del dron;
4. interpretacion general del pipeline.

Ese orden conversa bien con todo lo que ya venimos construyendo en `Metodo`.
