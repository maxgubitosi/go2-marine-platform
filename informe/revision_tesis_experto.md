# Revisión experta: Correcciones y mejoras obligatorias para entrega final

> Revisión exhaustiva del documento `informe/main.tex`, código fuente del repositorio completo (`src/`, `aruco_relative_pose/`, `marine_robot_dataset/`, configs, URDF, scripts) y bibliografía. Revisor experto en robótica marina, visión por computadora y sistemas ROS2.

---

## Resumen ejecutivo de hallazgos críticos (bloqueantes)

1. **Error metrológico en la altura de la cámara fija:** existe una discrepancia de **1 cm** (1,945 m vs 1,955 m) entre el script `estimate_relative_pose.py` y `evaluate_realtime_aruco.py`. Esto introduce un bias sistemático en el eje Z (heave) que invalida parcialmente la comparación entre pipelines.
2. **Offset de yaw del marcador no declarado:** el código aplica un `yaw_offset_rad = -π/2` entre el frame del ArUco y `base_link`, pero la tesis asume alineación rígida sin rotación relativa. Esto sesga la interpretación de los errores angulares y la reconstrucción del GT.
3. **Tasa de detección inexplicablemente baja:** la cámara fija simulada corre a **30 Hz**, pero el baseline reporta una tasa de detección de solo **4,78 Hz** (~16 % de éxito). En el dron, la cámara es **15 Hz** y la detección es **4,6–5,3 Hz** (~30 %). La tesis no explica por qué se pierden más del 70 % de los frames en el caso fijo. ¿Es un cuello de botella del nodo Python? ¿Un bug de callback? ¿El marcador sale del FOV? En cámara fija nadir esto no debería ocurrir.
4. **Sesgo sistemático en Y del dron no investigado:** valores de **-0,15 m a -0,32 m** en el eje lateral son demasiado grandes para atribuirlos a ruido de esquina. La tesis los reporta pero no hipotetiza su origen (¿error en las extrínsecas del dron? ¿ausencia de joint `optical` en el URDF del SJTU?).
5. **Figuras y tablas huérfanas:** **11 figuras** y **3 tablas** con `\label{}` nunca son referenciadas en el texto con `\ref{}`. En una entrega final, esto es inaceptable: o se integran al flujo narrativo o se eliminan.
6. **Colisión de topics `/aruco/pose`:** ambos detectores (cámara fija y dron) publican en los **mismos topics absolutos**. La tesis no advierte este riesgo de arquitectura, que impediría ejecutar ambos escenarios simultáneamente.
7. **Modelo de oleaje "irregular" sin fundamento físico:** el código implementa una suma de senos con frecuencias arbitrarias (1,3×, 2,1×, etc.) que no corresponden a ningún espectro oceánico (JONSWAP, Pierson-Moskowitz). Llamarlo "irregular" en una tesis de ingeniería es una sobredeclaración metodológica.
8. **Laboratorio sin evaluación visual ni heave dinámico:** los ensayos R4/R5 no incluyeron heave oscilatorio ni ground truth visual. El resumen y las conclusiones presentan el laboratorio como validación del "framework de estimación de pose", pero en realidad solo validaron la dinámica del robot. Esto es una discontinuidad metodológica que debe explicitarse con mayor fuerza en el resumen.
9. **Inconsistencia numérica en retardos de R5:** la Tabla `tab:lab_r4_r5` reporta lag óptimo para R5 de 0,55 s / 1,20 s, pero la Figura `fig:lab_error_hist` (caption) dice 0,58 s / 1,16 s.
10. **Marco teórico con ecuaciones ornamentales:** las ecuaciones de dinámica de Fossen, del cuadrúpedo multicuerpo y del Jacobiano de proyección nunca se usan en el análisis experimental. Un revisor experto las leerá como "relleno" si no se conectan con los resultados.

---

## 1. Preámbulo y estructura del documento

