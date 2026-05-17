#!/usr/bin/env python3
"""Generate the platform corner-height diagram as pure SVG/PDF/PNG."""
from __future__ import annotations

import html
import shutil
import subprocess
from pathlib import Path


WIDTH = 1600
HEIGHT = 760
VIEWBOX_Y = 110

COLORS = {
    "ink": "#0f172a",
    "muted": "#475569",
    "deck": "#f1f5f9",
    "deck_edge": "#334155",
    "hull": "#94a3b8",
    "hull_dark": "#64748b",
    "water": "#d9f4ff",
    "water_line": "#0284c7",
    "water_soft": "#7dd3fc",
    "sample": "#111827",
    "height": "#0ea5e9",
    "heave": "#dc2626",
    "pitch": "#d97706",
    "roll": "#0f766e",
    "white": "#ffffff",
}


def _arrow_marker(marker_id: str, color: str) -> str:
    return (
        f'<marker id="{marker_id}" markerWidth="12" markerHeight="12" '
        'refX="10" refY="6" orient="auto" markerUnits="strokeWidth">'
        f'<path d="M0,0 L12,6 L0,12 z" fill="{color}"/>'
        "</marker>"
    )


def _dot_marker(marker_id: str, color: str) -> str:
    return (
        f'<marker id="{marker_id}" markerWidth="8" markerHeight="8" '
        'refX="4" refY="4" orient="auto" markerUnits="strokeWidth">'
        f'<circle cx="4" cy="4" r="3.2" fill="{color}"/>'
        "</marker>"
    )


def _svg_header() -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 {VIEWBOX_Y} {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">',
        '<title id="title">Platform corner heights under wave excitation</title>',
        (
            '<desc id="desc">Perspective diagram of a floating platform over a wavy '
            'water surface, with four sampled deck zones and local water heights.</desc>'
        ),
        "<defs>",
        "<style>",
        ".label { font-family: Arial, Helvetica, sans-serif; font-size: 30px; font-weight: 700; fill: #0f172a; }",
        ".motion { font-family: Arial, Helvetica, sans-serif; font-size: 30px; font-weight: 700; }",
        ".small { font-family: Arial, Helvetica, sans-serif; font-size: 22px; font-weight: 600; fill: #475569; }",
        "</style>",
        '<linearGradient id="waterGradient" x1="0" y1="0" x2="0" y2="1">',
        f'<stop offset="0%" stop-color="{COLORS["water"]}" stop-opacity="0.96"/>',
        f'<stop offset="100%" stop-color="{COLORS["water_soft"]}" stop-opacity="0.40"/>',
        "</linearGradient>",
        '<filter id="softShadow" x="-20%" y="-20%" width="140%" height="160%">',
        '<feDropShadow dx="0" dy="18" stdDeviation="18" flood-color="#0f172a" flood-opacity="0.13"/>',
        "</filter>",
        _arrow_marker("arrow-heave", COLORS["heave"]),
        _arrow_marker("arrow-pitch", COLORS["pitch"]),
        _arrow_marker("arrow-roll", COLORS["roll"]),
        _dot_marker("dot-height", COLORS["height"]),
        "</defs>",
        f'<rect x="0" y="{VIEWBOX_Y}" width="{WIDTH}" height="{HEIGHT}" fill="{COLORS["white"]}"/>',
    ]


def _path(d: str, *, fill: str = "none", stroke: str = "none", stroke_width: float = 1.0, **attrs: str) -> str:
    attr_text = " ".join(f'{key.replace("_", "-")}="{html.escape(str(value))}"' for key, value in attrs.items())
    if attr_text:
        attr_text = " " + attr_text
    return (
        f'<path d="{d}" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="{stroke_width}"{attr_text}/>'
    )


def _polygon(points: list[tuple[float, float]], *, fill: str, stroke: str, stroke_width: float = 2.5, **attrs: str) -> str:
    point_text = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    attr_text = " ".join(f'{key.replace("_", "-")}="{html.escape(str(value))}"' for key, value in attrs.items())
    if attr_text:
        attr_text = " " + attr_text
    return (
        f'<polygon points="{point_text}" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="{stroke_width}" stroke-linejoin="round"{attr_text}/>'
    )


def _line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    color: str,
    width: float = 2.0,
    opacity: float = 1.0,
    dashed: bool = False,
) -> str:
    dash = ' stroke-dasharray="12 9"' if dashed else ""
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{color}" stroke-width="{width}" stroke-linecap="round" '
        f'opacity="{opacity}"{dash}/>'
    )


