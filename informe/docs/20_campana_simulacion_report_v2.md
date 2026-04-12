# Campana de simulacion comparable `report_v2`

Este documento resume la campana nueva de simulacion comparable armada para
cerrar la subseccion de experimentacion en simulacion. La idea es dejar
trazabilidad de las corridas oficiales, de los cambios introducidos en el
pipeline de generacion de figuras y de los problemas que siguen abiertos antes
de volcar los resultados a `informe/main.tex`.

## Bags oficiales de la campana

Se fijaron cuatro bolsas oficiales bajo el mismo perfil experimental
`report_sim_v2`:

- `rosbags/marine_sim_20260410_155332_report_v2_ref`
- `rosbags/sjtu_drone_sim_20260410_155834_report_v2_r1`
- `rosbags/sjtu_drone_sim_20260410_160419_report_v2_r2`
- `rosbags/sjtu_drone_sim_20260410_160814_report_v2_r3`

En los cuatro casos se guardo `experiment_manifest.yaml` dentro del rosbag. Los
manifests confirman:

- mismo commit base: `665092fd241e7567bcb068e84b6e36c1ee30e3b3`;
- mismo `world_init_x=0.4` y `world_init_y=0.0`;
- mismo perfil marino sinusoidal;
- misma duracion objetivo de medicion (`60 s`);
- mismo setup del dron para `r1`, `r2` y `r3`.

La campana, por lo tanto, ya es comparable en configuracion. Las diferencias
que aparecen en los resultados no se deben a una mezcla de implementaciones
viejas sino al comportamiento actual del pipeline.

## Cambios implementados para esta campana

Se agregaron o ajustaron estos componentes:

- `rosbags/report_sim_campaign.yaml`: perfil congelado `report_sim_v2`.
- `rosbags/run_report_simulation_campaign.py`: orquestador unico para grabar
  cada corrida con manifest y validacion basica.
- `rosbags/wait_for_drone_ready.py`: espera de readiness del dron antes de
  grabar.
- `src/fixed_camera/fixed_camera/aruco_detector.py` y
  `src/sjtu_drone/sjtu_drone_control/sjtu_drone_control/aruco_detector.py`:
  fallback a `solvePnP` para entornos donde OpenCV no expone
  `estimatePoseSingleMarkers`.
- `informe/scripts/generate_simulation_artifacts.py`: soporte para multiples
  corridas de dron y lectura de `experiment_manifest.yaml`.

## Cambios recientes en las figuras del informe

Despues de inspeccionar los primeros artefactos, se ajusto
`informe/scripts/generate_simulation_artifacts.py` para que:

- las figuras `sim_fixed_position_vs_gt.png` y `sim_drone_position_vs_gt.png`
  se exporten sin el bias medio por eje;
- el resumen numerico y los histogramas sigan guardando los errores crudos, sin
  correccion;
- se agregue `sim_fixed_angle_error_hist_raw.png` con histogramas raw de
  `Δpitch` y `Δyaw` para el baseline fijo;
- el CSV `simulation_metrics_summary.csv` incorpore tambien
  `slope_err_y_mm_s`, util para describir la deriva lenta observada en `Y`.
- las figuras finales queden limpias para LaTeX: sin titulo global y sin notas
  al pie incrustadas dentro de la imagen.
- la figura comparativa entre `R1`, `R2` y `R3` se centre en error angular, no
  en dinamica temporal ni en posicion.

La correccion de bias se usa solo para visualizacion. Sirve para comparar forma
y fase entre estimacion y ground truth sin esconder que el error bruto tiene
offset. Los numeros de tablas deben seguir saliendo de los CSV crudos.

## Notas editoriales para mover a LaTeX

Como las figuras exportadas ya no incluyen titulos ni notas al pie, estas
aclaraciones deben aparecer en las captions o en el parrafo que introduce cada
figura en `main.tex`:

- `sim_fixed_position_vs_gt.png`: la posicion estimada se muestra sin bias
  medio por eje, solo para visualizacion. El bias removido fue
  `ΔX=0.006 m`, `ΔY=-0.041 m`, `ΔZ=-0.034 m`.