| Problema | Severidad | Detalle |
|---|---|---|
| Paquetes LaTeX redundantes/conflictivos | Medio | Se cargan `inputenc` y `fontenc` (líneas 3–4) pero luego `fontspec` (línea 52), que los invalida en XeLaTeX. `tikz` se carga dos veces (l. 10 y 35). `pdflscape` dos veces (l. 21 y 39). Limpieza profesional requerida. |
| Comandos muertos en preámbulo | Medio | `\figureplaceholder`, `\pendingcitation`, `\pendingreal`, `\analysisplaceholder` se definen pero **nunca se invocan** en el cuerpo. Eliminadlos o comentadlos. |
| Comentarios de desarrollador en el cuerpo | Alto | Líneas 84–91 y 2515–2517 contienen comentarios tipo `TODO`, `FIXME` y notas internas ("recortar la mitad superior o aplicar edición con IA"). **Deben eliminarse** en la versión final. |
| `\section` forzada a `\clearpage` | Medio | La redefinición global (l. 95–96) genera páginas en blanco innecesarias entre secciones cortas. Considerad aplicar `\clearpage` solo donde sea estrictamente necesario. |

---

## 2. Resumen (l. 136–169)

| Problema | Severidad | Detalle |
|---|---|---|
| Sobrevenda del alcance del laboratorio | Alto | El resumen afirma: *"En laboratorio se verifica que la consigna postural llega al robot... y que el framework propuesto permite estudiar percepción, movimiento y evaluación"*. Sin embargo, **en laboratorio no se evaluó la percepción visual cuantitativamente** (no hay GT visual ni comparación pose estimada vs real en el laboratorio). El lector espera, tras leer el resumen, que el laboratorio validó los tres eslabones. Recomiendo reescribir el párrafo del laboratorio para que diga explícitamente que en esta etapa se aisló la dinámica del robot y que la validación visual conjunta queda para trabajo futuro. |
| Precisión numérica | Medio | "Error medio de posición de 5,8 cm" y "2°–3° en roll y pitch". Estos son valores agregados. Considerad añadir el rango de variabilidad entre repeticiones para no dar una falsa sensación de exactitud absoluta. |

---

## 3. Capítulo 1: Motivación e Introducción (l. 172–465)

| Problema | Severidad | Detalle |
|---|---|---|
| Figura `fig:intro_framework_overview` huérfana | Alto | Nunca se la referencia con `\ref{}` en el texto. Aparece en la Introducción pero no se le hace mención narrativa. |
| Tautología | Medio | Línea 2247 (en resultados, pero vale la pena señalarlo aquí por contexto): *"la evidencia visual queda sostenida por una cantidad de observaciones claramente mayor que en las campañas usadas en campañas preliminares"*. Repetición de "campañas". |
| Descripción del dron SJTU | Medio | La tesis nunca explica qué es el `sjtu_drone` (un paquete de simulación académico de Gazebo). Debéis justificar por qué se eligió este dron en particular frente a otros modelos (ej. Iris, Crazyflie, etc.). |

---

## 4. Capítulo 2: Estado del arte (l. 468–617)

| Problema | Severidad | Detalle |
|---|---|---|
| Cita huérfana en `.bib` | Medio | La entrada `opencv_aruco_tutorial` existe en `bibliography.bib` pero **nunca se cita** en el texto. Eliminadla o citadla en el marco teórico/metodología. |
| Inconsistencia ortográfica autor `.bib` vs. texto | Medio | `SanchezLopez2014` y `RomeroRamirez2018` aparecen sin tildes en el `.bib` pero con tildes en el cuerpo. Biblatex con XeLaTeX renderizará los nombres sin tilde en la bibliografía final, generando una inconsistencia visual entre cita narrativa y lista de referencias. Corregid el `.bib` para usar Unicode (`Sánchez-López`, `Romero-Ramírez`). |

---

## 5. Capítulo 3: Marco teórico (l. 619–1477)

Este capítulo es el más vulnerable a la crítica de un experto por la abundancia de formalismo sin uso posterior.

### 5.1. Ecuaciones ornamentales sin conexión experimental
**Severidad: Alta**

Las siguientes ecuaciones se presentan con rigor matemático pero **no se utilizan en ningún análisis, diseño o interpretación de resultados**:

- `eq:marine_dynamics` (dinámica completa 6-DoF de Fossen). No se resuelve ni se usa para definir los parámetros del simulador.
- `eq:quadruped_dynamics` (dinámica multicuerpo del cuadrúpedo). No se usa para el control postural; el trabajo delega esto al stack CHAMP.
- `eq:contact_velocity_constraint`, `eq:contact_acceleration_constraint`. No se verifican experimentalmente.
- `eq:support_polygon_condition` (estabilidad). No se calcula numéricamente ni se usa para fijar los límites de roll/pitch.
- `eq:leg_jacobian`, `eq:leg_inverse_differential_kinematics`. No se implementan en el simulador; el control es por pose del cuerpo, no por IK diferencial explícita.
- `eq:projection_jacobian_linearization`. No se usa para propagar incertidumbre de esquinas.

**Recomendación de experto:** para cada ecuación, o bien la elimináis y reemplazáis por una descripción conceptual, o bien conectáis explícitamente con el experimento. Por ejemplo, después de `eq:support_polygon_condition` podríais decir: *"Aunque en este trabajo no calculamos explícitamente el polígono de soporte en cada instante, esta condición justifica por qué saturamos las amplitudes a ±15°/±10°: valores mayores harían que el simulador CHAMP rechace la consigna por inestabilidad."*

### 5.2. Errores técnicos en la descripción geométrica

| Problema | Severidad | Detalle |
|---|---|---|
| `yaw_offset_rad = -π/2` omitido | **Crítico** | En `estimate_relative_pose.py` (l. 553) se aplica `yaw = wrap_angle(yaw + yaw_offset_rad)` con valor `-1,5708` rad. Esto significa que el frame del ArUco está rotado 90° respecto de `base_link`. La tesis asume en todo el marco teórico (ecuaciones de transformación, Figura `fig:theory_frames_overview`) que el montaje es rígido sin rotación relativa. **Debe declararse este offset en la sección de marcos de referencia** y justificar si es un artefacto del modelo URDF del marcador o una convención de OpenCV. |
| Altura de cámara fija inconsistente | **Crítico** | `estimate_relative_pose.py` usa `base_to_camera_link_xyz = [0,0,-0,055]` (dando altura efectiva 1,945 m), mientras que `evaluate_realtime_aruco.py` usa `FIXED_CAM_POS = [0,0,1,955]` y el URDF del joint pone `z = -0,045`. **Hay 1 cm de discrepancia** que introduce un sesgo estructural en el GT de heave. Debéis unificar a 1,955 m (consistente con URDF) y re-procesar los resultados del baseline si es posible. |
| Extrínsecas del dron SJTU indefinidas | Alto | El URDF del dron no declara un joint `bottom_cam_link_optical`. El código asume la misma convención de rotaciones que la cámara fija, pero esto depende del plugin C++ del dron. Dado el sesgo sistemático en Y, **deberíais verificar si el plugin publica en un frame alineado con la convención ROS óptica o con otra orientación**. |
| Uso de EPnP en teoría vs. IPPE/Iterative en código | Medio | El marco teórico cita a Lepetit et al. (2009) y menciona EPnP como solución eficiente. Sin embargo, el código usa `SOLVEPNP_IPPE_SQUARE` (fallback a `ITERATIVE`). Nunca EPnP. **Corregid el texto** para que refleje el método realmente utilizado, o justificad por qué se prefirió IPPE. |

### 5.3. Figuras no referenciadas en este capítulo

- `fig:wave_platform_response` (l. 791)
- `fig:wave_regular_irregular` (l. 977)
- `fig:go2_postural_control_scheme` (l. 1111)
- `fig:aruco_marker_id0` (l. 1317)
- `fig:camera_marker_geometry` (l. 1346)

Todas son ilustrativas pero **huérfanas narrativamente**. Integradlas al flujo o eliminadlas.

---

## 6. Capítulo 4: Metodología (l. 1480–2090)

### 6.1. Parámetros del simulador y consistencia código-texto

