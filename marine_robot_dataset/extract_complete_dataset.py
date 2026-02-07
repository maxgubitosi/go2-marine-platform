#!/usr/bin/env python3
"""
Script completo para extraer dataset y frames en un solo paso.
Ejecuta extract_dataset.py y luego extract_video_frames.py automáticamente.
"""

import sys
import subprocess
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 extract_complete_dataset.py <path_to_rosbag>")
        print("Ejemplo: python3 extract_complete_dataset.py ../rosbags/marine_sim_20260116_172734")
        sys.exit(1)
    
    rosbag_path = Path(sys.argv[1])
    rosbag_name = rosbag_path.name
    output_dir = Path("datasets") / rosbag_name
    dataset_csv = output_dir / "dataset.csv"
    video_path = rosbag_path / "output.avi"
    
    print("=" * 70)
    print("EXTRACCIÓN COMPLETA DE DATASET Y FRAMES")
    print("=" * 70)
    print()
    
    # Paso 1: Extraer dataset
    print("📊 Paso 1: Extrayendo dataset del rosbag...")
    print("-" * 70)
    try:
        result = subprocess.run(
            [sys.executable, "extract_dataset.py", str(rosbag_path)],
            check=True,
            capture_output=False
        )
        print()
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al extraer dataset: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Error: extract_dataset.py no encontrado")
        sys.exit(1)
    
    # Verificar que el dataset se generó
    if not dataset_csv.exists():
        print(f"❌ Error: No se generó el dataset en {dataset_csv}")
        sys.exit(1)
    
    print("✅ Dataset generado exitosamente")
    print()
    
    # Paso 2: Extraer frames del video
    if not video_path.exists():
        print(f"⚠️  Video no encontrado: {video_path}")
        print("   Omitiendo extracción de frames")
        sys.exit(0)
    
    print("🎬 Paso 2: Extrayendo frames del video...")
    print("-" * 70)
    try:
        result = subprocess.run(
            [sys.executable, "extract_video_frames.py", str(video_path), str(dataset_csv)],
            check=True,
            capture_output=False
        )
        print()
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al extraer frames: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Error: extract_video_frames.py no encontrado")
        sys.exit(1)
    
    print("✅ Frames extraídos exitosamente")
    print()
    
    # Resumen final
    print("=" * 70)
    print("🎉 EXTRACCIÓN COMPLETA FINALIZADA")
    print("=" * 70)
    print(f"📂 Dataset: {output_dir}")
    print(f"   - CSV: {dataset_csv.name}")
    print(f"   - Frames: {output_dir / 'frames'}")
    print(f"   - Mapeo: {output_dir / 'frame_to_timestamp_mapping.csv'}")
    print()


if __name__ == "__main__":
    main()
