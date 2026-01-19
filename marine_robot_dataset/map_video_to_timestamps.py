#!/usr/bin/env python3
"""
Script para mapear frames de video a timestamps del rosbag.
Uso: python3 map_video_to_timestamps.py <ruta_al_directorio_rosbag>
"""

import sys
import cv2
import yaml
from pathlib import Path
from datetime import datetime, timedelta

def get_video_info(video_path):
    """Obtiene información del video"""
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Error: No se pudo abrir el video {video_path}")
        return None
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = 0
    
    # Contar frames manualmente
    while True:
        ret, _ = cap.read()
        if not ret:
            break
        frame_count += 1
    
    cap.release()
    
    return {
        'fps': fps,
        'frame_count': frame_count,
        'duration': frame_count / fps if fps > 0 else 0
    }

def parse_rosbag_metadata(metadata_path):
    """Lee el metadata.yaml del rosbag"""
    with open(metadata_path, 'r') as f:
        metadata = yaml.safe_load(f)
    
    # Extraer tiempos de inicio y fin
    starting_time = metadata['rosbag2_bagfile_information']['starting_time']
    duration_ns = metadata['rosbag2_bagfile_information']['duration']['nanoseconds']
    
    # Convertir nanosegundos a segundos
    start_sec = starting_time['nanoseconds_since_epoch'] / 1e9
    duration_sec = duration_ns / 1e9
    
    return {
        'start_time': start_sec,
        'duration': duration_sec,
        'end_time': start_sec + duration_sec
    }

def map_frames_to_timestamps(video_info, rosbag_info, video_start_delay=3.0):
    """
    Mapea frames de video a timestamps del rosbag.
    
    Args:
        video_info: Información del video (fps, frame_count, duration)
        rosbag_info: Información del rosbag (start_time, duration, end_time)
        video_start_delay: Segundos después de iniciar rosbag que inició el video (default 3)
    
    Returns:
        Lista de tuplas (frame_number, timestamp_ros)
    """
    
    # El video comienza video_start_delay segundos después del rosbag
    video_start_time = rosbag_info['start_time'] + video_start_delay
    
    frame_duration = 1.0 / video_info['fps']
    
    mappings = []
    for frame_num in range(video_info['frame_count']):
        # Timestamp ROS para este frame
        timestamp_ros = video_start_time + (frame_num * frame_duration)
        mappings.append((frame_num, timestamp_ros))
    
    return mappings

def format_timestamp(timestamp_sec):
    """Formatea timestamp a formato legible"""
    dt = datetime.fromtimestamp(timestamp_sec)
    return dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 map_video_to_timestamps.py <directorio_rosbag>")
        print("Ejemplo: python3 map_video_to_timestamps.py marine_sim_20260119_102639")
        sys.exit(1)
    
    rosbag_dir = Path(sys.argv[1])
    
    if not rosbag_dir.exists():
        print(f"Error: El directorio {rosbag_dir} no existe")
        sys.exit(1)
    
    video_path = rosbag_dir / "output.avi"
    metadata_path = rosbag_dir / "metadata.yaml"
    
    if not video_path.exists():
        print(f"Error: No se encontró {video_path}")
        sys.exit(1)
    
    if not metadata_path.exists():
        print(f"Error: No se encontró {metadata_path}")
        sys.exit(1)
    
    print("=" * 70)
    print("MAPEO DE FRAMES DE VIDEO A TIMESTAMPS DE ROSBAG")
    print("=" * 70)
    print()
    
    # Analizar video
    print("📹 Analizando video...")
    video_info = get_video_info(str(video_path))
    if not video_info:
        sys.exit(1)
    
    print(f"   Frames totales: {video_info['frame_count']}")
    print(f"   FPS: {video_info['fps']:.2f}")
    print(f"   Duración video: {video_info['duration']:.2f} segundos")
    print()
    
    # Analizar rosbag
    print("💾 Analizando rosbag metadata...")
    rosbag_info = parse_rosbag_metadata(metadata_path)
    
    print(f"   Inicio rosbag: {format_timestamp(rosbag_info['start_time'])}")
    print(f"   Duración rosbag: {rosbag_info['duration']:.2f} segundos")
    print(f"   Fin rosbag: {format_timestamp(rosbag_info['end_time'])}")
    print()
    
    # Mapear frames
    print("🔗 Mapeando frames a timestamps...")
    video_start_delay = 3.0  # El video empieza 3 seg después del rosbag
    mappings = map_frames_to_timestamps(video_info, rosbag_info, video_start_delay)
    
    print(f"   Video comienza: {format_timestamp(rosbag_info['start_time'] + video_start_delay)}")
    print(f"   Video termina: {format_timestamp(mappings[-1][1])}")
    print()
    
    # Mostrar algunos ejemplos
    print("📊 Ejemplos de mapeo (primeros 10 y últimos 10 frames):")
    print("=" * 70)
    print(f"{'Frame':<10} {'Timestamp ROS':<30} {'Tiempo relativo (s)':<20}")
    print("-" * 70)
    
    # Primeros 10
    for i in range(min(10, len(mappings))):
        frame_num, timestamp = mappings[i]
        rel_time = timestamp - rosbag_info['start_time']
        print(f"{frame_num:<10} {format_timestamp(timestamp):<30} {rel_time:.3f}")
    
    if len(mappings) > 20:
        print("...")
        print()
        # Últimos 10
        for i in range(max(10, len(mappings)-10), len(mappings)):
            frame_num, timestamp = mappings[i]
            rel_time = timestamp - rosbag_info['start_time']
            print(f"{frame_num:<10} {format_timestamp(timestamp):<30} {rel_time:.3f}")
    
    print("=" * 70)
    print()
    
    # Guardar mapeo completo a CSV
    csv_path = rosbag_dir / "frame_to_timestamp.csv"
    print(f"💾 Guardando mapeo completo a {csv_path.name}...")
    
    with open(csv_path, 'w') as f:
        f.write("frame_number,timestamp_ros_sec,timestamp_ros_nsec,timestamp_formatted,relative_time_sec\n")
        for frame_num, timestamp in mappings:
            timestamp_sec = int(timestamp)
            timestamp_nsec = int((timestamp - timestamp_sec) * 1e9)
            rel_time = timestamp - rosbag_info['start_time']
            formatted = format_timestamp(timestamp)
            f.write(f"{frame_num},{timestamp_sec},{timestamp_nsec},{formatted},{rel_time:.6f}\n")
    
    print(f"✅ Mapeo guardado exitosamente")
    print()
    print("Uso del mapeo:")
    print("  - Para obtener timestamp de un frame: busca el frame en el CSV")
    print("  - Para sincronizar con datos del rosbag: usa los timestamps ROS")
    print("  - timestamp_ros_sec.timestamp_ros_nsec es compatible con ROS time")

if __name__ == "__main__":
    main()
