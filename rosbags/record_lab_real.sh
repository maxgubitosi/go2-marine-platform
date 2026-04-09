#!/bin/bash
# ============================================================================
# Record real lab experiments.
#
# Default workflow:
#   1. Validate robot-only telemetry first.
#   2. Once robot topics are confirmed, add camera + ArUco with --full-topics.
#
# Usage:
#   ./record_lab_real.sh                    # 60s, robot-only mode (default)
#   ./record_lab_real.sh 15 smoke          # 15s, robot-only, suffix=smoke
#   ./record_lab_real.sh --full-topics     # Robot + camera + ArUco
#
# Modes:
#   --robot-topics    Record robot telemetry only (default)
#   --full-topics     Record robot + camera + ArUco topics
#   --extended-topics Alias for --full-topics
#   --all-topics      Record every detected topic with local type support
#
# Extras:
#   --list-only       Show selected topics and exit
#   --duration N      Duration in seconds
#   --suffix NAME     Bag suffix
#   --skip-preflight  Skip live-data checks before recording
#   --rmw-cyclone     Force rosbag recorder to use CycloneDDS
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"
BAG_DIR="$WORKSPACE_DIR/rosbags"
VALIDATOR="$SCRIPT_DIR/validate_lab_bag.py"
WAIT_FOR_TOPIC="$SCRIPT_DIR/wait_for_topic.py"

DURATION=60
SUFFIX=""
RECORD_MODE="robot"
LIST_ONLY=false
SKIP_PREFLIGHT=false
FORCE_RMW_CYCLONE=false
AUTO_RMW_CYCLONE=false
POSITIONAL_DURATION_SET=false
POSITIONAL_SUFFIX_SET=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --robot-topics)
            RECORD_MODE="robot"
            shift
            ;;
        --full-topics|--extended-topics)
            RECORD_MODE="full"
            shift
            ;;
        --all-topics)
            RECORD_MODE="all"
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
            if [[ "$1" =~ ^[0-9]+$ && "$POSITIONAL_DURATION_SET" == false ]]; then
                DURATION="$1"
                POSITIONAL_DURATION_SET=true
                shift
            elif [[ "$1" != --* && "$POSITIONAL_SUFFIX_SET" == false ]]; then
                SUFFIX="$1"
                POSITIONAL_SUFFIX_SET=true
                shift
            else
                echo "Opcion desconocida: $1"
                exit 1
            fi
            ;;
    esac
done

if [[ "$RECORD_MODE" == "full" && "$FORCE_RMW_CYCLONE" == false ]]; then
    AUTO_RMW_CYCLONE=true
fi

mkdir -p "$BAG_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
if [[ -n "$SUFFIX" ]]; then
    BAG_NAME="lab_real_${TIMESTAMP}_${SUFFIX}"
else
    BAG_NAME="lab_real_${TIMESTAMP}"
fi

ROBOT_STATE_GROUP="/sportmodestate /lowstate /utlidar/robot_odom /lf/sportmodestate /lf/lowstate /mf/sportmodestate /rt/sportmodestate /rt/lowstate /go2/sportmodestate /go2/lowstate"
ROBOT_REQUIRED_GROUPS=(
    "/marine_platform/debug_state"
    "/api/sport/request"
    "$ROBOT_STATE_GROUP"
)
FULL_REQUIRED_GROUPS=(
    "/marine_platform/debug_state"
    "/api/sport/request"
    "$ROBOT_STATE_GROUP"
    "/stereo_camera/image_raw"
    "/stereo_camera/camera_info"
    "/aruco/detection /aruco/debug_image"
)

FULL_OPTIONAL_GROUPS=(
    "/aruco/pose"
    "/tf /tf_static"
)

mapfile -t AVAILABLE_TOPICS < <(ros2 topic list 2>/dev/null | sed '/^$/d' | sort -u)
mapfile -t AVAILABLE_TOPICS_TYPES < <(ros2 topic list -t 2>/dev/null | sed '/^$/d' | sort -u)

