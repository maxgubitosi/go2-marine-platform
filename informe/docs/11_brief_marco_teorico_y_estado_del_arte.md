# Brief de escritura: Marco teorico y Estado del arte

Este documento define como deberia construirse el bloque `Marco teorico/Estado
del arte` del informe. No es redaccion final: es un mapa de discovery para que
despues podamos escribir con una logica narrativa clara y con referencias bien
alineadas al problema de la tesis.

## Funcion de la seccion

Este bloque tiene que lograr tres cosas:

1. dar las herramientas conceptuales minimas para entender la metodologia;
2. mostrar que el problema ya fue abordado parcialmente desde varias lineas de
   trabajo;
3. explicar por que nuestra tesis necesita integrar simulacion, percepcion
   visual y validacion experimental en un mismo framework.

## Meta de extension

- objetivo orientativo total: `14-18 paginas`
- texto estimado: `26.000-36.000` caracteres con espacios

Distribucion sugerida:

- `Marco teorico`: `8-10 paginas`
- `Estado del arte`: `5-8 paginas`

## Pregunta que debe responder

`Que hace falta entender y que antecedentes hay que mirar para justificar un
framework orientado a probar aterrizaje de drones sobre plataformas marinas?`

## Decision narrativa principal

No conviene escribir esta seccion como:

- definicion 1;
- definicion 2;
- paper 1;
- paper 2.

Conviene escribirla como una secuencia de necesidades:

1. cual es el problema general;
2. que parte del movimiento importa;
3. como puede sintetizarse ese movimiento;
4. como puede medirse visualmente;
5. que muestran y que no resuelven del todo los trabajos previos.

## Estructura interna sugerida

### Bloque 1. Problema general y contexto

Objetivo:

- instalar el contexto de plataformas marinas moviles y de operaciones con UAVs;
- mostrar por que el aterrizaje o la interaccion con plataformas moviles exige
  precision relativa y validacion segura.

Que deberia aparecer:

- dificultad del escenario;
- combinacion de movimiento, percepcion y riesgo experimental;
- necesidad de reducir incertidumbre antes de llegar al caso final.

Rol narrativo:

- abrir el relato;
- preparar el terreno para justificar simulacion y percepcion visual.

Peso estimado:

- `1,5-2 paginas`

Referencias sugeridas:

- trabajos de aterrizaje sobre plataforma movil;
- trabajos de aterrizaje preciso sin GNSS;
- trabajos en entorno marino.

### Bloque 2. Movimiento marino relevante para el problema

Objetivo:

- presentar la descripcion general del movimiento marino;
- justificar la simplificacion a roll, pitch y heave en este trabajo.

Que deberia aparecer:

- seis grados de libertad de una plataforma marina;
- por que no todos impactan igual en nuestro caso;
- relacion entre esas componentes y lo que ve la camara.

Idea clave a dejar explicita:

- el recorte a roll, pitch y heave no se hace porque los otros grados de
  libertad no importen en general, sino porque en esta tesis se busca aislar el
  subconjunto de movimientos que mas altera la pose observada del marcador en
  el setup actual.

Rol narrativo:

- pasar del problema general a la primera decision de modelado de la tesis.

Peso estimado:

- `2-2,5 paginas`

Referencia base sugerida:

- Fossen y Fjellstad.

### Bloque 3. Sintesis del movimiento con un cuadrupedo

Objetivo:

- explicar por que un cuadrupedo puede usarse como plataforma marina sintetica;
- introducir la idea de control postural del torso.

Que deberia aparecer:

- postura del torso y configuracion de patas;
- nociones de cinematica o control postural relevantes;
- diferencia entre locomocion horizontal y uso del cuerpo como plataforma.

Rol narrativo:

- justificar la eleccion metodologica mas singular del trabajo: usar el Go2
  como sustituto de una plataforma marina.

Peso estimado:

- `2-2,5 paginas`

Referencias sugeridas:

- paper de whole-body control en cuadrupedos;
- referencia complementaria mas actual si hace falta reforzar estado del arte.

### Bloque 4. Medicion visual de la pose

Objetivo:

- introducir las herramientas de percepcion necesarias para el problema;
- conectar marcadores, geometria de camara y recuperacion de pose.

Que deberia aparecer:

- marcadores fiduciales;
- ArUco;
- modelo pinhole;
- correspondencias 2D-3D;
- PnP y `solvePnP`.

Rol narrativo:

- responder la pregunta de como observar la plataforma una vez que ya puede
  moverse.

Peso estimado:

- `2,5-3 paginas`

Referencias sugeridas:

- Garrido-Jurado et al.;
- Lepetit et al.;
- paper comparativo de fiduciales si queremos contextualizar la eleccion.

### Bloque 5. Estado del arte integrado

Objetivo:

- mostrar las lineas de trabajo previas mas cercanas al objetivo final;
- identificar el hueco donde se ubica la tesis.

