#!/usr/bin/env python3
"""
04_validate_calibration.py — Validación visual: original vs undistorted.

Controles:
    Q  → salir
    C  → capturar par de imágenes
"""
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


def crop_eye(frame, eye, eye_w):
    return frame[:, :eye_w].copy() if eye == "left" else frame[:, eye_w:].copy()


def main() -> None:
    cfg = load_config()
    cam = cfg["camera"]
    intr = cfg["intrinsics"]

    if intr["matrix"] is None or intr["dist_coeffs"] is None:
        print("ERROR: No hay calibración. Ejecutar primero 03_calibrate.py")
        sys.exit(1)

    K = np.array(intr["matrix"], dtype=np.float64)
    D = np.array(intr["dist_coeffs"], dtype=np.float64)
    rms = intr.get("reprojection_error_px", "?")
    model = intr.get("distortion_model", "pinhole")
    is_fisheye = model == "fisheye"

    print(f"═══ Validación de calibración ({model}) ═══")
    print(f"  fx={K[0,0]:.2f}  fy={K[1,1]:.2f}  cx={K[0,2]:.2f}  cy={K[1,2]:.2f}")
    print(f"  dist={D.flatten()}")
    print(f"  RMS: {rms}")
    print(f"  Controles: Q=salir, C=capturar")

    # Abrir cámara
    dev_index = int(cam["device"].replace("/dev/video", ""))
    cap = cv2.VideoCapture(dev_index, cv2.CAP_V4L2)
    if not cap.isOpened():
        print(f"ERROR: No se pudo abrir {cam['device']}")
        sys.exit(1)

    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    cap.set(cv2.CAP_PROP_FOURCC, fourcc)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam["full_width"])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam["full_height"])
    cap.set(cv2.CAP_PROP_FPS, cam["fps"])

    eye_w = cam["eye_width"]
    eye_h = cam["eye_height"]
    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    if actual_w != cam["full_width"]:
        eye_w = actual_w // 2
        eye_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Pre-calcular mapas de undistort
    if is_fisheye:
        D_fish = D.flatten()[:4].reshape(4, 1)
        new_K = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(
            K, D_fish, (eye_w, eye_h), np.eye(3), balance=0.0,
        )
        map1, map2 = cv2.fisheye.initUndistortRectifyMap(
            K, D_fish, np.eye(3), new_K, (eye_w, eye_h), cv2.CV_16SC2,
        )
    else:
        new_K, roi = cv2.getOptimalNewCameraMatrix(K, D, (eye_w, eye_h), 0, (eye_w, eye_h))
        map1, map2 = cv2.initUndistortRectifyMap(K, D, None, new_K, (eye_w, eye_h), cv2.CV_16SC2)

    output_dir = SCRIPT_DIR.parent / "calibration" / "validation"
    output_dir.mkdir(parents=True, exist_ok=True)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        eye_img = crop_eye(frame, cam["selected_eye"], eye_w)
        undist = cv2.remap(eye_img, map1, map2, cv2.INTER_LINEAR)

        # Resize para display
        scale = min(1.0, 640.0 / eye_w)
        dw, dh = int(eye_w * scale), int(eye_h * scale)
        orig_d = cv2.resize(eye_img, (dw, dh))
        undist_d = cv2.resize(undist, (dw, dh))

        # Labels y líneas de referencia
        cv2.putText(orig_d, "ORIGINAL", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        cv2.putText(undist_d, "UNDISTORTED", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        for y in range(0, dh, dh // 8):
            cv2.line(orig_d, (0, y), (dw, y), (255, 255, 0), 1)
            cv2.line(undist_d, (0, y), (dw, y), (255, 255, 0), 1)

        combined = cv2.hconcat([orig_d, undist_d])
        info = f"{model} | RMS: {rms} px | Q=salir C=capturar"
        cv2.putText(combined, info, (10, combined.shape[0] - 10),
                     cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
        cv2.imshow("Calibration Validation", combined)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("c"):
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            cv2.imwrite(str(output_dir / f"orig_{ts}.png"), eye_img)
            cv2.imwrite(str(output_dir / f"undist_{ts}.png"), undist)
            print(f"  Capturado: orig_{ts}.png + undist_{ts}.png")

    cap.release()
    cv2.destroyAllWindows()
    print(f"\n✓ Validación completada.")
    print(f"  Siguiente paso: python3 scripts/05_detect_aruco.py")


if __name__ == "__main__":
    main()
