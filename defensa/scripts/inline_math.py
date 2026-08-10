"""Inyecta los SVG de las ecuaciones dentro del HTML del deck.

Cada fórmula vive en el HTML como un contenedor marcado:

    <div class="eq hero" data-eq="reduced_state"></div>

y este script le mete adentro el contenido de `assets/math/reduced_state.svg`.

Por qué inline y no un `<img src=...>`: el SVG usa `currentColor`, así que
inyectado hereda el color del CSS y una misma fórmula puede ir en tinta plena
cuando es la protagonista de la lámina o apagada cuando se la menciona al pasar.
Cargada como imagen externa eso no funciona, porque el CSS de la página no
cruza el borde del documento SVG.

Es idempotente: reemplaza el contenido del contenedor, no lo duplica. O sea que
se puede correr todas las veces que haga falta, y hay que correrlo cada vez que
se vuelva a generar una fórmula con render_math.py.

Uso:
    python3 defensa/scripts/inline_math.py            # inyecta
    python3 defensa/scripts/inline_math.py --check    # sólo informa
    python3 defensa/scripts/inline_math.py --strip    # vacía los contenedores

--check no escribe nada: sólo informa si el HTML está al día. Sirve para
verificar antes de publicar.

--strip hace lo contrario de inyectar: deja los contenedores vacíos. Es para
poder editar una lámina cómodamente, porque con los SVG adentro cada fórmula
ocupa miles de caracteres y encontrar el texto alrededor se vuelve imposible. El
ciclo es: --strip, editar, y volver a inyectar.
"""

import re
import sys
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"
SLIDES = WEB / "slides"
MATH = WEB / "assets" / "math"

# Captura el contenedor completo: apertura, contenido actual y cierre.
PATRON = re.compile(
    r'(<div class="[^"]*\beq\b[^"]*" data-eq="(\w+)"\s*>)(.*?)(</div>)',
    re.S)


def main():
    check = "--check" in sys.argv
    strip = "--strip" in sys.argv
    laminas = sorted(SLIDES.glob("*.html"))
    if not laminas:
        sys.exit(f"No hay láminas en {SLIDES}")

    faltantes, iguales, cambiadas, total = [], 0, [], 0

    def sustituir(m):
        nonlocal iguales
        apertura, nombre, actual, cierre = m.groups()
        svg_path = MATH / f"{nombre}.svg"
        if not svg_path.exists():
            faltantes.append(nombre)
            return m.group(0)
        svg = svg_path.read_text(encoding="utf-8").strip()
        if actual.strip() == svg:
            iguales += 1
        else:
            cambiadas.append(nombre)
        return apertura + svg + cierre

    for lamina in laminas:
        html = lamina.read_text(encoding="utf-8")
        total += len(PATRON.findall(html))
        if strip:
            lamina.write_text(PATRON.sub(lambda m: m.group(1) + m.group(4), html),
                              encoding="utf-8")
            continue
        antes = len(cambiadas)
        nuevo = PATRON.sub(sustituir, html)
        if not check and len(cambiadas) > antes:
            lamina.write_text(nuevo, encoding="utf-8")

    if strip:
        print(f"{total} contenedores vaciados. "
              f"Editar y volver a correr sin --strip.")
        return

    if faltantes:
        print("sin SVG (correr render_math.py primero): " + ", ".join(sorted(set(faltantes))))

    if check:
        estado = "al día" if not cambiadas and not faltantes else "desactualizado"
        print(f"{total} contenedores, {iguales} al día, {len(cambiadas)} desactualizados -> {estado}")
        sys.exit(1 if (cambiadas or faltantes) else 0)

    for n in cambiadas:
        print(f"  inyectada  {n}")
    print(f"\n{total} contenedores: {len(cambiadas)} actualizados, {iguales} ya estaban al día.")


if __name__ == "__main__":
    main()
