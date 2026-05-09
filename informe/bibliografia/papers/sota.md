# Estado del arte sobre aterrizaje visual y validación de estimación de pose en plataformas móviles con dinámica marina

## Alcance del corpus y criterio de lectura

Para ubicar este proyecto dentro de la literatura conviene separar cinco planos que muchas veces se mezclan: trabajos que resuelven el aterrizaje completo; trabajos centrados en percepción y estimación de pose relativa; trabajos que usan simulación o software-in-the-loop como etapa de validación; trabajos que modelan movimiento marino con cierto realismo; y trabajos que llegan a hardware real. Dos revisiones recientes sirven como mapa del campo: de Paula et al. revisan 56 publicaciones sobre aterrizaje VTOL sobre superficies navales dinámicas y clasifican las obras por sensores, criterio de aterrizaje y fidelidad del movimiento de la plataforma; Semerikov et al. revisan 143 artículos de 2018–2025 sobre aterrizaje visual, con foco explícito en marcadores fiduciales, detección, métricas y hardware embebido. citeturn27view0turn38view0

Desde esa taxonomía, la literatura útil para tu capítulo se organiza en tres familias. La primera resuelve el problema cerrado de “seguir, alinear y posar” sobre una plataforma móvil; la segunda traslada ese problema al mar, donde aparecen roll, pitch, heave, oleaje, GNSS poco fiable y cubiertas oscilantes; la tercera aporta las piezas habilitadoras de percepción, sobre todo marcadores fiduciales y estimación PnP, que son precisamente las que más dialogan con un pipeline basado en ArUco más solvePnP. citeturn27view0turn38view0turn12search0turn13search1turn14search3

Una primera conclusión importante es que el estado del arte no está vacío en “landing on moving platforms”, pero sí está mucho menos poblado en la intersección concreta que te interesa: validación rigurosa de estimación de pose visual sobre una plataforma con movimiento marino sintetizado, comparación explícita contra ground truth del simulador y uso de bancos experimentales sustitutivos del barco real. Esa intersección aparece sólo parcialmente en antecedentes como Sánchez-López 2014, Delbene 2022 o algunos trabajos muy recientes sobre marcadores fractales y simuladores 4-DoF, pero no está resuelta de manera estándar. citeturn25view0turn42view0turn30search16turn28search1

## Aterrizaje completo sobre plataformas móviles

### Lee, Ryan y Kim 2012

La referencia de Lee et al. es una de las piezas fundacionales del problema moderno: control de un VTOL que debe seguir y aterrizar sobre una plataforma móvil usando image-based visual servoing. La ficha accesible destaca que el controlador genera referencias de velocidad desde el error visual en imagen y las entrega a un controlador sliding-mode adaptativo. Es un antecedente clave porque instala la estructura conceptual “visión relativa + control de seguimiento + fase final de aterrizaje”, que luego reaparece en casi toda la literatura posterior. citeturn19search1turn19search4

BibTeX sugerido:
```bibtex
@inproceedings{lee2012autonomous,
  author    = {Daewon Lee and Tyler Ryan and H. Jin Kim},
  title     = {Autonomous Landing of a VTOL UAV on a Moving Platform Using Image-Based Visual Servoing},
  booktitle = {2012 IEEE International Conference on Robotics and Automation},
  pages     = {971--976},
  year      = {2012},
  doi       = {10.1109/ICRA.2012.6224828},
  url       = {https://doi.org/10.1109/ICRA.2012.6224828}
}
```

**Resumen.** El trabajo aborda el aterrizaje visual de un VTOL sobre plataforma móvil a partir de IBVS, sin introducir todavía un tratamiento marítimo específico. Su relevancia histórica es menos la fidelidad del entorno y más la formalización del lazo visión-control para un blanco móvil. La percepción se concibe como generadora directa de referencias de velocidad, no como módulo separado de estimación 6D con benchmark propio. Eso lo vuelve un antecedente claro para el linaje de control, pero menos directo para un capítulo centrado en validación de pose. citeturn19search1turn19search4

**Lectura crítica.** Problema: seguimiento y aterrizaje sobre blanco móvil. Sensores/marcadores: visión monocular e IBVS; la ficha accesible no enfatiza un marcador fiducial codificado. Validación: antecedente experimental clásico, pero las métricas agregadas no aparecen desglosadas en la ficha visible. Plataforma: móvil no marina. Relación con tu trabajo: útil para ubicar la genealogía de los métodos visual-servoed. Limitación abierta: no separa el problema de percepción del de control, no modela oleaje y no compara estimación visual contra ground truth de simulación. citeturn19search1turn19search4

### Araar, Aouf y Vitanov 2017

Araar et al. desarrollan una solución específicamente “vision based” para aterrizar un multirrotor en una plataforma móvil y, según el resumen accesible, el artículo no sólo trata el control sino también el diseño de una nueva landing pad y su estimación de pose relativa. Eso lo vuelve especialmente pertinente porque se acerca más que Lee al problema de “target design + pose estimation + landing loop”, es decir, el mismo encadenamiento que luego adoptan muchos trabajos basados en fiduciales o patrones artificiales. citeturn43search0turn43search3

BibTeX sugerido:
```bibtex
@article{araar2017vision,
  author  = {Oualid Araar and Nabil Aouf and Ivan Vitanov},
  title   = {Vision Based Autonomous Landing of Multirotor UAV on Moving Platform},
  journal = {Journal of Intelligent \& Robotic Systems},
  volume  = {85},
  number  = {2},
  pages   = {369--384},
  year    = {2017},
  doi     = {10.1007/s10846-016-0399-z},
  url     = {https://doi.org/10.1007/s10846-016-0399-z}
}
```

