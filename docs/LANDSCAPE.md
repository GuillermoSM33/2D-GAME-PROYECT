# Paisaje, edificios y objetos del mapa

Los diez niveles usan nueve temas (1-1 y 1-2 comparten atardecer). El paisaje y
los objetos son pixel art nativo, PNG RGBA de 8 bits sin entrelazado. Los dibujos
procedurales se conservan en `tools/` y usan solamente la biblioteca estándar.

| Tema | Niveles | Ambiente |
| --- | --- | --- |
| `atardecer` | 1-1, 1-2 | Desierto, mesetas y cielo naranja |
| `cementerio` | 1-3 | Panteón morado, creciente y niebla |
| `noche` | 1-4 | Desierto azul, luna llena y niebla |
| `pueblo_fantasma` | 1-5 | Pueblo en ruinas, cielo rojo |
| `afueras` | 2-1 | Amanecer, viviendas y gasolinera |
| `centro` | 2-2 | Torres, azoteas y esmog |
| `vias` | 2-3 | Patio ferroviario al atardecer |
| `ciudad_noche` | 2-4 | Edificios oscuros, ventanas y niebla |
| `base_militar` | 2-5 | Retén, hangares y focos de alarma |

## Escala y cámara

El mundo mide 1920 × 1080 unidades (`VIEW_WIDTH`, `VIEW_HEIGHT`), con cuatro
unidades por píxel de arte. Se dibuja en una textura y se presenta a 0.5×:
la ventana lógica de 960 × 540 muestra **480 × 270 píxeles de arte**, dos
píxeles de ventana por píxel de arte, sin suavizado.

La cámara mantiene a la protagonista en el centro: **960 unidades de mundo a
cada lado**, con el mismo espacio para emboscadas por delante y por detrás.
La línea del suelo está en la fila 240 del arte (y = 480 de ventana); el HUD
usa los primeros 135 píxeles de ventana. La referencia de escala es la sheriff:
56 píxeles de arte equivalen aproximadamente a 1.70 m. Las puertas miden unos
60 píxeles; los postes y árboles pasan sobre su cabeza y caben completos en la vista.

## Materiales y profundidad

La luz llega desde arriba a la izquierda. Cada material conserva detalles
propios: juntas, veta y clavos en la madera; bloques, grietas y mortero en la
piedra; costuras y pliegues en sacos y lona; bordes, remaches y óxido en el metal;
costillas y espinas en los cactus; ramas, corteza y masas de hojas en la vegetación.
Evitar superficies plásticas, rectángulos sin estructura y ruido uniforme.

Los personajes se leen contra las capas cercanas oscuras. El contraste disminuye
con la distancia: edificios y decorados usan los tonos `prop_shadow`, `prop_light`
y `haze` de `ThemeDef`. Los originales se dibujan en colores diurnos y
`assets_texture_graded` los adapta al tema, conservando el detalle entre tonos.
Las casas reciben además `HOUSE_HAZE` de neblina atmosférica. Los píxeles de luces
propias se marcan con alfa 254 (`Canvas.light`): el juego los convierte en opacos
y conserva su color. No se usa ese alfa para transparencia normal.

Los objetos interactivos tienen algo más de contraste y sus estados conservan
las mismas siluetas, pivotes y dimensiones de colisión. La iluminación local
de faroles, linterna y explosiones se aplica al primer plano.

Los objetos separados dejan seis píxeles de arte de suelo libre entre sus
huellas. El camión de suministros reserva su anchura completa; la decoración
procedural respeta también las fachadas y todo el exterior del tren, incluso
después de usarlos. Los decorados grandes se separan entre sí y entre tramos.
Las trampas conservan además su espacio para aterrizar. Las capturas
`THE_MIRACLE_CAPTURE_GROUP=layout` permiten revisar suministros, descansos y
retenes en las distribuciones reales de los diez niveles.

El foco del outpost permanece apagado hasta registrar sus suministros. Al
encenderse usa el mismo haz direccional que la linterna: nace en la lente,
apunta al camino hacia la izquierda, pierde intensidad con la distancia y
respeta los obstáculos. El sprite conserva solo la lente encendida; el haz
se calcula en la escena. El foco y la linterna pueden iluminar simultáneamente.

## Capas

`tools/landscape_kit.py:LAYERS` comparte geometría entre el generador y el
validador. Coincide con `BACKGROUND_LAYERS` en `src/game/themes.c`; `--verify`
comprueba los recursos incrustados contra la tabla del juego.

