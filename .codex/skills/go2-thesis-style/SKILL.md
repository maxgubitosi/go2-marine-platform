---
name: go2-thesis-style
description: Estilo de escritura para el informe de tesis del proyecto Go2 marine. Usar al redactar o editar secciones en espanol academico, especialmente en informe/main.tex, abstracts, captions y texto tecnico del proyecto.
---

# Go2 Thesis Style

Usar esta skill cuando la tarea sea escribir o editar el informe de tesis del proyecto Go2 marine.

## Alcance

- Escribir siempre en espanol.
- Mantener una voz academica clara, preferentemente en primera persona del plural o pasiva refleja.
- Priorizar una narrativa honesta: explicar decisiones, cambios de enfoque, limitaciones y resultados intermedios sin exagerar aportes.
- Recordar que el branch actual cubre simulacion; cualquier contenido del Go2 real version EDU debe quedar como placeholder hasta consultar la branch `real`.

## Tono

- Directo y tecnico, pero legible.
- Dar intuicion antes de detalles algebraicos o de implementacion.
- Evitar relleno, promesas vagas y frases sin respaldo.
- Cuando un dato, una figura o una referencia bibliografica no este disponible, dejar un placeholder visible y compilable en lugar de inventarlo.

## Figuras y tablas

- Toda figura debe tener una caption descriptiva que diga que muestra y por que importa.
- Introducir cada figura en el texto antes o inmediatamente despues de comentarla.
- Si la figura todavia no existe, usar el placeholder definido en `informe/main.tex` y describir con precision que grafico falta.

## Redaccion del proyecto

- Describir el sistema como un pipeline completo: simulacion, percepcion, registro y evaluacion.
- Diferenciar con claridad lo que ocurre en tiempo real de lo que se evalua offline.
- Cuando se hable del Go2, enfocarse en el uso concreto dentro del repo actual: plataforma marina simulada, control postural y comparacion contra ground truth.

## Evitar

- Cambiar arbitrariamente entre "nosotros", "se" y formas impersonales en el mismo parrafo.
- Usar lenguaje de marketing.
- Afirmar precision, robustez o generalidad sin datos del repo o sin dejar una marca de pendiente.
