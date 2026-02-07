#!/usr/bin/env python3
"""
Script completo para extraer dataset desde un rosbag.
Las imágenes se extraen directamente del rosbag (con timestamps ROS exactos),
junto con los datos de pose, IMU y articulaciones sincronizados.

Uso: python3 extract_complete_dataset.py <path_to_rosbag>
"""

import sys
import subprocess
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 extract_complete_dataset.py <path_to_rosbag>")
        print("Ejemplo: python3 extract_complete_dataset.py ../rosbags/marine_sim_20260207_143824")
        sys.exit(1)

    rosbag_path = Path(sys.argv[1])
    rosbag_name = rosbag_path.name
    output_dir = Path("datasets") / rosbag_name

    print("=" * 60)
    print("  EXTRACCION DE DATASET DESDE ROSBAG")
    print("=" * 60)
    print(f"Rosbag: {rosbag_path}")
    print(f"Output: {output_dir}")
    print()

    try:
        subprocess.run(
            [sys.executable, "extract_dataset.py", str(rosbag_path)],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error al extraer dataset: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: extract_dataset.py no encontrado")
        sys.exit(1)

    dataset_csv = output_dir / "dataset.csv"
    frames_dir = output_dir / "frames"

    print()
    print("=" * 60)
    print("  EXTRACCION COMPLETADA")
    print("=" * 60)
    print(f"  CSV:    {dataset_csv}")
    print(f"  Frames: {frames_dir}")
    print(f"  Mapeo:  {output_dir / 'frame_to_timestamp_mapping.csv'}")
    print()


if __name__ == "__main__":
    main()
