# Marine Platform Simulator v2 — Movimiento Fluido

**Fecha:** 2026-03-05  
**Archivo:** `src/go2_tools/go2_tools/marine_platform_simulator.py`

## Problema

El movimiento del Go2 era "trabado" (jerky/steppy). Causas identificadas:

1. **Sender thread a 10 Hz** — el Go2 recibía una posición nueva cada 100ms y "saltaba" a ella
2. **Dos hilos desincronizados** — el timer ROS2 calculaba targets a 10 Hz, el sender los leía a 10 Hz, pero sin sincronización temporal → posiciones mantenidas por duraciones irregulares
3. **Smoothing por frame (EMA)** — `smooth = 0.3 * smooth + 0.7 * target` depende de la tasa de ejecución, no del tiempo real → comportamiento inconsistente si la tasa varía
4. **Sin interpolación** — el sender leía un target discreto del timer → el robot ve una "escalera" de posiciones

## Solución

### Arquitectura v2

```
┌─────────────────────────────────────────────┐
│           ROS2 Timer (2 Hz)                 │
│  • Lee debug values bajo lock               │
│  • Publica /marine_platform/debug_state      │
│  • Logea roll/pitch/hz/rpc_ms               │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│        Sender Thread (~50 Hz)               │
│  1. Genera onda via time.time() (continuo)  │
│  2. Aplica startup ramp                     │
│  3. Smoothing temporal (tau=0.15s)          │
│  4. Clampea a límites hardware              │
│  5. Envía Euler(roll, pitch, 0) al Go2      │
│  6. Actualiza debug values bajo lock        │
│  7. Sleep adaptativo                        │
└─────────────────────────────────────────────┘
```

### Cambios clave

| Aspecto | v1 (trabado) | v2 (fluido) |
|---------|-------------|-------------|
| Sender rate | 10 Hz | **50 Hz** (configurable) |
| Generación de onda | Timer ROS2 → shared var → sender | **Sender calcula directo** con `time.time()` |
| Smoothing | EMA por frame (`sf * old + (1-sf) * new`) | **Temporal** (`1 - exp(-dt/tau)`) rate-independent |
| Timer ROS2 (real) | Calcula onda + actualiza targets | **Solo debug/logging** a 2 Hz |
| Desincronización | Dos loops a 10 Hz leyendo/escribiendo | **Un solo loop** genera + envía |
| Parámetro smoothing | `smoothing_factor` (0-1, frame-dependent) | `smoothing_tau` (segundos, rate-independent) |

### Smoothing temporal explicado

```python
alpha = 1 - exp(-dt / tau)
smooth += alpha * (target - smooth)
```

- `tau = 0.15s` → alcanza 95% del target en ~0.45s (3×tau)
- `tau = 0.05s` → más reactivo, 95% en ~0.15s
- `tau = 0.30s` → más suave, 95% en ~0.90s
- **Rate-independent**: produce el mismo resultado a 50 Hz, 30 Hz, o cualquier tasa variable

### Nuevos parámetros

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| `smoothing_tau` | `0.15` | Constante de tiempo en segundos para smoothing exponencial |
| `sender_rate_hz` | `50.0` | Frecuencia target del sender thread en Hz |

### Parámetro eliminado

- `smoothing_factor` → reemplazado por `smoothing_tau`

### Monitoreo de rendimiento

El sender thread trackea:
- **FPS efectivos**: reportado en logs cada 2s via el debug timer
- **Latencia RPC**: si `Euler()` tarda > 30ms promedio, logea un warning
- Ambos valores visibles en los logs: `sender=48Hz rpc=12ms`

## Modo sim

Sin cambios funcionales significativos. El timer de simulación usa `_apply_temporal_smoothing()` (misma fórmula exponencial) en vez del EMA antiguo. El modo sim no usa sender thread.

## Verificación

```bash
# Lanzar en robot real
./run_marine_real.sh

# En otra terminal, verificar debug topic
ros2 topic hz /marine_platform/debug_state

# Verificar que modo sim sigue funcionando
ros2 run go2_tools marine_platform_simulator --ros-args -p mode:=sim
```

## Tuning

### v2.1 — "Que baile" (2026-03-05)

Parámetros ajustados para movimiento más dramático y natural:

| Parámetro | v2.0 | v2.1 (baile) | Efecto |
|-----------|------|-------------|--------|
| `real_max_roll_deg` | 15° | **20°** | Más balanceo lateral |
| `real_max_pitch_deg` | 10° | **15°** | Más cabeceo |
| `real_max_heave_m` | 0.02m | **0.04m** | Más sube/baja (2x) |
| `wave_frequency` | 0.1 Hz | **0.15 Hz** | Ola 50% más rápida (periodo 6.7s) |
| `wave_pattern` | sinusoidal | **irregular** | 3 sinusoides superpuestas = más orgánico |
| `smoothing_tau` | 0.15s | **0.08s** | Más reactivo (95% en 0.24s vs 0.45s) |

El patrón `irregular` superpone múltiples sinusoides con distintas frecuencias
y fases, generando un movimiento que no se repite exactamente igual cada ciclo.
Esto, combinado con tau más bajo y ángulos más grandes, produce el efecto de
"baile" natural.

### Tau (τ) — Constante de tiempo

Tau controla qué tan rápido el robot sigue al target calculado por la onda:

```
alpha = 1 - exp(-dt / tau)
smooth += alpha * (target - smooth)
```

- **tau chico** (0.05s): sigue instantáneamente, puede verse "nervioso"
- **tau medio** (0.08s): reactivo pero suave (actual)
- **tau grande** (0.30s): muy suave pero con lag notable

Regla: **95% del target en 3×τ**. Con tau=0.08, alcanza 95% en 0.24s.

Es rate-independent: produce el mismo resultado a cualquier frecuencia de ejecución.

Si el movimiento sigue trabado:
- Bajar `smoothing_tau` a `0.05` (más reactivo, menos lag)
- Subir `sender_rate_hz` a `100` (si la RPC lo permite)

Si el movimiento es nervioso/tembloroso:
- Subir `smoothing_tau` a `0.25` o `0.30`
- Bajar `sender_rate_hz` a `30`

```bash
# Ejemplo: más reactivo
./run_marine_real.sh  # editar parámetros en el script o:
ros2 run go2_tools marine_platform_simulator --ros-args \
    -p mode:=real \
    -p sender_rate_hz:=100.0 \
    -p smoothing_tau:=0.05 \
    -p network_interface:=enp2s0
```