**Resumen.** El artículo investiga el aterrizaje autónomo sobre objetivos estáticos y móviles, y presenta tanto el diseño del pad como su pose estimation relativa. Esa combinación lo hace importante para cualquier revisión que quiera unir percepción artificial y aterrizaje de precisión. A diferencia de trabajos más puramente controlistas, aquí el diseño del objetivo visual no es accesorio sino parte del sistema. Sin embargo, sigue estando en el dominio de plataformas móviles genéricas, no de cubiertas sometidas a oleaje. citeturn43search0turn43search3

**Lectura crítica.** Problema: aterrizaje autónomo completo sobre plataforma móvil. Sensores/marcadores: cámara y landing pad artificial diseñado ad hoc. Validación: el artículo es de journal y su ficha enfatiza la estimación de pose relativa, aunque el resumen accesible no expone una métrica sintética única. Plataforma: móvil no marina. Relación con tu trabajo: ayuda a justificar el uso de patrones artificiales como componente de estimación relativa. Limitación abierta: no incorpora dinámica marina en roll/pitch/heave ni un marco explícito de V&V contra ground truth simulado. citeturn43search0turn43search3turn43search5

### Falanga et al. 2017

Falanga et al. representan otra referencia muy citada porque muestran un quadrotor capaz de aterrizar sobre plataforma móvil usando sólo percepción y cómputo a bordo. El resumen accesible destaca visión de última generación, fusión multisensor para localización propia, detección y estimación de movimiento de la plataforma. Metodológicamente, el paper es importante porque refuerza la idea de “autonomía onboard real” y reduce la dependencia de infraestructura externa, algo que luego se vuelve una aspiración recurrente en la literatura de aterrizaje. citeturn21search13

BibTeX sugerido:
```bibtex
@inproceedings{falanga2017vision,
  author    = {Davide Falanga and Alessio Zanchettin and Alessandro Simovic and Jeffrey Delmerico and Davide Scaramuzza},
  title     = {Vision-based Autonomous Quadrotor Landing on a Moving Platform},
  booktitle = {2017 IEEE International Symposium on Safety, Security and Rescue Robotics},
  pages     = {200--207},
  year      = {2017},
  doi       = {10.1109/SSRR.2017.8088164},
  url       = {https://doi.org/10.1109/SSRR.2017.8088164}
}
```

**Resumen.** La contribución central no es el mar ni el uso de marcadores, sino la demostración de un pipeline completo de percepción y control explotable en hardware real con computación embarcada. Eso lo vuelve un benchmark de “sistema funcionando”, especialmente útil para contrastar con trabajos que se quedan sólo en pose estimation o sólo en simulación. Aun así, su foco no está en descomponer el error visual frente a una verdad de terreno controlada, que es precisamente donde un framework de validación como el tuyo se vuelve distintivo. citeturn21search13

**Lectura crítica.** Problema: aterrizaje autónomo completo. Sensores/marcadores: visión onboard y fusión multisensor; el resumen accesible no enfatiza un fiducial específico. Validación: hardware real con percepción en el lazo. Plataforma: móvil no marina. Resultados: demostración de autonomía onboard, sin detalle numérico agregado visible en la ficha accesible. Relación con tu trabajo: muestra el estándar de lo que significa un pipeline cerrado. Limitación abierta: no aporta banco marino sintético ni compara explícitamente la exactitud geométrica del pose estimator con ground truth del simulador. citeturn21search13

### Keipour et al. 2022

Keipour et al. proponen un método para aterrizar un UAV sobre un vehículo en movimiento usando sólo cámara monocular, un LiDAR puntual y cómputo a bordo. El artículo subraya que no necesita marcadores IR ni canales extra de comunicación con la plataforma, y que fue probado en simulación, interiores y exteriores, alcanzando aterrizajes sobre vehículos a 15 km/h. Además, los autores liberan código y el entorno de simulación, lo que lo vuelve especialmente útil como antecedente metodológico de reproducibilidad. citeturn17view3turn22search9turn41search9

BibTeX sugerido:
```bibtex
@article{keipour2022visual,
  author  = {Azarakhsh Keipour and Guilherme A. S. Pereira and Rogerio Bonatti and Rohit Garg and Puru Rastogi and Geetesh Dubey and Sebastian Scherer},
  title   = {Visual Servoing Approach to Autonomous UAV Landing on a Moving Vehicle},
  journal = {Sensors},
  volume  = {22},
  number  = {17},
  pages   = {6549},
  year    = {2022},
  doi     = {10.3390/s22176549},
  url     = {https://doi.org/10.3390/s22176549}
}
```

**Resumen.** Este trabajo es de los más útiles para contrastar con una propuesta de aterrizaje visual moderna porque combina mínima sensórica, control visual directo y validación en varios dominios. A diferencia de muchos enfoques marker-based, evita depender de infraestructura especial del entorno. También es un buen antecedente para justificar el valor de una etapa de simulación previa a ensayos reales. El límite de esta línea es que el entorno sigue siendo terrestre y la variable dominante es la traslación del objetivo, no la oscilación marítima de la cubierta. citeturn17view3turn22search9

**Lectura crítica.** Problema: aterrizaje completo sobre vehículo en movimiento. Sensores/marcadores: cámara monocular, LiDAR puntual y patrón de plataforma; sin IR marker ni setup especial. Validación: simulación, indoor y outdoor. Plataforma: vehículo terrestre móvil. Resultados: aterrizaje a velocidades de hasta 15 km/h y publicación de código y simulador. Relación con tu trabajo: antecedente fuerte en V&V antes de campo. Limitación abierta: no contempla roll, pitch y heave inducidos por oleaje, ni un estudio específico de exactitud de pose marker-based frente a ground truth. citeturn17view3turn41search9

## Plataformas marinas, cubiertas oscilantes y bancos experimentales

