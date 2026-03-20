#!/usr/bin/env python3
"""
03_auto_calibrate.py — Calibración automática: prueba múltiples modelos,
valida cada uno, y muestra los resultados para elegir el mejor.

El problema con pocos puntos (ej. 3×4 = 12 esquinas) es que modelos con
muchos parámetros sobreajustan. Este script prueba desde el modelo más
conservador (1 parámetro) hasta el más complejo, y valida que el undistort
sea razonable antes de aceptar.

Uso:
    python3 scripts/03_auto_calibrate.py            # auto-prueba todo
    python3 scripts/03_auto_calibrate.py --save N   # guardar modelo N
"""
from __future__ import annotations

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


# ─── Checkerboard detection ───────────────────────────────────────────

def gather_checkerboard_points(
    images_dir: Path,
    checkerboard_size: tuple[int, int],
    square_size_m: float,
) -> tuple[list, list, list, tuple[int, int] | None]:
    """Find checkerboard corners in all calibration images.
    Returns obj_points, img_points, image_paths_used, image_size.
    obj_points shape: each element is (1, N, 3) for fisheye compat.
    img_points shape: each element is (1, N, 2).
    """
    image_paths = sorted(images_dir.glob("calib_*.png"))
    if not image_paths:
        return [], [], [], None

    N = checkerboard_size[0] * checkerboard_size[1]
    objp = np.zeros((1, N, 3), np.float32)
    objp[0, :, :2] = np.mgrid[
        0 : checkerboard_size[0], 0 : checkerboard_size[1]
    ].T.reshape(-1, 2)
    objp *= square_size_m

    obj_points, img_points, used_paths = [], [], []
    image_size = None
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    for i, p in enumerate(image_paths):
        img = cv2.imread(str(p))
        if img is None:
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if image_size is None:
            image_size = (gray.shape[1], gray.shape[0])

        found, corners = cv2.findChessboardCorners(
            gray, checkerboard_size,
            cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE,
        )
        if found:
            corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            obj_points.append(objp)
            img_points.append(corners.reshape(1, -1, 2))
            used_paths.append(p)
            print(f"  [{i+1}/{len(image_paths)}] ✓ {p.name}")
        else:
            print(f"  [{i+1}/{len(image_paths)}] ✗ {p.name}")

    return obj_points, img_points, used_paths, image_size


# ─── Calibración por modelo ──────────────────────────────────────────

def calibrate_model(
    name: str,
    obj_points: list,
    img_points: list,
    image_size: tuple[int, int],
) -> dict | None:
    """Try one calibration configuration. Returns dict with results or None on failure."""
    try:
        if name.startswith("fisheye"):
            return _calibrate_fisheye_variant(name, obj_points, img_points, image_size)
        else:
            return _calibrate_pinhole_variant(name, obj_points, img_points, image_size)
    except Exception as e:
        print(f"    ⚠ {name}: FALLÓ — {e}")
        return None


def _calibrate_fisheye_variant(
    name: str, obj_points, img_points, image_size
) -> dict:
    K = np.zeros((3, 3), dtype=np.float64)
    D = np.zeros((4, 1), dtype=np.float64)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 1e-6)

    base_flags = cv2.fisheye.CALIB_RECOMPUTE_EXTRINSIC | cv2.fisheye.CALIB_FIX_SKEW

    if name == "fisheye_k1":
        flags = base_flags | cv2.fisheye.CALIB_FIX_K2 | cv2.fisheye.CALIB_FIX_K3 | cv2.fisheye.CALIB_FIX_K4
    elif name == "fisheye_k1k2":
        flags = base_flags | cv2.fisheye.CALIB_FIX_K3 | cv2.fisheye.CALIB_FIX_K4
    elif name == "fisheye_k1k2k3":
        flags = base_flags | cv2.fisheye.CALIB_FIX_K4
    elif name == "fisheye_full":
        flags = base_flags
    else:
        flags = base_flags | cv2.fisheye.CALIB_FIX_K3 | cv2.fisheye.CALIB_FIX_K4

    try:
        flags_with_check = flags | cv2.fisheye.CALIB_CHECK_COND
        rms, K, D, _, _ = cv2.fisheye.calibrate(
            obj_points, img_points, image_size, K, D,
            flags=flags_with_check, criteria=criteria,
        )
    except cv2.error:
        K = np.zeros((3, 3), dtype=np.float64)
        D = np.zeros((4, 1), dtype=np.float64)
        rms, K, D, _, _ = cv2.fisheye.calibrate(
            obj_points, img_points, image_size, K, D,
            flags=flags, criteria=criteria,
        )

    return {"model": "fisheye", "variant": name, "K": K, "D": D.flatten(), "rms": rms}


