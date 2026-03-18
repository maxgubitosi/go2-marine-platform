---
name: thesis-guide
description: Guía la estructura del informe de tesis y las convenciones LaTeX del proyecto Go2 marine. Usar al escribir o editar informe/main.tex, al agregar figuras/tablas/referencias, o cuando se pregunte qué incluir en cada sección.
---

# Guía del informe de tesis (Go2 marine)

- Contenido del informe: un único archivo [informe/main.tex](informe/main.tex).
- Desglose sección por sección: [structure.md](structure.md).

## Estructura de secciones (resumen)

| Sección | Contenido principal |
|---------|----------------------|
| Introducción | Motivación, problema, contribuciones, estructura del documento |
| Marco teórico | Interpolación de olas, cinemática Go2, detección ArUco/solvePnP |
| Método | Implementación de cada subsistema (marine_platform_simulator, fixed_camera, sjtu_drone, etc.) |
| Experimentación | Simulación (métricas, resultados) y Real (si aplica) |
| Conclusiones | Logros y limitaciones |
| Trabajo futuro | Mejoras y líneas futuras |

## Convenciones LaTeX

### Figuras

- Rutas desde `informe/`: usar subcarpetas `figures/setup/`, `figures/results/`, `figures/diagrams/`.
- Ejemplo: `\includegraphics[width=0.8\textwidth]{figures/results/error_pose.pdf}`
- Subfiguras: paquete `subcaption`; etiquetas coherentes y caption descriptivo (ver skill thesis-style).
- Referencias: `\label{fig:nombre}` y `\ref{fig:nombre}`.

### Tablas

- Estilo `booktabs`: `\toprule`, `\midrule`, `\bottomrule`.
- Encabezados en negrita si hace falta; numeración con `\label{tab:nombre}`.

### Referencias cruzadas

- Prefijos: `fig:`, `sec:`, `eq:`, `tab:` (ej. `\label{fig:setup}`, `\label{sec:mt}`).

### Fórmulas

- Ecuaciones numeradas: `equation`.
- Sistemas o varias líneas alineadas: `align`.

### Citas (natbib)

- Estilo round: `\citep{}` para (Autor, año), `\citet{}` para Autor (año).
- Bibliografía: [informe/bibliography.bib](informe/bibliography.bib); estilo `plainnat`.

### Idioma

- Babel: `spanish`. Escribir siempre con tildes correctas (á, é, í, ó, ú, ñ).
