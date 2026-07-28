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

**Riesgo:** la defensa (S21, B9, B10) muestra material que el jurado no leyó en el informe. Pregunta previsible: *"¿por qué esto no está en el informe?"*

**Opciones cuando se retome:**
- (a) Agregar un párrafo a §5.3.1 si el informe todavía se puede editar → resuelve el problema de raíz.
- (b) Si ya está entregado: preparar la respuesta oral — son observaciones de la campaña experimental posteriores al cierre del texto, y la caracterización dinámica (τ, g) que **sí** está en el informe es justamente su consecuencia medible.

### 2. Justificación de los 0,10 Hz — pregunta previsible del jurado

B9 ahora dice que se ensayó a 0,10 Hz porque a menor frecuencia los episodios de trote se espacian. El informe (línea ~3124) presenta 0,10 Hz como el régimen que une simulación y laboratorio, y observa que *"el movimiento marino al que apunta el entorno está dentro del rango que el cuadrúpedo puede reproducir"* — consistente, sin contradicción.

**Pero falta cerrar esto:** ¿0,10 Hz es además representativo de oleaje real (período ~10 s cae en rango de swell), o la elección fue puramente una restricción del robot? Si las dos razones convergen, **decirlo explícitamente es una respuesta mucho más fuerte** que cualquiera de las dos sola. Verificar contra bibliografía antes de afirmarlo en voz alta.

---

## 🟡 Media — material y producción

### 3. Video del robot en trote / moviéndose "trabado"

Sería el activo más fuerte de S21: convierte una tabla en evidencia. Ninguno de los 8 clips de laboratorio curados en `defensa/media/videos_lab/` lo muestra — todos son posturas que salen bien. Existe el rosbag `lab_real_20260320_112522_trote_robot_full` (~59,7 s), pero no un video.

### 4. Export a PDF de respaldo

Por si el día de la defensa falla la web (proyector, navegador, resolución). La presentación ya es self-contained y funciona offline, pero el PDF es el paracaídas.

### 5. Video del Go2 con heave

Mejoraría S23. No bloquea — el heave está cubierto por la simulación.

---

## 🟢 Baja

### 6. Reparto de la exposición entre Máximo y Jack

Definido sólo parcialmente: Jack cubre movimiento del robot (envío de comandos, control postural, y ahora también el bloque de obstáculos S21). El resto se define sobre la marcha. El plan tiene una propuesta tentativa en la tabla de arriba de `plan_presentacion.md` — **no está anclada**.

### 7. Foto de los dos autores con el robot

Confirmado que no existe. S31 usa la vista cenital como fallback y funciona bien. Si sale una foto antes de agosto, es una mejora obvia del cierre.
