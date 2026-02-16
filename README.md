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
│   ├── drone/                      # Simulación de dron con cámara
│   │   ├── drone/
│   │   │   ├── drone_controller.py     # Control de posición del dron
│   │   │   └── aruco_detector.py       # Detección ArUco en tiempo real
│   │   ├── launch/
│   │   │   └── drone.launch.py         # Dron (+ detector ArUco con aruco:=true)
│   │   └── config/
│   │       ├── drone_params.yaml
│   │       └── aruco_detector_params.yaml
│   ├── go2_tools/                  # Simulador de plataforma marina
│   └── unitree-go2-ros2/           # Paquetes del robot Unitree Go2
│                                   # https://github.com/maxgubitosi/unitree-go2-ros2
├── aruco_relative_pose/            # Estimación de pose offline y evaluación
│   ├── scripts/
│   │   ├── estimate_relative_pose.py       # Estimación offline desde dataset
│   │   ├── analyze_pose_results.py         # Análisis y gráficos
│   │   └── evaluate_realtime_aruco.py      # Evaluación offline vs GT desde rosbag
│   └── config.yaml
├── marine_robot_dataset/           # Extracción de datasets desde rosbags
├── rosbags/                        # Grabaciones y scripts de reproducción
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

# Terminal 3: Dron con cámara (sin ArUco)
source install/setup.bash
ros2 launch drone drone.launch.py aruco:=false

# Terminal 4 (opcional): Grabar datos
cd rosbags
./record_marine_simulation.sh 60
vlc LINK_VIDEO_DRONE_CAMARA
```

### Opción 3: Con detección ArUco en tiempo real

Lanza el dron con el nodo de detección ArUco incluido. Estima la pose del marcador (DICT_6X6_250 id=0, 0.50m) relativa a la cámara en tiempo real usando `cv2.aruco` + `solvePnP`.

```bash
# Terminal 1: Gazebo y RViz
colcon build --symlink-install
source install/setup.bash
ros2 launch go2_config gazebo.launch.py rviz:=true

# Terminal 2: Simulador de plataforma marina
source install/setup.bash
ros2 run go2_tools marine_platform_simulator

# Terminal 3: Dron con cámara + detector ArUco
source install/setup.bash
ros2 launch drone drone.launch.py

# Terminal 4: Visualizar detección en tiempo real
source /opt/ros/humble/setup.bash
ros2 run rqt_image_view rqt_image_view
# Seleccionar el topic /aruco/debug_image en el dropdown

# Terminal 5 (opcional): Ver pose estimada
source install/setup.bash
ros2 topic echo /aruco/pose

# Terminal 6 (opcional): Grabar datos para evaluación offline
cd rosbags
./record_marine_simulation.sh 60
```

#### Evaluación offline (post-proceso)

Una vez grabado el rosbag, se puede comparar la estimación en tiempo real con el ground truth del Go2 (odometría + IMU + heave). El script calcula las transformaciones necesarias para llevar el GT al frame de la cámara y lo compara con las estimaciones del detector:

```bash
python3 aruco_relative_pose/scripts/evaluate_realtime_aruco.py rosbags/<nombre_rosbag>
```

Genera un CSV con errores por frame y gráficos de posición/orientación estimada vs GT en `aruco_relative_pose/outputs/`.

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
- `/aruco/pose` - Pose estimada del marcador ArUco en frame cámara (PoseStamped)
- `/aruco/detection` - Flag de detección del ArUco (Bool)
- `/aruco/debug_image` - Imagen anotada con bordes y ejes del ArUco detectado

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
