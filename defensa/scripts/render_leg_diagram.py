"""Genera el diagrama de la estructura articular del Go2 para la lámina J1.

Por qué un script y no SVG escrito a mano: el diagrama tiene tres vistas que
tienen que compartir escala métrica y no pisarse ni una etiqueta. Ajustar eso a
ojo, mirando capturas, es un lazo largo y frágil. Acá la geometría se calcula
desde los mismos parámetros del URDF que cita la lámina, y al final el script
verifica que ninguna etiqueta se superponga con otra ni con un trazo. Si el
chequeo falla, no emite nada.

Las tres vistas comparten escala: un metro mide lo mismo en las tres, así que el
offset de abducción se puede comparar de un vistazo contra la longitud del muslo.

Uso:
    python3 defensa/scripts/render_leg_diagram.py            # escribe el SVG
    python3 defensa/scripts/render_leg_diagram.py --check    # sólo verifica

Salida: defensa/web/assets/img/leg_kinematics.svg
El SVG se inyecta inline en index.html (no como <img>) para que el texto herede
la tipografía del deck. Ver `.legfig` en css/style.css.
"""

import math
import sys
from pathlib import Path

DST = Path("defensa/web/assets/img/leg_kinematics.svg")

# --- Parámetros del URDF del Go2, los mismos que cita la lámina --------------
D = 0.0955          # offset lateral de abducción
L1 = L2 = 0.213     # muslo y pantorrilla
HIP_X = 0.1934      # montaje de cadera sobre el torso, longitudinal
HIP_Y = 0.0465      # idem, transversal

# --- Postura dibujada --------------------------------------------------------
# Se dibuja una postura de apoyo realista y no una pata estirada: con el muslo a
# 38 grados de la vertical y la rodilla flexionada al doble, el pie cae justo
# debajo de la cadera, que es la configuración nominal del régimen postural.
ALPHA = math.radians(38.0)      # muslo respecto de la vertical
BETA = 2 * ALPHA                # flexión de rodilla: deja el pie bajo la cadera
Q_ABD = math.radians(12.0)      # abducción dibujada

S = 481.0           # escala, px por metro, común a las tres vistas
GAP = 104.0         # aire entre vistas
MARGIN = 16.0
CAP_DY = 34.0       # separación entre el contenido y su epígrafe

# Alto efectivo de la pata en el plano de la pata: es la cantidad
# l1*cos(q2) + l2*cos(q2+q3) que aparece en la cinemática directa.
REACH = (L1 * math.cos(ALPHA) + L2 * math.cos(ALPHA - BETA))

# --- Paleta, en literal porque el SVG se estiliza por clase desde el deck ----
INK, SOFT, FAINT = "#0f2a43", "#4a6480", "#8aa0b4"
LINK, PANEL, EDGE = "#2b5f80", "#e7eef3", "#b9cbd8"
OFFSET, ANG, GUIDE = "#8e6bb5", "#ef6a4c", "#b9cbd8"


