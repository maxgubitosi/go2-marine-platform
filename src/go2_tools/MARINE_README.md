# Marine Platform Simulator - Unitree Go2

Simulador de plataforma marina usando el robot cuadrúpedo Unitree Go2. Este sistema permite simular los movimientos de heave (vertical), pitch (cabeceo) y roll (balanceo) característicos de una embarcación en el mar.

## 🌊 Características Principales

- **Simulación automática de olas**: Patrones sinusoidales e irregulares
- **Control manual interactivo**: Interfaz de teclado para control directo
- **Movimientos suaves**: Sistema de filtrado para evitar saltos bruscos
- **Límites de seguridad**: Configuración de rangos máximos de movimiento
- **Visualización en tiempo real**: Integración con RViz y topics de debug
- **Parámetros configurables**: Ajuste dinámico de comportamiento

## 🚀 Inicio Rápido

### Pasos para ejecutar la simulación actual:

```bash
# Terminal 1: Construir y lanzar Gazebo
cd /home/linar/Proyecto-Final
colcon build --packages-select go2_tools --symlink-install
source install/setup.bash
ros2 launch go2_config gazebo.launch.py

# Terminal 2: Lanzar simulador marino
cd /home/linar/Proyecto-Final
source install/setup.bash
ros2 run go2_tools marine_platform_simulator --ros-args -p enable_manual:=False
```

### Uso del script automático:
```bash
# Ejecutar todo automáticamente
cd /home/linar/Proyecto-Final
./run_marine_simulation.sh
```

## 📦 Instalación y Construcción

```bash
# Navegar al workspace
cd /home/linar/Proyecto-Final

# Construir el paquete con symlink
colcon build --packages-select go2_tools --symlink-install

# Sourcing del workspace
source install/setup.bash

# Verificar que los ejecutables están disponibles
ros2 pkg executables go2_tools
```

## 🎮 Uso Detallado

### 1. Marine Platform Simulator (`marine_platform_simulator.py`)

Este es el nodo principal que genera los comandos de movimiento marino.

#### Inicio del Simulador

```bash
# Modo automático (por defecto)
ros2 run go2_tools marine_platform_simulator --ros-args -p enable_manual:=False

# Con parámetros personalizados
ros2 run go2_tools marine_platform_simulator \
    --ros-args \
    -p enable_manual:=False \
    -p max_roll_deg:=20.0 \
    -p max_pitch_deg:=15.0 \
    -p wave_frequency:=0.15 \
    -p wave_pattern:=irregular
```

#### Parámetros Configurables

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| `rate_hz` | 20.0 | Frecuencia de publicación en Hz |
| `wave_frequency` | 0.1 | Frecuencia de las olas en Hz |
| `max_roll_deg` | 15.0 | Máximo balanceo en grados |
| `max_pitch_deg` | 10.0 | Máximo cabeceo en grados |
| `max_heave_m` | 0.1 | Máximo heave en metros |
| `enable_manual` | false | Activar control manual |
| `wave_pattern` | 'sinusoidal' | Tipo: 'sinusoidal' o 'irregular' |
| `phase_offset_pitch` | 1.0 | Desfase entre roll y pitch |
| `phase_offset_heave` | 1.5 | Desfase entre roll y heave |
| `smoothing_factor` | 0.95 | Factor de suavizado (0-1) |

#### Modos de Operación

**Modo Automático (Default)**:
- Genera ondas sinusoidales continuas
- Simula movimiento realista de una embarcación
- Dos patrones disponibles: 'sinusoidal' (suave) e 'irregular' (complejo)

**Modo Manual**:
- Responde a comandos del topic `/marine_platform/manual_cmd`
- Útil para testing y control directo
- Se activa con `enable_manual:=true`

#### Topics ROS

**Publicados**:
- `/go2/pose_rphz_cmd` (Float64MultiArray): Comandos de pose [roll°, pitch°, heave_m]
- `/marine_platform/debug_state` (Vector3): Estado actual para visualización

**Suscritos**:
- `/marine_platform/manual_cmd` (Float64MultiArray): Comandos manuales [roll°, pitch°, heave_m]

### 2. Marine Manual Control (`marine_manual_control.py`)

Interfaz de control manual por teclado para el simulador marino.

#### Uso del Control Manual

```bash
# Iniciar control manual (en terminal separado)
cd /home/linar/Proyecto-Final
source install/setup.bash
ros2 run go2_tools marine_manual_control
```

#### Para usar control manual, cambiar el parámetro del simulador:
```bash
# En otro terminal, cambiar a modo manual
ros2 param set /marine_platform_simulator enable_manual true
```

#### Controles de Teclado

