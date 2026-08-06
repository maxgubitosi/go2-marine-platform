# Plan de la presentación — Defensa oral PF

**Formato:** página web (slides fullscreen, navegación con teclado), fondo claro, mínimo texto.
**Tiempo:** 30 min de exposición + 20 de preguntas. **Total: 34 slides + 10 de backup.**
**Estrategia narrativa:** embudo: arranca general para público no técnico, converge a técnico para el jurado. El momento bisagra es la slide 7 (la idea del "barco sintético"), y la 6 es la que presenta el robot para que esa bisagra no llegue en frío.

**Reparto tentativo** (Jack = movimiento del robot; resto a definir):

| Tramo | Slides | Presentador sugerido |
|---|---|---|
| Apertura → arquitectura | 1–9 | Máximo |
| Modelo marino y movimiento del robot | 10–12 | Jack |
| Percepción y evaluación | 13–16 | Máximo |
| Resultados simulación | 17–22 | Máximo |
| Laboratorio (obstáculos + resultados) | 23–30 | Jack |
| Lectura conjunta y cierre | 31–34 | Máximo (o ambos) |

> **Pasada global de titulares (28-07-2026).** Se reescribieron 26 de los 33 titulares para que digan lo que la lámina muestra en vez de funcionar como titular de revista, y se sacó la palabra en turquesa de todos salvo cinco, donde marca un término técnico que la lámina introduce. Fuera también las preguntas retóricas autocontestadas, los pares por antítesis y los pills de remate vagos.
>
> **Criterio para los titulares que se agreguen de acá en más:** que nombren el contenido o el hallazgo, no que lo anuncien. *"Caracterización dinámica: retardo τ y ganancia g"* sirve; *"Un error dinámico parametrizable"* no. Ver la memoria `registro-academico-no-gpteado`.
>
> **Ojo con el largo:** el titular entra en dos líneas a 1280x720. Si pasa de ~70 caracteres empuja el cuerpo y desborda. Si hace falta más precisión, la configuración del ensayo va en el eyebrow (así se resolvió en S19 y S20), no en el titular.

Presupuesto de tiempo: contexto+problema ~7 min · metodología ~8 min · resultados ~12 min · cierre ~3 min.

---

## Bloque 0 — Portada

**S1 · Portada**
- **Se ve:** tres franjas de arriba abajo, ocupando la pantalla completa. (1) Titular alineado a la izquierda: *"Simulación de dinámica de plataforma marina mediante un robot cuadrúpedo"*, con autores y mentores en dos columnas debajo. (2) Franja de mar animada de borde a borde, con el buque cabeceando. (3) Pie institucional con el logo UdeSA, "Ingeniería en Inteligencia Artificial" y "Departamento de Ingeniería · Universidad de San Andrés". Sin subtítulo explicativo.
- **Ojo:** el título de la portada ya **no** coincide con el del informe. Es una simplificación pedida para que entre en una línea de lectura.
- **Ojo:** el logo institucional va **al pie**, no arriba. Arriba compite con el titular y descoloca la lectura.
- **Se dice:** saludo y presentación del equipo (30 s).

## Bloque 1 — Contexto (público general)

**S2 · El barco como base móvil de un dron**
- **Se ve:** ilustración simple mar + embarcación + dron (animación SVG propia, estilo limpio). Tres íconos: búsqueda y rescate, inspección offshore, monitoreo marítimo.
- **Se dice:** el valor operativo — el barco como base móvil: más tiempo de misión, menos dependencia de costa.

**S3 · Los tres grados que mueven la cubierta**
- **Se ve:** dos animaciones SVG del mismo buque, lado a lado. **Vista de perfil** con flechas de *pitch* (arco en la proa) y *heave* (flecha vertical contra una referencia fija de cubierta). **Vista de proa** con el arco de *roll*. Las tres etiquetas van en coral, igual que sus flechas. Sin bullets: los términos viven en las captions.
- **Ojo:** el *roll* se ilustra de proa, no en vista cenital. Desde arriba lo que se ve girar es el *yaw*, no el balanceo.
- **Se dice:** el dron necesita saber en cada instante dónde está la cubierta y cómo está inclinada; la percepción visual cambia cuadro a cuadro.

