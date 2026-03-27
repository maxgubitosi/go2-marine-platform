# Marco teorico como relato

Este documento fija una decision de escritura para la fase de discovery del
informe: el `Marco teorico/Estado del arte` no deberia escribirse como un
catalogo de conceptos o una lista de papers, sino como una historia tecnica que
explique por que la tesis termino tomando la forma que tomo.

## Idea central

El lector no deberia sentir que entra a una enciclopedia. Deberia sentir que el
texto lo lleva, paso a paso, desde el problema general hasta las herramientas
conceptuales que hicieron posible la metodologia.

En nuestro caso, la pregunta guia podria ser:

`Que hace falta entender para construir un framework que permita probar
aterrizaje de drones sobre plataformas marinas?`

## Estructura narrativa recomendada

### 1. El problema de fondo

Abrir con el problema mayor:

- aterrizar drones sobre plataformas marinas es dificil;
- la plataforma se mueve;
- la percepcion cambia con ese movimiento;
- probar directamente en hardware real es costoso y riesgoso.

Este bloque no deberia resolver nada todavia. Solo instalar la necesidad del
trabajo.

### 2. Que parte del movimiento importa

Una vez instalado el problema, aparece la primera pregunta tecnica:

`Como describimos el movimiento de una plataforma marina de una forma util para
este trabajo?`

Ahi entra la explicacion de:

- seis grados de libertad marinos;
- por que en esta tesis nos concentramos en roll, pitch y heave;
- por que esa simplificacion es razonable desde el punto de vista perceptivo.

La justificacion deberia quedar muy clara:

- `roll` y `pitch` modifican la orientacion observada del plano del marcador;
- `heave` modifica la distancia camara-objetivo y, por ende, la escala aparente;
- en el setup de esta tesis `x`, `y` y `yaw` no son el foco porque la
  simulacion los mantiene anulados para aislar las perturbaciones visuales mas
  relevantes en una primera validacion del framework.

La teoria entra como respuesta a una necesidad concreta, no como bloque aislado.

### 3. Como sintetizar ese movimiento

Despues de definir el movimiento relevante, la narrativa deberia pasar a una
segunda pregunta:

`Como generamos ese movimiento en un entorno controlado sin construir un barco
completo?`

Ahi aparece el Go2:

- control postural del cuadrupedo;
- relacion entre postura del torso y configuracion de las patas;
- por que esa idea permite usar al robot como plataforma marina sintetica.

Este es el lugar natural para introducir cinematica, postura y frames del robot.

### 4. Como observar la plataforma

Una vez que la plataforma ya puede moverse, aparece otra necesidad:

`Como medimos visualmente la pose de esa plataforma?`

Ahi entran:

- marcadores ArUco;
- modelo pinhole;
- correspondencias 2D-3D;
- `solvePnP`.

Otra vez, la teoria aparece como respuesta al problema de observacion.

### 5. Por que hace falta un framework y no solo un algoritmo

Recien despues conviene abrir el estado del arte con mas claridad:

- que existe sobre aterrizaje en barcos o plataformas moviles;
- que existe sobre pose estimation visual;
- que existe sobre simulacion o validacion segura;
- que hueco deja abierta esa literatura.

La funcion de este bloque no es resumir todo, sino mostrar por que una tesis
como esta necesita integrar simulacion, percepcion y validacion.

## Formula practica para cada subseccion

Cada subseccion del marco teorico deberia seguir, idealmente, esta secuencia:

1. plantear una pregunta o necesidad;
2. introducir la idea teorica que la responde;
3. mencionar brevemente que resuelve la literatura o el enfoque clasico;
4. cerrar diciendo por que eso importa especificamente en nuestra tesis.

## Tono recomendado

Tiene que sonar academico, pero no pesado. Eso significa:

- menos inventario de definiciones;
- mas progresion argumental;
- menos `Autor A hizo X, Autor B hizo Y` como unica estructura;
- mas `este problema requiere tal concepto, y por eso lo introducimos aca`.

## Que evitar

- subsecciones que parecen apuntes de clase;
- definiciones largas que despues no se usan;
- bloques de literatura sin puente con la tesis;
- abrir demasiados temas en paralelo;
- usar formulas antes de explicar que problema resuelven.

## Ejemplo de tono

En lugar de escribir:

`Los movimientos marinos se describen mediante seis grados de libertad...`

conviene abrir algo mas narrativo, por ejemplo:

`Antes de discutir la estimacion visual, es necesario precisar que aspectos del
movimiento de una plataforma marina afectan de forma mas directa la observacion
del marcador. Aunque la dinamica completa de una embarcacion involucra seis
grados de libertad, en nuestro problema no todas esas componentes tienen el
mismo impacto perceptivo.`

En lugar de escribir:

`Los marcadores ArUco son patrones fiduciales bidimensionales...`

conviene algo como:

`Una vez definido el movimiento de la plataforma, el problema pasa a ser como
medirlo desde imagen. En nuestro caso, esa medicion se apoya en marcadores
ArUco, porque permiten obtener correspondencias geometricas suficientes para
recuperar la pose relativa entre camara y objeto a partir de un unico patron.`

## Posible estructura concreta para nuestro caso

Si mas adelante esta logica se lleva al texto, una version razonable del
`Marco teorico/Estado del arte` podria ser:

1. El problema de operar y validar sobre plataformas marinas moviles.
2. Modelado simplificado del movimiento marino relevante para percepcion.
3. Control postural de cuadrupedos como mecanismo de sintesis de movimiento.
4. Estimacion de pose visual con marcadores fiduciales.
5. Estado del arte en aterrizaje, simulacion y validacion visual.
6. Sintesis: por que un framework integrado como el nuestro tiene sentido.

## Decision editorial para discovery

Mientras sigamos en discovery, este documento funciona como criterio. No
obliga todavia a fijar el texto final del `main.TeX`, pero si a evaluar cada
idea futura con esta pregunta:

`Esto ayuda a contar la historia del problema y de nuestras decisiones, o solo
agrega teoria suelta?`
