#!/usr/bin/env python3
"""
03_calibrate.py — Calibración de cámara.

Uso:
    python3 scripts/03_calibrate.py              # pinhole (default)
    python3 scripts/03_calibrate.py --fisheye     # fisheye (equidistante, 4 coefs)
"""
import argparse
import re
import sys
from pathlib import Path

import cv2
import numpy as np
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR.parent / "config.yaml"


def load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fisheye", action="store_true", help="Usar modelo fisheye")
    args = parser.parse_args()
    model = "fisheye" if args.fisheye else "pinhole"

    cfg = load_config()
    cal = cfg["calibration"]

    cb_size = (cal["checkerboard_cols"], cal["checkerboard_rows"])
    square_m = cal["square_size_mm"] / 1000.0
    images_dir = SCRIPT_DIR.parent / cal["images_dir"]
    result_file = SCRIPT_DIR.parent / cal["result_file"]

    print(f"═══ Calibración de cámara ({model}) ═══")
    print(f"  Checkerboard: {cb_size[0]}×{cb_size[1]} esquinas interiores")
    print(f"  Tamaño cuadro: {cal['square_size_mm']} mm")

    # --- Detectar esquinas ---
    image_paths = sorted(images_dir.glob("calib_*.png"))
    if not image_paths:
        print(f"ERROR: No hay imágenes en {images_dir}")
        sys.exit(1)

    # Puntos 3D del patrón
    objp = np.zeros((cb_size[0] * cb_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:cb_size[0], 0:cb_size[1]].T.reshape(-1, 2)
    objp *= square_m

    obj_points = []
    img_points = []
    used = []
    image_size = None
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    for i, path in enumerate(image_paths):
        img = cv2.imread(str(path))
        if img is None:
            print(f"  [{i+1}/{len(image_paths)}] ⚠ No se pudo leer: {path.name}")
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if image_size is None:
            image_size = (gray.shape[1], gray.shape[0])

        found, corners = cv2.findChessboardCorners(
            gray, cb_size,
            cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE,
        )
        if found:
            corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            obj_points.append(objp)
            img_points.append(corners)
            used.append(path.name)
            print(f"  [{i+1}/{len(image_paths)}] ✓ {path.name}")
        else:
            print(f"  [{i+1}/{len(image_paths)}] ✗ {path.name}")

    print(f"\nImágenes usadas: {len(used)} / {len(image_paths)}")
    if len(used) < 5:
        print("ERROR: Se necesitan al menos 5 imágenes.")
        sys.exit(1)

    # --- Calibrar ---
    print(f"\nCalibrando ({model})...")
    if model == "fisheye":
        # fisheye necesita shape (1, N, 3) y (1, N, 2)
        obj_fish = [o.reshape(1, -1, 3) for o in obj_points]
        img_fish = [p.reshape(1, -1, 2) for p in img_points]
        K = np.zeros((3, 3), dtype=np.float64)
        D = np.zeros((4, 1), dtype=np.float64)
        flags = cv2.fisheye.CALIB_RECOMPUTE_EXTRINSIC | cv2.fisheye.CALIB_FIX_SKEW
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 1e-6)
        rms, K, D, _, _ = cv2.fisheye.calibrate(
            obj_fish, img_fish, image_size, K, D, flags=flags, criteria=criteria,
        )
    else:
        rms, K, D, _, _ = cv2.calibrateCamera(
            obj_points, img_points, image_size, None, None,
        )
    d = D.flatten()

    print(f"\n═══ Resultados ({model}) ═══")
    print(f"  RMS: {rms:.4f} px")
    print(f"  fx = {K[0,0]:.2f}  fy = {K[1,1]:.2f}")
    print(f"  cx = {K[0,2]:.2f}  cy = {K[1,2]:.2f}")
    if model == "fisheye":
        print(f"  k1={d[0]:.6f}  k2={d[1]:.6f}  k3={d[2]:.6f}  k4={d[3]:.6f}")
    else:
        print(f"  k1={d[0]:.6f}  k2={d[1]:.6f}  p1={d[2]:.6f}  p2={d[3]:.6f}  k3={d[4]:.6f}")

    # --- Guardar calibration_result.yaml ---
    result_file.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "image_width": image_size[0],
        "image_height": image_size[1],
        "camera_matrix": {"rows": 3, "cols": 3, "data": [float(x) for x in K.flatten()]},
        "distortion_coefficients": {"rows": 1, "cols": len(d), "data": [float(x) for x in d]},
        "reprojection_error_rms": float(rms),
        "num_images_used": len(used),
    }
    with open(result_file, "w") as f:
        yaml.dump(result, f, default_flow_style=False, sort_keys=False)
    print(f"\n  ✓ {result_file}")

    # --- Actualizar config.yaml ---
    with open(CONFIG_PATH, "r") as f:
        raw = f.read()

    matrix_str = (
        f"[\n"
        f"    [{K[0,0]:.6f}, {K[0,1]:.6f}, {K[0,2]:.6f}],\n"
        f"    [{K[1,0]:.6f}, {K[1,1]:.6f}, {K[1,2]:.6f}],\n"
        f"    [{K[2,0]:.6f}, {K[2,1]:.6f}, {K[2,2]:.6f}]\n"
        f"  ]"
    )
    dist_str = "[" + ", ".join(f"{x:.8f}" for x in d) + "]"

    # matrix: null → valores
    raw = re.sub(r"(matrix:\s*)null", rf"\g<1>{matrix_str}", raw)
    # matrix: [...] → valores (si ya tenía datos)
    raw = re.sub(r"(matrix:\s*)\[[\s\S]*?\]\s*\]", rf"\g<1>{matrix_str}", raw)
    # dist_coeffs: null → valores
    raw = re.sub(r"(dist_coeffs:\s*)null", rf"\1{dist_str}", raw)
    # dist_coeffs: [...] → valores
    raw = re.sub(r"(dist_coeffs:\s*)\[[^\]]+\]", rf"\1{dist_str}", raw)
    # reprojection_error
    raw = re.sub(r"(reprojection_error_px:\s*)[\w.]+", rf"\g<1>{rms:.6f}", raw)
    # distortion_model
    if "distortion_model:" in raw:
        raw = re.sub(r'(distortion_model:\s*)"?\w+"?', f'\\1"{model}"', raw)
    else:
        raw = raw.replace(
            f"reprojection_error_px: {rms:.6f}",
            f'reprojection_error_px: {rms:.6f}\n  distortion_model: "{model}"',
        )

    with open(CONFIG_PATH, "w") as f:
        f.write(raw)
    print(f"  ✓ config.yaml actualizado (modelo: {model})")

    print(f"\n═══ Siguiente paso ═══")
    print(f"  python3 scripts/04_validate_calibration.py")


if __name__ == "__main__":
    main()
