# Metodologia en laboratorio - guia detallada

## Objetivo de este documento

Este documento organiza que deberia contar la subseccion
`Metodologia en laboratorio` y deja visible que informacion todavia falta
relevar para escribirla con seguridad.

## Funcion narrativa

La etapa de laboratorio no deberia presentarse como una replica perfecta de la
simulacion. Su valor metodologico es otro:

- mostrar que el movimiento sintetizado puede trasladarse a un robot real;
- observar que cambia al salir de un entorno totalmente controlado;
- contrastar si las senales reales guardan relacion con el movimiento propuesto.

Ese bloque tiene que leerse como un paso de validacion y no como una promesa de
equivalencia total entre simulacion y mundo real.

## Subestructura recomendada

### 1. Introduccion del pasaje a laboratorio

Esta apertura deberia explicar:

- por que no alcanzaba con la simulacion;
- que se quiso contrastar especificamente en el Go2 real;
- que tipo de incertidumbres aparecen al pasar a laboratorio.

El tono aca tiene que ser honesto: se pierde ground truth perfecto, se gana
contraste fisico.

### 2. Reproduccion del movimiento en el Go2 real

#### Lo minimo que hace falta documentar

- que señal o consigna se le envio al robot;
- que software o controlador se utilizo;
- que grados de libertad se intentaron reproducir;
- que limites de amplitud o seguridad se impusieron;
- como se decidio el tiempo de prueba y la repetibilidad.

#### Decision ya confirmada

- La logica de laboratorio parte de la misma consigna conceptual usada en
  simulacion: `body_pose`.
- Entonces el eje narrativo del pasaje simulacion-real puede sostenerse como
  una continuidad metodologica, aunque despues haya diferencias practicas de
  hardware, estabilidad y medicion.

#### Aclaracion importante para la escritura

- La comparacion principal en laboratorio no se apoya en un ground truth
  externo perfecto, sino en contrastar el movimiento objetivo con lo que miden
  los sensores internos del cuadrupedo.
- Por eso, esta subseccion deberia escribirse como una validacion de
  correspondencia entre consigna y respuesta observada, no como una replica del
  esquema de evaluacion usado en Gazebo.

#### Lo que importa narrativamente

- si el robot siguio exactamente la misma logica que en simulacion o una
  version adaptada;
- que ajustes fueron necesarios por estabilidad, seguridad o hardware;
- que señales quedaron disponibles para comparar despues.

### 3. Estimacion visual con camara sostenida en posicion fija

#### Lo minimo que hace falta documentar

- como se monto el ArUco sobre el robot real;
- como se sostuvo o fijo la camara;
- altura o distancia aproximada;
- si hubo calibracion formal o una configuracion ad hoc;
- que se registro: video, rosbag, pose estimada, imagenes, etc.

#### Lo que importa narrativamente

- en que se parece y en que no se parece este setup al caso de camara fija en
  Gazebo;
- que incertidumbres nuevas introduce una camara sostenida "fija";
- si el objetivo fue cuantitativo, cualitativo o mixto.

#### Decisiones ya confirmadas

- El marcador ArUco estaba pegado sobre el lomo del cuadrupedo.
- La camara de laboratorio era una camara estereo, pero para estas pruebas se
  utilizo solo uno de sus lados.
- Hubo que calibrar esa camara y resolver las condiciones necesarias para poder
  usarla como sensor de prueba.
- Durante la toma, la camara se sostenia de manera fija por encima del
  cuadrupedo.

#### Consecuencia editorial

Conviene contar este setup como una aproximacion experimental controlada, no
como una copia exacta del caso `fixed_camera` de Gazebo. La similitud esta en
la intencion geometrica del montaje; la diferencia esta en que aqui aparecen
calibracion real, fijacion manual y pequeñas incertidumbres de posicionamiento.

### 4. Comparacion entre movimiento propuesto y odometria del robot

#### Lo minimo que hace falta documentar

- que señales se compararon exactamente;
- si se comparo consigna vs odometria, consigna vs IMU, o una combinacion;
- como se alinearon temporalmente las series;
- si la comparacion fue visual, por amplitud/frecuencia, por correlacion
  estadistica o por otra metrica;
- que se considero una correspondencia razonable.

#### Lo que importa narrativamente

- la pregunta no es si el laboratorio calca la simulacion pixel a pixel;
- la pregunta es si el movimiento propuesto y el movimiento observado guardan
  una relacion util para sostener el framework.

#### Decision ya confirmada

- La comparacion de laboratorio se planteo como `objetivo` versus mediciones de
  los sensores internos del cuadrupedo.
- Como hipotesis de trabajo actual, la señal principal para esa comparacion es
  `odom`.

#### Duda que todavia hay que precisar

- Falta identificar con nombre mas fino que señales internas entran en esa
  comparacion si finalmente no fuera solo odometria, por ejemplo IMU,
  estimacion de pose del cuerpo u otra combinacion.

## Lo que hoy no esta en esta branch

- branch `real`;
- scripts de laboratorio;
- rosbags de laboratorio;
- fotos o diagramas del montaje real;
- notas de calibracion y criterio de correlacion;
- resultados versionados del contraste simulacion-real.

Eso significa que esta subseccion todavia depende de informacion de ustedes.

Al mismo tiempo, asumimos como criterio de trabajo que el material existe o
puede generarse. Entonces esta falta de versionado no bloquea la arquitectura
de la escritura: simplemente indica que, antes de cerrar la redaccion final,
habra que bajar ese material al informe en forma de figuras, tablas, plots o
descripciones precisas.

## Como escribirla cuando tengamos el material

El orden recomendado es:

1. contar el objetivo de la prueba real;
2. describir el montaje fisico;
3. explicar las señales registradas;
4. explicar el criterio de comparacion;
5. cerrar con las limitaciones del entorno.

## Riesgos a evitar

- escribirla como si hubiera un ground truth equivalente al de Gazebo;
- ocultar que la camara era sostenida y no rigidamente montada;
- mezclar observaciones cualitativas con afirmaciones cuantitativas fuertes;
- prometer una validacion real mas completa de la que efectivamente hubo.

## Figuras que probablemente hagan falta

1. foto del Go2 real con el marcador montado;
2. foto o esquema del setup de camara en laboratorio;
3. plot comparando consigna y señal real del robot;
4. si existe, secuencia o frame del detector ArUco en laboratorio.

Si esas figuras todavia no estan exportadas, conviene dejar desde ya previsto
que se van a generar y seleccionar despues a partir del material del
laboratorio.

## Informacion minima que necesito para cerrar esta parte

1. que branch o carpeta contiene el material `real`;
2. que señales internas del robot se registraron en laboratorio, tomando `odom`
   como referencia provisoria;
3. como estaba montada la camara;
4. como definieron la comparacion entre movimiento propuesto y movimiento real;
5. que evidencia visual o numerica quieren mostrar en el informe.
