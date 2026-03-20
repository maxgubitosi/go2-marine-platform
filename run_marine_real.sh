#!/bin/bash

# =============================================================================
# Script para lanzar simulación marina en el Go2 REAL
# Envía comandos Euler/BalanceStand via unitree_api al robot conectado por
# Ethernet (192.168.123.x)
#
# Prerequisitos:
#   1. Go2 encendido y conectado por cable Ethernet
#   2. IP del PC configurada a 192.168.123.99/24 en la interfaz correcta
#   3. unitree_sdk2py instalado (pip3 install --user unitree_sdk2_python)
#   4. Workspace local compilado
#
# Uso:
#   ./run_marine_real.sh                    # Modo automático, parámetros default
#   ./run_marine_real.sh --manual           # Modo manual (abre ventana de control)
#   ./run_marine_real.sh --roll 3 --pitch 3 # Custom limits (grados)
# =============================================================================

set -e

echo "============================================"
echo "  Marine Platform — Unitree Go2 REAL"
echo "============================================"

# ===== Configuración por defecto =====
MANUAL=false
MAX_ROLL=20.0
MAX_PITCH=15.0
MAX_HEAVE=0.04
WAVE_FREQ=0.15
WAVE_PATTERN="irregular"
RAMP_SECONDS=3.0
NETWORK_IFACE="enp2s0"

# ===== Parse argumentos =====
while [[ $# -gt 0 ]]; do
    case $1 in
        --manual)
            MANUAL=true
            shift ;;
        --roll)
            MAX_ROLL="$2"
            shift 2 ;;
        --pitch)
            MAX_PITCH="$2"
            shift 2 ;;
        --heave)
            MAX_HEAVE="$2"
            shift 2 ;;
        --freq)
            WAVE_FREQ="$2"
            shift 2 ;;
        --pattern)
            WAVE_PATTERN="$2"
            shift 2 ;;
        --ramp)
            RAMP_SECONDS="$2"
            shift 2 ;;
        --iface)
            NETWORK_IFACE="$2"
            shift 2 ;;
        --help|-h)
            echo "Uso: $0 [opciones]"
            echo ""
            echo "Opciones:"
            echo "  --manual          Modo manual (abre control por teclado)"
            echo "  --roll  DEG       Máx roll en grados (default: $MAX_ROLL)"
            echo "  --pitch DEG       Máx pitch en grados (default: $MAX_PITCH)"
            echo "  --heave M         Máx heave en metros (default: $MAX_HEAVE)"
            echo "  --freq  HZ        Frecuencia de olas (default: $WAVE_FREQ)"
            echo "  --pattern TYPE    'sinusoidal' o 'irregular' (default: $WAVE_PATTERN)"
            echo "  --ramp  SEC       Rampa de arranque en seg (default: $RAMP_SECONDS)"
            echo "  --iface NAME      Interfaz de red (default: $NETWORK_IFACE)"
            exit 0 ;;
        *)
            echo "Opción desconocida: $1"
            exit 1 ;;
    esac
done

# ===== Verificar interfaz de red =====
if ! ip link show "$NETWORK_IFACE" &>/dev/null; then
    echo "ERROR: Interfaz de red '$NETWORK_IFACE' no encontrada."
    echo "Interfaces disponibles:"
    ip link show | grep -E "^[0-9]+:" | awk '{print "  " $2}' | tr -d ':'
    exit 1
fi

echo "Interfaz de red: $NETWORK_IFACE"

# ===== Verificar IP configurada =====
if ip addr show "$NETWORK_IFACE" | grep -q "192.168.123"; then
    echo "IP detectada: $(ip addr show "$NETWORK_IFACE" | grep 'inet 192.168.123' | awk '{print $2}')"
else
    echo "ADVERTENCIA: No se detectó IP 192.168.123.x en $NETWORK_IFACE"
    echo "Configurar manualmente: sudo ip addr add 192.168.123.99/24 dev $NETWORK_IFACE"
    read -p "¿Continuar de todos modos? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# ===== Source environments =====
cd ~/gazebo-no-seas-malo

echo "Sourcing ROS2 Humble..."
source /opt/ros/humble/setup.bash

# IMPORTANTE: NO usar rmw_cyclonedds_cpp para ROS2.
# unitree_sdk2py usa la librería Python cyclonedds internamente para
# comunicarse con el Go2 (DDS domain 0). Si ROS2 también usa CycloneDDS
# (rmw_cyclonedds_cpp + CYCLONEDDS_URI), ambos compiten por domain 0
# y el DomainParticipant del SDK2 puede unirse al domain equivocado,
# causando error 3102 (publication_matched_count == 0).
#
# Solución: usar FastRTPS (default) para ROS2. Así CycloneDDS es
# exclusivamente para el SDK2.
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
unset CYCLONEDDS_URI 2>/dev/null || true

