/**
 * Genera la version PowerPoint del deck a partir de defensa/build/deck.json.
 *
 * El objetivo no es clonar el deck web pixel por pixel: eso no se puede, porque
 * el web usa grids CSS y componentes propios que PowerPoint no tiene. El objetivo
 * es que todo el contenido cruce en un layout limpio y facil de editar a mano,
 * que es justamente para lo que se pasa a Google Slides.
 *
 * El layout se arma en dos pasos. Primero se reparten los bloques en una o dos
 * columnas segun la marca `col` que dejo el extractor. Despues cada columna se
 * apila verticalmente calculando la altura natural de cada bloque; si la suma no
 * entra, se achican solo las imagenes y ecuaciones, que son lo unico que se puede
 * escalar sin perder informacion.
 *
 * Uso:
 *   node defensa/scripts/build_pptx.js
 * Requiere pptxgenjs. Salida: defensa/build/defensa.pptx
 */

const fs = require("fs");
const path = require("path");
const PptxGenJS = require("pptxgenjs");

const RAIZ = path.resolve(__dirname, "../..");
const ASSETS = path.join(RAIZ, "defensa/web/assets");
const DATOS = JSON.parse(fs.readFileSync(path.join(RAIZ, "defensa/build/deck.json"), "utf8"));

// Paleta del deck web, para que las dos versiones sean reconociblemente la misma.
const INK = "0F2A43", INK_SOFT = "4A6480", INK_FAINT = "8AA0B4";
const SEA = "0E6E8C", CORAL = "EF6A4C", PAPEL = "F5F8FA", LINEA = "CFDCE4";

// Lienzo 13.3 x 7.5. Margenes generosos: en proyeccion el borde se pierde.
const W = 13.333, H = 7.5;
const MX = 0.62, ARRIBA = 0.45;
const CUERPO_Y0 = 1.72, CUERPO_H = H - CUERPO_Y0 - 0.5;
const GAP = 0.34;

const pptx = new PptxGenJS();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Máximo Gubitosi · Jack Spolski";
pptx.title = "Simulación de dinámica de plataforma marina mediante un robot cuadrúpedo";

const dim = (rel) => DATOS.dims[rel] || [1600, 900];
const ruta = (rel) => path.join(ASSETS, rel);

/** Alto estimado de un texto, en pulgadas. */
function altoTexto(txt, ancho, cuerpo) {
  const porLinea = Math.max(1, Math.floor((ancho * 96) / (cuerpo * 0.52)));
  const lineas = Math.max(1, Math.ceil(txt.length / porLinea));
  return lineas * (cuerpo / 72) * 1.35 + 0.06;
}

/** Alto de cada fila de una tabla, contemplando que las celdas envuelven.
 *
 * Con un alto fijo por fila la estimacion queda corta apenas una celda pasa de
 * una linea, y el bloque siguiente se dibuja encima de la tabla. */
function altosFila(b, ancho) {
  const cols = Math.max(1, ...b.filas.map((f) => f.length));
  const anchoCelda = ancho / cols - 0.12;
  return b.filas.map((fila) => {
    const lineas = Math.max(1, ...fila.map((c) =>
      Math.ceil(c.length / Math.max(6, Math.floor((anchoCelda * 96) / 5.8)))));
    return Math.max(0.28, lineas * 0.20 + 0.10);
  });
}

/** Alto natural de un bloque a un ancho dado. */
function altoNatural(b, ancho) {
  switch (b.tipo) {
    case "imagen":
    case "video": {
      const rel = b.tipo === "video" ? b.poster : b.src;
      const [w, h] = dim(rel);
      return Math.min(ancho * (h / w), CUERPO_H * 0.62);
    }
    case "ecuacion": {
      const [w, h] = dim(b.src);
      // Las formulas no deben ocupar todo el ancho: a tamano completo compiten
      // con el titular. Se las topea y se las centra.
      const a = Math.min(ancho * (b.enfasis ? 0.86 : 0.68), ancho);
      return a * (h / w);
    }
    case "tabla":
      return altosFila(b, ancho).reduce((a, c) => a + c, 0) + 0.08;
    case "vinetas":
      return b.items.reduce((s, t) => s + altoTexto(t, ancho - 0.25, 13), 0) + 0.1;
    case "cifra":
      return 1.0;
    case "pill":
      return altoTexto(b.texto, ancho - 0.4, 12) + 0.16;
    case "epigrafe":
      return altoTexto(b.texto, ancho, 10);
    default:
      return altoTexto(b.texto, ancho, 13);
  }
}

