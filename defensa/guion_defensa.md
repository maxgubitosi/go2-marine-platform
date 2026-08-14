# Guion simplificado — Defensa oral (martes 18-08)

Bullets de temas por lámina, no script literal. Tiempos estimados sobre 30 min totales.
Numeración = orden del deck (`web/index.html`). Se va completando a medida que ensayamos.

Señal en pantalla: el número de página (abajo a la derecha) va en gris azulado si arranca Maxo y en **negro** si arranca Jack (`data-speaker="jack"` en la lámina fuente).

Presupuesto por bloque: contexto+problema ~7 min (S1–S8) · metodología ~8 min (S9–S17) · resultados ~12 min (S18–S23) · cierre ~3 min (S24–S27).

---

## S1 · Portada — Maxo · 0:30

- Saludo, presentación de ambos, mentores (Gastón Castro, Juan Ignacio Giribet).
- Título en una frase: simulación de dinámica de plataforma marina mediante un robot cuadrúpedo.

## S2 · El barco como base móvil de un dron — Maxo (a, b) + Jack (c) · 1:00

- La idea: el barco como **base móvil** del dron → más tiempo de misión, menos dependencia de infraestructura costera, el vehículo cerca del área de interés.
- Tres casos de uso (uno por tarjeta): búsqueda y rescate (Maxo) · inspección offshore (Maxo) · monitoreo marítimo (Jack).
- **Transición a S3**: para operar así, el dron tiene que aterrizar de vuelta en la cubierta… y la cubierta se mueve.

## S3 · Movimiento de una plataforma marina — Maxo explica + Jack acota · 1:30

- La palabra: **seis grados de libertad** — tres traslaciones (surge, sway, heave) y tres rotaciones (roll, pitch, yaw). [Callback en S6: el torso del Go2 tiene los mismos seis.]
- Narrar sobre las animaciones, con el lenguaje de la lámina (mismo que reaparece en S9):
  - **Heave**: la altura del agua sube y baja la cubierta (vista de perfil).
  - **Pitch**: pendiente proa–popa → cabeceo (vista de perfil). ⚠️ NO decir "rota en el sentido longitudinal" (eso es roll).
  - **Roll**: pendiente babor–estribor → el barco se **inclina** al costado (vista de proa). ⚠️ NO decir "se mueve al costado" (eso es sway).
  - Mención breve de yaw: rotación en el plano.
- **Jack cierra — por qué retenemos solo 3**: criterio perceptual. Roll y pitch cambian la orientación del plano del marcador frente a la cámara; heave cambia la distancia (escala en la imagen). Surge, sway y yaw desplazan la cubierta en el plano **pero no la inclinan** → no afectan lo que la cámara necesita medir. Complemento: seguirla en el plano es un problema de tracking horizontal, otro problema, fuera de alcance a propósito.

## S4 · ¿Por qué no probar directo en el mar? — Jack · 1:00

- Un error de estimación de pose = colisión o pérdida del vehículo → hay que validar antes.
- Validar exige cuatro cosas que el mar abierto no garantiza: **repetir** la misma condición · **medir** contra referencia conocida · **fallar** sin perder el vehículo · **iterar** en minutos.
- (Contexto informe: alternativas descartadas = banco mecánico a medida, caro y desvía el esfuerzo al diseño mecánico; ensayo real directo, riesgoso y poco repetible. Nuestro camino: simulación → laboratorio.)

## S5 · Estado del arte — Maxo · 1:15