### Sánchez-López et al. 2014

Sánchez-López et al. son un antecedente seminal y, para tu caso, de los más cercanos conceptualmente. El artículo propone aterrizaje visual autónomo sobre cubierta de barco y, para demostrar la eficacia de sus algoritmos, emula dinámica de cubierta para distintos estados de mar y tipos de buque mediante una plataforma de movimiento de seis grados de libertad. También implementa un sistema robusto de visión para medir la pose de la cubierta respecto del vehículo y filtra la estimación con Kalman. citeturn25view0turn26search2

BibTeX sugerido:
```bibtex
@article{sanchezlopez2014shipboard,
  author  = {Jose Luis Sanchez-Lopez and Jesus Pestana and Srikanth Saripalli and Pascual Campoy},
  title   = {An Approach Toward Visual Autonomous Ship Board Landing of a VTOL UAV},
  journal = {Journal of Intelligent \& Robotic Systems},
  volume  = {74},
  pages   = {113--127},
  year    = {2014},
  doi     = {10.1007/s10846-013-9926-3},
  url     = {https://doi.org/10.1007/s10846-013-9926-3}
}
```

**Resumen.** Este paper es especialmente valioso porque no reduce el problema a un “moving target” genérico; lo define explícitamente como shipboard landing y discute estados de mar, dirección de ola y modelado 6-DoF del buque. El sistema usa cámara monocular color orientada hacia abajo y una plataforma tipo helipad pintada con marcas típicas, no con fiduciales codificados. La simulación física con motion platform le permite estudiar oclusiones, cambios de intensidad y robustez de la visión sin depender de un barco real. citeturn25view0

**Lectura crítica.** Problema: aterrizaje visual en cubierta de barco. Sensores/marcadores: cámara monocular, helipad pintado, sensores sonar en fase final. Validación: banco físico 6-DoF, no buque real. Plataforma: cubierta marina sintetizada con movimiento dependiente del estado de mar. Resultados: el artículo enfatiza robustez frente a oclusión e iluminación y una simulación “accurate, realistic, random and simple enough”. Relación con tu trabajo: es probablemente el antecedente más claro para justificar bancos sustitutivos de embarcación real. Limitación abierta: no usa marcadores ArUco/AprilTag, no explota una infraestructura tipo ROS/Gazebo y no formula la validación como comparación cuantitativa del pose estimator con ground truth simulada. citeturn25view0

### Alarcón et al. 2019

Aunque ya lo tienen en el corpus, conviene tratarlo explícitamente como antecedente de contraste. Alarcón et al. presentan un sistema preciso y GNSS-free para aproximar y aterrizar en plataformas móviles con precisión centimétrica, pero la estimación relativa no proviene de visión sino de la medida de los ángulos de un cable físico que conecta UAV y plataforma. Justamente por eso es muy útil en un estado del arte: demuestra que la literatura sobre plataformas móviles no es homogénea y que existen soluciones de alta precisión que evitan por completo el problema de la percepción visual. citeturn40search2turn30search4

BibTeX sugerido:
```bibtex
@article{alarcon2019precise,
  author  = {Francisco Alarc{\'o}n and Manuel Garc{\'i}a and Ivan Maza and Antidio Viguria and An{\'i}bal Ollero},
  title   = {A Precise and GNSS-Free Landing System on Moving Platforms for Rotary-Wing UAVs},
  journal = {Sensors},
  volume  = {19},
  number  = {4},
  pages   = {886},
  year    = {2019},
  doi     = {10.3390/s19040886},
  url     = {https://doi.org/10.3390/s19040886}
}
```

**Resumen.** El artículo resuelve el problema de precisión en plataformas móviles desde otra filosofía: infraestructura física compartida y estimación relativa no visual. Eso le permite alcanzar precisión centimétrica y robustez alta, pero a costa de una instrumentación que no escala bien a escenarios donde el objetivo es evaluar la visión como sensor principal. Para tu capítulo es importante porque marca con claridad una frontera: no todo antecedente de landing on moving platforms es antecedente de pose estimation visual. citeturn40search2turn30search4

**Lectura crítica.** Problema: aterrizaje preciso GNSS-free. Sensores/marcadores: medición angular de cable; sin marcador visual. Validación: paper experimental con exactitud centimétrica. Plataforma: móvil, no específicamente marina. Resultados: precisión a nivel centimétrico y robustez alta. Relación con tu trabajo: sirve como contrapunto metodológico frente a la familia visual. Limitación abierta: no informa sobre fidelidad de pose vía cámara, no usa patrones fiduciales y no cubre la validación de percepción en escenarios de oleaje sintetizado. citeturn40search2turn30search4

### Delbene, Baglietto y Simetti 2022

Delbene et al. son uno de los antecedentes más cercanos a tu planteo entre los trabajos recientes y sí merecen un lugar central. El artículo introduce un procedimiento de aterrizaje autónomo de un quadrotor sobre un USV/catamarán en entorno marino, estimando pose y velocidad relativa mediante una visión que reconoce un conjunto de AprilTags sobre el vehículo y un sensor ultrasónico para robustecer la fase final. Además, los movimientos de la plataforma en simulación se replican a partir de datos reales tomados en mar, y la arquitectura está preparada tanto para software-in-the-loop como para integración en hardware real. citeturn42view0

BibTeX sugerido:
```bibtex
@article{delbene2022visual,
  author  = {Andrea Delbene and Marco Baglietto and Enrico Simetti},
  title   = {Visual Servoed Autonomous Landing of an UAV on a Catamaran in a Marine Environment},
  journal = {Sensors},
  volume  = {22},
  number  = {9},
  pages   = {3544},
  year    = {2022},
  doi     = {10.3390/s22093544},
  url     = {https://doi.org/10.3390/s22093544}
}
```

