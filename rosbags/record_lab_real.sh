#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# Graba datos del experimento real en el lab.
#
# Perfil actual (diagnóstico extendido):
#   - Cámara + ArUco (imagen, camera_info, pose, detección, debug)
#   - Comandos marine
#   - Estado del robot (joints, IMU, odom, contactos)
#   - Comandos locomoción/body
#   - TF + eventos ROS
#   - Topics de posibles bridges SDK2 (/rt/*, /go2/*)
#
# Uso:
#   ./record_lab_real.sh                          # 60s, modo robot (default)
#   ./record_lab_real.sh 120                      # 120s, modo robot
#   ./record_lab_real.sh 120 trote               # 120s + sufijo
#
# Modos:
#   --robot-topics    Graba tópicos del robot (unitree/rt/go2 + estado útil)
#   --all-topics      Graba todos los tópicos detectados y soportados localmente
#   --extended-topics Perfil extendido actual (cámara + aruco + robot + tf)
#
# Extras:
#   --list-only       Solo muestra qué se grabaría y no arranca rosbag
#   --duration N      Duración en segundos
#   --suffix NAME     Sufijo del nombre del bag
#   --rmw-cyclone     Fuerza rosbag con RMW CycloneDDS (útil si FastDDS pierde payloads)
# ═══════════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"
BAG_DIR="$WORKSPACE_DIR/rosbags"
DURATION=60
SUFFIX=""
RECORD_MODE="robot"
LIST_ONLY=false
SKIP_PREFLIGHT=false
FORCE_RMW_CYCLONE=false

# Compatibilidad con formato anterior: ./record_lab_real.sh 120 [suffix]
if [[ $# -gt 0 && "$1" =~ ^[0-9]+$ ]]; then
    DURATION="$1"
    shift
    if [[ $# -gt 0 && "$1" != --* ]]; then
        SUFFIX="$1"
        shift
    fi
fi

while [[ $# -gt 0 ]]; do
    case "$1" in
        --robot-topics)
            RECORD_MODE="robot"
            shift
            ;;
        --all-topics)
            RECORD_MODE="all"
            shift
            ;;
        --extended-topics)
            RECORD_MODE="extended"
            shift
            ;;
        --list-only)
            LIST_ONLY=true
            shift
            ;;
        --skip-preflight)
            SKIP_PREFLIGHT=true
            shift
            ;;
        --rmw-cyclone)
            FORCE_RMW_CYCLONE=true
            shift
            ;;
        --duration)
            DURATION="$2"
            shift 2
            ;;
        --suffix)
            SUFFIX="$2"
            shift 2
            ;;
        *)
            echo "Opción desconocida: $1"
            exit 1
            ;;
    esac
done

mkdir -p "$BAG_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
if [ -n "$SUFFIX" ]; then
    BAG_NAME="lab_real_${TIMESTAMP}_${SUFFIX}"
else
    BAG_NAME="lab_real_${TIMESTAMP}"
fi

echo "══════════════════════════════════════"
echo "  GRABANDO EXPERIMENTO LAB REAL"
echo "══════════════════════════════════════"
echo "Rosbag: $BAG_NAME"
echo "Duración: $DURATION segundos"
echo "══════════════════════════════════════"

# Verificar topics y construir lista según modo
echo ""
echo "Verificando topics (modo: $RECORD_MODE)..."

MANDATORY_TOPICS=(
    /stereo_camera/image_raw
    /stereo_camera/camera_info
    /aruco/pose
    /aruco/detection
    /aruco/debug_image
    /marine_platform/debug_state
)

