# Revisión integral de la tesis

Fecha de revisión: 2026-04-15  
Archivo revisado: `informe/main.tex`  
Alcance de esta revisión: lectura completa de la tesis actual, con foco en narrativa, consistencia académica, completitud formal, balance técnico y soporte visual.

Las referencias de línea incluidas abajo corresponden a la versión actual de `informe/main.tex` al momento de esta revisión.

## Diagnóstico global

La tesis ya tiene una base muy sólida en tres frentes.

- La pregunta de investigación es clara: construir un framework reproducible para estudiar estimación visual de pose sobre una plataforma marina sintética.
- El arco narrativo simulación -> laboratorio está bien elegido y, en líneas generales, se entiende.
- La sección experimental es hoy el bloque más maduro del documento: tiene evidencia real, métricas, comparaciones y una lectura interpretativa razonable.

Dicho eso, todavía hay varias señales de manuscrito en construcción que hoy le quitan fuerza académica al texto.

- El `abstract` está vacío.
- `Conclusiones` y `Trabajo futuro` están vacíos.
- Siguen apareciendo `\todo{}`, `\pendingcitation{}` y `\figureplaceholder{}`.
- Hay al menos una repetición conceptual/equacional innecesaria.
- Algunas figuras pendientes ya existen en el repo y solo falta integrarlas.
- En varias partes el texto todavía explica cómo fue escrito o cómo conviene leerlo, en vez de dejar que la propia estructura lo haga.

Mi lectura general es esta: la tesis ya no tiene un problema de “falta de idea”, sino de cierre editorial, jerarquización y pulido académico.

## Prioridades de cierre

### Prioridad 0: imprescindible antes de cualquier entrega seria

1. Completar el `abstract` (`main.tex:114-122`).
  Por ahora la tesis no tiene un resumen ejecutivo del problema, del método, de los resultados y del alcance. Es la primera gran ausencia formal.
2. Escribir `Conclusiones` y `Trabajo futuro` (`main.tex:2419-2424`).
  Hoy el documento termina sin cierre argumental. Eso debilita mucho la lectura global, incluso si el cuerpo técnico es bueno.
3. Eliminar todas las marcas de borrador visibles.
  Casos detectados:
  - `\todo{}` en `main.tex:148`
  - `\todo[inline]{}` en `main.tex:149`
  - `\pendingcitation{}` en `main.tex:167-169`
  - `\todo[inline]{}` en `main.tex:1922`
4. Resolver las figuras pendientes más fáciles, especialmente donde ya hay material listo.
  Hay placeholders en `main.tex:692`, `894`, `1025`, `1105`, `1515`, `1684`, `1878`, `2290`, `2320`, `2352`, `2371`.
5. Corregir la repetición de la aproximación discreta del movimiento marino.
  La relación entre alturas locales y `heave`/`pitch`/`roll` aparece dos veces:
  - como ecuación numerada en `main.tex:678-686`
  - como bloque repetido en `main.tex:704-712`
   Esta duplicación debería desaparecer.

### Prioridad 1: mejoras de alto impacto narrativo

1. Terminar de separar de forma limpia `Motivación` e `Introducción`.
  Hoy ambas secciones funcionan, pero todavía rozan el solapamiento: la primera explica por qué el problema importa; la segunda explica qué hace la tesis. Esa frontera debería quedar todavía más nítida.
2. Hacer explícitas las preguntas de investigación o criterios de validación.
  Falta una formulación breve del tipo:
  - qué quiere demostrar la simulación,
  - qué quiere demostrar el laboratorio,
  - qué se considera evidencia suficiente de éxito en cada caso.
3. Reemplazar meta-comentarios por afirmaciones académicas directas.
  El ejemplo más claro es `main.tex:1902-1906`, donde el texto explica cómo fue escrita la sección experimental. En una tesis suele ser mejor mostrar esa jerarquía con estructura y no comentarla explícitamente.