def _calibrate_pinhole_variant(
    name: str, obj_points, img_points, image_size
) -> dict:
    obj_ph = [op.reshape(-1, 3) for op in obj_points]
    img_ph = [ip.reshape(-1, 1, 2) for ip in img_points]

    if name == "pinhole_k1":
        flags = cv2.CALIB_FIX_K2 | cv2.CALIB_FIX_K3 | cv2.CALIB_ZERO_TANGENT_DIST
    elif name == "pinhole_k1k2":
        flags = cv2.CALIB_FIX_K3 | cv2.CALIB_ZERO_TANGENT_DIST
    elif name == "pinhole_k1k2_tangential":
        flags = cv2.CALIB_FIX_K3
    elif name == "pinhole_full":
        flags = 0
    else:
        flags = cv2.CALIB_FIX_K2 | cv2.CALIB_FIX_K3 | cv2.CALIB_ZERO_TANGENT_DIST

    rms, K, D, _, _ = cv2.calibrateCamera(
        obj_ph, img_ph, image_size, None, None, flags=flags
    )

    return {"model": "pinhole", "variant": name, "K": K, "D": D.flatten(), "rms": rms}


# ─── Validación de undistort ──────────────────────────────────────────

def validate_undistort(
    result: dict, sample_img: np.ndarray, image_size: tuple[int, int]
) -> dict:
    """Test undistortion on a sample image. Returns result dict with extra fields."""
    K = result["K"]
    D = result["D"]
    model = result["model"]

    if model == "fisheye":
        D4 = D[:4].reshape(4, 1) if len(D) >= 4 else np.zeros((4, 1))
        D4[:len(D)] = D.reshape(-1, 1)[:len(D)]

        # Try balance=0 (crop to valid region)
        new_K = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(
            K, D4, image_size, np.eye(3), balance=0.0
        )
        map1, map2 = cv2.fisheye.initUndistortRectifyMap(
            K, D4, np.eye(3), new_K, image_size, cv2.CV_16SC2
        )
    else:
        new_K, roi = cv2.getOptimalNewCameraMatrix(K, D, image_size, 0, image_size)
        map1, map2 = cv2.initUndistortRectifyMap(K, D, None, new_K, image_size, cv2.CV_16SC2)

    undistorted = cv2.remap(sample_img, map1, map2, cv2.INTER_LINEAR)

    # Check quality: what fraction of pixels are black (0,0,0) or white (255,255,255)?
    gray_und = cv2.cvtColor(undistorted, cv2.COLOR_BGR2GRAY)
    total_px = gray_und.size
    black_frac = np.sum(gray_und < 5) / total_px
    white_frac = np.sum(gray_und > 250) / total_px
    dead_frac = black_frac + white_frac

    # Also check if new_K has reasonable values
    new_fx = new_K[0, 0]
    new_fy = new_K[1, 1]
    fx_ratio = new_fx / K[0, 0] if K[0, 0] > 0 else 0

    result["undistorted"] = undistorted
    result["new_K"] = new_K
    result["black_frac"] = black_frac
    result["white_frac"] = white_frac
    result["dead_frac"] = dead_frac
    result["fx_ratio"] = fx_ratio

    # Mark as valid if less than 50% dead pixels and fx ratio is reasonable
    result["valid"] = dead_frac < 0.50 and 0.3 < fx_ratio < 5.0

    return result


# ─── Save results ─────────────────────────────────────────────────────

def save_calibration(result: dict, image_size: tuple[int, int], num_images: int) -> None:
    """Save calibration to both calibration_result.yaml and config.yaml."""
    K = result["K"]
    D = result["D"]
    rms = result["rms"]
    model = result["model"]

    cfg = load_config()
    result_path = SCRIPT_DIR.parent / cfg["calibration"]["result_file"]

    # Save calibration_result.yaml
    cal_result = {
        "image_width": image_size[0],
        "image_height": image_size[1],
        "camera_name": "stereo_camera_single_eye",
        "distortion_model": model,
        "calibration_variant": result["variant"],
        "camera_matrix": {
            "rows": 3, "cols": 3,
            "data": [float(x) for x in K.flatten()],
        },
        "distortion_coefficients": {
            "rows": 1, "cols": len(D),
            "data": [float(x) for x in D],
        },
        "reprojection_error_rms": float(rms),
        "num_images_used": num_images,
    }
    result_path.parent.mkdir(parents=True, exist_ok=True)
    with open(result_path, "w") as f:
        yaml.dump(cal_result, f, default_flow_style=False, sort_keys=False)
    print(f"  ✓ {result_path}")

    # Update config.yaml
    _update_config(K, D, rms, model)
    print(f"  ✓ config.yaml")


