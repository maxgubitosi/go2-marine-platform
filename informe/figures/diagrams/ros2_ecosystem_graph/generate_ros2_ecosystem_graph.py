#!/usr/bin/env python3
"""Generate separate ROS 2 and TF2 thesis diagrams as pure SVG/PDF/PNG."""
from __future__ import annotations

import argparse
import html
import shutil
import subprocess
from pathlib import Path


COLORS = {
    "sim": "#d97706",
    "gazebo": "#475569",
    "camera": "#0f766e",
    "aruco": "#1d4ed8",
    "rosbag": "#7c3aed",
    "robot": "#64748b",
    "marker": "#b45309",
    "ink": "#0f172a",
    "muted": "#475569",
    "soft": "#dbe4ef",
    "panel": "#f8fafc",
    "white": "#ffffff",
}


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def _tint(color: str, mix: float = 0.86) -> str:
    r, g, b = _hex_to_rgb(color)
    tinted = (
        round(255 * mix + r * (1.0 - mix)),
        round(255 * mix + g * (1.0 - mix)),
        round(255 * mix + b * (1.0 - mix)),
    )
    return _rgb_to_hex(tinted)


def _arrow_marker(marker_id: str, color: str) -> str:
    return (
        f'<marker id="{marker_id}" markerWidth="12" markerHeight="12" refX="10" refY="6" '
        'orient="auto" markerUnits="strokeWidth">'
        f'<path d="M0,0 L12,6 L0,12 z" fill="{color}"/>'
        "</marker>"
    )


def _svg_header(width: int, height: int, title: str, desc: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f"<title id=\"title\">{html.escape(title)}</title>",
        f"<desc id=\"desc\">{html.escape(desc)}</desc>",
        "<defs>",
        "<style>",
        ".node-title { font-family: Arial, Helvetica, sans-serif; font-weight: 700; font-size: 24px; fill: #0f172a; }",
        ".node-body { font-family: Arial, Helvetica, sans-serif; font-size: 18px; fill: #475569; }",
        ".frame-text { font-family: Arial, Helvetica, sans-serif; font-weight: 700; font-size: 20px; fill: #0f172a; }",
        ".label { font-family: Arial, Helvetica, sans-serif; font-size: 15px; font-weight: 600; fill: #0f172a; }",
        ".note { font-family: Arial, Helvetica, sans-serif; font-size: 15px; fill: #475569; }",
        "</style>",
        _arrow_marker("arrow-sim", COLORS["sim"]),
        _arrow_marker("arrow-gazebo", COLORS["gazebo"]),
        _arrow_marker("arrow-camera", COLORS["camera"]),
        _arrow_marker("arrow-aruco", COLORS["aruco"]),
        _arrow_marker("arrow-robot", COLORS["robot"]),
        _arrow_marker("arrow-marker", COLORS["marker"]),
        "</defs>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{COLORS["white"]}"/>',
    ]


def _rounded_rect(
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    fill: str,
    stroke: str,
    stroke_width: float = 3.0,
    radius: float = 24.0,
) -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
        f'rx="{radius}" ry="{radius}" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="{stroke_width}"/>'
    )


def _text(
    x: float,
    y: float,
    content: str,
    *,
    klass: str,
    anchor: str = "start",
) -> str:
    return (
        f'<text x="{x}" y="{y}" class="{klass}" text-anchor="{anchor}">'
        f"{html.escape(content)}</text>"
    )


def _multiline_text(
    x: float,
    y: float,
    lines: list[str],
    *,
    klass: str,
    line_gap: float,
    anchor: str = "start",
) -> list[str]:
    return [
        _text(x, y + idx * line_gap, line, klass=klass, anchor=anchor)
        for idx, line in enumerate(lines)
    ]


def _node(
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    title_lines: list[str],
    body_lines: list[str],
    color: str,
) -> list[str]:
    elements = [
        _rounded_rect(x, y, width, height, fill=_tint(color), stroke=color),
        f'<rect x="{x}" y="{y}" width="{width}" height="18" fill="{color}" rx="24" ry="24"/>',
    ]
    elements.extend(
        _multiline_text(
            x + 18.0,
            y + 52.0,
            title_lines,
            klass="node-title",
            line_gap=28.0,
        )
    )
    elements.extend(
        _multiline_text(
            x + 18.0,
            y + 78.0 + (len(title_lines) - 1) * 18.0,
            body_lines,
            klass="node-body",
            line_gap=24.0,
        )
    )
    return elements