**Resumen.** Este trabajo se ubica exactamente en la frontera entre percepción marker-based, software architecture y operación marina. Su valor no está sólo en usar AprilTags, sino en combinar visión, ultrasónico, máquina de estados y una validación SIL alimentada con telemetría real del catamarán. Además, la arquitectura se diseñó explícitamente para ser modular y trasladable entre simulación y outdoor tests. En literatura marina reciente, es uno de los antecedentes más directos para un marco de validación progresiva antes del ensayo real. citeturn42view0

**Lectura crítica.** Problema: aterrizaje autónomo sobre USV en mar. Sensores/marcadores: AprilTags, GNSS de aproximación y ultrasonido para la fase final. Validación: SIL con movimientos replicados desde pruebas reales del catamarán, más validación offline del sistema visual sobre video real de un aterrizaje manual. Plataforma: catamarán USV. Resultados: modularidad ROS 2/Gazebo/PX4 y mejora de robustez con más tags en la plataforma. Relación con tu trabajo: es probablemente el antecedente más cercano desde el lado “marine + fiducials + simulation first”. Limitación abierta: no plantea la evaluación principal como benchmark cuantitativo de exactitud de pose frente a ground truth del simulador, y la validación real autónoma completa queda menos enfatizada que la arquitectura y la percepción. citeturn42view0

### Cho et al. 2022

El trabajo de Cho et al. es una referencia fuerte porque se toma en serio la cubierta oscilante y no sólo el desplazamiento horizontal del objetivo. Los autores proponen un sistema de aterrizaje autónomo sobre una pequeña cubierta de barco en alta velocidad y con oscilaciones por oleaje, basado en feed-forward image-based visual servoing, ganancia adaptativa, compensación de deformación de la característica visual y estimación de velocidad del barco por filtrado de Kalman y fusión sensorial. El artículo destaca plataformas experimentales duras y menciona condiciones equivalentes a Sea State 4. citeturn17view2turn22search16

BibTeX sugerido:
```bibtex
@article{cho2022shipdeck,
  author  = {Gangik Cho and Joonwon Choi and Geunsik Bae and Hyondong Oh},
  title   = {Autonomous Ship Deck Landing of a Quadrotor UAV Using Feed-Forward Image-Based Visual Servoing},
  journal = {Aerospace Science and Technology},
  year    = {2022},
  url      = {https://www.sciencedirect.com/science/article/pii/S1270963822005430}
}
```

**Resumen.** Si Sánchez-López es el antecedente seminal de simulación física de cubierta, Cho es una de las mejores referencias recientes para la lógica de aterrizaje completo sobre cubierta marina oscilante con visual servoing. El paper entiende que la dificultad no está sólo en detectar el blanco, sino en conservarlo en el field of view, compensar la deformación aparente debida a la actitud del barco y cerrar un procedimiento entero desde approach hasta touchdown. Esa visión de sistema completo es especialmente útil para contrastarla con trabajos que se ocupan sólo de pose estimation. citeturn17view2

**Lectura crítica.** Problema: aterrizaje autónomo completo sobre cubierta oscilante. Sensores/marcadores: cámara del UAV, AR tags cuidadosamente diseñados, GPS sobre el barco y Kalman/filter fusion. Validación: simulaciones y experimentos en condiciones duras equivalentes a Sea State 4. Plataforma: barco/cubierta marina móvil y oscilante. Resultados: enfoque FF-IBVS con compensación explícita de velocidad del target y de la forma visual. Relación con tu trabajo: legitimiza centrar la discusión en roll, pitch y heave como variables críticas. Limitación abierta: el paper privilegia el éxito del aterrizaje completo y no un benchmark separado de la exactitud del estimador de pose marker-based frente a ground truth. citeturn17view2turn22search16

### Morales et al. 2023

Morales et al., que ya tienen incorporado, son relevantes porque tratan conjuntamente el seguimiento autónomo de una plataforma móvil y la maniobra final de aterrizaje, dos etapas que a menudo aparecen separadas en la bibliografía. La ficha accesible confirma la publicación en *Sensors* y ubica el sistema en un montaje de dron y vehículo terrestre móvil. Aunque el resumen accesible no deja ver tantos detalles instrumentales como en Delbene o Cho, el paper es útil para señalar una tendencia clara de la literatura reciente: la unificación de tracking y touchdown dentro de una misma arquitectura visual. citeturn40search1turn40search7turn41search11

BibTeX sugerido:
```bibtex
@article{morales2023following,
  author  = {Jes{\'u}s Morales and Isabel Castelo and Rodrigo Serra and Pedro U. Lima and Meysam Basiri},
  title   = {Vision-Based Autonomous Following of a Moving Platform and Landing for an Unmanned Aerial Vehicle},
  journal = {Sensors},
  volume  = {23},
  number  = {2},
  pages   = {829},
  year    = {2023},
  doi     = {10.3390/s23020829},
  url     = {https://doi.org/10.3390/s23020829}
}
```

**Resumen.** El interés de este artículo para tu estado del arte no está en la condición marina, que no es su foco, sino en mostrar cómo la literatura reciente integra seguimiento, aproximación y aterrizaje dentro de un mismo framing experimental. En términos de posicionamiento bibliográfico, ayuda a mostrar que el campo ya no ve el landing como un simple “último metro”, sino como una secuencia de tareas visuales encadenadas. Eso lo acerca a tu proyecto desde la arquitectura funcional, pero no desde el modelado del oleaje. citeturn40search1turn40search7turn41search11

