# Brief de escritura para Metodologia

## Funcion de la seccion

La seccion `Metodologia` no deberia leerse como un inventario de paquetes ni
como una repeticion del marco teorico. Su trabajo es otro: explicar con
claridad como se construyo el pipeline, como se organizo la validacion y que
cambia al pasar de simulacion a laboratorio.

La pregunta central que deberia poder responder un lector despues de esta
seccion es:

> como se implemento concretamente el framework y como se preparo la evidencia
> que luego se analiza en experimentacion.

## Idea editorial principal

La metodologia conviene escribirla como una progresion operativa:

1. primero se define el entorno controlado en simulacion;
2. despues se explica como ese entorno produce imagenes y estimaciones;
3. luego se muestra como se registran los datos y como se comparan;
4. finalmente se cuenta que cambia cuando parte de esa logica se traslada al
   laboratorio.

Eso la vuelve mucho mas facil de leer que una organizacion por paquetes o
scripts.

## Regla de lectura

Cada bloque metodologico deberia responder, en este orden:

1. que problema practico resuelve;
2. como se implemento;
3. que entradas y salidas tiene;
4. por que esa decision importo para el pipeline;
5. que limitaciones o simplificaciones introduce.

En la parte de simulacion conviene sumar una regla mas:

6. que hiperparametros se variaron y por que importan.

No alcanza con nombrarlos. Hay que explicar que cambia cuando se modifica
frecuencia, amplitud, desfases o suavizado, porque eso define la dificultad del
movimiento que luego observa el sistema visual.

## Estructura recomendada

### 1. Apertura general de Metodologia

Un bloque corto, de uno o dos parrafos, para explicar:

- por que la metodologia se divide en simulacion y laboratorio;
- que se puede validar en cada entorno;
- por que el pasaje entre ambos tiene valor para la tesis.

### 2. Metodologia en simulacion

Primero una breve introduccion de contexto y despues cuatro bloques claros:

1. generacion del movimiento marino;
2. control postural del Go2 en simulacion;
3. estimacion visual en simulacion;
4. registro y evaluacion offline.

Cada uno deberia explicar una etapa del pipeline, no solo su implementacion.

Dentro de esta etapa conviene fijar desde el comienzo una jerarquia clara entre
las fuentes de imagen:

- `fixed_camera` como caso base, porque simplifica la geometria del problema y
  permite explicar el setup sin sumar movimiento propio del sensor;
- `sjtu_drone` como extension metodologica mas fuerte, porque acerca el
  framework a un escenario mas cercano al objetivo final de aterrizaje.

Tambien conviene dejar claro que las corridas de simulacion se organizaron como
sesiones grabadas en rosbag de un minuto de duracion. Eso hace mas concreto el
pipeline y despues ayuda a ordenar la experimentacion.

### 3. Metodologia en laboratorio

Tambien conviene abrir con una introduccion breve y despues ordenar por tareas:

1. reproduccion del movimiento en el Go2 real;
2. montaje visual con ArUco y camara;
3. comparacion entre movimiento propuesto y senales del robot.

En esta parte el criterio no es "mostrar control absoluto", sino "explicar con
honestidad que se pudo contrastar al salir de Gazebo".

## Criterios de redaccion

- Dar intuicion antes de nombres de nodos o topics.
- Una idea principal por parrafo.
- Evitar derivar a matematica que ya vive en el marco teorico.
- Evitar resultados en esta seccion; aqui se explica el procedimiento.
- Diferenciar siempre online de offline.
- Diferenciar siempre lo confirmado por codigo de lo que depende de memoria o
  de la branch `real`.

## Riesgos a evitar

- mezclar "como funciona" con "que resultado dio";
- describir la simulacion como si ya fuera equivalente al laboratorio;
- sobrecargar la lectura con demasiados nombres internos del repo;
- afirmar detalles del stack `unitree-go2-ros2` que hoy no pueden verificarse
  en este checkout;
- dejar ambigua la relacion entre camara fija y dron.
- dar a `fixed_camera` y `sjtu_drone` exactamente el mismo rol si en la
  narrativa del trabajo no lo tuvieron.

## Figuras que probablemente valen la pena

1. pipeline metodologico completo:
   Gazebo/Go2 -> fuente de imagen -> detector ArUco -> rosbag -> evaluacion.
2. esquema del simulador marino:
   parametros, patron de movimiento, suavizado y publicacion a `/body_pose`.
3. setup visual en simulacion:
   comparacion entre camara fija y dron.
4. figura de laboratorio:
   foto o esquema del montaje real con marcador y camara.

## Presupuesto orientativo

- `Metodologia en simulacion`: 12 a 15 paginas si se profundiza bien.
- `Metodologia en laboratorio`: 5 a 7 paginas si se documenta con evidencia.

No es una cuota. Es solo una referencia para no dejar la seccion ni demasiado
corta ni sobredesarrollada.
