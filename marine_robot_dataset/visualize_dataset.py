#!/usr/bin/env python3
"""
Script para visualizar muestras del dataset generado.
Muestra frame + pose del robot + ángulos de articulaciones.
"""

import cv2
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import ast


def visualize_sample(dataset_path, sample_idx=0):
    """Visualiza una muestra específica del dataset"""
    
    df = pd.read_csv(dataset_path)
    dataset_dir = Path(dataset_path).parent
    
    if sample_idx >= len(df):
        print(f"Sample {sample_idx} fuera de rango (max: {len(df)-1})")
        return
    
    row = df.iloc[sample_idx]
    
    frame_path = dataset_dir / "frames" / row['frame_path']
    if not frame_path.exists():
        print(f"Frame no encontrado: {frame_path}")
        print("Ejecuta primero: python3 extract_dataset.py <rosbag>")
        return
    
    img = cv2.imread(str(frame_path))
    
    # Parsear datos de joints
    joint_names = ast.literal_eval(row['joint_names'])
    joint_positions = ast.literal_eval(row['joint_positions'])
    
    # Crear visualización con info
    h, w = img.shape[:2]
    vis = np.zeros((h + 300, w, 3), dtype=np.uint8)
    vis[:h, :] = img
    
    # Texto de información
    y_offset = h + 30
    font = cv2.FONT_HERSHEY_SIMPLEX
    
    # Timestamp
    cv2.putText(vis, f"Timestamp: {row['timestamp']:.3f}s", 
                (10, y_offset), font, 0.6, (255, 255, 255), 1)
    y_offset += 30
    
    # Posición
    heave_dt = row.get('heave_dt_ms', None)
    heave_info = f" (dt={heave_dt:.0f}ms)" if heave_dt is not None else ""
    cv2.putText(vis, f"Position: X={row['position_x']:.3f} Y={row['position_y']:.3f} Heave={row['heave']:.4f}{heave_info}", 
                (10, y_offset), font, 0.5, (0, 255, 0), 1)
    y_offset += 25
    
    # Orientación (Euler angles)
    # Verificar si el dataset tiene roll/pitch/yaw o quaternion
    if 'roll' in row:
        roll_deg = np.degrees(row['roll'])
        pitch_deg = np.degrees(row['pitch'])
        yaw_deg = np.degrees(row['yaw'])
        cv2.putText(vis, f"Orientation: Roll={roll_deg:.1f}° Pitch={pitch_deg:.1f}° Yaw={yaw_deg:.1f}°", 
                    (10, y_offset), font, 0.5, (0, 255, 255), 1)
    else:
        cv2.putText(vis, f"Orientation: [{row['orientation_x']:.2f}, {row['orientation_y']:.2f}, "
                    f"{row['orientation_z']:.2f}, {row['orientation_w']:.2f}]", 
                    (10, y_offset), font, 0.5, (0, 255, 255), 1)
    y_offset += 30
    
    # Joints (primeros 6)
    cv2.putText(vis, "Joint Positions:", (10, y_offset), font, 0.5, (255, 200, 0), 1)
    y_offset += 25
    
    for i, (name, pos) in enumerate(zip(joint_names[:6], joint_positions[:6])):
        cv2.putText(vis, f"  {name}: {pos:.3f} rad", 
                    (15, y_offset), font, 0.4, (200, 200, 200), 1)
        y_offset += 20
    
    cv2.imshow(f'Dataset Sample {sample_idx}', vis)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def play_dataset(dataset_path, fps=30):
    """Reproduce el dataset como un video"""
    
    df = pd.read_csv(dataset_path)
    dataset_dir = Path(dataset_path).parent
    
    print(f"Reproduciendo dataset ({len(df)} frames)")
    print("Presiona 'q' para salir, 'p' para pausar")
    
    paused = False
    for idx in range(len(df)):
        if not paused:
            visualize_sample(dataset_path, idx)
            
        key = cv2.waitKey(int(1000/fps)) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('p'):
            paused = not paused
            print("Pausado" if paused else "Reproduciendo")
    
    cv2.destroyAllWindows()


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 visualize_dataset.py <dataset.csv> [sample_idx]")
        print("Ejemplo: python3 visualize_dataset.py datasets/marine_sim_20260116_172734/dataset.csv 0")
        print("\nPara reproducir todo: python3 visualize_dataset.py <dataset.csv> play")
        sys.exit(1)
    
    dataset_path = Path(sys.argv[1])
    
    if not dataset_path.exists():
        print(f"Dataset no encontrado: {dataset_path}")
        sys.exit(1)
    
    if len(sys.argv) > 2:
        if sys.argv[2] == 'play':
            play_dataset(dataset_path)
        else:
            sample_idx = int(sys.argv[2])
            visualize_sample(dataset_path, sample_idx)
    else:
        visualize_sample(dataset_path, 0)


if __name__ == "__main__":
    main()