| Archivo | Tamaño nativo | Filas del arte | Paralaje | Repite |
| --- | --- | --- | --- | --- |
| `sky.png` | 480 × 180 | 0–179, última fila extendida al suelo | 0 | No |
| `far.png` | 720 × 72 | 104–175 | 0.15 | Sí |
| `hills_far.png` | 720 × 70 | 140–209 | 0.35 | Sí |
| `hills_near.png` | 720 × 64 | 176–239 | 0.6 | Sí |
| `ground.png` | 480 × 30 | 240–269 | 1 | Sí |
| `fog.png` (opcional) | 480 × 48 | 216–263 | 1 + deriva | Sí |

La niebla tiene un solo color, dos niveles de alfa entre 30 y 100 y deriva
de 24 unidades de mundo por segundo. Las capas recortadas usan alfa 0 fuera de
su silueta. El validador informa costuras y exceso de píxeles sueltos para revisión
visual; no modifica el arte. En la banda del HUD la luminancia recomendada es
≤ 55; detrás de los cuerpos (184–239), ≤ 62, con acentos de luz de hasta 120.

## Decorados

`tools/make_props.py` genera todas las hojas de `sprites/props/` salvo casas.
Cada variante ocupa un cuadro, se apoya en su última fila y se centra en él.
`src/game/props.c` es la tabla que usa el juego.

| Hoja | Cuadro | Variantes |
| --- | --- | --- |
| cactus | 44 × 100 | 4 |
| rock | 48 × 24 | 3 |
| fence | 72 × 40 | 2 |
| dead_tree | 100 × 150 | 2 |
| grass | 24 × 14 | 4 |
| wagon_wheel | 44 × 44 | 2 |
| skull | 34 × 18 | 2 |
| tombstone | 28 × 40 | 4 |
| sign | 36 × 62 | 2 |
| shrub | 40 × 36 | 4 |
| telegraph | 40 × 176 | 2 |
| hydrant | 14 × 24 | 1 |
| streetlight | 40 × 150 | 2 |
| trash | 26 × 32 | 2 |
| cone | 16 × 24 | 1 |
| tires | 40 × 34 | 1 |
| sandbags | 66 × 28 | 1 |
| jersey | 104 × 27 | 1 |
| pole | 44 × 160 | 1 |
| litter | 20 × 6 | 3 |
| signal | 24 × 110 | 1 |
| drums | 48 × 34 | 1 |
| fallen_pole | 150 × 26 | 1 |
| traffic_light | 60 × 140 | 2 |

Cada tramo de 960 unidades tiene cuatro sitios posibles para objetos grandes,
elegidos por los pesos del tema y separados según su ancho, más 2–6 matas de
pasto (basura en los temas urbanos). La semilla y el camino determinan la distribución.

## Edificios

`tools/make_houses.py` genera `sprites/props/houses.png`: **21 cuadros de
256 × 192**, hoja de **5376 × 192**. No mezclar los recortes con la hoja histórica
de 80 × 64. Todos comparten suelo y escala de puertas.

| Cuadros | Diseño |
| --- | --- |
| 0–4 | Saloon, cabaña, granero, casa derrumbada, tanque de agua |
| 5–9 | Iglesia, sheriff, herrería, establo, banco |
| 10–12 | Almacén, casa de adobe, silo caído |
| 13–17 | Espectacular, gasolinera, tiendas, departamentos, bodega |
| 18–20 | Hangar, torre de vigilancia, radar |

Los edificios pasan a 0.8 del movimiento del camino. Hay un sitio cada 1200
unidades con variación de posición de hasta 176: los cuadros no se superponen.
Los temas urbanos eligen sus edificios mediante `ThemeDef.houses`.

## Objetos interactivos

`tools/refine_terrain.py` reconstruye los objetos desde las funciones de
`make_terrain.py`, `city_terrain.py` y `make_city.py`, y agrega detalles según su
material. Siempre empieza desde el dibujo fuente: ejecutarlo varias veces no
acumula texturas. Los módulos `terrain_architecture_detail.py`,
`terrain_vehicle_detail.py`, `terrain_object_detail.py` y `terrain_water_detail.py`
dibujan la construcción, el volumen y los acabados de cada familia. Conservan
cuadros de animación, roturas, huecos de paso, luces, posiciones y colisiones.
Incluye barricadas, cajas, barriles, muros,
fachadas, fogatas, trampas, carros, autos, tren y estructuras militares.

