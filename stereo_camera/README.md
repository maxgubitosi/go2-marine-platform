# Stereo Camera — Calibración y Detección ArUco

Carpeta de trabajo para la cámara estéreo **3D USB Camera** (`32e4:0035`),
usada en modo **monocular** (un solo lente) para detección de marcadores
ArUco sobre el Unitree Go2.

## Hardware

| Parámetro | Valor |
|-----------|-------|
| **Dispositivo** | `/dev/video2` |
| **USB ID** | `32e4:0035` |
| **Tipo** | Estéreo side-by-side |
| **Frame completo** | 3840×1080 (MJPG, hasta 60 fps) |
| **Por ojo** | 1920×1080 |
| **Uso** | Un solo lente (left o right), selección en paso 1 |

## Flujo de trabajo

```
01_preview  →  02_capture  →  03_calibrate  →  04_validate  →  05_detect
```

### Paso 1: Previsualizar y elegir lente

```bash
cd stereo_camera
python3 scripts/01_preview_stereo.py
```

- Muestra ambos lentes lado a lado
- Presiona **L** (izquierdo) o **R** (derecho) para seleccionar
- La elección se guarda en `config.yaml` → `camera.selected_eye`
- Presiona **Q** para salir

### Paso 2: Capturar imágenes del checkerboard

```bash
python3 scripts/02_capture_calibration.py
```

- Muestra el feed del lente seleccionado
- Detecta esquinas del checkerboard (3×4 interiores) en tiempo real
- Cuando aparece **DETECTADO** en verde, presiona **SPACE** para capturar
- Objetivo: **20-30 imágenes** con el tablero en distintas posiciones y ángulos
- Las imágenes se guardan en `calibration/images/`

**Tips para buenas capturas:**
- Cubrir toda el área del frame (esquinas, centro, bordes)
- Variar la inclinación del tablero (no solo frontal)
- Variar la distancia (cerca y lejos)
- Evitar motion blur (mantener tablero quieto al capturar)
- Buena iluminación uniforme

### Paso 3: Calibrar

```bash
python3 scripts/03_calibrate.py
```

- Procesa todas las imágenes capturadas
- Ejecuta `cv2.calibrateCamera()` con checkerboard 3×4, cuadro 200mm
- Muestra error RMS de reproyección (objetivo: **< 1.0 px**, ideal **< 0.5 px**)
- Guarda resultados en:
  - `calibration/calibration_result.yaml` (formato completo, compatible ROS)
  - `config.yaml` → sección `intrinsics` (actualización automática)

### Paso 4: Validar calibración

```bash
python3 scripts/04_validate_calibration.py
```

- Muestra lado a lado: original vs undistorted
- Líneas horizontales amarillas de referencia
- Verificar que líneas rectas se ven rectas en la imagen corregida
- Presiona **C** para capturar pares de comparación

### Paso 5: Detección ArUco en vivo

```bash
python3 scripts/05_detect_aruco.py
```

- Detecta marcadores `DICT_6X6_250` ID 0 (0.50m de lado)
- Muestra pose 3D: tvec (posición), Euler (roll/pitch/yaw), distancia
- Dibuja ejes 3D sobre el marcador
- Presiona **U** para toggle undistort on/off
- Presiona **C** para capturar frames con detección

## Checkerboard

- **Patrón**: 4×5 cuadrados → **3×4 esquinas interiores**
- **Tamaño total**: ~80.2×99.9 cm
- **Tamaño cuadro**: ~200 mm

## Configuración

Todo centralizado en [`config.yaml`](config.yaml):

- `camera` — dispositivo, resolución, lente seleccionado
- `calibration` — parámetros del checkerboard
- `intrinsics` — matriz K y distorsión (se llena tras calibración)
- `aruco` — diccionario, ID, tamaño del marcador
- `mounting` — pose de la cámara en el mundo (a medir)

## Estructura

```
stereo_camera/
├── config.yaml                       # Configuración centralizada
├── README.md                         # Este archivo
├── requirements.txt                  # Dependencias Python
├── calibration/
│   ├── images/                       # Imágenes capturadas para calibración
│   ├── calibration_result.yaml       # Resultado de calibración (tras paso 3)
│   ├── validation/                   # Pares original/undistorted (paso 4)
│   └── detections/                   # Capturas de detección ArUco (paso 5)
├── scripts/
│   ├── 01_preview_stereo.py          # Previsualizar y elegir lente
│   ├── 02_capture_calibration.py     # Capturar imágenes del checkerboard
│   ├── 03_calibrate.py               # Ejecutar calibración OpenCV
│   ├── 04_validate_calibration.py    # Validar visualmente
│   └── 05_detect_aruco.py           # Detección ArUco standalone
└── launch/                           # (futuro) launch files ROS2
```

## Integración con ROS2 (siguiente paso)

Una vez validada la calibración con el paso 5:

1. Copiar `calibration/calibration_result.yaml` como archivo de calibración para `v4l2_camera`:
   ```bash
   ros2 run v4l2_camera v4l2_camera_node --ros-args \
     -p video_device:="/dev/video2" \
     -p camera_info_url:="file:///path/to/calibration_result.yaml"
   ```

2. Actualizar intrínsecos en `aruco_relative_pose/config.yaml` con los valores de `stereo_camera/config.yaml`

3. Configurar el nodo `aruco_detector` para los topics de la cámara real

**Nota**: La cámara entrega frame estéreo side-by-side. Para ROS2, se necesitará
un nodo intermedio que recorte el lente seleccionado, o usar el script standalone
como puente.

## Dependencias

```bash
pip install -r requirements.txt
```

Requiere: `opencv-contrib-python>=4.5.0`, `numpy>=1.21.0`, `PyYAML>=5.4.0`
