#!/bin/bash

# Script para lanzar toda la simulación marina con dron automáticamente
# Requiere: tmux o gnome-terminal

WORKSPACE_DIR=~/gazebo-no-seas-malo

echo "=================================="
echo "  LANZANDO SIMULACIÓN COMPLETA"
echo "=================================="
echo ""

# Verificar que estamos en el workspace
cd $WORKSPACE_DIR
source install/setup.bash

# Detectar terminal emulator disponible
if command -v gnome-terminal &> /dev/null; then
    TERMINAL="gnome-terminal"
elif command -v tmux &> /dev/null; then
    TERMINAL="tmux"
else
    echo "❌ ERROR: Necesitás instalar gnome-terminal o tmux"
    echo "   sudo apt install gnome-terminal"
    echo "   # o"
    echo "   sudo apt install tmux"
    exit 1
fi

echo "Usando: $TERMINAL"
echo ""

if [ "$TERMINAL" = "gnome-terminal" ]; then
    # Opción 1: Usando gnome-terminal (más visual)
    echo "Lanzando terminales..."
    
    # Terminal 1: Gazebo + RViz
    gnome-terminal --title="Gazebo + RViz" -- bash -c "
        cd $WORKSPACE_DIR && 
        source install/setup.bash && 
        echo '🚀 Lanzando Gazebo + RViz...' && 
        ros2 launch go2_config gazebo.launch.py rviz:=true; 
        exec bash"
    
    sleep 5
    
    # Terminal 2: Marine simulator
    gnome-terminal --title="Marine Simulator" -- bash -c "
        cd $WORKSPACE_DIR && 
        source install/setup.bash && 
        echo '🌊 Lanzando simulador marino...' && 
        sleep 3 &&
        ros2 run go2_tools marine_platform_simulator; 
        exec bash"
    
    sleep 3
    
    # Terminal 3: Drone
    gnome-terminal --title="Drone" -- bash -c "
        cd $WORKSPACE_DIR && 
        source install/setup.bash && 
        echo '🚁 Lanzando dron...' && 
        sleep 3 &&
        ros2 launch drone_landing drone_landing.launch.py; 
        exec bash"
    
    echo ""
    echo "✅ Simulación lanzada en 3 terminales separadas"
    echo ""
    echo "Para grabar, ejecutá en una nueva terminal:"
    echo "  cd ~/gazebo-no-seas-malo/rosbags"
    echo "  ./record_marine_simulation.sh 60"
    
elif [ "$TERMINAL" = "tmux" ]; then
    # Opción 2: Usando tmux (más ligero)
    SESSION_NAME="marine_sim"
    
    # Crear sesión de tmux
    tmux new-session -d -s $SESSION_NAME -n "gazebo"
    
    # Window 1: Gazebo + RViz
    tmux send-keys -t $SESSION_NAME:gazebo "cd $WORKSPACE_DIR" C-m
    tmux send-keys -t $SESSION_NAME:gazebo "source install/setup.bash" C-m
    tmux send-keys -t $SESSION_NAME:gazebo "ros2 launch go2_config gazebo.launch.py rviz:=true" C-m
    
    sleep 5
    
    # Window 2: Marine simulator
    tmux new-window -t $SESSION_NAME -n "marine"
    tmux send-keys -t $SESSION_NAME:marine "cd $WORKSPACE_DIR" C-m
    tmux send-keys -t $SESSION_NAME:marine "source install/setup.bash" C-m
    tmux send-keys -t $SESSION_NAME:marine "sleep 3 && ros2 run go2_tools marine_platform_simulator" C-m
    
    sleep 3
    
    # Window 3: Drone
    tmux new-window -t $SESSION_NAME -n "drone"
    tmux send-keys -t $SESSION_NAME:drone "cd $WORKSPACE_DIR" C-m
    tmux send-keys -t $SESSION_NAME:drone "source install/setup.bash" C-m
    tmux send-keys -t $SESSION_NAME:drone "sleep 3 && ros2 launch drone_landing drone_landing.launch.py" C-m
    
    # Window 4: Control (para grabar)
    tmux new-window -t $SESSION_NAME -n "control"
    tmux send-keys -t $SESSION_NAME:control "cd $WORKSPACE_DIR/rosbags" C-m
    tmux send-keys -t $SESSION_NAME:control "source $WORKSPACE_DIR/install/setup.bash" C-m
    tmux send-keys -t $SESSION_NAME:control "echo ''" C-m
    tmux send-keys -t $SESSION_NAME:control "echo '✅ Simulación lista. Para grabar ejecutá:'" C-m
    tmux send-keys -t $SESSION_NAME:control "echo '   ./record_marine_simulation.sh 60'" C-m
    tmux send-keys -t $SESSION_NAME:control "echo ''" C-m
    
    # Adjuntar a la sesión
    tmux attach-session -t $SESSION_NAME
    
    echo ""
    echo "ℹ️  Controles de tmux:"
    echo "  Ctrl+b d     - Despegar de tmux"
    echo "  Ctrl+b n     - Siguiente ventana"
    echo "  Ctrl+b p     - Ventana anterior"
    echo "  Ctrl+b 0-3   - Ir a ventana específica"
    echo "  tmux attach  - Volver a adjuntar"
    echo "  tmux kill-session -t marine_sim  - Cerrar todo"
fi


# ============================================
# INSTRUCCIONES DE USO
# ============================================
# 
# 1. Hacer ejecutable:
#    chmod +x run_full_simulation.sh
#
# 2. Lanzar todo de una vez:
#    ./run_full_simulation.sh
#
# 3. Esperar ~10-15 segundos a que todo arranque
#
# 4. En la ventana "control" (tmux) o nueva terminal:
#    cd ~/gazebo-no-seas-malo/rosbags
#    ./record_marine_simulation.sh 60
#
