#!/bin/bash

# Script para grabar simulación marina + video de cámara del# Iniciar grabación de video de la cámara en background
echo "🎥 Iniciando grabación de video de cámara..."
cd $BAG_DIR
ros2 run image_view video_recorder image:=/drone/camera/image_raw \
  __params:=filename:=$VIDEO_NAME,fps:=30.0,codec:=mjpeg \
  > /dev/null 2>&1 &
VIDEO_PID=$!
cd $WORKSPACE_DIRUso: ./record_marine_simulation.sh [duración_en_segundos]

set -e

WORKSPACE_DIR=~/gazebo-no-seas-malo
BAG_DIR=$WORKSPACE_DIR/rosbags
DURATION=${1:-60}  # Default: 60 segundos

# Crear carpeta de bags si no existe
mkdir -p $BAG_DIR

# Timestamp para nombre único
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BAG_NAME="marine_sim_${TIMESTAMP}"
VIDEO_NAME="drone_camera_${TIMESTAMP}.avi"

echo "=================================="
echo "  GRABANDO SIMULACIÓN MARINA"
echo "=================================="
echo "Carpeta: $BAG_DIR"
echo "Rosbag: $BAG_NAME"
echo "Video: $VIDEO_NAME"
echo "Duración: $DURATION segundos"
echo "=================================="
echo ""

# Verificar que la simulación esté corriendo
echo "Verificando que la simulación esté activa..."
if ! ros2 topic list | grep -q "/clock"; then
    echo "❌ ERROR: La simulación no está corriendo."
    echo "   Por favor lanzá primero:"
    echo "   Terminal 1: ros2 launch go2_config gazebo.launch.py rviz:=true"
    echo "   Terminal 2: ros2 run go2_tools marine_platform_simulator"
    echo "   Terminal 3: ros2 launch drone drone.launch.py"
    exit 1
fi

if ! ros2 topic list | grep -q "/drone/camera/image_raw"; then
    echo "⚠️  WARNING: El dron no está publicando imágenes."
    echo "   Asegurate de haber lanzado: ros2 launch drone drone.launch.py"
fi

echo "✅ Simulación detectada"
echo ""

# Cambiar al workspace
cd $WORKSPACE_DIR
source install/setup.bash

# Lista de topics a grabar
TOPICS=(
  /body_pose
  /go2/pose_rphz_cmd
  /marine_platform/debug_state
  /joint_states
  /odom
  /tf
  /tf_static
  /clock
  /cmd_vel
  /drone/camera/image_raw
  /drone/camera/camera_info
  /drone/pose
  /drone/robot_description
)

echo "Topics a grabar en rosbag:"
printf '  - %s\n' "${TOPICS[@]}"
echo ""

# Iniciar grabación de rosbag en background (PRIMERO para crear la carpeta)
echo "💾 Iniciando grabación de rosbag..."
ros2 bag record "${TOPICS[@]}" -o $BAG_DIR/$BAG_NAME > /dev/null 2>&1 &
BAG_PID=$!

# Esperar a que se cree la carpeta del bag
sleep 3

# Iniciar grabación de video de la cámara en background DENTRO de la carpeta del bag
echo "🎥 Iniciando grabación de video de cámara..."
cd $BAG_DIR/$BAG_NAME
ros2 run image_view video_recorder image:=/drone/camera/image_raw > /dev/null 2>&1 &
VIDEO_PID=$!
cd $WORKSPACE_DIR

# Pequeña pausa para que arranque el video
sleep 1

# Mostrar progreso
echo ""
echo "⏱️  Grabando durante ${DURATION} segundos..."
for ((i=1; i<=DURATION; i++)); do
    if [ $((i % 10)) -eq 0 ]; then
        echo "   ${i}/${DURATION} segundos..."
    fi
    sleep 1
done

echo ""
echo "🛑 Deteniendo grabación..."

# Detener rosbag (Ctrl+C)
kill -SIGINT $BAG_PID 2>/dev/null
sleep 3

# Detener video
kill -SIGINT $VIDEO_PID 2>/dev/null
sleep 2

# Si aún siguen corriendo, forzar
kill -9 $BAG_PID 2>/dev/null || true
kill -9 $VIDEO_PID 2>/dev/null || true

sleep 2

echo ""
echo "=================================="
echo "  GRABACIÓN COMPLETADA"
echo "=================================="

# Mostrar información del bag
if [ -d "$BAG_DIR/$BAG_NAME" ]; then
    echo "📦 Rosbag guardado en: $BAG_DIR/$BAG_NAME"
    echo ""
    echo "Información del bag:"
    ros2 bag info $BAG_DIR/$BAG_NAME
    echo ""
    echo "Tamaño del rosbag:"
    du -h $BAG_DIR/$BAG_NAME
else
    echo "❌ Error: No se encontró el archivo de rosbag"
fi

echo ""

# Verificar y renombrar video (image_view genera output.avi por defecto)
if [ -f "$BAG_DIR/$BAG_NAME/output.avi" ]; then
    mv $BAG_DIR/$BAG_NAME/output.avi $BAG_DIR/$BAG_NAME/$VIDEO_NAME
    echo "🎥 Video guardado en: $BAG_DIR/$BAG_NAME/$VIDEO_NAME"
    echo "Tamaño del video:"
    du -h $BAG_DIR/$BAG_NAME/$VIDEO_NAME
    echo ""
    echo "Para reproducir el video:"
    echo "  vlc $BAG_DIR/$BAG_NAME/$VIDEO_NAME"
    echo "  # o"
    echo "  mpv $BAG_DIR/$BAG_NAME/$VIDEO_NAME"
else
    echo "⚠️  No se generó el video correctamente"
    echo "   Verificá que image_view esté instalado: sudo apt install ros-humble-image-view"
fi

echo ""
echo "📁 Todos los archivos guardados en: $BAG_DIR/$BAG_NAME/"
echo "   - Rosbag: *.db3 y metadata.yaml"
echo "   - Video: $VIDEO_NAME"
echo ""
echo "✅ Grabación completa finalizada"


# ============================================
# INSTRUCCIONES DE USO
# ============================================
# 
# 1. Hacer ejecutable:
#    chmod +x rosbags/record_marine_simulation.sh
#
# 2. Lanzar simulación primero (3 terminales):
#    Terminal 1: ros2 launch go2_config gazebo.launch.py rviz:=true
#    Terminal 2: ros2 run go2_tools marine_platform_simulator
#    Terminal 3: ros2 launch drone drone.launch.py
#
# 3. Grabar (en una 4ta terminal):
#    cd ~/gazebo-no-seas-malo/rosbags
#    ./record_marine_simulation.sh 60    # 60 segundos
#    ./record_marine_simulation.sh 120   # 2 minutos
#    ./record_marine_simulation.sh 300   # 5 minutos
#