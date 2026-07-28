# Plan de la presentación — Defensa oral PF

**Formato:** página web (slides fullscreen, navegación con teclado), fondo claro, mínimo texto.
**Tiempo:** 30 min de exposición + 20 de preguntas. **Total: 31 slides + 10 de backup.**
**Estrategia narrativa:** embudo — arranca general para público no técnico, converge a técnico para el jurado. El momento bisagra es la slide 6 (la idea del "barco sintético").

**Reparto tentativo** (Jack = movimiento del robot; resto a definir):

| Tramo | Slides | Presentador sugerido |
|---|---|---|
| Apertura → arquitectura | 1–8 | Máximo |
| Metodología de movimiento | 9–10 | Jack |
| Percepción y evaluación | 11–14 | Máximo |
| Resultados simulación | 15–20 | Máximo |
| Laboratorio (obstáculos + resultados) | 21–27 | Jack |
| Lectura conjunta y cierre | 28–31 | Máximo (o ambos) |

Presupuesto de tiempo: contexto+problema ~7 min · metodología ~8 min · resultados ~12 min · cierre ~3 min.

---

## Bloque 0 — Portada

**S1 · Portada**
- **Se ve:** título del PF, nombres + mentores, logo UdeSA, fecha. De fondo, sutil: loop corto del Go2 en posturas (videos_lab/03) o imagen `fig_panoramica_tesis.png`.
- **Se dice:** saludo y presentación del equipo (30 s).

## Bloque 1 — Contexto (público general)

**S2 · ¿Por qué aterrizar drones sobre barcos?**
- **Se ve:** ilustración simple mar + embarcación + dron (animación SVG propia, estilo limpio). Tres íconos: búsqueda y rescate, inspección offshore, monitoreo marítimo.
- **Se dice:** el valor operativo — el barco como base móvil: más tiempo de misión, menos dependencia de costa.

**S3 · El problema: la cubierta nunca está quieta**
- **Se ve:** animación del oleaje moviendo una plataforma con los tres ejes etiquetados: **roll, pitch, heave** (versión animada de `fig_wave_platform_diagram.jpeg`). Interactivo opcional: slider que mueve la plataforma.
- **Se dice:** el dron necesita saber en cada instante dónde está la cubierta y cómo está inclinada; la percepción visual cambia cuadro a cuadro.

**S4 · ¿Por qué no probar directo en el mar?**
- **Se ve:** comparación visual de 3 caminos: banco mecánico a medida (lento/caro) · ensayo real (riesgoso) · **simulación + laboratorio (nuestro camino)**.
- **Se dice:** un error de estimación = colisión o pérdida del vehículo; necesitamos validar de forma segura, repetible y medible ANTES.

## Bloque 2 — Problema y objetivos (transición general → técnico)

**S5 · ¿Qué se hizo antes? (estado del arte en 1 lámina)**
- **Se ve:** 3 tarjetas: aterrizaje autónomo sobre plataformas móviles · marcadores fiduciales (foto de un ArUco) · validación en simulación (SIL). Cita clave: la validación previa al ensayo real es decisiva.
- **Se dice:** el problema se aborda como cadena percepción→estimación→control; el eslabón donde este trabajo se ubica: **la validación experimental**.

**S6 · LA IDEA: un robot cuadrúpedo como barco sintético** ⭐ *(bisagra de la charla)*
- **Se ve:** lado a lado: animación de barco oscilando ↔ video del Go2 real reproduciendo el mismo movimiento (videos_lab/03 primer plano). Efecto de "morphing" o transición entre ambos.
- **Se dice:** en vez de modelar una embarcación, usamos el torso actuado del Go2 para reproducir roll/pitch/heave. Bonus: el mismo robot existe en simulación y en el laboratorio → continuidad total.

**S7 · Objetivo y las dos preguntas de validación**
- **Se ve:** objetivo general arriba; abajo dos columnas: **SIMULACIÓN** — ¿el pipeline visual mide bien la pose? (pregunta de percepción) · **LABORATORIO** — ¿el robot real reproduce el movimiento? (pregunta de dinámica).
- **Se dice:** alcance explícito: NO resolvemos el aterrizaje completo; construimos la capa habilitante. Estas dos columnas estructuran todo lo que sigue.

## Bloque 3 — Metodología (técnico)

**S8 · Arquitectura del entorno**
- **Se ve:** diagrama de pipeline (`method_pipeline`) rediseñado para la web, con animación de flujo: simulador marino → Go2 → cámara (fija o dron) → detector ArUco → rosbag → evaluación offline.
- **Se dice:** recorrido de 1 minuto por los bloques; todo corre en ROS2 + Gazebo, todo queda registrado.

**S9 · Generación del movimiento marino** 🦿 *(Jack)*
- **Se ve:** `fig_method_motion_components` + `fig_method_wave_patterns` (ondas sinusoidal/irregular). Parámetros clave grandes: **0,10 Hz · ±10–20° · 20 Hz de publicación**.
- **Se dice:** cómo se sintetiza el oleaje (componentes por eje, superposición), por qué esas amplitudes y frecuencias son representativas.

