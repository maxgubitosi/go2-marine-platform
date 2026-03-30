# Estado actual del informe

## Archivo principal

- Informe: `informe/main.TeX`
- Bibliografia: `informe/bibliography.bib`
- PDF compilado: `informe/main.pdf`

## Que ya esta escrito

### Introduccion y marco teorico

Hay texto avanzado en:

- introduccion del problema y del objetivo macro del framework;
- modelado simplificado de roll, pitch y heave;
- control postural del Go2 en simulacion;
- fundamentos de ArUco, camara pinhole y `solvePnP`.

### Metodo

Hay texto avanzado en:

- metodologia en simulacion:
  - generacion del movimiento marino;
  - control postural del Go2;
  - percepcion con `fixed_camera` y `sjtu_drone`;
  - registro y evaluacion offline;
- metodologia en laboratorio:
  - dificultades del pasaje simulacion-laboratorio;
  - reproduccion del movimiento con `marine_platform_simulator` en `mode=real`;
  - setup visual con camara estereo usada como monocular;
  - comparacion entre referencia, comando y respuesta del robot.

Tambien ya hay figuras insertadas en el cuerpo del informe:

- `figures/images/aruco_id0_dict_6x6_250.png`
- `figures/images/aruco_detection_frame.png`

### Experimentacion

La seccion `Experimentacion y resultados` ya quedo estructurada en el informe:

- simulacion:
  - diseno experimental;
  - metricas;
  - caso base `fixed_camera`;
  - caso fuerte `sjtu_drone`;
  - sintesis;
- laboratorio:
  - presentacion del material experimental;
  - fidelidad del camino de comando;
  - comparacion entre movimiento esperado y respuesta del robot.

## Secciones todavia abiertas

- `Experimentacion/Simulacion` en su parte analitica final
- `Conclusiones`
- `Trabajo futuro`
- `Abstract`

## Placeholders detectados en `main.TeX`

### Figuras pendientes

Hay placeholders para:

- arquitectura del simulador marino;
- comparacion entre fuentes de imagen;
- pipeline completo desde Gazebo hasta evaluacion offline;
- setup de laboratorio;
- comparacion objetivo-comando-respuesta en laboratorio;
- figuras cuantitativas de simulacion y laboratorio todavia no exportadas.

### Analisis pendientes

Persisten placeholders de analisis en la parte de simulacion, sobre todo en:

- interpretacion del baseline `fixed_camera`;
- analisis detallado de la corrida principal del `sjtu_drone`;
- comparacion entre corridas del dron;
- sintesis final de la evidencia en simulacion.

La parte de laboratorio ya no esta pendiente a nivel estructural, pero todavia
conviene sumar figuras reales y, si aparece el material, una evaluacion visual
mas fuerte sobre `/aruco/pose`.

## Riesgos de consistencia

- El metodo menciona detalles del stack del Go2 que dependen de un repo externo
  no presente en este checkout.
- En laboratorio, la redaccion ya mejoro mucho, pero todavia hay un punto a
  confirmar antes del cierre final: si el ArUco real medido fue de `0.20 m` o
  de `0.50 m`.
- La parte experimental real hoy sostiene mejor la reproduccion del movimiento
  del Go2 que una validacion cuantitativa cerrada de la pose visual.

## Orden recomendado para seguir escribiendo

1. Generar las figuras faltantes de simulacion y reemplazar los bloques de
   analisis placeholder por redaccion final.
2. Exportar las figuras clave de laboratorio a partir del bag real y de los
   scripts ya identificados.
3. Cerrar `Conclusiones` y `Trabajo futuro` una vez consolidados los resultados.
4. Dejar `Abstract` para el final, cuando ya este estabilizada la narrativa
   completa del informe.

## Que conviene no inventar

- resultados numericos de `fixed_camera` si no aparecen en ningun output;
- detalle fino del control del Go2 si no tenemos el fork presente;
- una precision visual real que hoy no este respaldada por bags o plots;
- decisiones experimentales que ustedes recuerdan pero no quedaron guardadas.
