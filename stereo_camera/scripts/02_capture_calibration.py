#!/usr/bin/env python3
"""
02_capture_calibration.py — Captura de imágenes para calibración de cámara.

Abre la cámara estéreo, recorta el lente seleccionado en config.yaml,
y permite capturar imágenes del patrón checkerboard para calibración.

Detecta esquinas del checkerboard en tiempo real y muestra overlay visual.

Controles:
    SPACE  → capturar imagen (solo si se detectaron esquinas)
    S      → capturar imagen (forzar, sin detección de esquinas)
    Q      → salir
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR.parent / "config.yaml"


def load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def crop_eye(frame: np.ndarray, eye: str, eye_w: int) -> np.ndarray:
    """Recorta el lente seleccionado del frame estéreo side-by-side."""
    if eye == "left":
        return frame[:, :eye_w].copy()
    else:
        return frame[:, eye_w:].copy()


def main() -> None:
    cfg = load_config()
    cam_cfg = cfg["camera"]
    cal_cfg = cfg["calibration"]

    device = cam_cfg["device"]
    full_w = cam_cfg["full_width"]
    full_h = cam_cfg["full_height"]
    eye_w = cam_cfg["eye_width"]
    eye_h = cam_cfg["eye_height"]
    fps = cam_cfg["fps"]
    selected_eye = cam_cfg["selected_eye"]

    cb_cols = cal_cfg["checkerboard_cols"]
    cb_rows = cal_cfg["checkerboard_rows"]
    images_dir = SCRIPT_DIR.parent / cal_cfg["images_dir"]
    min_images = cal_cfg["min_images"]

    # Crear directorio de imágenes si no existe
    images_dir.mkdir(parents=True, exist_ok=True)

    # Contar imágenes existentes
    existing = list(images_dir.glob("calib_*.png"))
    img_count = len(existing)

    print(f"═══ Captura de imágenes para calibración ═══")
    print(f"  Cámara: {device}")
    print(f"  Lente: {selected_eye.upper()}")
    print(f"  Resolución por ojo: {eye_w}×{eye_h}")
    print(f"  Checkerboard: {cb_cols}×{cb_rows} esquinas interiores")
    print(f"  Imágenes existentes: {img_count}")
    print(f"  Mínimo recomendado: {min_images}")
    print()
    print("Controles:")
    print("  SPACE → capturar (con detección de esquinas)")
    print("  S     → capturar (forzar, sin detección)")
    print("  Q     → salir")
    print()

    # Abrir cámara
    dev_index = int(device.replace("/dev/video", ""))
    cap = cv2.VideoCapture(dev_index, cv2.CAP_V4L2)
    if not cap.isOpened():
        print(f"ERROR: No se pudo abrir {device}")
        sys.exit(1)

    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    cap.set(cv2.CAP_PROP_FOURCC, fourcc)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, full_w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, full_h)
    cap.set(cv2.CAP_PROP_FPS, fps)

    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if actual_w != full_w:
        eye_w = actual_w // 2
        eye_h = actual_h

    # Criterio de terminación para cornerSubPix
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    checkerboard_size = (cb_cols, cb_rows)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("ERROR: No se pudo leer frame")
            break

        eye_img = crop_eye(frame, selected_eye, eye_w)
        gray = cv2.cvtColor(eye_img, cv2.COLOR_BGR2GRAY)

        # Intentar detectar esquinas del checkerboard
        found, corners = cv2.findChessboardCorners(
            gray, checkerboard_size,
            cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE + cv2.CALIB_CB_FAST_CHECK
        )

        display = eye_img.copy()

        if found:
            # Refinar esquinas a sub-pixel
            corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            cv2.drawChessboardCorners(display, checkerboard_size, corners_refined, found)
            status_text = f"DETECTADO | Imagenes: {img_count}/{min_images} | SPACE=capturar"
            status_color = (0, 255, 0)
        else:
            status_text = f"Buscando checkerboard... | Imagenes: {img_count}/{min_images}"
            status_color = (0, 0, 255)

        # Barra de estado
        cv2.rectangle(display, (0, 0), (eye_w, 50), (0, 0, 0), -1)
        cv2.putText(display, status_text, (10, 35),
                     cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

        # Progreso
        if img_count >= min_images:
            prog_text = f"OK: {img_count} imagenes capturadas (min: {min_images})"
            cv2.putText(display, prog_text, (10, eye_h - 20),
                         cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Mostrar redimensionado si es muy grande
        scale = min(1.0, 1280.0 / eye_w)
        if scale < 1.0:
            disp = cv2.resize(display, (int(eye_w * scale), int(eye_h * scale)))
        else:
            disp = display
        cv2.imshow("Calibration Capture", disp)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == ord("Q"):
            break
        elif key == ord(" ") and found:
            # Guardar imagen original (sin overlay) al presionar SPACE
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"calib_{img_count:03d}_{timestamp}.png"
            filepath = images_dir / filename
            cv2.imwrite(str(filepath), eye_img)
            img_count += 1
            print(f"  [{img_count:3d}] Guardada: {filename}")
        elif key == ord("s") or key == ord("S"):
            # Guardar forzado sin detección
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"calib_{img_count:03d}_{timestamp}.png"
            filepath = images_dir / filename
            cv2.imwrite(str(filepath), eye_img)
            img_count += 1
            print(f"  [{img_count:3d}] Guardada (forzado): {filename}")

    cap.release()
    cv2.destroyAllWindows()

    print(f"\n═══ Resumen ═══")
    print(f"  Total imágenes: {img_count}")
    print(f"  Directorio: {images_dir}")
    if img_count >= min_images:
        print(f"  ✓ Listo para calibrar: python3 scripts/03_calibrate.py")
    else:
        print(f"  ⚠ Faltan {min_images - img_count} imágenes (mínimo: {min_images})")


if __name__ == "__main__":
    main()
