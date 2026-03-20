# Análisis completo de movimiento

Bag: `lab_real_20260320_125002_movimiento_full_v3`
Duración: 59.73 s
Mensajes: 159020

## 1) Disponibilidad de señales

### Señal esperada (comando)
- `/marine_platform/debug_state`: 120 muestras (~2.00 Hz)

### Señal de comando efectivo hacia robot
- `/api/sport/request`: 3126 mensajes totales
  - `api_id=1007` (Euler): 2968 (~49.70 Hz)

### Señales de estado real del robot (principales)
- `/sportmodestate`: 29671 (~498.02 Hz)
- `/lowstate`: 29788 (~499.77 Hz)
- `/utlidar/robot_odom`: 14461 (~242.73 Hz)

Conclusión de adquisición: este bag **sí** captura el estado real principal de forma continua.

---

## 2) Movimiento esperado (lo que manda tu nodo)

Fuente: `/marine_platform/debug_state`

- Roll:
  - rango: -19.637° a 19.173°
  - desviación estándar: 9.892°
  - frecuencia dominante: 0.1500 Hz (periodo ~6.67 s)

- Pitch:
  - rango: -14.719° a 14.212°
  - desviación estándar: 7.897°
  - frecuencia dominante: 0.1500 Hz (periodo ~6.67 s)

- Heave (z esperado):
  - `debug_state.z`: 0.0 en todas las muestras

---

## 3) Fidelidad del camino de comando (nodo → API robot)

Comparación entre `/marine_platform/debug_state` y `/api/sport/request` (api_id=1007):

- pares comparados: 120
- desfase temporal medio: 4.98 ms (máximo 10.18 ms)
- correlación:
  - `x` API vs `roll(rad)` esperado: 0.999887
  - `y` API vs `pitch(rad)` esperado: 0.999909
- RMSE:
  - `x-roll(rad)`: 0.00261 rad
  - `y-pitch(rad)`: 0.00188 rad
- `z` API:
  - mínimo = 0.0, máximo = 0.0

Conclusión: el comando enviado al robot coincide prácticamente perfecto con lo esperado y sin componente `z`.

---

## 4) Movimiento real observado (estado principal)

### Rango angular real (IMU body)
Fuente: `/sportmodestate` (idéntico en `/lowstate`)

- roll real: -14.388° a 16.190°
- pitch real: -11.532° a 11.455°

### Correlación instantánea (lag 0)
Interpolando estado real al tiempo de `/marine_platform/debug_state`:

- `debug_roll` vs `roll_real`:
  - sport: 0.9115
  - low: 0.9122
  - odom: 0.9112

- `debug_pitch` vs `pitch_real`:
  - sport: 0.8131
  - low: 0.8143
  - odom: 0.8124

### Correlación con búsqueda de lag (±3 s)

- Roll (comando → real):
  - mejor lag ≈ 0.35 s
  - corr ≈ 0.9695 (sport/low/odom consistentes)

- Pitch (comando → real):
  - mejor lag ≈ 0.60 s
  - corr ≈ 0.9680 (sport/low/odom consistentes)

Interpretación: la respuesta real del cuerpo del robot es fuertemente coherente con los comandos, con retardo dinámico estable del orden de 0.35–0.60 s.

---

## 5) Heave / Z real vs esperado

### Señal esperada y señal enviada
- `z` esperado (`/marine_platform/debug_state.z`):
  - min = 0.0, max = 0.0, media = 0.0
- `z` enviado al robot (`/api/sport/request` api_id=1007, campo JSON `z`):
  - min = 0.0, max = 0.0, media = 0.0
  - RMSE esperado vs enviado: 0.0

### Señal real de heave
- `z` real (estado principal, `/sportmodestate.position[2]`):
  - rango: 0.31542 m a 0.32777 m
  - media: 0.31951 m
  - desviación estándar: 0.00154 m
- `z` real (odometría, `/utlidar/robot_odom.pose.pose.position.z`):
  - rango: 0.31542 m a 0.32777 m
  - media: 0.31951 m
  - desviación estándar: 0.00154 m

### ¿Ese z es del tronco o del pie?
- En `/utlidar/robot_odom`, `header.frame_id = odom` y `child_frame_id = base_link`.
  - Por definición, ese `pose.position.z` corresponde al `base_link` (tronco/cuerpo), no a un pie.
- En `/sportmodestate`, además de `position[2]` existen `foot_position_body` (posición de pies en frame cuerpo).
  - Los `z` de pie en frame cuerpo están alrededor de -0.31 m (aprox):
    - FL: media -0.3113 m
    - FR: media -0.3135 m
    - RL: media -0.3185 m
    - RR: media -0.3145 m

