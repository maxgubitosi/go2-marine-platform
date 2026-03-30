# Preguntas prioritarias para cerrar Metodologia

Estas son las preguntas que hoy mas destraban una metodologia profunda,
prolija y consistente con lo que realmente hicieron.

## Simulacion

1. Configuracion de referencia acordada hasta ahora:
   usar la parametrizacion base con la que corre la simulacion en el repo
   (`wave_frequency`, amplitudes, desfases, suavizado y `rate_hz` por default).
   Si despues aparece una corrida final distinta, se ajusta.

2. Tenes el fork o branch de `unitree-go2-ros2` que realmente usaron?
   Sin eso puedo escribir la arquitectura general, pero no validar fino la
   parte del controlador del Go2.

3. Alguna vez usaron una altura de camara fija distinta de `2.0 m` en las
   corridas del informe?

## Laboratorio

4. Como estaba montado el ArUco en el laboratorio?
   Sobre una tabla, directo sobre el robot, con soporte impreso, etc.

5. Como estaba resuelta la camara del laboratorio?
   Me sirve altura o distancia aproximada, si estaba sostenida por una persona
   o por una estructura, y si tenia calibracion formal o no.

6. Señal de referencia provisoria para el laboratorio:
   `odom`.
   Si despues confirman que entraba otra señal o una combinacion, se corrige.

7. Como definieron esa comparacion?
   Necesito saber si fue por inspeccion visual, por series temporales
   alineadas, por amplitud/frecuencia o por alguna metrica estadistica.

8. Tenes bags, videos, fotos, plots o notas del laboratorio fuera del repo?
   Si existen, esa evidencia va a ordenar mucho mejor la subseccion real.

## Decisiones de escritura

9. Queres que deje explicitadas las limitaciones practicas del desarrollo
   dentro de Metodologia?
   Pienso en cosas como drift del dron, camara sostenida a mano, cambios de
   topics, offsets de spawn o diferencias entre branches.

10. Hubo decisiones o cambios de enfoque que quieras que Metodologia cuente
    como parte del proceso?
    Por ejemplo: primero camara fija, despues dron, o primero simulacion pura y
    despues validacion real.
