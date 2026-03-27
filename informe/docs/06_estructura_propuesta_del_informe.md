# Estructura propuesta del informe

Esta propuesta busca que el informe sea facil de leer sin perder tono
academico. La idea es contar una historia clara: primero construimos el entorno
controlado en simulacion, despues lo usamos para validar percepcion visual, y
finalmente llevamos parte de esa logica al laboratorio para verificar cuanto se
parece el movimiento sintetizado al comportamiento real del robot.

El marco general que ordena toda la tesis es que este sistema no se construye
como fin en si mismo, sino como framework para poder probar aterrizaje de
drones sobre plataformas marinas en condiciones controladas y luego cada vez
mas realistas.

## Principio organizador

No conviene estructurar el informe solo por paquetes de software. Eso sirve
para el repo, pero no necesariamente para un lector. Para el informe conviene
organizar por preguntas de investigacion:

1. como simular una plataforma marina con un cuadrupedo;
2. como estimar visualmente su pose desde distintas camaras;
3. en que medida esa simulacion se relaciona con el comportamiento real;
4. como todo eso habilita futuros ensayos de aterrizaje sobre plataformas
   moviles.

## Estructura de alto nivel

### 1. Introduccion

- problema: drones o sistemas visuales sobre plataformas marinas moviles;
- dificultad de validar directamente con hardware real;
- idea central: usar un Go2 como plataforma marina sintetica;
- objetivo doble:
  - construir un framework para probar aterrizaje de drones;
  - contrastar luego parte de ese comportamiento con ensayos reales.

### 2. Marco teorico

- movimiento marino simplificado en roll, pitch y heave;
- control postural del cuadrupedo para inducir movimiento del torso;
- frames, pose relativa y convenciones geometricas;
- ArUco, modelo pinhole y `solvePnP`.

### 3. Metodo

#### 3.1 Metodologia en simulacion

Breve introduccion:

- que parte del problema resolvemos en un entorno controlado;
- por que simulacion fue el primer paso del trabajo;
- que componentes del framework quedan cubiertos en esta etapa.

Subsecciones detalladas:

- simulacion base del Unitree en ROS2 y Gazebo;
- agregado de la tabla y del marcador sobre el lomo;
- generacion del movimiento de oleaje.

- estimacion visual en simulacion con camara fija;
- incorporacion del `sjtu_drone` como segundo escenario;
- criterio de registro y evaluacion offline.

#### 3.2 Metodologia en laboratorio

Breve introduccion:

- que motivacion tuvo el pasaje de simulacion a laboratorio;
- que partes del framework se buscaron contrastar en el robot real;
- que cambia al pasar de un entorno totalmente controlado a uno fisico.

Subsecciones detalladas:

- reproduccion del movimiento propuesto en el Go2 real;
- montaje del ArUco y de la camara sostenida en posicion fija;
- comparacion entre movimiento propuesto y odometria del robot.

#### 3.3 Criterio de comparacion y validacion

- reconstruccion de GT en simulacion;
- metricas de posicion y orientacion;
- criterio de correlacion entre movimiento propuesto y movimiento real;
- separacion entre estimacion online y analisis offline.

### 4. Experimentacion

#### 4.1 Experimentos en simulacion

- condiciones de setup;
- resultados con camara fija;
- resultados con dron;
- comparacion e interpretacion.

#### 4.2 Experimentos en laboratorio

- reproduccion del movimiento en el Go2 real;
- montaje del ArUco y de la camara sostenida en posicion fija;
- comparacion entre movimiento propuesto y señales publicadas por el robot;
- alcance y limites de esta validacion.

Nota: esta subseccion debe quedar pendiente hasta relevar la branch o material
real correspondiente.

### 5. Conclusiones

- que demostro la simulacion;
- que mostro la comparacion con el robot real;
- como estos resultados aportan una base creible para futuros ensayos de
  aterrizaje;
- limitaciones de la validacion alcanzada.

### 6. Trabajo futuro

- cerrar el loop hacia aterrizaje autonomo;
- mejorar calibracion, escenarios y evaluacion real;
- extender comparacion simulacion-real.

## Ventajas de esta estructura

- mantiene una lectura natural de problema a solucion y luego a validacion;
- evita mezclar simulacion y laboratorio dentro del mismo bloque explicativo;
- permite que el lector entienda primero el sistema controlado y despues la
  comparacion con el mundo real;
- deja al dron como una extension del caso fijo, no como un bloque aislado.

## Decision editorial importante

Si esta estructura les cierra, el `Metodo` deberia describir solo lo que hoy
podemos sostener con evidencia tecnica del repo, y la parte de laboratorio
deberia reservarse en `Experimentacion` como validacion posterior. Eso ayuda a
mantener el informe prolijo y evita contaminar el cuerpo tecnico con partes que
todavia no relevamos bien. A la vez, la introduccion y las conclusiones deberian
dejar claro que todo el framework apunta a aterrizaje de drones, aunque la
tesis no cierre todavia con un controlador de aterrizaje completo.
