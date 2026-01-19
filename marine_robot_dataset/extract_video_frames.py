#!/usr/bin/env python3
"""
Script para extraer frames de video sincronizados con el dataset.
Debe ejecutarse DESPUÉS de extract_dataset.py
NOTA: Ahora usa el mapeo correcto de frame_path del dataset que ya tiene
la sincronización correcta con los frames reales del video.
"""

import cv2
import pandas as pd
import numpy as np
from pathlib import Path
import sys


def extract_frames_from_video(video_path, dataset_csv, output_frames_dir):
    """
    Extrae frames del video según el mapeo del dataset.
    El dataset ya tiene la sincronización correcta entre frames y timestamps.
    """
    # Leer dataset
    df = pd.read_csv(dataset_csv)
    
    # Abrir video
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"❌ Error: No se pudo abrir el video {video_path}")
        return False
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # Contar frames manualmente (CAP_PROP_FRAME_COUNT no funciona con Motion JPEG)
    print("📹 Analizando video...")
    all_frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        all_frames.append(frame)
    cap.release()
    
    total_frames_video = len(all_frames)
    duration_video = total_frames_video / fps if fps > 0 else 0
    
    print(f"📹 Video info:")
    print(f"  - FPS: {fps:.2f}")
    print(f"  - Total frames: {total_frames_video}")
    print(f"  - Duración: {duration_video:.2f}s")
    
    print(f"\n📊 Dataset info:")
    print(f"  - Total samples: {len(df)}")
    print(f"  - Rango timestamps: {df['timestamp'].min():.2f}s - {df['timestamp'].max():.2f}s")
    
    # Extraer números de frame del dataset (frame_XXXXXX.png -> XXXXXX)
    print(f"\n🎬 Extrayendo frames según mapeo del dataset...")
    frames_saved = 0
    frames_skipped = 0
    
    for idx, row in df.iterrows():
        frame_filename = row['frame_path']
        # Extraer número de frame: frame_000042.png -> 42
        try:
            frame_num = int(frame_filename.split('_')[1].split('.')[0])
        except:
            print(f"⚠️  No se pudo parsear número de frame de: {frame_filename}")
            frames_skipped += 1
            continue
        
        # Verificar que el frame existe en el video
        if frame_num >= total_frames_video:
            print(f"⚠️  Frame {frame_num} fuera de rango (video tiene {total_frames_video} frames)")
            frames_skipped += 1
            continue
        
        # Obtener frame directamente del array
        frame = all_frames[frame_num]
        
        # Guardar frame
        frame_path = output_frames_dir / frame_filename
        cv2.imwrite(str(frame_path), frame)
        frames_saved += 1
        
        if (idx + 1) % 50 == 0:
            print(f"  Procesados {idx + 1}/{len(df)} frames...")
    
    print(f"\n✅ Guardados {frames_saved} frames en {output_frames_dir}")
    if frames_skipped > 0:
        print(f"⚠️  {frames_skipped} frames omitidos (fuera de rango o error)")
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