**S10 · Del comando a las patas: control postural** 🦿 *(Jack)*
- **Se ve:** `go2_postural_control_scheme.png` + `fig_go2_postures.jpeg` (posturas render). Esquema: pose deseada del torso → cinemática inversa → 12 ángulos articulares.
- **Se dice:** el modelo principal y el resultado (sin despeje paso a paso): dado roll/pitch/heave del torso, cada pata resuelve su IK analítica. Detalle completo en backup.

**S11 · Estimación visual: ArUco + PnP**
- **Se ve:** `aruco_id0_dict_6x6_250.png` + `camera_marker_geometry.png` + frame real con ejes dibujados (`aruco_detection_frame.png`).
- **Se dice:** qué es un marcador fiducial (última concesión al público general); PnP: esquinas detectadas + geometría conocida + calibración → pose relativa completa.

**S12 · Registro y evaluación offline**
- **Se ve:** esquema simplificado: rosbag → reconstrucción del ground truth (odometría+IMU+heave) → comparación frame a frame → métricas. Métricas destacadas: Δroll, Δpitch, ΔZ (heave).
- **Se dice:** la estimación en vivo no alcanza: el valor del entorno es poder MEDIR la calidad contra referencia verdadera, de forma reproducible.

**S13 · Escenarios de observación en simulación**
- **Se ve:** lado a lado: cámara fija nadir (`fotos_sim/04` contexto) vs dron SJTU con cámara inferior (`fotos_sim/03`).
- **Se dice:** caso base (sensor quieto = pregunta limpia) vs caso fuerte (sensor volando = geometría exigente). Diseño deliberado para separar preguntas.

**S14 · Del simulador al robot real: qué cambia** 🦿 *(Jack, opcional Máximo)*
- **Se ve:** tabla visual sim vs lab: ground truth perfecto → no hay · cámara ideal → webcam en trípode · comando directo → API del robot + control interno. Foto del montaje (`fotos_lab/04` o `01_setup_montaje.jpeg`).
- **Se dice:** las dificultades del pasaje y la decisión metodológica clave: en el lab evaluamos movimiento y visión POR SEPARADO (evitar saturación de cómputo que contamine registros).

## Bloque 4a — Resultados: simulación

**S15 · Campaña experimental**
- **Se ve:** tabla simple: 1 caso base (cámara fija, 57,5 s) + 3 repeticiones con dron (R1–R3, ~57 s c/u). Misma consigna, mismo postproceso.
- **Se dice:** el diseño busca repetibilidad, no acumulación: 3 corridas comparables para descartar que la lectura dependa de una corrida con suerte.

**S16 · El pipeline en acción (video)**
- **Se ve:** video `videos_sim/01` (cámara fija + detección con overlay) a pantalla generosa; miniatura del contexto Gazebo al lado.
- **Se dice:** narración en vivo sobre el video: el marcador sube, baja y se inclina; los ejes dibujados son la estimación en tiempo real.

**S17 · Caso base (cámara fija): resultados**
- **Se ve:** `sim_fixed_position_vs_gt.png` (agrandada para proyector) + cifra héroe: **error medio de posición 5,8 cm**.
- **Se dice:** la estimación sigue la dinámica del marcador; el heave se recupera con claridad. Esta es la referencia limpia del entorno.

**S18 · Caso fuerte (dron): video + resultados**
- **Se ve:** video corto `videos_sim/02` (detección desde el dron) y `sim_drone_orientation_vs_gt.png`.
- **Se dice:** ahora el sensor también se mueve; aun así las series de roll/pitch/heave siguen al ground truth.

**S19 · Caso fuerte: números y repetibilidad**
- **Se ve:** cifras héroe: **2–3° en roll/pitch · 2–2,4 cm en heave** + `sim_drone_runs_comparison.png` (las 3 corridas superpuestas).
- **Se dice:** las tres repeticiones conservan el mismo orden de magnitud → el resultado no es una corrida aislada.

**S20 · Qué aprendimos de la simulación (y sus límites)**
- **Se ve:** 2 columnas: ✅ el pipeline sigue la dinámica global, medible contra referencia / ⚠️ heave es el eje más sensible, sesgo sistemático en Y (limitación de la cadena geométrica, no movimiento real).
- **Se dice:** admitir limitaciones con precisión — para eso sirve la simulación: aislarlas con ground truth antes del mundo físico.

## Bloque 4b — Resultados: laboratorio 🦿 *(Jack)*

**S21 · Lo que la simulación no anticipó** 🧱 *(bisagra sim → lab)*
- **Se ve:** tres filas obstáculo → adaptación. (1) Conectarnos al robot → refactor de la capa de comunicación. (2) Guardrail de marcha: el Go2 trota en el lugar para reasegurar estabilidad → barrido de frecuencias, a menor frecuencia el trote se espacia (no se elimina). (3) Sin acceso al firmware → no se pudo corregir la dinámica, se la midió (τ, g).
- **Se dice:** en simulación salió bien; al enchufar el robot real aparecieron tres muros. Las dos últimas limitaciones explican los números de S24–S25. Punto marcado por los mentores (Gastón / Juan) — no es una disculpa, es la justificación de las decisiones de diseño experimental.
- **Backup asociado:** B9 (guardrail de gait) y B10 (movimiento trabado / firmware).