4. Incorporar una sección corta y explícita de limitaciones.
  Las limitaciones hoy aparecen dispersas. Sería mejor consolidarlas en el cierre del documento o, alternativamente, en el final de la experimentación.

### Prioridad 2: pulido técnico y formal

1. Uniformar notación y terminología.
2. Acortar algunas captions demasiado cargadas.
3. Mover ciertos detalles demasiado operativos al apéndice o a tablas.
4. Diferenciar mejor qué es resultado central y qué es soporte metodológico.

## Revisión por secciones

## 1. Motivación

Ubicación: `main.tex:136-239`

### Qué funciona bien

- La tesis arranca por una motivación técnicamente relevante y no por una definición abstracta del sistema.
- La progresión “problema difícil -> necesidad de validación segura -> enfoque progresivo” está bien pensada.

### Qué mejoraría

1. Resolver de inmediato las citas pendientes y las marcas internas.
  La subsección de aplicaciones marítimas pierde credibilidad mientras mantenga `\todo{}` y `\pendingcitation{}` visibles (`main.tex:148-149`, `167-169`).
2. Acotar un poco la enumeración de aplicaciones.
  El listado actual es razonable, pero es largo y todavía está poco jerarquizado. Conviene condensarlo en menos ejemplos, mejor apoyados bibliográficamente.
3. Reforzar la transición entre “valor operativo” y “necesidad metodológica”.
  La segunda subsección es buena, pero podría cerrar con una frase más fuerte del tipo: “por eso el problema no es solo de control o visión, sino también de validación experimental”.
4. Evaluar si `Motivación` debe seguir siendo sección separada.
  No es incorrecto que exista como bloque propio, pero en su forma actual se acerca mucho a una introducción extendida. Si se quisiera una estructura más convencional, se podría integrar dentro de `Introducción` como subsección inicial.

## 2. Introducción

Ubicación: `main.tex:241-402`

### Qué funciona bien

- El objetivo y el alcance están bastante bien delimitados.
- La introducción ya enmarca correctamente el uso del Go2, de ArUco, de ROS2/Gazebo y de `solvePnP`.
- La subsección de aportes organiza bien el resto del informe.

### Qué mejoraría

1. Explicitar preguntas de investigación o criterios de validación.
  Hoy el lector entiende el objetivo general, pero no queda formulado con la suficiente precisión qué se espera confirmar en simulación y qué se espera confirmar en laboratorio.
2. Evitar una leve reiteración entre “alcance” y “aportes”.
  Los párrafos de `main.tex:253-261` y `379-390` no son redundantes, pero sí conversan sobre lo mismo. Se puede afinar el reparto:
  - `alcance`: qué no hace la tesis
  - `aportes`: qué sí deja resuelto
3. Cuidar la primera gran figura panorámica.
  La Figura `fig:intro_framework_overview` cumple su función, pero el componente de laboratorio todavía se siente más “frame de cámara” que “figura editorial”. Si se mantiene, conviene revisar encuadre y limpieza visual.
4. Incorporar una frase final que anticipe con mayor claridad la diferencia entre evidencia de simulación y evidencia de laboratorio.
  Esa distinción es central en la tesis y conviene anunciarla ya en la introducción.

## 3. Marco teórico

Ubicación: `main.tex:406-1243`

### Balance general

La reestructuración reciente mejoró mucho esta sección. Ahora el marco teórico sí funciona como lugar de introducción conceptual y no como una antesala dispersa de la metodología. El orden nuevo está bien elegido.

### 3.1 Introducción conceptual

Ubicación: `main.tex:408-452`

- Está bien orientada y cumple la función de puente.
- No la alargaría más.
- Sí convendría que su última frase cierre con una promesa más concreta de lectura: infraestructura -> movimiento -> plataforma -> marcos -> visión.

### 3.2 Ecosistema experimental: ROS2, Gazebo y registro reproducible