**S4 · Tres vías de validación**
- **Se ve:** comparación visual de 3 caminos: banco mecánico a medida (lento/caro) · ensayo real (riesgoso) · **simulación + laboratorio (nuestro camino)**.
- **Se dice:** un error de estimación = colisión o pérdida del vehículo; necesitamos validar de forma segura, repetible y medible ANTES.

## Bloque 2 — Problema y objetivos (transición general → técnico)

**S5 · La cadena de aterrizaje y el tramo que cubre este trabajo**
- **Se ve:** la cadena completa dibujada de punta a punta sobre un solo riel: dinámica marina real · el torso del Go2 como cubierta · la cámara ve el marcador · pose relativa estimada · control y aterrizaje del dron. El riel va coral en las tres etapas centrales y gris en los dos extremos, que quedan fuera de alcance.
- **Se dice:** el alcance se explica por posición, no por lista. Aguas arriba no se modela la hidrodinámica del casco (interesa el efecto del oleaje sobre la pose, no su causa) y aguas abajo no se resuelve el aterrizaje. Lo que sí se hace es generar el movimiento, observarlo y medirlo, primero en simulación y después en el robot real.
- **Ojo:** el estado del arte quedó comprimido en el renglón de cierre (aterrizaje sobre plataformas móviles · marcadores fiduciales · validación en simulación). Si la cátedra lo pide con más entidad, se parte en dos láminas.

**S6 · El instrumento: un cuadrúpedo comercial**
- **Se ve:** a la izquierda, el render del Go2 en tres posturas distintas del torso (`go2_postures_trim.jpg`), con la caption que aclara que las cuatro patas siguen apoyadas. A la derecha, el conteo de grados de libertad como flowline (**18 coordenadas → −12 → quedan 6**), el pill coral *"los mismos seis con los que se describe una embarcación"*, y la vista del Go2 dentro de Gazebo (`sim_gazebo_go2.png`).
- **Por qué existe:** sin esta lámina el robot aparecía de la nada en la bisagra y la simulación no se mostraba nunca antes de S18. Las dos cosas rompían la narrativa.
- **El número viene del informe** (línea ~1780): de las 18 coordenadas (6 de la base flotante + 12 articulares), los cuatro apoyos sin deslizamiento remueven 12 y quedan exactamente 6, la pose del torso. Es la justificación formal de la equivalencia que S7 propone, y conviene tenerla dicha *antes*.
- **Ojo:** la mecánica articular fina va en S12 y en el backup B1. Acá sólo se cuenta.
- **Se dice:** qué es el Go2, que no nos interesa que camine sino que sostenga una inclinación, y que existe dos veces (modelo en Gazebo y unidad física en el laboratorio). Eso último es lo que habilita el "continuidad total" de S7.

**S7 · LA IDEA: un robot cuadrúpedo como barco sintético** ⭐ *(bisagra de la charla)*
- **Se ve:** lado a lado, con un "=" coral en el medio. A la izquierda, **dos** animaciones apiladas del mismo buque: de perfil (cabeceo y elevación) y de proa (balanceo), esta última reusando la escena de S3 pero **sin las flechas** (acá ilustra, no define los términos). A la derecha, video del Go2 real reproduciendo el mismo movimiento (videos_lab/03 primer plano).
- **Ojo:** falta el video de tercera persona del robot en simulación. No existe ninguno en el repo: los cuatro videos de sim son feeds de sensor (cámara fija y cámara inferior del dron, que es justo el ángulo cenital que no queremos). Conseguirlo implica volver a correr la simulación y grabar la pantalla de Gazebo desde un ángulo oblicuo. Ver backlog.
- **Se dice:** en vez de modelar una embarcación, usamos el torso actuado del Go2 para reproducir roll/pitch/heave. Bonus: el mismo robot existe en simulación y en el laboratorio → continuidad total.

