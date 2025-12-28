# Drone Landing Package

Paquete ROS2 para simular un dron con cámara mirando hacia abajo, diseñado para aterrizaje sobre plataforma marina con marcador ArUco.

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
cd ~/gazebo-no-seas-malo
colcon build --packages-select drone_landing
source install/setup.bash
```

## Uso

### Lanzar solo el dron (con Gazebo ya corriendo)

```bash
# Terminal 1: Asegurate de tener Gazebo corriendo
ros2 launch go2_config gazebo.launch.py rviz:=true

# Terminal 2: Lanzar el dron
cd ~/gazebo-no-seas-malo
source install/setup.bash
ros2 launch drone_landing drone_landing.launch.py
```

### Integrado con simulación marina completa

```bash
# Terminal 1: Lanzar todo el sistema
cd ~/gazebo-no-seas-malo
source install/setup.bash
ros2 launch go2_config gazebo.launch.py rviz:=true

# Terminal 2: Lanzar simulador marino
ros2 run go2_tools marine_platform_simulator

# Terminal 3: Lanzar dron
ros2 launch drone_landing drone_landing.launch.py

# Terminal 4: Ver tópicos y grabar
ros2 topic list
ros2 topic echo /drone/camera/image_raw
```

## Topics publicados

- `/drone/camera/image_raw` (sensor_msgs/Image) - Imagen de cámara RGB
- `/drone/camera/camera_info` (sensor_msgs/CameraInfo) - Parámetros intrínsecos
- `/drone/pose` (geometry_msgs/Pose) - Posición y orientación del dron
- `/drone/robot_description` (std_msgs/String) - Descripción URDF del dron

## TF frames

- `world` → `drone_base_link` - Posición del dron en el mundo
- `drone_base_link` → `camera_link` - Enlace de la cámara
- `camera_link` → `camera_link_optical` - Frame óptico (convención ROS)

## Configuración

Editá `config/drone_params.yaml` para ajustar parámetros:

```yaml
drone_controller:
  ros__parameters:
    initial_height: 3.0          # Altura inicial (m)
    vertical_range: 1.0          # Rango movimiento vertical (±m)
    vertical_velocity: 0.2       # Velocidad vertical (m/s)
    position_x: 0.0              # Posición X fija
    position_y: 0.0              # Posición Y fija
    noise_position_std: 0.05     # Ruido posición (m)
    noise_orientation_std: 0.035 # Ruido orientación (rad, ~2°)
    update_rate: 50.0            # Frecuencia de actualización (Hz)
```

## Calibración de cámara

Los parámetros intrínsecos simulados son:

- Resolución: 640x480
- FOV horizontal: 80°
- Focal length (fx, fy): ~381 px
- Centro principal (cx, cy): ~(320, 240)
- Distorsión radial: k1=-0.05, k2=0.02
- Distorsión tangencial: p1=0.001, p2=-0.001

Para calibración real con OpenCV, usá estos valores como iniciales.

## Visualización en RViz

Agregá estos displays en RViz:

1. **Camera** - Topic: `/drone/camera/image_raw`
2. **TF** - Mostrar frames del dron
3. **RobotModel** - Topic: `/drone/robot_description`

## Grabación de rosbag

Ver `rosbags/code-example.md` para comandos de grabación que incluyen topics del dron.

## Estructura del paquete

```
drone_landing/
├── config/
│   └── drone_params.yaml       # Configuración del controlador
├── drone_landing/
│   ├── __init__.py
│   └── drone_controller.py     # Nodo de control con ruido
├── launch/
│   └── drone_landing.launch.py # Launch file principal
├── urdf/
│   └── drone_camera.xacro      # Modelo URDF del dron
├── package.xml
├── setup.py
└── README.md
```

## Próximos pasos

- [ ] Implementar nodo de detección ArUco (`aruco_detector.py`)
- [ ] Controlador de aterrizaje basado en visión
- [ ] Estimación de pose relativa plataforma-dron

## Autor

Maximiliano Gubitosi - mgubitosi@udesa.edu.ar