Ubicación: `main.tex:465-527`

### Qué funciona bien

- La explicación de ROS2 mejoró claramente.
- Ahora sí se entiende qué es el grafo, qué es un nodo, qué es un tópico y por qué eso importa para el experimento.
- La entrada de `tf2`, Gazebo y rosbags está bien encadenada.

### Qué mejoraría

1. Agregar una figura simple del grafo ROS2.
  No hace falta una imagen compleja: basta un esquema con 4 o 5 nodos, 3 o 4 tópicos y una caja lateral indicando registro en rosbag.
2. Cuidar que `tf2` no quede un poco más abstracto que ROS2.
  Hoy está bien definido, pero un diagrama de frames ayudaría mucho más que otra explicación verbal.
3. Evaluar si conviene citar también una referencia específica del robot o del fabricante.
  ROS2, tf2 y Gazebo ya tienen soporte. El Go2 todavía no tiene una referencia formal equivalente en bibliografía.

### 3.3 Movimiento marino simplificado

Ubicación: `main.tex:529-793`

### Qué funciona bien

- La lógica física está bien explicada.
- El pasaje desde la intuición de ola hacia la reducción a `heave`, `roll` y `pitch` es claro.
- Las figuras conceptuales existentes son útiles.

### Qué mejoraría

1. Eliminar la duplicación de la aproximación discreta.
  Esto es la corrección más clara y más urgente de esta subsección.
2. Revisar si el nivel de ecuaciones está perfectamente alineado con el resto del documento.
  La sección es valiosa, pero puede estar un poco más cargada de lo que luego se usa explícitamente en metodología y resultados.
3. Considerar mover una de las dos capas de formalización al apéndice si se necesita aligerar.
  Si hiciera falta recortar, yo preservaría:
  - la intuición física,
  - la reducción a tres componentes,
  - la onda sinusoidal e irregular.
   Y dejaría más condensado el desarrollo más general de dinámica marina.
4. Reemplazar el placeholder `fig:platform_corner_heights` con una figura propia limpia.
  Esta figura sí vale la pena, porque ayuda mucho a explicar el paso desde la ola a la postura de la plataforma.

### 3.4 Plataforma robótica e instrumentación visual

Ubicación: `main.tex:795-838`

### Qué funciona bien

- La sección está bien enfocada en por qué el Go2 sirve como plataforma sintética.
- La distinción entre cámara fija y dron está bien lograda.

### Qué mejoraría

1. Añadir una figura clara del Go2 como plataforma experimental.
  La tesis todavía describe muy bien al robot, pero no termina de “mostrarlo” con una figura pensada para el texto teórico.
2. Citar formalmente al Go2.
  Si se lo introduce como plataforma experimental, conviene respaldar al menos su identificación básica con una fuente oficial.
3. Evaluar si conviene incluir aquí el diagrama `unitree_go2_diagram.png` como base.
  El archivo local existe y puede servir si se le agrega una edición mínima.

### 3.5 Control postural del Go2 y marcos de referencia

Ubicación: `main.tex:840-1049`

### Qué funciona bien

- El vínculo entre consigna postural, patas y torso está bien razonado.
- La distinción entre `base_link` y `base_footprint` es importante y está bien introducida.
- La cadena de transformaciones hacia cámara y marcador está bien elegida.

### Qué mejoraría

1. Evaluar si hace falta tanta densidad matemática.
  Esta sección es conceptualmente correcta, pero probablemente sea la que más riesgo tiene de “pasarse” de formalización en relación con lo que después se explota experimentalmente.
2. Si hubiera que recortar, yo mantendría sí o sí:
  - `main.tex:903-943`
  - `main.tex:1013-1049`
   porque son las partes más directamente útiles para el resto del informe.
3. El placeholder `fig:go2_postural_control_scheme` merece ser reemplazado.
  Además, acá sí hay una oportunidad clara de combinar una figura propia del robot con overlays simples.