class Panel:
    """Una vista. Acumula trazos y etiquetas en coordenadas locales."""

    def __init__(self, caption):
        self.caption = caption
        self.draw = []      # (svg, bbox|None) de los trazos estructurales
        self.labels = []    # (svg, bbox, texto) de las etiquetas
        self.segs = []      # segmentos que una etiqueta no puede pisar

    # -- primitivas -----------------------------------------------------------
    def line(self, a, b, color, w, dash=None, mark=True):
        d = f" stroke-dasharray='{dash}'" if dash else ""
        self.draw.append(f"<line x1='{a[0]:.1f}' y1='{a[1]:.1f}' x2='{b[0]:.1f}' "
                         f"y2='{b[1]:.1f}' stroke='{color}' stroke-width='{w}'{d}/>")
        if mark:
            self.segs.append((a, b))

    def rect(self, x, y, w, h, r=6):
        self.draw.append(f"<rect x='{x:.1f}' y='{y:.1f}' width='{w:.1f}' height='{h:.1f}' "
                         f"rx='{r}' fill='{PANEL}' stroke='{EDGE}' stroke-width='1.2'/>")

    def joint(self, p, axis_out=False):
        """Junta. Con axis_out se le pone el punto central: eje perpendicular
        al plano dibujado, que es la convención con la que se leen las tres."""
        self.draw.append(f"<circle cx='{p[0]:.1f}' cy='{p[1]:.1f}' r='5.5' fill='#fff' "
                         f"stroke='{INK}' stroke-width='2'/>")
        if axis_out:
            self.draw.append(f"<circle cx='{p[0]:.1f}' cy='{p[1]:.1f}' r='1.7' fill='{INK}'/>")

    def foot(self, p):
        self.draw.append(f"<circle cx='{p[0]:.1f}' cy='{p[1]:.1f}' r='5' fill='{INK}'/>")

    def vector(self, a, b, color):
        """Flecha de a a b. Es la notación que usan las láminas siguientes, así
        que se dibuja con punta y no como un segmento más."""
        import math as _m
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = _m.hypot(dx, dy) or 1.0
        ux, uy = dx / n, dy / n
        # se corta antes del punto para que la punta no tape la junta
        ex, ey = b[0] - ux * 9, b[1] - uy * 9
        px, py = -uy, ux
        self.draw.append(
            f"<line x1='{a[0]:.1f}' y1='{a[1]:.1f}' x2='{ex:.1f}' y2='{ey:.1f}' "
            f"stroke='{color}' stroke-width='2.2'/>"
            f"<path d='M{ex:.1f} {ey:.1f} L{ex - ux * 9 + px * 4:.1f} {ey - uy * 9 + py * 4:.1f} "
            f"L{ex - ux * 9 - px * 4:.1f} {ey - uy * 9 - py * 4:.1f} Z' fill='{color}'/>")

    def origin(self, p):
        """Origen del marco del cuerpo: cruz y punto, la marca convencional."""
        self.draw.append(
            f"<path d='M{p[0] - 7:.1f} {p[1]:.1f} H{p[0] + 7:.1f} M{p[0]:.1f} {p[1] - 7:.1f} "
            f"V{p[1] + 7:.1f}' stroke='{INK}' stroke-width='1.4'/>"
            f"<circle cx='{p[0]:.1f}' cy='{p[1]:.1f}' r='2.4' fill='{INK}'/>")

    def arc(self, center, r, u_from, u_to, sweep):
        a = (center[0] + r * u_from[0], center[1] + r * u_from[1])
        b = (center[0] + r * u_to[0], center[1] + r * u_to[1])
        self.draw.append(f"<path d='M{a[0]:.1f} {a[1]:.1f} A {r} {r} 0 0 {sweep} "
                         f"{b[0]:.1f} {b[1]:.1f}' fill='none' stroke='{ANG}' stroke-width='2'/>")

    def right_angle(self, corner, u1, u2, s=9.0):
        p1 = (corner[0] + s * u1[0], corner[1] + s * u1[1])
        p3 = (corner[0] + s * u2[0], corner[1] + s * u2[1])
        p2 = (p1[0] + s * u2[0], p1[1] + s * u2[1])
        self.draw.append(f"<path d='M{p1[0]:.1f} {p1[1]:.1f} L{p2[0]:.1f} {p2[1]:.1f} "
                         f"L{p3[0]:.1f} {p3[1]:.1f}' fill='none' stroke='{SOFT}' "
                         f"stroke-width='1.1'/>")

    def axes(self, right, up, origin, size=30):
        x0, y0 = origin
        self.draw.append(
            f"<path d='M{x0 + size:.1f} {y0:.1f} L{x0:.1f} {y0:.1f} L{x0:.1f} {y0 - size:.1f}' "
            f"fill='none' stroke='{FAINT}' stroke-width='1.3'/>")
        self.text(right, (x0 + size + 5, y0 + 4), 11, FAINT, cls="lf-ax")
        self.text(up, (x0 - 5, y0 - size - 4), 11, FAINT, anchor="end", cls="lf-ax")

    # -- texto ----------------------------------------------------------------
    def text(self, s, p, size, color, anchor="start", cls="lf-t", sub=None, weight=None):
        """Coloca una etiqueta y guarda su caja para el chequeo de colisiones.

        `sub` es el subíndice, que va como tspan y no como <text> aparte: así la
        caja que se verifica es la misma que el navegador va a pintar.
        """
        w = _width(s, size) + (_width(sub, size * 0.72) if sub else 0.0)
        x0 = {"start": p[0], "middle": p[0] - w / 2, "end": p[0] - w}[anchor]
        box = (x0, p[1] - size * 0.78, x0 + w, p[1] + size * 0.24)
        body = _esc(s) + (f"<tspan dy='{size * .22:.1f}' font-size='{size * .72:.1f}'>"
                          f"{_esc(sub)}</tspan>" if sub else "")
        fw = f" font-weight='{weight}'" if weight else ""
        self.labels.append((
            f"<text x='{p[0]:.1f}' y='{p[1]:.1f}' class='{cls}' fill='{color}' "
            f"text-anchor='{anchor}'{fw}>{body}</text>", box, s + (sub or "")))

    # -- salida ---------------------------------------------------------------
    def bbox(self):
        xs, ys = [], []
        for _, b, _ in self.labels:
            xs += [b[0], b[2]]
            ys += [b[1], b[3]]
        for a, b in self.segs:
            xs += [a[0], b[0]]
            ys += [a[1], b[1]]
        return min(xs), min(ys), max(xs), max(ys)