**S22 · El montaje real**
- **Se ve:** video `videos_lab/08` (setup completo: trípode + cámara cenital + Go2 con ArUco haciendo posturas) o fotos `fotos_lab/04`–`06`.
- **Se dice:** mismo concepto que en Gazebo, con hardware real: webcam en trípode, marcador en el lomo, consigna marina por la API del Go2.

**S23 · El barco sintético existe (video estrella)** ⭐
- **Se ve:** video `videos_lab/02` (operador comanda → Go2 ejecuta posturas marinas, 34 s, recortado a ~15 s) a pantalla completa.
- **Se dice:** esto es el resultado central del lab en una imagen: la consigna de oleaje moviendo un robot real.

**S24 · ¿Llega el comando intacto? Sí.**
- **Se ve:** `lab_plot_02_api_fidelity.png` + cifra héroe: **correlación > 0,9999** entre consigna esperada y comando enviado.
- **Se dice:** primer eslabón validado: nada se pierde ni deforma en el camino de software hasta la API del robot.

**S25 · Comando vs respuesta física**
- **Se ve:** `strong_15_10_plot_01_timeseries_cmd_vs_real.png` (R4: series roll y pitch, esperado vs real).
- **Se dice:** el robot reproduce la FORMA del movimiento — se ve a ojo en las series — pero con retardo y menor amplitud. Eso es física, no falla.

**S26 · Cuantificando la dinámica: retardo y ganancia**
- **Se ve:** `strong_15_10_plot_03_lag_correlation.png` + cifras héroe: **τ = 0,45–0,95 s · ganancia ≈ 0,62 · r > 0,95**. El modelo afín con retardo: θ_real(t) ≈ g·θ_cmd(t−τ) + b.
- **Se dice:** el desacople es fase + escala, no deformación → error dinámico *parametrizable*. Patrón replicado a dos amplitudes (R4 y R5).

**S27 · El pipeline visual también corre en el lab**
- **Se ve:** frames `lab_aruco_realtime_t00/t26/t49.png` (secuencia) + clip corto de `videos_lab/07` (detección en pantalla en vivo).
- **Se dice:** la detección ArUco funciona sobre el robot real con la cámara del montaje; se evaluó por separado del movimiento (decisión metodológica de S14).

## Bloque 5 — Cierre

**S28 · Lectura conjunta: dos piezas de una misma validación**
- **Se ve:** diagrama de dos piezas de puzzle: SIM = percepción (si el robot se mueve perfecto, la visión mide con cm de error) + LAB = dinámica (el robot real sigue la consigna con retardo/ganancia medibles). Pieza faltante marcada: **ambos a la vez**.
- **Se dice:** mismo régimen en ambos entornos (0,10 Hz, ±10–20°) — que los dos experimentos sean ejecutables con la misma plataforma ya es un resultado.

**S29 · Conclusiones**
- **Se ve:** 3 eslabones con check: el simulador genera movimiento representativo ✓ · el robot lo reproduce de forma consistente ✓ · el pipeline visual lo mide ✓. Frase: "no un sistema de aterrizaje: una base de investigación".
- **Se dice:** objetivo cumplido; afirmación moderada pero sólida; límites ya admitidos en S20/S24.

**S30 · Trabajo futuro**
- **Se ve:** roadmap visual en 4 pasos: validación conjunta (visión + movimiento simultáneos) → ground truth externo (OptiTrack) → heave dinámico + yaw/surge/sway + oleaje irregular → aproximaciones de aterrizaje sobre el Go2.
- **Se dice:** la línea inmediata es cerrar la pieza faltante de S27; misma lógica de siempre: complejidad gradual con trazabilidad.

**S31 · Cierre y preguntas**
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
3. **Animaciones propias:** oleaje SVG (S2–S3), pipeline animado (S8), puzzle (S27). Sobrias, sin distraer.
4. **Cifras héroe:** los números clave (5,8 cm · 2–3° · 0,9999 · 0,62) en tipografía gigante — legibles desde el fondo del aula.
5. **Paleta tentativa:** fondo claro casi blanco, tinta azul marino profundo + un acento (a definir: coral/cian), tipografía sans-serif. Identidad "marina" sutil sin caer en cliché náutico.
6. **Export PDF de respaldo** por si falla todo el día de la defensa.

## Pendientes de material

- **Video o clip del robot en trote / moviéndose "trabado"** — sería el activo más fuerte para S21. Ninguno de los 8 clips de laboratorio curados lo muestra: todos son posturas que salen bien.
- Foto de los dos autores con el robot (S31) — **confirmado que no existe**; S31 usa la vista cenital como fallback.
- Video del Go2 con heave (mejoraría S23; no bloquea).
- ~~Nombres de mentores~~ — Gastón Castro (mentor) · Juan Ignacio Giribet (comentor). ✅

Ver **`backlog.md`** para lo que queda abierto (informe sin documentar las limitaciones, justificación de los 0,10 Hz, export PDF, reparto).