def _update_config(K: np.ndarray, D: np.ndarray, rms: float, model: str) -> None:
    with open(CONFIG_PATH, "r") as f:
        raw = f.read()

    matrix_str = (
        f"[\n"
        f"    [{K[0,0]:.6f}, {K[0,1]:.6f}, {K[0,2]:.6f}],\n"
        f"    [{K[1,0]:.6f}, {K[1,1]:.6f}, {K[1,2]:.6f}],\n"
        f"    [{K[2,0]:.6f}, {K[2,1]:.6f}, {K[2,2]:.6f}]\n"
        f"  ]"
    )
    d = D.flatten()
    dist_str = "[" + ", ".join(f"{x:.8f}" for x in d) + "]"

    raw = re.sub(
        r"(intrinsics:\s*\n\s*#[^\n]*\n\s*matrix:\s*)null",
        f"\\g<1>{matrix_str}", raw,
    )
    raw = re.sub(
        r"(intrinsics:\s*\n\s*#[^\n]*\n\s*matrix:\s*)\[[\s\S]*?\]\s*\]",
        f"\\g<1>{matrix_str}", raw,
    )
    raw = re.sub(r"(dist_coeffs:\s*)null", f"\\1{dist_str}", raw)
    raw = re.sub(r"(dist_coeffs:\s*)\[[^\]]+\]", f"\\1{dist_str}", raw)
    raw = re.sub(r"(reprojection_error_px:\s*)[\w.]+", f"\\g<1>{rms:.6f}", raw)
    if "distortion_model:" in raw:
        raw = re.sub(r'(distortion_model:\s*)"?\w+"?', f'\\1"{model}"', raw)

    with open(CONFIG_PATH, "w") as f:
        f.write(raw)


# ─── Display ──────────────────────────────────────────────────────────