# --- métrica tipográfica aproximada -----------------------------------------
# No hay forma de medir de verdad sin un motor de texto, así que se usa una
# tabla de anchos con margen: sobreestimar es lo seguro, porque el chequeo de
# colisiones tiene que fallar de más y no de menos.
#
# El umbral de los chequeos es un margen visual, no cero: dos etiquetas separadas
# por dos píxeles no se superponen pero se leen pegadas, que era el problema.
_NARROW = set("ijl.,;:'|!()[]₁₂₃")
_WIDE = set("mwMW")


def _width(s, size):
    total = 0.0
    for ch in s:
        if ch in _NARROW:
            total += 0.30
        elif ch in _WIDE:
            total += 0.88
        elif ch.isupper():
            total += 0.68
        else:
            total += 0.56
    # margen de seguridad: subestimar es lo unico que el chequeo no perdona
    return total * size * 1.06


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _overlap(a, b, pad=7.0):
    return not (a[2] + pad <= b[0] or b[2] + pad <= a[0]
                or a[3] + pad <= b[1] or b[3] + pad <= a[1])


def _seg_hits_box(seg, box, pad=5.0):
    """Clipping de Liang-Barsky: dice si el segmento entra en la caja."""
    (x0, y0), (x1, y1) = seg
    xmin, ymin, xmax, ymax = box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad
    dx, dy = x1 - x0, y1 - y0
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x0 - xmin), (dx, xmax - x0), (-dy, y0 - ymin), (dy, ymax - y0)):
        if p == 0:
            if q < 0:
                return False
            continue
        r = q / p
        if p < 0:
            if r > t1:
                return False
            t0 = max(t0, r)
        else:
            if r < t0:
                return False
            t1 = min(t1, r)
    return t0 <= t1


# --- las tres vistas ---------------------------------------------------------

def planta():
    """(a) Vista superior: dónde se monta cada pata sobre el torso."""
    p = Panel("(a) planta: las cuatro caderas sobre el torso")
    hx, hy, off = HIP_X * S, HIP_Y * S, D * S
    p.rect(-hx - 12, -hy - 11, 2 * hx + 24, 2 * hy + 22)
    p.text("torso", (0, 4), 12, FAINT, anchor="middle")
    for sx, sy, name, lab_anchor in ((1, -1, "FL", "start"), (1, 1, "FR", "start"),
                                     (-1, -1, "RL", "end"), (-1, 1, "RR", "end")):
        hip = (sx * hx, sy * hy)
        toe = (sx * hx, sy * (hy + off))
        p.line(hip, toe, OFFSET, 3.4)
        p.joint(hip)
        p.foot(toe)
        p.text(name, (sx * hx + sx * 11, toe[1] + (7 if sy > 0 else 0)), 12, SOFT,
               anchor=lab_anchor, weight="620")
    # El offset se acota una sola vez: repetirlo en las cuatro patas es ruido.
    p.text("d", (hx - 9, -hy - off / 2 - 3), 13, OFFSET, anchor="end", weight="700")
    p.axes("x", "y", origin=(-hx - 70, -hy - off - 40), size=24)
    return p