**Lectura crítica.** Problema: following y landing sobre plataforma móvil. Sensores/marcadores: visión onboard; la ficha accesible no permite fijar con seguridad la familia exacta de marcador sin ir al PDF final. Validación: sistema con dron y vehículo terrestre móvil. Plataforma: no marina. Resultados: el valor principal es integrar seguimiento y aterrizaje en una sola arquitectura. Relación con tu trabajo: útil para la transición entre percepción relativa y maniobra final. Limitación abierta: no trata roll/pitch/heave marinos ni la validación cuantitativa del estimador de pose contra truth sintética. citeturn40search1turn40search7turn41search11

### Neves, Claro y Pinto 2023

Neves et al. no resuelven el aterrizaje completo, pero sí un problema crítico para el entorno offshore: detección robusta de la plataforma de aterrizaje través de fusión temprana de cámara RGB, infrarroja y LiDAR. El paper reporta recalls de hasta 99% incluso con fallos individuales de sensor y condiciones adversas como deslumbramiento, oscuridad y niebla, con inferencia menor a 6 ms. Para un estado del arte serio conviene incluirlo porque muestra que, en el entorno marino, el problema de percepción no siempre se resuelve sólo con un marcador monocromático observado por una única cámara. citeturn37search1turn37search3

BibTeX sugerido:
```bibtex
@article{neves2023offshore,
  author  = {Francisco Soares Neves and Rafael Marques Claro and Andry Maykol Pinto},
  title   = {End-to-End Detection of a Landing Platform for Offshore UAVs Based on a Multimodal Early Fusion Approach},
  journal = {Sensors},
  volume  = {23},
  number  = {5},
  pages   = {2434},
  year    = {2023},
  doi     = {10.3390/s23052434},
  url     = {https://doi.org/10.3390/s23052434}
}
```

**Resumen.** Este artículo desplaza la atención desde “¿cómo aterrizo?” hacia “¿cómo percibo de forma segura en offshore?”. Esa distinción es pertinente para tu capítulo porque permite mostrar que la percepción sobre el mar puede ser, por sí sola, un problema de investigación autónomo. En comparación con pipelines basados en un solo fiducial y solvePnP, Neves introduce redundancia sensorial y robustez ambiental, pero a costa de mayor complejidad y menor interpretabilidad geométrica del estimador. citeturn37search1turn37search3

**Lectura crítica.** Problema: detección de plataforma offshore, no touchdown completo. Sensores/marcadores: RGB, IR y LiDAR; sin depender únicamente de fiduciales planos. Validación: evaluación de detector bajo fallo de sensor y clima adverso. Plataforma: offshore marino. Resultados: recall hasta 99% e inferencia inferior a 6 ms. Relación con tu trabajo: sirve para justificar por qué una solución monocular marker-based puede elegirse deliberadamente cuando interesa exactitud geométrica y benchmarking, no máxima robustez multimodal. Limitación abierta: no aborda comparación explícita entre pose visual estimada y ground truth 6D de simulador. citeturn37search1turn37search3

### Wu et al. 2024

Wu et al. son una referencia reciente y útil porque vuelven al caso marítimo de UAV sobre ASV/barco, pero con una filosofía distinta a Delbene o Cho: controlador adaptativo NN-PSO que ajusta en línea un PID de velocidad usando sólo cámara de bajo costo y sensor de altitud. El paper reporta errores medios de unos 5 cm en plataforma estática y 10 cm en barcos en movimiento, y además afirma un incremento del máximo landing speed aceptable hasta el 80.9% de la velocidad tope del UAV. citeturn17view1turn10search2turn10search16

BibTeX sugerido:
```bibtex
@article{wu2024adaptive,
  author  = {Li-Fan Wu and Zihan Wang and Mo Rastgaar and Nina Mahmoudian},
  title   = {Adaptive Velocity Control for UAV Boat Landing: A Neural Network and Particle Swarm Optimization Approach},
  journal = {Journal of Intelligent \& Robotic Systems},
  year    = {2024},
  doi     = {10.1007/s10846-024-02201-4},
  url     = {https://doi.org/10.1007/s10846-024-02201-4}
}
```

**Resumen.** El valor de este trabajo para tu revisión es doble. Primero, confirma que el problema UAV–boat sigue activo en 2024 y que la literatura reciente ya reporta métricas concretas de error medio en dispositivos reales. Segundo, muestra una alternancia metodológica importante: no toda la mejora viene por el lado de la percepción; parte del desempeño se empuja desde la adaptación del controlador. Eso ayuda a separar con claridad qué parte del problema pertenece a pose estimation y cuál al control. citeturn17view1turn10search16

**Lectura crítica.** Problema: aterrizaje completo sobre ASV/boat. Sensores/marcadores: cámara low-cost y sensor de altitud; la ficha accesible no resalta un fiducial particular. Validación: múltiples vuelos reales. Plataforma: barco/ASV. Resultados: ~5 cm en caso estático, ~10 cm en caso dinámico y ampliación del envelope de velocidad. Relación con tu trabajo: ofrece un comparador reciente con métricas de hardware real. Limitación abierta: no aísla la exactitud geométrica del estimador visual, no usa banco sintético de ground truth y el movimiento marino se observa como perturbación global del sistema, no como variable independiente para V&V de percepción. citeturn17view1turn10search2turn10search16

## Obras habilitantes para estimación de pose con marcadores fiduciales

### Garrido-Jurado et al. 2014 y Romero-Ramírez et al. 2018

Si el proyecto usa ArUco y solvePnP, estos dos artículos son obligatorios en el estado del arte porque fundan y aceleran la familia ArUco. Garrido-Jurado et al. presentan la generación y detección de marcadores altamente fiables bajo oclusión, y posicionan el sistema como especialmente apropiado para estimación de pose de cámara. Romero-Ramírez et al. mejoran la detección de marcadores cuadrados con una implementación acelerada, relevante cuando la pose debe estimarse en tiempo real sobre hardware embarcado. citeturn12search0turn12search6turn12search2turn12search5