# NO sourcing unitree_ros2 — no es necesario para SDK2 (pip package),
# y podría contaminar env con CYCLONEDDS_URI
# Si necesitas herramientas de diagnóstico (ros2 topic echo /lowstate),
# ábrelas en otra terminal con source unitree_ros2 + rmw_cyclonedds_cpp.

echo "Sourcing workspace local..."
if [ -f install/setup.bash ]; then
    source install/setup.bash
else
    echo "Workspace no compilado. Compilando..."
    colcon build --symlink-install --packages-select go2_tools
    source install/setup.bash
fi

# Verificar unitree_sdk2py
echo ""
echo "Verificando unitree_sdk2py..."
if python3 -c "from unitree_sdk2py.go2.sport.sport_client import SportClient; print('✓ unitree_sdk2py disponible')" 2>/dev/null; then
    :
else
    echo "ERROR: unitree_sdk2py no instalado."
    echo "Instalar con:"
    echo "  cd /tmp && git clone https://github.com/unitreerobotics/unitree_sdk2_python.git"
    echo "  cd unitree_sdk2_python && pip3 install --user ."
    exit 1
fi

# ===== Verificar conectividad con el Go2 =====
echo ""
echo "Verificando comunicación con Go2 (ping)..."
if ping -c 1 -W 2 192.168.123.161 &>/dev/null; then
    echo "✓ Go2 responde a ping (192.168.123.161)"
else
    echo "ADVERTENCIA: Go2 no responde a ping en 192.168.123.161"
    echo "  (Puede que la IP del Go2 sea diferente)"
    read -p "¿Continuar de todos modos? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# ===== Función de cleanup =====
cleanup() {
    echo ""
    echo "Deteniendo procesos..."
    kill 0 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM

# ===== Mostrar configuración =====
echo ""
echo "============================================"
echo "  Configuración:"
echo "    Modo:     $([ "$MANUAL" = true ] && echo 'MANUAL' || echo 'AUTOMÁTICO')"
echo "    Roll:     ±${MAX_ROLL}°"
echo "    Pitch:    ±${MAX_PITCH}°"
echo "    Heave:    ±${MAX_HEAVE}m"
echo "    Ola freq: ${WAVE_FREQ} Hz"
echo "    Patrón:   ${WAVE_PATTERN}"
echo "    Rampa:    ${RAMP_SECONDS}s"
echo "============================================"
echo ""

# ===== Asegurar que valores numéricos sean float (ROS2 requiere DOUBLE) =====
# Añadir .0 si el valor no tiene punto decimal
ensure_float() {
    local val="$1"
    if [[ "$val" != *.* ]]; then
        echo "${val}.0"
    else
        echo "$val"
    fi
}
MAX_ROLL=$(ensure_float "$MAX_ROLL")
MAX_PITCH=$(ensure_float "$MAX_PITCH")
MAX_HEAVE=$(ensure_float "$MAX_HEAVE")
WAVE_FREQ=$(ensure_float "$WAVE_FREQ")
RAMP_SECONDS=$(ensure_float "$RAMP_SECONDS")

# ===== Lanzar nodo principal =====
echo "Iniciando marine_platform_simulator v2 en modo REAL..."
ros2 run go2_tools marine_platform_simulator --ros-args \
    -p mode:=real \
    -p enable_manual:="$MANUAL" \
    -p real_max_roll_deg:="$MAX_ROLL" \
    -p real_max_pitch_deg:="$MAX_PITCH" \
    -p real_max_heave_m:="$MAX_HEAVE" \
    -p wave_frequency:="$WAVE_FREQ" \
    -p wave_pattern:="$WAVE_PATTERN" \
    -p startup_ramp_seconds:="$RAMP_SECONDS" \
    -p network_interface:="$NETWORK_IFACE" \
    -p sender_rate_hz:=50.0 \
    -p smoothing_tau:=0.08 &

SIMULATOR_PID=$!

# Si modo manual, abrir terminal de control
if [ "$MANUAL" = true ]; then
    sleep 3
    echo "Abriendo control manual..."
    gnome-terminal -- bash -c "
        cd ~/gazebo-no-seas-malo
        source /opt/ros/humble/setup.bash
        source install/setup.bash
        export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
        unset CYCLONEDDS_URI
        ros2 run go2_tools marine_manual_control
        exec bash
    " &
fi

echo ""
echo "Sistema iniciado. Presiona Ctrl+C para detener."
echo "  IMPORTANTE: Ctrl+C enviará shutdown seguro al Go2 (reset postura + reactivar RC)"
echo ""

wait $SIMULATOR_PID
cleanup
