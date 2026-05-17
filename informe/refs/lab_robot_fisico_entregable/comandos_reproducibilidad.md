# Comandos de reproducibilidad

Estos comandos documentan el flujo usado para obtener los ensayos limpios de
laboratorio. No hace falta repetirlos para completar el informe actual.

## Preparar entorno

```bash
cd ~/gazebo-no-seas-malo
source /opt/ros/humble/setup.bash
source install/setup.bash
```

## Verificar topics criticos

```bash
ros2 topic list | grep -E 'sportmodestate|lowstate|api/sport|marine_platform|utlidar/robot_odom'
```

Minimo esperado para el analisis cuantitativo:

- `/marine_platform/debug_state`
- `/api/sport/request`
- `/api/sport/response`
- `/sportmodestate`
- `/lowstate`
- `/utlidar/robot_odom`

## Grabar robot sin video

```bash
BAG=rosbags/lab_real_$(date +%Y%m%d_%H%M%S)_robot_min
timeout --signal=SIGINT 60s ros2 bag record \
  /api/sport/request \
  /api/sport/response \
  /marine_platform/debug_state \
  /sportmodestate \
  /lowstate \
  /utlidar/robot_odom \
  /rosout \
  -o "$BAG"
```

Nota: si se usa `timeout --signal=SIGINT`, el recorder termina solo y cierra
correctamente el bag. No hace falta cortar con `Ctrl+C`.

## Generar plots

```bash
python3 rosbags/plot_movimiento_comparaciones.py "$BAG"
```

Plots esperados:

- `plot_01_timeseries_cmd_vs_real.png`
- `plot_02_api_fidelity.png`
- `plot_03_lag_correlation.png`
- `plot_04_gait_distribution.png`
- `plot_05_heave_z_comparison.png`

## Inspeccionar bag

```bash
ros2 bag info "$BAG"
```

## Ensayos usados en este entregable

```bash
ros2 bag info rosbags/lab_real_20260424_120323_strong_15_10
ros2 bag info rosbags/lab_real_20260424_114454_robot_min
python3 rosbags/plot_movimiento_comparaciones.py rosbags/lab_real_20260424_120323_strong_15_10
python3 rosbags/plot_movimiento_comparaciones.py rosbags/lab_real_20260424_114454_robot_min
```