BibTeX sugerido:
```bibtex
@article{garrido2014aruco,
  author  = {Sergio Garrido-Jurado and Rafael Mu{\~n}oz-Salinas and Francisco J. Madrid-Cuevas and Manuel J. Mar{\'i}n-Jim{\'e}nez},
  title   = {Automatic Generation and Detection of Highly Reliable Fiducial Markers under Occlusion},
  journal = {Pattern Recognition},
  volume  = {47},
  number  = {6},
  pages   = {2280--2292},
  year    = {2014},
  doi     = {10.1016/j.patcog.2014.01.005},
  url     = {https://doi.org/10.1016/j.patcog.2014.01.005}
}

@article{romeroramirez2018speeded,
  author  = {Francisco J. Romero-Ramirez and Rafael Mu{\~n}oz-Salinas and Rafael Medina-Carnicer},
  title   = {Speeded Up Detection of Squared Fiducial Markers},
  journal = {Image and Vision Computing},
  volume  = {76},
  pages   = {38--47},
  year    = {2018},
  doi     = {10.1016/j.imavis.2018.05.004},
  url     = {https://doi.org/10.1016/j.imavis.2018.05.004}
}
```

**Resumen.** Estos artículos no resuelven el aterrizaje por sí mismos, pero sí resuelven la pieza de percepción 6D que muchos sistemas de aterrizaje reutilizan después. El primero justifica por qué ArUco se vuelve una opción natural para tareas de localización relativa; el segundo reduce el costo computacional de detección, lo que es crucial cuando la cámara está en el dron o cuando se quiere comparar performance en varias vistas y tasas de cuadro. En un capítulo académico, conviene presentarlos como obras habilitantes, no como papers de landing. citeturn12search0turn12search2turn12search15

**Lectura crítica.** Problema: detección robusta y eficiente de fiduciales cuadrados. Sensores/marcadores: cámara monocular y marcadores ArUco. Validación: experimentos de visión por computador, no hardware de aterrizaje. Plataforma: no aplica. Resultados: robustez bajo oclusión y aceleración de detección. Relación con tu trabajo: son la base bibliográfica directa del módulo de percepción marker-based. Limitación abierta: no estudian dinámica marina ni el comportamiento del estimador cuando la plataforma induce roll, pitch y heave comparables a oleaje. citeturn12search0turn12search2turn12search12

### Olson 2011 y Wang–Olson 2016

La línea AprilTag cumple un rol análogo al de ArUco, y por eso es imprescindible para contextualizar papers como Delbene 2022. Olson 2011 define AprilTag como un sistema fiducial robusto y flexible capaz de localizar 6 DoF desde una sola imagen; Wang y Olson 2016 rediseñan el detector para mejorar robustez, tasa de detección y tiempo de cómputo, especialmente en tags pequeños. En la práctica, muchas comparaciones entre sistemas de aterrizaje terminan siendo comparaciones indirectas entre elecciones ArUco versus AprilTag. citeturn13search1turn13search7turn13search3turn13search4

BibTeX sugerido:
```bibtex
@inproceedings{olson2011apriltag,
  author    = {Edwin Olson},
  title     = {AprilTag: A Robust and Flexible Visual Fiducial System},
  booktitle = {Proceedings of the IEEE International Conference on Robotics and Automation},
  pages     = {3400--3407},
  year      = {2011},
  doi       = {10.1109/ICRA.2011.5979561},
  url       = {https://doi.org/10.1109/ICRA.2011.5979561}
}

@inproceedings{wang2016apriltag2,
  author    = {John Wang and Edwin Olson},
  title     = {AprilTag 2: Efficient and Robust Fiducial Detection},
  booktitle = {2016 IEEE/RSJ International Conference on Intelligent Robots and Systems},
  year      = {2016},
  doi       = {10.1109/IROS.2016.7759617},
  url       = {https://doi.org/10.1109/IROS.2016.7759617}
}
```

**Resumen.** Estos dos trabajos son habilitadores de toda una subfamilia de papers marinos y terrestres que usan tags codificados como landing pad. Lo importante para tu capítulo es que muestran que la decisión sobre “qué fiducial usar” no es trivial: afecta robustez a oclusión, distancia, tamaño aparente y costo computacional. Por eso conviene no presentar ArUco o AprilTag como detalles de implementación, sino como elecciones de diseño con consecuencias experimentales. citeturn13search1turn13search3turn13search6

**Lectura crítica.** Problema: fiduciales 6-DoF robustos y eficientes. Sensores/marcadores: cámara monocular, AprilTags. Validación: benchmark visual, no aterrizaje. Plataforma: no aplica. Resultados: localización 6DoF desde imagen única y mejora posterior del detector en robustez y eficiencia. Relación con tu trabajo: permiten justificar por qué un proyecto basado en ArUco debe compararse conceptualmente con la línea AprilTag usada en varios antecedentes marinos. Limitación abierta: no incluyen escenarios de oleaje, cámaras aéreas móviles ni comparación contra un simulador físico de plataforma marina sintética. citeturn13search1turn13search3turn13search7

### La pieza algorítmica de PnP

Aunque no es un paper de landing, la familia PnP es el puente formal entre un fiducial detectado y una pose 6D estimada. El paper EPnP de Lepetit et al. proporciona una solución O(n) al problema Perspective-n-Point y su espíritu está detrás de implementaciones operativas muy usadas en bibliotecas de visión; la documentación de OpenCV explica precisamente que `solvePnP` devuelve rotación y traslación del objeto respecto de la cámara a partir de correspondencias 3D–2D. Para un trabajo como el tuyo, esta referencia ayuda a separar con rigor “detección del marcador” de “estimación geométrica de pose”. citeturn14search3turn14search1

