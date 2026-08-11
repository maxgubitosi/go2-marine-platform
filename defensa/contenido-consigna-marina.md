# Bloque de modelado marino · contenido y script

Estado: **láminas armadas**. Corresponden a `090-modelo-marino-reducido.html` y
`100-consigna-sinusoidal-y-parametros-del-ensayo.html`.

Reemplazan a las dos versiones anteriores, que estaban en el orden equivocado
(la consigna antes que el modelo) y con demasiado texto.

Orden: el del informe. Primero qué es el movimiento marino y qué simplificación
adoptamos, después la consigna concreta y qué llega al robot.

---

## Aclaración previa

Los tres grados de libertad que retenemos son **heave, roll y pitch**. Yaw se
descarta junto con surge y sway, y eso ya está dicho en la lámina 3. Cuidado con
decir "yaw" en la defensa.

El plano de la lámina 1 es la superficie **del agua**, linealizada bajo la
plataforma. No es la cubierta. La cubierta adopta su altura y sus dos pendientes,
y κ dice qué fracción de la pendiente adopta realmente.

---

## Lámina 1 · El oleaje, reducido a un plano

Encabezado: III · Metodología: modelo marino

Bajada, en tres viñetas:

- La superficie del agua bajo la plataforma, como un **plano**
- Un plano: **una altura y dos pendientes**
- Los tres grados de libertad que retuvimos

En la lámina: la ecuación `reduced_state` a la izquierda, y a la derecha sus tres
filas leídas en el mismo orden (altura → heave, pendiente babor-estribor → roll,
pendiente proa-popa → pitch), más la nota de κ.

### Script · unos 2:10

> El movimiento real de una cubierta en el mar depende de muchas cosas a la vez.
> El oleaje no es regular: llegan componentes de distintas frecuencias y
> direcciones. Y el casco tiene inercia, amortiguamiento hidrodinámico y fuerzas
> de restauración, así que responde distinto según su geometría y su tamaño
> respecto de la longitud de onda. Resolver todo eso es un problema de dinámica
> marina completo, y no es lo que necesitábamos.
>
> Nuestra simplificación es geométrica. Miramos la superficie del agua justo
> debajo de la plataforma y la tratamos como un plano. Y un plano queda definido
> por tres números: una altura y dos pendientes. Esos tres números son exactamente
> los tres grados de libertad que retuvimos.
>
> La altura respecto del nivel medio del mar es el heave: la cubierta flota, si el
> agua sube, la cubierta sube. La pendiente de babor a estribor la inclina de
> costado, y eso es el roll. La pendiente de proa a popa la cabecea, y eso es el
> pitch.
>
> *[a la ecuación]* Es lo que dice esta ecuación. Zeta es la altura de la
> superficie del agua: un campo, un número para cada punto del mar y cada
> instante. Evaluada bajo la plataforma da el heave, que es la primera fila. Y sus
> dos derivadas parciales son las pendientes, que dan roll y pitch. El signo menos
> es convención de ejes.
>
> Los coeficientes kappa dicen cuánto acompaña la cubierta esa pendiente. Kappa
> igual a uno sería una balsa perfecta, que se pone paralela a la ola. Un casco
> real tiene eslora e inercia, así que promedia y se inclina menos.
>
> Hay dos aproximaciones acá. Una es quedarnos sólo con altura y pendiente en un
> punto y descartar la curvatura, que vale mientras la longitud de onda sea grande
> frente al barco. La otra es que prescribimos el movimiento desde la superficie
> en vez de resolverlo desde las fuerzas. No estamos simulando un casco.

**Corte si venís apretado:** el último párrafo se comprime a "Es una aproximación
local, y es cinemática: prescribimos el movimiento en vez de resolver las fuerzas."

### Si preguntan

*¿La consigna sale de esta ecuación?* Sí, evaluada sobre una ola regular: la
altura y las dos pendientes salen todas sinusoides. Lo que hicimos fue dejar
libres la relación de frecuencias y el desfase entre ejes en vez de atarlos a una
única onda plana. Va en la dirección correcta, porque un mar real es una
superposición de componentes que llegan de distintas direcciones, y ahí heave y
pendientes no quedan en fase fija.

Ese argumento **no está escrito así en el informe**. Están las dos piezas por
separado (la ec. 10 que liga pendiente con k, y la 11 que describe el mar
irregular como superposición) pero no las junta. Es una interpretación del propio
material, no una afirmación nueva.

---

## Lámina 2 · Una sinusoide por componente

Encabezado: III · Metodología: consigna marina

Bajada: *Un nodo de ROS 2 sintetiza la consigna y la publica a 20 Hz.*

En la lámina: a la izquierda las tres ecuaciones `commands` y la tabla de la
consigna; a la derecha el suavizado `ema` y la tabla de lo que el filtro cuesta;
al pie los dos destinos.

Las dos tablas van por eje y con la misma forma, para que se lean como un par:

| Consigna | amplitud | frecuencia | desfase |     | Tras el filtro | al robot | de lo pedido |
|---|---|---|---|---|---|---|---|
| roll | ±15,0° | ω | — |  | roll | ±12,8° | 85 % |
| pitch | ±10,0° | ω | π/3 |  | pitch | ±8,5° | 85 % |
| heave | ±0,100 m | 1,5 ω | — |  | heave | ±0,074 m | 74 % |

