# Plataforma marina — laboratorio real

Plataforma marina usando un robot cuadrúpedo Unitree Go2 con un marcador ArUco montado encima. El robot se encuentra fijo en el lugar (las 4 patas fijas al piso) pero usa las articulaciones para mover el torso simulando el movimiento de una plataforma marina. El movimiento resultante es en términos de roll, pitch y heave.

Una cámara USB estéreo fija detecta el ArUco en tiempo real y estima la pose del marcador. Todo se graba en rosbags y se exporta a video MP4 + CSVs para evaluación offline.

## Arquitectura

```
gazebo-no-seas-malo/
├── src/
│   ├── fixed_camera/                   # Nodos ROS2: cámara + ArUco detector
│   │   ├── fixed_camera/
│   │   │   ├── stereo_eye_publisher.py     # Publica 1 ojo de cámara estéreo USB
│   │   │   ├── aruco_detector.py           # Detección ArUco (solvePnP)
│   │   │   └── camera_controller.py        # TF estático de la cámara
│   │   ├── launch/
│   │   │   └── lab_real.launch.py          # Launch file para lab real
│   │   └── config/
│   │       ├── fixed_camera_params.yaml
│   │       └── aruco_detector_params.yaml
│   └── go2_tools/                      # Simulador de plataforma marina (modo real)
├── stereo_camera/                      # Pipeline de calibración y exportación
│   ├── config.yaml                         # Config central (device, intrínsecos, ArUco)
│   ├── scripts/
│   │   ├── 01_preview_stereo.py            # Previsualizar cámara estéreo
│   │   ├── 02_capture_calibration.py       # Capturar imágenes de checkerboard
│   │   ├── 03_calibrate.py                 # Calibrar (pinhole o --fisheye)
│   │   ├── 04_validate_calibration.py      # Validar undistort visual
│   │   ├── 05_detect_aruco.py              # Test de detección ArUco (sin ROS2)
│   │   └── 06_export_from_bag.py           # Exportar rosbag → video MP4 + CSV
│   └── calibration/                        # Imágenes + resultado de calibración
├── rosbags/                            # Grabaciones
│   └── record_lab_real.sh                  # Script para grabar experimento
├── run_marine_real.sh                  # Script: movimiento marino en Go2 real
└── README.md
```

## Requisitos

- ROS2 Humble
- Python 3.10+ con OpenCV 4.8+ (`pip3 install opencv-contrib-python`)
- `cv_bridge`, `tf2_ros`
- `unitree_sdk2py` (`pip3 install unitree_sdk2_python`)
- Cámara USB estéreo ("3D USB Camera" 32e4:0035 o similar) en `/dev/video2`
- Unitree Go2 conectado por Ethernet (`192.168.123.161`)
- ArUco impreso: DICT_6X6_250 id 0, **0.20 m** de lado, pegado sobre el trunk del Go2

## Instalación

```bash
git clone https://github.com/maxgubitosi/gazebo-no-seas-malo.git
cd gazebo-no-seas-malo

# Compilar
colcon build --symlink-install
source install/setup.bash

# Dependencias Python
pip3 install opencv-contrib-python pyyaml

# unitree_sdk2py (si no está instalado)
cd /tmp && git clone https://github.com/unitreerobotics/unitree_sdk2_python.git
cd unitree_sdk2_python && pip3 install --user .
```

## Calibración de la cámara (se hace una sola vez)

La cámara estéreo viene con dos lentes. Se usa un solo ojo (1920×1080). Antes de correr el sistema hay que calibrarla con un checkerboard:

```bash
cd stereo_camera
python3 scripts/01_preview_stereo.py          # Verificar qué ojo usar (left/right)
python3 scripts/02_capture_calibration.py      # Capturar ~20 imágenes con checkerboard
python3 scripts/03_calibrate.py                # Calibrar (pinhole). Agregar --fisheye si es lente fisheye
python3 scripts/04_validate_calibration.py     # Verificar undistort visual
python3 scripts/05_detect_aruco.py             # Test standalone de detección ArUco
```