def frontal():
    """(b) Plano frontal: la abducción y el offset lateral."""
    p = Panel("(a) plano frontal · abducción")
    u = (math.sin(Q_ABD), math.cos(Q_ABD))            # dirección de la pata
    n = (math.cos(Q_ABD), -math.sin(Q_ABD))           # normal, hacia afuera
    h = (0.0, 0.0)
    a = (D * S * n[0], D * S * n[1])
    f = (a[0] + REACH * S * u[0], a[1] + REACH * S * u[1])

    p.rect(-104, -17, 104, 34)
    p.text("torso", (-52, 4), 12, FAINT, anchor="middle")
    p.line(h, (h[0], f[1] + 12), GUIDE, 1, dash="4 4", mark=False)     # vertical del cuerpo
    p.line(a, (a[0], a[1] + 92), GUIDE, 1, dash="4 4", mark=False)     # vertical local
    p.line(h, a, OFFSET, 3.6)
    p.line(a, f, LINK, 4)
    p.right_angle(a, (-n[0], -n[1]), u)
    p.arc(a, 78, (0, 1), u, sweep=0)
    p.joint(h, axis_out=True)
    p.joint(a)
    p.foot(f)

    p.text("HAA", (h[0] + 14, h[1] - 20), 12, INK, weight="620")
    p.text("d", ((h[0] + a[0]) / 2, 15), 13, OFFSET, anchor="middle", weight="700")
    p.text("q", (a[0] - 9, a[1] + 84), 13, ANG, anchor="end", sub="i,1")
    p.axes("y", "z", origin=(-104, f[1] + 26))
    return p


def sagital():
    """(b) Plano sagital: la cadena de dos eslabones y los dos vectores.

    Los vectores van en esta vista y no en la frontal porque la componente
    dominante del montaje de cadera es la longitudinal (0,1934 m contra 0,0465):
    en el plano frontal la flecha mediría 22 px contra una pata de 162.
    """
    p = Panel("(b) plano sagital · muslo y rodilla")
    o = (0.0, 0.0)
    t = (HIP_X * S, 0.0)
    u1 = (math.sin(ALPHA), math.cos(ALPHA))
    u2 = (math.sin(ALPHA - BETA), math.cos(ALPHA - BETA))
    k = (t[0] + L1 * S * u1[0], t[1] + L1 * S * u1[1])
    f = (k[0] + L2 * S * u2[0], k[1] + L2 * S * u2[1])

    p.rect(-78, -23, 78 + t[0] + 20, 46)
    p.text("torso", (-52, -12), 12, FAINT, anchor="middle")
    p.line(t, (t[0], t[1] + 96), GUIDE, 1, dash="4 4", mark=False)
    p.line(k, (k[0] + 52 * u1[0], k[1] + 52 * u1[1]), GUIDE, 1, dash="4 4", mark=False)
    p.line(t, k, LINK, 4)
    p.line(k, f, LINK, 4)
    p.arc(t, 58, (0, 1), u1, sweep=0)
    p.arc(k, 44, u1, u2, sweep=1)
    # Los vectores se dibujan después de la pata para que la punta quede encima.
    p.vector(o, t, OFFSET)
    p.vector(o, f, ANG)
    p.origin(o)
    p.joint(t, axis_out=True)
    p.joint(k, axis_out=True)
    p.foot(f)

    p.text("{b}", (-13, 9), 12, INK, anchor="end", weight="620")
    p.text("r", (t[0] / 2, -8), 13, OFFSET, anchor="middle", sub="h i", weight="700")
    p.text("p", (f[0] - 24, f[1] - 30), 13, ANG, anchor="end", sub="f i", weight="700")
    p.text("HFE", (t[0] + 10, -32), 12, INK, weight="620")
    p.text("KFE", (k[0] + 13, k[1] - 6), 12, INK, weight="620")
    p.text("pie", (f[0] + 4, f[1] + 22), 12, SOFT, anchor="middle")
    p.text("q", (t[0] - 10, 76), 13, ANG, anchor="end", sub="i,2")
    p.text("q", (k[0] + 52, k[1] + 48), 13, ANG, sub="i,3")
    p.text("l₁", ((t[0] + k[0]) / 2 + 18, (t[1] + k[1]) / 2 - 2), 12, FAINT)
    p.text("l₂", ((k[0] + f[0]) / 2 - 26, (k[1] + f[1]) / 2 + 4), 12, FAINT, anchor="end")
    p.axes("x", "z", origin=(-52, f[1] + 30))
    return p