- Encuadre: tres referencias = tres maneras distintas de **validar antes de ir al mar** (no explicar autores, decir qué probó cada uno).
  - **2014 Sánchez-López**: banco físico — plataforma de movimiento de 6 GDL que emula la cubierta para distintos estados de mar; valida ahí antes de salir al mar. (Detalle por si preguntan: monocular + helipad pintado, sin fiduciales codificados, + Kalman.)
  - **2022 Cho**: desde el control — aterriza sobre una cubierta que oscila por oleaje, compensando el movimiento desde la imagen (feed-forward IBVS). Ensayos equivalentes a estado de mar 4. ⚠️ NO decir "en un barco real": es una cubierta emulada.
  - **2022 Delbene**: simulación — valida en software-in-the-loop con **Gazebo y ROS2** (mencionar: nuestro mismo ecosistema) sobre un catamarán, alimentado con telemetría real del vehículo. (Detalle: AprilTags + ultrasonido.)
- **Remate (lo central)**: todos evalúan por éxito del aterrizaje completo. Casi no hay trabajos que **aíslen el estimador de pose y lo midan contra una referencia limpia bajo movimiento marino sintetizado** → ese hueco es donde se ubica este trabajo (informe §1.6.5).
- **Transición a S6**: "y para eso necesitábamos algo que hiciera de cubierta…" → entra el Go2.

## S6 · Unitree Go2 como plataforma marina — Maxo · (pendiente)

## S7 · El escenario de simulación — Jack · (pendiente)

## S8 · Pipeline de trabajo — Maxo arranca, Jack acompaña · (pendiente)

## S9 · Modelo reducido del oleaje — Maxo · 2:00

*(Script completo en `contenido-consigna-marina.md`; esto es el esqueleto.)*

- Apertura: el movimiento real de una cubierta depende de oleaje irregular + inercia/amortiguamiento/restauración del casco. Resolver eso es dinámica marina completa — **no es lo que necesitamos**.
- Nuestra simplificación es **geométrica**: la superficie del agua bajo la plataforma, tratada como un **plano**. Un plano = **una altura y dos pendientes** = exactamente los tres GDL retenidos.
  - altura respecto del nivel medio del mar → **heave**
  - pendiente babor–estribor (∂ζ/∂y) → **roll**
  - pendiente proa–popa (∂ζ/∂x) → **pitch** (el signo menos: convención de ejes)
- La ecuación: **ζ es un campo** (un número por punto del mar y por instante), ⚠️ no "una gradiente". Evaluado bajo la plataforma da heave; sus derivadas parciales dan las pendientes.
- **κ**: cuánto acompaña la cubierta esa pendiente. κ = 1 = balsa perfecta; un casco real tiene eslora e inercia, promedia y se inclina menos. ⚠️ κ es atenuación **estática** — NO decir "desfasaje" (el desfase es otra cosa y aparece en S10).
- **Cierre — las dos aproximaciones (decirlas explícitas):** (1) **local**: altura y pendientes en un solo punto, sin curvatura — vale si la ola es larga frente al barco; (2) **cinemática**: el movimiento se prescribe desde la superficie, no se resuelven las fuerzas (M, C, D, g quedan como marco conceptual). "No estamos simulando un casco."

## S10 · Consigna sinusoidal y suavizado — Maxo · 2:00

*(Script completo en `contenido-consigna-marina.md`.)*

- Con el modelo definido, lo nuestro es directo: **una sinusoide por componente**, sintetizada por un nodo de ROS 2 que publica a 20 Hz.
- Parámetros (el machete): roll y pitch comparten ω (f = 0,10 Hz, ciclo de 10 s); roll ±15°, pitch ±10° con desfase π/3; heave aparte: 1,5ω y ±0,10 m.
- **Por qué el desacople**: si las tres llegan juntas a los extremos, el marcador recorre siempre la misma familia de poses; corridas, el estimador ve inclinaciones y distancias más variadas. Un mar real tampoco es una sola onda.
- **Suavizado exponencial** (α = 0,95): cada valor publicado = 95 % del anterior + 5 % del objetivo. Pasa-bajos de primer orden, τ ≈ 1 s.
  - **Por qué**: no mandamos fuerza, mandamos una postura que el robot realiza con 12 articulaciones. Un salto = un tirón: en Gazebo transiciones poco plausibles; en el robot real el controlador lo puede leer como empujón y **romper a trotar** (semilla del guardrail del bloque lab).
  - **Costo**: llegan ±12,8° / ±8,5° / ±0,074 m (85 / 85 / 74 %). Heave pierde más porque va más rápido y esto es un pasa-bajos.
  - **Punto fino**: la referencia registrada es la suavizada → la atenuación cambia la excitación aplicada, no ensucia el error medido.
