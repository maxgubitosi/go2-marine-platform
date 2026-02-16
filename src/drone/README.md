# Drone

Paquete ROS2 que simula un dron con cámara nadir (mirando hacia abajo) para experimentos de aterrizaje visual sobre plataforma marina.

## Características

- **Dron cuadricóptero** con modelo físico simple
- **Cámara RGB** mirando verticalmente hacia abajo (640x480 @ 30Hz, FOV 80°)
- **Movimiento vertical** sinusoidal configurable
- **Ruido realista** en posición y orientación (simula turbulencias/error GPS)
- Publicación de parámetros intrínsecos de cámara (`/drone/camera/camera_info`)

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
colcon build --packages-select drone
source install/setup.bash

# Lanzar con Gazebo corriendo
ros2 launch drone drone.launch.py

# Sin detector ArUco
ros2 launch drone drone.launch.py aruco:=false
```

## Topics principales

- `/drone/camera/image_raw` - Imagen RGB 640x480 @ 30Hz
- `/drone/camera/camera_info` - Parámetros intrínsecos de cámara
- `/drone/pose` - Pose del dron en el mundo

## Configuración

Parámetros configurables en `config/drone_params.yaml`:
- Altura inicial y rango de movimiento vertical
- Desviación estándar del ruido en posición/orientación
- Frecuencia de actualización del controlador

## Arquitectura

```
drone/
├── drone/drone_controller.py  # Nodo que controla movimiento y publica pose
├── urdf/drone_camera.xacro    # Definición del modelo del dron
├── launch/drone.launch.py     # Launch file (aruco:=true|false)
└── config/drone_params.yaml   # Parámetros de configuración
```

El controlador actualiza la pose del dron a 50Hz, publica transforms TF2, y gestiona el spawn del modelo URDF en Gazebo. La cámara está configurada con un FOV de 80° y publica datos realistas incluyendo distorsión simulada.

## Autores

Maximo Gubitosi, Jack Spolski
