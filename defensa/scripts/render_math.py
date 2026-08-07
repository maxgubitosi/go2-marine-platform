"""Renderiza las ecuaciones del deck a SVG desde LaTeX.

Por qué SVG pre-renderizado y no una librería de JavaScript: la presentación se
proyecta en una máquina que no controlamos y tiene que andar también sin internet
y desde un pendrive. KaTeX o MathJax agregan una dependencia en tiempo de
ejecución que puede fallar justo ahí. Un SVG con los glifos convertidos a curvas
no depende de nada, escala a cualquier resolución y, sobre todo, sale de la misma
cadena de LaTeX que compila el informe: la notación proyectada es exactamente la
que el jurado leyó en el texto.

Las fórmulas se copian del informe (`informe/main.tex`, que es sólo lectura) y se
anota de qué línea vino cada una para poder auditarlas.

Uso:
    python3 defensa/scripts/render_math.py            # las que faltan
    python3 defensa/scripts/render_math.py --force    # todas de nuevo

Salida: defensa/web/assets/math/<nombre>.svg
"""

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DST = Path("defensa/web/assets/math")

# Cuerpo del documento con el que se compila cada fórmula. Sirve de unidad para
# convertir los pt que emite dvisvgm en em relativos al texto del deck.
BASE_PT = 12.0

# El preámbulo replica los paquetes de matemática del informe para que la
# notación salga igual. No se usa fontspec porque acá compilamos con latex y no
# con xelatex: para matemática, Computer Modern y Latin Modern son equivalentes.
PREAMBLE = r"""
\documentclass[preview,border=1pt,12pt]{standalone}
\usepackage{amsmath,amsfonts,amssymb}
\usepackage{mathtools}
\usepackage{upgreek}
\begin{document}
"""

AUX = Path("informe/main.aux")
AUDIT = DST / "PROCEDENCIA.md"

# nombre -> (linea del informe, LaTeX, label del informe)
EQUATIONS = {}


def eq(name, informe_line, latex, label=None):
    """Registra una fórmula. `label` es su \\label en el informe, si tiene uno.

    El label es lo que permite citarla en la lámina por su número real de
    ecuación: ese número no está en el .tex sino que lo asigna LaTeX al
    compilar, así que se lo lee del .aux y no se lo copia a mano. Si el informe
    se recompila y la numeración se corre, basta con volver a correr esto.
    """
    EQUATIONS[name] = (informe_line, latex, label)


def numeros_del_informe():
    """label -> número de ecuación, leídos del .aux del informe ya compilado."""
    if not AUX.exists():
        print(f"aviso: no está {AUX}, las láminas no van a poder citar números")
        return {}
    aux = AUX.read_text(encoding="utf-8", errors="replace")
    return dict(re.findall(r"\\newlabel\{(eq:[a-z_0-9]+)\}\{\{(\d+)\}", aux))


# --- Modelo marino y síntesis del oleaje -----------------------------------
eq("marine_kinematics", 1293, r"\dot{\eta} = J(\eta)\,\nu",
   "eq:marine_kinematics")
eq("marine_dynamics", 1314,
   r"M \dot{\nu} + C(\nu)\nu + D(\nu)\nu + g(\eta) = \tau + \tau_w",
   "eq:marine_dynamics")
# La del puente entre el oleaje y la actitud de la cubierta: es la ecuación que
# sostiene todo el trabajo, así que va completa y no sólo con el lado izquierdo.
eq("reduced_state", 1340,
   r"\eta_r(t) \approx \begin{bmatrix} z(t) \\[2pt] \phi(t) \\[2pt] \theta(t) \end{bmatrix}"
   r" = \begin{bmatrix} \zeta(x_p,y_p,t) \\[4pt]"
   r" \kappa_{\phi}\,\dfrac{\partial \zeta}{\partial y}(x_p,y_p,t) \\[4pt]"
   r" -\kappa_{\theta}\,\dfrac{\partial \zeta}{\partial x}(x_p,y_p,t) \end{bmatrix}",
   "eq:reduced_marine_state")
eq("wave_field", 1430, r"\zeta(x,y,t) = A \sin(k_x x + k_y y - \omega t + \delta)",
   "eq:sinusoidal_wave_model")
eq("wave_harmonic", 1453,
   r"\zeta(x,y,t) = \sum_{n=1}^{N} A_n \sin(k_{x,n} x + k_{y,n} y - \omega_n t + \delta_n)",
   "eq:harmonic_wave_model")

