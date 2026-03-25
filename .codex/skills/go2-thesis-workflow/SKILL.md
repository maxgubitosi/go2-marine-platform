---
name: go2-thesis-workflow
description: Flujo de trabajo para escribir el informe de tesis Go2 marine en Codex. Usar cuando haya que redactar una seccion, mantener placeholders compilables, verificar consistencia con el repo y avanzar una parte del informe por vez.
---

# Go2 Thesis Workflow

Usar esta skill cuando la tarea sea avanzar el informe de tesis de forma iterativa.

## Flujo

1. Leer primero el contexto del repo y el contenido actual de `informe/main.tex`.
2. Redactar una sola seccion o un bloque cohesivo por vez.
3. Basar cada afirmacion tecnica en el codigo, README, analisis guardados o material del repo.
4. Si falta una figura, referencia o dato del branch `real`, usar un placeholder compilable.
5. Compilar con `latexmk -xelatex` despues de cada tanda de cambios relevantes.

## Reglas de contenido

- No inventar resultados numericos.
- No describir experimentos reales sin haber consultado la branch correspondiente.
- Si una subseccion del esquema original no coincide exactamente con el repo, reinterpretarla para que refleje la implementacion real en lugar de forzar una narrativa artificial.
- Mantener consistencia entre nombres de topics, parametros, scripts y launch files.

## Orden recomendado

- Escribir primero `Metodo`.
- Escribir despues `Marco teorico`.
- Escribir `Experimentacion` solo con evidencia disponible.
- Dejar `Introduccion`, `Abstract`, `Conclusiones` y `Trabajo futuro` para cuando ya exista un cuerpo tecnico estable.

## Checklist rapido

- La seccion explica que hace el sistema y como se valida.
- Toda figura tiene caption o placeholder descriptivo.
- Toda cita faltante esta marcada.
- Todo contenido de hardware real esta marcado como pendiente.