| Problema | Severidad | Detalle |
|---|---|---|
| Nombre del topic de consigna | Alto | El código publica en `/body_pose` (`geometry_msgs/Pose`). El `README.md` del repo (que puede ser leído por revisores) dice `/go2/pose_rphz_cmd`, pero la tesis no menciona ninguno de los dos nombres en el cuerpo principal. El Apéndice tampoco lista topics. **Agregad una tabla de topics exactos en el Apéndice** para reproducibilidad. |
| Frecuencia de cámara fija vs. tasa de detección | **Crítico** | La cámara fija genera imágenes a **30 Hz** (`<update_rate>30</update_rate>` en `fixed_camera.xacro`). La tesis (l. 2245) reporta una tasa de detección de **4,78 Hz** en el baseline. Eso implica que el detector pierde el 84 % de los frames. Esto es anómalo: en una cámara estática nadir observando un marcador de 0,5 m a 2 m de distancia, la detección debería ser casi perfecta (30 Hz). ¿Es un problema de saturación de CPU del nodo Python? ¿Un throttling no declarado? ¿El `aruco_detector` publica solo cuando hay una detección válida pero el marcador desaparece por algún artefacto de Gazebo? **Debe explicarse o corregirse**. |
| Parámetros de distorsión asimétricos | Medio | La cámara fija tiene distorsión modelada (`k1=-0,05`, `k2=0,02`, etc.), pero la cámara del dron **no tiene distorsión** en su URDF. La tesis no menciona esta asimetría ni discute su impacto en la comparación entre escenarios. |
| Modelo "irregular" sin fundamento físico | Alto | La tesis describe el modo irregular como "superposición de armónicos" que aproxima un "estado de mar más irregular". Sin embargo, el código usa frecuencias arbitrarias (1,3×, 2,1×, 0,8×) sin relación con espectros oceánicos. **No debe llamarse "irregular"**; llamadlo "multi-sinusoidal" o "pseudo-aleatorio". Si queréis mantener la palabra "irregular", justificad las frecuencias elegidas o citad un modelo espectral. |
| Heave=0 en laboratorio sin justificación suficiente | Alto | Los ensayos R4/R5 usaron consigna de heave = 0 (l. 2743–2752). La tesis lo admite, pero esto rompe la simetría metodológica con la simulación, donde heave sí fue excitado. Dado que el resumen presenta el laboratorio como validación del "framework de movimiento marino", la ausencia de heave dinámico es una limitación grave que debe destacarse ya en el resumen y en las conclusiones. |
| Modo de marcha del Go2 no especificado | Medio | La tesis dice (l. 2444): *"Ambos ensayos mantuvieron el modo de marcha estable en un único valor durante toda la corrida, sin transiciones"*. ¿Cuál era ese modo? (`stand`, `trot`, `walk`?). Esto es relevante porque la rigidez del control postural depende del gait. |

### 6.2. Figuras y tablas huérfanas en este capítulo

- `fig:method_motion_components` (l. 1657) — **no referenciada**.
- `fig:method_wave_patterns` (l. 1690) — **no referenciada**.
- `fig:method_camera_sources` (l. 1855) — **no referenciada**.
- `fig:method_pipeline` (l. 1915) — **no referenciada** (aunque es el diagrama central del pipeline; debería referenciarse explícitamente en la metodología de simulación).
- `tab:method_sim_to_lab` (l. 1967) — **no referenciada** (tabla muy útil; debería citarse al inicio de la metodología de laboratorio).
- `tab:sim_selected_runs` (l. 2133) — **no referenciada** (tabla esencial; debería citarse en la introducción de la experimentación).
- `tab:lab_signals_summary` (l. 2465) — **no referenciada** (debería citarse al presentar R4).

---

## 7. Capítulo 5: Experimentación y resultados (l. 2093–2822)

### 7.1. Resultados en simulación

