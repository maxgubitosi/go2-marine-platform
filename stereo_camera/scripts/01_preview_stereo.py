#!/usr/bin/env python3
"""
01_preview_stereo.py — Previsualización de cámara estéreo side-by-side.

Abre la cámara estéreo 3D USB Camera en /dev/video2, muestra el frame
completo y cada ojo por separado. Permite elegir qué lente usar (L/R)
y guarda la elección en config.yaml.

Controles:
    L  → seleccionar lente izquierdo
    R  → seleccionar lente derecho
    Q  → salir sin cambiar
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import cv2
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR.parent / "config.yaml"


def load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def save_selected_eye(eye: str) -> None:
    """Update only the selected_eye field in config.yaml."""
    with open(CONFIG_PATH, "r") as f:
        raw = f.read()

    # Simple replacement to preserve comments and formatting
    import re
    new_raw = re.sub(
        r'(selected_eye:\s*)"?\w+"?',
        f'\\1"{eye}"',
        raw,
    )
    with open(CONFIG_PATH, "w") as f:
        f.write(new_raw)
    print(f"\n✓ Lente seleccionado: {eye.upper()} — guardado en config.yaml")


def main() -> None:
    cfg = load_config()
    cam_cfg = cfg["camera"]
    device = cam_cfg["device"]
    full_w = cam_cfg["full_width"]
    full_h = cam_cfg["full_height"]
    eye_w = cam_cfg["eye_width"]
    eye_h = cam_cfg["eye_height"]
    fps = cam_cfg["fps"]

    print(f"Abriendo cámara estéreo: {device}")
    print(f"  Frame completo: {full_w}×{full_h}  @ {fps} fps  MJPG")
    print(f"  Cada ojo: {eye_w}×{eye_h}")
    print()
    print("Controles:")
    print("  L → seleccionar lente izquierdo")
    print("  R → seleccionar lente derecho")
    print("  Q → salir sin cambiar")

    # Extraer índice numérico del device path
    dev_index = int(device.replace("/dev/video", ""))
    cap = cv2.VideoCapture(dev_index, cv2.CAP_V4L2)
    if not cap.isOpened():
        print(f"ERROR: No se pudo abrir {device}")
        sys.exit(1)

    # Configurar formato MJPG y resolución
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    cap.set(cv2.CAP_PROP_FOURCC, fourcc)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, full_w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, full_h)
    cap.set(cv2.CAP_PROP_FPS, fps)

    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"\nResolución real: {actual_w}×{actual_h} @ {actual_fps:.1f} fps")

    if actual_w != full_w or actual_h != full_h:
        print(f"⚠ Resolución diferente a la configurada ({full_w}×{full_h}).")
        print(f"  Ajustando eye_w = {actual_w // 2}")
        eye_w = actual_w // 2
        eye_h = actual_h

    selected = cam_cfg.get("selected_eye", "left")
    print(f"\nLente actual configurado: {selected.upper()}")
    print("Mostrando preview... (presiona L, R o Q)\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("ERROR: No se pudo leer frame")
            break

        left = frame[:, :eye_w]
        right = frame[:, eye_w:]

        # Redimensionar para visualización cómoda
        scale = 0.5
        disp_w = int(eye_w * scale)
        disp_h = int(eye_h * scale)

        left_disp = cv2.resize(left, (disp_w, disp_h))
        right_disp = cv2.resize(right, (disp_w, disp_h))

        # Agregar etiquetas
        cv2.putText(left_disp, "LEFT (L)", (20, 40),
                     cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        cv2.putText(right_disp, "RIGHT (R)", (20, 40),
                     cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

        # Marcar el lente seleccionado
        if selected == "left":
            cv2.rectangle(left_disp, (0, 0), (disp_w - 1, disp_h - 1), (0, 255, 0), 3)
        else:
            cv2.rectangle(right_disp, (0, 0), (disp_w - 1, disp_h - 1), (0, 0, 255), 3)

        # Mostrar side by side
        combined = cv2.hconcat([left_disp, right_disp])
        cv2.putText(combined, f"Seleccionado: {selected.upper()} | L/R para cambiar | Q para salir",
                     (20, disp_h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        cv2.imshow("Stereo Camera Preview", combined)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == ord("Q"):
            print("Saliendo sin cambios.")
            break
        elif key == ord("l") or key == ord("L"):
            selected = "left"
            save_selected_eye(selected)
        elif key == ord("r") or key == ord("R"):
            selected = "right"
            save_selected_eye(selected)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
