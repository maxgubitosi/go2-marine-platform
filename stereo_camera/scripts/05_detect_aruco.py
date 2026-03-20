#!/usr/bin/env python3
"""
05_detect_aruco.py — Detección ArUco en vivo con estimación de pose.

Controles:
    Q  → salir
    C  → capturar frame
"""
import math
import sys
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR.parent / "config.yaml"

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


def euler_from_rvec(rvec):
    R, _ = cv2.Rodrigues(rvec)
    sy = math.sqrt(R[0, 0]**2 + R[1, 0]**2)
    if sy > 1e-6:
        roll = math.atan2(R[2, 1], R[2, 2])
        pitch = math.atan2(-R[2, 0], sy)
        yaw = math.atan2(R[1, 0], R[0, 0])
    else:
        roll = math.atan2(-R[1, 2], R[1, 1])
        pitch = math.atan2(-R[2, 0], sy)
        yaw = 0.0
    return math.degrees(roll), math.degrees(pitch), math.degrees(yaw)


def crop_eye(frame, eye, eye_w):
    return frame[:, :eye_w].copy() if eye == "left" else frame[:, eye_w:].copy()


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def main() -> None:
    cfg = load_config()
    cam = cfg["camera"]
    intr = cfg["intrinsics"]
    aruco_cfg = cfg["aruco"]

    if intr["matrix"] is None or intr["dist_coeffs"] is None:
        print("ERROR: No hay calibración. Ejecutar: python3 scripts/03_calibrate.py")
        sys.exit(1)

    K = np.array(intr["matrix"], dtype=np.float64)
    D = np.array(intr["dist_coeffs"], dtype=np.float64)
    model = intr.get("distortion_model", "pinhole")
    is_fisheye = model == "fisheye"

    dict_name = aruco_cfg["dictionary"]
    target_id = aruco_cfg["target_id"]
    marker_len = aruco_cfg["marker_length_m"]

    dictionary = cv2.aruco.getPredefinedDictionary(ARUCO_DICTS[dict_name])
    detector = cv2.aruco.ArucoDetector(dictionary, cv2.aruco.DetectorParameters())

    print(f"═══ Detección ArUco ═══")
    print(f"  Cámara: {cam['device']} | Lente: {cam['selected_eye'].upper()}")
    print(f"  ArUco: {dict_name} ID {target_id} | lado={marker_len}m")
    print(f"  Controles: Q=salir, C=capturar")

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

    # Pre-calcular mapas de undistort para fisheye
    if is_fisheye:
        D_fish = D.flatten()[:4].reshape(4, 1)
        new_K = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(
            K, D_fish, (eye_w, eye_h), np.eye(3), balance=0.0,
        )
        map1, map2 = cv2.fisheye.initUndistortRectifyMap(
            K, D_fish, np.eye(3), new_K, (eye_w, eye_h), cv2.CV_16SC2,
        )

    output_dir = SCRIPT_DIR.parent / "calibration" / "detections"
    output_dir.mkdir(parents=True, exist_ok=True)

    det_count = 0
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        eye_img = crop_eye(frame, cam["selected_eye"], eye_w)

        # Para fisheye: undistort primero, luego detectar con new_K y dist=0
        if is_fisheye:
            eye_img = cv2.remap(eye_img, map1, map2, cv2.INTER_LINEAR)
            cam_K = new_K
            cam_D = np.zeros(5)
        else:
            cam_K = K
            cam_D = D

        gray = cv2.cvtColor(eye_img, cv2.COLOR_BGR2GRAY)
        display = eye_img.copy()

        corners, ids, _ = detector.detectMarkers(gray)

        tvec_str = euler_str = dist_str = ""
        detected = False

        if ids is not None and len(ids) > 0:
            cv2.aruco.drawDetectedMarkers(display, corners, ids)
            ids_flat = ids.flatten().tolist()
            if target_id in ids_flat:
                idx = ids_flat.index(target_id)
                # Puntos 3D del marcador centrado en su origen
                half = marker_len / 2.0
                obj_pts = np.array([
                    [-half,  half, 0],
                    [ half,  half, 0],
                    [ half, -half, 0],
                    [-half, -half, 0],
                ], dtype=np.float32)
                img_pts = corners[idx].reshape(4, 2)
                _, rvec, tvec = cv2.solvePnP(obj_pts, img_pts, cam_K, cam_D)
                cv2.drawFrameAxes(display, cam_K, cam_D, rvec, tvec, marker_len * 0.5)

                roll, pitch, yaw = euler_from_rvec(rvec)
                distance = np.linalg.norm(tvec)
                tvec_str = f"tvec: [{tvec[0,0]:.3f}, {tvec[1,0]:.3f}, {tvec[2,0]:.3f}] m"
                euler_str = f"RPY: [{roll:.1f}, {pitch:.1f}, {yaw:.1f}] deg"
                dist_str = f"Dist: {distance:.3f} m"
                detected = True
                det_count += 1

        # HUD
        overlay = display.copy()
        cv2.rectangle(overlay, (0, 0), (500, 150), (0, 0, 0), -1)
        display = cv2.addWeighted(overlay, 0.5, display, 0.5, 0)

        color = (0, 255, 0) if detected else (0, 0, 255)
        status = "DETECTADO" if detected else "Buscando..."
        cv2.putText(display, f"ArUco ID {target_id}: {status}", (10, 25),
                     cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        if detected:
            cv2.putText(display, tvec_str, (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            cv2.putText(display, euler_str, (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            cv2.putText(display, dist_str, (10, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        if frame_count > 0:
            rate = det_count / frame_count * 100
            cv2.putText(display, f"Rate: {rate:.0f}%", (10, 135),
                         cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        scale = min(1.0, 1280.0 / eye_w)
        if scale < 1.0:
            disp = cv2.resize(display, (int(eye_w * scale), int(eye_h * scale)))
        else:
            disp = display
        cv2.imshow("ArUco Detection", disp)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("c"):
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            cv2.imwrite(str(output_dir / f"detect_{ts}.png"), display)
            print(f"  Capturado: detect_{ts}.png")

    cap.release()
    cv2.destroyAllWindows()
    print(f"\n═══ Resumen ═══")
    print(f"  Frames: {frame_count} | Detecciones: {det_count}")
    if frame_count > 0:
        print(f"  Tasa: {det_count/frame_count*100:.1f}%")


if __name__ == "__main__":
    main()
