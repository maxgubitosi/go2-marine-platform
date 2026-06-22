#!/usr/bin/env python3
"""Crop lab ArUco realtime panels to a common frame anchored on the marker."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
IMAGE_DIR = ROOT / "figures" / "images"
NAMES = [
    "lab_aruco_realtime_t00",
    "lab_aruco_realtime_t26",
    "lab_aruco_realtime_t49",
]
TARGET_SIZE = (720, 432)
TARGET_ASPECT = TARGET_SIZE[0] / TARGET_SIZE[1]
MARKER_CENTER = (0.47, 0.49)
ROBOT_PAD = {
    "left": 2.75,
    "right": 1.45,
    "top": 1.25,
    "bottom": 1.95,
}


def find_green_bbox(img: Image.Image) -> tuple[int, int, int, int]:
    pixels = img.load()
    width, height = img.size
    xs: list[int] = []
    ys: list[int] = []
    for y in range(height):
        for x in range(width):
            red, green, blue = pixels[x, y][:3]
            if (
                green > 140
                and red < 110
                and blue < 110
                and green > red + 25
                and green > blue + 25
            ):
                xs.append(x)
                ys.append(y)
    if not xs:
        raise RuntimeError("No ArUco overlay detected")
    return min(xs), min(ys), max(xs), max(ys)


def fit_box(
    img_w: int,
    img_h: int,
    cx: float,
    cy: float,
    ms: float,
    pads: dict[str, float],
) -> tuple[float, float, float, float]:
    left = cx - ms * pads["left"]
    right = cx + ms * pads["right"]
    top = cy - ms * pads["top"]
    bottom = cy + ms * pads["bottom"]

    width = right - left
    height = bottom - top
    aspect = width / height
    if aspect > TARGET_ASPECT:
        new_h = width / TARGET_ASPECT
        delta = (new_h - height) / 2
        top -= delta
        bottom += delta
    else:
        new_w = height * TARGET_ASPECT
        delta = (new_w - width) / 2
        left -= delta
        right += delta

    width = right - left
    height = bottom - top
    rel_x = MARKER_CENTER[0] * width
    rel_y = MARKER_CENTER[1] * height
    left += (cx - left) - rel_x
    top += (cy - top) - rel_y
    right = left + width
    bottom = top + height

    if left < 0:
        right -= left
        left = 0
    if top < 0:
        bottom -= top
        top = 0
    if right > img_w:
        shift = right - img_w
        left -= shift
        right -= shift
    if bottom > img_h:
        shift = bottom - img_h
        top -= shift
        bottom -= shift

    left = max(0.0, left)
    top = max(0.0, top)
    right = min(float(img_w), right)
    bottom = min(float(img_h), bottom)
    return left, top, right, bottom


def crop_panel(img: Image.Image) -> Image.Image:
    img_w, img_h = img.size
    x0, y0, x1, y1 = find_green_bbox(img)
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    ms = max(x1 - x0, y1 - y0)

    pads = dict(ROBOT_PAD)
    for _ in range(12):
        left, top, right, bottom = fit_box(img_w, img_h, cx, cy, ms, pads)
        width = right - left
        height = bottom - top
        if width <= 0 or height <= 0:
            break
        current_aspect = width / height
        if abs(current_aspect - TARGET_ASPECT) < 0.01:
            break
        scale = min(
            (cx - left) / (pads["left"] * ms),
            (right - cx) / (pads["right"] * ms),
            (cy - top) / (pads["top"] * ms),
            (bottom - cy) / (pads["bottom"] * ms),
            1.0,
        )
        if scale >= 0.99:
            break
        for key in pads:
            pads[key] *= scale

    cropped = img.crop((int(left), int(top), int(right), int(bottom)))
    return cropped.resize(TARGET_SIZE, Image.Resampling.LANCZOS)


def main() -> None:
    for name in NAMES:
        src = IMAGE_DIR / f"{name}.png"
        backup = IMAGE_DIR / f"{name}.orig.png"
        if not backup.exists():
            Image.open(src).save(backup)
        source = backup if backup.exists() else src
        out = crop_panel(Image.open(source).convert("RGB"))
        out.save(src)
        print(f"Wrote {src} ({out.size[0]}x{out.size[1]})")


if __name__ == "__main__":
    main()