# Candidatos explícitos de alto valor para diagnosticar "trote".
CANDIDATE_TOPICS=(
    /marine_platform/manual_cmd
    /body_pose
    /cmd_vel
    /cmd_vel/smooth
    /joint_states
    /joint_states/raw
    /imu/data
    /imu/mag
    /imu/raw
    /foot_contacts
    /foot_contacts/raw
    /odom
    /odom/local
    /tf
    /tf_static
    /joint_group_effort_controller/joint_trajectory
    /joint_group_position_controller/command
    /clock
    /parameter_events
    /rosout
    /rt/lowstate
    /rt/sportmodestate
    /lowstate
    /sportmodestate
    /go2/lowstate
    /go2/sportmodestate
)

# Patrones para auto-detectar namespaces reales en runtime (modo extended).
AUTO_PATTERNS=(
    '^/marine_platform/.+'
    '^/aruco/.+'
    '^/stereo_camera/.+'
    '^/imu/.+'
    '^/joint.+$'
    '^/foot_contacts.*$'
    '^/cmd_vel.*$'
    '^/body_pose$'
    '^/odom(/.*)?$'
    '^/tf$'
    '^/tf_static$'
    '^/rt/.+'
    '^/go2/.+'
    '^/parameter_events$'
    '^/rosout$'
    '^/clock$'
)

mapfile -t AVAILABLE_TOPICS < <(ros2 topic list 2>/dev/null | sed '/^$/d' | sort -u)
mapfile -t AVAILABLE_TOPICS_TYPES < <(ros2 topic list -t 2>/dev/null | sed '/^$/d' | sort -u)