El agua conserva una superficie compartida entre `river` y `river_front`:
reflejos largos y espuma siguen la corriente, con lecho y piedras visibles en
las orillas. El fuego tiene lenguas curvas que cambian de forma entre los
cuatro cuadros y una base de aceite y brasa; sus medidas de daño no cambian.

Los árboles y arbustos que ocultan trampas se comparten con los señuelos
inofensivos del camino; deben seguir siendo visualmente indistinguibles.

## Regenerar y comprobar

Los árboles secos tienen dos ramificaciones continuas dibujadas con nodos compartidos;
su corteza gris parda usa luces mates, sin el borde dorado anterior. Las cuatro plantas de
`shrub` se distinguen como arbusto, yuca, nopal y mata seca. Las 25 hojas de props conservan
sus dimensiones, apoyos y luces con alfa 254. La torre y el radar de `houses` incluyen
carcasas, lentes, articulaciones y costillas que siguen su volumen.

`city_fronts` contiene ocho estructuras de 288 × 216, primero las ocho pintadas por
los merodeadores y después sus ocho versiones sin pintar. A tienda, comisaría, viviendas
y retén se añaden clínica, taller, subestación y radio central. Sus variantes se distribuyen
en los cinco temas urbanos. `CITY_FRONT_VARIANT` conserva el identificador 10 del tren de
las partidas antiguas y reserva su hueco al traducir la hoja.

Las fachadas del oeste ocupan 288 × 200; las urbanas, 288 × 216. Las plantillas
se amplían alrededor de las jambas, conservando la abertura central de 44 × 64.
Las casas del fondo se excluyen cuando su recorrido de paralaje podría acercarlas
a una fachada o al tren, incluso después de destruir su bloqueo; no aparecen ni
desaparecen al mover la cámara. Los coches decorativos respetan toda esa anchura.

El tren laboratorio de 2-3 ocupa 5432 × 192 y sale de `tools/train_art.py`:
trece vagones Vantrell, una unidad de maquinaria sin cabina y la locomotora de
control orientada a la derecha (capó largo, cabina, morro, piloto, depósito y
bogies de tres ejes). **Cada unidad se dibuja a su tamaño final; nada se
reescala**, porque un reescalado no uniforme deforma el píxel. Tiene margen en
ambos extremos y cabe en una textura de menos de 8192 píxeles. El mundo se
amplió a 160 tramos; se conserva el origen de la protagonista en 48000.

Con E se entra por la puerta lateral del vagón 01. El exterior se sustituye por
`train_interior`: quince habitaciones de 360 × 270 con un mismo sistema de
materiales (paneles esmaltados distintos entre sí, zócalo de acero, chapa
estriada, escurrimientos y manchas pequeñas, nunca ruido uniforme) y una luz
calculada desde los dos tubos del techo, con bandas por *dithering*; pantallas,
líquidos y lámparas brillan solos y tiñen su entorno. Las salas: descontaminación,
prototipos, cultivos MRC-2, cirugía, análisis, contención, criogenia, archivo
móvil, dormitorio, comedor, enfermería, armería (de Halcón Seguridad), radio,
máquinas y control. El mobiliario está en `tools/train_furnishing.py`: la puerta
corrediza con su riel y su hoja, la cabina de descontaminación (vidrio curvo,
regaderas, panel), el tablero de herramientas con siluetas pintadas, la cristalería
del vagón 05, la cápsula del vagón 07 estrellada desde dentro y las pantallas con
carcasa, barrido y reflejo. Los fuelles entre vagones unen las baldosas y llevan
el número de cada vagón. Dentro, la cámara se limita a los extremos del tren
(`train_camera`): nunca se ve el vacío detrás de las paredes finales.

Los accesorios corresponden al uso de cada sala: bandejas, suministros médicos,
canaletas, válvulas, avisos y pertenencias de la tripulación dan señales de lo que
ocurrió sin agrandar el mobiliario. Las cortinas clínicas tienen riel y soportes
visibles y delimitan su camilla. Cinco extractores giran dentro de marcos fijos;
`TRAIN_VENT_FANS` comparte sus posiciones entre arte y render. Las bahías de las
cajas utilizables siguen libres, incluidas las de la pista del contenedor.