def _frame_node(x: float, y: float, width: float, label: str, color: str) -> list[str]:
    return [
        _rounded_rect(
            x,
            y,
            width,
            54.0,
            fill=_tint(color, mix=0.90),
            stroke=color,
            stroke_width=2.2,
            radius=16.0,
        ),
        _text(x + width / 2.0, y + 34.0, label, klass="frame-text", anchor="middle"),
    ]


def _arrow(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    color: str,
    marker_id: str,
    dashed: bool = False,
) -> str:
    dash = ' stroke-dasharray="12 10"' if dashed else ""
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
        f'stroke-width="4" stroke-linecap="round" marker-end="url(#{marker_id})"{dash}/>'
    )


def _label(x: float, y: float, lines: list[str]) -> list[str]:
    return _multiline_text(x, y, lines, klass="label", line_gap=18.0, anchor="middle")


def build_ros2_svg() -> str:
    width = 1700
    height = 430
    parts = _svg_header(
        width,
        height,
        "ROS 2 graph for the fixed-camera simulation pipeline",
        "Simplified ROS 2 graph with nodes, topics, and rosbag recording for the fixed-camera scenario.",
    )

    parts.extend(
        _node(
            40.0,
            120.0,
            270.0,
            170.0,
            title_lines=["marine_platform", "simulator"],
            body_lines=[
                "Genera la consigna postural",
                "de roll, pitch y heave.",
            ],
            color=COLORS["sim"],
        )
    )
    parts.extend(
        _node(
            360.0,
            110.0,
            310.0,
            185.0,
            title_lines=["Gazebo + Go2"],
            body_lines=[
                "Integra la dinamica del robot,",
                "el render visual y el estado:",
                "/odom, /imu/data y postura base.",
            ],
            color=COLORS["gazebo"],
        )
    )
    parts.extend(
        _node(
            740.0,
            70.0,
            290.0,
            180.0,
            title_lines=["fixed_camera"],
            body_lines=[
                "Publica la imagen RGB y",
                "los intrinsecos de camara.",
                "Pose fija en world.",
            ],
            color=COLORS["camera"],
        )
    )
    parts.extend(
        _node(
            1090.0,
            70.0,
            280.0,
            180.0,
            title_lines=["aruco_detector"],
            body_lines=[
                "Consume los datos de camara",
                "y estima la pose del marcador",
                "en el frame optico.",
            ],
            color=COLORS["aruco"],
        )
    )
    parts.extend(
        _node(
            1425.0,
            115.0,
            225.0,
            240.0,
            title_lines=["rosbag2", "recorder"],
            body_lines=[
                "Registro persistente para",
                "replay y evaluacion offline.",
                "",
                "Senales:",
                "- /aruco/pose",
                "- /odom",
                "- /imu/data",
                "- /base_to_footprint_pose",
            ],
            color=COLORS["rosbag"],
        )
    )

    parts.extend(
        [
            _arrow(312.0, 205.0, 352.0, 205.0, color=COLORS["sim"], marker_id="arrow-sim"),
            _arrow(672.0, 198.0, 735.0, 155.0, color=COLORS["gazebo"], marker_id="arrow-gazebo", dashed=True),
            _arrow(1032.0, 160.0, 1082.0, 160.0, color=COLORS["camera"], marker_id="arrow-camera"),
            _arrow(1372.0, 196.0, 1417.0, 210.0, color=COLORS["aruco"], marker_id="arrow-aruco"),
            _arrow(672.0, 318.0, 1418.0, 318.0, color=COLORS["gazebo"], marker_id="arrow-gazebo"),
        ]
    )

    for x, y, lines in (
        (332.0, 96.0, ["/body_pose"]),
        (708.0, 54.0, ["escena renderizada", "y sensor en Gazebo"]),
        (1060.0, 30.0, ["/fixed_camera/camera/image_raw", "/fixed_camera/camera/camera_info"]),
        (1378.0, 250.0, ["/aruco/pose"]),
        (1045.0, 386.0, ["/odom, /imu/data,", "/base_to_footprint_pose"]),
    ):
        parts.extend(_label(x, y, lines))

    parts.append("</svg>")
    return "\n".join(parts)


