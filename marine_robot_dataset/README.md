# Marine Robot Dataset Generator

Scripts para generar datasets de entrenamiento a partir de rosbags de la simulación marina del robot Go2.

## Estructura

```
marine_robot_dataset/
├── extract_dataset.py          # Extrae datos de rosbag (joints, pose)
├── extract_video_frames.py     # Extrae frames de video sincronizados
├── visualize_dataset.py        # Visualiza muestras del dataset
├── requirements.txt            # Dependencias Python
├── README.md                   # Esta documentación
└── datasets/                   # Datasets generados
    └── marine_sim_YYYYMMDD_HHMMSS/
        ├── dataset.csv         # Timestamps, poses, joints
        └── frames/             # Frames de video extraídos
            ├── frame_000000.png
            ├── frame_000001.png
            └── ...
```

## Instalación

```bash
cd marine_robot_dataset
pip3 install -r requirements.txt
```

## Uso

### 1. Extraer datos del rosbag

```bash
python3 extract_dataset.py ../rosbags/marine_sim_20260116_172734
```

Esto genera:
- `datasets/marine_sim_20260116_172734/dataset.csv` con columnas:
  - `timestamp`: Tiempo en segundos
  - `frame_path`: Nombre del frame correspondiente
  - `position_x/y/z`: Posición del robot
  - `orientation_x/y/z/w`: Orientación (quaternion)
  - `joint_names`: Nombres de las articulaciones
  - `joint_positions`: Ángulos de las articulaciones (rad)
  - `joint_velocities`: Velocidades de las articulaciones (rad/s)

### 2. Extraer frames del video (si existe)

```bash
# Ubicar el video .avi en la carpeta del rosbag
python3 extract_video_frames.py \
    ../rosbags/marine_sim_20260116_172734/output.avi \
    datasets/marine_sim_20260116_172734/dataset.csv
```

Esto extrae los frames sincronizados con los datos del dataset.

### 3. Visualizar el dataset

```bash
# Ver una muestra específica
python3 visualize_dataset.py datasets/marine_sim_20260116_172734/dataset.csv 0

# Reproducir todo el dataset
python3 visualize_dataset.py datasets/marine_sim_20260116_172734/dataset.csv play
```

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
