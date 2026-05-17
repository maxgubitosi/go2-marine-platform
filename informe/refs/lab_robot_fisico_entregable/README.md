# Entregable para informe - laboratorio con robot fisico

Este directorio junta material listo para portar al branch donde se edita
`informe/`. No modifica el informe en este branch.

## Decision tecnica

Con lo ya registrado alcanza para cerrar la parte cuantitativa de movimiento
del robot fisico, sin reconectar el Go2. El ensayo mas fuerte y limpio es:

- `rosbags/lab_real_20260424_120323_strong_15_10`
- Duracion efectiva: 59.66 s.
- Topics criticos presentes: `/marine_platform/debug_state`, `/api/sport/request`,
  `/api/sport/response`, `/sportmodestate`, `/lowstate`, `/utlidar/robot_odom`.
- Sin grabacion de video durante la corrida.

Este ensayo valida que el camino comando -> API no era la fuente principal del
error: la API sigue al comando con correlacion ~0.99995 y desfase medio ~5 ms.
La diferencia relevante aparece en la respuesta dinamica del cuerpo del robot:
retardo fisico de ~0.45 s en roll y ~0.95 s en pitch, con ganancia angular
aproximada de ~0.62 respecto del comando.

## Que usar en el informe

- Usar el ensayo `strong_15_10` como resultado principal de laboratorio fisico.
- Usar `nominal_10_8` como control mas suave que confirma el mismo patron.
- Mantener `historico_20260320` solo como antecedente, o reemplazarlo si el
  informe debe mostrar la corrida mas reciente y limpia.
- Incluir `lab_camera_fixed_raw.png` como evidencia visual del pipeline de
  camara fija. No presentarlo como validacion cuantitativa completa de ArUco.

## Contenido

- `memo_para_informe.md`: diagnostico, faltantes del PDF actual y texto base.
- `comandos_reproducibilidad.md`: comandos usados/recomendados para repetir.
- `data/resultados_laboratorio_robot_fisico.csv`: tabla numerica principal.
- `data/figuras_para_informe.csv`: mapa de figuras, fuentes y captions.
- `figures/`: figuras PNG listas para insertar en el informe.
- `rosbags/`: copia local de los bags/referencias usados por este entregable.

## Rosbags incluidos

- `rosbags/lab_real_20260424_120323_strong_15_10`: bag principal, incluye
  `.db3`, metadata y plots generados.
- `rosbags/lab_real_20260424_114454_robot_min`: bag de control, incluye
  `.db3`, metadata y plots generados.
- `rosbags/lab_real_20260320_125002_movimiento_full_v3`: referencia historica
  usada por el informe actual; en este workspace esta disponible con metadata,
  plots y reporte, pero no con el `.db3`.

Estos bags estan copiados dentro del entregable para que la carpeta pueda
trasladarse manualmente al branch del informe sin depender del directorio
`rosbags/` original.

## Limitacion importante

La evidencia cuantitativa fuerte corresponde a movimiento del robot fisico
medido por telemetria del robot y odometria lidar. El ensayo completo con
camara + ArUco + robot bajo carga no queda cerrado estadisticamente en este
material. Para el informe actual conviene declararlo como limitacion y trabajo
futuro, no forzarlo como resultado cuantitativo.