## Simulación, SIL y validación previa al ensayo real

La literatura reciente muestra una tendencia clara: la simulación ya no se usa sólo para depurar controladores, sino como etapa explícita de verificación y validación antes del mar o del campo. Delbene 2022 es un caso claro porque construye un entorno SIL con telemetría real del catamarán; Keipour 2022 acompaña su paper con simulador y código; y un paper de infraestructura como Nguyen y Nguyen 2019 muestra que la combinación Gazebo más PX4 es una base recurrente para visión en el lazo sobre UAVs. En otras palabras, el uso de simulación no es accesorio sino una práctica consolidada del estado del arte. citeturn42view0turn17view3turn8search20

BibTeX sugerido para la pieza de infraestructura:
```bibtex
@inproceedings{nguyen2019sitl,
  author    = {K. Dang Nguyen and T.-T. Nguyen},
  title     = {Vision-Based Software-in-the-Loop-Simulation for Unmanned Aerial Vehicles Using Gazebo and PX4 Open Source},
  booktitle = {2019 International Conference on System Science and Engineering},
  pages     = {429--432},
  year      = {2019},
  doi       = {10.1109/ICSSE.2019.8823322},
  url       = {https://doi.org/10.1109/ICSSE.2019.8823322}
}
```

Al mismo tiempo, la review de de Paula et al. deja una observación muy útil para tu capítulo: una buena parte de la literatura naval recurre a plataformas “scaled-down” o simplificadas, con distintas combinaciones de heave, pitch y roll, y los autores remarcan que no existe todavía un marco común para escalar o sintetizar el movimiento de cubierta sin introducir irrealismos. Ese diagnóstico legitima directamente una tesis metodológica como la tuya: construir un banco sintético controlable y luego validar si la dinámica postural reproducida conserva sentido físico suficiente para estudiar percepción y comparación contra ground truth. citeturn31view1turn31view3turn31view4

Como antecedentes muy recientes y cercanos temáticamente, aunque de peso bibliográfico menor que los journals revisados por pares de arriba, también aparecen trabajos de 2025 sobre uso de marcadores fractales ArUco y plataformas 4-DoF para cubierta simulada. Esos papers muestran que la comunidad está empujando justo hacia el nicho “pose estimation marker-based sobre deck sintético”, pero todavía con evidencia dispersa y sin una convención dominante de benchmark. Conviene citarlos como antecedentes adyacentes, no como base principal del capítulo. citeturn28search1turn28search4turn30search16

## Síntesis comparativa

La tabla siguiente resume los antecedentes más útiles para comparar arquitectura experimental, percepción y tipo de validación.

| Autor/año | plataforma objetivo | entorno marino o no | percepción usada | marcador usado | simulación | validación real | aterrizaje completo o solo estimación | relación con tu trabajo |
|---|---|---|---|---|---|---|---|---|
| Lee 2012 citeturn19search1turn19search7 | VTOL sobre plataforma móvil | No marino | IBVS monocular | no explicitado como fiducial codificado | no detallado en ficha accesible | sí, antecedente experimental clásico | completo | antecedente fundacional del lazo visión-control |
| Araar 2017 citeturn43search0turn43search3 | multirrotor sobre plataforma móvil | No marino | visión relativa | landing pad artificial diseñado ad hoc | sí | sí | completo | conecta diseño del pad con pose estimation |
| Falanga 2017 citeturn21search13 | quadrotor sobre plataforma móvil | No marino | visión onboard + fusión multisensor | no enfatizado | sí / pipeline validado | sí | completo | benchmark de autonomía onboard real |
| Sánchez-López 2014 citeturn25view0turn26search2 | VTOL sobre cubierta de barco simulada | Marino | cámara monocular + Kalman | helipad pintado | banco físico 6-DoF | sí, sobre testbed | estimación + enfoque de landing | antecedente más directo en cubierta marina sintética |
| Alarcón 2019 citeturn40search2turn30search4 | UAV sobre plataforma móvil | No marino en foco | navegación relativa no visual | ninguno | sí | sí | completo | contrapunto: precisión alta sin visión |
| Keipour 2022 citeturn17view3turn41search9 | UAV sobre vehículo terrestre | No marino | cámara monocular + LiDAR puntual + servoing visual | patrón de landing, sin IR especial | sí | sí | completo | fuerte antecedente en V&V y reproducibilidad |
| Delbene 2022 citeturn42view0 | quadrotor sobre catamarán/USV | Marino | visión + GNSS + ultrasónico + máquina de estados | AprilTags | SIL con telemetría real | sí, validación del sistema visual sobre video real | procedimiento completo en SIL; visión validada con datos reales | uno de los antecedentes más cercanos a tu enfoque |
| Cho 2022 citeturn17view2turn22search16 | quadrotor sobre ship deck oscilante | Marino | FF-IBVS + GPS/barco + Kalman | AR tags | sí | sí | completo | legitima centrarse en roll/pitch/heave y FOV |
| Morales 2023 citeturn40search1turn40search7turn41search11 | UAV sobre plataforma móvil terrestre | No marino | visión para following + landing | no visible en ficha accesible | no claro | sí | completo | integra seguimiento y aterrizaje en una sola arquitectura |
| Neves 2023 citeturn37search1turn37search3 | plataforma offshore | Marino | RGB + IR + LiDAR, fusión temprana | no centrado en fiducial plano | sí, benchmark perceptual | validación perceptual | solo detección/percepción | muestra la alternativa multimodal a marker-based monocular |
| Wu 2024 citeturn17view1turn10search16 | UAV sobre boat/ASV | Marino | cámara low-cost + sensor de altitud + control adaptativo | no enfatizado | no principal | sí | completo | comparador reciente con métricas reales de error |

