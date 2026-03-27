# Papers para marco teorico y estado del arte

Este documento junta una primera base de referencias para el `Marco
teorico/Estado del arte`. La idea no es llenar la bibliografia de papers, sino
identificar un conjunto corto y util que sostenga el relato tecnico de la
tesis.

## Criterio de seleccion

Se priorizaron referencias que ayuden a justificar al menos uno de estos
bloques:

- por que el problema de aterrizaje en plataformas moviles es dificil;
- como se modela el movimiento marino relevante para nuestro caso;
- por que un cuadrupedo puede usarse como plataforma marina sintetica;
- como se estima pose visual con marcadores fiduciales y PnP;
- que lugar ocupa nuestra propuesta dentro del estado del arte.

## Set minimo recomendado

Si queremos una version corta pero solida del marco teorico, yo arrancaria con
estas referencias.

### 1. Movimiento marino y 6 GDL

`Thor I. Fossen, Ola-Erik Fjellstad (1995). Nonlinear modelling of marine
vehicles in 6 degrees of freedom.`

Link:
[Taylor & Francis / DOI](https://www.tandfonline.com/doi/abs/10.1080/13873959508837004)

Por que sirve:

- es una referencia fuerte para justificar la descripcion del movimiento marino
  en seis grados de libertad;
- ayuda a sostener por que luego nosotros simplificamos a roll, pitch y heave.

Como usarla:

- en la transicion entre problema marino general y simplificacion perceptiva
  que adopta la tesis.

### 2. Marcadores ArUco

`S. Garrido-Jurado, R. Muñoz-Salinas, F. J. Madrid-Cuevas, M. J. Marín-Jiménez
(2014). Automatic generation and detection of highly reliable fiducial markers
under occlusion.`

Link:
[Pattern Recognition / DOI](https://www.sciencedirect.com/science/article/pii/S0031320314000235)

Por que sirve:

- es la referencia base del sistema ArUco;
- conecta directamente con deteccion y estimacion de pose mediante marcadores
  cuadrados.

Como usarla:

- en la subseccion que introduce fiduciales y justifica la eleccion de ArUco.

### 3. PnP

`Vincent Lepetit, Francesc Moreno-Noguer, Pascal Fua (2009). EPnP: An Accurate
O(n) Solution to the PnP Problem.`

Link:
[IJCV abstract / EPnP](https://www.ovid.com/journals/ijcv/pdf/00013850-200981020-00004~epnp-an-accurate-on-solution-to-the-pnp-problem)

Por que sirve:

- da respaldo teorico al problema Perspective-n-Point;
- sirve para conectar las correspondencias 2D-3D con la recuperacion de pose.

Como usarla:

- en la parte donde el relato pasa de deteccion de esquinas a estimacion de la
  pose relativa.

### 4. Control postural de cuadrupedos

`Shamel Fahmi, Carlos Mastalli, Michele Focchi, Claudio Semini (2018). Passive
Whole-body Control for Quadruped Robots: Experimental Validation over
Challenging Terrain.`

Link:
[arXiv](https://arxiv.org/abs/1811.00884)

Por que sirve:

- apoya la idea de control del torso y coordinacion de cuerpo completo en
  cuadrupedos;
- es util para justificar que la postura del trunk puede regularse de manera
  activa sin pensar solo en locomocion horizontal.

Como usarla:

- en la parte del marco teorico donde explicamos por que el Go2 puede actuar
  como plataforma marina sintetica.

### 5. Aterrizaje visual sobre plataforma movil

`Marker-guided auto-landing on a moving platform (2017).`

Link:
[DOI / abstract](https://www.sciencedirect.com/org/science/article/abs/pii/S2049642717000069)

Por que sirve:

- introduce una linea de trabajo directamente relacionada con aterrizaje sobre
  plataformas moviles;
- muestra el uso de vision y marcadores en un problema afín al nuestro.

Como usarla:

- en el estado del arte, como antecedente de aterrizaje visual sobre blanco
  movil.

### 6. Aterrizaje preciso sin GNSS en plataformas moviles

`A. Alarcón et al. (2019). A Precise and GNSS-Free Landing System on Moving
Platforms for Rotary-Wing UAVs.`

Link:
[Sensors](https://www.mdpi.com/1424-8220/19/4/886)

Por que sirve:

- aporta un antecedente fuerte de aterrizaje preciso en plataformas moviles;
- ayuda a mostrar que el problema requiere mediciones relativas robustas y no
  se resuelve solo con GNSS.

Como usarla:

- en el estado del arte, para motivar por que un framework seguro de prueba
  sigue siendo necesario.

### 7. Estado del arte especifico en entorno marino

`Visual Servoed Autonomous Landing of an UAV on a Catamaran in a Marine
Environment (2022).`

Link:
[Sensors](https://www.mdpi.com/1424-8220/22/9/3544)

Por que sirve:

- es muy cercano al contexto de interes final de la tesis;
- conecta UAV, entorno marino y la necesidad de cerrar el loop con vision.

Como usarla:

- en el cierre del estado del arte, para mostrar la cercania con el objetivo
  final del proyecto.

## Referencias complementarias recomendadas

Estas no son estrictamente necesarias para una primera version, pero pueden
mejorar mucho la solidez del estado del arte.

### Fiduciales: comparacion entre familias de marcadores

`Michail Kalaitzakis et al. (2021). Fiducial Markers for Pose Estimation:
Overview, Applications and Experimental Comparison of the ARTag, AprilTag,
ArUco and STag Markers.`

Link:
[Springer / metadata](https://www.researchgate.net/publication/350418791_Fiducial_Markers_for_Pose_Estimation_Overview_Applications_and_Experimental_Comparison_of_the_ARTag_AprilTag_ArUco_and_STag_Markers)

Por que sirve:

- da una vista comparativa de marcadores fiduciales;
- puede ayudar a justificar por que ArUco es una decision razonable, aunque no
  necesariamente optima en todos los escenarios.

Precaucion:

- la entrada que encontre accesible rapido fue metadata/summary; antes de usarla
  en el texto final conviene descargar el paper completo.

### Estabilidad de pose en marcadores

`Burak Benligiray, Cihan Topal, Cuneyt Akinlar (2019). STag: A Stable Fiducial
Marker System.`

Link:
[arXiv](https://arxiv.org/abs/1707.06292)

Por que sirve:

- aporta una comparacion conceptual util para discutir estabilidad de pose y
  jitter en sistemas de marcadores;
- puede ayudar a contextualizar limitaciones de ArUco.

### Plataformas moviles seguidas y aterrizaje con ArUco

`Vision-Based Autonomous Following of a Moving Platform and Landing for an
Unmanned Aerial Vehicle (2023).`

Link:
[Sensors](https://www.mdpi.com/1424-8220/23/2/829)

Por que sirve:

- usa ArUco de forma mas directa en seguimiento y aterrizaje sobre plataforma
  movil;
- puede ser un antecedente muy cercano a la narrativa del proyecto.

### Aterrizaje de precision con fiduciales modernos

`Joshua Springer, Gylfi Þór Guðmundsson, Marcel Kyas (2024). A Precision Drone
Landing System using Visual and IR Fiducial Markers and a Multi-Payload
Camera.`

Link:
[arXiv](https://arxiv.org/abs/2403.03806)

Por que sirve:

- es una referencia reciente;
- muestra hacia donde evoluciono el problema de aterrizaje de precision con
  fiduciales.

### Control postural mas actual en cuadrupedos

`Xiangyu Miao et al. (2025). PALo: Learning Posture-Aware Locomotion for
Quadruped Robots.`

Link:
[arXiv](https://arxiv.org/abs/2503.04462)

Por que sirve:

- no es la referencia base para nuestra metodologia, pero si una señal util del
  interes actual por control locomotor con consignas explicitas de postura;
- puede enriquecer el estado del arte de robotica cuadrupeda si queremos una
  mirada mas moderna.

## Como encajan en el relato del marco teorico

### Bloque 1. El problema general

Usaria principalmente:

- `Marker-guided auto-landing on a moving platform`
- `A Precise and GNSS-Free Landing System on Moving Platforms`
- `Visual Servoed Autonomous Landing of an UAV on a Catamaran in a Marine Environment`

Funcion narrativa:

- mostrar que aterrizar sobre plataformas moviles es un problema real y activo;
- cerrar el bloque diciendo que esas lineas motivan la necesidad de un entorno
  controlado de validacion.

### Bloque 2. Movimiento marino relevante

Usaria principalmente:

- `Fossen and Fjellstad (1995)`

Funcion narrativa:

- pasar del movimiento marino general a la simplificacion en roll, pitch y
  heave adoptada por la tesis.

### Bloque 3. Go2 como plataforma sintetica

Usaria principalmente:

- `Passive Whole-body Control for Quadruped Robots`

Complemento opcional:

- `PALo`

Funcion narrativa:

- justificar que la postura del torso de un cuadrupedo puede comandarse y
  aprovecharse como mecanismo de sintesis de movimiento.

### Bloque 4. Estimacion visual de pose

Usaria principalmente:

- `Garrido-Jurado et al. (2014)`
- `Lepetit et al. (2009)`

Complemento opcional:

- `Kalaitzakis et al. (2021)`
- `STag (2019)`

Funcion narrativa:

- pasar del problema de observar la plataforma a la solucion concreta basada en
  fiduciales y PnP.

### Bloque 5. Estado del arte integrado

Usaria una seleccion corta de:

- `Marker-guided auto-landing on a moving platform`
- `A Precise and GNSS-Free Landing System on Moving Platforms`
- `Vision-Based Autonomous Following of a Moving Platform and Landing for an UAV`
- `Visual Servoed Autonomous Landing of an UAV on a Catamaran in a Marine Environment`
- `A Precision Drone Landing System using Visual and IR Fiducial Markers`

Funcion narrativa:

- mostrar la evolucion del problema;
- ubicar la tesis como framework experimental y perceptivo para ensayar una
  parte de ese desafio con menor riesgo.

## Recomendacion practica

Para no volver el marco teorico pesado, yo no meteria todos estos papers de una
vez. Haria primero una version con:

- 1 referencia base de movimiento marino;
- 1 referencia base de cuadrupedos;
- 2 referencias base de pose estimation visual;
- 2 o 3 referencias de aterrizaje/plataformas moviles.

Y recien despues ampliaria si vemos que el estado del arte queda corto.

## Pendientes

- descargar o confirmar acceso completo a algunas referencias que hoy solo
  quedaron identificadas por metadata/abstract;
- decidir cuales van al marco teorico y cuales conviene reservar para
  `Introduccion` o `Trabajo futuro`;
- si queres, en la siguiente etapa puedo transformar esta lista en una
  propuesta concreta de subsecciones y citas sugeridas para cada una, todavia
  sin tocar `main.TeX`.
