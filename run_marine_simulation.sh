#!/bin/bash

# Script para lanzar simulación marina completa
# Inicia Gazebo, RViz y el simulador de plataforma marina

echo "Marine Platform Simulator - Unitree Go2"
echo "========================================"

cd ~/gazebo-no-seas-malo

# Compilar workspace
echo "Compilando workspace..."
colcon build --symlink-install
if [ $? -ne 0 ]; then
    echo "ERROR: Falló la compilación"
    exit 1
fi

source install/setup.bash

# Verificar que el paquete existe
if ! ros2 pkg list | grep -q "go2_tools"; then
    echo "ERROR: Paquete go2_tools no encontrado"
    exit 1
fi

# Función para cleanup
cleanup() {
    echo "Deteniendo procesos..."
    kill 0
    exit 0
}

trap cleanup SIGINT SIGTERM

# Lanzar Gazebo y RViz
echo "Iniciando Gazebo y RViz..."
gnome-terminal -- bash -c "cd ~/gazebo-no-seas-malo && source install/setup.bash && ros2 launch go2_config gazebo.launch.py rviz:=true; exec bash" &

sleep 20

# Lanzar simulador de plataforma marina
echo "Iniciando simulador de plataforma marina..."
gnome-terminal -- bash -c "cd ~/gazebo-no-seas-malo && source install/setup.bash && ros2 run go2_tools marine_platform_simulator; exec bash" &

echo "Sistema iniciado. Presiona Ctrl+C para detener."

wait
cleanup