**S8 · Objetivo y las dos preguntas de validación**
- **Se ve:** objetivo general arriba; abajo dos columnas: **SIMULACIÓN** — ¿el pipeline visual mide bien la pose? (pregunta de percepción) · **LABORATORIO** — ¿el robot real reproduce el movimiento? (pregunta de dinámica).
- **Se dice:** alcance explícito: NO resolvemos el aterrizaje completo; construimos la capa habilitante. Estas dos columnas estructuran todo lo que sigue.

## Bloque 3 — Metodología (técnico)

**S9 · Arquitectura del entorno**
- **Se ve:** diagrama de pipeline (`method_pipeline`) rediseñado para la web, con animación de flujo: simulador marino → Go2 → cámara (fija o dron) → detector ArUco → rosbag → evaluación offline.
- **Se dice:** recorrido de 1 minuto por los bloques; todo corre en ROS2 + Gazebo, todo queda registrado.

> **Las cuatro láminas que siguen se reconstruyeron el 28-07-2026** tras el feedback de Gastón Castro: *"tienen que entrar en la matemática y dar detalles técnicos claros"*, *"no pueden ser todos títulos generales y cajitas con flechas conceptuales"*. Antes eran cuatro `flowline` consecutivas con flechas y la matemática derivada al backup. Ahora cada una lleva las ecuaciones del informe, **citadas por su número real** para que el jurado pueda ir a buscarlas al texto.
>
> Las fórmulas se generan con `defensa/scripts/render_math.py` y se inyectan con `inline_math.py`. **Si se edita una de estas láminas hay que correr `inline_math.py --strip` primero**, editar, y volver a inyectar. La procedencia de cada fórmula está en `defensa/web/assets/math/PROCEDENCIA.md`.

**S10 · Modelo marino reducido**
- **Se ve:** la ecuación del estado reducido **(9)** como protagonista, completa: heave es la elevación de la superficie libre en el punto de la plataforma, y roll y pitch son sus dos derivadas parciales. Debajo, la tabla de símbolos. A la derecha, el campo de olas sinusoidal **(11)**. Al pie, la dinámica marina **(8)** apagada.
- **Se dice:** de los seis grados de libertad marinos retenemos tres, que son los que una cámara puede observar sobre un marcador plano.
- **Lo importante es lo que se declara que NO se hace:** la ecuación (8) se retiene sólo como marco conceptual y no se resuelven M, C, D ni g. El movimiento se sintetiza cinemáticamente, no se simula la hidrodinámica del casco. Decir esto explícito es lo que separa un alcance acotado de un agujero metodológico.

**S11 · Consigna sinusoidal y parámetros del ensayo** 🦿 *(Jack)*
- **Se ve:** las tres consignas `r(t)`, `p(t)`, `h(t)` y la tabla de parámetros del ensayo de referencia. A la derecha, `method_motion_components.png`, que es la misma figura del informe. Al pie, el filtro exponencial.
- **Esta lámina es el machete:** son los valores que hay que poder decir de memoria si el jurado pregunta con qué se corrió. **f = 0,10 Hz · A_r = ±15° · A_p = ±10° · A_h = ±0,10 m · κ_p = 1,0 · κ_h = 1,5 · desfase π/3 en pitch · α = 0,95.**
- **Se dice:** por qué el sinusoidal es el caso principal (repetible, cada hiperparámetro con efecto interpretable) y por qué los κ distintos y el desfase evitan que las tres componentes lleguen a sus extremos a la vez.

**S12 · Control postural: restricción de contacto** 🦿 *(Jack)*
- **Se ve:** la dinámica de base flotante **(14)**, la restricción de contacto **(15)**, el conteo `18 − 12 = 6` con *rank J_c* bajo el 12, la tabla de símbolos, el esquema de control postural y la cinemática inversa diferencial **(23)**.
- **Cierra el argumento que S6 abre:** en S6 el `18 − 12 = 6` es una cuenta; acá se ve de dónde sale el 12, que es el rango del jacobiano de contacto. Conviene decirlo enlazado.
- **Se dice:** con las cuatro patas apoyadas, cada una invierte su propio jacobiano para sostener la actitud pedida. El despeje en forma cerrada sigue en el backup B1.

