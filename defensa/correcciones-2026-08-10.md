# Correcciones del 10-08-2026 y plan de rework

Devolución de Gastón y Juan sobre el deck presentado el 10 de agosto, más las
notas que tomamos Máximo y Jack. Este documento es la fuente de verdad del
rework: qué pidieron, qué decidimos, en qué orden lo hacemos y qué falta
resolver. `plan_presentacion.md` sigue describiendo el deck lámina por lámina;
cuando el rework termine, hay que volcar ahí el resultado.

---

## 1. La devolución, textual

> * Pasar la presentación a wide y mayor tamaño de letras
> * El contenido de las slides tiene que ser afín al orden discursivo de cómo van a decir las cosas
> * Dividir mejor el diagrama de qué es simulación y qué es realidad. Identificar qué partes son el sistema de retroalimentación y control que proponen ustedes (y que es reutilizable en ambos casos sim/real), remarcar eso porque habla del aporte y sistema que programaron. Consigna -> Procesamiento de imagen: Detección del marker + PnP -> Resolución de consigna a pose -> envío de comandos al quad
> * Las slides de entorno de pruebas de 14 a 21, deberían ser 3 o 4 slides max
> * Gráficos de resultados, importante que se vean bien para poder indicar y decir lo que quieren notar
> * Partir slides de resultados si se necesita el espacio para agrandar las imágenes
> * No vuelvan a explicar o mostrar setup de experimentos, una vez que entran en resultados mantengan la centralidad en los resultados cuantitativos
> * Juntar limitaciones y experiencias del trabajo en una slide con bullets
> * Cerrar con conclusiones
>
> En términos generales el esquema es: Intro -> Modelado -> Setup de Experimentos -> Resultados -> Limitaciones + Conclusiones

Referencias visuales que pasaron: `docs/media/ejemplo-pipeline.png` (diagrama
Verilator sim/real) y `docs/media/ejemplo-pipeline2.png` (el diagrama clásico de
Gazebo + ROS + ros_control de Dave Coleman). Los dos son diagramas de bloques
con **la frontera simulación / realidad dibujada explícitamente** y el software
propio compartido entre las dos ramas. Eso es el modelo a seguir para la
lámina 7.

---

## 2. Chequeo de numeración

