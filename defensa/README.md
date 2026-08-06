# Defensa oral · presentación

La presentación es una **página web**, no un PPT. Vive entera en `web/` y funciona
offline, así que el día de la defensa alcanza con abrir el archivo.

**Publicada en:** <https://maxgubitosi.github.io/go2-marine-platform/defensa/web/>
GitHub Pages sirve desde `main`, así que **cada push actualiza la presentación**
(el build tarda alrededor de un minuto).

---

## Verla

```bash
python3 defensa/scripts/preview.py     # desde la raíz del repo
```

y abrir <http://localhost:8771>. El servidor sirve sin caché, que es lo que evita
quedarse mirando una versión vieja del CSS sin darse cuenta.

También se puede abrir `web/index.html` directo con doble clic: el deck no hace
ningún `fetch` ni carga nada externo. Es más incómodo para iterar, pero sirve
para verificar que anda sin servidor, que es como va a andar el día de la defensa.

**Teclas:** `→` `←` o espacio para navegar · `O` índice · `B` backup · `D`
borrador · `F` pantalla completa.

---

## Cómo está armado

| Archivo | Qué es |
|---|---|
| `web/index.html` | las láminas, una `<section class="slide">` cada una |
| `web/css/style.css` | todo el estilo, con comentarios explicando cada decisión |
| `web/js/deck.js` | el motor: navegación, progreso, índice, animaciones |
| `plan_presentacion.md` | qué se ve y qué se dice en cada lámina |
| `IDENTIDAD.md` | cómo se ve y cómo se escribe: paleta, tipografía, componentes, antipatrones |
| `backlog.md` | lo que falta resolver antes de agosto |

**Antes de escribir una lámina nueva, leer `IDENTIDAD.md`.** Es lo que evita que
el deck vuelva a los títulos genéricos y las cajitas conceptuales que Gastón pidió
sacar.

**Tres tipos de lámina.** Las del hilo principal se numeran solas. Las que
llevan `data-backup="N"` quedan afuera del conteo y se saltan con `B`: son las
respuestas preparadas para preguntas previsibles. Las que llevan
`data-draft="N"` van al final de todo, se saltan con `D` y son el **borrador**:
versiones guardadas por si se retoman, cambios temporales, pruebas. No cuentan
en el total ni aparecen en el progreso.

**El motor deriva todo del orden del DOM**: número de lámina, progreso por bloque
y el índice salen de dónde está cada `<section>`. Eso quiere decir que **agregar o
mover una lámina no obliga a tocar `deck.js`**, sólo a renumerar la documentación.

Verificar siempre a **1280x720 y 1920x1080**. El deck entra sin desborde vertical
en las dos; el único desborde horizontal es el de la portada y es a propósito
(la franja de mar va a sangre).

---

## Dos convenciones que conviene conocer antes de editar

**1. Cero em dashes.** No debe haber ni un `—` en las láminas. Reemplazar según el
caso por dos puntos, paréntesis, coma o `·`. Nunca de forma mecánica.

```bash
grep -c '—' defensa/web/index.html defensa/web/css/style.css   # tiene que dar 0
```

**2. Las ecuaciones no se editan a mano.** Son SVG pre-renderizados desde el
mismo LaTeX que compila el informe, inyectados dentro de contenedores
`<div class="eq" data-eq="nombre">`. Con el SVG adentro cada fórmula ocupa miles
de caracteres, así que para editar una lámina que tenga fórmulas el ciclo es:

```bash
python3 defensa/scripts/inline_math.py --strip   # vacía los contenedores
# ... editar web/index.html cómodo ...
python3 defensa/scripts/inline_math.py           # vuelve a inyectar
python3 defensa/scripts/inline_math.py --check   # verifica que esté al día
```

Para **agregar** una fórmula: se la declara en `scripts/render_math.py` (con su
`\label` del informe, si tiene), se corre el script y después el inliner.

`web/assets/math/PROCEDENCIA.md` registra de qué línea y qué `\label` del informe
salió cada una, y con qué número se la cita en la lámina.

> Los números de ecuación se leen de `informe/main.aux`, que **no está versionado**
> por ser un artefacto de compilación. Si hace falta agregar una fórmula nueva,
> compilar el informe una vez primero. Las que ya están citadas no lo necesitan:
> su número quedó escrito en el HTML y en `PROCEDENCIA.md`.

---

## Regenerar cosas

```bash
python3 defensa/scripts/render_math.py           # ecuaciones a SVG (y PNG)
python3 defensa/scripts/crop_escenarios.py       # recortes de S15
python3 defensa/scripts/crop_setup_sim.py        # recorte de Gazebo de S16
```

Todos los scripts de recorte **escriben a archivos nuevos y nunca pisan el
original**. Si se cambia una imagen de un par comparativo, hay que volver a pasar
las dos por el script: varias láminas dependen de que las dos imágenes compartan
exactamente la misma relación de aspecto para que las cajas midan igual.

**Versión PowerPoint** (probada y por ahora descartada, pero la cadena funciona):

```bash
python3 defensa/scripts/extract_deck.py > defensa/build/deck.json
node defensa/scripts/build_pptx.js               # necesita `npm install pptxgenjs`
```

`build/` está ignorado: es todo derivado.

---

## Lo que NO está en el repo

`defensa/media/` es el **material crudo curado** (unos 348 MB) del que salieron
los assets del deck: los `.MOV` de iPhone del laboratorio, las fotos `.HEIC` y las
capturas de simulación. No se versiona por peso.

**No hace falta para trabajar en la presentación**: los videos y las fotos que el
deck usa ya están convertidos y versionados en `web/assets/`. Sólo hace falta para
re-cortar un clip o elegir una toma distinta.

Se comparte aparte (Drive). Tiene su propio `README.md`, que sí está versionado,
así que se puede saber qué contiene sin tenerlo descargado.

**Ojo con los formatos:** los `.mov` de iPhone son HEVC y las fotos `.heic` son
HEIF. Ningún navegador los reproduce: hay que convertirlos a H.264 y JPEG antes de
embeberlos.

---

## Herramientas

| Para qué | Qué hace falta |
|---|---|
| Ver y editar el deck | nada, sólo Python 3 para el servidor |
| Regenerar ecuaciones | TeX Live (`latex`, `dvisvgm`, `dvipng`) |
| Recortar imágenes | `pip install pillow` |
| Exportar a PowerPoint | `pip install lxml` · Node y `npm install pptxgenjs` |
| Convertir media cruda | `ffmpeg` |