def show_comparison(results: list[dict], sample_img: np.ndarray) -> int | None:
    """Show interactive comparison. Returns index of selected model, or None."""
    valid_results = [r for r in results if r.get("undistorted") is not None]
    if not valid_results:
        print("ERROR: Ningún modelo produjo resultado.")
        return None

    # Build display
    thumb_w, thumb_h = 480, 270  # 16:9 thumbnails
    cols = min(3, len(valid_results) + 1)  # +1 for original
    rows = (len(valid_results) + 1 + cols - 1) // cols

    canvas_w = cols * thumb_w
    canvas_h = rows * (thumb_h + 40)  # 40px for text
    canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)

    # Original in position 0
    orig_thumb = cv2.resize(sample_img, (thumb_w, thumb_h))
    cv2.putText(orig_thumb, "ORIGINAL", (5, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    y0, x0 = 0, 0
    canvas[y0:y0+thumb_h, x0:x0+thumb_w] = orig_thumb

    # Each model result
    for idx, r in enumerate(valid_results):
        pos = idx + 1  # position in grid (0 is original)
        row = pos // cols
        col = pos % cols
        y = row * (thumb_h + 40)
        x = col * thumb_w

        thumb = cv2.resize(r["undistorted"], (thumb_w, thumb_h))

        # Color code: green if valid, red if not
        color = (0, 255, 0) if r["valid"] else (0, 0, 255)
        tag = "✓" if r["valid"] else "✗"

        # Label
        label = f"[{idx+1}] {r['variant']}"
        cv2.putText(thumb, label, (5, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

        info1 = f"RMS={r['rms']:.3f} dead={r['dead_frac']*100:.0f}%"
        cv2.putText(thumb, info1, (5, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

        d = r["D"]
        dist_txt = " ".join(f"{x:.3f}" for x in d[:4])
        cv2.putText(thumb, f"D=[{dist_txt}]", (5, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (200, 200, 200), 1)

        # Reference lines
        for y_line in range(0, thumb_h, thumb_h // 6):
            cv2.line(thumb, (0, y_line), (thumb_w, y_line), (255, 255, 0), 1)

        canvas[y:y+thumb_h, x:x+thumb_w] = thumb

    # Instructions at bottom
    last_row_y = (rows - 1) * (thumb_h + 40) + thumb_h + 5
    if last_row_y + 30 < canvas_h:
        cv2.putText(canvas, "Presiona 1-9 para guardar ese modelo, Q para salir",
                    (10, last_row_y + 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

    print(f"\n═══ Comparación visual ═══")
    print(f"  Ventana: {cols}×{rows} thumbnails")
    print(f"  Presiona 1-{len(valid_results)} para guardar, Q para salir sin guardar")
    print()
    for idx, r in enumerate(valid_results):
        tag = "✓" if r["valid"] else "✗"
        d = r["D"]
        dist_str = ", ".join(f"{x:.4f}" for x in d[:4])
        print(f"  [{idx+1}] {tag} {r['variant']:25s} RMS={r['rms']:.4f}  dead={r['dead_frac']*100:.1f}%  D=[{dist_str}]")

    cv2.imshow("Auto-Calibration Comparison", canvas)

    while True:
        key = cv2.waitKey(0) & 0xFF
        if key == ord("q") or key == ord("Q") or key == 27:
            cv2.destroyAllWindows()
            return None
        # Number keys 1-9
        num = key - ord("0")
        if 1 <= num <= len(valid_results):
            cv2.destroyAllWindows()
            return num - 1  # return index into valid_results

    return None


# ─── Main ─────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Auto-calibración con múltiples modelos")
    parser.add_argument("--save", type=int, default=None, metavar="N",
                        help="Guardar modelo N directamente (sin GUI)")
    args = parser.parse_args()

    cfg = load_config()
    cal_cfg = cfg["calibration"]

    cb_cols = cal_cfg["checkerboard_cols"]
    cb_rows = cal_cfg["checkerboard_rows"]
    square_size_mm = cal_cfg["square_size_mm"]
    images_dir = SCRIPT_DIR.parent / cal_cfg["images_dir"]

    checkerboard_size = (cb_cols, cb_rows)
    square_size_m = square_size_mm / 1000.0

    print(f"═══ Auto-Calibración ═══")
    print(f"  Checkerboard: {cb_cols}×{cb_rows} esquinas")
    print(f"  Tamaño cuadro: {square_size_mm} mm")
    print()

    # Detect corners
    print("Detectando esquinas...")
    obj_points, img_points, used_paths, image_size = \
        gather_checkerboard_points(images_dir, checkerboard_size, square_size_m)

    if not obj_points:
        print(f"ERROR: No se encontraron esquinas en {images_dir}")
        sys.exit(1)

    n_imgs = len(obj_points)
    print(f"\n  Imágenes usadas: {n_imgs}")

    if n_imgs < 5:
        print(f"ERROR: Se necesitan al menos 5 imágenes.")
        sys.exit(1)

    # Load a sample image for validation
    sample_img = cv2.imread(str(used_paths[n_imgs // 2]))  # middle image

    # ─── Try multiple models ───
    models_to_try = [
        "pinhole_k1",
        "pinhole_k1k2",
        "pinhole_k1k2_tangential",
        "fisheye_k1",
        "fisheye_k1k2",
        "fisheye_k1k2k3",
        "fisheye_full",
    ]

    print(f"\n═══ Probando {len(models_to_try)} configuraciones ═══\n")

    results = []
    for name in models_to_try:
        print(f"  → {name}...", end=" ", flush=True)
        r = calibrate_model(name, obj_points, img_points, image_size)
        if r is not None:
            r = validate_undistort(r, sample_img, image_size)
            results.append(r)
            tag = "✓" if r["valid"] else "✗"
            print(f"{tag} RMS={r['rms']:.4f}  dead={r['dead_frac']*100:.1f}%  D=[{', '.join(f'{x:.3f}' for x in r['D'][:4])}]")
        else:
            print("FALLÓ")

    if not results:
        print("ERROR: Ningún modelo funcionó.")
        sys.exit(1)

    # If --save N, just save that one
    if args.save is not None:
        valid_results = [r for r in results if r.get("undistorted") is not None]
        idx = args.save - 1
        if 0 <= idx < len(valid_results):
            chosen = valid_results[idx]
            print(f"\nGuardando modelo [{args.save}] {chosen['variant']}...")
            save_calibration(chosen, image_size, n_imgs)
            return
        else:
            print(f"ERROR: índice {args.save} fuera de rango (1-{len(valid_results)})")
            sys.exit(1)

    # Show comparison GUI
    valid_results = [r for r in results if r.get("undistorted") is not None]
    chosen_idx = show_comparison(valid_results, sample_img)

    if chosen_idx is not None:
        chosen = valid_results[chosen_idx]
        print(f"\n═══ Guardando modelo [{chosen_idx+1}] {chosen['variant']} ═══")
        save_calibration(chosen, image_size, n_imgs)
        print(f"\n✓ Calibración guardada.")
        print(f"  Siguiente: python3 scripts/04_validate_calibration.py")
    else:
        print("\n  No se guardó nada.")


if __name__ == "__main__":
    main()
