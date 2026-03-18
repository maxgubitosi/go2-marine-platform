# Contexto para asistentes IA (go2-marine-platform)

Proyecto de tesis de grado en Ingeniería en IA (UdeSA). Autores: Máximo Gubitosi, Jack Spolski.

## Qué es este proyecto

- **Objetivo:** Framework de simulación para desarrollar y validar algoritmos de **estimación de pose visual** (ArUco + solvePnP) en escenarios marinos, sin usar hardware real.
- **Setup:** Robot cuadrúpedo Unitree Go2 en Gazebo simula el movimiento de una plataforma marina (roll, pitch, heave). Una cámara (fija o montada en un dron SJTU) observa un marcador ArUco sobre el Go2; se estima la pose en tiempo real y se compara con el ground truth del simulador.
- **Stack:** ROS2 Humble, Gazebo Classic, Python 3.10+, OpenCV (ArUco, solvePnP), paquetes: `go2_tools`, `fixed_camera`, `sjtu_drone`, `unitree-go2-ros2`. Evaluación offline en `aruco_relative_pose/`.

## Informe de tesis

- **Ubicación:** Todo el contenido en un único archivo: `informe/main.tex`.
- **Referencias:** `informe/bibliography.bib`. Figuras en `informe/figures/` (subcarpetas: `setup/`, `results/`, `diagrams/`). Documentos de referencia en `informe/refs/`.
- **Skills de Cursor (escritura del informe):**
  - **thesis-style** (`.cursor/skills/thesis-style/SKILL.md`): estilo de escritura académica en español (voz nosotros/pasiva refleja, narrativa cronológica, captions descriptivos). Referencia de estilo: `informe/refs/PPO_Car_Racing.pdf`.
  - **thesis-guide** (`.cursor/skills/thesis-guide/SKILL.md`): estructura de secciones (Introducción, Marco teórico, Método, Experimentación, Conclusiones, Trabajo futuro) y convenciones LaTeX del proyecto (figuras, tablas, referencias, citas). Desglose detallado en `.cursor/skills/thesis-guide/structure.md`.

Al editar o redactar el informe, seguir las convenciones de esas skills para mantener coherencia y estilo.

## Convenciones de código

- ROS2 packages bajo `src/`; launch files en `launch/`, configs en `config/`.
- Scripts de evaluación y análisis en `aruco_relative_pose/` y `marine_robot_dataset/`.
- Ver README.md para arquitectura completa y comandos de build/run.
