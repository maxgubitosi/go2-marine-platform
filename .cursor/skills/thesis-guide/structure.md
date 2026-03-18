# Estructura del informe (Go2 marine platform)

Contenido esperado por sección. El informe vive en un único archivo: [informe/main.tex](informe/main.tex).

## Introducción (\label{intro})

- Motivación: por qué un framework de simulación marina para robots cuadrúpedos (drones, plataformas en movimiento, aterrizaje autónomo).
- Problema: necesidad de validar algoritmos de estimación de pose visual sin arriesgar hardware real.
- Contribuciones del trabajo (enumeradas).
- Breve descripción de la estructura del documento.

## Marco teórico (\label{mt})

### Interpolación de olas

- Modelo de olas (sinusoidal, JONSWAP u otro usado): ecuaciones, parámetros (amplitud, período, etc.).
- Relación con el movimiento del robot (roll, pitch, heave).

### Cinemática directa e inversa de un robot cuadrúpedo

- Modelo del Unitree Go2 (URDF, CHAMP si aplica).
- Cómo se traduce una pose deseada (ángulos de ola) a posiciones de articulaciones.

### Detección de patrones visuales

- ArUco: qué son los marcadores, cómo se detectan (cv2.aruco, solvePnP).
- Estimación de pose 6DoF a partir de la cámara.

## Método

- Cómo se implementó cada subsistema en el proyecto:
  - Interpolación de olas → nodo/simulador (marine_platform_simulator, /body_pose).
  - Cinemática → control del Go2 en Gazebo.
  - Detección visual → fixed_camera y/o cámara en dron (ArUco + solvePnP).
- Detalles de implementación: ROS2, Gazebo, paquetes (go2_tools, fixed_camera, sjtu_drone), frecuencias, temas.

## Experimentación

### Simulación

- Setup: Gazebo, cámara fija o dron, escenario.
- Métricas: error de posición (Euclidiano), error de orientación (p. ej. yaw), tasa de detección (Hz).
- Resultados cuantitativos y cualitativos (gráficos, tablas). Comparación con ground truth del simulador.

### Real

- Si aplica: pruebas con hardware real, diferencias o limitaciones respecto a simulación.

## Conclusiones

- Resumen de logros: precisión alcanzada, viabilidad del framework.
- Limitaciones actuales.

## Trabajo futuro

- Mejoras planeadas: control de aterrizaje autónomo, más escenarios, experimentos en real, etc.
