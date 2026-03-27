# Brief de escritura: Introduccion

Este documento define como deberia funcionar la `Introduccion` del informe.
Todavia no es texto final para `main.TeX`: es una guia de discovery para que,
cuando la escribamos, salga con una estructura clara, una longitud razonable y
un tono consistente con el resto de la tesis.

## Funcion de la seccion

La `Introduccion` tiene que hacer cuatro trabajos al mismo tiempo:

1. instalar el problema general;
2. mostrar por que vale la pena estudiar ese problema en este proyecto;
3. explicar cual es el aporte concreto de la tesis;
4. dejar al lector bien parado para entrar al resto del informe.

Si la seccion cumple esas cuatro funciones, no importa si termina mas cerca de
6 o de 8 paginas. Lo importante es que no quede ni apurada ni inflada.

## Meta de extension

- objetivo orientativo: `6-8 paginas`
- texto estimado: `12.000-18.000` caracteres con espacios

Esto no es una cuota. Es un rango razonable para:

- presentar el problema sin simplificarlo en exceso;
- dar motivacion tecnica y experimental;
- definir el objetivo general y el alcance real de la tesis;
- anticipar la estructura del documento.

## Pregunta que debe responder

`Por que fue necesario construir este framework y que aporta la tesis dentro del
problema mas amplio de aterrizar drones sobre plataformas marinas?`

## Hilo narrativo recomendado

La introduccion deberia avanzar de esta forma:

1. problema amplio;
2. dificultad practica de validarlo en hardware real;
3. necesidad de un entorno de prueba controlado;
4. idea central de usar el Go2 como plataforma marina sintetica;
5. extension hacia percepcion visual y escenarios con dron;
6. paso al laboratorio para contrastar simulacion y realidad;
7. objetivo general, aportes y alcance del trabajo;
8. mapa del resto del informe.

## Estructura interna sugerida

### Bloque 1. Apertura del problema

Objetivo:

- abrir con el problema de operar o aterrizar drones sobre plataformas marinas
  en movimiento;
- instalar que el desafio no es solo de control, sino tambien de percepcion y
  validacion experimental.

Que deberia aparecer:

- la plataforma se mueve;
- la pose relativa cambia constantemente;
- el riesgo de probar directo con hardware es alto;
- la necesidad de validar antes en un entorno controlado.

Que no deberia aparecer todavia:

- detalle de ROS2, Gazebo, topics o implementacion;
- lista de componentes del repo.

Peso estimado:

- `1-1,5 paginas`

### Bloque 2. Motivacion de la tesis

Objetivo:

- pasar del problema general al recorte especifico del trabajo;
- justificar por que la tesis se concentra en framework, percepcion visual y
  contraste simulacion-real, en lugar de cerrar ya un aterrizaje autonomo
  completo.

Que deberia aparecer:

- necesidad de desacoplar primero el problema;
- importancia de contar con una plataforma reproducible;
- valor de comparar estimacion visual contra ground truth;
- rol del laboratorio como paso intermedio entre simulacion y aplicacion final.

Peso estimado:

- `1-1,5 paginas`

### Bloque 3. Idea central del enfoque

Objetivo:

- introducir la solucion conceptual de la tesis;
- mostrar que el framework no es una suma de herramientas sueltas, sino una
  estrategia integrada.

Que deberia aparecer:

- uso del Unitree Go2 para sintetizar movimiento marino;
- agregado de una tabla con ArUco sobre el lomo;
- explicacion breve de por que el recorte se concentra en roll, pitch y heave,
  y no en los seis grados de libertad de una embarcacion;
- observacion desde camara fija y desde dron;
- evaluacion visual en simulacion;
- verificacion posterior en laboratorio.

Que conviene cuidar:

- mantenerlo a nivel conceptual;
- no convertir este bloque en una mini metodologia.

Peso estimado:

- `1-1,5 paginas`

### Bloque 4. Objetivo general y objetivos especificos

Objetivo:

- declarar con claridad que el objetivo global del proyecto es habilitar un
  framework para probar aterrizaje de drones sobre plataformas marinas;
