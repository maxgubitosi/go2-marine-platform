#!/bin/bash
# Graba todos los datos de la simulación marina en un rosbag.
# Las imágenes de la cámara se graban en el rosbag con sus timestamps ROS exactos.
# Uso: ./record_marine_simulation.sh [duración_en_segundos]

set -e

source /opt/ros/humble/setup.bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"
BAG_DIR="$WORKSPACE_DIR/rosbags"
DURATION=${1:-60}

mkdir -p "$BAG_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BAG_NAME="marine_sim_${TIMESTAMP}"

echo "=================================="
echo "  GRABANDO SIMULACIÓN MARINA"
echo "=================================="
echo "Workspace: $WORKSPACE_DIR"
echo "Rosbag: $BAG_NAME"
echo "Duración: $DURATION segundos"
echo "=================================="

if ! ros2 topic list 2>/dev/null | grep -q "/clock"; then
    echo "ERROR: La simulación no está corriendo."
    exit 1
fi
echo "Simulación detectada"

cd "$WORKSPACE_DIR"
source install/setup.bash

TOPICS=(
    /tf
    /tf_static
    /joint_states
    /odom
    /cmd_vel
    /imu/data
    /marine_motion
    /drone/camera/image_raw
    /drone/camera/camera_info
    /drone/pose
    /base_to_footprint_pose
    /aruco/pose
    /aruco/detection
)

echo "Iniciando grabación..."
ros2 bag record "${TOPICS[@]}" -o "$BAG_DIR/$BAG_NAME" > /dev/null 2>&1 &
BAG_PID=$!

echo "Grabando durante ${DURATION} segundos..."
sleep "$DURATION"

echo "Deteniendo grabación..."
kill -SIGINT $BAG_PID 2>/dev/null
wait $BAG_PID 2>/dev/null || true

echo "=================================="
echo "  GRABACIÓN COMPLETADA"
echo "=================================="
echo "Rosbag: $BAG_DIR/$BAG_NAME"