4. El placeholder `fig:theory_frames_overview` es clave.
  Esta figura no es decorativa. Haría muchísimo más intuitiva toda la parte geométrica.

### 3.6 Marcadores fiduciales y estimación de pose

Ubicación: `main.tex:1051-1240`

### Qué funciona bien

- La sección está muy bien encaminada.
- Ahora sí presenta primero el marcador y después la geometría.
- El rol de `solvePnP` quedó claro.

### Qué mejoraría

1. Añadir una figura buena de geometría cámara-marcador.
  El placeholder `fig:camera_marker_geometry` es muy importante y hoy se siente como la ausencia visual más notoria del marco teórico.
2. Revisar si la discusión de homografía puede quedar un poco más corta.
  No está mal, pero si más adelante no se recupera explícitamente, podría simplificarse para que el foco siga estando en el pipeline real del trabajo.
3. Mantener la figura del marcador ArUco, pero sumar un esquema de ejes.
  La imagen actual muestra el patrón. Lo que todavía falta es mostrar cómo se organiza geométricamente su frame.

## 4. Metodología

Ubicación: `main.tex:1244-1888`

### Balance general

La metodología ya está mejor resuelta que antes. Se entiende la división simulación/laboratorio y la lógica de implementación. Aun así, todavía hay material que podría jerarquizarse mejor.

### Qué mejoraría

1. Reducir repeticiones con el marco teórico.
  Hay párrafos correctos, pero todavía reiteran racionales ya explicados en `Marco teórico`, especialmente en:
  - `main.tex:1276-1291`
  - `main.tex:1694-1737`
2. Mover detalles demasiado operativos fuera del flujo principal cuando no son analíticamente decisivos.
  Ejemplos:
  - `api_id=1007`
  - resolución exacta `3840 x 1080`
  - algunos offsets muy específicos
   Son útiles, pero no todos necesitan estar en el centro del relato.
3. Reemplazar placeholders por material existente del repo.
  Casos muy claros:
  - `fig:lab_api_fidelity`
  - `fig:lab_target_vs_odom`
  - `fig:lab_lag_correlation`
  - `fig:lab_heave_comparison`
4. Evitar duplicar la misma figura de laboratorio en metodología y resultados.
  `fig:method_lab_setup` (`main.tex:1836-1843`) y `fig:lab_results_setup` (`main.tex:2249-2256`) usan la misma imagen base. Conviene:
  - dejarla una sola vez y referenciarla después,
  - o usar dos versiones realmente distintas con roles distintos.
5. Cerrar cada gran bloque metodológico con una frase de salida más nítida.
  La tesis mejoraría si cada subsección terminara anunciando exactamente qué dato o figura habilita la siguiente.

### Observaciones específicas

1. `Registro y evaluación offline` (`main.tex:1640-1690`) está bien planteada, pero merece una figura de pipeline.
  Ese pipeline es una pieza central del trabajo y todavía no tiene una visualización propia.
2. `Dificultades del pasaje de simulación a laboratorio` (`main.tex:1705-1755`) es útil, aunque puede ganar concisión.
  La tabla comparativa ya hace mucho trabajo; el texto podría apoyarse un poco más en ella.
3. `Estimación visual con cámara en configuración cuasi fija` (`main.tex:1800-1843`) está bien, pero puede enfatizar mejor una idea:
  en laboratorio la estimación visual existe, aunque la evidencia cuantitativa hoy se apoya más en movimiento y comando que en error pose-vs-ground-truth.

## 5. Experimentación y resultados

Ubicación: `main.tex:1891-2415`

### Balance general

Esta es, hoy, la mejor sección de la tesis. Tiene narrativa, datos, comparación entre escenarios y una interpretación bastante honesta del alcance.

### Qué mejoraría

