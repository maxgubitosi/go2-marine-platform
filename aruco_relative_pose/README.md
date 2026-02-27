# Estimación de pose relativa (ArUco)

Esta carpeta toma los `frames/` del dataset y estima la pose del marcador ArUco (sobre el cuadrúpedo) **en el frame de la cámara** usando OpenCV. También copia el ground truth del `dataset.csv` para comparar.

Soporta **dos fuentes de cámara**:

| Fuente | Rosbags | Resolución | Cámara |
|---|---|---|---|
| `fixed_camera` | `marine_sim_*` | 640×480, FOV=1.396 | Estática en el mundo |
| `sjtu_drone` | `sjtu_drone_sim_*` | 640×360, FOV=1.047 | Bottom cam del SJTU drone (se mueve) |

La fuente se **auto-detecta** a partir del prefijo del nombre del rosbag, o se puede forzar con `--camera-source`.

## Requisitos

```bash
pip3 install -r aruco_relative_pose/requirements.txt
```

## Configuración

Edita `aruco_relative_pose/config.yaml`:

- `camera.matrix`: intrínsecos reales (fx, fy, cx, cy)
- `camera.dist_coeffs`: coeficientes de distorsión
- `aruco.dictionary`: diccionario ArUco usado en la simulación
- `aruco.marker_length_m`: lado del marcador en metros
- `aruco.target_id`: (opcional) ID del marcador si hay más de uno
- `aruco.xacro_path`: (opcional) ruta al xacro del patrón para usar un diccionario personalizado
- `aruco.bit_pattern`: patrón 6x6 (1 blanco, 0 negro)
- `aruco.bit_one_is_white`: interpreta 1 como blanco
- `aruco.quad_detection`: detección de cuadrado oscuro (fallback)
- `aruco.template_match`: (opcional) fallback por template matching si ArUco no detecta

## Uso

```bash
python3 aruco_relative_pose/scripts/estimate_relative_pose.py \
  --dataset-csv datasets/marine_sim_20260207_155320/dataset.csv \
  --config aruco_relative_pose/config.yaml

# Debug (imprime estadisticas por frame)
python3 aruco_relative_pose/scripts/estimate_relative_pose.py \
  --dataset-csv datasets/marine_sim_20260207_155320/dataset.csv \
  --config aruco_relative_pose/config.yaml \
  --debug --max-frames 5
```

Salida por defecto:

```
aruco_relative_pose/outputs/<dataset>_aruco_pose.csv
```

Para guardar visualizaciones con ejes:

```bash
python3 aruco_relative_pose/scripts/estimate_relative_pose.py \
  --dataset-csv datasets/marine_sim_20260207_155320/dataset.csv \
  --config aruco_relative_pose/config.yaml \
  --viz-dir aruco_relative_pose/outputs/viz
```

## Formato de salida

Columnas principales (por frame):

- `tvec_x/y/z`: posición del marcador en el **frame de cámara** (metros)
- `rvec_x/y/z`: vector de rotación (Rodrigues)
- `roll/pitch/yaw`: Euler XYZ (radianes) del marcador en el frame de cámara
- `reproj_error_px`: error medio de reproyección (pixeles)
- `detected`: `True/False`
- `marker_id`, `n_markers`

Ground truth copiado desde `dataset.csv`:

- `gt_x`, `gt_y`, `gt_z`, `gt_roll`, `gt_pitch`, `gt_yaw`

Ground truth transformado al frame de camara (para comparar directo con estimado):

- `gt_cam_marker_x`, `gt_cam_marker_y`, `gt_cam_marker_z`
- `gt_cam_marker_roll`, `gt_cam_marker_pitch`, `gt_cam_marker_yaw`

## Notas importantes

- OpenCV usa el frame de cámara con **X derecha, Y abajo, Z hacia adelante**.
- El ground truth del CSV corresponde al trunk del robot en el frame de odometría. Si ese frame coincide con el de la cámara (o conoces la extrínseca), la comparación es directa. Si no, necesitarás transformar los GT antes de comparar.

## Evaluación en tiempo real desde rosbag

Compara las estimaciones `/aruco/pose` grabadas en un rosbag con el ground truth calculado a partir de odometría + IMU + pose del dron.

### Cámara fija (fixed_camera)

```bash
python3 aruco_relative_pose/scripts/evaluate_realtime_aruco.py \
  rosbags/marine_sim_20260215_190303
```

### SJTU Drone (bottom camera)

```bash
python3 aruco_relative_pose/scripts/evaluate_realtime_aruco.py \
  rosbags/sjtu_drone_sim_20260216_180434
```

### Forzar fuente de cámara

```bash
python3 aruco_relative_pose/scripts/evaluate_realtime_aruco.py \
  rosbags/some_bag --camera-source sjtu_drone
```

La salida se guarda en `aruco_relative_pose/outputs/<bag_name>_realtime_eval/` con:
- `realtime_aruco_evaluation.csv`
- Plots de posición, orientación y distribución de errores

### Parámetro `--world-init-x`

La odometría de pata de CHAMP siempre arranca en (0,0) sin importar dónde se
spawneó el Go2 en Gazebo. El script necesita conocer ese offset para calcular
el ground truth correctamente.

**El default es 0.40 m** (valor usado en nuestro bringup launch). Si en tu
simulación el Go2 se spawneó en otra posición, sobreescríbelo:

```bash
python3 aruco_relative_pose/scripts/evaluate_realtime_aruco.py \
  rosbags/some_bag --world-init-x 0.0
```
