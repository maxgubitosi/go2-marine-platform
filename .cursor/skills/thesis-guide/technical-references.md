# Referencias técnicas en el informe (ROS, rutas y datos)

Guía para redactar `informe/main.tex` sin saturar el cuerpo con literales de código. Complementa [thesis-style](../thesis-style/SKILL.md) (prosa académica) y [SKILL.md](./SKILL.md) (LaTeX general).

## Objetivo

El lector de una tesis debe entender **qué se hizo y por qué**; los **identificadores exactos** (tópicos ROS 2, rutas de archivos, nombres de bags) sirven para **reproducibilidad** y deben aparecer donde se consultan con comodidad (tablas, apéndice, nota al pie), no repetidos en cada párrafo.

## Reglas de oro

1. **Primera mención de un conjunto de interfaces**: nombre en español + remisión a `Tabla~\ref{tab:...}` del informe (tablas de interfaces ROS) o, si es un detalle puntual, **una sola** `\footnote{...}` con el literal.
2. **Menciones siguientes**: solo el **nombre conceptual** (“la consigna postural”, “el tópico de depuración del simulador marino”, “la odometría del robot”), sin volver a pegar el path completo.
3. **Parámetros numéricos**: no en listas dentro del párrafo; ya están en tablas de metodología (p. ej. `tab:method_marine_params`) o en tablas dedicadas. En prosa: resumen en una frase + “según la Tabla X”.
4. **Archivos de configuración o calibración**: describir en prosa (“archivo de calibración del estéreo”, “configuración del publicador de imagen”); el path relativo al repositorio **una vez**, en tabla de apéndice o en nota al pie.
5. **Rosbags**: en el cuerpo, **campaña**, **fecha** y/o **etiqueta** (R1, baseline laboratorio); los **nombres de archivo** largos van al **Apéndice** (tabla de correspondencia), no en párrafos.
6. **Tipografía de literales** cuando deben aparecer en línea (cortos): `\texttt{nombre_paquete}`, modos `\texttt{sinusoidal}`. Para paths con `/`, preferir `\path{ruta/completa}` (proporciona `hyperref`) para permitir cortes de línea; en tablas y apéndice es preferible `\path` o columna monoespacio.
7. **No usar itálica** para tópicos ROS completos: no comunica que es un literal; use prosa + tabla o `\path`/`\texttt` breve.

## Ejemplos (evitar vs preferir)

| Evitar en el cuerpo | Preferir |
|---------------------|----------|
| Párrafo con cinco `\texttt{/topic/...}` seguidos | Una frase + “(Tabla~\ref{tab:ros_interfaces_sim})” o nombres en prosa ya definidos |
| Lista de parámetros `wave_frequency = 0{,}1 Hz, max_roll_deg = ...` en prosa | “los valores de la Tabla~\ref{tab:method_marine_params}” + tabla |
| Path completo del bag en tres secciones | “la corrida de referencia del 20 de marzo de 2026 (Apéndice~\ref{...})” |
| `stereo_camera/calibration/calibration_result.yaml` cada vez | Primera vez nota al pie o apéndice; luego “el archivo de calibración” |

## Dónde vive qué en este proyecto

- **Tablas de tópicos ROS** (`tab:ros_interfaces_sim`, `tab:ros_interfaces_lab`): lista canónica de nombres en prosa + tópico + tipo de mensaje.
- **Apéndice**: nombres de archivos de registros ROS 2, paths de datos versionados, opcionalmente comandos de reproducción.
- **Figuras**: captions descriptivos; si hace falta un literal, acortar y remitir a la tabla de interfaces.

## Mantenimiento

Al agregar un nodo o tópico nuevo al pipeline documentado: actualizar la tabla correspondiente en `main.tex` **antes** o **al mismo tiempo** que el párrafo metodológico, y usar siempre el mismo nombre en prosa para ese rol.