1. Eliminar el meta-comentario de apertura.
  `main.tex:1902-1906` explica cómo fue escrita la sección. Yo lo quitaría. La sección ya puede sostener su narrativa por sí sola.
2. Resolver el `\todo` sobre una corrida futura (`main.tex:1922`).
  Si la corrida adicional no se va a incorporar ahora, esa línea no debería quedar visible en el manuscrito principal.
3. Hacer más explícito por qué `R2` es la corrida principal.
  El texto actual lo dice, pero podría quedar mejor apoyado con un criterio sintético:
  - corrida intermedia,
  - suficiente cantidad de muestras,
  - dispersión exigente pero representativa.
4. Aprovechar material gráfico ya generado para sostener la discusión del drift o la evolución temporal del error.
  El archivo local `informe/figures/results/sim_drone_error_time.png` puede ser útil si se decide enfatizar la evolución temporal del error posicional.
5. Añadir una tabla comparativa final simulación vs laboratorio.
  Hoy esa comparación existe en prosa, pero una tabla breve ayudaría mucho a cerrar:
  - qué se validó en simulación,
  - qué se validó en laboratorio,
  - qué sigue abierto.
6. Hacer todavía más explícito el límite de la evidencia visual real.
  La sección de laboratorio lo insinúa bien, pero conviene que el lector no espere un cierre cuantitativo visual equivalente al de simulación.

### Lo que no cambiaría demasiado

- El baseline con cámara fija está bien puesto como primer caso.
- La lectura del caso fuerte con dron está bien lograda.
- La síntesis final de simulación (`main.tex:2166-2195`) funciona muy bien como cierre de bloque.

## 6. Conclusiones

Ubicación: `main.tex:2419-2421`

Hoy esta sección está vacía y es una de las ausencias más importantes del manuscrito.

Mi recomendación es que no sea larga. Bastarían cuatro movimientos claros:

1. recordar el objetivo real de la tesis;
2. decir qué quedó demostrado en simulación;
3. decir qué quedó demostrado en laboratorio;
4. marcar con honestidad qué todavía no quedó cerrado.

La conclusión debería contener números concretos, pero pocos y muy bien elegidos.

## 7. Trabajo futuro

Ubicación: `main.tex:2423-2424`

También está vacía.

Acá yo distinguiría dos escalas.

1. Trabajo futuro cercano.
  - cerrar las figuras faltantes,
  - completar evaluación visual real,
  - sumar una campaña de laboratorio con `heave` dinámico,
  - refinar la cadena geométrica del dron.
2. Trabajo futuro de mayor alcance.
  - incorporar control del dron más cercano al aterrizaje,
  - sumar trayectorias relativas más realistas,
  - estudiar cierre visual y control en lazo.

Separar estas dos escalas ayuda mucho a que el cierre suene creíble y no aspiracional.

## 8. Consistencia transversal de escritura

### Terminología

Sugiero estandarizar estas decisiones en todo el manuscrito.

- Usar `\emph{roll}`, `\emph{pitch}`, `\emph{heave}` cuando se hable de los movimientos físicos.
- Reservar `\texttt{roll}`, `\texttt{pitch}`, `\texttt{yaw}` para variables, campos o nombres de ejes en mensajes y gráficos.
- Elegir una sola forma dominante para “ground truth”.
Mi preferencia: usar “ground truth” una vez, definirlo, y luego hablar de “referencia reconstruida” o “referencia del simulador”.
- Elegir una forma estable para “frame óptico de la cámara”.
Hoy conviven “frame óptico”, “frame de la cámara” y “frame cámara”.
- Mantener “plataforma marina sintética” como denominación estable del Go2 dentro del problema.

### Estilo

1. Reducir las frases demasiado metadiscursivas.
  Ejemplos:
  - “Lo importante aquí es...”
  - “Esta sección se escribió...”
  - “Desde el punto de vista metodológico...”
