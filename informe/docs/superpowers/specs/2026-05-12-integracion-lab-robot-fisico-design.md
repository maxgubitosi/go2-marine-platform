# Diseño: Integración de resultados de laboratorio físico en el informe

**Fecha:** 2026-05-12
**Scope:** Sección 5.2 (Experimentos en laboratorio) + Apéndice de registros

---

## Contexto

Se incorpora la carpeta `informe/refs/lab_robot_fisico_entregable` que contiene
material listo para el informe: dos rosbags limpios del Go2 real (abril 2026),
figuras generadas, CSV de métricas y un memo con texto base.

El informe actual usa la corrida histórica de marzo 2026 como fuente principal
de la sección 5.2. El objetivo es reemplazarla por los ensayos de abril, que
son más limpios, cuantifican la ganancia dinámica y aíslan la fuente del error
observado en pruebas integradas con video.

---

## Convención de nomenclatura

Los ensayos de laboratorio siguen la numeración de las corridas de simulación
(baseline, R1, R2, R3):

| Etiqueta | Bag | Rol |
|---|---|---|
| **R4** | `lab_real_20260424_120323_strong_15_10` | Ensayo principal |
| **R5** | `lab_real_20260424_114454_robot_min` | Ensayo de control |
| *(sin etiqueta en el cuerpo)* | `lab_real_20260320_125002_movimiento_full_v3` | Referencia histórica — solo apéndice |

---

## Enfoque general

**Opción elegida:** reescritura del contenido de 5.2 usando R4/R5 como fuente
principal, con una sola oración en 5.2.1 que menciona el ensayo previo de marzo
para preservar la evidencia de amplitudes mayores (±19°/±15°).

El histórico **no aparece** en el análisis cuantitativo del cuerpo. Queda en el
apéndice como registro.

---

## Cambios por sección

### 5.2.1 — Presentación del material experimental

**Tipo:** Reescritura significativa.

**Estructura del bloque:**

1. **Párrafo de contexto** *(nuevo)*: Explica que un ensayo previo (marzo 2026,
   amplitudes ±19°/±15°) confirmó que el pipeline funciona en ese rango, pero
   que pruebas integradas con video presentaron incidentes de procesamiento. Para
   aislar la fuente del error se repitieron los ensayos en abril sin video y con
   tópicos mínimos.

2. **Figura de montaje** *(nueva)*: `lab_camera_fixed_raw.png` como evidencia
   visual del setup físico. Caption explícito: evidencia de montaje, no
   validación cuantitativa de ArUco.

3. **Párrafo de presentación de R4 y R5**: R4 como ensayo principal (59.66 s,
   cmd ±14.8°/±9.9°, 100% gait-9), R5 como ensayo de control de menor amplitud
   (59.67 s, cmd ±9.9°/±7.9°).

4. **Tabla de señales** (`tab:lab_signals_summary`): misma estructura que hoy,
   actualizada con frecuencias y conteos de R4.

**TODO comment a insertar:**
```
% TODO: agregar subsubsección sobre dificultades del pasaje simulación→laboratorio
% real: qué falló, por qué fue complejo (saturación de procesamiento, video en
% tiempo real, sincronización de tópicos), y qué aprendimos. Pendiente para un
% pass posterior del informe.
```

---

### 5.2.2 — Fidelidad del camino de comando

**Tipo:** Actualización de números y figura.

**Cambios:**
- Referencias al ensayo → "R4" en lugar de fecha o "esta corrida".
- Tabla `tab:lab_command_fidelity`: actualizar métricas:
  - Correlación roll: 0.999887 → **0.999957**
  - Correlación pitch: 0.999909 → **0.999953**
  - Desfase medio: 4.98 ms → **5.21 ms**
  - Desfase máximo: 10.18 ms → **10.08 ms**
- Figura: `lab_plot_02_api_fidelity.png` → `strong_15_10_plot_02_api_fidelity.png`.
  Caption actualizado con referencia a R4.

**Lo que no cambia:** argumento central, metodología de comparación, conclusión
de que el primer eslabón del pipeline no introduce error significativo.

---

### 5.2.3 — Comparación entre movimiento objetivo y respuesta del robot

**Tipo:** Actualización + contenido nuevo.

**Cambios:**

1. **Números de comando y respuesta:**

   | | Histórico (hoy) | R4 (nuevo) |
   |---|---|---|
   | Cmd roll | ±19.6° | ±14.8° |
   | Cmd pitch | ±14.7° | ±9.9° |
   | Real roll | −14.4° a 16.2° | −11.1° a 10.5° |
   | Real pitch | −11.5° a 11.5° | −5.4° a 6.6° |
   | Lag roll | 0.35 s | 0.45 s |
   | Lag pitch | 0.60 s | 0.95 s |
   | Corr. roll (best lag) | 0.969 | 0.954 |
   | Corr. pitch (best lag) | 0.968 | 0.984 |

2. **Ganancia dinámica** *(nuevo — primera aparición en el informe)*: párrafo
   que introduce y cuantifica la ganancia ~0.62 en R4 (relación entre amplitud
   comandada y amplitud real observada).

