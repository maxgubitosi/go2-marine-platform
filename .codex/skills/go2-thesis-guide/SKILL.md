---
name: go2-thesis-guide
description: Guia de estructura y convenciones LaTeX para el informe de tesis Go2 marine. Usar cuando haya que decidir que va en cada seccion, como organizar el contenido y como insertar placeholders, figuras y referencias en informe/main.tex.
---

# Go2 Thesis Guide

Usar esta skill para ordenar el contenido del informe y mantener consistencia con el proyecto real.

## Archivo principal

- El informe vive en `informe/main.tex`.
- La bibliografia vive en `informe/bibliography.bib`.
- El material visual existente esta principalmente en `docs/media/`.

## Regla de alcance

- Este branch documenta la simulacion.
- La validacion con el Go2 real version EDU existe, pero no debe redactarse todavia. Dejar placeholders `REAL PENDIENTE` donde corresponda.

## Estructura

- Ver `references/structure.md` para el desglose seccion por seccion.
- Mantener las secciones principales del informe, pero ajustar las subsecciones para que reflejen lo implementado de verdad en el repo.

## Convenciones LaTeX

- Usar etiquetas con prefijos `sec:`, `fig:`, `tab:` y `eq:`.
- No insertar `\includegraphics` a archivos inexistentes.
- No usar claves `\cite{}` inventadas; si falta una referencia, usar el placeholder visible definido en el documento.
- Preferir captions descriptivas y referencias cruzadas naturales dentro del texto.

## Soporte visual

- Para setup, usar placeholders o assets ya existentes del repo.
- Para resultados, usar solo figuras o analisis respaldados por archivos del proyecto.
- Si una figura todavia no existe, describir exactamente que deberia mostrar para poder producirla despues.