| Problema | Severidad | Detalle |
|---|---|---|
| Sesgo sistemático en Y no investigado | **Crítico** | Los sesgos en Y de R1, R2, R3 (-0,322; -0,297; -0,151 m) son del orden del 10–15 % de la distancia cámara–marcador. La tesis los atribuye a "limitación de la cadena geométrica" pero no propone hipótesis. Como experto, exijo al menos tres verificaciones: (a) ¿las extrínsecas del dron en el URDF coinciden con las asumidas en `evaluate_realtime_aruco.py`? (b) ¿El dron hovera realmente centrado en (x=0, y=0) o hay un offset de spawn? (c) ¿El plugin de la cámara bottom publica en un frame con convención Z-forward? Incluid al menos una hipótesis y, si es posible, una figura de diagnóstico (ej. error Y vs. pose del dron). |
| Inconsistencia en "ganancia dinámica promedio ~0,62" | Medio | La tesis dice (l. 2623) que la ganancia RMS promedio es ~0,62, pero luego indica que por rangos extremos roll da ~0,73 y pitch ~0,60. El promedio de 0,73 y 0,60 es 0,665, no 0,62. ¿Cómo se calculó el 0,62? ¿Es un promedio ponderado por duración? ¿Incluye heave? Clarificad el cálculo. |
| Pérdida de frames no explicada | Alto | Como se mencionó, la tasa de detección del baseline (4,78 Hz) frente a la frecuencia de cámara (30 Hz) es inexplicablemente baja para una escena estática. En el dron, 4,6 Hz frente a 15 Hz es más razonable (pérdidas por FOV, oclusión de patas, etc.), pero aún así debería explicarse. |

### 7.2. Resultados en laboratorio

| Problema | Severidad | Detalle |
|---|---|---|
| Inconsistencia numérica en retardos de R5 | Medio | Tabla `tab:lab_r4_r5`: R5 lag óptimo = 0,55 s (roll) / 1,20 s (pitch). Figura `fig:lab_error_hist` (caption): lag compensado = 0,58 s / 1,16 s. Estos 30–40 ms de diferencia no son menores en el contexto de una señal de 0,1 Hz. Unificad los valores o explicad de qué estimación provienen cada uno. |
| `/utlidar/robot_odom` no listado en `tab:ros_interfaces_lab` | Medio | La tesis menciona este topic en el análisis de R5 (l. 2708) pero la Tabla `tab:ros_interfaces_lab` no lo incluye. Agregadlo. |
| Nombre de archivo roto en Apéndice | Medio | `lab_real__robot_min` (doble guión bajo) parece un nombre truncado o corrupto. Verificad el nombre real en el repositorio. |

---

## 8. Capítulo 6: Conclusiones (l. 2825–2880)

| Problema | Severidad | Detalle |
|---|---|---|
| Sobredeclaración del alcance visual en laboratorio | Alto | La conclusión dice: *"En laboratorio, el aporte principal fue comprobar que la lógica de movimiento planteada en simulación conserva sentido físico sobre el Go2 real"*. Esto es correcto. Pero el resumen (y en menor medida la introducción) insinúa que el laboratorio también validó la percepción. **Asegurad que el resumen, la introducción y las conclusiones usen exactamente el mismo tono de alcance**: el laboratorio validó dinámica, no estimación visual. |
| Limitaciones bien delimitadas | Bien | Las limitaciones están bien enumeradas (l. 2862–2872). Considerad añadir explícitamente: *"No se ejecutó el pipeline visual durante los ensayos dinámicos R4/R5, por lo que no se dispone de error de estimación de pose en el robot real en movimiento"*. |

---

## 9. Trabajo futuro (l. 2884–2934)

En general está bien. Una recomendación de experto:

| Problema | Severidad | Detalle |
|---|---|---|
| Orden de prioridades | Medio | La validación conjunta (pipeline visual + robot real + GT externo) debería ser el **primer** ítem, no solo porque es el cierre lógico, sino porque sin ella el framework no demuestra viabilidad de extremo a extremo. Considerad invertir el orden: primero el cierre conjunto, luego OptiTrack, luego el modelo de olas. |

---

## 10. Apéndice (l. 2936–2991)

| Problema | Severidad | Detalle |
|---|---|---|
| Falta de tabla de topics exactos | Alto | El Apéndice lista rosbags pero no los topics ROS2 con sus tipos de mensaje. Para reproducibilidad, debería haber una tabla análoga a la del `README.md` del repo con los nombres canónicos (`/body_pose`, `/aruco/pose`, `/drone/bottom/image_raw`, etc.). |
| Nombres de archivos inconsistentes | Medio | `lab_real__robot_min` (doble guión bajo). `lab_real_20260320_125002_movimiento_full_v3` dice "sólo metadata.yaml disponible en este checkout". Esto suena a nota de desarrollador. Reescribid o eliminad la fila si no aporta reproducibilidad. |
| Referencia a archivos de calibración | Medio | Se mencionan rutas `stereo_camera/config.yaml` y `stereo_camera/calibration/calibration_result.yaml`, pero no se incluyen en el repositorio listado en el directorio raíz. ¿Son privados? Si no están en el repo público, aclarad que se encuentran en una rama privada o en el workspace local. |

