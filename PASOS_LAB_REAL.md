# Guía: pasar la simulación al laboratorio real

Este documento detalla los pasos para usar el sistema de detección ArUco con un Unitree Go2 real y una cámara fija física, reemplazando la simulación de Gazebo.

---

## 1. Hardware necesario

| Componente | Descripción |
|---|---|
| **Unitree Go2** | Robot real con su SDK corriendo |
| **Marcador ArUco** | Impreso en papel mate, DICT_6X6_250 id 0, lado exacto de 0.50 m |
| **Cámara fija** | USB o IP, montada mirando hacia abajo a altura conocida |
| **PC con ROS2 Humble** | Conectada a la cámara (y opcionalmente al Go2 por red) |
| **Trípode o soporte rígido** | Para montar la cámara a la altura deseada sin vibración |

---

## 2. Imprimir y montar el ArUco

1. Generar la imagen del marcador DICT_6X6_250 id 0. Podés usar el script que ya existe en `extra/generate_aruco.py` o hacerlo con OpenCV:
   ```python
   import cv2
   d = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
   img = cv2.aruco.generateImageMarker(d, 0, 800)  # 800px
   cv2.imwrite("aruco_6x6_250_id0.png", img)
   ```
2. Imprimirlo en papel **mate** (no glossy — los reflejos causan fallos de detección).
3. El lado impreso del cuadrado negro exterior debe medir **exactamente** 0.50 m. Si usás otro tamaño, actualizá `marker_length_m` en `src/fixed_camera/config/aruco_detector_params.yaml` y en `aruco_relative_pose/config.yaml`.
4. Pegarlo sobre una superficie plana y rígida (cartón pluma, MDF, acrílico).
5. Montarlo sobre el trunk del Go2 en la misma posición que en la simulación. El offset actual respecto al trunk es Z = 0.091 m (ver `aruco.marker_offset_xyz` en `aruco_relative_pose/config.yaml`). Si en el robot real cambia, ajustá ese valor.

---

## 3. Instalar y configurar la cámara

### 3.1 Elegir driver ROS2

Opciones comunes:

| Driver | Tipo de cámara | Instalación |
|---|---|---|
| `usb_cam` | Webcam USB genérica | `sudo apt install ros-humble-usb-cam` |
| `v4l2_camera` | Cualquier V4L2 (USB, laptop) | `sudo apt install ros-humble-v4l2-camera` |
| `realsense2_camera` | Intel RealSense (solo RGB) | `sudo apt install ros-humble-realsense2-camera` |

**Recomendación:** `v4l2_camera` es la opción más simple y robusta para una cámara USB estándar. Si ya tenés una RealSense, usá `realsense2_camera`.

### 3.2 Verificar que la cámara publica

Lanzar el driver y verificar que existen los topics de imagen y camera_info:

```bash
# Ejemplo con v4l2_camera
ros2 run v4l2_camera v4l2_camera_node --ros-args -p video_device:="/dev/video0"

# Verificar topics
ros2 topic list | grep -E "image_raw|camera_info"
```

Deberías ver algo como:
```
/image_raw
/camera_info
```

Los nombres exactos dependen del driver. Anotá estos nombres porque los vas a necesitar en el paso 5.

---

## 4. Calibrar la cámara (CRÍTICO)

En simulación los intrínsecos son ideales (calculados del FOV del URDF). En real, **una calibración incorrecta arruina completamente la estimación de pose**. Esto es lo más importante de todo el proceso.

### 4.1 Calibrar con ROS2

```bash
# Instalar el paquete
sudo apt install ros-humble-camera-calibration

# Correr el calibrador con un tablero de ajedrez
# Ajustá --size (esquinas internas) y --square (lado en metros)
ros2 run camera_calibration cameracalibrator \
  --size 9x6 \
  --square 0.025 \
  image:=/image_raw \
  camera:=/camera
```

Mové el tablero delante de la cámara en distintas posiciones, ángulos y distancias hasta que los indicadores X, Y, Size y Skew estén todos en verde. Luego hacé click en "Calibrate" y después en "Save".

### 4.2 Actualizar los intrínsecos

El calibrador genera una camera matrix `K` (3x3) y coeficientes de distorsión `D` (5 valores). Actualizá estos valores en **dos lugares**:

**a) Para el nodo en tiempo real** — el driver ROS2 de la cámara publica el `CameraInfo` (el nodo `aruco_detector` lo lee automáticamente de ahí). Si usás `v4l2_camera`, le podés pasar el archivo de calibración:
```bash
ros2 run v4l2_camera v4l2_camera_node \
  --ros-args -p camera_info_url:="file:///path/to/calibration.yaml"
```