**S13 · Estimación visual: ArUco + PnP**
- **Se ve:** la proyección pinhole **(2)**, los intrínsecos **(3)**, el `argmin` del error de reproyección **(6)** como protagonista, la tabla de símbolos y `camera_marker_geometry.png`.
- **Se dice:** el problema es sobredeterminado (cuatro correspondencias conocidas para seis incógnitas de pose). PnP no invierte nada: minimiza el error de reproyección. Con el marcador plano las esquinas son coplanares y la solución inicial sale de una homografía (ec. 4 y 5).

**S14 · Registro y evaluación offline**
- **Se ve:** la cadena de transformaciones **(26)** sola arriba, y debajo la tabla de marcos (c, w, bf, bl, a) con la explicación.
- **Se dice:** el simulador conoce cada eslabón, así que la pose verdadera se reconstruye sin medirla. De ahí salen Δroll, Δpitch y ΔZ.
- **Prepara S16:** en laboratorio esta cadena no existe porque no hay simulador que la publique. Esa es la razón de fondo del cambio de criterio de evaluación, y no una limitación de la cámara. Vale decirlo acá para que el pasaje al lab no parezca una excusa.

**S15 · Escenarios de observación en simulación**
- **Se ve:** lado a lado: el cuadro crudo de la cámara fija (`sim_escenario_fija.png`) vs el dron SJTU con su cámara inferior (`sim_escenario_dron.png`).
- **Se dice:** caso base (sensor quieto = pregunta limpia) vs caso fuerte (sensor volando = geometría exigente). Diseño deliberado para separar preguntas.
- **La asimetría es a propósito:** a la izquierda va lo que *ve* el sensor y a la derecha la *geometría* de la escena. Se probó poner los dos feeds crudos (`fotos_sim/01` y `fotos_sim/02`) y son casi idénticos entre sí, así que el contraste que el slide quiere hacer se perdía.
- **Ojo con las imágenes:** las dos van recortadas a la misma relación 3:2 con `defensa/scripts/crop_escenarios.py`. Los originales tienen relaciones distintas, y en columnas de igual ancho cualquier diferencia hace que una caja salga más alta, desborde el cuerpo del slide y se superponga con el párrafo de cierre. Si se cambia alguna de las dos imágenes, hay que volver a pasarlas por el script.
- **Resolución:** el recorte de cámara fija queda en 315 px de ancho y se muestra a 494 en 720p (1,56x). Es lo mejor disponible: el original es de 640x480 y casi todo el cuadro es fondo vacío.

**S16 · Del simulador al robot real: qué cambia** 🦿 *(Jack, opcional Máximo)*
- **Se ve:** a la izquierda la tabla sim vs lab: ground truth perfecto → no hay · cámara ideal → webcam en trípode · comando directo → API del robot + control interno. A la derecha el mismo montaje dos veces, con una flecha en el medio: el Go2 con el marcador dentro de Gazebo (`sim_setup_gazebo.png`) y la foto del laboratorio con el trípode (`lab_go2_aruco_tripode_a.jpg`).
- **Se dice:** las dificultades del pasaje y la decisión metodológica clave: en el lab evaluamos movimiento y visión POR SEPARADO (evitar saturación de cómputo que contamine registros). La flecha es el gesto que acompaña todo el bloque: lo que se armó en el simulador es lo que después se montó en el piso del laboratorio.
- **Ojo con las imágenes:** las dos van en 3:4 para que los paneles midan igual y la flecha se lea como correspondencia. La de Gazebo se recorta a esa relación con `defensa/scripts/crop_setup_sim.py`. La del laboratorio ya está en 3:4, pero **el archivo se ve apaisado si se lo abre a mano**: trae orientación EXIF 6 y es el navegador el que la endereza. No re-exportarla sin conservar ese metadato.
- **Los epígrafes tienen que entrar en una línea** (*"El montaje en Gazebo"* y *"Y en el laboratorio"*). Si se alargan y uno envuelve a dos líneas, las dos fotos se desalinean verticalmente.

## Bloque 4a — Resultados: simulación

