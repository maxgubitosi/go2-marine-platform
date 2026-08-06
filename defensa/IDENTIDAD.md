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
grep -c 'class="head".*accent' defensa/web/index.html    # no debería pasar de 5
```

### 2.3 Eyebrow (`div.eyebrow`)

Es la ubicación en la charla, no un título alternativo. De S9 en adelante sigue
el patrón `Bloque · Subtema` (*Metodología · Percepción*, *Resultados · Cámara
fija*), que es el que conviene extender.

Va en mayúsculas por CSS: escribirlo en capitalización normal en el HTML.

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
grep -c '—' defensa/web/index.html defensa/web/css/style.css   # tiene que dar 0
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
| `--coral` | `#ef6a4c` | **señal**: lo que hay que mirar |
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
| eyebrow y rótulos | 0,74 a 0,82rem, mayúsculas, `letter-spacing .12em` | 600 |

**La mono es para datos, nunca para prosa:** cifras, identificadores, tópicos ROS,
nombres de archivo, ecuaciones en línea. Un párrafo en mono es un tic de terminal
y no aporta nada.

Ancho de línea: entre 32ch y 48ch en columnas. Más que eso cansa a la distancia
de proyección.

---

## 5. Tipos de lámina

| Tipo | Cuándo | Con qué |
|---|---|---|
| Portada | una | `.cover-*`, franja de mar a sangre |
| Concepto ilustrado | contexto para público general | SVG propio, `.escenas` |
| Par comparativo | sim contra lab, dos configuraciones | `.split`, `.simreal`, `.scenerow` |
| Diagrama de proceso | pipeline, cadena, alcance | `.cadena`, `.flowline`, `.pipeline` |
| Matemática | metodología | `.eq` + tabla de símbolos + cita al informe |
| Resultado con figura | resultados | `.res-fig` + epígrafe de lectura |
| Tabla | campañas, trazabilidad | `table` |
| Decisión | comparar opciones no equivalentes | `.decision` |
| Backup | respuestas a preguntas previsibles | igual que las anteriores, después de S34 |

**Una lámina, una idea.** Si hacen falta dos titulares para describirla, son dos
láminas. Y antes de dar por floja una lámina, revisar si su versión sustanciosa
**ya existe en el backup**: pasó dos veces (la matemática de metodología y los
histogramas de error).

---

## 6. Componentes

Inventario de lo que ya existe, para no reinventar. Cada uno tiene su bloque
comentado en `css/style.css`.

| Clase | Qué es | Cuándo NO usarlo |
|---|---|---|
| `.escenas` | tres ilustraciones con título y bajada corta | si las tres cosas no son comparables entre sí |
| `.decision` | opciones descartadas en gris, elegida con barra coral | si las opciones sí son equivalentes |
| `.cadena` | proceso completo con el tramo propio marcado en el riel | si no hay un proceso lineal real detrás |
| `.split` | media a un lado, texto al otro | si la imagen no aporta información |
| `.eq` | ecuación en SVG pre-renderizado | nunca escribir la fórmula a mano en HTML |
| `.pill` | etiqueta de dato (ROS2, Gazebo, una cifra) | como remate de lámina o como rótulo de rango |
| `.cards` | grilla de tarjetas | cuando los ítems no son equivalentes, que es casi siempre |
| `.hero-num` | cifra grande | en resultados |

Sobre `.cards`: queda en uso en cinco láminas, pero **es el componente con más
riesgo de leerse como plantilla**. Antes de usarlo, preguntarse si los ítems son
realmente intercambiables. Si uno de ellos es la conclusión, no lo son.

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

La prueba práctica: **¿esta lámina podría estar en la presentación de cualquier
otro trabajo si le cambio las palabras?** Si la respuesta es sí, el formato no
está diciendo nada y hay que buscar la estructura que sí es propia de este
trabajo. La cadena de aterrizaje de S5 es el ejemplo: no es una lista de rasgos,
es el proceso real con el tramo propio marcado.

---

## 8. Antes de dar una lámina por cerrada

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