Los puntos de interacción están dibujados donde el juego los coloca (constantes
`TRAIN_*_ART` de `src/game/train.h`, comprobadas por `tests/test_scenery_assets.py`):
puerta en x 40 del vagón 01, los ganchos de los trajes a ambos lados de x 218 y
el casillero abierto de la tableta en x 311; cunas de las piezas en x 259 de los
vagones 02, 07 y 14 (máquinas), terminal (con su base para la tableta) en x 234 y
escotilla en x 320 del vagón 15. Los trajes colgados y la tableta son
`terrain/train_gear` (2 × 32 × 80) y el juego los dibuja mientras siguen ahí. La
escotilla tiene un piloto que el juego enciende en rojo intermitente y pasa a verde
al abrirse. Dentro no se dibujan casas, aves ni meteorología exterior. Se puede
retroceder hasta la entrada; la salida requiere eliminar a los treinta infectados,
recoger las tres piezas del tren y leer el Archivo 4 en la terminal, que solo lo
abre con la tableta del vagón 01 conectada.

**Tableta, trajes y aire tóxico.** La tableta (E en el casillero del vagón 01)
es la llave de la terminal y el mapa del tren: M abre y cierra el mapa sobre el
nivel pausado (los quince vagones, dónde está ella, piezas, terminal, infectados
que quedan, aire tóxico y trajes). Con E en los ganchos se pone o se quita un
traje aislante; sin él, el aire de los tanques rotos de cultivos (03) y criogenia
(07) le quita un 5 % de la salud por segundo, sin armadura ni empuje. Al salir
del tren lo deja. Con el traje puesto se dibuja con él en todas sus animaciones
(`characters/<id>/suit/`, `tools/make_hazmat.py`).
La sheriff lleva el overol amarillo holgado con visor azul: el traje oculta
su anatomía, cabello y ropa, de modo que no se distingue quién va dentro.
El SWAT usa visor naranja y conserva, encima del traje, placas y protecciones
oscuras, guantes reforzados y una botella de aire.
Las armas mantienen sus colores y su dibujo original.

**Interfaz del tren.** La lista de objetivos vive dentro de la tableta, junto al
mapa, y deja despejado el escenario durante la partida. E recoge la tableta y
abre su consulta una vez. M abre/cierra el mapa y P el inventario; cambiar entre
ambos o cerrarlos con Esc conserva el nivel pausado hasta volver a jugar. El mapa
presenta los quince vagones con planos de pixel art propios, la posición actual,
los infectados, gases, piezas y la lista de objetivos con destino y estado.
El inventario tiene un estuche de campo ilustrado y muestra personaje, equipo,
armas, munición y provisiones. Ambos salen de `tools/make_field_ui.py`.
Solo la pieza recién recogida aparece brevemente en la columna derecha; nada se
encima con el HUD (lo comprueba `hud_verify_layout`). Los avisos inferiores llevan
E solo cuando actúa; si falta algo, dicen qué en rojo («SALIDA CERRADA · FALTAN 2 PIEZAS»).
Cada pieza tiene halo, columna de luz y un marcador; un marcador igual señala
la puerta, la terminal o la escotilla cuando son el siguiente paso.

La terminal entrega la carta de porte del expediente y señala Cerro Gris,
búnker 2. Los ocho módulos del prototipo se guardan como bits del expediente,
compartidos entre personajes y conservados al reintentar:

| Módulo | Ubicación |
| --- | --- |
| Cámara de plasma | 2-3, vagón 2 |
| Bobina criogénica | 2-3, vagón 7 |
| Celda de potencia | 2-3, sala de máquinas |
| Regulador y lente | 2-4 |
| Inyector, aislante y núcleo | 2-5 |

E recupera un módulo y el expediente muestra el total. Esta entrega incorpora
la búsqueda y el registro de las ocho piezas; el ensamblaje del arma queda
como continuación de la historia. El esquema de guardado 11 conserva el vagón,
los enemigos, los módulos, la terminal, la tableta, el traje y el ciclo de gases.
Admite los esquemas anteriores; un punto de control de 2-3 anterior al esquema
11 reinicia ese intento porque usaba la distribución anterior, conservando
el progreso previo y el expediente.
`THE_MIRACLE_CAPTURE_GROUP=train` revisa acceso, quince habitaciones, piezas,
trajes de ambos personajes, inventario, mapa, escotilla, terminal y salida.

### Cruzar un coche (N)

