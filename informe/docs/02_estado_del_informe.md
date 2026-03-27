# Estado actual del informe

## Archivo principal

- Informe: `informe/main.TeX`
- Bibliografia: `informe/bibliography.bib`
- PDF ya compilado en este checkout: `informe/main.pdf`

## Que ya esta escrito

### Marco teorico

Hay texto avanzado en:

- modelado simplificado de roll, pitch y heave;
- control postural del Go2 en simulacion;
- fundamentos de ArUco, camara pinhole y `solvePnP`.

### Metodo

Hay texto avanzado en:

- simulador marino;
- control postural del Go2;
- deteccion visual con camara fija y dron;
- detalles generales de implementacion del pipeline.

Tambien ya hay dos figuras reales insertadas:

- `figures/images/aruco_id0_dict_6x6_250.png`
- `figures/images/aruco_detection_frame.png`

### Secciones todavia muy abiertas

- `Introduccion`
- `Experimentacion/Simulacion`
- `Experimentacion/Real`
- `Conclusiones`
- `Trabajo futuro`
- `Abstract`

## Placeholders detectados en `main.TeX`

### Citas pendientes

Solo hay dos referencias en `bibliography.bib` y ambas son de OpenCV. Faltan,
como minimo, fuentes para:

- cinematica y convenciones de movimiento marino en 6 GDL;
- cinematica o control postural de cuadrupedos.

### Figuras pendientes

Hay placeholders para:

- arquitectura del simulador marino;
- comparacion entre fuentes de imagen;
- pipeline completo desde Gazebo hasta evaluacion offline.

### Parte real pendiente

La subseccion `Experimentacion/Real` ya esta marcada como `REAL PENDIENTE`,
lo cual es consistente con la branch actual. Sin embargo, por lo que aclaro el
usuario, esa parte no es accesoria: forma parte del cierre metodologico de la
tesis y despues habra que integrarla con cuidado.

## Riesgos de consistencia

- El metodo ya menciona internamente CHAMP, `quadruped_controller_node`,
  `state_estimation_node` y EKFs de `robot_localization`, pero ese stack no esta
  en el checkout actual.
- Si esos detalles salieron de otra branch, de notas internas o de un repo
  externo, conviene validarlos antes de consolidarlos en el texto final.
- El informe todavia no explicita con suficiente claridad el objetivo macro del
  proyecto: construir un framework para probar aterrizaje de drones en
  plataformas marinas. Ese hilo conductor deberia aparecer desde la
  introduccion y reaparecer en conclusiones.

## Orden recomendado para seguir escribiendo

1. Cerrar `Experimentacion/Simulacion` con evidencia ya disponible.
2. Definir desde ahora la estructura final para que la lectura sea cronologica y
   facil de seguir: simulacion primero, validacion real despues.
3. Limpiar y reforzar `Metodo` con solo detalles que podamos sostener por codigo
   o material complementario.
4. Completar `Introduccion` cuando ya este claro el alcance final.
5. Recien despues escribir `Conclusiones`, `Trabajo futuro` y `Abstract`.

## Que conviene no inventar

- resultados numericos de camara fija si no aparecen en ningun output;
- detalle fino del control del Go2 si no tenemos el fork presente;
- validacion con hardware real antes de revisar la branch `real`;
- decisiones experimentales que ustedes recuerdan pero no quedaron guardadas.
