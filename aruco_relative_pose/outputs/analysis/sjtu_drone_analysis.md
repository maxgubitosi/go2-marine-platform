# Análisis de resultados — SJTU Drone ArUco Pose Estimation

**Fecha:** 2026-02-27  
**Fuente de cámara:** SJTU Drone bottom camera (640×360, FOV=1.047, fx≈554.4)  
**Marcador:** ArUco DICT_6X6_250 ID 0, lado = 0.50 m  
**Plataforma:** Go2 sobre simulación marina con oleaje  
**Dron:** SJTU drone en hovering estático a z ≈ 3.0 m  
**Corrección aplicada:** `--world-init-x 0.40` (offset de spawn del Go2)

---

## 1. Resumen de las bolsas

| Parámetro | Bag 164654 | Bag 180434 |
|---|---|---|
| Muestras | 197 | 135 |
| Duración | 54.5 s | 55.6 s |
| Tasa de detección | ~3.6 Hz | ~2.4 Hz |
| Distancia GT cámara–marcador | 2.63 – 2.79 m (μ=2.71 m) | 2.63 – 2.79 m (μ=2.72 m) |
| Altitud del dron | 3.00 m (constante) | 3.00 m (constante) |
| Altura trunk Go2 | ~0.20 m | ~0.19 m |

En ambas bolsas el dron permanece inmóvil en hovering. La variabilidad proviene
exclusivamente del oleaje marino que mueve la plataforma del Go2.

---

## 2. Error absoluto de posición

Error entre la pose estimada por ArUco (`solvePnP`) y el ground truth calculado
a partir de odometría + IMU + pose del dron.

### 2.1 Estadísticas por eje (metros)

| Eje | Métrica | Bag 164654 | Bag 180434 |
|---|---|---|---|
| **ΔX** | media ± std | +0.044 ± 0.010 | +0.022 ± 0.018 |
| | |media|, max | 0.044, 0.072 | 0.024, 0.057 |
| | mediana, P95 | 0.044, 0.066 | 0.024, 0.051 |
| **ΔY** | media ± std | −0.020 ± 0.019 | +0.025 ± 0.011 |
| | |media|, max | 0.023, 0.054 | 0.025, 0.056 |
| | mediana, P95 | −0.021, 0.048 | 0.023, 0.045 |
| **ΔZ** | media ± std | +0.010 ± 0.048 | +0.002 ± 0.080 |
| | |media|, max | 0.035, 0.137 | 0.061, 0.181 |
| | mediana, P95 | 0.012, 0.106 | 0.007, 0.152 |

### 2.2 Error euclidiano (‖Δpos‖)

| Métrica | Bag 164654 | Bag 180434 |
|---|---|---|
| Media | 0.068 m | 0.078 m |
| Std | 0.023 m | 0.044 m |
| Mediana | 0.060 m | 0.063 m |
| P95 | 0.118 m | 0.154 m |
| Máximo | 0.151 m | 0.186 m |

### 2.3 Observaciones de posición

- **Z es el eje con mayor varianza** (std 4.8–8.0 cm). Es el eje de profundidad
  de la cámara, donde `solvePnP` tiene la mayor incertidumbre porque la
  profundidad se estima a partir de la escala aparente del marcador. A ~2.7 m,
  un error de 1 pixel se traduce en ~5 cm de profundidad.
- **X e Y tienen bias pequeños** (~2–4 cm) con baja dispersión (std 1–2 cm).
  El bias en X del bag 164654 (+4.4 cm) podría deberse a una pequeña
  desalineación o error residual en el spawn offset.
- El **bag 180434 tiene más dispersión** en Z (std 8.0 cm vs 4.8 cm),
  posiblemente por un oleaje más fuerte que causa mayor variación en la
  perspectiva del marcador.

---

## 3. Error relativo de posición

El error relativo se calcula como porcentaje de la distancia GT cámara–marcador,
lo que permite evaluar la precisión independientemente de la escala.

### 3.1 Error euclidiano relativo (‖Δpos‖ / distancia GT × 100%)