Las notas usan la numeración del deck **de hoy** (37 láminas en el hilo, después
del merge del PR #4 de metodología). Lo verifiqué cruzando contenido, no
posición:

| Nota | Cae en | ¿Coherente? |
|---|---|---|
| "23: video de dron despegando" | 23 · Error con cámara en el dron | sí |
| "25-26: juntar" | 25 · Alcance y limitaciones + 26 · Lo que la simulación no anticipó | sí, las dos son limitaciones |
| "27-28: eliminar o juntar y mover" | 27 · El montaje real + 28 · El torso sigue la consigna | sí, son las dos de setup metidas dentro de resultados |
| "34-35: juntar conclusiones" | 34 · Lectura conjunta + 35 · Conclusiones | sí |
| "14-19/21" (mentores: "de 14 a 21") | 14 a 19 son setup puro; 20-21 abren resultados | sí |

**Una sola ambigüedad:** "30: retardo dejar". Hoy 30 es *Comando vs respuesta
física* y 31 es *Cuantificando: retardo y ganancia*. Las dos hablan del retardo.
Asumo que se refiere a las dos y que ninguna se toca. **Confirmar.**

---

## 3. Diagnóstico del punto transversal (wide + tamaño de letra)

Los dos pedidos son el mismo problema y tienen la misma causa: los topes del CSS
se calibraron para un lienzo de ~1220 px y nunca se levantaron para una
proyección 16:9 real.

Medido a 1920×1080:

| | Valor | |
|---|---|---|
| Ancho de pantalla | 1920 px | |
| Padding lateral (`--pad`) | 88 px × 2 | |
| Ancho utilizable | 1744 px | |
| Ancho real del contenido (`--maxw`) | **1214 px** | topeado en `1220px` |
| **Desperdiciado** | **530 px** | **30% del ancho útil** |

Por eso se ve "no wide": hay 265 px de margen muerto a cada lado que ninguna
lámina usa.

La tipografía tiene la misma raíz. Los `clamp()` escalan con `vw` pero el tope
corta antes de llegar a 1920:

| Elemento | A 1920 | Tope que lo corta | Lo que daría el `vw` |
|---|---|---|---|
| `h2.head` | 50 px | `3.1rem` | 4,2vw = 80 px |
| `.lead` | 24 px | `1.5rem` | 1,7vw = 33 px |
| `.eyebrow` | 15 px | fijo `.95rem` | — |

**Consecuencia de orden:** esto hay que hacerlo **primero**, antes de rehacer
contenido. Cambia cuánto entra en cada lámina, así que si se rehace una lámina
antes del cambio de escala hay que volver a maquetarla después. También puede
resolver sola alguna de las fusiones pedidas: con 530 px más de ancho, dos
láminas que hoy no entran juntas quizá sí entren.

---

## 4. Estructura objetivo

El esquema que pidieron contra lo que tenemos hoy:

| Bloque pedido | Hoy | Láminas hoy | Estado |
|---|---|---|---|
| Intro | b0 Introducción + b1 Problema | 2-6 | ok |
| Modelado | b2 Metodología (primera mitad) | 7-13 | 7 se rehace, 8-9 se iteran |
| Setup de Experimentos | b2 Metodología (segunda mitad) | 14-19 | **6 → 3 o 4** |
| Resultados | b3 Resultados | 20-33 | sacar setup, agrandar gráficos |
| Limitaciones + Conclusiones | b3 (25-26) + b4 | 25-26, 34-37 | juntar |

**Decisión pendiente:** hoy `data-block="2"` es un solo bloque "III ·
Metodología" que cubre modelado *y* setup. El esquema pedido los separa. Si los
separamos de verdad, el deck pasa de 5 a 6 bloques y hay que renumerar los
romanos del encabezado y agregar un color de sección. Es coherente con lo que
pidieron y hace más legible el riel de progreso, pero toca las 37 láminas.
**Decidir antes de empezar la fase B.**

Tamaño objetivo estimado: **~28 láminas en el hilo** (hoy 37).

---

## 5. Plan por fases

El orden no es arbitrario: lo transversal primero porque cambia la maqueta de
todo, después el contenido de adelante hacia atrás porque el orden discursivo se
define desde el principio.

### Fase A — transversal (bloquea todo lo demás)

- **A1.** Subir `--maxw` y recalibrar `--pad` para que el contenido use el ancho
  real de una proyección 16:9. Verificar las 37 láminas a 1280×720, 1440×810 y
  1920×1080.
- **A2.** Subir la escala tipográfica: topes de `h2.head`, `.lead`, `.eyebrow`,
  cuerpo de tablas y `figcaption`. Criterio: legible desde el fondo de un aula,
  no desde una notebook.
- **A3.** Pasada de regresión visual por las 37 láminas y arreglo de lo que se
  rompa.

### Fase B — Intro y Modelado (láminas 2-13)

- **B1.** ~~Lámina 6: reemplazar la foto de simulación~~ **hecho** (ver §7).
- **B2.** **Lámina 7, el diagrama.** Es el pedido más cargado de contenido:
  tiene que separar simulación de realidad y marcar qué construimos nosotros.
  Las dos decisiones de fondo ya están tomadas (dos cadenas paralelas, patrón de
  cajas · §6); queda definir el contenido exacto de cada bloque.
- **B3.** **Láminas 8-9, modelado.** Iterar. Requiere revisión teórica previa
  (§6).
- **B4.** **Lámina 13** (*El patrón articular*): no nos convence, rehacer.
  Definir qué tiene que decir antes de maquetarla.

### Fase C — Setup de experimentos (láminas 14-19 → 3 o 4)

Las seis de hoy: *Escenarios de observación*, *Estimación visual ArUco + PnP*,
*Registro y evaluación offline*, *Implementación en ROS2*, *El sensor del
laboratorio*, *Cambia la referencia, cambia la pregunta*.

Agrupación propuesta, a validar:

1. **Qué observa la cámara** — escenarios (fija / dron) + el sensor del lab.
2. **Cómo se estima la pose** — ArUco + PnP.
3. **Cómo se registra y se evalúa** — ROS2, rosbag, evaluación offline, y qué
   hace de referencia en cada montaje (absorbe *Cambia la referencia*).

Lo que no entre va a backup, no se borra.

### Fase D — Resultados (láminas 20-33)

- **D1.** Sacar el setup de adentro de resultados: 27-28 se eliminan o se mueven
  a la fase C. 29 se elimina.
- **D2.** Agrandar los gráficos. Partir láminas donde haga falta espacio, que
  los mentores lo autorizaron explícitamente.
- **D3.** Al lado de cada resultado, una referencia mínima del experimento que
  lo produjo (Gastón dijo sacar el setup, pero que quede como auxiliar: un
  rótulo o una miniatura, no una lámina).
- **D4.** Lámina 23 como patrón de layout de resultado (es la que más les
  gustó). Sumarle, si conseguimos el material, el video del dron despegando.
- **D5.** Lámina 24 (*Repetibilidad entre corridas*): no cierra, rehacer.
  Lámina 32 (*Residual de actitud R5*): arreglar. Lámina 33: editar o mover.
- **D6.** Poner el video de cámara fija en resultados.

### Fase E — Limitaciones y cierre (25-26, 34-37)

- **E1.** Una sola lámina de limitaciones y experiencias, con bullets, juntando
  25 y 26. Acá entran las tres limitaciones que ya están en `backlog.md` §1
  (guardrail de gait, firmware cerrado, refactor por el problema de conexión).
- **E2.** Juntar 34-35 en conclusiones y mejorarlas. Cerrar con conclusiones,
  no con trabajo futuro.

### Fase F — pasada de orden discursivo

Con el deck ya armado, recorrerlo leyendo en voz alta y ajustar para que cada
lámina muestre lo que se dice **cuando** se dice. Es la corrección más difusa de
las que dieron y la única que no se puede verificar mirando el deck quieto.

---

## 6. Lo que hay que resolver antes de tocar 7, 8 y 9

Decisión tomada: **antes de maquetar estas tres hacemos una revisión teórica a
fondo.** Lo que hay que dejar cerrado:

### Lámina 7 — el diagrama

- **Qué es exactamente "nuestro aporte"** en términos de bloques, y cuáles de
  esos bloques corren igual en simulación y en laboratorio. Hoy la lámina lo
  cuenta como "una sola arquitectura, en el laboratorio se sustituyen tres de
  las seis etapas", que es la misma idea pero contada desde lo que cambia en vez
  de desde lo que aportamos. **Sigue abierto**, es el contenido de los bloques.
- **DECIDIDO (10-08): son dos cadenas paralelas, no un lazo.** La cadena que
  dictaron (*consigna → detección + PnP → resolución de consigna a pose →
  comandos al quad*) se lee como un lazo cerrado por visión. En nuestro sistema
  la visión **no** cierra el lazo: el control postural es a lazo abierto desde la
  consigna sinusoidal, y la estimación ArUco + PnP es el observador que estamos
  validando, evaluado offline contra ground truth. El diagrama tiene que mostrar
  las dos cadenas en paralelo, no encadenadas:

  - **cadena de actuación** — consigna marina → pose del torso → cinemática
    inversa → comandos a las articulaciones;
  - **cadena de observación** — imagen → detección del marcador + PnP → pose
    estimada → evaluación contra la referencia.

  No hace falta consultarlo con ellos: dibujarlo bien es la corrección. Si
  preguntan en la defensa por qué no es el lazo que dictaron, la respuesta es
  que ese lazo es el de la aplicación final (aterrizaje) y que este trabajo
  valida por separado las dos piezas que ese lazo necesita.

- **DECIDIDO (10-08): pasamos al patrón de cajas.** Los dos ejemplos que pasaron
  usan cajas contenedoras rotuladas con la frontera simulación / realidad
  dibujada explícitamente. El riel actual (dos filas con sustituciones) queda
  reemplazado. Lo que hay que conservar del riel al migrar: que se lea que **es
  el mismo software** el que corre de los dos lados, que es justamente el aporte
  que los mentores quieren ver remarcado. En el patrón de cajas eso se dibuja
  como un bloque propio compartido, con las dos cajas de sustrato (Gazebo /
  mundo real) conectándose a él, que es exactamente lo que hace el diagrama de
  ros_control del ejemplo 2.

### Láminas 8-9 — modelado

Contenido actual: la 8 tiene el estado reducido (ec. 9), el campo de olas
(ec. 11), la clave de símbolos y el balance de fuerzas descartado; la 9 tiene la
consigna sinusoidal, la tabla de parámetros (f, A_r, A_p, A_h, κ), el gráfico de
componentes y el suavizado exponencial.

A revisar:

- Si el reparto entre las dos es el correcto, o si conviene *modelo* en una y
  *consigna concreta* en la otra.
- Cuánta matemática sostener en pantalla. Hoy hay cuatro ecuaciones renderizadas
  y las láminas de backup tienen más. El criterio de los mentores ("afín al
  orden discursivo") sugiere dejar sólo lo que se va a decir en voz alta.
- La justificación de los 0,10 Hz sigue abierta en `backlog.md` §2 y cae
  justo acá.
- Qué pasa con κ_φ, κ_θ: son el parámetro que dice "cuánto acompaña la
  plataforma la pendiente local" y no está claro que se explique en voz alta.

---

## 7. Hecho

- **Lámina 6** — la foto de simulación pasa a ser el montaje real con la
  plataforma y el marcador sobre el torso (`sim_montaje_aruco.png`), en lugar
  del Go2 solo. Fuente en `docs/media/montaje_aruco_sim.png`, recorte
  reproducible en `defensa/scripts/crop_montaje_aruco_sim.py`. Se recortó para
  que el robot ocupe lo mismo que en la foto del laboratorio: con el encuadre
  original el mismo robot se leía la mitad de grande de un lado que del otro.

---

## 8. Preguntas abiertas

1. "30: retardo dejar" — ¿30, 31, o las dos? (§2)
2. ¿Separamos Metodología en dos bloques (Modelado / Setup) con romano y color
   propios? (§4)
3. ¿Tenemos material para el video del dron despegando que pide la nota de la
   lámina 23?
4. ¿El deck se proyecta a 1920×1080 o a otra resolución? La fase A se calibra
   con ese número.

### Cerradas

- **La cadena dictada para la lámina 7** (10-08): se refiere a nuestro sistema y
  son dos cadenas paralelas, no un lazo. Lo corregimos en el diagrama sin
  consultarlo. Ver §6.
- **Riel o cajas** (10-08): cajas. Ver §6.