La calibración actual (checkerboard 8×6, cuadros de 80.38 mm) dio RMS = 0.22 px. Los intrínsecos se guardan en `stereo_camera/config.yaml` y el nodo `stereo_eye_publisher` los lee automáticamente.

## Correr el experimento

> **NOTA:** El script `run_marine_real.sh` configura CycloneDDS internamente para comunicarse con el Go2. Las demás terminales usan FastRTPS (default de ROS2). Si por alguna razón ves errores `enp2s0: does not match an available interface`, verificá que tu `.bashrc` no exporte `CYCLONEDDS_URI` ni `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp`.

### Terminal 1: Movimiento marino del Go2 real

```bash
./run_marine_real.sh
```

Este script configura CycloneDDS internamente y envía comandos Euler al Go2 via `unitree_sdk2py`.

Opciones:
```bash
./run_marine_real.sh --manual               # Control por teclado
./run_marine_real.sh --roll 10 --pitch 8    # Amplitudes custom (grados)
./run_marine_real.sh --pattern irregular     # Patrón de olas (default: irregular)
./run_marine_real.sh --freq 0.2             # Frecuencia de olas (Hz)
./run_marine_real.sh --heave 0.03           # Heave máximo (metros)
```

Parámetros por defecto: roll ±20°, pitch ±15°, heave ±0.04 m, freq 0.15 Hz, patrón irregular.

### Terminal 2: Cámara + detección ArUco

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch fixed_camera lab_real.launch.py
```

Argumentos opcionales:
```bash
ros2 launch fixed_camera lab_real.launch.py device:=/dev/video4   # Otro device
ros2 launch fixed_camera lab_real.launch.py marker_length:=0.20   # Tamaño ArUco (m)
ros2 launch fixed_camera lab_real.launch.py height:=2.5            # Altura cámara (m)
ros2 launch fixed_camera lab_real.launch.py eye:=right             # Usar ojo derecho
```

Esto lanza 3 nodos:
- `stereo_eye_publisher` — abre la cámara USB, cropea un ojo, publica `/stereo_camera/image_raw` + `/stereo_camera/camera_info`
- `aruco_detector` — detecta el ArUco y publica `/aruco/pose`, `/aruco/detection`, `/aruco/debug_image`
- `camera_controller` — publica TF estático de la posición de la cámara

### Terminal 3 (opcional): Visualizar en tiempo real

```bash
source /opt/ros/humble/setup.bash
ros2 run rqt_image_view rqt_image_view
```

Seleccionar en el dropdown:
- `/aruco/debug_image` — imagen con overlay de detección (bordes verdes + ejes 3D)
- `/stereo_camera/image_raw` — imagen cruda de la cámara

### Terminal 4: Grabar rosbag

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash
cd rosbags
./record_lab_real.sh 60          # Graba 60 segundos
./record_lab_real.sh 120 olas5   # 120 seg, sufijo "olas5"
```

**IMPORTANTE:** Las Terminales 1 y 2 deben estar corriendo antes de empezar a grabar. El script verifica que los topics existan y avisa si falta alguno.

### Qué se graba

| Topic | Tipo | Contenido |
|---|---|---|
| `/stereo_camera/image_raw` | `sensor_msgs/Image` | Imagen de un ojo (1920×1080 BGR8) |
| `/stereo_camera/camera_info` | `sensor_msgs/CameraInfo` | Intrínsecos calibrados |
| `/aruco/pose` | `geometry_msgs/PoseStamped` | Pose estimada del ArUco (x, y, z, quaternion) |
| `/aruco/detection` | `std_msgs/Bool` | Flag: ¿se detectó el ArUco en este frame? |
| `/aruco/debug_image` | `sensor_msgs/Image` | Imagen con overlay de detección |
| `/marine_platform/debug_state` | `geometry_msgs/Vector3` | Comandos enviados (roll, pitch, heave) |