**b) Para evaluación offline** — actualizá `aruco_relative_pose/config.yaml`:
```yaml
camera:
  matrix:
    - [fx, 0.0, cx]
    - [0.0, fy, cy]
    - [0.0, 0.0, 1.0]
  dist_coeffs: [k1, k2, p1, p2, k3]
```

---

## 5. Remapeo de topics (cómo conectar la cámara real al detector ArUco)

Este es el punto clave de la adaptación. El nodo `aruco_detector` se suscribe a dos topics, configurados como **parámetros ROS2** en `src/fixed_camera/config/aruco_detector_params.yaml`:

```yaml
aruco_detector:
  ros__parameters:
    image_topic: "/fixed_camera/camera/image_raw"
    camera_info_topic: "/fixed_camera/camera/camera_info"
```

Tu cámara real va a publicar en topics **distintos** (por ejemplo `/image_raw` y `/camera_info` si usás `v4l2_camera`). Necesitás que el detector lea de los topics correctos.

### Opción A: Cambiar los parámetros del YAML (RECOMENDADA)

Es la opción más limpia. Editá `src/fixed_camera/config/aruco_detector_params.yaml` y cambiá los topics a los que publica tu cámara real:

```yaml
aruco_detector:
  ros__parameters:
    image_topic: "/image_raw"              # ← topic real de tu cámara
    camera_info_topic: "/camera_info"      # ← topic real de tu cámara
    use_sim_time: false                    # ← IMPORTANTE: false en real
    dictionary: "DICT_6X6_250"
    target_id: 0
    marker_length_m: 0.50
    publish_debug_image: true
```

Después de cambiar esto, recompilá:
```bash
colcon build --packages-select fixed_camera --symlink-install
source install/setup.bash
```

Y lanzá solo el detector (sin Gazebo, sin spawn):
```bash
ros2 run fixed_camera aruco_detector
```

### Opción B: Pasar parámetros por línea de comandos

Sin editar archivos, podés sobreescribir parámetros al lanzar:

```bash
ros2 run fixed_camera aruco_detector --ros-args \
  -p image_topic:="/image_raw" \
  -p camera_info_topic:="/camera_info" \
  -p use_sim_time:=false
```

### Opción C: Usar remappings en el launch file

Si preferís crear un launch file nuevo para el lab, podés renombrar los topics del driver de cámara para que coincidan con lo que espera el detector. Por ejemplo:

```python
camera_node = Node(
    package='v4l2_camera',
    executable='v4l2_camera_node',
    remappings=[
        ('/image_raw', '/fixed_camera/camera/image_raw'),
        ('/camera_info', '/fixed_camera/camera/camera_info'),
    ],
    parameters=[{'video_device': '/dev/video0'}]
)
```

Esto hace que la cámara publique directamente en los topics que el detector ya espera. Es útil si no querés tocar ningún YAML existente.

### ¿Cuál elegir?

**La opción A es la más recomendable** porque:
- Es explícita y queda documentada en el YAML.
- No necesitás recordar flags de línea de comandos cada vez.
- No "ensuciás" el namespace del driver de la cámara con remappings que pueden confundir si además querés ver los topics originales.
- Es fácil de revertir (solo cambiás el YAML de vuelta).

---

## 6. Cambios en `use_sim_time`

En simulación, todos los nodos usan `use_sim_time: true` para sincronizarse con el reloj de Gazebo. En real, **hay que poner `use_sim_time: false`** (o simplemente no setearlo, ya que `false` es el default).

Archivos a cambiar:
- `src/fixed_camera/config/aruco_detector_params.yaml` → `use_sim_time: false`
- `src/fixed_camera/config/fixed_camera_params.yaml` → `use_sim_time: false` (si usás `camera_controller`)

O pasarlo por línea de comandos: `--ros-args -p use_sim_time:=false`

---

## 7. Medir y configurar la pose de la cámara en el mundo

En simulación la cámara está en `(0, 0, 2.0)` mirando perfectamente hacia abajo. En el lab:

1. Definí un punto de referencia como "origin" del mundo (por ejemplo, un punto en el piso del lab).
2. Medí con cinta métrica la posición (x, y, z) del centro óptico de la cámara respecto a ese origen.
3. Si la cámara no mira exactamente hacia abajo, medí los ángulos roll, pitch y yaw.
4. Actualizá en `aruco_relative_pose/config.yaml`:
   ```yaml
   camera:
     fixed_pose_world:
       x: 0.0      # metros, medido
       y: 0.0      # metros, medido
       z: 1.80     # metros, medido (ejemplo)
       roll: 0.0   # radianes
       pitch: 0.0  # radianes
       yaw: 0.0    # radianes
   ```
5. Si usás `camera_controller.py` para publicar el TF estático, actualizá también `fixed_camera_params.yaml`:
   ```yaml
   camera_controller:
     ros__parameters:
       position_x: 0.0
       position_y: 0.0
       position_z: 1.80   # ← tu valor medido
   ```