3. **Bloque de confirmación con R5** *(nuevo)*: párrafo breve + tabla comparativa
   R4 vs R5. El patrón (retardo + atenuación) persiste a menor amplitud, pero
   los parámetros varían: al bajar la consigna el lag *crece* y la ganancia
   *cae*. Esto se presenta como evidencia de comportamiento consistente y no
   como réplica exacta, evitando exagerar la similitud. Puede señalarse como
   indicio de no-linealidades del controlador interno del Go2:

   | Métrica | R4 | R5 |
   |---|---|---|
   | Cmd roll / pitch | ±14.8° / ±9.9° | ±9.9° / ±7.9° |
   | Lag roll / pitch | 0.45 s / 0.95 s | 0.55 s / 1.20 s |
   | Corr. roll / pitch | 0.954 / 0.984 | 0.937 / 0.973 |
   | Ganancia aprox. | 0.62 | 0.47 |

4. **Figuras** (3 swaps + 1 nueva):
   - `lab_plot_01_timeseries_cmd_vs_real.png` → `strong_15_10_plot_01_timeseries_cmd_vs_real.png`
   - `lab_plot_03_lag_correlation.png` → `strong_15_10_plot_03_lag_correlation.png`
   - `lab_plot_05_heave_z_comparison.png` → `strong_15_10_plot_05_heave_z_comparison.png`
   - Nueva: `nominal_10_8_plot_01_timeseries_cmd_vs_real.png` como figura de R5

5. **Heave:** argumento sobre el offset de altura (~0.32 m) se mantiene igual,
   solo se actualiza la referencia al ensayo.

---

### 5.2.4 — Lectura conjunta con la simulación

**Tipo:** Retoque leve.

**Cambios:**
- Actualizar números de amplitud: "±20° en roll y ±15° en pitch" → "±14.8° en
  roll y ±9.9° en pitch".
- Agregar una oración de cierre mencionando que R5 confirma que el patrón
  persiste a menor amplitud — no como "réplica exacta" sino como evidencia de
  que el comportamiento (retardo + atenuación) es consistente, aunque con
  parámetros que varían con la amplitud (lag crece, ganancia cae al bajar la
  consigna), lo cual es coherente con las no-linealidades del controlador
  interno del Go2.

**Frecuencia dominante de R4 (verificado):** el bag `strong_15_10` tiene
frecuencia dominante de **0.10 Hz** (período ~10 s) en ambos ejes, contra
0.15 Hz (período ~6.67 s) del histórico. Actualizar ese número en el texto.

**Lo que no cambia:** toda la argumentación cualitativa sim↔lab.

---

### Apéndice — Tabla de registros (`tab:appendix_rosbags`)

**Tipo:** Agregar 2 filas, actualizar 1.

| Referencia en el texto | Nombre base | Notas |
|---|---|---|
| Laboratorio R4 (principal) | `lab_real_20260424_120323_strong_15_10` | 24-04-2026; 59.63 s |
| Laboratorio R5 (control) | `lab_real_20260424_114454_robot_min` | 24-04-2026; 59.67 s |
| Laboratorio (ref. histórica) | `lab_real_20260320_125002_movimiento_full_v3` | 20-03-2026; 59.73 s |

La fila existente del histórico pasa de "Laboratorio (referencia)" a "Laboratorio
(ref. histórica)".

---

## Figuras: resumen completo

| Archivo fuente | Destino en `figures/images/` | Uso |
|---|---|---|
| `figures/lab_camera_fixed_raw.png` | `lab_camera_fixed_raw.png` | Nueva — 5.2.1 |
| `figures/strong_15_10_plot_02_api_fidelity.png` | `strong_15_10_plot_02_api_fidelity.png` | Reemplaza lab_plot_02 en 5.2.2 |
| `figures/strong_15_10_plot_01_timeseries_cmd_vs_real.png` | `strong_15_10_plot_01_timeseries_cmd_vs_real.png` | Reemplaza lab_plot_01 en 5.2.3 |
| `figures/strong_15_10_plot_03_lag_correlation.png` | `strong_15_10_plot_03_lag_correlation.png` | Reemplaza lab_plot_03 en 5.2.3 |
| `figures/strong_15_10_plot_05_heave_z_comparison.png` | `strong_15_10_plot_05_heave_z_comparison.png` | Reemplaza lab_plot_05 en 5.2.3 |
| `figures/nominal_10_8_plot_01_timeseries_cmd_vs_real.png` | `nominal_10_8_plot_01_timeseries_cmd_vs_real.png` | Nueva — 5.2.3 (R5) |

Figuras que **no entran al cuerpo** (disponibles para apéndice visual futuro):
`nominal_10_8_plot_02/03/04/05`, `strong_15_10_plot_04`, `historico_*`.

---

## Fuera de scope de esta integración

- Resumen / Abstract (placeholder vacío — pass separado)
- Conclusiones (sección vacía — pass separado)
- Trabajo futuro (sección vacía — incluirá limitación de ArUco+video)
- Subsubsección sobre dificultades sim→real (marcada con TODO)