**S17 · Campaña experimental**
- **Se ve:** tabla simple: 1 caso base (cámara fija, 57,5 s) + 3 repeticiones con dron (R1–R3, ~57 s c/u). Misma consigna, mismo postproceso.
- **Se dice:** el diseño busca repetibilidad, no acumulación: 3 corridas comparables para descartar que la lectura dependa de una corrida con suerte.

**S18 · El pipeline en acción (video)**
- **Se ve:** video `videos_sim/01` (cámara fija + detección con overlay) a pantalla generosa; miniatura del contexto Gazebo al lado.
- **Se dice:** narración en vivo sobre el video: el marcador sube, baja y se inclina; los ejes dibujados son la estimación en tiempo real.

> **Bloque de resultados reconstruido (28-07-2026).** Los números héroe sueltos se reemplazaron por las distribuciones que el informe ya reporta. Tres histogramas (`sim_fixed_error_hist`, `sim_drone_error_hist`, `lab_error_hist`) **ya estaban en el deck pero sólo en las láminas de backup**: se los trajo al frente y se borraron las copias `bk_` duplicadas, que eran byte a byte iguales.
>
> **Criterio:** toda cifra va con la condición en la que se midió (corrida, N, amplitud de consigna) y toda figura de distribución lleva un epígrafe que dice cómo leerla, no que la repite.

**S19 · Error de posición y de actitud con cámara fija**
- **Se ve:** serie temporal contra referencia y, al lado, la distribución de ΔX, ΔY, ΔZ y del error euclidiano (`sim_fixed_error_hist.png`). Debajo, N = 275 muestras útiles sobre 57,5 s, con tasa de detección de 4,78 Hz.
- **Lo que hay que decir sí o sí:** los histogramas son **crudos**, sin compensar el desfase temporal entre la estimación visual y el ground truth, que se reconstruye a otra frecuencia y se alinea por marca temporal. Parte del corrimiento respecto de cero es ese retardo entre cadenas, no error geométrico del estimador. Está en la franja al pie y es justo la distinción que un jurado busca.
- **Se sacó la cifra héroe de 5,8 cm suelta.** Sigue estando en la síntesis de S31, ahí como resumen.

**S20 · Degradación del error con el sensor en movimiento**
- **Se ve:** video corto `videos_sim/02` (detección desde el dron), la orientación estimada contra ground truth y la distribución de errores crudos (`sim_drone_error_hist.png`).
- **Se dice:** la nube abre respecto del caso fijo, y eso es el costo de la geometría de observación, no una falla del estimador.

**S21 · Repetibilidad entre corridas**
- **Se ve:** la banda de cifras (2–3° en roll/pitch · 2–2,4 cm en heave) y los diagramas de caja de |Δroll|, |Δpitch| y |Δheave| para R1 a R3.
- **Cómo leer la figura:** lo que importa no son las medianas sino **que las tres cajas se solapen**. Eso es lo que dice que el resultado no depende de la corrida. Está escrito en el epígrafe.

**S22 · Alcance y limitaciones de la validación en simulación**
- **Se ve:** 2 columnas: ✅ el pipeline sigue la dinámica global, medible contra referencia / ⚠️ heave es el eje más sensible, sesgo sistemático en Y (limitación de la cadena geométrica, no movimiento real).
- **Se dice:** admitir limitaciones con precisión — para eso sirve la simulación: aislarlas con ground truth antes del mundo físico.

## Bloque 4b — Resultados: laboratorio 🦿 *(Jack)*

**S23 · Lo que la simulación no anticipó** 🧱 *(bisagra sim → lab)*
- **Se ve:** tres filas obstáculo → adaptación. (1) Conectarnos al robot → refactor de la capa de comunicación. (2) Guardrail de marcha: el Go2 trota en el lugar para reasegurar estabilidad → barrido de frecuencias, a menor frecuencia el trote se espacia (no se elimina). (3) Sin acceso al firmware → no se pudo corregir la dinámica, se la midió (τ, g).
- **Se dice:** en simulación salió bien; al enchufar el robot real aparecieron tres muros. Las dos últimas limitaciones explican los números de S26–S27. Punto marcado por los mentores (Gastón / Juan) — no es una disculpa, es la justificación de las decisiones de diseño experimental.
- **Backup asociado:** B9 (guardrail de gait) y B10 (movimiento trabado / firmware).