- `sim_drone_position_vs_gt.png`: la posicion estimada se muestra sin bias
  medio por eje, solo para visualizacion. En la corrida principal `R2`, el
  bias removido fue `ΔX=0.037 m`, `ΔY=-0.297 m`, `ΔZ=0.008 m`.
- `sim_drone_orientation_vs_gt.png`: en `roll` se aplico `unwrap` angular solo
  para visualizacion, para evitar saltos artificiales en `±180°`.
- `sim_fixed_angle_error_hist_raw.png`: el histograma es raw; no tiene
  correccion visual ni recentrado.
- `sim_drone_runs_comparison.png`: resume las tres corridas `R1`, `R2` y `R3`
  con boxplots de error absoluto en las variables de mayor interes para el
  informe: `|Δroll|`, `|Δpitch|` y `|Δheave| = |ΔZ|`.

El criterio editorial recomendado es:

- usar la caption para explicar que muestra la figura y por que importa;
- mover las aclaraciones tecnicas de visualizacion al final de la caption o al
  parrafo inmediato posterior;
- evitar repetir en la imagen informacion que ya va a quedar mejor presentada
  por LaTeX.

## Inventario de figuras exportadas

Estos son los artefactos finales en `informe/figures/results/` y el uso
recomendado de cada uno al redactar:

- `sim_fixed_position_vs_gt.png`: baseline fijo; sirve para mostrar la forma
  temporal de `X`, `Y`, `Z` y discutir sesgo visual sin bias medio.
- `sim_fixed_error_hist.png`: baseline fijo; resume el error crudo de posicion
  (`ΔX`, `ΔY`, `ΔZ`, `||Δpos||`).
- `sim_fixed_angle_error_hist_raw.png`: baseline fijo; aporta el error angular
  raw de `Δpitch` y `Δyaw`.
- `sim_drone_position_vs_gt.png`: corrida principal `R2`; sirve para mostrar
  forma temporal de `X`, `Y`, `Z` en el escenario con dron, sin bias medio.
- `sim_drone_orientation_vs_gt.png`: corrida principal `R2`; sirve para leer
  `roll`, `pitch`, `yaw`, con `unwrap` en `roll` solo para visualizacion.
- `sim_drone_error_hist.png`: corrida principal `R2`; resume errores crudos de
  posicion y orientacion.
- `sim_drone_runs_comparison.png`: comparacion entre `R1`, `R2` y `R3`; es la
  figura recomendada para justificar que hubo tres repeticiones comparables y
  que la comparacion central del informe se apoya en `roll`, `pitch` y
  `heave/ΔZ`.
- `sim_drone_error_time.png`: corrida principal `R2`; solo usar si se quiere
  discutir estabilidad temporal del error de posicion. No es una figura central
  si el foco del capitulo queda puesto en la parte angular y en heave.
- `simulation_metrics_summary.csv`: fuente numerica de tablas y cifras
  agregadas.
- `simulation_temporal_summary.csv`: resumen por ventanas de la corrida
  principal; usar solo si se redacta una subseccion sobre estabilidad temporal.

## Resultados crudos de referencia

### Baseline fijo

Para `marine_sim_20260410_155332_report_v2_ref`:

- `mean(||Δpos||) = 0.0578 m`
- `std(||Δpos||) = 0.0171 m`
- `mean(ΔX) = 0.0060 m`
- `mean(ΔY) = -0.0414 m`
- `mean(ΔZ) = -0.0337 m`
- `std(Δroll) = 2.81°`
- `std(Δpitch) = 2.21°`
- `std(Δyaw) = 0.20°`

Este caso sigue siendo el mejor punto de apoyo para la narrativa del informe:
el error absoluto es bajo y la componente angular mas estable es `yaw`.

### Dron SJTU

Para las tres repeticiones comparables:

- `r1`: `mean(||Δpos||) = 0.3351 m`, `mean(ΔY) = -0.3223 m`
- `r2`: `mean(||Δpos||) = 0.3011 m`, `mean(ΔY) = -0.2967 m`
- `r3`: `mean(||Δpos||) = 0.1706 m`, `mean(ΔY) = -0.1513 m`