Chequeo de consistencia (aprox.):
- Si `z_base ≈ 0.3195 m` y `z_pie_en_cuerpo ≈ -0.31 m`, entonces `z_pie_mundo ≈ z_base + z_pie_en_cuerpo ≈ 0`.
- Resultado observado: `z_pie_mundo` aproximado queda cerca de 0 m (medias entre 0.001 y 0.008 m), consistente con pies apoyados en el piso mientras el tronco queda elevado.

### Diferencia heave esperado vs real
- RMSE (`debug_z` vs `sport_z` interpolado): 0.31949 m
- RMSE (`debug_z` vs `odom_z` interpolado): 0.31949 m
- sesgo medio (`sport_z - debug_z`): +0.31948 m
- sesgo medio (`odom_z - debug_z`): +0.31948 m

Interpretación: no hay comando dinámico de heave (z=0), y el valor real z representa la altura absoluta del cuerpo en su frame de estado/odometría (~0.32 m). Por eso la diferencia aparece como offset casi constante y no como error dinámico oscilatorio.

---

## 6) Gait / trote

Fuente: `/sportmodestate.gait_type`

- conteos:
  - `gait_type=9`: 29006 muestras
  - `gait_type=0`: 665 muestras

Lectura práctica: durante casi todo el tramo, el robot permanece en un único modo de marcha dominante (`9`), con apariciones breves de `0`.

---

## 7) Cómo se obtuvo cada dato (metodología detallada)

### Fuentes de dato (qué es real y qué es esperado)
1. Señal esperada (referencia del experimento):
   - tópico: `/marine_platform/debug_state`
   - tipo: `geometry_msgs/Vector3`
   - interpretación:
     - `x`: roll esperado [deg]
     - `y`: pitch esperado [deg]
     - `z`: heave esperado (en este ensayo queda en 0)

2. Señal enviada al robot (comando efectivo):
   - tópico: `/api/sport/request`
   - tipo: `unitree_api/Request`
   - filtro: `api_id = 1007` (Euler)
   - extracción: parseo JSON del campo `parameter` → `{x, y, z}`
   - unidades:
     - `x`, `y` en rad
     - `z` adimensional/según API (aquí siempre 0)

3. Estado real principal del robot:
   - `/sportmodestate` (`unitree_go/SportModeState`):
     - actitud real: `imu_state.rpy` [rad]
     - heave real: `position[2]` [m]
     - modo de marcha: `gait_type`
   - `/lowstate` (`unitree_go/LowState`):
     - actitud real alternativa: `imu_state.rpy` [rad]
   - `/utlidar/robot_odom` (`nav_msgs/Odometry`):
     - orientación real por cuaternión → conversión a rpy
     - heave real: `pose.pose.position.z` [m]

### Cómo se compararon señales con distinta frecuencia
- Las tasas no son iguales (`debug` ~2 Hz vs `sport/low` ~500 Hz vs `odom` ~243 Hz).
- Para comparar:
  - comando→API: se usa vecino temporal más cercano (nearest timestamp).
  - comando→estado real: se interpola señal real al tiempo de `debug_state`.

### Métricas calculadas
1. Fidelidad de comando (`debug` vs `api`):
   - correlación de Pearson entre pares sincronizados.
   - RMSE entre `roll/pitch` esperado (convertido a rad) y `x/y` enviados.
   - estadística de latencia temporal por diferencia de timestamps emparejados.

2. Movimiento real vs esperado (`debug` vs `sport/low/odom`):
   - correlación a lag 0 tras interpolación.
   - barrido de lag en ventana ±3 s para hallar máximo de correlación en valor absoluto.

3. Heave/z:
   - esperado: `debug_state.z`.
   - enviado: `parameter.z` en API 1007.
   - real: `sportmodestate.position[2]` y `robot_odom.pose.position.z`.
   - diferencia: RMSE y sesgo medio sobre timeline de `debug_state` (vía interpolación).

### Nota de interpretación de z/heave
- En esta corrida, `z` de comando es cero constante.
- El `z` real está en torno a 0.32 m porque representa altura absoluta del tronco (`base_link`) en su frame, no “z del pie” ni “delta heave” respecto a cero de comando.
- Para comparar dinámicas puras de heave, conviene usar señales centradas (restar media) o definir explícitamente un baseline de altura de equilibrio.

---

## 8) Conclusión global

1. La captura `movimiento_full_v3` resolvió el problema de telemetría faltante.
2. El camino de comando está validado con alta fidelidad (correlaciones ~0.9999 y latencia ~5 ms).
3. El movimiento real del cuerpo (sport/low/odom) sigue claramente al comando con alta correlación y lag físico moderado (~0.35–0.60 s).
4. La comparación real vs esperado queda cerrada con señales principales, ya sin depender de proxy lidar.