Lineas que conviene cubrir:

- aterrizaje visual en plataformas moviles;
- aterrizaje o servoing en entornos marinos;
- sistemas basados en fiduciales;
- validacion controlada y testing seguro antes de hardware final.

Rol narrativo:

- cerrar el bloque conceptual mostrando que nuestra tesis no compite con un
  controlador final de aterrizaje, sino que construye el marco experimental que
  hace viable estudiarlo.

Peso estimado:

- `5-6 paginas`

## Orden sugerido de lectura dentro del bloque

Una secuencia razonable seria:

1. el problema de operar sobre plataformas moviles;
2. movimiento marino y recorte perceptivo;
3. Go2 como plataforma marina sintetica;
4. estimacion visual de pose;
5. antecedentes de aterrizaje y hueco de integracion.

## Formula de escritura para cada subseccion

Cada subseccion deberia seguir este patron:

1. abrir con una necesidad;
2. introducir el concepto teorico;
3. conectar con una o dos referencias fuertes;
4. cerrar explicando por que eso importa en la tesis.

## Mapa de papers por bloque

### Bloque 1. Problema general

Usar principalmente:

- `Marker-guided auto-landing on a moving platform`
- `A Precise and GNSS-Free Landing System on Moving Platforms`
- `Visual Servoed Autonomous Landing of an UAV on a Catamaran in a Marine Environment`

Idea que sostienen:

- aterrizar o acoplar UAVs a plataformas moviles es un problema vigente y
  desafiante;
- el entorno marino agrega dificultad real;
- la percepcion relativa es central.

### Bloque 2. Movimiento marino

Usar principalmente:

- `Nonlinear Modelling of Marine Vehicles in 6 Degrees of Freedom`

Idea que sostiene:

- el modelo marino general existe y nuestra tesis toma de ahi un recorte
  deliberado hacia roll, pitch y heave.

### Bloque 3. Cuadrupedo como plataforma

Usar principalmente:

- `Passive Whole-body Control for Quadruped Robots`

Complemento opcional:

- `PALo`

Idea que sostienen:

- el torso de un cuadrupedo puede gobernarse mediante control postural y
  coordinacion de patas;
- eso vuelve razonable su uso como plataforma sintetica.

### Bloque 4. Pose visual

Usar principalmente:

- `Automatic generation and detection of highly reliable fiducial markers under occlusion`
- `EPnP: An Accurate O(n) Solution to the PnP Problem`

Complemento opcional:

- `Fiducial Markers for Pose Estimation`
- `STag`

Idea que sostienen:

- un marcador cuadrado permite estimar pose relativa de manera robusta y
  conveniente;
- PnP da el respaldo geometrico de esa estimacion.

### Bloque 5. Estado del arte integrado

Usar una seleccion breve de:

- `A Precise and GNSS-Free Landing System on Moving Platforms`
- `Vision-Based Autonomous Following of a Moving Platform and Landing for an UAV`
- `Visual Servoed Autonomous Landing of an UAV on a Catamaran in a Marine Environment`
- `A Precision Drone Landing System using Visual and IR Fiducial Markers`

Idea que sostienen:

- hay una linea madura hacia aterrizaje de precision;
- nuestra tesis aporta infraestructura experimental y validacion previa, no un
  sistema final cerrado.

## Lo que esta seccion no deberia hacer

- no deberia transformarse en una lista larga de papers;
- no deberia meter teoria que luego no reaparece;
- no deberia usar demasiadas referencias por parrafo;
- no deberia discutir implementacion fina del repo;
- no deberia adelantar resultados numericos.

## Criterio para el estado del arte

El estado del arte deberia responder tres preguntas:

1. que ya se hizo sobre aterrizaje o seguimiento de plataformas moviles;
2. que herramientas perceptivas suelen usarse;
3. que necesidad sigue existiendo y que lugar ocupa ahi nuestra tesis.

Si un paper no ayuda a responder alguna de esas preguntas, probablemente no haga
falta incorporarlo.

## Posible cierre de la seccion

El cierre del bloque deberia dejar una idea como esta:

- el problema final del aterrizaje sobre plataformas marinas ya fue abordado
  desde distintas perspectivas;
- sin embargo, sigue siendo valioso contar con un framework que permita
  desacoplar, probar y validar de forma segura el movimiento de la plataforma y
  la estimacion visual antes de cerrar el loop completo de aterrizaje.

## Pendientes de discovery

Antes de pasar a escritura final convendria decidir:

- si `Estado del arte` va a vivir dentro de `Marco teorico` o como subseccion
  claramente diferenciada;
- cuantas referencias queremos en una primera version;
- si queremos incluir una hipotesis mas explicita sobre por que simulacion y
  laboratorio deben coexistir;
- que peso narrativo va a tener el dron dentro del relato conceptual.