La componente angular mas estable vuelve a ser `yaw` en las tres corridas, con
`σ` alrededor de `0.21°`. El problema dominante no es angular sino posicional,
especialmente sobre `Y`.

Sin embargo, para la narrativa del informe conviene jerarquizar como variables
principales `roll`, `pitch` y `heave (Z)`, porque son las componentes mas
vinculadas al movimiento marino que se quiso emular. Por eso la figura
comparativa entre corridas del dron se reorientó a `|Δroll|`, `|Δpitch|` y
`|ΔZ|`, en lugar de centrarse en `yaw` o en error euclidiano de posicion.

## Analisis del drift en `Y`

La figura de posicion del baseline fijo sugiere que `Y` cae lentamente con el
tiempo. Los numeros confirman que esa percepcion es real, pero muestran tambien
que no se explica por una deriva equivalente del ground truth.

### Cuantificacion

En `marine_sim_20260410_155332_report_v2_ref`:

- pendiente de `est_y`: `-0.643 mm/s`
- pendiente de `gt_y`: `+0.068 mm/s`
- pendiente de `err_y`: `-0.710 mm/s`
- pendiente de `err_pos`: `+0.548 mm/s`

Entre los primeros `10 s` y el tramo final (`t_rel > 45 s`), el error medio en
`Y` pasa de aproximadamente `-0.0247 m` a `-0.0571 m`.

En el escenario con dron aparece el mismo signo:

- `r1`: pendiente de `err_y = -0.276 mm/s`
- `r2`: pendiente de `err_y = -0.324 mm/s`
- `r3`: pendiente de `err_y = -0.297 mm/s`

Esto sugiere un efecto comun al pipeline de estimacion y evaluacion, no un
problema aislado de una sola corrida.

### Lectura tecnica

En el baseline fijo, `err_y` correlaciona mucho mas con el estado lateral del
cuerpo y con la pose estimada que con el `ground truth` relativo del marcador:

- `corr(err_y, trunk_x) = 0.789`
- `corr(err_y, trunk_y) = 0.756`
- `corr(err_y, est_y) = 0.777`
- `corr(err_y, gt_z) = 0.155`
- `corr(err_y, gt_pitch) = -0.019`

La interpretacion mas razonable es la siguiente:

- el marcador no esta mostrando una deriva lateral fuerte en el ground truth;
- el estimador introduce un sesgo en `Y` que cambia lentamente con la geometria
  observada y con la actitud del cuerpo;
- ese sesgo se manifiesta tanto en camara fija como en dron, por lo que el
  origen probable esta en la cadena comun de pose relativa:
  deteccion ArUco, solvePnP, definicion de frames o extrinsecos usados en la
  evaluacion offline.

Todavia no esta aislado el origen exacto. Lo que si queda respaldado por los
datos es que no conviene describir la "caida" de `Y` como un movimiento real de
la plataforma: es, sobre todo, una deriva del error de estimacion.

## Estado para la redaccion del informe

Con esta campana ya se puede escribir la parte metodologica de adquisicion y la
descripcion del baseline fijo. Para cerrar la parte de resultados del dron hay
dos caminos posibles:

1. redactar ya mismo una subseccion honesta donde se explicite que las corridas
   son comparables pero todavia exhiben un offset sistematico importante en
   posicion;
2. depurar primero la geometria del caso dron y regenerar los bags si se busca
   una narrativa mas fuerte de precision absoluta.

En cualquier caso, al redactar se recomienda distinguir siempre entre:

- figuras de posicion "sin bias medio" usadas para leer fase y forma;
- tablas e histogramas crudos, usados para cuantificar el error real.

Tambien conviene explicitar que el escenario con dron no se apoya en una sola
corrida: se ejecutaron tres repeticiones comparables (`R1`, `R2`, `R3`). La
figura agregada `sim_drone_runs_comparison.png` sirve para mostrar diferencias
entre corridas en la variable que mas interesa para el informe: el error
en `roll`, `pitch` y `heave`. La narrativa recomendada es usar las tres
corridas para justificar repetibilidad cualitativa del escenario y dispersión
cuantitativa en esas tres variables.