/** Dibuja un bloque y devuelve el alto consumido. */
function dibujar(slide, b, x, y, ancho, escala) {
  switch (b.tipo) {
    case "imagen":
    case "video": {
      const rel = b.tipo === "video" ? b.poster : b.src;
      const [w, h] = dim(rel);
      let a = ancho, alt = ancho * (h / w);
      const tope = Math.min(CUERPO_H * 0.62, altoNatural(b, ancho) * escala);
      if (alt > tope) { alt = tope; a = alt * (w / h); }
      slide.addImage({ path: ruta(rel), x: x + (ancho - a) / 2, y, w: a, h: alt });
      if (b.tipo === "video") {
        // Marca de que ahi va un video: en Slides hay que insertarlo a mano.
        slide.addText("▶  VIDEO", {
          x: x + (ancho - a) / 2 + 0.08, y: y + 0.08, w: 1.15, h: 0.26,
          fontSize: 10, bold: true, color: "FFFFFF", align: "center",
          fill: { color: CORAL }, fontFace: "Arial", margin: 0,
        });
      }
      return alt;
    }
    case "ecuacion": {
      const [w, h] = dim(b.src);
      let a = Math.min(ancho * (b.enfasis ? 0.86 : 0.68), ancho);
      let alt = a * (h / w);
      const tope = altoNatural(b, ancho) * escala;
      if (alt > tope) { alt = tope; a = alt * (w / h); }
      slide.addImage({ path: ruta(b.src), x: x + (ancho - a) / 2, y, w: a, h: alt });
      return alt;
    }
    case "tabla": {
      const filas = b.filas.map((fila, i) =>
        fila.map((celda) => ({
          text: celda,
          options: {
            fontSize: b.simbolos ? 10.5 : 11,
            bold: b.encabezado && i === 0,
            color: b.encabezado && i === 0 ? INK_FAINT : (b.simbolos ? INK_SOFT : INK),
            fill: { color: i % 2 === 0 ? "FFFFFF" : PAPEL },
          },
        }))
      );
      // La primera columna es la etiqueta y va en color, como en el deck web.
      filas.forEach((f) => { if (f[0]) { f[0].options.color = SEA; f[0].options.bold = true; } });
      const altos = altosFila(b, ancho);
      slide.addTable(filas, {
        x, y, w: ancho, rowH: altos, border: { type: "solid", pt: 0.5, color: LINEA },
        fontFace: "Calibri", valign: "middle", margin: 4,
      });
      return altoNatural(b, ancho);
    }
    case "vinetas": {
      const alto = altoNatural(b, ancho);
      slide.addText(
        b.items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < b.items.length - 1 } })),
        { x, y, w: ancho, h: alto, fontSize: 13, color: INK, fontFace: "Calibri",
          paraSpaceAfter: 5, valign: "top", margin: 0 }
      );
      return alto;
    }
    case "cifra": {
      slide.addText(b.valor, { x, y, w: ancho, h: 1.0, fontSize: 54, bold: true,
        color: SEA, fontFace: "Calibri", align: "left", margin: 0, valign: "middle" });
      return 1.0;
    }
    case "pill": {
      const alto = altoNatural(b, ancho);
      slide.addText(b.texto, { x, y, w: ancho, h: alto, fontSize: 12, color: CORAL,
        fontFace: "Calibri", align: "center", valign: "middle", margin: 4,
        fill: { color: "FCEDE9" }, rectRadius: 0.1, shape: pptx.ShapeType.roundRect });
      return alto;
    }
    case "epigrafe": {
      const alto = altoNatural(b, ancho);
      slide.addText(b.texto, { x, y, w: ancho, h: alto, fontSize: 10, color: INK_FAINT,
        fontFace: "Calibri", valign: "top", margin: 0 });
      return alto;
    }
    default: {
      const alto = altoNatural(b, ancho);
      slide.addText(b.texto, { x, y, w: ancho, h: alto, fontSize: 13, color: INK_SOFT,
        fontFace: "Calibri", valign: "top", margin: 0, lineSpacingMultiple: 1.15 });
      return alto;
    }
  }
}

