"""Extrae el contenido del deck web a JSON, para poder regenerarlo en PowerPoint.

El HTML del deck es un documento de diseño: cada lámina tiene su propio layout,
con grids, columnas y componentes hechos a medida. Nada de eso cruza a PowerPoint.
Lo que sí cruza es el contenido, así que este script lo separa de la presentación:
por cada lámina saca el eyebrow, el titular y una lista ordenada de bloques
(texto, viñetas, imagen, ecuación, tabla, cifra destacada), anotando en qué
columna estaba cada uno para poder recomponer un layout de dos columnas.

Las ecuaciones se referencian por su PNG (assets/math/png/<nombre>.png), que
genera render_math.py, porque PowerPoint no acepta SVG.

Uso:
    python3 defensa/scripts/extract_deck.py > defensa/build/deck.json
"""

import json
import re
import sys
from pathlib import Path

from lxml import html as LH

HTML = Path("defensa/web/index.html")
WEB = Path("defensa/web")

# Videos: en PowerPoint van como fotograma fijo. El frame ya está extraído.
FRAMES = "assets/img/frames"

# Escenas SVG animadas, rasterizadas por su posición de aparición en el deck.
ESCENAS = ["img/escenas/portada_mar.jpg", "img/escenas/olas_perfil_dof.jpg",
           "img/escenas/olas_proa_dof.jpg", "img/escenas/olas_perfil.jpg",
           "img/escenas/olas_proa.jpg"]


def texto(el):
    """Texto plano de un elemento, con los espacios normalizados."""
    return " ".join("".join(el.itertext()).split())


def columna_de(el, raiz):
    """Devuelve 'izq', 'der' o None según en qué mitad del split cae el bloque.

    Sirve para que el layout de PowerPoint conserve la lectura en dos columnas
    en lugar de apilar todo, que es lo que hace que un deck convertido se vea
    como un volcado.
    """
    padre = el
    while padre is not None and padre is not raiz:
        abuelo = padre.getparent()
        clases_abuelo = (abuelo.get("class") or "") if abuelo is not None else ""
        # scenerow y cards son grids de dos columnas igual que split: si no se
        # los reconoce, sus dos mitades se apilan y la lamina queda vacia a los
        # costados.
        if any(k in clases_abuelo for k in ("split", "scenerow", "imgrow")):
            hermanos = [h for h in abuelo if h.tag is not LH.etree.Comment]
            try:
                return "izq" if hermanos.index(padre) == 0 else "der"
            except ValueError:
                return None
        padre = abuelo
    return None


# Un solo xpath con todo lo que cuenta como bloque. Se resuelve de una y en
# orden de documento, para después quedarse sólo con los de nivel más alto.
CANDIDATOS = (
    ".//*[@data-eq] | .//*[contains(@class,'wave-scene')] | .//img | .//video |"
    ".//table | .//ul | .//ol | .//dl[contains(@class,'symkey')] |"
    ".//*[contains(@class,'hero-num')] | .//p | .//figcaption |"
    ".//span[contains(@class,'pill')] | .//span[contains(@class,'eq-ref')]"
)


def bloques_de(slide, contador_escenas):
    """Arma la lista de bloques de una lámina, en orden de lectura.

    Ojo con dos cosas. La primera es que hay que descartar los candidatos que
    caen adentro de otro candidato (el texto de una celda de tabla, por ejemplo),
    porque si no el mismo contenido sale dos veces. La segunda es que la
    identidad se compara con `is` sobre elementos que se mantienen referenciados
    en `sel`: `id()` no sirve, porque lxml crea los proxies al vuelo y reusa la
    dirección de memoria de los que se recolectan, de modo que un `id()` viejo
    matchea elementos que no tienen nada que ver.
    """
    sel = slide.xpath(CANDIDATOS)
    conjunto = set(sel)
    externos = []
    for el in sel:
        p = el.getparent()
        anidado = False
        while p is not None and p is not slide:
            if p in conjunto:
                anidado = True
                break
            p = p.getparent()
        if not anidado:
            externos.append(el)

    out = []
    for el in externos:
        cls = el.get("class") or ""

        # Ecuación: contenedor marcado con data-eq
        if el.get("data-eq"):
            out.append({"tipo": "ecuacion", "nombre": el.get("data-eq"),
                        "enfasis": "hero" in cls, "col": columna_de(el, slide)})
            continue

        # Escena de oleaje animada -> imagen rasterizada
        if "wave-scene" in cls:
            i = contador_escenas[0]
            if i < len(ESCENAS):
                out.append({"tipo": "imagen", "src": ESCENAS[i],
                            "col": columna_de(el, slide)})
            contador_escenas[0] += 1
            continue

        if el.tag == "img" and el.get("src"):
            out.append({"tipo": "imagen", "src": el.get("src").replace("assets/", "", 1),
                        "alt": el.get("alt") or "", "col": columna_de(el, slide)})
            continue

        if el.tag == "video" and el.get("src"):
            nombre = Path(el.get("src")).stem
            out.append({"tipo": "video", "poster": f"{FRAMES}/{nombre}.jpg".replace("assets/", "", 1),
                        "archivo": el.get("src"), "col": columna_de(el, slide)})
            continue

        if el.tag == "table":
            filas = []
            for tr in el.iter("tr"):
                filas.append([texto(td) for td in tr if td.tag in ("td", "th")])
            encabezado = bool(el.find(".//thead") is not None)
            out.append({"tipo": "tabla", "filas": filas, "encabezado": encabezado,
                        "col": columna_de(el, slide)})
            continue

        if el.tag in ("ul", "ol"):
            items = [texto(li) for li in el.iter("li")]
            if items:
                out.append({"tipo": "vinetas", "items": items,
                            "col": columna_de(el, slide)})
            continue

        if el.tag == "dl" and "symkey" in cls:
            pares = []
            hijos = [h for h in el if h.tag in ("dt", "dd")]
            for a, b in zip(hijos[::2], hijos[1::2]):
                pares.append([texto(a), texto(b)])
            out.append({"tipo": "tabla", "filas": pares, "encabezado": False,
                        "simbolos": True, "col": columna_de(el, slide)})
            continue

        if "hero-num" in cls:
            out.append({"tipo": "cifra", "valor": texto(el), "col": columna_de(el, slide)})
            continue

        if el.tag in ("p", "figcaption", "span") and not el.get("data-eq"):
            t = texto(el)
            if not t:
                continue
            if "pill" in cls:
                out.append({"tipo": "pill", "texto": t, "col": columna_de(el, slide)})
            elif el.tag == "figcaption" or "res-cap" in cls or "eq-ref" in cls or "hero-label" in cls:
                out.append({"tipo": "epigrafe", "texto": t, "col": columna_de(el, slide)})
            elif el.tag == "p":
                out.append({"tipo": "texto", "texto": t, "col": columna_de(el, slide)})
    return out


def main():
    doc = LH.fromstring(HTML.read_text(encoding="utf-8"))
    contador_escenas = [0]
    laminas = []
    for slide in doc.xpath("//section[contains(@class,'slide')]"):
        cls = slide.get("class") or ""
        backup = slide.get("data-backup") is not None
        eb = slide.xpath(".//div[@class='eyebrow']")
        h2 = slide.xpath(".//h2[contains(@class,'head')]")
        laminas.append({
            "titulo_indice": slide.get("data-title") or "",
            "bloque": slide.get("data-block"),
            "backup": backup,
            "eyebrow": texto(eb[0]) if eb else "",
            "titular": texto(h2[0]) if h2 else "",
            "bloques": bloques_de(slide, contador_escenas),
        })
    json.dump({"laminas": laminas}, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
