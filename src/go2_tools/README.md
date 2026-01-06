# Go2 Tools

Herramientas para simulación de robot Unitree Go2 en entorno marino. Incluye simulador de movimientos de plataforma marina (heave, pitch, roll) para pruebas de navegación en condiciones marítimas.

## Características

- Simulación automática de movimientos marinos con patrones sinusoidales e irregulares
- Control manual interactivo por teclado
- Sistema de suavizado para movimientos realistas
- Parámetros configurables en tiempo de ejecución
- Publicación de marcador ArUco en plataforma marina

## Uso básico

```bash
# Compilar
colcon build --packages-select go2_tools
source install/setup.bash

# Lanzar simulador de plataforma marina
ros2 run go2_tools marine_platform_simulator
```

## Nodos principales

### marine_platform_simulator

Genera comandos de movimiento marino automáticos o responde a comandos manuales.

**Topics publicados:**
- `/go2/pose_rphz_cmd` - Comandos de pose [roll°, pitch°, heave_m]
- `/marine_platform/debug_state` - Estado actual para visualización

**Topics suscritos:**
- `/marine_platform/manual_cmd` - Comandos manuales [roll°, pitch°, heave_m]

**Parámetros principales:**

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| `wave_frequency` | 0.1 | Frecuencia de las olas (Hz) |
| `max_roll_deg` | 15.0 | Máximo balanceo (grados) |
| `max_pitch_deg` | 10.0 | Máximo cabeceo (grados) |
| `max_heave_m` | 0.1 | Máximo heave (metros) |
| `enable_manual` | false | Activar control manual |
| `wave_pattern` | sinusoidal | Patrón: 'sinusoidal' o 'irregular' |

**Ejemplos:**

```bash
# Mar calmo
ros2 run go2_tools marine_platform_simulator \
    --ros-args \
    -p max_roll_deg:=5.0 \
    -p max_pitch_deg:=3.0 \
    -p wave_frequency:=0.05

# Modo manual
ros2 run go2_tools marine_platform_simulator \
    --ros-args -p enable_manual:=true
```

### marine_manual_control

Interfaz de control manual por teclado para el simulador.

**Controles:**
- `w/s` - Pitch +/-
- `a/d` - Roll +/-
- `q/e` - Heave +/-
- `r` - Reset a posición neutral
- `ESC` - Salir

**Uso:**

```bash
ros2 run go2_tools marine_manual_control
```

## Arquitectura

```
src/go2_tools/
├── go2_tools/
│   ├── marine_platform_simulator.py
│   ├── marine_manual_control.py
│   └── aruco_marker_publisher.py
├── scripts/
│   └── [scripts ejecutables]
└── README.md
```

## Ajustes dinámicos

```bash
# Cambiar parámetros en tiempo real
ros2 param set /marine_platform_simulator wave_frequency 0.15
ros2 param set /marine_platform_simulator enable_manual true

# Monitorear comandos
ros2 topic echo /go2/pose_rphz_cmd
```

## Autores

Maximo Gubitosi, Jack Spolski