def _circle(x: float, y: float, r: float, *, fill: str, stroke: str = "none", stroke_width: float = 1.0, opacity: float = 1.0) -> str:
    return (
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="{stroke_width}" opacity="{opacity}"/>'
    )


def _text(x: float, y: float, content: str, *, klass: str = "label", fill: str | None = None, anchor: str = "middle") -> str:
    fill_attr = f' fill="{fill}"' if fill else ""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" class="{klass}" text-anchor="{anchor}"{fill_attr}>'
        f"{html.escape(content)}</text>"
    )


def build_svg() -> str:
    parts = _svg_header()

    water_surface = (
        "M70,666 C210,596 324,604 438,656 "
        "C565,724 667,628 756,563 "
        "C842,500 924,552 1003,492 "
        "C1085,430 1187,498 1275,555 "
        "C1372,618 1462,559 1534,506 "
        "L1552,835 L48,835 Z"
    )
    parts.append(_path(water_surface, fill="url(#waterGradient)", stroke=COLORS["water_line"], stroke_width=3.2))

    wave_paths = [
        "M95,706 C245,630 363,719 515,646 C650,582 746,646 862,584 C988,516 1111,603 1234,662 C1370,727 1452,638 1520,590",
        "M140,760 C288,695 409,771 552,704 C682,644 797,702 910,645 C1044,579 1150,666 1284,716 C1398,759 1486,696 1534,652",
        "M218,610 C334,552 452,618 574,566 C701,510 787,576 894,528 C1028,468 1150,544 1270,603 C1385,660 1468,606 1532,560",
        "M340,805 C455,753 566,812 704,760 C832,711 934,768 1064,716 C1197,663 1315,743 1450,782",
    ]
    for d in wave_paths:
        parts.append(_path(d, stroke=COLORS["water_soft"], stroke_width=3.0, opacity="0.72"))

    deck = {
        "stern_port": (560.0, 420.0),
        "bow_port": (998.0, 282.0),
        "bow_starboard": (1215.0, 405.0),
        "stern_starboard": (760.0, 575.0),
    }
    offset = (22.0, 46.0)
    stern_port_b = (deck["stern_port"][0] + offset[0], deck["stern_port"][1] + offset[1])
    stern_starboard_b = (deck["stern_starboard"][0] + offset[0], deck["stern_starboard"][1] + offset[1])
    bow_port_b = (deck["bow_port"][0] + offset[0], deck["bow_port"][1] + offset[1])
    bow_starboard_b = (deck["bow_starboard"][0] + offset[0], deck["bow_starboard"][1] + offset[1])

    parts.append('<g filter="url(#softShadow)">')
    parts.append(
        _polygon(
            [deck["bow_starboard"], deck["stern_starboard"], stern_starboard_b, bow_starboard_b],
            fill=COLORS["hull_dark"],
            stroke=COLORS["deck_edge"],
            stroke_width=2.1,
        )
    )
    parts.append(
        _polygon(
            [deck["stern_port"], deck["stern_starboard"], stern_starboard_b, stern_port_b],
            fill=COLORS["hull"],
            stroke=COLORS["deck_edge"],
            stroke_width=2.1,
        )
    )
    parts.append(
        _polygon(
            [deck["stern_port"], deck["bow_port"], deck["bow_starboard"], deck["stern_starboard"]],
            fill=COLORS["deck"],
            stroke=COLORS["deck_edge"],
            stroke_width=3.6,
        )
    )
    parts.append("</g>")

    proa = ((deck["bow_port"][0] + deck["bow_starboard"][0]) / 2, (deck["bow_port"][1] + deck["bow_starboard"][1]) / 2)
    popa = ((deck["stern_port"][0] + deck["stern_starboard"][0]) / 2, (deck["stern_port"][1] + deck["stern_starboard"][1]) / 2)
    babor = ((deck["stern_port"][0] + deck["bow_port"][0]) / 2, (deck["stern_port"][1] + deck["bow_port"][1]) / 2)
    estribor = ((deck["stern_starboard"][0] + deck["bow_starboard"][0]) / 2, (deck["stern_starboard"][1] + deck["bow_starboard"][1]) / 2)

    parts.extend(
        [
            _line(popa[0], popa[1], proa[0], proa[1], color="#94a3b8", width=2.0, opacity=0.82, dashed=True),
            _line(babor[0], babor[1], estribor[0], estribor[1], color="#94a3b8", width=2.0, opacity=0.82, dashed=True),
        ]
    )

    samples = [
        ("proa", proa, (proa[0], 524.0), (1248.0, 302.0), "start"),
        ("popa", popa, (popa[0], 642.0), (628.0, 530.0), "end"),
        ("babor", babor, (babor[0], 592.0), (735.0, 342.0), "end"),
        ("estribor", estribor, (estribor[0], 538.0), (1020.0, 528.0), "start"),
    ]

    for _name, deck_pt, water_pt, _label_pos, _anchor in samples:
        x, y = deck_pt
        wx, wy = water_pt
        parts.append(_line(x, y, wx, wy, color=COLORS["height"], width=5.0, opacity=0.22))
        parts.append(_line(x, y, wx, wy, color=COLORS["height"], width=2.2, opacity=0.92, dashed=True))
        parts.append(_circle(wx, wy, 9.5, fill=COLORS["white"], stroke=COLORS["height"], stroke_width=3.0, opacity=0.95))
        parts.append(_path(f"M{wx - 38:.1f},{wy + 10:.1f} C{wx - 16:.1f},{wy + 24:.1f} {wx + 18:.1f},{wy + 24:.1f} {wx + 40:.1f},{wy + 10:.1f}", stroke=COLORS["water_line"], stroke_width=2.2, opacity="0.55"))

    for name, deck_pt, _water_pt, label_pos, anchor in samples:
        x, y = deck_pt
        parts.append(_circle(x, y, 11.5, fill=COLORS["white"], stroke=COLORS["sample"], stroke_width=3.0))
        parts.append(_circle(x, y, 5.0, fill=COLORS["sample"]))
        parts.append(_text(label_pos[0], label_pos[1], name, anchor=anchor))

    # Motion cues: one vertical translation and two rotations.
    parts.append(
        '<line x1="405" y1="452" x2="405" y2="365" '
        f'stroke="{COLORS["heave"]}" stroke-width="7" stroke-linecap="round" '
        'marker-end="url(#arrow-heave)" opacity="0.92"/>'
    )
    parts.append(
        '<line x1="405" y1="452" x2="405" y2="540" '
        f'stroke="{COLORS["heave"]}" stroke-width="7" stroke-linecap="round" '
        'marker-end="url(#arrow-heave)" opacity="0.92"/>'
    )
    parts.append(_polygon([(405.0, 348.0), (389.0, 377.0), (421.0, 377.0)], fill=COLORS["heave"], stroke=COLORS["heave"], stroke_width=0.0))
    parts.append(_polygon([(405.0, 557.0), (389.0, 528.0), (421.0, 528.0)], fill=COLORS["heave"], stroke=COLORS["heave"], stroke_width=0.0))
    parts.append(_text(405.0, 338.0, "heave", klass="motion", fill=COLORS["heave"]))

    parts.append(
        _path(
            "M690,492 C790,430 970,375 1090,348",
            stroke=COLORS["pitch"],
            stroke_width=7.0,
            stroke_linecap="round",
            marker_end="url(#arrow-pitch)",
            opacity="0.92",
        )
    )
    parts.append(_polygon([(1110.0, 343.0), (1072.0, 336.0), (1084.0, 370.0)], fill=COLORS["pitch"], stroke=COLORS["pitch"], stroke_width=0.0))
    parts.append(_text(905.0, 374.0, "pitch", klass="motion", fill=COLORS["pitch"]))

    parts.append(
        _path(
            "M794,358 C846,424 919,466 980,490",
            stroke=COLORS["roll"],
            stroke_width=7.0,
            stroke_linecap="round",
            marker_end="url(#arrow-roll)",
            opacity="0.92",
        )
    )
    parts.append(_polygon([(1000.0, 499.0), (963.0, 489.0), (988.0, 463.0)], fill=COLORS["roll"], stroke=COLORS["roll"], stroke_width=0.0))
    parts.append(_text(906.0, 486.0, "roll", klass="motion", fill=COLORS["roll"]))

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


def main() -> None:
    out_dir = Path(__file__).resolve().parent
    svg_path = out_dir / "platform_corner_heights.svg"
    pdf_path = out_dir / "platform_corner_heights.pdf"
    png_path = out_dir / "platform_corner_heights.png"

    svg_path.write_text(build_svg(), encoding="utf-8")
    print(f"Saved {svg_path}")
    if _convert_with_sips(svg_path, pdf_path, "pdf"):
        print(f"Saved {pdf_path}")
    else:
        print("Could not convert SVG to PDF.")
    if _convert_with_sips(svg_path, png_path, "png"):
        print(f"Saved {png_path}")
    else:
        print("Could not convert SVG to PNG.")


if __name__ == "__main__":
    main()