Los pasos, cuadros, tiempos y distancias del cruce están en `src/game/car_pass.h`
(`car_plan`), y `tools/make_car_passage.py` los lee de ahí: cambiarlos en un lado es
cambiarlos en los dos. Ella camina hasta la puerta trasera (la delantera si va a la
izquierda) y toma la manija con el brazo casi extendido (`CAR_REACH`). Tira de ella y
la puerta se abre. Si tiene seguro, levanta el antebrazo y rompe el cristal de un
puñetazo; las astillas caen y quedan en la calle bajo la puerta (`terrain/car_glass`).
Luego mete la mano por el hueco y levanta el botón del seguro. Sube un pie al estribo,
se agacha hacia la puerta y entra; dentro va sentada en el piso con una rodilla arriba.
Al cerrarse la puerta ya no se le ve (el vidrio, entero o roto, la tapa) y se empuja
hacia la otra. Empuja la otra puerta, saca una pierna,
asoma la cabeza, se pone de pie y sigue caminando mientras la puerta se cierra. La
camioneta tiene una sola puerta: entra y sale por ella. Ella nunca retrocede en el
camino.

Cada hoja del personaje tiene 55 celdas de 81 × 80 en **dos filas**: arriba lo que de
ella queda fuera del coche (se dibuja encima de él) y abajo lo que queda dentro (debajo
de la carrocería y las puertas). Así el coche solo la tapa cuando de verdad está
dentro. Cada cuadro tiene todo su cuerpo en una sola de las dos filas, nunca un brazo o
una pierna sueltos en la otra. Ninguna pose gira el sprite entero: el torso se inclina desde la cintura, la
cabeza va derecha sobre el cuello, las caderas no giran y lo que cuelga del cinturón
sigue colgando; piernas y brazos van de sus articulaciones a pies y manos. Cada mano
se pone por ángulo y alcance desde su hombro, nunca a menos de `MIN_REACH` del brazo
estirado, y el codo dobla siempre hacia su lado: ningún brazo se pliega sobre sí mismo
ni se cruza sobre el pecho; sus brazos miden lo mismo que en todas sus hojas. Dentro
del coche nada de ella pasa de su piso (`FLOOR`; debajo se ve la calle entre las ruedas)
ni asoma por encima del techo: se sienta en el piso, casi derecha, sin hundir la cabeza
en los hombros.

Los vehículos son algo más grandes que en la vida real junto a ella, porque a tamaño
real parecían de su altura: autos, patrulla y todoterreno a 1.2 y el camión militar a
1.6 (`CAR_SCALE`, `TRUCK_SCALE` en `tools/make_city.py`). Cada uno se dibuja nativo a su
escala; ningún PNG se reescala. `tests/player_render.c` lo comprueba con `car_plan` y las
hojas incrustadas, en los tres modelos, los dos sentidos, abriendo y rompiendo.

Las capas `terrain/car_passage{,_damaged}{,_front}` tienen 15 estados por modelo:
cristal entero, roto el trasero o roto el delantero, por puertas cerradas, trasera
entreabierta o abierta, delantera entreabierta o abierta. El frontal es la
carrocería sin los huecos de las puertas abiertas ni el cristal roto, con las hojas
abiertas encima. Puerta, cristal y alarma usan `Piece.car_flags`; los impactos siguen
usando su contador independiente. Las capturas `THE_MIRACLE_CAPTURE_GROUP=props` y
`THE_MIRACLE_CAPTURE_GROUP=cars` permiten revisar el arte en el render del juego.

La [revisión visual](SCENERY_REVIEW.md) incluye comparativas y secuencias capturadas.

```bash
python3 tools/rebuild_scenery.py
python3 tools/check_landscape.py assets/backgrounds/*
python3 tools/make_car_passage.py --verify
python3 tools/make_field_ui.py --verify
python3 tests/test_scenery_assets.py
./build.sh
./build/bin/TheMiracle --capturas build/scenery-captures
```

Se pueden ejecutar por separado `make_landscape.py`, `make_props.py`,
`make_houses.py` y `refine_terrain.py`, todos con un directorio de assets opcional.
Los puntos de entrada históricos `make_city.py` y `make_terrain.py` usan los
generadores nuevos para no volver a exportar las hojas antiguas.

`--verify` valida todos los tamaños; las capturas `50_escenario_*` muestran los
diez temas con la protagonista y objetos a ambos lados. Revisar también faroles,
linterna, explosiones, trampas y estados rotos antes de aprobar arte nuevo.
Las capturas `51_outpost_apagado`, `51_outpost_encendido` y
`51_outpost_y_linterna` revisan el foco y ambos haces juntos.

Para agregar un tema, crear sus capas y parámetros en `landscape_west.py` o
`landscape_city.py`, registrar el `ThemeDef` y asignarlo en `stages.c`. El
laboratorio de las cintas se coloca en el valle entre las colinas lejanas y
cercanas, con paralaje 0.45 (`app/story_render.c`).