/** Apila una lista de bloques en una columna, achicando si no entran. */
function columna(slide, bloques, x, y0, ancho, altoDisp) {
  if (!bloques.length) return;
  const naturales = bloques.map((b) => altoNatural(b, ancho));
  const total = naturales.reduce((a, c) => a + c, 0) + GAP * (bloques.length - 1);
  // Solo se achica lo escalable. Si el excedente es texto, no hay nada que hacer
  // mas que dejarlo: es preferible una lamina apretada a una con texto cortado.
  let escala = 1;
  if (total > altoDisp) {
    const escalable = bloques.reduce((s, b, i) =>
      s + (["imagen", "video", "ecuacion"].includes(b.tipo) ? naturales[i] : 0), 0);
    const fijo = total - escalable;
    escala = escalable > 0 ? Math.max(0.42, (altoDisp - fijo) / escalable) : 1;
  }
  let y = y0;
  bloques.forEach((b) => {
    const usado = dibujar(slide, b, x, y, ancho,
      ["imagen", "video", "ecuacion"].includes(b.tipo) ? escala : 1);
    y += usado + GAP;
  });
}

// --- Construccion -----------------------------------------------------------
let nMain = 0;
DATOS.laminas.forEach((lam, idx) => {
  const slide = pptx.addSlide();
  slide.background = { color: PAPEL };
  if (!lam.backup) nMain++;

  if (lam.eyebrow) {
    slide.addText(lam.eyebrow.toUpperCase(), {
      x: MX, y: ARRIBA, w: W - 2 * MX, h: 0.26, fontSize: 10.5, bold: true,
      color: lam.backup ? INK_FAINT : CORAL, charSpacing: 1.5,
      fontFace: "Calibri", margin: 0, valign: "middle",
    });
  }
  if (lam.titular) {
    slide.addText(lam.titular, {
      x: MX, y: ARRIBA + 0.34, w: W - 2 * MX, h: 0.95, fontSize: 30, bold: true,
      color: INK, fontFace: "Calibri", margin: 0, valign: "top",
    });
  }

  const izq = lam.bloques.filter((b) => b.col === "izq");
  const der = lam.bloques.filter((b) => b.col === "der");
  const libres = lam.bloques.filter((b) => !b.col);

  if (izq.length && der.length) {
    const anchoCol = (W - 2 * MX - 0.5) / 2;
    // Los bloques sin columna (los que en el web van a todo el ancho, como la
    // franja de alcance) se cuelgan al final de la izquierda para no perderlos.
    columna(slide, izq.concat(libres), MX, CUERPO_Y0, anchoCol, CUERPO_H);
    columna(slide, der, MX + anchoCol + 0.5, CUERPO_Y0, anchoCol, CUERPO_H);
  } else {
    columna(slide, lam.bloques, MX, CUERPO_Y0, W - 2 * MX, CUERPO_H);
  }

  // Pie: numero de lamina y marca de backup.
  slide.addText(lam.backup ? `BACKUP  ·  ${lam.titulo_indice}` : `${nMain} / 34`, {
    x: MX, y: H - 0.42, w: W - 2 * MX, h: 0.24, fontSize: 9,
    color: INK_FAINT, fontFace: "Calibri", align: lam.backup ? "left" : "right", margin: 0,
  });

  const notas = [];
  lam.bloques.filter((b) => b.tipo === "video").forEach((b) => {
    notas.push(`VIDEO: insertar ${b.archivo} (Insertar > Video > Google Drive).`);
  });
  if (notas.length) slide.addNotes(notas.join("\n"));
});

const salida = path.join(RAIZ, "defensa/build/defensa.pptx");
pptx.writeFile({ fileName: salida }).then(() => {
  console.log(`${DATOS.laminas.length} laminas -> ${salida}`);
});