# --- Estimación de pose por marcador ---------------------------------------
eq("pinhole", 1079,
   r"s_i \begin{bmatrix} u_i \\ v_i \\ 1 \end{bmatrix} = K \begin{bmatrix} R & t \end{bmatrix}"
   r"\begin{bmatrix} P_i \\ 1 \end{bmatrix}",
   "eq:pinhole_projection")
eq("intrinsics", 1102,
   r"K = \begin{bmatrix} f_x & 0 & c_x \\ 0 & f_y & c_y \\ 0 & 0 & 1 \end{bmatrix}",
   "eq:camera_intrinsics")
eq("pnp", 1160,
   r"(\hat{R},\hat{t}) = \operatorname*{arg\,min}_{R,t} \sum_{i=1}^{4}"
   r"\left\| p_i - \pi\!\left(K(RP_i + t)\right) \right\|^2",
   "eq:pnp_optimization")

# --- Control postural del Go2 ----------------------------------------------
eq("quadruped_dynamics", 1717,
   r"M(\bar q)\,\ddot{\bar q} + h(\bar q,\dot{\bar q}) = S^\top \tau + J_c(\bar q)^\top \lambda",
   "eq:quadruped_dynamics")
eq("contact_constraint", 1748, r"J_c(q)\,\dot{q} = 0",
   "eq:contact_velocity_constraint")
eq("dof_count", 1748, r"\underbrace{18}_{6\ \text{base} \;+\; 12\ \text{art.}}"
                      r"\;-\;\underbrace{12}_{\operatorname{rank} J_c}\;=\;\underbrace{6}_{\text{pose del torso}}")
# El puente entre la consigna del torso y las patas: con los pies apoyados, una
# variación de la pose del cuerpo se lee como la corrección que cada pie tiene
# que compensar en el marco del cuerpo. Es la que hace física la consigna marina.
eq("body_to_feet", 1927,
   r"\delta\, {}^{b}\!p_{f_i} \approx -\,\delta p_b - \delta \omega \times {}^{b}\!p_{f_i,0}",
   "eq:body_variation_to_feet")
eq("leg_ik", 1984, r"\delta q_i = J_i(q_i)^{-1}\,\delta\, {}^{b}\!p_{f_i}",
   "eq:leg_inverse_differential_kinematics")

# --- Cadena de medición ----------------------------------------------------
eq("transform_chain", 2132,
   r"{}^{c}T_a(t) = {}^{c}T_w(t)\,{}^{w}T_{bf}(t)\,{}^{bf}T_{bl}(t)\,{}^{bl}T_a",
   "eq:camera_marker_chain")

# --- Consignas efectivamente enviadas --------------------------------------
eq("commands", 2282,
   r"\begin{aligned}"
   r"r(t) &= A_r \sin(\omega t) \\"
   r"p(t) &= A_p \sin(\omega \kappa_p t + \pi/3) \\"
   r"h(t) &= A_h \sin(\omega \kappa_h t)"
   r"\end{aligned}")
eq("ema", 2365, r"\tilde{x}_k = \alpha\,\tilde{x}_{k-1} + (1-\alpha)\,x_k")

# --- Resultados de laboratorio ---------------------------------------------
# El modelo de respuesta con el que se resume la caracterización dinámica. No es
# una ecuación numerada del informe: es la forma en que el deck resume el
# desacople medido (fase más escala), consistente con la tabla R4/R5.
eq("lab_response", 3385,
   r"\theta_{\text{real}}(t) \approx g\,\theta_{\text{cmd}}(t - \tau) + b")


def render_png(name, latex, workdir, dst_dir, dpi=600):
    """Compila la misma fórmula a PNG con fondo transparente.

    Hace falta para la versión PowerPoint/Google Slides, que no acepta SVG. Va a
    600 dpi para que aguante proyección sin verse pixelada: en la lámina se la
    reduce, así que lo que sobra es resolución y no tamaño en pantalla.
    """
    tex = workdir / f"{name}_png.tex"
    tex.write_text(PREAMBLE + f"\\[{latex}\\]\n" + r"\end{document}", encoding="utf-8")
    subprocess.run(["latex", "-interaction=nonstopmode", "-halt-on-error", tex.name],
                   cwd=workdir, capture_output=True, text=True, check=True)
    out = dst_dir / f"{name}.png"
    subprocess.run(["dvipng", "-D", str(dpi), "-T", "tight", "-bg", "Transparent",
                    "-o", str(out.resolve()), f"{name}_png.dvi"],
                   cwd=workdir, capture_output=True, text=True, check=True)
    return out