- **Cierre — los dos destinos**: en simulación, pose completa del torso publicada en el tópico `/body_pose`; en laboratorio, solo actitud por la API del robot (`SportClient.Euler(roll, pitch, yaw)`). ⚠️ El `0` de la lámina es **yaw, no heave**: la API de alto nivel no expone altura dinámica. "En el lab la cubierta se inclina pero no sube ni baja."

## S11 · Geometría articular del Go2 — Jack · (pendiente)

## S12 · Cinemática directa e inversa de una pata — Jack · (pendiente)

## S13 · Control PD por junta — Jack · (pendiente)

## S14 · Tres montajes de observación — Maxo · (pendiente)

## S15 · Marcador fiducial y estimación de pose — Maxo + Jack acota · (pendiente)

## S16 · Ensayos realizados — Jack + Maxo acota · (pendiente)

## S17 · Cambia la referencia, cambia la pregunta — Jack + Maxo acota · (pendiente)

## S18 · Caso base: cámara fija — Maxo · (pendiente)

## S19 · Cámara en el dron: video y series — Jack · (pendiente)

## S20 · Cámara en el dron: distribución del error — Jack · (pendiente)

## S21 · Repetibilidad entre corridas — Jack · (pendiente)

## S22 · El robot real sigue la consigna — Maxo · (pendiente)

## S23 · Cuantificando: retardo y ganancia (incluye el residual R5) — Maxo · (pendiente)

## S24 · Limitaciones y experiencias — empieza Jack · (pendiente)

## S25 · Trabajo futuro — empieza Maxo · (pendiente)

## S26 · Conclusiones — empieza Jack · (pendiente)

## S27 · Cierre y preguntas — empieza Maxo · 0:30

---

## Machete de preguntas probables (se va completando)

