# Rosbags

Grabaciones de simulaciones marinas y scripts para manejo de datos.

## Grabación

```bash
# Grabar 60 segundos de simulación
./record_marine_simulation.sh 60

# Grabar 5 minutos
./record_marine_simulation.sh 300
```

El script automáticamente:
- Verifica que la simulación esté corriendo
- Graba los topics principales
- Genera un video de la cámara del dron
- Organiza los archivos en un directorio timestamped

## Reproducción

```bash
# Reproducir rosbag con RViz
./play_bag_rviz.sh marine_sim_YYYYMMDD_HHMMSS
```

## Estructura

Cada grabación genera:
```
marine_sim_YYYYMMDD_HHMMSS/
├── rosbag/              # Archivos .db3 y metadata.yaml
├── drone_camera.avi     # Video de cámara del dron
└── simulation_info.txt  # Información de la grabación
```

## Topics grabados

- `/clock` - Tiempo de simulación
- `/drone/camera/image_raw` - Imágenes del dron
- `/drone/camera/camera_info` - Parámetros de cámara
- `/drone/pose` - Pose del dron
- `/go2/pose_rphz_cmd` - Comandos de movimiento marino
- `/tf` y `/tf_static` - Transforms
- `/aruco_marker/pose` - Pose del marcador ArUco

## Limpieza

Para eliminar grabaciones antiguas:
```bash
# Eliminar grabación específica
rm -rf marine_sim_20251219_122840

# Eliminar todas menos las últimas 3
ls -dt marine_sim_* | tail -n +4 | xargs rm -rf
```