| Tecla | Función | Descripción |
|-------|---------|-------------|
| `w` | Pitch + | Cabeceo hacia adelante (+2°) |
| `s` | Pitch - | Cabeceo hacia atrás (-2°) |
| `a` | Roll - | Balanceo hacia izquierda (-2°) |
| `d` | Roll + | Balanceo hacia derecha (+2°) |
| `q` | Heave + | Subir (+0.02m) |
| `e` | Heave - | Bajar (-0.02m) |
| `r` | Reset | Volver a posición neutral (0,0,0) |
| `ESC` | Salir | Terminar control manual |

#### Características del Control Manual

- **Interfaz en tiempo real**: Muestra valores actuales en la terminal
- **Límites de seguridad**: 
  - Roll: ±20°
  - Pitch: ±15°
  - Heave: ±0.15m
- **Incrementos configurables**: 2° para ángulos, 0.02m para heave
- **Restauración automática**: Envía comando neutral al salir

#### Salida de Ejemplo

```
==================================================
   CONTROL MANUAL - PLATAFORMA MARINA
==================================================
Controles:
  w/s: Pitch +/- (cabeceo)
  a/d: Roll +/- (balanceo)  
  q/e: Heave +/- (vertical)
  r:   Reset a posición neutral
  ESC: Salir
==================================================
Roll:   +4.0° | Pitch:  -2.0° | Heave: +0.040m
```

## 🔧 Uso Avanzado

### Control Híbrido (Automático + Manual)

```bash
# Terminal 1: Simulador en modo manual
ros2 run go2_tools marine_platform_simulator \
    --ros-args -p enable_manual:=true

# Terminal 2: Control manual
ros2 run go2_tools marine_manual_control

# Terminal 3: Comandos directos por topic
ros2 topic pub /marine_platform/manual_cmd std_msgs/msg/Float64MultiArray \
    "data: [10.0, -5.0, 0.08]"
```

### Configuración de Olas Personalizadas

```bash
# Olas suaves de mar calmo
ros2 run go2_tools marine_platform_simulator \
    --ros-args \
    -p max_roll_deg:=5.0 \
    -p max_pitch_deg:=3.0 \
    -p max_heave_m:=0.03 \
    -p wave_frequency:=0.05

# Olas fuertes de tormenta
ros2 run go2_tools marine_platform_simulator \
    --ros-args \
    -p max_roll_deg:=25.0 \
    -p max_pitch_deg:=20.0 \
    -p max_heave_m:=0.15 \
    -p wave_frequency:=0.2 \
    -p wave_pattern:=irregular
```

### Cambio Dinámico de Parámetros

```bash
# Cambiar a modo manual en tiempo real
ros2 param set /marine_platform_simulator enable_manual true

# Ajustar intensidad de olas
ros2 param set /marine_platform_simulator max_roll_deg 20.0
ros2 param set /marine_platform_simulator wave_frequency 0.15

# Volver a modo automático
ros2 param set /marine_platform_simulator enable_manual false
```

## 📊 Monitoreo y Debug

### Visualización de Estado

```bash
# Ver comandos generados
ros2 topic echo /go2/pose_rphz_cmd

# Ver estado del simulador (para gráficos)
ros2 topic echo /marine_platform/debug_state

# Información de frecuencia
ros2 topic hz /go2/pose_rphz_cmd
```

### Análisis de Parámetros

```bash
# Ver todos los parámetros activos
ros2 param list /marine_platform_simulator

# Ver valor específico
ros2 param get /marine_platform_simulator wave_frequency

# Ver información del nodo
ros2 node info /marine_platform_simulator
```

### Logs del Sistema

```bash
# Ver logs del simulador
ros2 log show /marine_platform_simulator

# Ver logs del control manual
ros2 log show /marine_manual_control
```

## 🛠️ Solución de Problemas

### Error de build
```bash
# Limpiar build anterior
rm -rf build/ install/ log/
colcon build --packages-select go2_tools --symlink-install
```

### El simulador no publica comandos

```bash
# Verificar que el nodo está corriendo
ros2 node list | grep marine

# Verificar topics
ros2 topic list | grep go2

# Revisar logs
ros2 log show /marine_platform_simulator
```

### Gazebo no se inicia

```bash
# Verificar que el launch file existe
ls install/go2_config/share/go2_config/launch/

# Verificar que ROS2 está correctamente configurado
echo $ROS_DOMAIN_ID
```

### El control manual no responde

- **Problema**: Terminal no captura teclas correctamente
- **Solución**: Asegúrate de que la terminal tiene foco y no hay otros programas interceptando el teclado

```bash
# Si el terminal queda "colgado", ejecutar:
reset
# O presionar Ctrl+C varias veces
```

### Movimientos muy bruscos

