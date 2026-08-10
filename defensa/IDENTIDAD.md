# Identidad visual y de redacción · defensa oral PF

Este documento fija **cómo se ve y cómo se escribe** la presentación, para que las
láminas nuevas se parezcan a las viejas y para no volver a discutir decisiones ya
tomadas. Es normativo: si una lámina lo contradice, se corrige la lámina.

Lo complementan `README.md` (cómo se edita y se sirve) y `plan_presentacion.md`
(qué se ve y qué se dice en cada lámina).

---

## 1. De dónde sale esto

Tres fuentes, en orden de autoridad:

**1. Gastón Castro (mentor), julio 2026.** Es el origen de casi todas las reglas
de esta página:

> *"tienen que entrar en la matemática y dar detalles técnicos claros"*
> *"no pueden ser todos títulos generales y cajitas con flechas conceptuales"*
> *"eviten títulos genéricos"*

De ahí salieron dos pasadas grandes, que están en el historial y conviene leer
antes de tocar nada:

| Commit | Qué resolvió |
|---|---|
| `272b21f` | la metodología pasa de flechas conceptuales a las ecuaciones del informe, citadas por su número real |
| `23686a2` | 26 de 33 titulares reescritos, y limpieza de tics de plantilla |

**2. Corrección de cátedra, mayo 2026** (`informe/correcciones_07-05-26/correcciones.md`).
Lo que aplica al deck: no decir "esta tesis" (no lo es formalmente) sino "este
trabajo"; no aclarar "en el informe" o "como base metodológica en este informe",
porque se entiende; el estado del arte se analiza sin referirlo al trabajo propio.

**3. Decisiones del equipo** ya cerradas: fondo claro, poco texto, cero em dashes,
resultados como distribuciones y no como cifras sueltas.

**El registro es académico.** El riesgo de este deck no es aburrir: es sonar a
pitch de empresa o a demo de hackathon frente a un jurado que espera un trabajo
de ingeniería. Ante la duda entre una formulación vistosa y una precisa, gana la
precisa.

---

## 2. Cómo se escribe

### 2.1 Titulares (`h2.head`)

**Regla:** el titular **nombra lo que la lámina muestra**, no lo anuncia ni lo
promociona. Si alguien lee sólo los titulares en el índice (`O`), tiene que
quedarle el contenido del trabajo, no una lista de intrigas.

| No | Sí |
|---|---|
| El barco sintético existe | El torso del Go2 sigue la consigna marina comandada |
| Una campaña para descartar la suerte | Campaña de simulación: escenarios, corridas y criterio de comparación |
| Qué aprendimos y qué admitimos | Alcance y limitaciones de la validación en simulación |

Prohibido en titulares:

- **Preguntas retóricas autocontestadas.** Había una ("¿Llega el comando intacto?
  Sí.") y se sacó.
- **Pares por antítesis** del tipo "la pregunta más limpia" / "la geometría más
  exigente". Decir qué aísla cada configuración es más informativo y más corto.
- **Meta-comentario sobre la propia charla** ("lo que viene ahora", "spoiler").
- **Adjetivos de venta**: potente, clave, impresionante, revolucionario.

Dos patrones que sí funcionan y ya están en uso:

- `Concepto: precisión` con dos puntos. *Pose por PnP: cuatro esquinas de
  geometría conocida y una cámara calibrada.*
- Afirmación declarativa con sujeto y verbo. *Los cuatro apoyos fijan doce de los
  dieciocho grados de libertad.*

Un titular no debería pasar de dos renglones a 1280x720. Si no entra, lo que
sobra suele ser la configuración experimental: va al eyebrow (así se resolvieron
S19 y S20).

### 2.2 La palabra en turquesa (`<span class="accent">`)

Estuvo en 31 de 33 titulares, o sea que no destacaba nada. **Queda en 5**, y sólo
cuando marca un **término técnico que esa lámina introduce**. No se usa para
resaltar la parte "linda" de la frase.

Antes de agregar un `accent`, contar cuántos hay:

```bash
grep -c 'class="head".*accent' defensa/web/slides/*.html   # no debería pasar de 5
```

### 2.3 Encabezado de sección (`div.eyebrow`)

Es la ubicación en la charla, no un título alternativo. Formato fijo:

```html
<div class="eyebrow"><span class="num">III</span><span class="lbl">Metodología<span class="s">: percepción</span></span></div>
```

- **Romano y color por sección.** El número dice qué capítulo es y el color
  refuerza en qué bloque estamos. No es decoración: es la única señal de
  ubicación que se ve desde el fondo del aula.
- **Dos puntos como separador**, que es la convención de título de capítulo
  (*Capítulo III: percepción*). Nunca `·`, nunca guion, nunca em dash.
- **El subtema va en minúscula** (regla del castellano después de dos puntos) y
  en gris, para que el nombre del bloque se lea primero.
- **Caja baja, sin tracking.** No lleva mayúsculas con `letter-spacing` ancho.
- **Portada y lámina de cierre usan `.eyebrow.plain`**: no son sección, así que
  no llevan romano ni color.

| Bloque | Romano | Token de color |
|---|---|---|
| Introducción | I | `--sec-intro` |
| Problema | II | `--sec-prob` |
| Metodología | III | `--sec-metodo` |
| Resultados | IV | `--sec-result` |
| Conclusiones | V | `--sec-concl` |
| Backup | B | `--sec-backup` |
| Borrador | D | `--sec-borrador` |

El color sale de `data-block` en el `<section>`, así que **una lámina nueva sólo
necesita su `data-block` correcto**: el color y el romano se escriben a mano en
el encabezado, pero el color no se repite en el HTML.

Los nombres de bloque viven en tres lugares y tienen que coincidir: el encabezado
de cada lámina, el array `BLOCKS` de `deck.js` y el rótulo de backup de
`deck.js`.

### 2.4 Bajada (`p.lead`) y cuerpo

- La bajada da el contexto que el titular no puede: una o dos oraciones, máximo
  40ch de ancho por CSS.
- El cuerpo es **apoyo visual, no guion**. Si un párrafo se lee en voz alta tal
  cual, sobra: va al `plan_presentacion.md`, que es donde vive lo que se dice.
- Tercera persona o plural impersonal ("se mide", "el trabajo cubre"). Evitar el
  "nosotros" enfático de pitch ("logramos", "atacamos el problema").
- Sin "esta tesis" ni "en el informe" (corrección de cátedra).

### 2.5 Cifras y resultados

Toda cifra va **con la condición en que se midió** (corrida, N, amplitud). El
bloque de resultados reporta distribuciones, no números héroe sueltos, y cada
figura de distribución lleva epígrafe que dice **cómo leerla**.

La cifra héroe (`.hero-num`, `.statband`) queda para el bloque de contexto, donde
la magnitud es el mensaje. En resultados, no.

### 2.6 Citas al informe

Las ecuaciones se citan por su número real (`Informe · ec. (9)`), que sale de
`informe/main.aux`. Es lo que le permite al jurado ir a buscarla al texto, y es
media respuesta al pedido de Gastón sobre detalle técnico.

### 2.7 Cero em dashes

Ni uno. Se reemplaza por dos puntos, paréntesis, coma o `·`, según el caso y
nunca de forma mecánica.

```bash
grep -c '—' defensa/web/slides/*.html defensa/web/css/style.css   # tiene que dar 0
```

---

## 3. Paleta

Definida en `:root` de `css/style.css`. **No inventar colores nuevos en el HTML:**
si hace falta uno, se agrega como token con su razón de ser.

| Token | Hex | Para qué |
|---|---|---|
| `--paper` | `#f5f8fa` | fondo de lámina |
| `--paper-2` | `#eef3f6` | panel sutil, fondo de ilustración |
| `--ink` | `#0f2a43` | texto principal, titulares |
| `--ink-soft` | `#4a6480` | texto secundario, bajadas, descripciones |
| `--ink-faint` | `#8aa0b4` | epígrafes, anotaciones, **lo que está fuera de foco** |
| `--sea` | `#0e6e8c` | acento tipográfico, término técnico, eyebrow |
| `--sea-bright` | `#12a3c4` | trayectorias y señales en ilustraciones |
| `--foam` / `--foam-line` | `#d7ebf1` / `#b9d9e3` | fondos y bordes de panel claro |
| `--coral` | `#ef6a4c` | **señal**: lo que hay que mirar, y color del bloque Resultados |
| `--sec-intro` … `--sec-backup` | ver §2.3 | color de sección en el encabezado |
| `--coral-soft` | `#f9d9d0` | fondo de énfasis coral |
| `--amber` | `#e8a13c` | haces, luces, advertencia en ilustración |
| `--line` | `#cfdce4` | bordes y rieles neutros |
| `--ok` / `--warn` | `#2e9e6b` / `#d98a2b` | cumple / no cumple en tablas |

Tres reglas de uso que importan más que la lista:

1. **El coral es escaso.** Marca una sola cosa por lámina: la que hay que mirar.
   Si hay dos corales compitiendo, uno de los dos está mal.
2. **El gris no es "menos lindo", es "fuera de foco".** La escala
   `ink → ink-soft → ink-faint` codifica jerarquía de atención, y en S5 codifica
   directamente el alcance: lo que el trabajo no cubre va en `ink-faint`.
3. **El azul es la identidad, no el énfasis.** El mar, el logo y los términos
   técnicos. Para llamar la atención está el coral.

---

## 4. Tipografía

Una sola familia, Inter (`--sans`), con la mono (`--mono`) reservada para datos.

| Uso | Tamaño | Peso |
|---|---|---|
| `h1.title` (portada) | `clamp(2.4rem, 6vw, 4.6rem)` | 800 |
| `h2.head` (titular) | `clamp(1.9rem, 4.2vw, 3.1rem)` | 780 |
| `p.lead` (bajada) | `clamp(1.05rem, 1.7vw, 1.5rem)`, máx. 40ch | 420 |
| `h3` de componente | 1,05 a 1,2rem | 640 a 720 |
| cuerpo | 0,9 a 1rem | 400 |
| `figcaption` | 0,85rem, `--ink-faint` | 400 |
| encabezado de sección | 0,95rem caja baja, romano en mono a 0,76em | 660 y 430 |

**La mono es para datos, nunca para prosa:** cifras, identificadores, tópicos ROS,
nombres de archivo, ecuaciones en línea. Un párrafo en mono es un tic de terminal
y no aporta nada.

Ancho de línea: entre 32ch y 48ch en columnas. Más que eso cansa a la distancia
de proyección.

---

## 5. Arquetipos de lámina

**Esta lista es cerrada.** Antes de escribir una clase de CSS nueva hay que poder
decir por qué la lámina no entra en ninguno de estos seis. La medición del
07-08-2026 explica por qué el inventario abierto que había acá no alcanzó: 165
clases de componente, **115 usadas en una sola lámina**, y 21 estructuras de
cuerpo distintas para 34 láminas. O sea que casi cada lámina se diseñó de cero.
Eso es exactamente lo que se lee como "muchos estilos y cosas distintas".

| | Arquetipo | Para qué | Estructura |
|---|---|---|---|
| **A** | Media y argumento | una figura y la afirmación que sostiene | `.split` |
| **B** | Matemática | la ecuación es el ancla de la lámina | `.eq` + clave de símbolos + lectura + cita |
| **C** | Par | dos cosas del mismo rango, comparables | dos `figure` de igual caja |
| **D** | Serie | tres o más ítems del mismo rango | una sola grilla, ver la regla de abajo |
| **E** | Resultado | figura de distribución con su lectura | cifra + figura + epígrafe |
| **F** | Diagrama propio | un argumento que ninguna de las otras cinco puede sostener | a medida |

Portada, backup y borrador quedan fuera: no son arquetipos, son estados.

### 5.1 La regla de la serie (D)

Es el arquetipo con más riesgo de leerse como plantilla, porque una grilla de
tarjetas iguales es la forma por defecto de cualquier generador. Antes de usarlo:

1. **¿Los ítems son intercambiables?** Si uno de ellos es la conclusión, o si hay
   un orden que importa, no son una serie. Es una D falsa.
2. **¿La grilla dice algo que una lista no diría?** Si la respuesta es que "queda
   más prolijo", va lista.
3. **Sin numerar.** Un `01 / 02 / 03` sólo se justifica si el contenido *es* una
   secuencia y el lector necesita el orden. Casi nunca lo es.

Está resuelto con **un solo componente**, `.serie`, y cuatro modificadores que
elige el contenido y no el gusto:

| Modificador | Cuándo |
|---|---|
| `.cols` | ítems en columnas. Lleva filete superior en el color de la sección |
| `.filas` | ítems apilados, con la marca a la izquierda. Reparte el alto |
| `.figs` | la serie lleva dibujos: la altura la fija el dibujo, no se estira |
| `.grande` | ítems de un renglón: se agranda el texto en vez de estirar la caja |

Dentro de cada ítem: `.serie-fig` (opcional), `.serie-k` para la marca propia del
ítem (un año, un orden real, el término que lo nombra) y `.serie-txt`. La
codificación semántica va por clase en el ítem, no por `style=`: `.ok`, `.warn`,
`.sim`, `.lab`.

**Estirar una caja no llena una lámina.** Si el ítem lleva un SVG, la caja crece
pero el dibujo conserva su proporción y queda flotando con bandas vacías. Se ve
igual de vacío y además engaña a cualquier medición de llenado, porque la caja
llega y la tinta no. Por eso existe `.figs`.

### 5.2 El presupuesto de diagramas propios (F)

**Como mucho cuatro en todo el deck.** Es la regla más importante de esta sección.

Un diagrama a medida es donde se gasta la audacia: el riel de arquitectura y las
dos filas del criterio de evaluación funcionan porque su forma *es* el argumento.
Pero si hay ocho, ninguno se destaca y el deck vuelve a parecer un muestrario.
Cuando entra un F nuevo, alguno de los que están tiene que salir o degradarse a
A-E.

Para calificar como F hay que contestar que **no** a las dos: ¿lo diría igual de
bien una tabla? ¿lo diría igual de bien un par?

---

## 6. Ritmo vertical

**El cuerpo tiene que llegar al 80% de su alto.** Medido el 07-08-2026 a 1280x720:
la mediana está en 96%, pero hay **13 láminas de 34 por debajo del 80%**, y las
peores en 45-48%. Ese es el "queda mucho espacio vacío".

Cuando una lámina no llega, la salida **no** es agregar relleno ni estirar
interlineados. En orden:

1. Agrandar la media hasta donde el arquetipo lo permita.
2. Si sigue sin llegar, la lámina tiene poco contenido: se funde con la vecina.
3. Si no se puede fundir, se acepta y se deja anotado. Una lámina aireada a
   propósito es legítima; trece no.

Dos cosas ya resueltas que conviene no volver a romper:

- `.s-body` separa del header con `margin-top`, **nunca `padding-top`**. Con
  padding, el `justify-content:center` reparte sólo el alto restante y todo el
  deck queda 18px más abajo que el centro de su caja. Estuvo así hasta el
  07-08-2026.
- Un elemento con `margin-top` grande al final del cuerpo (típicamente
  `.conclusion`) mete ese margen adentro de la línea que se centra, así que el
  contenido visible sube. Si la lámina se ve descolgada hacia arriba, es esto.

### 6.1 Cuándo se permite una clase nueva

Una clase nueva necesita **una de estas dos**:

- la van a usar **dos láminas o más**, o
- está adentro de un diagrama F, dentro del presupuesto.

Si no cumple ninguna, la lámina se rehace sobre un arquetipo. Y un `style=` en el
HTML no es una excepción a esto: es la misma deuda escrita en otro lado. Hoy hay
42 en 19 láminas.

---

## 7. Antipatrones

Lo que hace que una lámina se lea como generada automáticamente. Casi todos
aparecieron en este deck y se corrigieron.

1. **Grilla de tres tarjetas iguales** para cosas que no son iguales. La simetría
   afirma equivalencia; si una opción es la elegida, dibujarla igual que las
   descartadas contradice el contenido.
2. **Ícono decorativo** de 24px dentro de un cuadradito redondeado de color. No
   informa, sólo llena.
3. **Numeración `01` `02` `03`** en ítems que no son una secuencia temporal.
4. **Píldoras de color como rótulo de rango** ("Alternativa 1", "Nuestro camino").
5. **Filetes horizontales decorativos.** Separar con aire. Una línea horizontal
   se justifica sólo si es contenido, como el riel de `.cadena`.
6. **Énfasis en todos lados**: la palabra en turquesa en cada titular, negritas
   cada dos renglones. Si todo destaca, nada destaca.
7. **Titular de revista** que anuncia en vez de nombrar.
8. **Pregunta retórica autocontestada.**
9. **Meta-comentario** sobre la propia presentación.
10. **Cifra suelta sin la condición** en que se midió.
11. **Simetría perfecta** como valor por defecto. Un diseño hecho por alguien
    tiene jerarquía: algo es más importante y se nota.
12. **Micro rótulo en mayúsculas con tracking ancho, más guion de color al
    costado.** Es el encabezado de toda landing page de producto de los últimos
    diez años. Se reemplazó en las 44 láminas por el romano numerado con color de
    sección (§2.3). **Todavía queda en la portada**, en los rótulos "Autores" y
    "Mentores".

La prueba práctica: **¿esta lámina podría estar en la presentación de cualquier
otro trabajo si le cambio las palabras?** Si la respuesta es sí, el formato no
está diciendo nada y hay que buscar la estructura que sí es propia de este
trabajo. La cadena de aterrizaje de S5 es el ejemplo: no es una lista de rasgos,
es el proceso real con el tramo propio marcado.

---

## 8. Antes de dar una lámina por cerrada

- [ ] La lámina es uno de los **seis arquetipos** (§5), o justifica por qué no.
- [ ] El cuerpo llega al **80%** de su alto (§6).
- [ ] No agregó clases de un solo uso fuera de un diagrama F (§6.1).
- [ ] El titular nombra el contenido y no lo anuncia.
- [ ] Hay como mucho un elemento coral.
- [ ] Ningún em dash (`grep -c '—'` da 0).
- [ ] Las cifras van con su condición de medición.
- [ ] Las figuras de distribución tienen epígrafe de lectura.
- [ ] No hay adorno que no informe.
- [ ] Entra sin desborde a **1280x720 y 1920x1080**.
- [ ] Sigue funcionando **offline** (sin `fetch`, sin recursos externos, rutas
      relativas).
- [ ] Si se agregó o movió una lámina, se renumeró `plan_presentacion.md`.
