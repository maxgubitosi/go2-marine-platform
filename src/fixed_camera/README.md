# Fixed Camera

Paquete ROS2 que simula una cámara fija nadir (mirando hacia abajo) para experimentos de detección visual sobre plataforma marina.

## Características

- **Cámara estática** — no se mueve en ningún sentido, posición fija configurable
- **Cámara RGB** mirando verticalmente hacia abajo (640x480 @ 30Hz, FOV 80°)
- **Coherencia total** entre lo que se ve en Gazebo y los datos de TF/pose
- **Detector ArUco** integrado (opcional)
- Publicación de parámetros intrínsecos de cámara (`/fixed_camera/camera_info`)

## Requisitos

```bash
sudo apt install -y \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-xacro \
  ros-humble-robot-state-publisher \
  python3-opencv \
  ros-humble-cv-bridge
```

## Compilación

```bash
# Compilar
colcon build --packages-select fixed_camera
source install/setup.bash

# Lanzar con Gazebo corriendo
ros2 launch fixed_camera fixed_camera.launch.py

# Sin detector ArUco
ros2 launch fixed_camera fixed_camera.launch.py aruco:=false

# Cambiar altura
ros2 launch fixed_camera fixed_camera.launch.py height:=3.0
```

## Topics principales

- `/fixed_camera/image_raw` - Imagen RGB 640x480 @ 30Hz
- `/fixed_camera/camera_info` - Parámetros intrínsecos de cámara
- `/fixed_camera/pose` - Pose fija de la cámara en el mundo (PoseStamped)
- `/aruco/pose` - Pose estimada del marcador ArUco (cuando aruco:=true)
- `/aruco/detection` - Flag de detección del ArUco
- `/aruco/debug_image` - Imagen anotada con ejes del ArUco

## Configuración

Parámetros configurables en `config/fixed_camera_params.yaml`:
- `position_x`, `position_y`, `position_z` — posición fija de la cámara
- `publish_rate` — frecuencia de publicación de pose (Hz)

## Arquitectura

```
fixed_camera/
├── fixed_camera/
│   ├── camera_controller.py       # Publica pose fija + TF estático
│   └── aruco_detector.py          # Detección ArUco en tiempo real
├── urdf/fixed_camera.xacro        # Modelo URDF (caja pequeña + cámara)
├── launch/fixed_camera.launch.py  # Launch file (aruco:=true|false, height:=2.0)
└── config/
    ├── fixed_camera_params.yaml       # Parámetros de posición
    └── aruco_detector_params.yaml     # Parámetros del detector ArUco
```

El controlador publica un TF estático `world → camera_base_link` y una pose fija como PoseStamped. La cámara en Gazebo tiene `<static>true</static>` y `<gravity>false</gravity>`, garantizando que no se mueva.

## Autores

Maximo Gubitosi, Jack Spolski