Así el desacople se ve de un vistazo: roll y pitch comparten ω, heave no.

### Script · unos 2:15

> Con eso definido, lo nuestro es directo: una sinusoide por componente. Un nodo
> de ROS 2 las sintetiza y publica la consigna a 20 hertz.
>
> Roll y pitch comparten frecuencia, la base, 0,1 hertz: un ciclo cada diez
> segundos. Se diferencian en la amplitud, 15 grados contra 10, y en un desfase
> fijo de sesenta grados que le pusimos a pitch. Heave sí va a otra frecuencia,
> una vez y media la base, con 10 centímetros de amplitud.
>
> El desacople es deliberado. Si las tres llegaran juntas a sus extremos, el
> marcador recorrería siempre la misma familia de poses. Corriéndolas, el
> estimador ve inclinaciones y distancias mucho más variadas. Y va en la dirección
> correcta, porque un mar real tampoco es una sola onda.
>
> Esa consigna no se aplica directo. Antes pasa por un suavizado exponencial: cada
> valor que publicamos es un noventa y cinco por ciento del anterior más un cinco
> por ciento del objetivo nuevo. Es un pasa-bajos de primer orden, con una
> constante de tiempo de casi un segundo.
>
> Lo usamos porque no mandamos una fuerza, mandamos una postura que el robot tiene
> que realizar moviendo doce articulaciones. Un salto en la consigna se traduce en
> un tirón: en Gazebo da transiciones poco plausibles, y en el robot real el
> controlador puede leer esa perturbación como que lo están empujando y romper a
> trotar.
>
> Y cuesta amplitud. Roll y pitch llegan al ochenta y cinco por ciento de lo
> pedido, y heave al setenta y cuatro, porque va a más frecuencia y el filtro es
> justamente un pasa-bajos. Aclaro que la referencia que registramos es la
> suavizada, así que esa atenuación no ensucia el error medido: lo que cambia es
> la excitación que efectivamente aplicamos.
>
> Y eso es lo que sale hacia el robot. En simulación publicamos la pose completa
> del torso. En el laboratorio mandamos sólo actitud, roll y pitch, porque la API
> de alto nivel del Go2 no expone altura. Ahí la cubierta se inclina pero no sube
> ni baja.

**Corte si venís apretado:** en el párrafo del costo, quedate con la aclaración de
que la referencia registrada es la suavizada y soltá los dos porcentajes.

### Si preguntan

*¿Por qué no mandan heave al robot real?* Porque el pipeline real usa
`SportClient.Euler(roll, pitch, yaw)`, que comanda actitud del torso. El parámetro
de heave se conserva como referencia pero no se comanda dinámicamente. Está
declarado en el script de lanzamiento del laboratorio.

---

## Notación

Los desacoples van como **ρ** y no como κ. En el informe κ aparece con dos
sentidos: κ_φ y κ_θ son los coeficientes de pendiente de la lámina 1, y κ_p y κ_h
los desacoples temporales de la lámina 2. Como κ_θ y κ_p se refieren los dos a
pitch, proyectadas seguidas se prestan a confusión. La leyenda bajo la ecuación lo
declara: *ρ es la κ del informe*.

---

## Tres cosas del script que no están escritas en ninguna lámina

Son deliberadas: se dicen, no se muestran.

1. Que el balance de fuerzas se retiene sólo como marco conceptual y no simulamos
   el casco. La ecuación de dinámica marina salió de la lámina 1.
2. Que la referencia que registramos es la suavizada, así que la atenuación
   cambia la excitación aplicada y no el error medido.
3. Que en el laboratorio la cubierta se inclina pero no sube ni baja.

Las tres siguen en el script de arriba. Si alguna vez hace falta que queden a la
vista, la 1 vuelve como franja apagada al pie y la 2 como nota bajo la tabla del
filtro.

---

## Pendientes

1. **El filtro del laboratorio no es el mismo.** En simulación es el EMA con
   α = 0,95 a 20 Hz. En el laboratorio el nodo corre con `motion_model` en su
   default `second_order` (ζ = 0,82, f_n = 0,9 Hz) más límites de velocidad
   angular (45 °/s en roll, 35 °/s en pitch) a 50 Hz, porque el EMA de primer
   orden no acota la velocidad y el robot rompía a trotar. Ver commit
   `5ad01f7 "no trota"`. **El informe sólo documenta el exponencial.** Sin decidir:
   (a) no mencionarlo acá y dejarlo para las láminas de laboratorio, o (b) una
   línea al pie sin énfasis.

2. **La figura de las tres series temporales quedó afuera.** Entraba sólo
   achicando las dos tablas por debajo de lo legible. Si se la quiere, va como
   lámina de backup, regenerada desde
   `informe/scripts/plot_marine_sinusoidal_reference.py`.

3. **El cuerpo de las ecuaciones de estas dos láminas está subido a mano**
   (`.modelo .eq.hero`, `.consigna .eq.hero`). Cuando la fase A suba los topes
   tipográficos de todo el deck, revisar si esas reglas siguen haciendo falta.
