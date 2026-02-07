#!/usr/bin/env python3
"""Estimate relative pose between drone camera and ArUco marker.

Outputs marker pose in camera frame using OpenCV's ArUco detector and
adds ground-truth columns from the dataset CSV for comparison.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
import yaml

try:
    import cv2
except ImportError as exc:
    raise SystemExit("OpenCV not installed. Run: pip3 install -r aruco_relative_pose/requirements.txt") from exc


ARUCO_DICTS = {
    "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
    "DICT_4X4_100": cv2.aruco.DICT_4X4_100,
    "DICT_4X4_250": cv2.aruco.DICT_4X4_250,
    "DICT_4X4_1000": cv2.aruco.DICT_4X4_1000,
    "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
    "DICT_5X5_100": cv2.aruco.DICT_5X5_100,
    "DICT_5X5_250": cv2.aruco.DICT_5X5_250,
    "DICT_5X5_1000": cv2.aruco.DICT_5X5_1000,
    "DICT_6X6_50": cv2.aruco.DICT_6X6_50,
    "DICT_6X6_100": cv2.aruco.DICT_6X6_100,
    "DICT_6X6_250": cv2.aruco.DICT_6X6_250,
    "DICT_6X6_1000": cv2.aruco.DICT_6X6_1000,
    "DICT_7X7_50": cv2.aruco.DICT_7X7_50,
    "DICT_7X7_100": cv2.aruco.DICT_7X7_100,
    "DICT_7X7_250": cv2.aruco.DICT_7X7_250,
    "DICT_7X7_1000": cv2.aruco.DICT_7X7_1000,
    "DICT_ARUCO_ORIGINAL": cv2.aruco.DICT_ARUCO_ORIGINAL,
}


def load_config(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if not isinstance(cfg, dict):
        raise ValueError("Config YAML invalido")
    return cfg



def parse_xacro_pattern(xacro_path: Path) -> np.ndarray:
    """Parse 6x6 marker bits from xacro comments.

    Expects comments like: "Row 1 - Black borders + pattern (1 0 0 1 1 0)".
    Returns bits with 1=black, 0=white.
    """
    text = xacro_path.read_text(encoding="utf-8")
    row_bits = {}
    for match in re.finditer(r"Row\s+(\d)\s+-\s+Black borders \+ pattern \(([^)]+)\)", text):
        row = int(match.group(1))
        bits = [int(x) for x in match.group(2).split()]
        row_bits[row] = bits

    bits = np.zeros((6, 6), dtype=np.uint8)
    for r in range(1, 7):
        if r not in row_bits:
            raise ValueError(f"Falta Row {r} en {xacro_path}")
        if len(row_bits[r]) != 6:
            raise ValueError(f"Row {r} invalida (esperaba 6 bits)")
        for c in range(6):
            bits[r - 1, c] = row_bits[r][c]
    return bits


def build_custom_dictionary(bits_6x6: np.ndarray, base_dict_name: str) -> cv2.aruco.Dictionary:
    """Create a dictionary using the provided 6x6 bits as marker id 0."""
    if bits_6x6.shape != (6, 6):
        raise ValueError("bits_6x6 debe ser 6x6")
    if base_dict_name not in ARUCO_DICTS:
        raise ValueError(f"Diccionario base no soportado: {base_dict_name}")
    base_dict = cv2.aruco.getPredefinedDictionary(ARUCO_DICTS[base_dict_name])
    byte_list = cv2.aruco.Dictionary_getByteListFromBits(bits_6x6)
    base_dict.bytesList = byte_list
    return base_dict


def preprocess_gray(gray: np.ndarray, mode: str) -> np.ndarray:
    if mode == "none":
        return gray
    if mode == "normalize":
        return cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    if mode == "clahe":
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(gray)
    if mode == "adaptive":
        norm = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
        return cv2.adaptiveThreshold(norm, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                     cv2.THRESH_BINARY, 31, 7)
    raise ValueError(f"preprocess invalido: {mode}")



def order_corners(pts: np.ndarray) -> np.ndarray:
    """Order corners as top-left, top-right, bottom-right, bottom-left."""
    pts = pts.reshape(-1, 2)
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1).reshape(-1)
    tl = pts[np.argmin(s)]
    br = pts[np.argmax(s)]
    tr = pts[np.argmin(diff)]
    bl = pts[np.argmax(diff)]
    return np.array([tl, tr, br, bl], dtype=np.float32)


def warp_marker(gray: np.ndarray, corners: np.ndarray, size: int = 160) -> np.ndarray:
    ordered = order_corners(corners)
    dst = np.array([[0, 0], [size - 1, 0], [size - 1, size - 1], [0, size - 1]], dtype=np.float32)
    M = cv2.getPerspectiveTransform(ordered, dst)
    return cv2.warpPerspective(gray, M, (size, size))


def parse_bit_pattern(pattern_rows: list[str]) -> np.ndarray:
    if len(pattern_rows) != 6:
        raise ValueError("bit_pattern debe tener 6 filas")
    bits = np.zeros((6, 6), dtype=np.uint8)
    for r, row in enumerate(pattern_rows):
        row = row.strip()
        if len(row) != 6 or any(ch not in "01" for ch in row):
            raise ValueError("Cada fila de bit_pattern debe tener 6 caracteres 0/1")
        for c, ch in enumerate(row):
            bits[r, c] = 1 if ch == "1" else 0
    return bits


def extract_grid_bits(warp: np.ndarray) -> np.ndarray:
    """Return 8x8 grid where 1=white, 0=black after normalization."""
    norm = cv2.normalize(warp, None, 0, 255, cv2.NORM_MINMAX)
    _, binary = cv2.threshold(norm, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # ensure border is black; if not, invert
    border = np.concatenate([
        binary[0, :], binary[-1, :], binary[:, 0], binary[:, -1]
    ])
    if border.mean() > 127:
        binary = 255 - binary
    grid = np.zeros((8, 8), dtype=np.uint8)
    cell = binary.shape[0] // 8
    for r in range(8):
        for c in range(8):
            block = binary[r * cell:(r + 1) * cell, c * cell:(c + 1) * cell]
            grid[r, c] = 1 if block.mean() > 127 else 0
    return grid


def validate_pattern(warp: np.ndarray, bits_6x6: np.ndarray, one_is_white: bool = True) -> bool:
    grid = extract_grid_bits(warp)
    # border must be black
    if grid[0, :].any() or grid[-1, :].any() or grid[:, 0].any() or grid[:, -1].any():
        return False
    # inner 6x6 compare
    inner = grid[1:7, 1:7]
    if one_is_white:
        return np.array_equal(inner, bits_6x6)
    return np.array_equal(inner, 1 - bits_6x6)


def detect_marker_quad(gray: np.ndarray, min_area_ratio: float = 0.0005) -> Optional[np.ndarray]:
    """Detect largest dark square (marker border). Returns 4x2 corners or None."""
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    img_area = gray.shape[0] * gray.shape[1]
    min_area = img_area * min_area_ratio
    candidates = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area:
            continue
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) != 4 or not cv2.isContourConvex(approx):
            continue
        x, y, w, h = cv2.boundingRect(approx)
        if h == 0:
            continue
        ar = w / h
        if ar < 0.7 or ar > 1.3:
            continue
        candidates.append((area, approx))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1].reshape(4, 2).astype(np.float32)


def load_template_image(path: Optional[Path], dictionary: cv2.aruco.Dictionary) -> np.ndarray:
    """Return a grayscale template image for template matching."""
    if path:
        img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"No se pudo leer template: {path}")
        return img
    # Generate from dictionary (id 0)
    marker_size = 240
    return cv2.aruco.generateImageMarker(dictionary, 0, marker_size)


def template_match_marker(gray: np.ndarray, template: np.ndarray,
                          scales: list[float], threshold: float) -> Optional[tuple]:
    """Return (max_val, top_left, size, rotation) if match >= threshold."""
    best = (0.0, None, None, None)
    # Normalize for robustness
    norm = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    for rot in [0, 1, 2, 3]:
        tmpl_rot = np.rot90(template, rot)
        for scale in scales:
            tmpl = cv2.resize(tmpl_rot, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
            if tmpl.shape[0] >= norm.shape[0] or tmpl.shape[1] >= norm.shape[1]:
                continue
            res = cv2.matchTemplate(norm, tmpl, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            if max_val > best[0]:
                best = (max_val, max_loc, tmpl.shape, rot)
    if best[0] >= threshold:
        return best
    return None


def bbox_corners(top_left: tuple, shape_hw: tuple, rotation: int) -> np.ndarray:
    """Return 4 corners (tl, tr, br, bl) from template match."""
    x, y = top_left
    h, w = shape_hw
    corners = np.array([
        [x, y],
        [x + w - 1, y],
        [x + w - 1, y + h - 1],
        [x, y + h - 1],
    ], dtype=np.float32)
    # rotation indicates how template was rotated to match; corners are still bbox in image
    return corners


def rotation_matrix_to_euler_xyz(R: np.ndarray) -> Tuple[float, float, float]:
    """Return roll, pitch, yaw from rotation matrix using XYZ convention."""
    sy = float(np.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0]))
    singular = sy < 1e-6
    if not singular:
        roll = float(np.arctan2(R[2, 1], R[2, 2]))
        pitch = float(np.arctan2(-R[2, 0], sy))
        yaw = float(np.arctan2(R[1, 0], R[0, 0]))
    else:
        roll = float(np.arctan2(-R[1, 2], R[1, 1]))
        pitch = float(np.arctan2(-R[2, 0], sy))
        yaw = 0.0
    return roll, pitch, yaw



def rpy_to_rotation_matrix(roll: float, pitch: float, yaw: float) -> np.ndarray:
    cr, sr = np.cos(roll), np.sin(roll)
    cp, sp = np.cos(pitch), np.sin(pitch)
    cy, sy = np.cos(yaw), np.sin(yaw)
    Rz = np.array([[cy, -sy, 0.0], [sy, cy, 0.0], [0.0, 0.0, 1.0]], dtype=np.float64)
    Ry = np.array([[cp, 0.0, sp], [0.0, 1.0, 0.0], [-sp, 0.0, cp]], dtype=np.float64)
    Rx = np.array([[1.0, 0.0, 0.0], [0.0, cr, -sr], [0.0, sr, cr]], dtype=np.float64)
    return Rz @ Ry @ Rx



def wrap_angle(angle: float) -> float:
    return (angle + np.pi) % (2 * np.pi) - np.pi


def build_detector(dictionary_name: str):
    if dictionary_name not in ARUCO_DICTS:
        raise ValueError(f"Diccionario ArUco no soportado: {dictionary_name}")
    dictionary = cv2.aruco.getPredefinedDictionary(ARUCO_DICTS[dictionary_name])
    parameters = cv2.aruco.DetectorParameters()
    if hasattr(cv2.aruco, "ArucoDetector"):
        detector = cv2.aruco.ArucoDetector(dictionary, parameters)
        return detector, dictionary
    return (dictionary, parameters), dictionary


def detect_markers(gray: np.ndarray, detector_obj):
    if isinstance(detector_obj, tuple):
        dictionary, parameters = detector_obj
        corners, ids, rejected = cv2.aruco.detectMarkers(gray, dictionary, parameters=parameters)
    else:
        corners, ids, rejected = detector_obj.detectMarkers(gray)
    return corners, ids, rejected


def choose_marker(corners, ids, target_id: Optional[int]):
    if ids is None or len(ids) == 0:
        return None, None
    ids_flat = ids.flatten().tolist()
    if target_id is None:
        idx = 0
    else:
        if target_id not in ids_flat:
            return None, None
        idx = ids_flat.index(target_id)
    return corners[idx], int(ids_flat[idx])


def reprojection_error(corner: np.ndarray, rvec: np.ndarray, tvec: np.ndarray,
                       camera_matrix: np.ndarray, dist_coeffs: np.ndarray,
                       marker_length: float) -> float:
    half = marker_length / 2.0
    obj_points = np.array([
        [-half,  half, 0.0],
        [ half,  half, 0.0],
        [ half, -half, 0.0],
        [-half, -half, 0.0],
    ], dtype=np.float32)
    img_points, _ = cv2.projectPoints(obj_points, rvec, tvec, camera_matrix, dist_coeffs)
    img_points = img_points.reshape(-1, 2)
    corner_points = corner.reshape(-1, 2)
    return float(np.mean(np.linalg.norm(corner_points - img_points, axis=1)))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Estima pose relativa con ArUco y genera CSV")
    parser.add_argument("--dataset-csv", required=True, help="Ruta a dataset.csv")
    parser.add_argument("--config", default="aruco_relative_pose/config.yaml", help="Ruta a config YAML")
    parser.add_argument("--output", default=None, help="CSV de salida")
    parser.add_argument("--start-index", type=int, default=0, help="Indice inicial (fila) del CSV")
    parser.add_argument("--max-frames", type=int, default=None, help="Maximo de frames a procesar")
    parser.add_argument("--stride", type=int, default=1, help="Procesa uno cada N frames")
    parser.add_argument("--viz-dir", default=None, help="Carpeta para guardar debug PNGs")
    parser.add_argument("--preprocess", default="none", choices=["none","normalize","clahe","adaptive"],
                        help="Preprocesado de imagen antes de detectar")
    parser.add_argument("--debug", action="store_true", help="Imprime info de debug")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    dataset_csv = Path(args.dataset_csv)
    if not dataset_csv.exists():
        raise SystemExit(f"No existe: {dataset_csv}")
    dataset_dir = dataset_csv.parent
    frames_dir = dataset_dir / "frames"
    if not frames_dir.exists():
        raise SystemExit(f"No existe carpeta de frames: {frames_dir}")

    cfg = load_config(Path(args.config))
    camera_cfg = cfg.get("camera", {})
    aruco_cfg = cfg.get("aruco", {})
    gt_cfg = cfg.get("gt", {}).get("columns", {})

    camera_matrix = np.array(camera_cfg.get("matrix", []), dtype=np.float64)
    if camera_matrix.shape != (3, 3):
        raise SystemExit("camera.matrix debe ser 3x3 en config.yaml")
    dist_coeffs = np.array(camera_cfg.get("dist_coeffs", [0, 0, 0, 0, 0]), dtype=np.float64).reshape(-1, 1)

    # Fixed camera pose in world (drone is fixed)
    cam_pose_cfg = camera_cfg.get("fixed_pose_world", {}) or {}
    cam_world = np.array([
    float(cam_pose_cfg.get("x", 0.0)),
    float(cam_pose_cfg.get("y", 0.0)),
    float(cam_pose_cfg.get("z", 2.0)),
    ], dtype=np.float64)
    cam_world_rpy = np.array([
    float(cam_pose_cfg.get("roll", 0.0)),
    float(cam_pose_cfg.get("pitch", 0.0)),
    float(cam_pose_cfg.get("yaw", 0.0)),
    ], dtype=np.float64)
    
    extr_cfg = camera_cfg.get("extrinsics", {}) or {}
    base_to_camlink_xyz = np.array(extr_cfg.get("base_to_camera_link_xyz", [0.0, 0.0, -0.055]), dtype=np.float64)
    base_to_camlink_rpy = np.array(extr_cfg.get("base_to_camera_link_rpy", [0.0, np.pi / 2.0, 0.0]), dtype=np.float64)
    camlink_to_opt_xyz = np.array(extr_cfg.get("camera_link_to_optical_xyz", [0.0, 0.0, 0.0]), dtype=np.float64)
    camlink_to_opt_rpy = np.array(extr_cfg.get("camera_link_to_optical_rpy", [-np.pi / 2.0, 0.0, -np.pi / 2.0]), dtype=np.float64)
    
    R_w_base = rpy_to_rotation_matrix(cam_world_rpy[0], cam_world_rpy[1], cam_world_rpy[2])
    R_base_camlink = rpy_to_rotation_matrix(base_to_camlink_rpy[0], base_to_camlink_rpy[1], base_to_camlink_rpy[2])
    R_camlink_opt = rpy_to_rotation_matrix(camlink_to_opt_rpy[0], camlink_to_opt_rpy[1], camlink_to_opt_rpy[2])
    
    R_w_camopt = R_w_base @ R_base_camlink @ R_camlink_opt
    t_w_camopt = cam_world + R_w_base @ base_to_camlink_xyz + (R_w_base @ R_base_camlink) @ camlink_to_opt_xyz
    R_cw = R_w_camopt.T
    
    marker_offset_xyz = np.array(aruco_cfg.get("marker_offset_xyz", [0.0, 0.0, 0.091]), dtype=np.float64)

    dictionary_name = aruco_cfg.get("dictionary", "DICT_4X4_50")
    marker_length = float(aruco_cfg.get("marker_length_m", 0.1))
    target_id = aruco_cfg.get("target_id", None)
    if target_id is not None:
        target_id = int(target_id)
    tm_cfg = aruco_cfg.get("template_match", {}) or {}
    tm_enabled = bool(tm_cfg.get("enabled", False))
    tm_threshold = float(tm_cfg.get("threshold", 0.38))
    tm_scales = tm_cfg.get("scales", [0.1, 0.12, 0.15, 0.18, 0.2, 0.25, 0.3, 0.35])
    tm_template_path = aruco_cfg.get("template_path", None)
    yaw_offset_rad = float(aruco_cfg.get("yaw_offset_rad", 0.0))
    bit_pattern_rows = aruco_cfg.get("bit_pattern", None)
    bit_one_is_white = bool(aruco_cfg.get("bit_one_is_white", True))
    quad_cfg = aruco_cfg.get("quad_detection", {}) or {}
    quad_enabled = bool(quad_cfg.get("enabled", True))
    quad_min_area_ratio = float(quad_cfg.get("min_area_ratio", 0.0005))


    custom_dict = None
    bits_from_cfg = None
    if bit_pattern_rows:
        bits_from_cfg = parse_bit_pattern(bit_pattern_rows)
        if args.debug:
            print(f"Bits 6x6 (config):\n{bits_from_cfg}")
    xacro_path = aruco_cfg.get("xacro_path", None)
    if xacro_path:
        xacro_path = Path(xacro_path)
        if not xacro_path.exists():
            raise SystemExit(f"No existe xacro_path: {xacro_path}")
        if bits_from_cfg is None:
            bits = parse_xacro_pattern(xacro_path)
            custom_dict = build_custom_dictionary(bits, dictionary_name)
        else:
            custom_dict = build_custom_dictionary(bits_from_cfg, dictionary_name)
        if args.debug:
            print(f"Usando diccionario personalizado desde {xacro_path}")
            if bits_from_cfg is None:
                print(f"Bits 6x6 (xacro):\\n{bits}")

    if bits_from_cfg is not None and custom_dict is None:
        custom_dict = build_custom_dictionary(bits_from_cfg, dictionary_name)

    if custom_dict is not None:
        detector_obj, dictionary = build_detector(dictionary_name)
        # Reemplaza el diccionario en el detector
        if isinstance(detector_obj, tuple):
            detector_obj = (custom_dict, detector_obj[1])
        else:
            detector_obj = cv2.aruco.ArucoDetector(custom_dict, cv2.aruco.DetectorParameters())
        dictionary = custom_dict
    else:
        detector_obj, dictionary = build_detector(dictionary_name)

    template_img = None
    if tm_enabled:
        template_img = load_template_image(Path(tm_template_path) if tm_template_path else None, dictionary)
        if args.debug:
            print(f"[debug] Template matching habilitado (thr={tm_threshold}, scales={tm_scales})")

    df = pd.read_csv(dataset_csv)
    if args.start_index > 0:
        df = df.iloc[args.start_index:]
    if args.stride > 1:
        df = df.iloc[::args.stride]
    if args.max_frames is not None:
        df = df.iloc[:args.max_frames]

    viz_dir = Path(args.viz_dir) if args.viz_dir else None
    if viz_dir:
        viz_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for _, row in df.iterrows():
        frame_rel = Path(str(row["frame_path"]))
        frame_path = frame_rel if frame_rel.is_absolute() else frames_dir / frame_rel
        record = {
            "timestamp": row.get("timestamp", np.nan),
            "frame_path": str(frame_rel),
            "detected": False,
            "marker_id": -1,
            "tvec_x": np.nan,
            "tvec_y": np.nan,
            "tvec_z": np.nan,
            "rvec_x": np.nan,
            "rvec_y": np.nan,
            "rvec_z": np.nan,
            "roll": np.nan,
            "pitch": np.nan,
            "yaw": np.nan,
            "reproj_error_px": np.nan,
            "n_markers": 0,
            "frame_missing": False,
            "detector": "none",
            "gt_cam_marker_x": np.nan,
            "gt_cam_marker_y": np.nan,
            "gt_cam_marker_z": np.nan,
            "gt_cam_marker_roll": np.nan,
            "gt_cam_marker_pitch": np.nan,
            "gt_cam_marker_yaw": np.nan,
            "roll_wrapped": np.nan,
            "pitch_wrapped": np.nan,
            "yaw_wrapped": np.nan,
            "gt_cam_marker_roll_wrapped": np.nan,
            "gt_cam_marker_pitch_wrapped": np.nan,
            "gt_cam_marker_yaw_wrapped": np.nan,
            "roll_err_rad": np.nan,
            "pitch_err_rad": np.nan,
            "yaw_err_rad": np.nan,
            "roll_err_deg": np.nan,
            "pitch_err_deg": np.nan,
            "yaw_err_deg": np.nan,
        }

        if not frame_path.exists():
            record["frame_missing"] = True
            results.append(record)
            continue

        img = cv2.imread(str(frame_path))
        if img is None:
            record["frame_missing"] = True
            results.append(record)
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = preprocess_gray(gray, args.preprocess)

        if args.debug:
            gmin, gmax = int(gray.min()), int(gray.max())
            gmean, gstd = float(gray.mean()), float(gray.std())
            print(f"[debug] {frame_path.name}: min={gmin} max={gmax} mean={gmean:.1f} std={gstd:.1f}")
        corners, ids, _ = detect_markers(gray, detector_obj)
        record["n_markers"] = 0 if ids is None else int(len(ids))

        corner, marker_id = choose_marker(corners, ids, target_id)

        # Fallback: template matching if no ArUco detection
        if corner is None and tm_enabled and template_img is not None:
            match = template_match_marker(gray, template_img, tm_scales, tm_threshold)
            if match:
                max_val, top_left, shape_hw, rot = match
                corner = bbox_corners(top_left, shape_hw, rot).reshape(1, 4, 2).astype(np.float32)
                marker_id = int(target_id) if target_id is not None else 0
                record["n_markers"] = 1
                record["detector"] = "template"
                if args.debug:
                    print(f"[debug] TM match {frame_path.name}: score={max_val:.3f} rot={rot} tl={top_left} size={shape_hw}")

        if corner is not None:
            if corner.shape == (4, 2):
                corner_in = corner.reshape(1, 4, 2)
            else:
                corner_in = corner
            rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(corner_in, marker_length, camera_matrix, dist_coeffs)
            rvec = rvecs[0].reshape(3, 1)
            tvec = tvecs[0].reshape(3, 1)
            R, _ = cv2.Rodrigues(rvec)
            roll, pitch, yaw = rotation_matrix_to_euler_xyz(R)
            yaw = wrap_angle(yaw + yaw_offset_rad)
            record["roll_wrapped"] = float(wrap_angle(roll))
            record["pitch_wrapped"] = float(wrap_angle(pitch))
            record["yaw_wrapped"] = float(wrap_angle(yaw))
            err = reprojection_error(corner_in[0], rvec, tvec, camera_matrix, dist_coeffs, marker_length)

            record.update({
                "detector": "aruco" if record.get("detector") == "none" else record.get("detector"),
                "detected": True,
                "marker_id": marker_id,
                "tvec_x": float(tvec[0, 0]),
                "tvec_y": float(tvec[1, 0]),
                "tvec_z": float(tvec[2, 0]),
                "rvec_x": float(rvec[0, 0]),
                "rvec_y": float(rvec[1, 0]),
                "rvec_z": float(rvec[2, 0]),
                "roll": roll,
                "pitch": pitch,
                "yaw": yaw,
                "reproj_error_px": err,
            })

            if viz_dir:
                corners_vis = [corner_in[0].reshape(1, 4, 2)]
                cv2.aruco.drawDetectedMarkers(img, corners_vis, np.array([[marker_id]], dtype=np.int32))
                cv2.drawFrameAxes(img, camera_matrix, dist_coeffs, rvec, tvec, marker_length * 0.5)
                out_path = viz_dir / Path(frame_rel).name
                cv2.imwrite(str(out_path), img)


        # Ground truth in camera frame (marker pose)
        try:
            gt_x = row.get(gt_cfg.get("x", ""), np.nan)
            gt_y = row.get(gt_cfg.get("y", ""), np.nan)
            gt_z = row.get(gt_cfg.get("z", ""), np.nan)
            gt_roll = row.get(gt_cfg.get("roll", ""), np.nan)
            gt_pitch = row.get(gt_cfg.get("pitch", ""), np.nan)
            gt_yaw = row.get(gt_cfg.get("yaw", ""), np.nan)

            if (not np.isnan(gt_x) and not np.isnan(gt_y) and not np.isnan(gt_z) and
                not np.isnan(gt_roll) and not np.isnan(gt_pitch) and not np.isnan(gt_yaw)):
                t_w_trunk = np.array([gt_x, gt_y, gt_z], dtype=np.float64)
                R_w_trunk = rpy_to_rotation_matrix(gt_roll, gt_pitch, gt_yaw)
                t_w_marker = t_w_trunk + R_w_trunk @ marker_offset_xyz
                R_w_marker = R_w_trunk

                t_c_marker = R_cw @ (t_w_marker - t_w_camopt)
                R_c_marker = R_cw @ R_w_marker
                r_c_roll, r_c_pitch, r_c_yaw = rotation_matrix_to_euler_xyz(R_c_marker)

                record["gt_cam_marker_x"] = float(t_c_marker[0])
                record["gt_cam_marker_y"] = float(t_c_marker[1])
                record["gt_cam_marker_z"] = float(t_c_marker[2])
                record["gt_cam_marker_roll"] = float(wrap_angle(r_c_roll))
                record["gt_cam_marker_pitch"] = float(wrap_angle(r_c_pitch))
                record["gt_cam_marker_yaw"] = float(wrap_angle(r_c_yaw))
                record["gt_cam_marker_roll_wrapped"] = float(wrap_angle(r_c_roll))
                record["gt_cam_marker_pitch_wrapped"] = float(wrap_angle(r_c_pitch))
                record["gt_cam_marker_yaw_wrapped"] = float(wrap_angle(r_c_yaw))

                # Error envuelto entre estimado y GT (solo si hay estimado)
                if not np.isnan(record["roll_wrapped"]):
                    record["roll_err_rad"] = float(wrap_angle(record["roll_wrapped"] - record["gt_cam_marker_roll_wrapped"]))
                    record["pitch_err_rad"] = float(wrap_angle(record["pitch_wrapped"] - record["gt_cam_marker_pitch_wrapped"]))
                    record["yaw_err_rad"] = float(wrap_angle(record["yaw_wrapped"] - record["gt_cam_marker_yaw_wrapped"]))
                    record["roll_err_deg"] = float(np.degrees(record["roll_err_rad"]))
                    record["pitch_err_deg"] = float(np.degrees(record["pitch_err_rad"]))
                    record["yaw_err_deg"] = float(np.degrees(record["yaw_err_rad"]))
        except Exception:
            pass

        # Ground truth columns
        if gt_cfg:
            record["gt_x"] = row.get(gt_cfg.get("x", ""), np.nan)
            record["gt_y"] = row.get(gt_cfg.get("y", ""), np.nan)
            record["gt_z"] = row.get(gt_cfg.get("z", ""), np.nan)
            record["gt_roll"] = row.get(gt_cfg.get("roll", ""), np.nan)
            record["gt_pitch"] = row.get(gt_cfg.get("pitch", ""), np.nan)
            record["gt_yaw"] = row.get(gt_cfg.get("yaw", ""), np.nan)

        results.append(record)

    out_path = Path(args.output) if args.output else None
    if out_path is None:
        base = dataset_dir.name
        out_path = Path("aruco_relative_pose/outputs") / f"{base}_aruco_pose.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    out_df = pd.DataFrame(results)
    out_df.to_csv(out_path, index=False)
    if args.debug:
        detected_count = int(out_df["detected"].sum()) if "detected" in out_df else 0
        print(f"[debug] Detectados: {detected_count}/{len(out_df)}")
        if detected_count == 0:
            print("[debug] No se detectaron marcadores. Posibles causas: ")
            print("  - El patron no coincide con un diccionario ArUco estandar")
            print("  - El marcador no es visible en los frames o es demasiado pequeno")
            print("  - Bajo contraste/iluminacion")
    print(f"OK: {out_path} ({len(out_df)} filas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
