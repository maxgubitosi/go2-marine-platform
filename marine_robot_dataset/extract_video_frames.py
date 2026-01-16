#!/usr/bin/env python3
"""
Script para extraer frames de video sincronizados con el dataset.
Debe ejecutarse DESPUÉS de extract_dataset.py
"""

import cv2
import pandas as pd
import numpy as np
from pathlib import Path
import sys


def extract_frames_from_video(video_path, dataset_csv, output_frames_dir):
    """
    Extrae frames del video y los sincroniza con el dataset.
    """
    # Leer dataset para obtener timestamps
    df = pd.read_csv(dataset_csv)
    
    # Abrir video
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"❌ Error: No se pudo abrir el video {video_path}")
        return False
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # Contar frames manualmente (CAP_PROP_FRAME_COUNT no funciona con Motion JPEG)
    print("📹 Contando frames del video...")
    total_frames_video = 0
    while True:
        ret, _ = cap.read()
        if not ret:
            break
        total_frames_video += 1
    cap.release()
    
    # Reabrir el video para extracción
    cap = cv2.VideoCapture(str(video_path))
    duration_video = total_frames_video / fps if fps > 0 else 0
    
    print(f"📹 Video info:")
    print(f"  - FPS: {fps}")
    print(f"  - Total frames: {total_frames_video}")
    print(f"  - Duración: {duration_video:.2f}s")
    
    # Tiempo inicial del dataset
    t_start_dataset = df['timestamp'].min()
    t_end_dataset = df['timestamp'].max()
    
    print(f"\n📊 Dataset info:")
    print(f"  - Total samples: {len(df)}")
    print(f"  - Duración: {t_end_dataset - t_start_dataset:.2f}s")
    
    # Extraer frames
    print(f"\n🎬 Extrayendo frames...")
    frames_saved = 0
    
    for idx, row in df.iterrows():
        timestamp_relative = row['timestamp'] - t_start_dataset
        frame_idx = int(timestamp_relative * fps)
        
        if frame_idx >= total_frames_video:
            print(f"⚠️  Frame {frame_idx} fuera de rango del video")
            continue
        
        # Posicionar en el frame correcto
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        
        if not ret:
            print(f"⚠️  No se pudo leer frame {frame_idx}")
            continue
        
        # Guardar frame
        frame_filename = row['frame_path']
        frame_path = output_frames_dir / frame_filename
        cv2.imwrite(str(frame_path), frame)
        frames_saved += 1
        
        if (idx + 1) % 50 == 0:
            print(f"  Procesados {idx + 1}/{len(df)} frames...")
    
    cap.release()
    print(f"\n✅ Guardados {frames_saved} frames en {output_frames_dir}")
    return True


def main():
    if len(sys.argv) < 3:
        print("Uso: python3 extract_video_frames.py <video.avi> <dataset.csv>")
        print("Ejemplo: python3 extract_video_frames.py video.avi datasets/marine_sim_20260116_172734/dataset.csv")
        sys.exit(1)
    
    video_path = Path(sys.argv[1])
    dataset_csv = Path(sys.argv[2])
    
    if not video_path.exists():
        print(f"❌ Error: Video no encontrado: {video_path}")
        sys.exit(1)
    
    if not dataset_csv.exists():
        print(f"❌ Error: Dataset no encontrado: {dataset_csv}")
        sys.exit(1)
    
    # Directorio de salida para frames
    output_frames_dir = dataset_csv.parent / "frames"
    output_frames_dir.mkdir(exist_ok=True)
    
    success = extract_frames_from_video(video_path, dataset_csv, output_frames_dir)
    
    if success:
        print(f"\n🎉 Frames extraídos exitosamente!")


if __name__ == "__main__":
    main()