- **¿Con qué parámetros corrieron?** f = 0,10 Hz · A_roll ±15° · A_pitch ±10° · A_heave ±0,10 m · κ_p = 1,0 · κ_h = 1,5 · desfase π/3 en pitch · α = 0,95 a 20 Hz (τ_filtro ≈ 1 s).
- **Retardos R5: tabla vs residual de S23** (0,55/1,20 vs 0,58/1,16 s): dos estimaciones sobre señales distintas — la tabla sale del estado deportivo, el residual se reestimó sobre la odometría del rosbag. No es inconsistencia. (El caption del residual ya no muestra los números para no exhibir la diferencia en la lámina.)
- **Tamaño del ArUco**: mismo diccionario (6x6, id 0) en ambos entornos, pero 0,50 m de lado en simulación y 0,20 m en laboratorio.
- **¿De dónde salen los ±12,8° / ±8,5° / ±0,074 m de S10?** Efecto del filtro exponencial α = 0,95 sobre la consigna: atenúa al 85 % (roll), 85 % (pitch) y 74 % (heave, que oscila más rápido) con ~1 s de atraso.
- **¿Por qué esos tres papers y no otros? (S5)** Son los tres del caso marino y cubren las tres estrategias de validación (banco físico / control sobre cubierta oscilante / SIL). El corpus completo está en el informe §1.6: la familia no-marina de aterrizaje completo (Lee 2012, Araar 2017, Falanga 2017, Keipour 2022), el contrapunto no visual (Alarcón 2019: cable físico, precisión centimétrica sin cámara) y las herramientas de percepción (ArUco/Garrido-Jurado 2014, AprilTag/Olson 2011, EPnP/Lepetit 2009).
- **¿Alguien aterriza en un barco real?** De lo citado, no: los tres usan un sustituto del barco. Sánchez-López: plataforma de movimiento 6 GDL. Cho: simulación numérica (no Gazebo) + vuelos reales outdoor sobre una cubierta montada en un camión que oscila como estado de mar 4 (touchdown medio 0,2 m, camión a >5 m/s) — valida el control (FF-IBVS con velocidad del barco estimada por Kalman como feed-forward). Delbene: SIL en Gazebo/ROS2 alimentado con telemetría real de un catamarán. Punto retórico: toda la literatura usa cubiertas sintéticas; la nuestra es un cuadrúpedo comercial. Ejemplo reciente en embarcación real: Wu 2024 (~5 cm estático, ~10 cm en movimiento), no citado en la lámina.
- **¿Por qué ArUco y no AprilTag? (puede salir de S5 o S15)** Delbene usa AprilTags: familias equivalentes para el rol (cuadrado + código binario + 4 esquinas → PnP). ArUco por integración directa con OpenCV/cv2.aruco en el pipeline ROS2; probar AprilTags queda declarado en trabajo futuro (S25).
- **¿La consigna de S10 sale de la ecuación de S9?** Sí: evaluada sobre una ola regular, altura y pendientes salen todas sinusoides. Lo que hicimos fue liberar la relación de frecuencias y el desfase entre ejes en vez de atarlos a una única onda plana — dirección correcta porque un mar real es superposición de componentes de distintas direcciones. (Interpretación propia del material, no está escrita así en el informe.)
- **Dos κ distintas en el informe** — no mezclarlas: κ_φ/κ_θ (S9) = acople pendiente→inclinación (cuánto acompaña la cubierta); κ_p/κ_h (S10) = desacoples temporales de la consigna (1,0 y 1,5). En el deck la segunda ni aparece con nombre (la tabla muestra ω y 1,5ω directo).
- **¿α = 0,95 no congela el movimiento?** No: se aplica a 20 Hz. 5 % por paso × 20 pasos/s → constante de tiempo ≈ 1 s, contra una consigna de período 10 s: sigue bien, con ~1 s de atraso y 85 % de amplitud. Heave (1,5× más rápido) pierde más: 74 %.
- **¿El filtro no da simplemente otra sinusoide? ¿No bastaba mandar amplitud y fase ajustadas?** En régimen estacionario sí (misma ω, menos amplitud, fase corrida). Pero el filtro es una barrera genérica de salida: protege contra escalones del modo manual, arranques/paradas y el modo irregular (cada armónico se atenúa solo). No es diseño de señal, es seguridad.
- **¿Por qué no heave en el robot real?** La API de alto nivel (SportClient) solo expone la actitud como comando continuo (`Euler(roll,pitch,yaw)` a ~50 Hz); la altura solo como ajuste cuasi-estático de parada (`BodyHeight`, límites fijos, no streameable). Mandar heave real exigiría control de bajo nivel de las 12 articulaciones = reemplazar el controlador de fábrica: fuera de alcance y riesgoso. Por eso lab = roll y pitch; heave dinámico → limitación (S24) y trabajo futuro (S25).
- **Vocabulario náutico**: eslora = largo del barco (proa–popa) · manga = ancho (babor–estribor). κ < 1 porque el casco rígido promedia la pendiente a lo largo de su eslora (olas cortas se compensan bajo el casco) y su inercia no sigue cambios rápidos; una balsa chica y liviana copia la pendiente local → κ = 1.
- **⚠️ PENDIENTE con Jack — filtro del laboratorio**: el nodo del lab NO usa el EMA sino un conformador de 2.º orden (ζ = 0,82, f_n = 0,9 Hz) + límites de velocidad (45°/s roll, 35°/s pitch) a 50 Hz, porque el EMA no acota velocidad y el robot trotaba (commit `5ad01f7`). El informe solo documenta el exponencial. Acordar respuesta: "mismo principio —limitar cambios bruscos—, implementación distinta porque el primer orden no acota velocidad angular".
