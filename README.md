# Simulación de plataforma marina

Simulación de una plataforma marina usando un robot cuadrúpedo Unitree Go2 con una plataforma y patron aruco encima. El robot se encuentra fijo en el lugar, (las 4 patas fijas al piso) pero usa las articulaciones para mover el torso del robot simulando el movimimiento de una plataforma marina. El movimiento resultante de la plataforma sobre el robot es en términos de roll, pitch y heave.

## Descripción

Este proyecto implementa un entorno de simulación que combina:
- Robot cuadrúpedo Unitree Go2 operando sobre una plataforma marina simulada
- Movimientos marinos realistas (heave, pitch, roll)
- Dron con cámara nadir para aterrizaje visual
- Marcador ArUco en la plataforma para detección visual
- Sistema de grabación y reproducción de datos

## Arquitectura

```
gazebo-no-seas-malo/
├── src/
│   ├── drone/              # Simulación de dron con cámara
│   ├── go2_tools/          # Simulador de plataforma marina
│   └── unitree-go2-ros2/   # Paquetes del robot Unitree Go2
│                           # https://github.com/maxgubitosi/unitree-go2-ros2
├── rosbags/                # Grabaciones y scripts de reproducción
└── README.md
```

## Requisitos

- ROS2 Humble
- Gazebo Classic
- Python 3.10+
- Paquetes ROS2:
  - `gazebo_ros_pkgs`
  - `robot_state_publisher`
  - `xacro`
  - `cv_bridge`
  - `tf2_ros`

## Instalación

```bash
# Clonar repositorio
git clone https://github.com/maxgubitosi/gazebo-no-seas-malo.git
cd gazebo-no-seas-malo

# Compilar workspace
colcon build --symlink-install
source install/setup.bash
```

## Uso básico

### Opción 1: Script automático

```bash
./run_marine_simulation.sh
```

### Opción 2: Lanzamiento manual (recomendado)

```bash
# Terminal 1: Gazebo y RViz
colcon build --symlink-install
source install/setup.bash
ros2 launch go2_config gazebo.launch.py rviz:=true

# Terminal 2: Simulador de plataforma marina
source install/setup.bash
ros2 run go2_tools marine_platform_simulator

# Terminal 3: Dron con cámara
source install/setup.bash
ros2 launch drone drone.launch.py

# Terminal 4 (opcional): Grabar datos
cd rosbags
./record_marine_simulation.sh 60
```

## Componentes principales

### Unitree Go2 ROS2

Paquetes base del robot cuadrúpedo Unitree Go2 para ROS2. Incluye descripción URDF, controladores, configuración de Gazebo y navegación autónoma.

**Instalación:**
```bash
cd ~/gazebo-no-seas-malo/src
git clone https://github.com/maxgubitosi/unitree-go2-ros2
```

Este repositorio contiene:
- `champ` - Framework base para robots cuadrúpedos
- `go2_config` - Configuración específica del Unitree Go2
- `go2_description` - Descripción URDF y meshes del robot
- Launch files para Gazebo, RViz, SLAM y navegación

Ver el [repositorio](https://github.com/maxgubitosi/unitree-go2-ros2) para más detalles.

### Drone Package
Simulación de dron cuadricóptero con cámara mirando hacia abajo para experimentos de aterrizaje visual. Ver `src/drone/README.md` para más detalles.

### Go2 Tools
Herramientas para simulación de movimientos marinos en el robot Unitree Go2. Incluye generación automática de ondas y control manual. Ver `src/go2_tools/README.md` para más detalles.

### Rosbags
Sistema de grabación y reproducción de simulaciones. Ver `rosbags/` para scripts y ejemplos.

## Topics principales

- `/drone/camera/image_raw` - Imagen de cámara del dron (640x480 @ 30Hz)
- `/drone/camera/camera_info` - Parámetros intrínsecos de cámara
- `/drone/pose` - Pose del dron en el mundo
- `/go2/pose_rphz_cmd` - Comandos de movimiento marino [roll, pitch, heave]
- `/aruco_marker/pose` - Pose del marcador ArUco en la plataforma

## Desarrollo

```bash
# Compilar un paquete específico
colcon build --packages-select drone
colcon build --packages-select go2_tools

# Limpiar build completo
rm -rf build install log
colcon build --symlink-install
```

## Autores

Maximo Gubitosi - mgubitosi@udesa.edu.ar  
Jack Spolski - jspolski@udesa.edu.ar
