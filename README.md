# Simulación de plataforma marina

Simulación de una plataforma marina usando un robot cuadrúpedo Unitree Go2 con una plataforma y patron aruco encima. El robot se encuentra fijo en el lugar, (las 4 patas fijas al piso) pero usa las articulaciones para mover el torso del robot simulando el movimimiento de una plataforma marina. El movimiento resultante de la plataforma sobre el robot es en términos de roll, pitch y heave.

## Descripción

Este proyecto implementa un entorno de simulación que combina:
- Robot cuadrúpedo Unitree Go2 operando sobre una plataforma marina simulada
- Movimientos marinos realistas (heave, pitch, roll)
- **Cámara fija** nadir para captura visual sin movimiento
- **Dron sjtu_drone** con vuelo real y cámara bottom para aterrizaje visual
- Marcador ArUco en la plataforma para detección visual
- Sistema de grabación y reproducción de datos

## Arquitectura

```
gazebo-no-seas-malo/
├── src/
│   ├── fixed_camera/               # Cámara fija nadir (sin movimiento)
│   │   ├── fixed_camera/
│   │   │   ├── camera_controller.py    # Publica pose fija + TF estático
│   │   │   └── aruco_detector.py       # Detección ArUco en tiempo real
│   │   ├── launch/
│   │   │   └── fixed_camera.launch.py  # Cámara fija (+ ArUco con aruco:=true)
│   │   ├── urdf/
│   │   │   └── fixed_camera.xacro      # Modelo URDF de la cámara
│   │   └── config/
│   │       ├── fixed_camera_params.yaml
│   │       └── aruco_detector_params.yaml
│   ├── sjtu_drone/                 # Dron con vuelo real (sjtu_drone)
│   │   ├── sjtu_drone_description/     # URDF, plugin de Gazebo, worlds
│   │   ├── sjtu_drone_bringup/         # Launch files y configs
│   │   │   ├── launch/
│   │   │   │   └── sjtu_drone_spawn.launch.py
│   │   │   └── config/
│   │   │       ├── drone.yaml
│   │   │       ├── drone_position_params.yaml
│   │   │       └── aruco_detector_params.yaml
│   │   └── sjtu_drone_control/         # Nodos de control
│   │       └── sjtu_drone_control/
│   │           ├── drone_position_controller.py
│   │           ├── aruco_detector.py
│   │           └── teleop.py
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

### Opción 2: Cámara fija (sin movimiento)

Spawnea una cámara estática mirando hacia abajo sobre la plataforma. No se mueve en ningún sentido — lo que se ve en Gazebo es exactamente lo que dicen los datos.

```bash
# Terminal 1: Gazebo y RViz
colcon build --symlink-install
source install/setup.bash
ros2 launch go2_config gazebo.launch.py rviz:=true

# Terminal 2: Simulador de plataforma marina
source install/setup.bash
ros2 run go2_tools marine_platform_simulator

# Terminal 3: Cámara fija (sin ArUco)
source install/setup.bash
ros2 launch fixed_camera fixed_camera.launch.py aruco:=false

# Terminal 4 (opcional): Grabar datos
cd rosbags
./record_marine_simulation.sh 60
```

### Opción 3: Cámara fija + detección ArUco

Lanza la cámara fija con el nodo de detección ArUco incluido. Estima la pose del marcador (DICT_6X6_250 id=0, 0.50m) relativa a la cámara en tiempo real usando `cv2.aruco` + `solvePnP`.

```bash
# Terminal 1: Gazebo y RViz
colcon build --symlink-install
source install/setup.bash
ros2 launch go2_config gazebo.launch.py rviz:=true

# Terminal 2: Simulador de plataforma marina
source install/setup.bash
ros2 run go2_tools marine_platform_simulator

# Terminal 3: Cámara fija + detector ArUco
source install/setup.bash
ros2 launch fixed_camera fixed_camera.launch.py

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

### Opción 4: Dron sjtu_drone (vuelo real + ArUco)

Spawnea un dron sjtu_drone que despega automáticamente, vuela sobre la plataforma y detecta el ArUco desde la cámara bottom.

```bash
# Terminal 1: Gazebo y RViz
colcon build --symlink-install
source install/setup.bash
ros2 launch go2_config gazebo.launch.py rviz:=true

# Terminal 2: Simulador de plataforma marina
source install/setup.bash
ros2 run go2_tools marine_platform_simulator

# Terminal 3: sjtu_drone (spawn + takeoff + hover + ArUco)
source install/setup.bash
ros2 launch sjtu_drone_bringup sjtu_drone_spawn.launch.py

# Terminal 4: Visualizar detección en tiempo real
source /opt/ros/humble/setup.bash
ros2 run rqt_image_view rqt_image_view
# Seleccionar el topic /aruco/debug_image en el dropdown

# Terminal 5 (opcional): Grabar datos
cd rosbags
./record_sjtu_drone_simulation.sh 60
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

### Fixed Camera
Cámara fija nadir (mirando hacia abajo) para captura visual sobre la plataforma marina. No se mueve — posición estática configurable. Ver `src/fixed_camera/README.md` para más detalles.

### sjtu_drone
Dron cuadricóptero con vuelo real simulado en Gazebo (plugin C++). Despega automáticamente, vuela sobre la plataforma y detecta ArUco desde cámara bottom. Ver `src/sjtu_drone/` para más detalles.

### Go2 Tools
Herramientas para simulación de movimientos marinos en el robot Unitree Go2. Incluye generación automática de ondas y control manual. Ver `src/go2_tools/README.md` para más detalles.

### Rosbags
Sistema de grabación y reproducción de simulaciones. Ver `rosbags/` para scripts y ejemplos.

## Topics principales

### Cámara fija
- `/fixed_camera/image_raw` - Imagen de cámara fija (640x480 @ 30Hz)
- `/fixed_camera/camera_info` - Parámetros intrínsecos de cámara
- `/fixed_camera/pose` - Pose fija de la cámara en el mundo

### sjtu_drone
- `/drone/bottom/image_raw` - Imagen de cámara bottom del dron
- `/drone/bottom/camera_info` - Parámetros intrínsecos de cámara bottom
- `/drone/gt_pose` - Ground truth pose del dron desde Gazebo
- `/drone/pose` - Pose del dron (PoseStamped)
- `/drone/state` - Estado del dron (0=LANDED, 1=FLYING, 2=TAKINGOFF, 3=LANDING)

### Comunes
- `/go2/pose_rphz_cmd` - Comandos de movimiento marino [roll, pitch, heave]
- `/aruco/pose` - Pose estimada del marcador ArUco en frame cámara (PoseStamped)
- `/aruco/detection` - Flag de detección del ArUco (Bool)
- `/aruco/debug_image` - Imagen anotada con bordes y ejes del ArUco detectado

## Desarrollo

```bash
# Compilar un paquete específico
colcon build --packages-select fixed_camera
colcon build --packages-select go2_tools
colcon build --packages-select sjtu_drone_bringup sjtu_drone_control sjtu_drone_description

# Limpiar build completo
rm -rf build install log
colcon build --symlink-install
```

## Autores

Maximo Gubitosi - mgubitosi@udesa.edu.ar  
Jack Spolski - jspolski@udesa.edu.ar