- diferenciar ese objetivo macro de los aportes inmediatos de la tesis.

Formulacion sugerida:

- objetivo general: construir y validar un framework experimental para estudiar
  aterrizaje de drones sobre plataformas marinas;
- objetivos especificos:
  - sintetizar el movimiento de una plataforma marina en el Go2;
  - estimar visualmente la pose del marcador desde una camara fija y desde un
    dron;
  - comparar la estimacion contra ground truth en simulacion;
  - contrastar en laboratorio el movimiento propuesto con el comportamiento real
    del robot.

Peso estimado:

- `0,8-1,2 paginas`

### Bloque 5. Aportes y alcance

Objetivo:

- explicitar que demuestra esta tesis y que no demuestra todavia;
- marcar honestamente el alcance sin vender mas de lo que hay.

Que deberia aparecer:

- construccion del entorno de simulacion;
- integracion del pipeline de percepcion;
- evaluacion offline contra ground truth;
- primer puente entre simulacion y laboratorio;
- el aterrizaje autonomo completo queda como objetivo final del framework, no
  como resultado ya resuelto de la tesis.

Peso estimado:

- `0,8-1,2 paginas`

### Bloque 6. Organizacion del informe

Objetivo:

- cerrar la introduccion con una hoja de ruta breve y clara.

Que deberia aparecer:

- marco teorico;
- metodologia en simulacion y laboratorio;
- experimentacion;
- conclusiones y trabajo futuro.

Regla:

- que sea corto y limpio;
- no repetir parrafos enteros de otras secciones.

Peso estimado:

- `0,4-0,7 paginas`

## Posible reparto de parrafos

Una version equilibrada podria tener:

- `2-3 parrafos` para el problema general;
- `2-3 parrafos` para la motivacion y el recorte del trabajo;
- `2-3 parrafos` para la idea central del enfoque;
- `1-2 parrafos` para objetivos;
- `1-2 parrafos` para aportes y alcance;
- `1 parrafo` final de organizacion del informe.

## Lo que la Introduccion no deberia hacer

- no deberia convertirse en un resumen detallado de metodologia;
- no deberia parecer un abstract extendido;
- no deberia entrar temprano en detalles de codigo;
- no deberia hacer promesas de robustez o generalidad sin respaldo;
- no deberia discutir en profundidad resultados numericos.

## Frases o ideas que deberian quedar claras

Al terminar la Introduccion, el lector deberia entender:

- cual es el problema grande;
- por que no era razonable arrancar con pruebas directas de aterrizaje real;
- por que el Go2 aparece en esta tesis;
- por que el movimiento simulado se concentra en roll, pitch y heave;
- por que la estimacion visual importa;
- por que simulacion y laboratorio conviven en el trabajo;
- que aporta la tesis dentro del objetivo mas amplio del proyecto.

## Tono recomendado

- academico;
- directo;
- con narrativa tecnica clara;
- sin inflar el aporte;
- sin exagerar novedad;
- con una voz que muestre criterio metodologico.

## Puentes utiles hacia otras secciones

La `Introduccion` deberia dejar sembradas estas transiciones:

- hacia `Marco teorico`: para entender por que el problema se ataca asi, primero
  hay que precisar que movimiento importa, como puede sintetizarse y como puede
  medirse;
- hacia `Metodologia`: una vez planteado el problema y el enfoque general,
  corresponde describir como se implemento el framework;
- hacia `Experimentacion`: el valor del framework se juzga por su capacidad para
  generar evidencia util tanto en simulacion como en laboratorio.

## Pendientes de informacion para escribirla bien

Antes de redactar la version final convendria confirmar:

- si la aplicacion final se presentara como aterrizaje autonomo o como
  plataforma de pruebas para aterrizaje;
- que peso narrativo tendra el caso del dron respecto de la camara fija;
- que material real de laboratorio se incorporara finalmente al informe;
- si hay una hipotesis o pregunta de investigacion formal que ustedes quieran
  declarar de forma explicita.
