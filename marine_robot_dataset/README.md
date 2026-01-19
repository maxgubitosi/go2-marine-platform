# Marine Robot Dataset Generator

Scripts para generar datasets de entrenamiento a partir de rosbags de la simulación marina del robot Go2.

## Estructura

```
marine_robot_dataset/
├── extract_dataset.py               # Extrae datos de rosbag + mapeo de frames
├── extract_video_frames.py          # Extrae frames de video sincronizados
├── map_video_to_timestamps.py       # Mapea frames a timestamps (standalone)
├── visualize_dataset.py             # Visualiza muestras del dataset
├── requirements.txt                 # Dependencias Python
├── README.md                        # Esta documentación
├── venv/                            # Entorno virtual Python
└── datasets/                        # Datasets generados
    └── marine_sim_YYYYMMDD_HHMMSS/
        ├── dataset.csv                      # Timestamps, poses, joints
        ├── frame_to_timestamp_mapping.csv   # Mapeo frame -> timestamp
        └── frames/                          # Frames de video extraídos
            ├── frame_000000.png
            ├── frame_000001.png
            └── ...
```

## ⚠️ Sincronización Importante

Los videos de la simulación **NO tienen todos los frames esperados**:
- Duración del rosbag: ~62 segundos
- Duración del video: ~20-30 segundos (310-425 frames @ 15 FPS)
- **Problema**: La cámara no publica frames constantemente debido a carga de CPU

**Solución implementada**: 
1. `extract_dataset.py` mapea cada frame REAL del video a su timestamp ROS correcto
2. Solo se sincronizan los frames que realmente existen en el video
3. El mapeo considera que el video empieza 3 segundos después del rosbag

## Instalación

```bash
cd marine_robot_dataset
pip3 install -r requirements.txt
```

## Uso

### 1. Extraer datos del rosbag (con sincronización automática de video)

```bash
python3 extract_dataset.py ../rosbags/marine_sim_20260116_172734
```

Esto:
- Analiza el video `output.avi` y cuenta frames REALES
- Mapea cada frame a su timestamp ROS correcto (considerando delay de 3s)
- Sincroniza datos del rosbag (joints, odom, IMU) con cada frame del video
- Genera `datasets/marine_sim_20260116_172734/dataset.csv`

El CSV incluye:
- `timestamp`: Tiempo ROS en segundos (del frame de video)
- `frame_path`: Nombre del frame correspondiente (ej: `frame_000042.png`)
- `position_x/y/z`: Posición del robot
- `roll/pitch/yaw`: Orientación (Euler angles en radianes)
- `joint_names`: Nombres de las articulaciones
- `joint_positions`: Ángulos de las articulaciones (rad)
- `joint_velocities`: Velocidades de las articulaciones (rad/s)

### 2. Extraer frames del video

```bash
python3 extract_video_frames.py \
    ../rosbags/marine_sim_20260116_172734/output.avi \
    datasets/marine_sim_20260116_172734/dataset.csv
```

Esto extrae SOLO los frames que están en el dataset (sincronización garantizada).

### 3. Visualizar el dataset

```bash
# Ver una muestra específica
python3 visualize_dataset.py datasets/marine_sim_20260116_172734/dataset.csv 0

# Reproducir todo el dataset
python3 visualize_dataset.py datasets/marine_sim_20260116_172734/dataset.csv play
```

### 4. (Opcional) Generar solo el mapeo de frames a timestamps

Si solo necesitas el mapeo sin procesar el dataset completo:

```bash
python3 map_video_to_timestamps.py ../rosbags/marine_sim_20260119_102639
```

Esto genera un CSV standalone en la carpeta del rosbag con el mapeo completo.

## Archivos Generados

## Formato del Dataset

Cada fila del CSV representa un instante de tiempo con:

| Campo | Descripción | Unidad |
|-------|-------------|--------|
| `timestamp` | Tiempo desde inicio | segundos |
| `frame_path` | Path al frame de video | - |
| `position_x/y/z` | Posición del robot base | metros |
| `orientation_x/y/z/w` | Orientación (quaternion) | - |
| `joint_names` | Lista de nombres de joints | - |
| `joint_positions` | Ángulos de articulaciones | radianes |
| `joint_velocities` | Velocidades angulares | rad/s |

## Aplicaciones

- **Aprendizaje supervisado**: Predecir pose del robot desde imágenes
- **Detección de ArUco**: Entrenar detector de marcadores en movimiento
- **Control predictivo**: Predecir estado futuro del robot
- **Análisis de datos**: Estadísticas sobre el comportamiento del robot

## Notas

- Los timestamps están sincronizados entre video y datos de ROS 2
- Los frames del video son opcionales (el dataset funciona sin video)
- Los ángulos están en radianes (usar `np.degrees()` para convertir)
- La orientación es un quaternion `[x, y, z, w]`

## Próximos pasos

1. Agregar datos de `/marine_motion` (heave, pitch, roll de la plataforma)
2. Agregar datos de IMU
3. Exportar a formato HDF5 para mejor performance
4. Augmentación de datos (rotaciones, crops, etc.)