def build():
    panels = [frontal(), sagital()]

    # Las tres vistas se centran verticalmente en una misma banda y se apoyan en
    # una línea de epígrafes común. La (a) es mucho más baja que las otras dos:
    # alinearlas arriba la dejaría flotando, y alinearlas abajo la hundiría.
    boxes = [p.bbox() for p in panels]
    band = max(b[3] - b[1] for b in boxes)
    cap_y = MARGIN + band + CAP_DY

    out, problems, placed = [], [], []
    x = MARGIN
    for p, b in zip(panels, boxes):
        dx = x - b[0]
        dy = MARGIN + (band - (b[3] - b[1])) / 2 - b[1]
        # El epígrafe se centra sobre el contenido real de su vista y se agrega
        # después de medirla, así que no desplaza el centro que acaba de fijarse.
        # En coordenadas locales: el <g> de la vista ya aplica dx y dy.
        p.text(p.caption, ((b[0] + b[2]) / 2, cap_y - dy), 12.5, FAINT,
               anchor="middle", cls="lf-cap")
        body = "".join(p.draw) + "".join(s for s, _, _ in p.labels)
        out.append(f"<g transform='translate({dx:.1f},{dy:.1f})'>{body}</g>")
        placed.append((p, dx, dy))
        x += (b[2] - b[0]) + GAP

    # Chequeo: ninguna etiqueta contra otra, ninguna etiqueta contra un trazo.
    todos = []
    for p, dx, dy in placed:
        for _, box, txt in p.labels:
            todos.append(((box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy), txt))
        for a, b in p.segs:
            for _, box, txt in p.labels:
                if _seg_hits_box(((a[0], a[1]), (b[0], b[1])), box):
                    problems.append(
                        f"{p.caption[:3]} la etiqueta {txt!r} pisa el trazo "
                        f"({a[0]:.0f},{a[1]:.0f})-({b[0]:.0f},{b[1]:.0f})")
    for i in range(len(todos)):
        for j in range(i + 1, len(todos)):
            if _overlap(todos[i][0], todos[j][0]):
                problems.append(f"se pisan las etiquetas {todos[i][1]!r} y {todos[j][1]!r}")

    # El viewBox se cierra sobre las cajas reales y no sobre el avance de la
    # grilla: un epígrafe más ancho que su vista quedaría recortado.
    w = max(x - GAP, max(box[2] for box, _ in todos)) + MARGIN
    h = max(box[3] for box, _ in todos) + MARGIN
    svg = (f"<svg viewBox='0 0 {w:.0f} {h:.0f}' role='img' aria-label='Estructura "
           f"articular del Go2: planta con las cuatro patas, plano frontal con la "
           f"abducción de cadera y plano sagital con muslo y rodilla'>"
           + "".join(out) + "</svg>")
    return svg, sorted(set(problems))


def main():
    svg, problems = build()
    if problems:
        print("colisiones detectadas, no se escribe nada:")
        for p in problems:
            print("  " + p)
        sys.exit(1)
    print("sin colisiones entre etiquetas ni contra trazos")
    if "--check" in sys.argv:
        return
    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_text(svg, encoding="utf-8")
    print(f"{DST}  {len(svg)} B")
    print("pegar el contenido dentro de <figure class='legfig'> en index.html")


if __name__ == "__main__":
    main()