def build_tf2_svg() -> str:
    width = 1350
    height = 620
    parts = _svg_header(
        width,
        height,
        "TF2 frames for robot, marker, and camera",
        "Simplified TF2 frame chain linking world, robot frames, camera frames, and the ArUco marker.",
    )

    parts.extend(
        _frame_node(575.0, 48.0, 200.0, "world", COLORS["robot"])
    )

    parts.extend(_frame_node(210.0, 178.0, 220.0, "odom", COLORS["robot"]))
    parts.extend(_frame_node(210.0, 290.0, 220.0, "base_footprint", COLORS["robot"]))
    parts.extend(_frame_node(210.0, 402.0, 220.0, "base_link", COLORS["robot"]))
    parts.extend(_frame_node(210.0, 514.0, 220.0, "aruco_marker", COLORS["marker"]))

    parts.extend(_frame_node(910.0, 178.0, 260.0, "camera_base_link", COLORS["camera"]))
    parts.extend(_frame_node(910.0, 290.0, 220.0, "camera_link", COLORS["camera"]))
    parts.extend(_frame_node(910.0, 402.0, 290.0, "camera_link_optical", COLORS["camera"]))

    parts.extend(
        [
            _arrow(675.0, 102.0, 320.0, 176.0, color=COLORS["robot"], marker_id="arrow-robot"),
            _arrow(675.0, 102.0, 1040.0, 176.0, color=COLORS["camera"], marker_id="arrow-camera"),
            _arrow(320.0, 232.0, 320.0, 288.0, color=COLORS["robot"], marker_id="arrow-robot"),
            _arrow(320.0, 344.0, 320.0, 400.0, color=COLORS["robot"], marker_id="arrow-robot"),
            _arrow(320.0, 456.0, 320.0, 512.0, color=COLORS["marker"], marker_id="arrow-marker"),
            _arrow(1040.0, 232.0, 1040.0, 288.0, color=COLORS["camera"], marker_id="arrow-camera"),
            _arrow(1040.0, 344.0, 1040.0, 400.0, color=COLORS["camera"], marker_id="arrow-camera"),
            _arrow(1040.0, 456.0, 430.0, 540.0, color=COLORS["aruco"], marker_id="arrow-aruco", dashed=True),
        ]
    )

    for x, y, lines in (
        (760.0, 462.0, ["/aruco/pose"]),
    ):
        parts.extend(_label(x, y, lines))

    parts.append("</svg>")
    return "\n".join(parts)


def _convert_with_sips(svg_path: Path, out_path: Path, fmt: str) -> bool:
    sips = shutil.which("sips")
    if sips is None:
        return False
    try:
        subprocess.run(
            [sips, "-s", "format", fmt, str(svg_path), "--out", str(out_path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def _write_outputs(svg_text: str, stem: Path) -> None:
    svg_path = stem.with_suffix(".svg")
    pdf_path = stem.with_suffix(".pdf")
    png_path = stem.with_suffix(".png")

    svg_path.write_text(svg_text, encoding="utf-8")
    print(f"Saved {svg_path}")

    if _convert_with_sips(svg_path, pdf_path, "pdf"):
        print(f"Saved {pdf_path}")
    else:
        print(f"Could not convert {svg_path.name} to PDF.")

    if _convert_with_sips(svg_path, png_path, "png"):
        print(f"Saved {png_path}")
    else:
        print(f"Could not convert {svg_path.name} to PNG.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("informe/figures/diagrams/ros2_ecosystem_graph"),
    )
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    _write_outputs(build_ros2_svg(), args.out_dir / "ros2_graph")
    _write_outputs(build_tf2_svg(), args.out_dir / "tf2_frames_graph")


if __name__ == "__main__":
    main()
