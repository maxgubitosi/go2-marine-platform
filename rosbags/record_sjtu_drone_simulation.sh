#!/bin/bash
# Graba todos los datos de la simulación marina con el sjtu_drone.
# Incluye: cámara bottom, pose del dron, ArUco, TF, IMU, odometría del Go2.
# Uso: ./record_sjtu_drone_simulation.sh [duración_en_segundos] [sufijo_opcional]
# Ejemplo: ./record_sjtu_drone_simulation.sh 60 calm

set -e

source /opt/ros/humble/setup.bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"
BAG_DIR="$WORKSPACE_DIR/rosbags"
DURATION=${1:-60}
SUFFIX=${2:-""}

mkdir -p "$BAG_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
if [ -n "$SUFFIX" ]; then
    BAG_NAME="sjtu_drone_sim_${TIMESTAMP}_${SUFFIX}"
else
    BAG_NAME="sjtu_drone_sim_${TIMESTAMP}"
fi

echo "=================================="
echo "  GRABANDO SIMULACIÓN SJTU_DRONE"
echo "=================================="
echo "Workspace: $WORKSPACE_DIR"
echo "Rosbag: $BAG_NAME"
echo "Duración: $DURATION segundos"
echo "=================================="

# Verificar que la simulación está corriendo
if ! ros2 topic list 2>/dev/null | grep -q "/clock"; then
    echo "ERROR: La simulación no está corriendo."
    exit 1
fi
echo "✓ Simulación detectada"

# Verificar que el sjtu_drone está activo
if ! ros2 topic list 2>/dev/null | grep -q "/drone/bottom/image_raw"; then
    echo "WARNING: No se detectó /drone/bottom/image_raw. ¿El sjtu_drone está spawneado?"
fi

cd "$WORKSPACE_DIR"
source install/setup.bash

TOPICS=(
    # TF y tiempo
    /tf
    /tf_static
    /clock

    # Go2 robot (plataforma marina)
    /joint_states
    /odom
    /cmd_vel
    /imu/data
    /marine_motion
    /base_to_footprint_pose

    # sjtu_drone - cámara bottom (la que mira al ArUco)
    /drone/bottom/image_raw
    /drone/bottom/camera_info

    # sjtu_drone - cámara frontal (opcional, comentar si no se necesita)
    # /drone/front/image_raw
    # /drone/front/camera_info

    # sjtu_drone - estado y pose
    /drone/gt_pose
    /drone/gt_vel
    /drone/state
    /drone/pose

    # sjtu_drone - control
    /drone/cmd_vel
    /drone/posctrl
    /drone/takeoff
    /drone/land

    # sjtu_drone - sensores
    /drone/imu
    /drone/sonar

    # ArUco detección
    /aruco/pose
    /aruco/detection
    /aruco/debug_image
)

echo ""
echo "Topics a grabar:"
for t in "${TOPICS[@]}"; do
    # Saltar comentarios
    [[ "$t" == \#* ]] && continue
    # Verificar si el topic existe
    if ros2 topic list 2>/dev/null | grep -q "^${t}$"; then
        echo "  ✓ $t"
    else
        echo "  ✗ $t (no disponible)"
    fi
done
echo ""

echo "Iniciando grabación..."
ros2 bag record "${TOPICS[@]}" -o "$BAG_DIR/$BAG_NAME" > /dev/null 2>&1 &
BAG_PID=$!

echo "Grabando durante ${DURATION} segundos... (Ctrl+C para detener antes)"

# Capturar Ctrl+C para detener limpiamente
trap "echo ''; echo 'Deteniendo grabación (Ctrl+C)...'; kill -SIGINT $BAG_PID 2>/dev/null; wait $BAG_PID 2>/dev/null || true; echo 'Grabación detenida.'; exit 0" INT

sleep "$DURATION"

echo "Deteniendo grabación..."
kill -SIGINT $BAG_PID 2>/dev/null
wait $BAG_PID 2>/dev/null || true

echo ""
echo "=================================="
echo "  GRABACIÓN COMPLETADA"
echo "=================================="
echo "Rosbag: $BAG_DIR/$BAG_NAME"

# Mostrar info del bag
if command -v ros2 &> /dev/null; then
    echo ""
    echo "Info del bag:"
    ros2 bag info "$BAG_DIR/$BAG_NAME" 2>/dev/null || true
fi
