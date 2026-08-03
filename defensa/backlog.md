# Backlog — defensa oral PF

Cosas pendientes que no bloquean el armado de la presentación pero hay que resolver antes del día de la defensa (~2ª semana de agosto 2026).

---

## 🔴 Alta — revisar antes de la defensa

### 1. El informe no documenta las limitaciones prácticas del robot

**Estado: postergado a propósito. No tocar el informe por ahora** (decisión del 27-07-2026).

`informe/main.tex` §5.3.1 *"Dificultades del pasaje de simulación a laboratorio"* (línea ~2253) cubre las adaptaciones **metodológicas** — cámara real que hay que calibrar, ausencia de ground truth, comando de actitud en lugar de pose — pero **no menciona ninguna de las tres limitaciones que Gastón y Juan pidieron resaltar**:

- el guardrail de marcha (el Go2 trota en el lugar y abandona la postura),
- la falta de acceso al firmware (movimiento "trabado" → τ y g),
- el problema de conexión que forzó el refactor del código.

**Riesgo:** la defensa (S23, B9, B10) muestra material que el jurado no leyó en el informe. Pregunta previsible: *"¿por qué esto no está en el informe?"*

**Opciones cuando se retome:**
- (a) Agregar un párrafo a §5.3.1 si el informe todavía se puede editar → resuelve el problema de raíz.
- (b) Si ya está entregado: preparar la respuesta oral — son observaciones de la campaña experimental posteriores al cierre del texto, y la caracterización dinámica (τ, g) que **sí** está en el informe es justamente su consecuencia medible.

### 2. Justificación de los 0,10 Hz — pregunta previsible del jurado

B9 ahora dice que se ensayó a 0,10 Hz porque a menor frecuencia los episodios de trote se espacian. El informe (línea ~3124) presenta 0,10 Hz como el régimen que une simulación y laboratorio, y observa que *"el movimiento marino al que apunta el entorno está dentro del rango que el cuadrúpedo puede reproducir"* — consistente, sin contradicción.

**Pero falta cerrar esto:** ¿0,10 Hz es además representativo de oleaje real (período ~10 s cae en rango de swell), o la elección fue puramente una restricción del robot? Si las dos razones convergen, **decirlo explícitamente es una respuesta mucho más fuerte** que cualquiera de las dos sola. Verificar contra bibliografía antes de afirmarlo en voz alta.

---

## 🟡 Media — material y producción

### 3. Video del robot en trote / moviéndose "trabado"

Sería el activo más fuerte de S23: convierte una tabla en evidencia. Ninguno de los 8 clips de laboratorio curados en `defensa/media/videos_lab/` lo muestra — todos son posturas que salen bien. Existe el rosbag `lab_real_20260320_112522_trote_robot_full` (~59,7 s), pero no un video.

### 4. Video en tercera persona del Go2 moviéndose en simulación

Pedido para S7, para que la mitad "simulación" de la bisagra tenga la misma fuerza visual que el video de laboratorio. **No existe en el repo** (verificado el 28-07-2026, barrido completo de `*.mp4/.mov/.webm/.gif`):

- los cuatro `defensa/media/videos_sim/` son **feeds de sensor**: cámara fija (escena oscura, sólo se ve el ArUco) y cámara inferior del dron (que es exactamente el ángulo cenital que el usuario descartó),
- `docs/media/Screencast...webm` es también la vista de detección, y encima 259x243,
- lo único en tercera persona es estático: `docs/media/gazebo_go2.png` (captura de la GUI de Gazebo, con todo el chrome de la interfaz, robot parado, sin marcador) y `defensa/media/fotos_sim/03_contexto_dron_go2_aruco.png` / `04_contexto_go2_aruco.png` (ángulo oblicuo correcto, pero fotos fijas de 259x243).

**Para conseguirlo hay que volver a correr la simulación y grabar la pantalla de Gazebo** desde una cámara oblicua. Un replay de rosbag no sirve: los bags guardan los tópicos de cámara, no la escena.

**Mitigado a medias (28-07-2026):** S6 ya muestra la simulación con un recorte fijo de `gazebo_go2.png` sin el chrome de la GUI (`defensa/web/assets/img/sim_gazebo_go2.png`, generado con `defensa/scripts/crop_gazebo_go2.py`). Alcanza para que la simulación no aparezca recién en S18, pero sigue siendo una foto: el video se mantiene pedido para S7.

**Si se vuelve a correr la simulación, aprovechar para sacar capturas en tercera persona a resolución decente** (28-07-2026). Todo el material de escena que hay es chico: el panel derecho de S15 sale de `sim_contexto_dron.png` (702x454) y el izquierdo del cuadro crudo `fotos_sim/01_frame_camara_fija_raw.png` (640x480, del que sólo sirve el centro porque el resto es fondo vacío). Ninguno da para proyectar a tamaño grande. No hay originales mejores en el repo (verificado el 28-07-2026 sobre `defensa/media/`, `docs/media/` e `informe/figures/`). Es la misma sesión de captura que resolvería el video, así que conviene hacer todo junto.

### 5. Export a PDF de respaldo

Por si el día de la defensa falla la web (proyector, navegador, resolución). La presentación ya es self-contained y funciona offline, pero el PDF es el paracaídas.

### 6. Video del Go2 con heave

Mejoraría S25. No bloquea — el heave está cubierto por la simulación.

---

## 🟢 Baja

### 7. Reparto de la exposición entre Máximo y Jack

Definido sólo parcialmente: Jack cubre movimiento del robot (envío de comandos, control postural, y ahora también el bloque de obstáculos S23). El resto se define sobre la marcha. El plan tiene una propuesta tentativa en la tabla de arriba de `plan_presentacion.md` — **no está anclada**.

### 8. Foto de los dos autores con el robot

Confirmado que no existe. S33 usa la vista cenital como fallback y funciona bien. Si sale una foto antes de agosto, es una mejora obvia del cierre.
