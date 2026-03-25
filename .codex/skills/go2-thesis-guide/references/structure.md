# Estructura del informe Go2 marine

## Introduccion

- Motivar el problema de percepcion para plataformas marinas en movimiento.
- Explicar por que conviene validar primero en simulacion antes de arriesgar hardware.
- Presentar el objetivo del framework y los aportes del trabajo.
- Aclarar que la parte de laboratorio con el Go2 real se incorporara mas adelante.

## Marco teorico

- Modelado simplificado del movimiento marino en roll, pitch y heave.
- Frames y transformaciones entre mundo, robot, marcador y camara.
- Fundamentos de ArUco, modelo pinhole y `solvePnP`.
- Teoria del Go2 limitada al control postural y frames realmente usados por el sistema.

## Metodo

- Pipeline completo desde Gazebo hasta la evaluacion offline.
- Simulador marino y generacion de poses del cuerpo.
- Fuentes de imagen: camara fija y SJTU drone.
- Deteccion ArUco en tiempo real.
- Reconstruccion del ground truth y comparacion offline.
- Detalles de implementacion en ROS2, topics, launch files y configuraciones clave.

## Experimentacion

- Setup de simulacion.
- Metricas de posicion, orientacion y deteccion.
- Resultados disponibles del branch actual.
- Subsection `Real` reservada con placeholders.

## Conclusiones

- Hallazgos demostrados con simulacion.
- Limitaciones actuales.
- Dependencias de la validacion real todavia no integrada.

## Trabajo futuro

- Integracion del branch `real`.
- Mejoras de calibracion, mas escenarios y control de aterrizaje autonomo.