```bash
# Aumentar el suavizado
ros2 param set /marine_platform_simulator smoothing_factor 0.98

# Reducir la frecuencia
ros2 param set /marine_platform_simulator rate_hz 10.0

# Reducir amplitudes
ros2 param set /marine_platform_simulator max_roll_deg 8.0
```

### Movimientos muy lentos/pequeños

```bash
# Aumentar amplitudes
ros2 param set /marine_platform_simulator max_roll_deg 20.0
ros2 param set /marine_platform_simulator max_pitch_deg 15.0

# Aumentar frecuencia de olas
ros2 param set /marine_platform_simulator wave_frequency 0.15

# Usar patrón irregular para más variación
ros2 param set /marine_platform_simulator wave_pattern irregular
```

## 🏗️ Arquitectura del Sistema

```
marine_platform_simulator ──→ /go2/pose_rphz_cmd ──→ [Robot Controller]
         ↑                              ↓
/marine_platform/manual_cmd        [Robot Movement]
         ↑
marine_manual_control
```

### Flujo de Datos

1. **Marine Platform Simulator** genera comandos de movimiento
2. Los comandos se publican en `/go2/pose_rphz_cmd`
3. El controlador del robot recibe y ejecuta los comandos
4. **Marine Manual Control** puede override los comandos automáticos
5. El estado se publica en `/marine_platform/debug_state` para monitoreo

## 🔮 Funcionalidades Avanzadas

### Algoritmos de Generación de Olas

**Sinusoidal Simple**:
```python
roll = max_roll * sin(ωt)
pitch = max_pitch * sin(ωt * phase_pitch + π/3)
heave = max_heave * sin(ωt * phase_heave)
```

**Irregular (Multi-frecuencia)**:
```python
roll = max_roll * (0.6*sin(ωt) + 0.3*sin(1.3ωt + π/4) + 0.1*sin(2.1ωt + π/2))
```

### Sistema de Suavizado

- **Filtro exponencial**: Previene movimientos bruscos
- **Límites de velocidad**: Implícitos en el factor de suavizado
- **Continuidad**: Asegura transiciones suaves entre comandos

## 📚 Ejemplos de Uso Completos

### Ejemplo 1: Simulación de Mar Calmo

```bash
# Terminal 1: Gazebo
cd /home/linar/Proyecto-Final
source install/setup.bash
ros2 launch go2_config gazebo.launch.py

# Terminal 2: Simulador configurado para mar calmo
cd /home/linar/Proyecto-Final
source install/setup.bash
ros2 run go2_tools marine_platform_simulator \
    --ros-args \
    -p enable_manual:=False \
    -p max_roll_deg:=3.0 \
    -p max_pitch_deg:=2.0 \
    -p max_heave_m:=0.02 \
    -p wave_frequency:=0.03
```

### Ejemplo 2: Control Manual Interactivo

```bash
# Terminal 1: Gazebo
cd /home/linar/Proyecto-Final
source install/setup.bash
ros2 launch go2_config gazebo.launch.py

# Terminal 2: Simulador en modo manual
cd /home/linar/Proyecto-Final
source install/setup.bash
ros2 run go2_tools marine_platform_simulator \
    --ros-args -p enable_manual:=True

# Terminal 3: Control manual
cd /home/linar/Proyecto-Final
source install/setup.bash
ros2 run go2_tools marine_manual_control
```

## 🎯 Notas Importantes

- **Symlink Install**: Se usa `--symlink-install` para permitir modificaciones en el código sin reconstruir
- **Workspace Path**: El proyecto debe estar en `/home/linar/Proyecto-Final`
- **Launch File**: Se usa `go2_config gazebo.launch.py` en lugar del anterior `champ_config`
- **Parámetros**: Siempre especificar `enable_manual:=False` para modo automático

### Ejemplo 3: Transición Automático → Manual → Automático

```bash
# Terminal 1: Simulador (inicia automático)
ros2 run go2_tools marine_platform_simulator

# Terminal 2: Cambiar a manual y ajustar parámetros
ros2 param set /marine_platform_simulator enable_manual true
ros2 topic pub /marine_platform/manual_cmd std_msgs/msg/Float64MultiArray \
    "data: [15.0, 10.0, 0.05]"

# Volver a automático
ros2 param set /marine_platform_simulator enable_manual false
```

## 🎯 Próximas Mejoras

- [ ] Patrones de olas basados en datos oceanográficos reales
- [ ] Interfaz gráfica web para control manual
- [ ] Grabación y reproducción de secuencias de movimiento
- [ ] Integración con sensores IMU para feedback realista
- [ ] Modelos de perturbación atmosférica (viento)
- [ ] Simulación de diferentes tipos de embarcaciones