---

## 11. Problemas transversales de rigor científico

### 11.1. Reproducibilidad
El trabajo no incluye un `Dockerfile`, un `requirements.txt` completo para ROS2, ni instrucciones de build detalladas en el informe. Dado que el repo tiene una estructura compleja con submódulos (`unitree-go2-ros2`), la reproducibilidad completa es difícil. Para una entrega final de tesis de grado esto es aceptable, pero **deberíais versionar exactamente el commit del repo que se usó para cada campaña** (simulación abril 2026, laboratorio marzo/abril 2026).

### 11.2. Consistencia código–texto
- La tesis no menciona el flag `SOLVEPNP_IPPE_SQUARE`.
- La tesis no menciona el `yaw_offset_rad` del marcador.
- La tesis no menciona la discrepancia de 1 cm en la altura de cámara fija.
- El `README.md` del repo describe una arquitectura (`/go2/pose_rphz_cmd`) que no existe en la rama activa.

### 11.3. Métricas y su interpretación
- El error de posición euclidiano de 5,8 cm en el baseline **no debe interpretarse como precisión del detector en condiciones reales**, sino como error de toda la cadena (sincronización, alineación temporal, extrínsecas). La tesis lo aclara parcialmente, pero debería ser más explícita.
- El error angular se reporta como "error absoluto medio" ($\overline{|\Delta \theta|}$). Esto no es lo mismo que "error RMS angular". Si un revisor quiere comparar con otros trabajos, necesita saber qué métrica exacta usasteis. Especificad la fórmula en una nota al pie de la tabla.

---

## 12. Priorización de correcciones para la entrega final

### 🔴 Crítico (resolver obligatoriamente)
1. **Eliminar todos los comentarios de TODO/FIXME** del LaTeX.
2. **Referenciar o eliminar** las 11 figuras y 3 tablas huérfanas.
3. **Declarar el `yaw_offset_rad = -π/2`** en el marco teórico y justificarlo.
4. **Unificar la altura de la cámara fija** a 1,955 m (consistente con URDF) y verificar si los resultados del baseline cambian.
5. **Explicar la tasa de detección baja** (4,78 Hz vs 30 Hz) en el baseline o corregir el dato si fue un error de medición.
6. **Hipotecizar el origen del sesgo en Y** del dron con al menos una hipótesis verificable.
7. **Corregir el resumen** para no insinuar que el laboratorio validó la percepción visual.

### 🟡 Alto (afectan credibilidad)
8. Corregir inconsistencia numérica de lag en R5 (0,55/1,20 vs 0,58/1,16).
9. Corregir el `.bib` para que los nombres de autores usen tildes consistentes con el texto.
10. Eliminar o conectar las ecuaciones ornamentales del marco teórico.
11. Renombrar "oleaje irregular" a "superposición multi-sinusoidal" o justificar físicamente las frecuencias.
12. Incluir tabla de topics exactos en el Apéndice.
13. Especificar el modo de marcha del Go2 en laboratorio.

### 🟢 Medio (mejoran calidad)
14. Limpieza de preámbulo LaTeX (paquetes redundantes, comandos muertos).
15. Unificar notación de decimales en tablas.
16. Separar análisis de captions (algunas son ensayos en lugar de descripciones).
17. Añadir versión/commit del repo usado para cada campaña.

---

## Veredicto general

La tesis tiene una estructura narrativa sólida y una progresión metodológica clara (simulación → laboratorio). Sin embargo, para una entrega final, **debe cerrar las brechas de consistencia código-texto, explicar las anomalías numéricas (tasa de detección, sesgo en Y, lag inconsistente) y eliminar todo rastro de construcción incompleta (figuras huérfanas, TODOs, ecuaciones sin uso)**.

El hallazgo más grave para un revisor experto será la falta de explicación del sesgo en Y y la discrepancia del yaw offset no declarado, porque cuestionan la validez geométrica de toda la cadena de transformaciones.
