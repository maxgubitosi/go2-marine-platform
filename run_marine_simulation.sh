#!/bin/bash

# Script para ejecutar el simulador de plataforma marina con Gazebo y RViz
# Marine Platform Simulator for Unitree Go2

echo "============================================"
echo "Marine Platform Simulator - Unitree Go2"
echo "============================================"

# Ir al directorio del workspace
cd ~/gazebo-no-seas-malo

# Limpiar directorios build, install y log
echo "Limpiando directorios build, install y log..."
rm -rf build install log
echo "Limpieza completada."
echo ""

# Compilar el workspace
echo "Compilando workspace..."
colcon build --symlink-install
if [ $? -ne 0 ]; then
    echo "ERROR: Falló la compilación"
    exit 1
fi

# Source del workspace
echo "Cargando entorno ROS2..."
source install/setup.bash

# Verificar que el paquete existe
if ! ros2 pkg list | grep -q "go2_tools"; then
    echo "ERROR: Paquete go2_tools no encontrado"
    exit 1
fi

echo ""
echo "============================================"
echo "Lanzando componentes del simulador..."
echo "============================================"
echo ""

# Función para matar procesos al salir
cleanup() {
    echo ""
    echo "Deteniendo todos los procesos..."
    kill 0
    exit 0
}

trap cleanup SIGINT SIGTERM

# 1. Lanzar Gazebo y RViz con go2_config en una nueva terminal
echo "[1/2] Iniciando Gazebo y RViz con Go2 en nueva terminal..."
gnome-terminal -- bash -c "cd ~/gazebo-no-seas-malo && source install/setup.bash && ros2 launch go2_config gazebo.launch.py rviz:=true; exec bash" &
GAZEBO_PID=$!

# Esperar a que Gazebo y RViz se inicien completamente
echo "Esperando a que Gazebo y RViz se inicien (20 segundos)..."
sleep 20

# 2. Lanzar el simulador de plataforma marina en otra terminal
echo "[2/2] Iniciando simulador de plataforma marina en nueva terminal..."
echo ""
echo "Modo: Automático (ondas sinusoidales)"
echo ""
echo "Topics disponibles:"
echo "  - /body_pose (publicador de pose del robot)"
echo "  - /marine_platform/manual_cmd (para control manual)"
echo "  - /marine_platform/debug_state (estado debug)"
echo ""
echo "============================================"
echo "Sistema iniciado. Cierra las ventanas para detener"
echo "============================================"
echo ""

gnome-terminal -- bash -c "cd ~/gazebo-no-seas-malo && source install/setup.bash && ros2 run go2_tools marine_platform_simulator; exec bash" &

# Esperar a que el usuario presione Ctrl+C
wait

# Si el script termina, hacer cleanup
cleanup
