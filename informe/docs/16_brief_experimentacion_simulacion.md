# Brief de escritura para Experimentos en simulacion

## Funcion de la seccion

`Experimentos en simulacion` deberia responder una pregunta simple:

> que tan bien funciona el pipeline de estimacion visual cuando la plataforma
> marina sintetica se mueve bajo condiciones controladas.

No conviene escribirla como una lista de plots. Conviene contarla como una
historia experimental:

1. que se evaluo;
2. con que corridas;
3. con que metricas;
4. que se observo en el caso base;
5. que cambia cuando la camara pasa a estar sobre el dron.

## Estructura narrativa recomendada

### 1. Apertura corta

Un parrafo breve para recordar:

- que las corridas duran un minuto y se graban en rosbag;
- que la comparacion se hace offline contra ground truth reconstruido;
- que `fixed_camera` entra como baseline y `sjtu_drone` como escenario fuerte.

### 2. Setup experimental

Contar:

- configuracion de movimiento usada como referencia;
- fuente o fuentes de imagen consideradas;
- bags seleccionadas para el informe;
- metricas principales.

Si las corridas definitivas son pocas, conviene nombrarlas.

### 3. Caso base: `fixed_camera`

Esta subseccion no necesita tener el mismo peso que `sjtu_drone`, pero si
deberia dejar claro que:

- con sensor fijo, toda la variacion viene del movimiento del Go2;
- sirve para instalar el baseline visual del framework;
- permite leer con mas limpieza el efecto de `roll`, `pitch` y `heave`.

### 4. Caso fuerte: `sjtu_drone`

Aca deberia ir el mayor peso experimental:

- estimacion vs ground truth;
- distribucion de errores;
- estabilidad temporal;
- comparacion entre corridas si tienen mas de una bolsa final.

### 5. Cierre interpretativo

No repetir numeros. Cerrar con la lectura experimental:

- que se puede afirmar del pipeline;
- que limita la precision;
- por que este resultado alcanza para justificar el framework.

## Metricas que si valen la pena

Con lo que ya existe en el repo, estas metricas son las mas naturales:

- tasa de deteccion;
- duracion efectiva y cantidad de muestras;
- error absoluto por eje en posicion;
- error euclidiano de posicion;
- error angular por eje;
- dispersion temporal del error;
- si quieren, error relativo respecto de la distancia camara-marcador.

## Graficos minimos recomendados

### 1. Baseline visual del setup

No hace falta generarlo si ya alcanza con las figuras del metodo.
Solo usar si despues sienten que el lector llega a `Experimentacion` sin una
imagen clara del escenario.

### 2. `fixed_camera`: estimado vs ground truth en posicion

Grafico recomendado:

- `position_est_vs_gt.png` o equivalente.

Para que sirve:

- mostrar el baseline del caso mas limpio;
- dejar ver si la senal estimada sigue la dinamica general del marcador.

### 3. `fixed_camera`: histograma de errores

Grafico recomendado:

- `error_histograms.png` o, si queda cargado, solo el recorte de errores de
  posicion.

Para que sirve:

- resumir el baseline sin darle demasiado peso a este escenario.

### 4. `sjtu_drone`: estimado vs ground truth en posicion

Grafico recomendado:

- `position_est_vs_gt.png` para la bolsa representativa.

Para que sirve:

- mostrar el comportamiento mas importante del informe;
- dejar ver en que ejes el sistema sigue mejor o peor al GT.

### 5. `sjtu_drone`: estimado vs ground truth en orientacion

Grafico recomendado:

- `orientation_est_vs_gt.png`.

Para que sirve:

- mostrar que `yaw` suele ser mas estable que `roll` y `pitch`;
- conectar con la interpretacion geometrica del marco teorico.

### 6. `sjtu_drone`: distribucion de errores

Grafico recomendado:

- `error_histograms.png`.

Para que sirve:

- condensar sesgo y dispersion;
- visualizar rapido que ejes concentran la mayor incertidumbre.

### 7. Comparacion entre bolsas del dron

Grafico recomendado:

- bar chart o dot plot custom con:
  media de `‖Δpos‖`,
  `P95` de `‖Δpos‖`,
  std de `Δroll`,
  std de `Δpitch`,
  std de `Δyaw`.

Para que sirve:

- comparar sesiones sin inundar el texto con tablas;
- mostrar si una corrida fue claramente mas ruidosa que otra.

Este grafico no sale directo de los scripts actuales. Hay que generarlo a
partir de los CSV o de las tablas resumen.

### 8. Estabilidad temporal del error

Grafico recomendado:

- error euclidiano de posicion en el tiempo, o
- error medio por ventanas temporales.

Para que sirve:

- sostener la discusion sobre drift o ausencia de drift;
- mostrar si el error sube en tramos de mayor oleaje.

Esto puede salir del CSV de `evaluate_realtime_aruco.py`, aunque el script
actual no genera exactamente este plot por ventanas.

### 9. Tabla resumen de bolsas

Mas que grafico, esta tabla es muy util.

Columnas sugeridas:

- bag;
- duracion;
- cantidad de muestras;
- tasa de deteccion;
- media/std/P95/max de `‖Δpos‖`;
- media/std de `Δroll`, `Δpitch`, `Δyaw`.

Para el caso `sjtu_drone`, una tabla asi ya se apoya bastante en
`sjtu_drone_analysis.md`.

## Graficos opcionales

### 10. Scatter `estimado vs GT`

Grafico disponible:

- `scatter_est_vs_gt.png`.

Sirve si quieren reforzar visualmente sesgo o dispersion por eje.
No lo pondria como figura principal salvo que quede especialmente claro.

### 11. Error de reproyeccion

Grafico disponible solo para el pipeline offline tipo dataset:

- `reproj_error.png`.

Solo lo incluiria si van a discutir explicitamente la calidad geometrica de la
deteccion. Para la historia principal del informe no parece imprescindible.

## Que scripts ya generan material util

### Realtime evaluation desde rosbag

Script:

`aruco_relative_pose/scripts/evaluate_realtime_aruco.py`

Salidas:

- `realtime_aruco_evaluation.csv`
- `position_est_vs_gt.png`
- `orientation_est_vs_gt.png`
- `error_histograms.png`

Este script parece el mas alineado con la historia principal del informe porque
evalua exactamente el pipeline realtime contra ground truth reconstruido.

### Analisis desde CSV offline

Script:

`aruco_relative_pose/scripts/analyze_pose_results.py`

Salidas:

- `position_timeseries.png`
- `orientation_timeseries.png`
- `position_errors.png`
- `orientation_errors.png`
- `scatter_est_vs_gt.png`
- `reproj_error.png`

Este camino sirve mas como apoyo o zoom analitico que como columna vertebral de
la seccion.

## Graficos que yo pediria generar primero

Si queres minimizar trabajo y aun asi dejar una seccion fuerte, yo pediria estos:

1. un `position_est_vs_gt.png` de `fixed_camera` para el baseline;
2. un `error_histograms.png` de `fixed_camera`;
3. un `position_est_vs_gt.png` de la mejor bolsa `sjtu_drone`;
4. un `orientation_est_vs_gt.png` de esa misma bolsa;
5. un `error_histograms.png` de esa misma bolsa;
6. una tabla resumen comparando las bolsas `sjtu_drone`;
7. un grafico custom de comparacion entre bolsas del dron.

Con eso ya alcanza para escribir una experimentacion convincente.

## Preguntas abiertas para poder escribirla bien

1. Cuales son exactamente las bolsas definitivas de `sjtu_drone` que queres
   usar en el informe?

2. Tenes una o mas bolsas de `fixed_camera` listas para evaluar?
   Si no, este caso podria quedar mas corto y mas cerca del setup que del
   resultado fuerte.

3. Queremos que `fixed_camera` tenga solo una corrida representativa o tambien
   una mini comparacion cuantitativa?

4. Como queres nombrar narrativamente las dos bolsas del dron?
   Por ejemplo: `corrida A/B`, `sesion 1/2`, `oleaje moderado/fuerte`, etc.

5. Queres que la tasa de deteccion aparezca explicitamente como metrica en el
   texto principal o solo en una tabla?