| Métrica | Bag 164654 | Bag 180434 |
|---|---|---|
| Media | **2.51%** | **2.86%** |
| Std | 0.86% | 1.62% |
| Mediana | 2.25% | 2.32% |
| P95 | ~4.3% | ~5.7% |
| Máximo | 5.69% | 7.06% |

### 3.2 Error por eje relativo a la distancia total

| Eje | Bag 164654 | Bag 180434 |
|---|---|---|
| |ΔX| / dist | 1.62% | 0.87% |
| |ΔY| / dist | 0.86% | 0.92% |
| |ΔZ| / dist | 1.29% | 2.25% |

### 3.3 Interpretación

- A una distancia de ~2.7 m, el sistema ArUco logra una **precisión de ~2.5–3%**
  en posición euclidiana. Esto equivale a ~7 cm de error medio.
- En el peor caso (P95), el error sube a ~5% (~12–15 cm), y los picos máximos
  no superan el 7% (~19 cm).
- **Estos valores son consistentes con la literatura** para `solvePnP` con un
  marcador de 0.50 m a 2.7 m: la relación lado/distancia es ~0.185, lo que da
  el marcador un tamaño de ~105 px en la imagen (suficiente pero no holgado).

---

## 4. Error de orientación

| Eje | Métrica | Bag 164654 | Bag 180434 |
|---|---|---|---|
| **ΔRoll** | media ± std | −0.75° ± 5.99° | −0.59° ± 11.14° |
| | |media|, max | 4.02°, 16.22° | 8.56°, 22.69° |
| | P95 | 12.55° | 20.23° |
| **ΔPitch** | media ± std | +0.05° ± 4.04° | +0.18° ± 6.76° |
| | |media|, max | 2.71°, 15.60° | 5.05°, 17.38° |
| | P95 | 9.05° | 12.75° |
| **ΔYaw** | media ± std | −0.01° ± 0.19° | +0.10° ± 0.21° |
| | |media|, max | 0.15°, 0.51° | 0.18°, 0.84° |
| | P95 | 0.35° | 0.45° |

### 4.1 Observaciones de orientación

- **Yaw es excelente**: error medio < 0.2° con std < 0.21°. Yaw se estima a
  partir de la rotación planar del marcador en la imagen, que es la más estable.
- **Roll y pitch tienen dispersión alta** (std 4–11°). Estos ejes dependen de
  la perspectiva 3D del marcador, que a ~2.7 m es muy sensible a ruido en la
  detección de esquinas. El oleaje amplifica esto al inclinar el marcador.
- **Los medias están cerca de 0** (bias < 1°), indicando que no hay un error
  sistemático en orientación — solo ruido.
- **Bag 180434 tiene el doble de dispersión en roll** (std 11° vs 6°),
  correlacionado con el mayor oleaje de esa sesión.

---

## 5. Análisis temporal — ¿Se acumula error?

Para determinar si hay drift (acumulación de error en el tiempo), se dividió
cada bolsa en 5 ventanas temporales y se midió la evolución del error.
También se realizó una regresión lineal del error euclidiano vs tiempo.

### 5.1 Bag 164654 — Error por ventana temporal

| Ventana | Tiempo | ‖Δpos‖ media | ‖Δpos‖ std | ΔX media | ΔY media | ΔZ media |
|---|---|---|---|---|---|---|
| 1 | 0–8 s | 0.095 m | 0.031 m | +0.050 | +0.001 | +0.024 |
| 2 | 8–16 s | 0.058 m | 0.014 m | +0.042 | −0.006 | +0.001 |
| 3 | 16–29 s | 0.055 m | 0.011 m | +0.043 | −0.020 | +0.017 |
| 4 | 29–41 s | 0.060 m | 0.008 m | +0.043 | −0.033 | +0.019 |
| 5 | 41–55 s | 0.073 m | 0.015 m | +0.042 | −0.045 | −0.013 |

### 5.2 Bag 180434 — Error por ventana temporal

| Ventana | Tiempo | ‖Δpos‖ media | ‖Δpos‖ std | ΔX media | ΔY media | ΔZ media |
|---|---|---|---|---|---|---|
| 1 | 0–8 s | 0.093 m | 0.029 m | +0.023 | +0.032 | −0.007 |
| 2 | 8–16 s | 0.106 m | 0.046 m | +0.028 | +0.024 | +0.008 |
| 3 | 17–31 s | 0.088 m | 0.045 m | +0.012 | +0.031 | −0.000 |
| 4 | 32–48 s | 0.047 m | 0.030 m | +0.025 | +0.021 | −0.000 |
| 5 | 48–56 s | 0.054 m | 0.034 m | +0.023 | +0.017 | +0.009 |