## Ver grabaciones

### Reproducir rosbag con visualización

```bash
# Terminal A: reproducir el bag
source /opt/ros/humble/setup.bash
ros2 bag play rosbags/lab_real_20260310_133022/

# Terminal B: visualizar
source /opt/ros/humble/setup.bash
ros2 run rqt_image_view rqt_image_view
# Seleccionar /aruco/debug_image para ver la detección frame a frame
```

Opciones útiles de playback:
```bash
ros2 bag play rosbags/lab_real_.../ --rate 0.5    # Reproducir a mitad de velocidad
ros2 bag play rosbags/lab_real_.../ --loop         # Repetir en loop
ros2 bag play rosbags/lab_real_.../ --rate 2.0    # Doble velocidad
```

### Ver info del bag

```bash
ros2 bag info rosbags/lab_real_20260310_133022/
```

Muestra duración, cantidad de mensajes por topic, y tamaño.

### Exportar a video MP4 + CSVs

```bash
# Exportar todo: video + CSVs
python3 stereo_camera/scripts/06_export_from_bag.py rosbags/lab_real_20260310_133022/

# Solo CSVs (sin video, más rápido)
python3 stereo_camera/scripts/06_export_from_bag.py rosbags/lab_real_20260310_133022/ --no-video
```

Genera en `rosbags/lab_real_.../exports/`:

| Archivo | Contenido |
|---|---|
| `debug_video.mp4` | Video con overlay de detección ArUco |
| `aruco_poses.csv` | Timestamp, x, y, z, roll, pitch, yaw, distance, detected |
| `marine_commands.csv` | Timestamp, roll_cmd, pitch_cmd, heave_cmd |
| `merged_aruco_marine.csv` | Correlación temporal ArUco ↔ comandos marinos (threshold 200 ms) |

Los CSVs se pueden importar en Python/MATLAB/Excel para graficar y evaluar la estimación de pose vs los comandos enviados.

### Ver video exportado directamente

```bash
# Con cualquier reproductor
xdg-open rosbags/lab_real_20260310_133022/exports/debug_video.mp4

# O con ffplay
ffplay rosbags/lab_real_20260310_133022/exports/debug_video.mp4
```

## Troubleshooting

| Problema | Causa | Solución |
|---|---|---|
| `enp2s0: does not match an available interface` | `CYCLONEDDS_URI` exportado en `.bashrc` u otra terminal | Verificar que `.bashrc` no exporte `CYCLONEDDS_URI`. Si lo hace, comentar esas líneas |
| ArUco no se detecta | Marcador no visible, mal iluminado, o muy lejos | Verificar con `rqt_image_view` en `/aruco/debug_image` |
| `record_lab_real.sh` muestra topics ✗ | Terminal 2 no está corriendo o usa otro RMW | Verificar que `lab_real.launch.py` esté corriendo sin errores |
| FPS bajo en la grabación | Disco lento, imágenes 1920×1080 sin comprimir | Normal (~1-2 fps con imágenes crudas en disco HDD) |
| Go2 no se mueve | No conectado, IP incorrecta, o no en BalanceStand | Verificar ping a `192.168.123.161`, revisar output de `run_marine_real.sh` |
| Poses todas en (0,0,0) en el CSV | ArUco no fue detectado en esos frames | Reproducir el bag y verificar con `/aruco/debug_image` |

## Desarrollo

```bash
# Compilar solo el paquete de cámara
colcon build --packages-select fixed_camera --symlink-install

# Compilar solo go2_tools
colcon build --packages-select go2_tools --symlink-install

# Limpiar build completo
rm -rf build install log
colcon build --symlink-install
```

## Autores

Maximo Gubitosi - mgubitosi@udesa.edu.ar
Jack Spolski - jspolski@udesa.edu.ar