2. Variar un poco ciertas muletillas argumentativas.
  Esa expresión aparece muchas veces:
  - “conviene”
  - “resulta útil”
  - “desde el punto de vista metodológico”
   No están mal, pero repetidas restan naturalidad.
3. Revisar captions demasiado descriptivas en términos de implementación.
  Algunas captions incluyen demasiados parámetros o demasiada explicación de lectura. Parte de eso podría quedar en el cuerpo del texto.

## 9. Figuras e imágenes

## 9.1 Figuras que ya existen en el repo y deberían incorporarse o reutilizarse

Estas son, para mí, las oportunidades más claras de mejora visual sin depender de material externo.
Todas las imágenes listadas abajo fueron inspeccionadas visualmente durante esta revisión.


| Uso sugerido                              | Archivo disponible                                              | Observación                                                                                                                                                                                                             |
| ----------------------------------------- | --------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Fidelidad del comando API                 | `informe/figures/images/lab_plot_02_api_fidelity.png`           | Está prácticamente listo para reemplazar `fig:lab_api_fidelity`. Conviene regenerarlo con un título menos “de debugging” si va al manuscrito final.                                                                     |
| Comando vs respuesta real                 | `informe/figures/images/lab_plot_01_timeseries_cmd_vs_real.png` | Puede cubrir `fig:lab_target_vs_odom` o servir de base para `fig:method_lab_comparison`.                                                                                                                                |
| Correlación vs lag                        | `informe/figures/images/lab_plot_03_lag_correlation.png`        | Reemplaza muy bien `fig:lab_lag_correlation`.                                                                                                                                                                           |
| Lectura del eje vertical en laboratorio   | `informe/figures/images/lab_plot_05_heave_z_comparison.png`     | Reemplaza `fig:lab_heave_comparison`; además deja muy clara la diferencia entre consigna y altura absoluta.                                                                                                             |
| Pantalla/screenshot de Gazebo con el Go2  | `docs/media/gazebo_go2.png`                                     | Muy útil para `Ecosistema experimental` o para una subsección metodológica temprana.                                                                                                                                    |
| Detección ArUco en tiempo real            | `docs/media/aruco_detection_realtime.gif`                       | Excelente para slides o defensa; no es ideal para el PDF de tesis, pero sí como referencia de material complementario.                                                                                                  |
| Vista del dron sobre el Go2 en simulación | `docs/media/drone-unitree-aruco.png`                            | Puede complementar la explicación del caso con cámara embarcada.                                                                                                                                                        |
| Diagrama del Go2                          | `informe/figures/diagrams/unitree_go2_diagram.png`              | Buen punto de partida para una figura editorial del robot como plataforma sintética.                                                                                                                                    |
| Foto/frame del laboratorio                | `informe/figures/images/fig_lab_real_fixed_camera.png`          | Funciona como evidencia de que el setup existió, pero no es una gran figura editorial porque aparece parte del operador y del entorno. Si queda en el manuscrito, conviene usar una versión más limpia o más recortada. |
| Panorama general del proyecto             | `informe/figures/images/fig_panoramica_tesis.png`               | La idea es buena, pero la composición todavía está cargada. Puede servir como base para una figura síntesis final más pulida.                                                                                           |


## 9.2 Figuras conceptuales que faltan y que sí valdría la pena producir

Estas son las que más valor académico agregarían.

1. Diagrama ROS2 de nodos, tópicos y rosbag.
  Ubicación sugerida: subsección `Ecosistema experimental`.
2. Diagrama de frames.
  Ubicación sugerida: subsección `Control postural del Go2 y marcos de referencia`.
3. Diagrama cámara-marcador-pinhole.
  Ubicación sugerida: subsección `Marcadores fiduciales y estimación de pose`.
4. Esquema del Go2 como plataforma marina sintética.
  Ubicación sugerida: subsección `Plataforma robótica e instrumentación visual`.
5. Pipeline completo de simulación -> detección -> rosbag -> evaluación offline.
  Ubicación sugerida: cierre de `Metodología en simulación`.