### 5.3 Regresión lineal (pendiente del error en el tiempo)

| Métrica | Bag 164654 | Bag 180434 |
|---|---|---|
| Pendiente ‖Δpos‖ | −0.25 mm/s | −1.17 mm/s |
| Pendiente ΔX | −0.10 mm/s | −0.01 mm/s |
| Pendiente ΔY | −1.04 mm/s | −0.25 mm/s |
| Pendiente ΔZ | −0.47 mm/s | −0.03 mm/s |

### 5.4 Interpretación — No hay drift

- Las pendientes son **negativas y muy pequeñas** (< 1.2 mm/s). Esto significa
  que el error NO crece con el tiempo — de hecho tiende levemente a disminuir.
- Esto es lo esperado: ArUco+`solvePnP` es un estimador **sin memoria**
  (frame-by-frame). No tiene estado interno que pueda acumular error como sí
  lo haría un filtro o una odometría visual.
- La variación entre ventanas se debe al oleaje: en momentos de mayor
  inclinación del marcador, el error sube temporalmente, y baja cuando la
  plataforma se estabiliza.
- La **ventana 1 de ambos bags tiene error más alto** (~9 cm), probablemente
  porque al inicio de la grabación la plataforma aún no se estabilizó.

---

## 6. Desvío estándar y distribución del error

### 6.1 Resumen de dispersión

| Magnitud | Bag 164654 | Bag 180434 |
|---|---|---|
| σ(‖Δpos‖) | 2.3 cm | 4.4 cm |
| σ(ΔX) | 1.0 cm | 1.8 cm |
| σ(ΔY) | 1.9 cm | 1.1 cm |
| σ(ΔZ) | 4.8 cm | 8.0 cm |
| σ(ΔRoll) | 5.99° | 11.14° |
| σ(ΔPitch) | 4.04° | 6.76° |
| σ(ΔYaw) | 0.19° | 0.21° |

### 6.2 Estabilidad del desvío por ventana temporal (roll std como proxy)

| Ventana | Bag 164654 σ(roll) | Bag 180434 σ(roll) |
|---|---|---|
| 1 | 10.1° | 11.3° |
| 2 | 4.1° | 13.7° |
| 3 | 2.9° | 9.8° |
| 4 | 2.6° | 8.0° |
| 5 | 6.0° | 9.0° |

El desvío **no crece en el tiempo** — fluctúa según la intensidad del oleaje
en cada intervalo. Bag 180434 tiene consistentemente más dispersión en roll,
confirmando que esa sesión tuvo oleaje más fuerte.

---

## 7. Conclusiones

1. **Precisión de posición: ~2.5% relativo** (7 cm a 2.7 m). Excelente para
   seguimiento visual en un entorno marino con oleaje.

2. **No hay acumulación de error** (drift). El estimador ArUco es sin memoria,
   así que cada frame es independiente. Las fluctuaciones son por oleaje, no
   por degradación temporal.

3. **El eje Z (profundidad) domina el error** con std de 5–8 cm. Esto es una
   limitación inherente de `solvePnP` a esta distancia y se podría mejorar con:
   - Marcador más grande
   - Mayor resolución de cámara
   - Fusión con sonar del dron

4. **Yaw es el ángulo más preciso** (< 0.2°). Roll y pitch tienen std de
   4–11° por la sensibilidad a perspectiva — aceptable como estimación gruesa
   pero no para control preciso de orientación.

5. **Bag 180434 tiene ~2x más ruido** que 164654 en orientación, pero error
   de posición similar. Esto sugiere que el oleaje afecta más la orientación
   estimada que la posición del centroide del marcador.

6. **El bias residual de ~2–4 cm en X/Y** es pequeño y constante. Podría
   reducirse refinando el valor de `world_init_x` o calibrando la posición
   exacta de hovering del dron.
