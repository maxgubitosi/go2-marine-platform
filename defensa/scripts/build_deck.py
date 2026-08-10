"""Arma web/index.html pegando las láminas de web/slides/ dentro de web/plantilla.html.

Cada lámina vive en su propio archivo para que dos personas puedan editar
láminas distintas sin pisarse: git no tiene que fusionar nada porque los cambios
caen en archivos separados.

El orden sale del número al principio del nombre (`010-portada.html`,
`020-...`). Van de a 10 justamente para poder meter una lámina en el medio
(`015-...`) sin renombrar todas las que siguen, que sería el conflicto que esto
viene a evitar. El resto del nombre es descriptivo y no lo mira nadie.

`web/index.html` es generado: se pisa entero en cada build, así que editarlo a
mano es perder el cambio. Se versiona igual porque es lo que sirve GitHub Pages
y lo que se abre con doble clic sin servidor.

Uso:
    python3 defensa/scripts/build_deck.py     # desde cualquier lado
"""

import sys
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"
SLIDES = WEB / "slides"
MARCA = "<!-- SLIDES -->"


def armar():
    """Devuelve el HTML completo del deck, sin escribir nada."""
    laminas = sorted(SLIDES.glob("*.html"))
    if not laminas:
        sys.exit(f"No hay láminas en {SLIDES}")
    plantilla = (WEB / "plantilla.html").read_text(encoding="utf-8")
    if MARCA not in plantilla:
        sys.exit(f"plantilla.html no tiene la marca {MARCA}")
    cuerpo = "\n\n".join(p.read_text(encoding="utf-8").rstrip("\n") for p in laminas)
    return plantilla.replace(MARCA, cuerpo), len(laminas)


def build():
    """Regenera index.html si cambió. Devuelve (cambió, cuántas láminas)."""
    html, n = armar()
    destino = WEB / "index.html"
    if destino.exists() and destino.read_text(encoding="utf-8") == html:
        return False, n
    destino.write_text(html, encoding="utf-8")
    return True, n


if __name__ == "__main__":
    cambio, n = build()
    print(f"{n} láminas -> web/index.html" + ("" if cambio else " (ya estaba al día)"))
