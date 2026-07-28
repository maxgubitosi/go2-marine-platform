# Media curada para la defensa oral

Material fotográfico y de video para la presentación web de la defensa.
Organizado en cuatro carpetas: `videos_sim/`, `videos_lab/`, `fotos_sim/`, `fotos_lab/`.

> **Nota técnica:** los `.mov` de iPhone están codificados en **HEVC** y las fotos `.heic`
> en HEIF. Antes de embeberlos en la web hay que convertirlos (H.264 MP4 / JPEG-PNG).
> Los `.mp4` extraídos de rosbags ya son compatibles con navegador.

## videos_lab/ — laboratorio con el Go2 real

- `01_setup_camara_fija_deteccion_aruco.mp4`
  - Fuente: `lab_bundle_for_informe/videos/lab_real_20260310_133022_aruco_debug.mp4`.
  - Vista de la cámara fija real con overlay de detección ArUco funcionando.
  - Calidad: útil y presentable; baja tasa de cuadros, aparece parte del operador/cableado.

- `02_go2_posturas_marinas_con_operador_34s.mov` (1080p vertical, 34 s, HEVC)
  - iPhone (ex `IMG_7302.MOV`). Operador en la mesa enviando comandos; el Go2 ejecuta
    posturas marinas (pitch/roll marcados). Cuenta la historia completa comando → respuesta.
  - **Cubre el hueco que declaraba el README anterior**: video externo del robot físico moviéndose.

- `03_go2_posturas_marinas_primer_plano_23s.mov` (1080p vertical, 23 s, HEVC)
  - iPhone (ex `IMG_7302(1).mov`). Primer plano del Go2 haciendo posturas, sin operador
    en cuadro la mayor parte del tiempo. **El mejor clip para mostrar el movimiento limpio.**

- `04_go2_posturas_marinas_vista_trasera_4k_24s.mov` (4K vertical, 24 s, HEVC)
  - iPhone (ex `IMG_7311.MOV`). Vista trasera/elevada del Go2 en posturas de pitch.
    Máxima resolución disponible; encuadre limpio sin personas.

- `05_go2_posturas_roll_con_operador_15s.mov` (1080p vertical, 15 s, HEVC)
  - iPhone (ex `IMG_7303.MOV`). Go2 con roll visible, operador al fondo.

- `06_go2_postura_pitch_contexto_4k_7s.mov` (4K vertical, 7 s, HEVC)
  - iPhone (ex `IMG_7299.MOV`). Clip corto de contexto: operador trabajando y Go2
    inclinado en primer plano. Bueno como plano de ambiente/transición.

- `07_aruco_montado_y_deteccion_en_pantalla_16s.mov` (1080p vertical 60 fps, 16 s, HEVC)
  - iPhone (ex `IMG_7347.MOV`). Empieza mostrando el ArUco montado en el lomo del Go2 y
    pasa a la pantalla del laptop con `rqt_image_view` + logs de roll/pitch en vivo.
  - **Único registro del pipeline visual corriendo en vivo en el laboratorio.** La toma de
    pantalla tiene moiré; puede convenir recortar solo el tramo inicial o usarlo pequeño.

- `08_setup_completo_camara_aruco_posturas_16s.mov` (1080p vertical 60 fps, 16 s, HEVC)
  - iPhone (ex `IMG_7390.MOV`). Setup experimental completo: trípode con cámara cenital,
    Go2 con ArUco haciendo posturas debajo. **El mejor clip para explicar el montaje del lab.**

## videos_sim/ — simulación en Gazebo

- `01_camara_fija_deteccion_aruco.mp4`
  - Fuente: rosbag `rosbags/marine_sim_20260410_155332_report_v2_ref`, topic `/aruco/debug_image`.
  - Cámara fija en simulación con overlay de detección. Claro para explicar detección.

- `02_dron_camara_inferior_deteccion_aruco.mp4`
  - Fuente: rosbag `rosbags/sjtu_drone_sim_20260410_160419_report_v2_r2`, topic `/aruco/debug_image`.
  - Detección desde la cámara inferior del dron. No se ve el dron: acompañar con
    `fotos_sim/03_contexto_dron_go2_aruco.png`.

- `03_camara_fija_raw.mp4` / `04_dron_camara_inferior_raw.mp4`
  - Mismos rosbags, topics raw (`/fixed_camera/camera/image_raw`, `/drone/bottom/image_raw`).
  - Uso secundario: comparar entrada vs salida del detector.

## fotos_lab/

- `01_setup_montaje.jpeg` — montaje físico del laboratorio (foto original curada).
- `02_go2_aruco_contexto.png` — Go2 real con marcador, contexto.
- `03_frame_camara_fija_raw.png` — frame raw de la cámara fija real.
- `04_go2_aruco_tripode_camara_a.heic` / `05_..._b.heic` — Go2 con ArUco montado frente al
  trípode de la cámara; las mejores fotos del setup experimental (fondo con auto del lab).
- `06_vista_cenital_go2_aruco.png` — vista cenital del Go2 + ArUco desde la cámara del
  trípode, alta resolución. Ideal para explicar la geometría cámara–marcador.
- `07_operador_trabajando_con_go2_a.heic` / `08_..._b.heic` — operador en el laptop con el
  Go2 en primer plano. Foto de "trabajo real en el lab" (aparece una sola persona).
- `09_go2_reposo_contexto.heic` — Go2 en reposo, contexto de laboratorio.
- `10_panorama_laboratorio.heic` — plano amplio del laboratorio (poca luz).

## fotos_sim/

- `01_frame_camara_fija_raw.png` — frame raw de cámara fija en simulación.
- `02_frame_dron_raw.png` — frame raw de cámara inferior del dron.
- `03_contexto_dron_go2_aruco.png` — dron sobre el Go2 en Gazebo (contexto).
- `04_contexto_go2_aruco.png` — Go2 con marcador en Gazebo (contexto).

## Material adicional disponible fuera de esta carpeta

- `informe/figures/` — todos los diagramas y gráficos de resultados del informe
  (pipeline, cinemática, series temporales, histogramas de error, etc.).
- `informe/figures/images/jack-1705/` — fotos de WhatsApp del 17/05 (sin curar).

## Material revisado y descartado

- `docs/media/Screencast from 15-02-26 18:36:30.webm`: baja resolución; redundante.
- `src/unitree-go2-ros2/.docs/go2_teleop.mp4`: demo genérica de teleoperación, no es del trabajo.
- `marine_robot_dataset/datasets/*/frames`: técnicamente útiles pero visualmente pobres.
- `/frontvideostream` de rosbags reales: no se pudo deserializar de forma confiable.

## Huecos pendientes (pedidos al equipo)

1. **Foto de los dos autores con el robot** — para portada o cierre. Lo disponible
   (`07`/`08_operador_trabajando_con_go2`) muestra una sola persona.
2. Video externo del Go2 **con heave** (oscilación vertical) si existe; los clips actuales
   muestran principalmente roll/pitch.
3. Si se repite algún ensayo: mismo movimiento filmado en horizontal (16:9) rendiría mejor
   en pantalla de proyector que los verticales de iPhone.
