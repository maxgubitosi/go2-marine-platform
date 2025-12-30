#!/bin/bash

# Script para reproducir rosbag con visualización completa del robot

if [ -z "$1" ]; then
    echo "Uso: ./play_bag_with_rviz.sh <nombre_del_bag>"
    echo "Ejemplo: ./play_bag_with_rviz.sh rosbags/marine_simulation_20251222_113219"
    exit 1
fi

BAG_PATH=$1

if [ ! -d "$BAG_PATH" ]; then
    echo "ERROR: Bag no encontrado: $BAG_PATH"
    exit 1
fi

echo "============================================"
echo "  Reproduciendo Rosbag con RViz"
echo "============================================"
echo "Bag: $BAG_PATH"
echo ""

cd ~/gazebo-no-seas-malo
source install/setup.bash

# Función cleanup
cleanup() {
    echo ""
    echo "Cerrando aplicaciones..."
    kill 0
    exit 0
}

trap cleanup SIGINT SIGTERM

# 1. Publicar robot_description (necesario para ver el robot)
echo "[1/3] Publicando robot_state_publisher..."
ros2 run robot_state_publisher robot_state_publisher \
  --ros-args \
  -p use_sim_time:=true \
  -p robot_description:="$(xacro src/unitree-go2-ros2/robots/descriptions/go2_description/xacro/robot.xacro)" &

sleep 2

# 2. Reproducir bag en una terminal separada
echo "[2/3] Reproduciendo bag en nueva terminal..."
gnome-terminal -- bash -c "cd ~/gazebo-no-seas-malo && source install/setup.bash && ros2 bag play $BAG_PATH --clock --loop --rate 1.0; exec bash" &

sleep 2

# 3. Lanzar RViz
echo "[3/3] Abriendo RViz..."
echo ""
echo "============================================"
echo "Configuración de RViz:"
echo "  1. Fixed Frame: 'odom'"
echo "  2. Add → RobotModel (verás el robot)"
echo "  3. Add → TF (verás los ejes)"
echo "  4. Add → Odometry (topic: /odom)"
echo "============================================"
echo ""
echo "Presiona Ctrl+C para cerrar todo"
echo ""

ros2 run rviz2 rviz2 --ros-args --param use_sim_time:=true

# Cuando RViz cierre, hacer cleanup
cleanup