if [[ ${#AVAILABLE_TOPICS[@]} -eq 0 ]]; then
    echo "ERROR: No se pudieron obtener topics con 'ros2 topic list'."
    echo "Asegurate de tener el entorno ROS2 sourceado y nodos corriendo."
    exit 1
fi

declare -A SELECTED_SET=()
declare -A FILTERED_SET=()
declare -A TOPIC_TYPE_MAP=()
declare -A TYPE_SUPPORT_CACHE=()
SELECTED_TOPICS=()
FILTERED_TOPICS=()
SKIPPED_TOPICS=()

for line in "${AVAILABLE_TOPICS_TYPES[@]}"; do
    topic="${line%% *}"
    type="${line#*[}"
    type="${type%]}"
    if [[ -n "$topic" && -n "$type" ]]; then
        TOPIC_TYPE_MAP["$topic"]="$type"
    fi
done

topic_exists() {
    local target="$1"
    local topic
    for topic in "${AVAILABLE_TOPICS[@]}"; do
        if [[ "$topic" == "$target" ]]; then
            return 0
        fi
    done
    return 1
}

add_topic() {
    local topic="$1"
    if [[ -z ${SELECTED_SET[$topic]+x} ]]; then
        SELECTED_SET["$topic"]=1
        SELECTED_TOPICS+=("$topic")
    fi
}

add_topic_if_exists() {
    local topic="$1"
    if topic_exists "$topic"; then
        add_topic "$topic"
        return 0
    fi
    return 1
}

is_supported_topic() {
    local topic="$1"
    local topic_type="${TOPIC_TYPE_MAP[$topic]-}"

    if [[ -z "$topic_type" ]]; then
        return 1
    fi

    if [[ -n ${TYPE_SUPPORT_CACHE[$topic_type]+x} ]]; then
        [[ "${TYPE_SUPPORT_CACHE[$topic_type]}" == "ok" ]]
        return
    fi

    if ros2 interface show "$topic_type" >/dev/null 2>&1; then
        TYPE_SUPPORT_CACHE["$topic_type"]="ok"
        return 0
    fi

    TYPE_SUPPORT_CACHE["$topic_type"]="missing"
    return 1
}

first_filtered_topic_in_group() {
    local group="$1"
    local topic
    for topic in $group; do
        if [[ -n ${FILTERED_SET[$topic]+x} ]]; then
            echo "$topic"
            return 0
        fi
    done
    return 1
}

first_live_topic_in_group() {
    local group="$1"
    local topic topic_type
    for topic in $group; do
        if [[ -z ${FILTERED_SET[$topic]+x} ]]; then
            continue
        fi
        topic_type="${TOPIC_TYPE_MAP[$topic]-}"
        if [[ -z "$topic_type" ]]; then
            continue
        fi
        if python3 "$WAIT_FOR_TOPIC" "$topic" "$topic_type" --timeout 3 >/dev/null 2>&1; then
            echo "$topic"
            return 0
        fi
    done
    return 1
}

build_robot_topic_selection() {
    local line topic

    for line in "${AVAILABLE_TOPICS_TYPES[@]}"; do
        topic="${line%% *}"
        if [[ "$line" == *"[unitree_"* ]] || [[ "$line" == *"[unitree_api/"* ]]; then
            add_topic "$topic"
        fi
    done

    for topic in "${AVAILABLE_TOPICS[@]}"; do
        if [[ "$topic" =~ ^/rt/ ]] || [[ "$topic" =~ ^/go2/ ]] || [[ "$topic" =~ (^|/)(lowstate|sportmodestate)$ ]]; then
            add_topic "$topic"
        fi
    done

    local support_topics=(
        /marine_platform/debug_state
        /marine_platform/manual_cmd
        /api/sport/request
        /api/sport/response
        /cmd_vel
        /cmd_vel/smooth
        /body_pose
        /joint_states
        /joint_states/raw
        /imu/data
        /imu/raw
        /imu/mag
        /odom
        /odom/local
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

    for topic in "${support_topics[@]}"; do
        add_topic_if_exists "$topic" >/dev/null || true
    done
}

build_full_topic_selection() {
    build_robot_topic_selection

    local topic
    local visual_topics=(
        /stereo_camera/image_raw
        /stereo_camera/camera_info
        /aruco/pose
        /aruco/detection
        /aruco/debug_image
    )

    for topic in "${visual_topics[@]}"; do
        add_topic_if_exists "$topic" >/dev/null || true
    done

    for topic in "${AVAILABLE_TOPICS[@]}"; do
        if [[ "$topic" =~ ^/aruco/ ]] || [[ "$topic" =~ ^/stereo_camera/ ]]; then
            add_topic "$topic"
        fi
    done
}

validate_selected_required_groups() {
    local mode_label="$1"
    shift

    local ok=true
    local group resolved

    echo ""
    echo "Chequeo de grupos requeridos seleccionados (${mode_label})..."

    for group in "$@"; do
        if resolved=$(first_filtered_topic_in_group "$group"); then
            echo "  + grupo cubierto por: $resolved"
        else
            echo "  x falta grupo requerido: $group"
            ok=false
        fi
    done

    if ! $ok; then
        echo ""
        echo "ERROR: faltan topics requeridos o su type support local."
        exit 1
    fi
}

run_live_preflight() {
    local mode_label="$1"
    shift

    local ok=true
    local group live_topic

    echo ""
    echo "Preflight de mensajes en vivo (${mode_label})..."

    for group in "$@"; do
        if live_topic=$(first_live_topic_in_group "$group"); then
            echo "  + datos en: $live_topic"
        else
            echo "  x sin datos en grupo requerido: $group"
            ok=false
        fi
    done

    if ! $ok; then
        echo ""
        echo "ERROR: el preflight fallo. No arranco la grabacion para evitar un bag incompleto."
        echo "Tip: verifica manualmente con 'ros2 topic hz' o 'ros2 topic echo --once'."
        echo "Si queres forzar igual: --skip-preflight"
        exit 1
    fi
}

echo "======================================"
echo "  GRABANDO EXPERIMENTO LAB REAL"
echo "======================================"
echo "Rosbag:   $BAG_NAME"
echo "Duracion: $DURATION s"
echo "Modo:     $RECORD_MODE"
echo "======================================"
echo ""
echo "Topics publicados actualmente: ${#AVAILABLE_TOPICS[@]}"

case "$RECORD_MODE" in
    all)
        for topic in "${AVAILABLE_TOPICS[@]}"; do
            add_topic "$topic"
        done
        ;;
    robot)
        build_robot_topic_selection
        ;;
    full)
        build_full_topic_selection
        ;;
    *)
        echo "ERROR: modo invalido '$RECORD_MODE'"
        exit 1
        ;;