def render(name, latex, workdir):
    """Compila una fórmula y devuelve el SVG como texto."""
    tex = workdir / f"{name}.tex"
    tex.write_text(PREAMBLE + f"\\[{latex}\\]\n" + r"\end{document}", encoding="utf-8")

    run = subprocess.run(
        ["latex", "-interaction=nonstopmode", "-halt-on-error", tex.name],
        cwd=workdir, capture_output=True, text=True)
    if run.returncode != 0:
        err = [l for l in run.stdout.split("\n") if l.startswith("!")]
        raise RuntimeError(f"{name}: LaTeX falló\n  " + "\n  ".join(err[:4]))

    # --no-fonts convierte los glifos a curvas: el SVG no depende de ninguna
    # fuente instalada en la máquina que proyecte.
    subprocess.run(
        ["dvisvgm", "--no-fonts", "--exact-bbox", "--precision=4",
         f"{name}.dvi", "-o", f"{name}.svg"],
        cwd=workdir, capture_output=True, text=True, check=True)

    svg = (workdir / f"{name}.svg").read_text(encoding="utf-8")

    # dvisvgm pinta en negro fijo. Se lo saca para que el color lo mande el CSS
    # del deck vía currentColor y las fórmulas sigan el tema de la lámina.
    svg = re.sub(r"\bfill=['\"]#000(?:000)?['\"]", "fill='currentColor'", svg)
    svg = re.sub(r"<\?xml[^>]*\?>\s*", "", svg)
    svg = re.sub(r"<!DOCTYPE[^>]*>\s*", "", svg)

    # dvisvgm mide en pt, y una fórmula alta sale con más pt que una baja. Si el
    # CSS las dimensiona a todas con la misma altura, cada una queda a un cuerpo
    # distinto y la notación se ve descalibrada de lámina en lámina.
    # Como todas se compilan a 12pt, pasar pt a em dividiendo por 12 hace que
    # 1em sea el cuerpo del texto: a partir de ahí alcanza con un font-size en
    # el contenedor para que todas compartan escala tipográfica.
    def pt_a_em(m):
        return f"{m.group(1)}='{float(m.group(2)) / BASE_PT:.4f}em'"

    svg = re.sub(r"\b(width|height)=['\"]([\d.]+)pt['\"]", pt_a_em, svg, count=2)
    return svg.strip()


def main():
    force = "--force" in sys.argv
    if not shutil.which("latex") or not shutil.which("dvisvgm"):
        sys.exit("Faltan latex o dvisvgm. Instalar TeX Live.")

    DST.mkdir(parents=True, exist_ok=True)
    nums = numeros_del_informe()
    hechas = saltadas = 0
    filas = []

    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        for name, (line, latex, label) in EQUATIONS.items():
            num = nums.get(label) if label else None
            filas.append((name, num, line, label))
            out = DST / f"{name}.svg"
            if out.exists() and not force:
                saltadas += 1
                continue
            svg = render(name, latex, workdir)
            out.write_text(svg, encoding="utf-8")
            hechas += 1
            cita = f"ec. ({num})" if num else "sin numerar"
            print(f"  {name:22s} {cita:>13s}  linea {line:<5} {len(svg):>6}B")

    faltan = [n for n, num, _, lbl in filas if lbl and not num]
    if faltan:
        print(f"\naviso: sin número en el .aux -> {', '.join(faltan)}")

    escribir_procedencia(filas)
    print(f"\n{hechas} renderizadas, {saltadas} ya estaban. Total {len(EQUATIONS)}.")
    print(f"Procedencia en {AUDIT}")


def escribir_procedencia(filas):
    """Deja por escrito de dónde salió cada fórmula.

    Sirve para dos cosas: poder auditar contra el informe sin abrir el script, y
    tener a mano el número de ecuación que cada lámina cita, porque es lo que le
    permite al jurado ir a buscarla al texto.
    """
    out = [
        "# Procedencia de las ecuaciones del deck",
        "",
        "Generado por `defensa/scripts/render_math.py`. No editar a mano.",
        "",
        "Los números de ecuación salen de `informe/main.aux`, o sea de la última",
        "compilación del informe. Si el informe se recompila y la numeración se",
        "corre, hay que volver a correr el script y actualizar las citas de las",
        "láminas.",
        "",
        "| SVG | Ecuación en el informe | Línea en `main.tex` | `\\label` |",
        "|---|---|---|---|",
    ]
    for name, num, line, label in sorted(filas):
        cita = f"({num})" if num else "sin numerar"
        out.append(f"| `{name}.svg` | {cita} | {line} | `{label or '-'}` |")
    out.append("")
    AUDIT.write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
    main()