En conjunto, la tabla muestra una asimetría persistente: los trabajos más fuertes en aterrizaje completo suelen priorizar tasa de éxito y control cerrado; los trabajos más cercanos a percepción pura priorizan robustez del detector o del tag. Son menos frecuentes los estudios que tomen la estimación de pose marker-based como objeto principal de validación cuantitativa frente a una verdad de terreno limpia y controlable, especialmente bajo movimientos marinos sintetizados. citeturn27view0turn38view0turn25view0turn42view0

## Ubicación del aporte dentro del panorama

Visto el corpus, el proyecto que describís quedaría ubicado en una zona todavía poco saturada de la literatura. No compite directamente con Alarcón 2019, porque allí la novedad está en la infraestructura física no visual; tampoco replica Delbene 2022, porque ese paper enfatiza una arquitectura completa de aterrizaje marino con SIL alimentado por telemetría real y validación de visión sobre video real, no un benchmark geométrico sistemático del pose estimator; y no coincide con Morales 2023, porque ese antecedente se mueve más en el problema de seguimiento y aterrizaje sobre plataforma móvil que en la validación de percepción bajo oleaje sintetizado. citeturn40search2turn42view0turn40search1

La contribución diferencial del proyecto, tal como lo describís, puede formularse con claridad en cuatro ejes. Primero, desplaza el centro de la evaluación al bloque de estimación de pose visual y lo compara contra ground truth del simulador, algo que en muchos antecedentes queda absorbido por métricas finales de aterrizaje. Segundo, sintetiza movimiento marino a partir de roll, pitch y heave sobre una plataforma sustitutiva, lo que dialoga con Sánchez-López 2014 y con la crítica de de Paula 2024 sobre la falta de un marco común para plataformas escaladas, pero lo hace con una instrumentación distinta y potencialmente más accesible. Tercero, admite dos geometrías de observación —cámara fija y cámara inferior de dron— dentro del mismo marco de validación, lo que permite estudiar sensibilidad a viewpoint sin cambiar el target. Cuarto, incorpora una etapa preliminar con hardware real para discutir la plausibilidad física de la síntesis postural antes de trasladar la pregunta al simulador. citeturn25view0turn31view3turn31view4

Dicho de otro modo: mientras buena parte del estado del arte se pregunta “¿puedo aterrizar exitosamente?”, tu proyecto se coloca en una pregunta más fina y metodológicamente muy útil para un informe académico: “¿cuándo y con qué fidelidad geométrica puedo confiar en una estimación visual de pose sobre una plataforma con movimiento marino sintetizado, antes de exponerme al costo y al riesgo del mar real?”. Esa pregunta no reemplaza a la literatura de aterrizaje completo; la complementa y le da una etapa de V&V que hoy aparece fragmentaria. citeturn42view0turn17view3turn25view0turn27view0

## Estructura sugerida para el capítulo de estado del arte

Una estructura sólida de cinco subsecciones, que primero ordene el panorama general y recién al final ubique el aporte del proyecto, podría ser la siguiente:

### Aterrizaje autónomo de UAVs sobre plataformas móviles

Abrir con la evolución desde helipads estáticos hacia plataformas móviles, mostrando la transición desde visión basada en seguimiento visual simple a arquitecturas completas de visual servoing y control cerrado. Aquí entran Lee 2012, Araar 2017, Falanga 2017 y Keipour 2022 como línea troncal no marina. citeturn19search1turn43search0turn21search13turn17view3

### Operación marítima y cubiertas sometidas a oleaje

Pasar después al caso marino como subproblema más exigente: GNSS insuficiente, dinámica de cubierta, acoplamiento entre heave, roll y pitch, field of view y sincronización con el touchdown. Aquí conviene presentar Sánchez-López 2014, Delbene 2022, Cho 2022 y Wu 2024, y usar Alarcón 2019 como contraste metodológico no visual. citeturn25view0turn42view0turn17view2turn17view1turn40search2

### Estimación de pose visual con marcadores fiduciales

Luego separar explícitamente la literatura de percepción de la literatura de control. Esta subsección puede introducir ArUco, AprilTag y la familia PnP como tecnologías habilitantes para localización relativa 6D. Aquí entran Garrido-Jurado 2014, Olson 2011, Wang–Olson 2016, Romero-Ramírez 2018 y una breve mención a EPnP como fundamento geométrico del solvePnP. citeturn12search0turn13search1turn13search3turn12search2turn14search3turn14search1

### Simulación, software-in-the-loop y bancos experimentales sustitutivos

Después conviene una subsección dedicada sólo a validación. Ahí se puede mostrar cómo la simulación pasa de ser entorno auxiliar a componente central del proceso de verificación, incluyendo SIL, motion platforms, replay de telemetría real y testbeds sustitutos del barco. Delbene 2022, Nguyen 2019 y Sánchez-López 2014 son las citas más útiles; de Paula 2024 sirve para justificar la discusión metodológica sobre fidelidad del movimiento sintetizado. citeturn42view0turn8search20turn25view0turn27view0

### Síntesis crítica y ubicación del proyecto

Recién aquí conviene cerrar el capítulo ubicando el aporte del proyecto: un framework de simulación y validación para estimación de pose visual en escenarios marinos, con movimiento sintético físicamente interpretable, marcador fiducial, dos configuraciones de cámara y comparación directa contra ground truth del simulador. El argumento de cierre puede ser que la literatura vigente cubre bien el aterrizaje completo, razonablemente bien la percepción marker-based y cada vez mejor la simulación previa a campo, pero todavía ofrece pocos marcos específicamente diseñados para validar cuantitativamente el bloque de pose estimation bajo dinámica marina sintetizada. citeturn27view0turn38view0turn25view0turn42view0