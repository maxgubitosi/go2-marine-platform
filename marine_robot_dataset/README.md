# Marine Robot Dataset Generator

Scripts para generar datasets de entrenamiento a partir de rosbags de la simulación marina del robot Go2.

## Estructura

```
marine_robot_dataset/
├── extract_dataset.py               # Extrae imagenes y datos del rosbag
├── extract_complete_dataset.py      # Wrapper que ejecuta extract_dataset.py
├── visualize_dataset.py             # Visualiza muestras del dataset
├── requirements.txt                 # Dependencias Python
└── datasets/                        # Datasets generados
    └── marine_sim_YYYYMMDD_HHMMSS/
        ├── dataset.csv                      # Timestamps, poses, joints
        ├── frame_to_timestamp_mapping.csv   # Mapeo frame -> timestamp
        └── frames/                          # Imagenes extraidas del rosbag
            ├── frame_000000.png
            ├── frame_000001.png
            └── ...
```

## Sincronización

Las imágenes de la cámara del drone se graban directamente en el rosbag
(topic `/drone/camera/image_raw`), por lo que cada frame tiene su timestamp
ROS exacto. El script de extracción usa búsqueda binaria para emparejar
cada imagen con los datos de joints, odometría e IMU más cercanos
temporalmente (umbral: 50ms).

La altura del trunk (heave) se obtiene preferentemente del topic
`/base_to_footprint_pose` publicado a 50 Hz por el nodo `state_estimation`.
Si el rosbag no contiene ese topic (grabaciones anteriores), se usa la TF
`base_footprint → base_link` (~2 Hz) con interpolación lineal como fallback.

## Instalación

```bash
cd marine_robot_dataset
pip3 install -r requirements.txt
```

## Uso

### 1. Grabar simulación

```bash
cd rosbags
./record_marine_simulation.sh 60
```

### 2. Extraer dataset

```bash
python3 extract_dataset.py ../rosbags/marine_sim_20260207_143824
```

Esto extrae del rosbag:
- Imágenes de `/drone/camera/image_raw` como PNGs con timestamps exactos
- Datos de `/joint_states`, `/odom`, `/imu/data`, `/tf`
- Sincroniza todo por timestamp y genera un CSV

O usando el wrapper:

```bash
python3 extract_complete_dataset.py ../rosbags/marine_sim_20260207_143824
```

### 3. Visualizar

```bash
# Ver una muestra
python3 visualize_dataset.py datasets/marine_sim_20260207_143824/dataset.csv 0

# Reproducir como video
python3 visualize_dataset.py datasets/marine_sim_20260207_143824/dataset.csv play
```

## Formato del CSV

| Campo | Descripción | Unidad |
|-------|-------------|--------|
| `timestamp` | Timestamp ROS de la imagen | segundos |
| `frame_path` | Nombre del archivo PNG | - |
| `position_x/y` | Posición XY del trunk (odometría) | metros |
| `heave` | Altura del trunk sobre base_footprint | metros |
| `heave_dt_ms` | Distancia temporal al dato de heave más cercano | milisegundos |
| `roll/pitch/yaw` | Orientación (Euler) | radianes |
| `joint_names` | Nombres de articulaciones | - |
| `joint_positions` | Ángulos de articulaciones | radianes |
| `joint_velocities` | Velocidades angulares | rad/s |

### Columna `heave_dt_ms`

La columna `heave_dt_ms` indica la distancia temporal (en milisegundos)
al dato de heave real más cercano. La fuente depende de lo disponible
en el rosbag:

- **`/base_to_footprint_pose`** (50 Hz): publicado por `state_estimation`,
  contiene directamente la altura del trunk. Con esta fuente, `heave_dt_ms`
  es típicamente < 20 ms.
- **TF `base_footprint → base_link`** (~2 Hz, fallback): se usa si el
  topic anterior no está en el rosbag. El heave se interpola linealmente
  entre TFs y `heave_dt_ms` puede llegar a cientos de ms.

Esto permite filtrar por calidad según el caso de uso.
