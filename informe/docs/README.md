# Docs de apoyo para escribir el informe

Esta carpeta resume el estado actual del proyecto y del informe a partir del
checkout disponible hoy. La idea es usarla como base de trabajo para redactar
sin perder de vista tres cosas:

- que esta branch documenta principalmente la parte de simulacion;
- que hay detalles del pipeline confirmados por codigo y otros que todavia
  requieren validacion manual;
- que varias decisiones metodologicas y experimentales seguramente viven en la
  memoria de ustedes y no quedaron reflejadas en el repo.

## Alcance de este relevamiento

Se revisaron especialmente estos insumos:

- `README.md`
- `informe/main.TeX`
- `informe/bibliography.bib`
- `src/go2_tools/`
- `src/fixed_camera/`
- `src/sjtu_drone/`
- `aruco_relative_pose/`
- `marine_robot_dataset/`
- `rosbags/`
- outputs y figuras ya guardados en el repo

No se pudo revisar en este checkout:

- el fork `unitree-go2-ros2` mencionado en el README y en el metodo;
- la branch `real`;
- rosbags y datasets completos, porque no estan versionados en el repo actual.

## Como usar esta carpeta

- `01_resumen_del_proyecto.md`: mapa tecnico del sistema y hechos confirmados.
- `02_estado_del_informe.md`: que ya esta escrito en `main.TeX`, que falta y
  por donde conviene seguir.
- `03_material_disponible.md`: figuras, resultados y evidencia reutilizable.
- `04_huecos_y_preguntas.md`: inconsistencias detectadas y preguntas para
  completar lo que no aparece en codigo o documentos.
- `05_criterios_de_redaccion_y_lectura.md`: reglas de estructura y legibilidad
  para mantener tono academico sin volver el texto pesado.
- `06_estructura_propuesta_del_informe.md`: propuesta de estructura global del
  informe basada en la progresion real del proyecto.
- `07_marco_teorico_como_relato.md`: guia para escribir el marco teorico y el
  estado del arte con una logica narrativa, no enciclopedica.
- `08_papers_para_marco_teorico.md`: base inicial de papers y referencias
  primarias para sostener el marco teorico y el estado del arte.
- `09_presupuesto_de_extension.md`: estimacion de paginas y caracteres por
  seccion para llegar a un informe final de alrededor de 80 paginas.

## Criterio de confianza

- Confirmado por codigo: se vio en nodos, launch files, configs o scripts.
- Respaldado por artefactos: aparece en figuras, README u outputs guardados.
- Requiere validacion: se infiere de texto existente o depende de material no
  presente en este checkout.