---

## 8. Qué nodos lanzar (y qué NO lanzar)

### En simulación lanzás:
1. Gazebo + RViz (`go2_config gazebo.launch.py`)
2. Marine platform simulator (`go2_tools marine_platform_simulator`)
3. Fixed camera launch (`fixed_camera fixed_camera.launch.py`) — que incluye spawn en Gazebo, robot_state_publisher, camera_controller y aruco_detector

### En real lanzás:
1. **Driver de cámara** — por ejemplo `v4l2_camera`
2. **camera_controller** (opcional) — solo si necesitás el TF estático `world → camera_base_link` para evaluación
3. **aruco_detector** — el nodo principal, configurado con los topics de tu cámara real

**NO lanzás:** Gazebo, spawn_entity, marine_platform_simulator, robot_state_publisher de la cámara.

Ejemplo mínimo de lanzamiento en real:
```bash
# Terminal 1: Driver de cámara
ros2 run v4l2_camera v4l2_camera_node --ros-args \
  -p video_device:="/dev/video0" \
  -p camera_info_url:="file:///home/linar/calibration.yaml"

# Terminal 2: Detector ArUco
ros2 run fixed_camera aruco_detector --ros-args \
  -p image_topic:="/image_raw" \
  -p camera_info_topic:="/camera_info" \
  -p use_sim_time:=false

# Terminal 3: Verificación visual
ros2 run rqt_image_view rqt_image_view
# Seleccionar /aruco/debug_image

# Terminal 4: Ver pose estimada
ros2 topic echo /aruco/pose
```

---

## 9. Ground truth en el laboratorio

En simulación el ground truth viene de la odometría de CHAMP y la pose del dron en Gazebo. En real no tenés esa "verdad" gratis.

| Método | Precisión | Complejidad |
|---|---|---|
| **Motion capture** (OptiTrack, Vicon) | Sub-milimétrica | Alta (requiere sistema instalado) |
| **Odometría del Go2** (SDK Unitree) | ~cm, con drift | Media (necesitás el SDK de Unitree corriendo con ROS2) |
| **Posición estática conocida** | Depende de tu medición | Baja (poné el robot en un lugar fijo y medí con cinta) |

Para una primera validación, lo más práctico es poner el Go2 en una posición estática conocida, medir su posición real con cinta métrica y comparar con lo que reporta `/aruco/pose`.

Si necesitás el script `evaluate_realtime_aruco.py`, vas a necesitar tener algún topic de pose del robot publicándose en el rosbag para poder comparar. El topic que usa depende de la fuente de cámara:
- `fixed_camera` → usa odometría del Go2 (`/odom`) + pose de la cámara fija
- `sjtu_drone` → usa odometría del Go2 + pose del dron

---

## 10. Checklist final

- [ ] ArUco impreso, medido (0.50 m de lado) y montado plano sobre el Go2
- [ ] Cámara montada a altura conocida, mirando hacia abajo
- [ ] Driver ROS2 de la cámara instalado y publicando `/image_raw` + `/camera_info`
- [ ] Cámara calibrada (matrix K + dist_coeffs D)
- [ ] `aruco_detector_params.yaml` actualizado con topics reales y `use_sim_time: false`
- [ ] `config.yaml` actualizado con intrínsecos reales y pose de cámara medida
- [ ] Verificar detección con `rqt_image_view` en `/aruco/debug_image`
- [ ] Verificar pose con `ros2 topic echo /aruco/pose`
- [ ] (Opcional) Grabar rosbag: `ros2 bag record /image_raw /camera_info /aruco/pose /aruco/detection /odom`

---

## 11. Simulación marina en el Go2 real

El nodo `marine_platform_simulator` ahora soporta un parámetro `mode` que permite enviar los comandos de wave motion directamente al Go2 real via la API de Sport Mode de Unitree (sin Gazebo).

### 11.1 Prerequisitos

1. **unitree_ros2 compilado** — los paquetes de mensajes (`unitree_api`, `unitree_go`) deben estar compilados:
   ```bash
   # Si no está clonado:
   cd ~ && git clone https://github.com/unitreerobotics/unitree_ros2
   
   # Compilar mensajes:
   cd ~/unitree_ros2/cyclonedds_ws
   source /opt/ros/humble/setup.bash
   colcon build --packages-select unitree_go unitree_api
   ```

2. **CycloneDDS como RMW** — Unitree usa CycloneDDS. Hay que exportar estas variables antes de lanzar nodos:
   ```bash
   export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
   export CYCLONEDDS_URI='<CycloneDDS><Domain><General><Interfaces>
       <NetworkInterface name="enp2s0" priority="default" multicast="default" />
   </Interfaces></General></Domain></CycloneDDS>'
   ```
   Cambiar `enp2s0` por tu interfaz Ethernet real (verificar con `ip link show`).

