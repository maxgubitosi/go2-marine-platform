# Memo para completar la parte de laboratorio con robot fisico

## Lectura del PDF actual

Se reviso `informe/main.pdf` sin modificarlo. La seccion de laboratorio ya
describe el objetivo correcto: comparar senal esperada, comando efectivo hacia
la API Sport Mode y estado real del robot. Tambien hay texto de resultados
basado en `lab_real_20260320_125002_movimiento_full_v3`.

Faltantes o puntos a actualizar en el branch del informe:

- El resumen todavia contiene un placeholder de analisis final.
- Hay una figura pendiente para la comparacion senal esperada / API / estado real.
- La seccion 5.2 puede fortalecerse con las corridas sin video del 2026-04-24.
- El apendice de datos deberia listar tambien los bags del 2026-04-24.
- La parte visual de ArUco debe quedar como evidencia de pipeline/montaje, no como metrica cerrada, salvo que se agregue otro ensayo especifico.

## Diagnostico de las fallas de laboratorio

La hipotesis de saturacion es consistente con lo observado. En las pruebas
problematicas se ejecutaban video, deteccion en tiempo real, recepcion de muchos
topics del robot y publicacion de poses en simultaneo. Esa combinacion puede
introducir jitter y colas de procesamiento, especialmente si ademas se graba
video o imagenes grandes.

Las corridas nuevas sin video no muestran un problema de fidelidad en el envio
de comandos:

- En `strong_15_10`, el comando esperado y `/api/sport/request` tienen
  correlacion 0.999957 en roll y 0.999953 en pitch.
- El desfase medio comando -> API es 5.21 ms, con maximo 10.08 ms.
- El robot mantiene telemetria de estado a ~497-500 Hz durante toda la corrida.

Por lo tanto, el problema no parece estar en la serializacion ni en el envio
basico de Euler a Sport Mode. Lo que si aparece es la dinamica real del robot:
la respuesta del cuerpo esta retardada y atenuada respecto del comando. En el
ensayo fuerte, el mejor lag fue ~0.45 s para roll y ~0.95 s para pitch, con
ganancia aproximada de 0.62 en ambos ejes.

Interpretacion para el informe: el sistema de comando se comporta de forma
coherente, pero la plataforma fisica no reproduce instantaneamente ni con
amplitud completa la consigna. La caida observada en pruebas cargadas debe
presentarse como incidente de integracion bajo carga, no como error demostrado
del mapeo comando -> API.

## Ensayos disponibles

Ensayo principal:

- Bag: `rosbags/lab_real_20260424_120323_strong_15_10`
- Inicio efectivo: 2026-04-24 12:04:03
- Duracion: 59.66 s
- Mensajes: 80313
- Comando: roll +-14.8 deg, pitch +-9.9 deg
- Estado real: roll -11.12 a 10.52 deg, pitch -5.36 a 6.63 deg
- Resultado: estable, sin video, todos los topics necesarios presentes

Ensayo de control:

- Bag: `rosbags/lab_real_20260424_114454_robot_min`
- Inicio efectivo: 2026-04-24 11:46:30
- Duracion: 59.67 s
- Mensajes: 80352
- Comando: roll +-9.87 deg, pitch +-7.93 deg
- Estado real: roll -5.76 a 5.16 deg, pitch -3.06 a 4.39 deg
- Resultado: estable, patron dinamico equivalente al ensayo fuerte

Referencia historica:

- Bag: `rosbags/lab_real_20260320_125002_movimiento_full_v3`
- El directorio versionado conserva plots y reporte, pero no conserva el DB3.
- Sirve como antecedente porque el informe actual ya usa sus metricas.

## Figuras recomendadas

- `figures/strong_15_10_plot_01_timeseries_cmd_vs_real.png`: figura principal de comando vs movimiento real.
- `figures/strong_15_10_plot_02_api_fidelity.png`: evidencia de fidelidad comando -> API.
- `figures/strong_15_10_plot_03_lag_correlation.png`: evidencia de retardo dinamico.
- `figures/strong_15_10_plot_05_heave_z_comparison.png`: aclaracion de offset de altura del cuerpo.
- `figures/lab_camera_fixed_raw.png`: evidencia visual del pipeline de camara fija.

## Texto base para insertar/adaptar

Para aislar la fuente de error observada en las pruebas integradas, se repitio
el ensayo de movimiento del robot fisico sin grabacion de video y registrando
solo los topics necesarios para la comparacion dinamica. El bag principal
(`lab_real_20260424_120323_strong_15_10`) contiene 59.66 s de datos, con
comandos Euler publicados hacia Sport Mode a 49.74 Hz y telemetria de estado
del robot a aproximadamente 497-500 Hz. La comparacion entre la referencia
interna (`/marine_platform/debug_state`) y el comando efectivo enviado a la API
(`/api/sport/request`, `api_id=1007`) muestra correlaciones de 0.999957 en roll
y 0.999953 en pitch, con un desfase medio de 5.21 ms. Esto indica que, en la
corrida aislada, el camino de comando no introduce un error significativo.

La comparacion con el estado real del robot muestra una respuesta fisica
coherente pero no ideal. Para una consigna aproximada de roll +-14.8 deg y
pitch +-9.9 deg, el cuerpo del robot alcanzo rangos de roll entre -11.12 y
10.52 deg, y pitch entre -5.36 y 6.63 deg. La correlacion maxima se obtuvo
aplicando un retardo de 0.45 s en roll y 0.95 s en pitch, con correlaciones de
0.954 y 0.984 respectivamente. Estos resultados son consistentes con una
plataforma fisica que filtra, retrasa y atenua la consigna angular, aun cuando
el comando sea transmitido correctamente.

En consecuencia, las caidas observadas durante las pruebas integradas con video
y deteccion en tiempo real no deben atribuirse directamente a un error de
conversion o publicacion de las poses. La evidencia disponible apunta a una
combinacion de carga computacional, asincronia de procesamiento y dinamica
propia del controlador del robot. Para el alcance actual del informe, la prueba
sin video cierra la validacion cuantitativa de movimiento fisico; la validacion
visual completa con ArUco queda documentada como limitacion y trabajo futuro.