**S24 · El montaje real**
- **Se ve:** video `videos_lab/08` (setup completo: trípode + cámara cenital + Go2 con ArUco haciendo posturas) o fotos `fotos_lab/04`–`06`.
- **Se dice:** mismo concepto que en Gazebo, con hardware real: webcam en trípode, marcador en el lomo, consigna marina por la API del Go2.

**S25 · El torso del Go2 sigue la consigna marina (video estrella)** ⭐
- **Se ve:** video `videos_lab/02` (operador comanda → Go2 ejecuta posturas marinas, 34 s, recortado a ~15 s) a pantalla completa.
- **Se dice:** esto es el resultado central del lab en una imagen: la consigna de oleaje moviendo un robot real.

**S26 · Fidelidad del comando: qué le llega a la API**
- **Se ve:** `lab_plot_02_api_fidelity.png` + cifra héroe: **correlación > 0,9999** entre consigna esperada y comando enviado.
- **Se dice:** primer eslabón validado: nada se pierde ni deforma en el camino de software hasta la API del robot.

**S27 · Seguimiento: actitud medida contra consigna**
- **Se ve:** `strong_15_10_plot_01_timeseries_cmd_vs_real.png` (R4: series roll y pitch, esperado vs real).
- **Se dice:** el robot reproduce la FORMA del movimiento — se ve a ojo en las series — pero con retardo y menor amplitud. Eso es física, no falla.

**S28 · Caracterización dinámica: retardo τ y ganancia g**
- **Se ve:** el modelo de respuesta θ_real(t) ≈ g·θ_cmd(t − τ) + b, renderizado con la misma tipografía que el resto, y la **tabla completa R4 contra R5** del informe: consigna, retardo óptimo, correlación máxima y ganancia, por eje. Al lado, `lab_lag_correlation.png`.
- **Por qué la tabla y no los rangos:** dos ensayos a amplitudes distintas dando el mismo patrón es lo que convierte esto en caracterización y no en anécdota. Con los rangos sueltos (0,45 a 0,95 s) esa réplica se perdía, que era justamente lo más fuerte del resultado.
- **Se dice:** la limitación se enuncia como hipótesis con evidencia, no como causa probada. Ver backlog.

**S29 · La forma bimodal del residual es consecuencia de la atenuación**
- **Se ve:** `lab_error_hist.png` con Δroll y Δpitch, ya compensado el retardo físico de cada eje (0,58 s y 1,16 s). Al lado, media (−0,77° y +0,55°) y dispersión (3,86° y 2,93°).
- **Es la lámina más fuerte del bloque.** No se limita a mostrar la distribución: explica su forma. Las dos quedan centradas cerca de cero, así que **no hay sesgo sistemático de actitud**, pero la frecuencia se acumula hacia los extremos en vez de alrededor de la media. Esa estructura bimodal es la huella de la atenuación: al restar una sinusoide atenuada de la consigna queda otra sinusoide, y el histograma de una sinusoide se concentra en los picos, no en el centro. Es consistente con la ganancia g ≈ 0,47 de S28.
- **Si el jurado pregunta una sola cosa del laboratorio, es probable que sea por acá.**

**S30 · El pipeline visual también corre en el lab**
- **Se ve:** frames `lab_aruco_realtime_t00/t26/t49.png` (secuencia) + clip corto de `videos_lab/07` (detección en pantalla en vivo).
- **Se dice:** la detección ArUco funciona sobre el robot real con la cámara del montaje; se evaluó por separado del movimiento (decisión metodológica de S16).

## Bloque 5 — Cierre

**S31 · Lectura conjunta: dos piezas de una misma validación**
- **Se ve:** diagrama de dos piezas de puzzle: SIM = percepción (si el robot se mueve perfecto, la visión mide con cm de error) + LAB = dinámica (el robot real sigue la consigna con retardo/ganancia medibles). Pieza faltante marcada: **ambos a la vez**.
- **Se dice:** mismo régimen en ambos entornos (0,10 Hz, ±10–20°) — que los dos experimentos sean ejecutables con la misma plataforma ya es un resultado.