if [ ${#AVAILABLE_TOPICS[@]} -eq 0 ]; then
    echo "ERROR: No se pudieron obtener topics con 'ros2 topic list'."
    echo "Asegurate de tener el entorno ROS2 sourceado y nodos corriendo."
    exit 1
fi

declare -A SELECTED_SET
SELECTED_TOPICS=()
declare -A TOPIC_TYPE_MAP
declare -A TYPE_SUPPORT_CACHE

for line in "${AVAILABLE_TOPICS_TYPES[@]}"; do
    topic="${line%% *}"
    type="${line#*[}"
    type="${type%]}"
    if [ -n "$topic" ] && [ -n "$type" ]; then
        TOPIC_TYPE_MAP["$topic"]="$type"
    fi
done

echo "Topics publicados actualmente: ${#AVAILABLE_TOPICS[@]}"

add_topic_if_exists() {
    local topic="$1"
    for t in "${AVAILABLE_TOPICS[@]}"; do
        if [ "$t" = "$topic" ]; then
            if [ -z "${SELECTED_SET[$t]}" ]; then
                SELECTED_SET[$t]=1
                SELECTED_TOPICS+=("$t")
            fi
            return 0
        fi
    done
    return 1
}

add_topic() {
    local topic="$1"
    if [ -z "${SELECTED_SET[$topic]}" ]; then
        SELECTED_SET[$topic]=1
        SELECTED_TOPICS+=("$topic")
    fi
}

is_supported_topic() {
    local topic="$1"
    local topic_type="${TOPIC_TYPE_MAP[$topic]}"

    if [ -z "$topic_type" ]; then
        return 1
    fi

    if [ -n "${TYPE_SUPPORT_CACHE[$topic_type]}" ]; then
        if [ "${TYPE_SUPPORT_CACHE[$topic_type]}" = "ok" ]; then
            return 0
        else
            return 1
        fi
    fi

    if ros2 interface show "$topic_type" >/dev/null 2>&1; then
        TYPE_SUPPORT_CACHE[$topic_type]="ok"
        return 0
    else
        TYPE_SUPPORT_CACHE[$topic_type]="missing"
        return 1
    fi
}

ALL_OK=true

if [ "$RECORD_MODE" = "all" ]; then
    for topic in "${AVAILABLE_TOPICS[@]}"; do
        add_topic "$topic"
    done
elif [ "$RECORD_MODE" = "robot" ]; then
    # 1) Todo topic cuyo tipo sea unitree_*.
    for line in "${AVAILABLE_TOPICS_TYPES[@]}"; do
        topic="${line%% *}"
        if [[ "$line" == *"[unitree_"* ]]; then
            add_topic "$topic"
        fi
    done

    # 2) Fallback por namespaces/nombres típicos del Go2.
    for topic in "${AVAILABLE_TOPICS[@]}"; do
        if [[ "$topic" =~ ^/rt/ ]] || [[ "$topic" =~ ^/go2/ ]] || [[ "$topic" =~ (^|/)lowstate$ ]] || [[ "$topic" =~ (^|/)sportmodestate$ ]]; then
            add_topic "$topic"
        fi
    done

    # 3) Señales de soporte para correlación temporal.
    SUPPORT_TOPICS=(
        /marine_platform/debug_state
        /marine_platform/manual_cmd
        /cmd_vel
        /cmd_vel/smooth
        /body_pose
        /joint_states
        /imu/data
        /odom
        /utlidar/robot_odom
        /utlidar/imu
        /utlidar/lidar_state
        /uslam/frontend/odom
        /uslam/localization/odom
        /lio_sam_ros2/mapping/odometry
        /tf
        /tf_static
        /parameter_events
        /rosout
        /clock
    )
    for topic in "${SUPPORT_TOPICS[@]}"; do
        add_topic_if_exists "$topic" >/dev/null || true
    done

    # Chequeo explícito de señales clave.
    for topic in /lowstate /sportmodestate /rt/lowstate /rt/sportmodestate; do
        if add_topic_if_exists "$topic" >/dev/null; then
            echo "  ✓ clave robot: $topic"
        fi
    done
else
    # Modo extended (comportamiento previo).
    for topic in "${MANDATORY_TOPICS[@]}"; do
        if add_topic_if_exists "$topic"; then
            echo "  ✓ $topic"
        else
            echo "  ✗ $topic (no encontrado)"
            ALL_OK=false
        fi
    done

    for topic in "${CANDIDATE_TOPICS[@]}"; do
        add_topic_if_exists "$topic" >/dev/null || true
    done

    for topic in "${AVAILABLE_TOPICS[@]}"; do
        for pattern in "${AUTO_PATTERNS[@]}"; do
            if [[ "$topic" =~ $pattern ]]; then
                add_topic "$topic"
                break
            fi
        done
    done
fi

echo ""
echo "Topics seleccionados para grabar: ${#SELECTED_TOPICS[@]}"
for topic in "${SELECTED_TOPICS[@]}"; do
    echo "  - $topic"
done

if [ "$ALL_OK" = false ]; then
    echo ""
    echo "ADVERTENCIA: Algunos topics no están disponibles."
    echo "Asegurate de tener corriendo:"
    echo "  ros2 launch fixed_camera lab_real.launch.py"
    echo ""
    read -p "¿Grabar de todos modos con los topics disponibles? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelado."
        exit 1
    fi
fi

# Filtrar tópicos que no tienen type support local (evita que rosbag se detenga).
FILTERED_TOPICS=()
SKIPPED_TOPICS=()
for topic in "${SELECTED_TOPICS[@]}"; do
    if is_supported_topic "$topic"; then
        FILTERED_TOPICS+=("$topic")
    else
        SKIPPED_TOPICS+=("$topic [${TOPIC_TYPE_MAP[$topic]}]")
    fi
done
SELECTED_TOPICS=("${FILTERED_TOPICS[@]}")

if [ ${#SKIPPED_TOPICS[@]} -gt 0 ]; then
    echo ""
    echo "Se omiten topics sin type support local (${#SKIPPED_TOPICS[@]}):"
    for s in "${SKIPPED_TOPICS[@]}"; do
        echo "  - $s"
    done
fi

if [ ${#SELECTED_TOPICS[@]} -eq 0 ]; then
    echo "ERROR: No hay topics seleccionados para grabar."
    exit 1
fi

# Preflight: validar que tópicos críticos estén realmente entregando mensajes.
if [ "$RECORD_MODE" = "robot" ] && [ "$SKIP_PREFLIGHT" = false ] && [ "$LIST_ONLY" = false ]; then
    echo ""
    echo "Preflight de mensajes en vivo (robot)..."

    check_group_once() {
        local group="$1"
        GROUP_OK=false
        for topic in $group; do
            if [ -z "${SELECTED_SET[$topic]}" ]; then
                continue
            fi
            if timeout 3s ros2 topic echo "$topic" --once >/dev/null 2>&1; then
                echo "  ✓ datos en: $topic"
                GROUP_OK=true
                break
            fi
        done

        if [ "$GROUP_OK" = true ]; then
            return 0
        else
            return 1
        fi
    }

    PREFLIGHT_OK=true

    # Requisitos duros para empezar a grabar.
    REQUIRED_GROUPS=(
        "/marine_platform/debug_state"
        "/lowstate /lf/lowstate"
    )

    for group in "${REQUIRED_GROUPS[@]}"; do
        if check_group_once "$group"; then
            :
        else
            echo "  ✗ sin datos en grupo requerido: $group"
            PREFLIGHT_OK=false
        fi
    done

    # Requisitos opcionales (solo warning): gait explícito y odometría global.
    OPTIONAL_GROUPS=(
        "/sportmodestate /lf/sportmodestate /mf/sportmodestate"
        "/utlidar/robot_odom /uslam/frontend/odom /uslam/localization/odom /lio_sam_ros2/mapping/odometry"
    )

    for group in "${OPTIONAL_GROUPS[@]}"; do
        if check_group_once "$group"; then
            :
        else
            echo "  ⚠ sin datos en grupo opcional: $group"
        fi
    done

    if [ "$PREFLIGHT_OK" = false ]; then
        echo ""
        echo "ERROR: Preflight falló. No arranco grabación para evitar bag incompleto."
        echo "Tip: verificá robot activo y probá manualmente:"
        echo "  ros2 topic hz /sportmodestate"
        echo "  ros2 topic hz /lowstate"
        echo "Si querés forzar de todos modos: --skip-preflight"
        exit 1
    fi
fi

if [ "$LIST_ONLY" = true ]; then
    echo ""
    echo "Modo --list-only: no se inicia grabación."
    exit 0
fi

echo ""
echo "Iniciando grabación..."
BAG_LOG="$BAG_DIR/${BAG_NAME}_record.log"
if [ "$FORCE_RMW_CYCLONE" = true ]; then
    echo "RMW para recorder: rmw_cyclonedds_cpp"
    RMW_IMPLEMENTATION=rmw_cyclonedds_cpp ros2 bag record "${SELECTED_TOPICS[@]}" -o "$BAG_DIR/$BAG_NAME" > "$BAG_LOG" 2>&1 &
else
    ros2 bag record "${SELECTED_TOPICS[@]}" -o "$BAG_DIR/$BAG_NAME" > "$BAG_LOG" 2>&1 &
fi
BAG_PID=$!

echo "Grabando durante ${DURATION} segundos... (Ctrl+C para detener antes)"

# Trap Ctrl+C to stop recording gracefully
trap "echo ''; echo 'Deteniendo grabación...'; kill -SIGINT $BAG_PID 2>/dev/null; wait $BAG_PID 2>/dev/null; exit 0" SIGINT

sleep "$DURATION"

echo ""
echo "Deteniendo grabación..."
kill -SIGINT $BAG_PID 2>/dev/null
wait $BAG_PID 2>/dev/null || true

echo ""
echo "══════════════════════════════════════"
echo "  GRABACIÓN COMPLETADA"
echo "══════════════════════════════════════"
echo "Rosbag: $BAG_DIR/$BAG_NAME"
echo "Log record: $BAG_LOG"
echo ""
echo "Para exportar video + CSV:"
echo "  python3 stereo_camera/scripts/06_export_from_bag.py $BAG_DIR/$BAG_NAME"
