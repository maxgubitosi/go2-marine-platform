# Presupuesto de extension del informe

Este documento fija una meta editorial de tamano para que el informe final
quede en el orden de las `80 paginas`, sin que la `Introduccion` resulte
demasiado corta ni que `Metodologia` absorba desproporcionadamente todo el
espacio.

## Supuestos de estimacion

Estas cuentas son aproximadas y estan pensadas para el formato actual del
proyecto:

- `article` en `12pt`;
- margenes de `1 in`;
- cuerpo principal en doble espaciado;
- con figuras, tablas, ecuaciones y captions distribuidas dentro del texto.

Por eso, las paginas no se traducen de forma exacta a caracteres. Como regla
practica:

- `1 pagina de texto corrido` equivale aproximadamente a `2.000-2.400`
  caracteres con espacios;
- una figura o tabla mediana puede consumir entre `0,5` y `1,2` paginas;
- una seccion con muchas figuras necesitara menos caracteres para ocupar el
  mismo numero de paginas.

## Objetivo global

Para un informe de alrededor de `80 paginas`, una meta razonable es:

- `texto principal`: `120.000-145.000` caracteres con espacios;
- `figuras, tablas, captions, ecuaciones y aire editorial`: el resto hasta
  completar el volumen final.

## Presupuesto recomendado por seccion

### Front matter

- portada, resumen, pagina de titulo y material inicial;
- objetivo: `3-4 paginas`.

Nota:

- no conviene gastar demasiado espacio aca; el cuerpo tecnico tiene que llevar
  el peso del informe.

### Introduccion

- objetivo: `6-8 paginas`
- texto estimado: `12.000-18.000` caracteres

Por que:

- la introduccion tiene que instalar el problema, motivar el framework,
  explicitar el objetivo de aterrizaje en plataformas marinas, definir el
  alcance de la tesis y anticipar la estructura del documento;
- si queda por debajo de `6 paginas`, hay una alta chance de que se lea como
  una apertura apurada o demasiado resumida.

Decision editorial:

- cuando me pidas la introduccion, la voy a pensar deliberadamente en este
  rango, no como una pagina de contexto rapido.

### Marco teorico y estado del arte

- objetivo: `14-18 paginas`
- texto estimado: `26.000-36.000` caracteres

Distribucion sugerida:

- `marco teorico`: `8-10 paginas`
- `estado del arte`: `5-8 paginas`

Por que:

- aca vive buena parte de la narrativa conceptual del trabajo;
- si el marco queda demasiado corto, la metodologia se vuelve dificil de seguir;
- si queda demasiado largo, se corre el riesgo de que parezca un apunte
  enciclopedico.

### Metodologia en simulacion

- objetivo: `12-15 paginas`
- texto estimado: `22.000-30.000` caracteres

Incluye:

- simulacion del Go2;
- tabla y ArUco;
- generacion del movimiento;
- camara fija;
- dron;
- registro y evaluacion offline.

Nota:

- este bloque puede apoyarse bastante en figuras del pipeline y del setup, por
  lo que no todo necesita ir en prosa continua.

### Metodologia en laboratorio

- objetivo: `5-7 paginas`
- texto estimado: `9.000-14.000` caracteres

Incluye:

- pasaje desde simulacion al laboratorio;
- reproduccion del movimiento en el Go2 real;
- montaje visual;
- criterio de comparacion con odometria real.

Nota:

- este bloque no tiene por que ser tan largo como el de simulacion, pero
  tampoco conviene reducirlo a un apendice menor, porque conceptualmente es la
  parte que conecta la simulacion con el mundo fisico.

### Experimentacion en simulacion

- objetivo: `12-15 paginas`
- texto estimado: `18.000-26.000` caracteres

Incluye:

- setup experimental;
- metricas;
- resultados con camara fija;
- resultados con dron;
- interpretacion.

Nota:

- esta seccion probablemente ocupe bastante espacio visual si incorporamos
  plots, tablas y comparaciones.

### Experimentacion en laboratorio

- objetivo: `6-8 paginas`
- texto estimado: `10.000-15.000` caracteres

Incluye:

- setup real;
- criterio de medicion;
- resultados de correlacion entre movimiento propuesto y comportamiento real;
- observaciones practicas y limitaciones.

### Conclusiones

- objetivo: `4-5 paginas`
- texto estimado: `7.000-10.000` caracteres

Por que:

- tiene que cerrar de verdad el trabajo, no solo repetir el resumen del metodo;
- si queda muy corta, el informe pierde peso argumental justo al final.

### Trabajo futuro

- objetivo: `2-3 paginas`
- texto estimado: `3.500-6.000` caracteres

Incluye:

- aterrizaje autonomo como etapa siguiente;
- mejoras de calibracion y validacion real;
- extension del framework.

### Bibliografia

- objetivo: `4-6 paginas`

Nota:

- esto depende mucho de cuantas referencias terminemos incorporando y del estilo
  final de cita.

## Resumen del presupuesto

En una version equilibrada del informe, el reparto deberia quedar mas o menos
asi:

| Seccion | Paginas objetivo |
|---|---:|
| Front matter | 3-4 |
| Introduccion | 6-8 |
| Marco teorico y estado del arte | 14-18 |
| Metodologia en simulacion | 12-15 |
| Metodologia en laboratorio | 5-7 |
| Experimentacion en simulacion | 12-15 |
| Experimentacion en laboratorio | 6-8 |
| Conclusiones | 4-5 |
| Trabajo futuro | 2-3 |
| Bibliografia | 4-6 |

Esto da un total aproximado de `68-89 paginas`. La banda es deliberadamente
amplia porque depende mucho de cuantas figuras y tablas pongamos. La meta
practica deberia ser aterrizar cerca de:

- `76-82 paginas` si el informe queda mas austero visualmente;
- `78-84 paginas` si incorporamos varias figuras y resultados.

## Regla para no desbalancear el informe

Si durante la escritura una seccion empieza a crecer mucho, conviene revisar:

- esta desarrollando una idea nueva o repitiendo detalle de implementacion;
- una parte de esto deberia pasar a figura o tabla;
- este contenido pertenece a metodo o a experimentacion;
- estamos sosteniendo el objetivo narrativo general del informe.

## Decision editorial para las proximas iteraciones

Dejo fijados estos criterios:

- la `Introduccion` no se va a escribir como una apertura breve;
- `Marco teorico` y `Metodologia` van a ser los bloques de mayor peso;
- la parte de simulacion y la parte de laboratorio tienen que ocupar espacio
  suficiente para que el pasaje entre ambas se entienda;
- cuando hagamos discovery de una seccion, conviene mirar tambien si su tamaño
  proyectado sigue siendo consistente con este presupuesto.