**S32 · Conclusiones**
- **Se ve:** 3 eslabones con check: el simulador genera movimiento representativo ✓ · el robot lo reproduce de forma consistente ✓ · el pipeline visual lo mide ✓. Frase: "no un sistema de aterrizaje: una base de investigación".
- **Se dice:** objetivo cumplido; afirmación moderada pero sólida; límites ya admitidos en S22/S26.

**S33 · Trabajo futuro**
- **Se ve:** roadmap visual en 4 pasos: validación conjunta (visión + movimiento simultáneos) → ground truth externo (OptiTrack) → heave dinámico + yaw/surge/sway + oleaje irregular → aproximaciones de aterrizaje sobre el Go2.
- **Se dice:** la línea inmediata es cerrar la pieza faltante de S30; misma lógica de siempre: complejidad gradual con trazabilidad.

**S34 · Cierre y preguntas**
- **Se ve:** foto del equipo con el robot (pendiente de conseguir; fallback: `fotos_lab/07` + foto de Máximo, o la panorámica del sistema). Agradecimientos. "¿Preguntas?"
- **Se dice:** agradecimiento breve a mentores y laboratorio.

## Backup — 10 slides construidas (tecla `B`)

- **B1** Estructura articular del Go2.
- **B2** Cinemática inversa de pata (IK analítica).
- **B3** Marcos de referencia y transformaciones.
- **B4** Grafo del sistema ROS2.
- **B5** Histogramas de error (simulación).
- **B6** Sesgo sistemático en Y (escenario dron): hipótesis y evidencia.
- **B7** Dos amplitudes: R4 y R5.
- **B8** Identificadores de registros / rosbags.
- **B9** 🧱 **El guardrail de gait** — síntoma / interpretación / evidencia (`lab_real_20260320_112522_trote_robot_full`) / consecuencia sobre el régimen de ensayo.
- **B10** 🧱 **Movimiento trabado y acceso al firmware** — síntoma / qué se descartó (fidelidad > 0,9999) / hipótesis / cómo se verificaría (OptiTrack + barrido de frecuencia).

*Ideas de backup aún no construidas:* por qué Go2 y no una plataforma Stewart o un gimbal; parámetros exactos del modelo de oleaje; detalle formal de PnP y calibración; arquitectura de comunicación antes/después del refactor.

---

## Decisiones de diseño web (a validar)

1. **Navegación:** flechas/teclado + barra de progreso con los 5 bloques visibles (el jurado siempre sabe dónde estamos). Tecla `B` salta a backup.
2. **Videos:** autoplay silencioso al entrar a la slide, loop en clips cortos. Todos convertidos a H.264 MP4, self-contained (funciona sin internet).
3. **Animaciones propias:** oleaje SVG (S2–S3), pipeline animado (S9), puzzle (S30). Sobrias, sin distraer.
4. **Cifras héroe:** los números clave (5,8 cm · 2–3° · 0,9999 · 0,62) en tipografía gigante — legibles desde el fondo del aula.
5. **Paleta tentativa:** fondo claro casi blanco, tinta azul marino profundo + un acento (a definir: coral/cian), tipografía sans-serif. Identidad "marina" sutil sin caer en cliché náutico.
6. **Export PDF de respaldo** por si falla todo el día de la defensa.

## Pendientes de material

- **Video o clip del robot en trote / moviéndose "trabado"** — sería el activo más fuerte para S23. Ninguno de los 8 clips de laboratorio curados lo muestra: todos son posturas que salen bien.
- Foto de los dos autores con el robot (S34) — **confirmado que no existe**; S34 usa la vista cenital como fallback.
- Video del Go2 con heave (mejoraría S25; no bloquea).
- ~~Nombres de mentores~~ — Gastón Castro (mentor) · Juan Ignacio Giribet (comentor). ✅

Ver **`backlog.md`** para lo que queda abierto (informe sin documentar las limitaciones, justificación de los 0,10 Hz, export PDF, reparto).