esac

for topic in "${SELECTED_TOPICS[@]}"; do
    if is_supported_topic "$topic"; then
        FILTERED_SET["$topic"]=1
        FILTERED_TOPICS+=("$topic")
    else
        SKIPPED_TOPICS+=("$topic [${TOPIC_TYPE_MAP[$topic]-sin_tipo}]")
    fi
done

SELECTED_TOPICS=("${FILTERED_TOPICS[@]}")

if [[ ${#SKIPPED_TOPICS[@]} -gt 0 ]]; then
    echo ""
    echo "Topics omitidos por falta de type support local (${#SKIPPED_TOPICS[@]}):"
    for topic in "${SKIPPED_TOPICS[@]}"; do
        echo "  - $topic"
    done
fi

if [[ ${#SELECTED_TOPICS[@]} -eq 0 ]]; then
    echo "ERROR: no hay topics seleccionados para grabar."
    exit 1
fi

echo ""
echo "Topics seleccionados para grabar: ${#SELECTED_TOPICS[@]}"
for topic in "${SELECTED_TOPICS[@]}"; do
    echo "  - $topic"
done

case "$RECORD_MODE" in
    robot)
        validate_selected_required_groups "$RECORD_MODE" "${ROBOT_REQUIRED_GROUPS[@]}"
        ;;
    full)
        validate_selected_required_groups "$RECORD_MODE" "${FULL_REQUIRED_GROUPS[@]}"
        ;;
esac

if [[ "$SKIP_PREFLIGHT" == false && "$LIST_ONLY" == false ]]; then
    case "$RECORD_MODE" in
        robot)
            run_live_preflight "$RECORD_MODE" "${ROBOT_REQUIRED_GROUPS[@]}"
            ;;
        full)
            run_live_preflight "$RECORD_MODE" "${FULL_REQUIRED_GROUPS[@]}"
            for group in "${FULL_OPTIONAL_GROUPS[@]}"; do
                if live_topic=$(first_live_topic_in_group "$group"); then
                    echo "  + opcional disponible: $live_topic"
                else
                    echo "  ! opcional sin datos: $group"
                fi
            done
            ;;
    esac
fi

if [[ "$LIST_ONLY" == true ]]; then
    echo ""
    echo "Modo --list-only: no se inicia grabacion."
    exit 0
fi

if [[ ! -f "$VALIDATOR" ]]; then
    echo "ERROR: no se encontro el validador en $VALIDATOR"
    exit 1
fi

if [[ ! -f "$WAIT_FOR_TOPIC" ]]; then
    echo "ERROR: no se encontro el helper de preflight en $WAIT_FOR_TOPIC"
    exit 1
fi

BAG_LOG="$BAG_DIR/${BAG_NAME}_record.log"
BAG_PID=""
EARLY_STOP=false

stop_recording() {
    if [[ -n "$BAG_PID" ]] && kill -0 "$BAG_PID" 2>/dev/null; then
        echo ""
        echo "Deteniendo grabacion..."
        kill -SIGINT "$BAG_PID" 2>/dev/null || true
        wait "$BAG_PID" 2>/dev/null || true
    fi
    BAG_PID=""
}

on_sigint() {
    EARLY_STOP=true
    stop_recording
}
trap on_sigint SIGINT

echo ""
echo "Iniciando grabacion..."
if [[ "$FORCE_RMW_CYCLONE" == true || "$AUTO_RMW_CYCLONE" == true ]]; then
    if [[ "$AUTO_RMW_CYCLONE" == true ]]; then
        echo "RMW para recorder: rmw_cyclonedds_cpp (auto en modo full)"
    else
        echo "RMW para recorder: rmw_cyclonedds_cpp"
    fi
    RMW_IMPLEMENTATION=rmw_cyclonedds_cpp ros2 bag record "${SELECTED_TOPICS[@]}" -o "$BAG_DIR/$BAG_NAME" > "$BAG_LOG" 2>&1 &
else
    ros2 bag record "${SELECTED_TOPICS[@]}" -o "$BAG_DIR/$BAG_NAME" > "$BAG_LOG" 2>&1 &
fi
BAG_PID=$!

echo "Grabando durante ${DURATION} segundos... (Ctrl+C para detener antes)"
sleep "$DURATION" &
SLEEP_PID=$!
wait "$SLEEP_PID" 2>/dev/null || true

if [[ "$EARLY_STOP" == false ]]; then
    stop_recording
else
    echo "Grabacion detenida por usuario antes del timeout."
fi

echo ""
echo "======================================"
echo "  GRABACION COMPLETADA"
echo "======================================"
echo "Rosbag:     $BAG_DIR/$BAG_NAME"
echo "Log record: $BAG_LOG"

echo ""
echo "Resumen ros2 bag info:"
ros2 bag info "$BAG_DIR/$BAG_NAME"

if [[ "$RECORD_MODE" != "all" ]]; then
    echo ""
    echo "Validando bag contra requisitos minimos..."
    python3 "$VALIDATOR" --mode "$RECORD_MODE" "$BAG_DIR/$BAG_NAME"
fi

echo ""
echo "Para exportar video + CSV:"
echo "  python3 stereo_camera/scripts/06_export_from_bag.py $BAG_DIR/$BAG_NAME"