3. **Red configurada** — El PC debe tener IP `192.168.123.99/24` en la interfaz Ethernet conectada al Go2:
   ```bash
   # Verificar
   ip addr show enp2s0
   
   # Si no está configurada:
   sudo ip addr add 192.168.123.99/24 dev enp2s0
   ```

4. **Verificar comunicación** — Con el Go2 encendido:
   ```bash
   source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
   export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
   ros2 topic list
   # Deberías ver: /sportmodestate, /api/sport/request, /lowstate, etc.
   ```

### 11.2 Cómo funciona

En modo `real`, el nodo:
1. **Inicializa** el robot: `RecoveryStand` → `BalanceStand` → `SwitchJoystick(false)`
2. **Envía periódicamente** (10 Hz):
   - `Euler(roll, pitch, 0)` — controla la orientación del cuerpo (API 1007)
   - `BodyHeight(heave)` — controla la altura relativa (API 1013)
   - `BalanceStand()` — mantiene el modo balance activo (API 1002)
3. **Aplica rampa de arranque** — escala amplitud de 0% a 100% en los primeros N segundos
4. **Al cerrar (Ctrl+C)**: resetea postura a neutral y reactiva el mando RC

### 11.3 Lanzamiento rápido

```bash
# Opción A: Script automatizado (recomendado)
./run_marine_real.sh                        # Automático, defaults conservadores
./run_marine_real.sh --manual               # Con control por teclado
./run_marine_real.sh --roll 3 --pitch 3     # Custom limits

# Opción B: Manual (más control)
source /opt/ros/humble/setup.bash
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
source ~/gazebo-no-seas-malo/install/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI='<CycloneDDS><Domain><General><Interfaces>
    <NetworkInterface name="enp2s0" priority="default" multicast="default" />
</Interfaces></General></Domain></CycloneDDS>'

ros2 run go2_tools marine_platform_simulator --ros-args \
    -p mode:=real \
    -p real_max_roll_deg:=5.0 \
    -p real_max_pitch_deg:=5.0 \
    -p real_max_heave_m:=0.02 \
    -p wave_frequency:=0.1 \
    -p startup_ramp_seconds:=5.0
```

### 11.4 Parámetros del modo real

| Parámetro | Default | Descripción |
|---|---|---|
| `mode` | `sim` | `'sim'` para Gazebo, `'real'` para Go2 hardware |
| `real_max_roll_deg` | `5.0` | Máx roll en grados (hardware permite hasta ±43°) |
| `real_max_pitch_deg` | `5.0` | Máx pitch en grados |
| `real_max_heave_m` | `0.02` | Máx heave en metros (hardware: -0.18 a +0.03) |
| `startup_ramp_seconds` | `5.0` | Segundos de rampa lineal al arrancar |
| `network_interface` | `enp2s0` | Interfaz Ethernet con el Go2 |
| `wave_frequency` | `0.1` | Frecuencia de olas en Hz |
| `wave_pattern` | `sinusoidal` | `'sinusoidal'` o `'irregular'` |
| `enable_manual` | `false` | `true` para control manual por teclado |

### 11.5 Emergency Stop

- **Desde el control manual**: Presionar **SPACE** envía señal de emergencia → el robot entra en modo **Damp** (todos los motores se detienen en amortiguación).
- **Desde terminal**: `Ctrl+C` ejecuta un shutdown seguro (resetea postura, reactiva RC).
- **Siempre tener el mando RC a mano** como backup. Después de un emergency stop, el mando se puede reactivar reiniciando el nodo o presionando L2+A en el mando.

### 11.6 Versión de software del Go2

La API usada asume Go2 con software **< V1.1.6**. Si tu Go2 tiene versión **>= V1.1.6**, la interfaz de Sport Services es V2.0 y los API IDs pueden ser diferentes. Verificar en: https://support.unitree.com/home/en/developer/Motion_Services_Interface_V2.0

Para ver la versión, revisar la app de Unitree o consultar `/sportmodestate`.

### 11.7 Troubleshooting

| Problema | Solución |
|---|---|
| `No se encontraron los mensajes de Unitree` | Hacer `source ~/unitree_ros2/cyclonedds_ws/install/setup.bash` antes de lanzar |
| `ros2 topic list` no muestra topics del Go2 | Verificar IP y que `CYCLONEDDS_URI` apunta a la interfaz correcta |
| El robot no se mueve | Verificar que está en modo `BalanceStand` (mode=1 en `/sportmodestate`) |
| Movimientos erráticos | Reducir `real_max_roll_deg` y `real_max_pitch_deg`. Aumentar `startup_ramp_seconds` |
| `BodyHeight` no responde | Puede ser limitación de versión. El heave funciona solo con Euler en ese caso |