## 9.3 Referencias externas útiles para imágenes o para redibujar figuras

Revisé fuentes externas que pueden servir como apoyo visual. Mi recomendación general es esta: para la tesis final conviene más redibujar esquemas propios inspirados en estas fuentes que pegar capturas tal cual. Eso mejora la consistencia estética y reduce ambigüedades de derechos de uso.
Las referencias listadas abajo también fueron revisadas visualmente durante esta auditoría.

### A. ROS2: nodos, tópicos y grafo

- Fuente oficial:
[ROS 2 Documentation: About Topics](https://docs.ros.org/en/rolling/Concepts/Basic/About-Topics.html)
- Fuente complementaria:
[ROS 2 Documentation: Introducing Turtlesim and rqt](https://docs.ros.org/en/humble/Tutorials/Beginner-CLI-Tools/Introducing-Turtlesim/Introducing-Turtlesim.html)
- Uso sugerido:
inspiración para una figura propia muy simple de publicación/suscripción o, si hiciera falta, una captura acotada de `rqt_graph`.
- Recomendación:
no usar una captura compleja del ecosistema ROS real; conviene redibujar un grafo mínimo y específico del proyecto.

### B. Gazebo Classic

- Fuente oficial:
[Gazebo Classic tutorials](https://classic.gazebosim.org/tutorials)
- Recurso local más útil:
`docs/media/gazebo_go2.png`
- Uso sugerido:
mostrar la interfaz de Gazebo una sola vez, como anclaje visual del entorno de simulación.
- Recomendación:
para el manuscrito final prefiero usar la captura local del propio proyecto antes que una imagen genérica tomada de internet.

### C. Unitree Go2

- Fuente oficial:
[Unitree Go2 product page](https://www.unitree.com/go2/)
- Uso sugerido:
una imagen limpia de identificación del robot o un apoyo para una figura propia del montaje experimental.
- Recomendación:
usarla como referencia documental o bibliográfica. Si el objetivo es una figura técnica del informe, sigue siendo mejor un diagrama propio o una foto del propio setup.

### D. ArUco y sistema de ejes del marcador

- Fuente oficial:
[OpenCV: Detection of ArUco Boards](https://docs.opencv.org/3.4/db/da9/tutorial_aruco_board_detection.html)
- Fuente oficial complementaria:
[OpenCV: Detection of ArUco Markers](https://docs.opencv.org/4.x/d5/dae/tutorial_aruco_detection.html)
- Uso sugerido:
redibujar una figura con:
  - el plano del marcador,
  - sus cuatro esquinas,
  - el sistema de ejes del patrón,
  - el frame óptico de la cámara,
  - los rayos proyectivos.
- Recomendación:
esta es probablemente la mejor referencia externa para cerrar `fig:camera_marker_geometry`.

## 10. Orden sugerido de trabajo

Si yo tuviera que priorizar las mejoras sin reabrir toda la tesis, lo haría en este orden.

1. Completar `abstract`, `conclusiones` y `trabajo futuro`.
2. Eliminar `todos`, `pendingcitation` y duplicaciones obvias.
3. Integrar las figuras ya disponibles en el repo.
4. Reemplazar los tres placeholders conceptuales más importantes:
  - grafo ROS2,
  - marcos de referencia,
  - cámara-marcador.
5. Ajustar `Motivación` e `Introducción` para que no se solapen.
6. Hacer una última pasada de estilo, notación y captions.

## 11. Juicio final

La tesis ya tiene suficiente sustancia técnica y experimental como para convertirse en un muy buen manuscrito. No veo un problema de fondo en la propuesta ni en la evidencia principal. Lo que falta ahora es cerrar el documento con disciplina editorial.

Si tuviera que resumirlo en una sola frase, diría esto:

> la tesis ya convenció técnicamente; ahora le falta terminar de convencer formalmente.

