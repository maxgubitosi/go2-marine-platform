---
name: thesis-style
description: Guía el estilo de escritura académica en español para el informe de tesis (Go2 marine). Usar al redactar o editar secciones del informe en informe/main.tex, al pedir resúmenes o abstracts, o cuando el usuario pida que el texto siga su estilo.
---

# Estilo de escritura del informe de tesis

Referencia de estilo: [informe/refs/PPO_Car_Racing.pdf](informe/refs/PPO_Car_Racing.pdf).

## Lengua y voz

- **Idioma:** español. Tildes correctas (á, é, í, ó, ú, ñ).
- **Persona:** primera del plural ("nosotros") o **voz pasiva refleja** (voz pasiva con "se": "se implementó", "se observó").
- **Tono:** académico pero accesible; directo, sin rodeos innecesarios.

## Estructura narrativa

- Contar el desarrollo de forma **cronológica** cuando corresponda: qué se probó, qué falló, por qué se cambió de enfoque.
- Ser **honesto con limitaciones y fracasos intermedios** (ej. "A pesar de entrenar durante X, los resultados evidenciaron dificultades...").
- Dar **intuición antes de fórmulas**: explicar en prosa el "por qué" antes de ecuaciones o algoritmos.
- Permitir un tono **ligeramente informal** en momentos puntuales (ej. "experimento bonus", "resultados particularmente interesantes").

## Abstract y contribuciones

- El abstract debe resumir objetivo, método y **aportes numerados** (1), (2), (3), (4) cuando haya contribuciones claras.
- Ejemplo de formato: "Nuestros aportes principales son: (1) ...; (2) ...; (3) ..."

## Figuras y tablas

- **Captions descriptivos:** no solo "Curva de aprendizaje" sino qué muestra, qué se compara y qué se concluye (ej. "Evolución del retorno medio durante el entrenamiento para PPO en SB3 y nuestra implementación.").
- Referenciar figuras/tablas en el texto de forma natural antes o después de comentar el contenido.

## Referencias a código, ROS y datos

Seguir [technical-references.md](../thesis-guide/technical-references.md): no saturar el cuerpo con tópicos `\texttt{/...}`, paths de archivos ni nombres largos de rosbags.

- **Prosa primero:** nombre en español del rol de cada señal (“consigna postural”, “depuración del simulador marino”).
- **Literales concentrados:** tablas `tab:ros_interfaces_sim` y `tab:ros_interfaces_lab` en `main.tex`, más apéndice de registros cuando haga falta.
- **Parámetros:** remitir a tablas de metodología, no listar `clave = valor` en párrafos.
- **Tipografía:** `\path{...}` para paths con barras (requiere `hyperref`); `\texttt{}` breve para modos (`sinusoidal`) y paquetes.

## Evitar

- Frases genéricas o relleno.
- Afirmaciones sin respaldo (datos, referencias o "en la Figura X se observa...").
- Mezclar "tú" o "usted" con "nosotros"; mantener una sola convención de persona.
- Párrafos con muchos tópicos ROS o rutas pegadas; usar la guía de referencias técnicas.
