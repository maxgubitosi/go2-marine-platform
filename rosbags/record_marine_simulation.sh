#!/bin/bash
# Uso: ./record_marine_simulation.sh [duración_en_segundos]

set -e

# Source ROS 2 environment
source /opt/ros/humble/setup.bash

# Detectar automáticamente el workspace (directorio padre de rosbags)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"
BAG_DIR="$WORKSPACE_DIR/rosbags"
DURATION=${1:-60}

# Crear carpeta de bags si no existe
mkdir -p "$BAG_DIR"

# Timestamp para nombre único
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BAG_NAME="marine_sim_${TIMESTAMP}"

echo "=================================="
echo "  GRABANDO SIMULACIÓN MARINA"
echo "=================================="
echo "Workspace: $WORKSPACE_DIR"
echo "Carpeta bags: $BAG_DIR"
echo "Rosbag: $BAG_NAME"
echo "Duración: $DURATION segundos"
echo "=================================="

# Verificar que la simulación esté corriendo
echo "Verificando que la simulación esté activa..."
if ! ros2 topic list 2>/dev/null | grep -q "/clock"; then
    echo "❌ ERROR: La simulación no está corriendo."
    exit 1
fi

echo "✅ Simulación detectada"

# Cambiar al workspace y source
cd "$WORKSPACE_DIR"
source install/setup.bash

# Lista de topics a grabar
TOPICS=(
    /tf
    /tf_static
    /joint_states
    /odom
    /cmd_vel
    /imu/data
    /marine_motion
)

echo "💾 Iniciando grabación de rosbag..."
ros2 bag record "${TOPICS[@]}" -o "$BAG_DIR/$BAG_NAME" > /dev/null 2>&1 &
BAG_PID=$!

sleep 3

echo "🎥 Iniciando grabación de video de cámara..."
cd "$BAG_DIR/$BAG_NAME"
ros2 run image_view video_recorder image:=/drone/camera/image_raw > /dev/null 2>&1 &
VIDEO_PID=$!
cd "$WORKSPACE_DIR"

echo "⏱️  Grabando durante ${DURATION} segundos..."
sleep "$DURATION"

echo "🛑 Deteniendo grabación..."
kill -SIGINT $BAG_PID 2>/dev/null
sleep 2
kill -SIGINT $VIDEO_PID 2>/dev/null
sleep 2

echo "=================================="
echo "  GRABACIÓN COMPLETADA"
echo "=================================="