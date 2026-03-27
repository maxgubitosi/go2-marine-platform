# Criterios de redaccion y lectura

Este documento fija el criterio editorial del informe. La idea es que el texto
sea academico, pero tambien facil de seguir para una persona que no conoce el
repo ni vio el desarrollo del proyecto desde adentro.

## Principio general

Cada seccion debe responder rapido tres preguntas:

1. que problema aborda;
2. como lo resolvimos;
3. por que esa parte importa dentro de la tesis.

Si un bloque no ayuda a contestar alguna de esas preguntas, probablemente haya
que recortarlo, moverlo o reescribirlo.

Ademas, en nuestro caso conviene sostener siempre el hilo de aplicacion final:
el framework se construye para habilitar pruebas de aterrizaje de drones sobre
plataformas marinas. No hace falta repetirlo en exceso, pero si recordar en los
lugares clave por que simulacion, percepcion y validacion real importan.

## Estructura recomendada por seccion

### Introduccion

- abrir con el problema general y su motivacion;
- bajar rapido al caso concreto del proyecto;
- explicitar objetivo, alcance y aporte;
- cerrar con una hoja de ruta corta del resto del informe.

### Marco teorico

- incluir solo teoria que luego se usa de verdad en metodo o experimentacion;
- escribirlo como una progresion de problemas y decisiones, no como una lista
  aislada de conceptos;
- hacer que cada subseccion responda por que esa teoria fue necesaria para
  construir esta tesis;
- presentar intuicion primero y formulacion despues;
- evitar subsecciones enciclopedicas o demasiado largas;
- conectar cada bloque teorico con el sistema real del proyecto.

### Metodo

- contar el pipeline en el mismo orden en que fluye la informacion;
- separar explicitamente lo que pertenece a simulacion de lo que pertenece a
  laboratorio;
- abrir cada uno de esos bloques con una breve introduccion que explique su rol
  dentro del trabajo;
- despues desglosar en subsecciones mas concretas que detallen que se hizo en
  cada entorno;
- separar claramente simulacion, percepcion, registro y evaluacion;
- usar nombres de nodos, topics y scripts solo cuando aportan claridad;
- no saturar el texto con detalle de implementacion que no cambia la comprension.

### Experimentacion

- empezar por el setup;
- luego definir metricas;
- despues mostrar resultados;
- cerrar cada subseccion con una interpretacion corta, no solo con numeros.

### Conclusiones

- retomar objetivos y decir que se pudo demostrar;
- distinguir hallazgos, limitaciones y alcance real del trabajo;
- evitar repetir todo el metodo en forma resumida.

## Reglas de legibilidad

### Parrafos

- priorizar parrafos cortos o medianos;
- una idea principal por parrafo;
- evitar parrafos que mezclen contexto, implementacion y resultado al mismo
  tiempo;
- cerrar cada parrafo con una frase que conecte con el siguiente.

### Subsections

- cada subseccion debe tener un rol claro;
- si una subseccion necesita demasiados desvios, probablemente haya que partirla;
- preferir titulos informativos antes que titulos demasiado genericos.

### Oraciones

- preferir oraciones directas y tecnicas;
- evitar cadenas demasiado largas con muchas subordinadas;
- introducir terminologia nueva una sola vez y usarla de forma consistente;
- usar voz academica sobria, sin marketing ni grandilocuencia.

### Ecuaciones

- incluir solo las necesarias para entender el metodo;
- presentar antes la intuicion fisica o geometrica;
- explicar que representa cada simbolo al momento de introducirlo;
- no dejar ecuaciones "decorativas" sin uso posterior.

### Figuras y tablas

- cada figura debe aparecer porque aclara algo que el texto solo explica peor;
- introducir la figura en el texto antes o inmediatamente despues;
- captions descriptivas: que muestra, en que contexto, y por que importa;
- las tablas deben resumir, no duplicar sin criterio lo que ya dicen los plots.

## Regla practica para nuestro caso

Como esta tesis mezcla software, simulacion, vision por computadora y robotica,
la legibilidad depende mucho de no cambiar de nivel de abstraccion sin aviso.
Por eso, en cada bloque conviene seguir este orden:

1. intuicion del problema;
2. decision metodologica;
3. implementacion concreta en el proyecto;
4. implicancia para la evaluacion.

## Señales de que una pagina quedo pesada

- aparecen demasiados nombres de topics o archivos en pocas lineas;
- se describen varios frames de referencia sin una guia visual o verbal clara;
- se usan mas de dos niveles de detalle en el mismo parrafo;
- una figura necesita demasiada explicacion extra porque el texto no la preparo;
- una subseccion no tiene frase de cierre interpretativa.

## Criterio para nuestras siguientes iteraciones

Cada vez que escribamos o editemos una seccion deberiamos revisar:

- si una persona externa puede seguir la historia sin mirar el codigo;
- si el texto avanza de lo general a lo especifico;
- si las figuras estan puestas donde ayudan y no donde "sobran";
- si el tono sigue siendo academico pero fluido;
- si hay algo que conviene mandar a una tabla, figura o nota en vez de dejarlo
  enterrado en un parrafo largo.
