# THE MIRACLE

(Antes Vaquera 2D; el repo y la carpeta del proyecto conservan el nombre viejo.)

La historia, sus nombres y las fases están en `docs/LORE.md`: respétalo. El arte de las
cinemáticas sale de `tools/make_cinematics.py`. **Sin voces:** la
historia se cuenta solo con cinemáticas, ruidos y texto.

Juego 2D en C11 + SDL2/SDL2_ttf con motor propio (`src/engine`), lógica en `src/game`,
pruebas en `tests/`. Los recursos se incrustan al compilar con `tools/embed_assets.py`.
Documentación en `README.md` y `docs/`; dónde va cada recurso y cómo se nombra:
`docs/ASSETS.md` (respétalo al agregar sprites, fondos o sonidos).

## Directriz principal: Windows y Linux

**El juego debe compilar y funcionar siempre en Windows y en Linux.** Todo cambio (código,
`Makefile`, `build.sh`, `tools/`, recursos, docs) tiene que funcionar en ambos.

- Nada de APIs, rutas ni comandos propios de un solo sistema sin cubrir el otro; lo que
  dependa del sistema va por SDL.
- Scripts en POSIX `sh`/`bash` y con finales de línea **LF** (con CRLF dejan de funcionar).
- No agregar dependencias que no existan tanto en apt (Ubuntu/Debian) como en MSYS2 UCRT64.
- Después de un cambio, corre `./build.sh` en la máquina actual y avisa qué falta probar en
  el otro sistema.

## Dependencias

SDL2, SDL2_ttf y **SDL2_mixer** (audio).
Si al bajar cambios `build.sh` dice que falta SDL2_mixer:

- **Linux:** `sudo apt install libsdl2-mixer-dev`
- **Windows (MSYS2 UCRT64):** `pacman -S mingw-w64-ucrt-x86_64-SDL2_mixer`

Solo para `tools/crush_sfx.py` (grabar/convertir sonidos, no para compilar): **ffmpeg**
(`sudo apt install ffmpeg` / `pacman -S mingw-w64-ucrt-x86_64-ffmpeg`).

## Compilar

- **Linux:** `./build.sh` (requisitos en `README.md`).
- **Windows:** MSYS2 en `C:\msys64`, entorno UCRT64. Desde una terminal MSYS2 UCRT64:
  `./build.sh`. Desde PowerShell:
  `$env:MSYSTEM="UCRT64"; $env:CHERE_INVOKING="1"; C:\msys64\usr\bin\bash.exe --login -c "./build.sh"`
- En ambos sistemas sirven `make`, `make test`, `make run` y `make watch`.
- **Zip para jugadores:** `./dist.sh` pide la versión y deja el zip del sistema actual en
  `dist/linux/` o `dist/windows/`.

## Cambios de diseño: primero la cuadrícula de píxeles

Para cualquier cambio de diseño a partir de una referencia del usuario, primero
`python3 tools/pixel_grid.py referencia.png --ours hoja.png:ancho:cuadro` (necesita
Pillow): encuentra cuánto mide un píxel de la imagen, recorta sus figuras a tamaño
nativo y las cuadricula con coordenadas, tabla de tramos, medidas por fila y paleta,
junto a nuestras hojas y a la misma escala. Es la herramienta que pidió el usuario
(2026-11-24). De la referencia se toman proporciones, piezas y materiales; **el dibujo
es siempre propio**: nunca copiar sus píxeles ni sus personajes. Después, abrir las
imágenes y compararlas: los números solos no validan un diseño.

## Arte de la vaquera (la sheriff Dolores Vega)

El usuario pidió el rework visual el 2026-11-12 para acompañar los escenarios y objetos:
materiales terrosos, luz superior izquierda y revólver de ocho balas, recarga de 1.2 s
como el rifle del SWAT. `tools/detail_cowgirl.py` aplica el acabado a todas las hojas
al final del generador. La última referencia del usuario **reemplaza el azul por vino**:
chaquetita/chalequito corto y abierto encima del corsé, con solapas y mangas color vino
tomadas de su foto. El corsé conserva el gris pizarra/carbón; el pantalón lleva **grises**
(dos de luz y dos de sombra, `TONES` en `tools/cowgirl_legs.py`) con pliegues y franja
iluminada, sin azul. Cuero marrón oscuro y vino en el pañuelo.
El usuario pidió **recuperar el rojo anterior al rework**: conservar exactamente la paleta
original del pelo (`#6b333a`, `#902004`, `#d03305`), sin recolorearla ni añadir reflejos
rosados. Los extremos del encaje se esconden bajo las solapas para que no queden puntos
blancos sobre la chamarra. Lleva dos botones de latón discretos, distintos de la placa.
El busto tiene un aumento sutil, con volumen cubierto por el corsé, igual en todas las
poses. En SIT, el cinturón se deriva del plano claro de la cara original, y las solapas y
botones (`JACKET_BUTTON`) se dibujan de frente.
La ropa sigue sobria; no añadirle bordes blancos, ribetes luminosos ni halo.
Debe distinguirse del fondo de 1-1 mediante contraste cromático y materiales separados, con
volumen por planos suaves y contorno oscuro. Encaje gris marfil y latón envejecido,
sin blancos ni amarillos intensos en la ropa.
Tiene **un solo cuerpo, en tres cuartos hacia la derecha**, en todas las poses de pie,
quieta o en movimiento: torso, cinturón, funda y pañuelo salen de los mapas de
`tools/cowgirl_torso.py` (`TORSO`, `LOWER`, `HOLSTER`), y caderas y piernas de
`tools/cowgirl_legs.py`. Cámbialo ahí, nunca en una sola hoja. Solo el banco (SIT) conserva
el cuerpo frontal de `dress` (`TORSO_FRONT`, `BELT_FRONT` en `tools/rework_cowgirl.py`). La
meta es una silueta de reloj de arena: hombros y cadera de ancho parecido, cintura marcada y
sin escalón entre cinturón y pierna; la curva va en tramos de dos filas para que no salga en
escalera. Cabeza, sombrero, cara y pelo son **siempre sus píxeles**, trasladados enteros: el
usuario rechazó la cara deformada; no girarlos ni proyectarlos.
Sus brazos se dibujan aparte, con un solo modelo de brazo y guante (`tools/cowgirl_arm.py`)
y **un solo dibujo de pistola**, `assets/sprites/characters/cowgirl/weapons/pistol.png`,
generado por `tools/make_revolver.py`, para las dos manos; las poses están en `walk_arms`,
`jump_arms`, `rest_arms` y `stand_arms`. El brazo izquierdo del dibujo es el **cercano**: se
compone delante del cuerpo. El otro, el del arma, es el lejano: sale de detrás de su solapa
(`make_melee.behind`). En la linterna los nombres viejos llaman «far» al cercano.
`behind_arm` cambia por tela lo que un brazo deja como resto suelto (placa, botón, pelo
en el hueco del codo) y `finish_cowgirl.no_specks` quita los que queden: **ningún píxel de
color suelto**.
La referencia de movimiento (2026-11-23) es `build/prototipo_sheriff_v2/objetivo`: `walk`,
`stand`, `apuntar`, `shoot_v2`, `shoot_cadera` y `reload`. De ella salen **solo medidas y
poses, nunca píxeles**. `tools/cowgirl_pose.py` guarda la tabla de las diez claves de
`walk.gif` medidas en su cuadrícula nativa, y `python3 tools/measure_cowgirl_pixels.py`
vuelve a medir referencia y sheriff (tabla, grosores y cuadrículas en
`build/sheriff_medidas`). Los números no validan el movimiento: abrir las imágenes y
compararlas con la cuadrícula antes de dar algo por bueno.
**Carrera:** 20 cuadros (las diez claves y la pose media entre cada dos) a 24 por segundo,
`PLAYER_SHERIFF_WALK_*`; arranca en el 2 y los pies caen en el 0 y el 10 (ahí suenan los
pasos). El pie apoyado retrocede lo que ella avanza, así que no resbala; al correr las
piernas van `PLAYER_RUN_SPEED_MULT` más rápido. El torso casi no gira: se mueven la pelvis,
las piernas y los antebrazos. La pelvis gira (`YAW`), el cinturón se inclina, la hebilla se
oculta y en las claves 5 a 8 **se ven los glúteos con la raya entre ellos** (`SEAT`, el
borde oscuro del muslo cercano con luz a ambos lados). El pecho cubierto sube o baja un
píxel como mucho y un paso tarde (`CHEST`); nada más. El usuario vio la versión anterior
exagerada. Las piernas nunca adelgazan: en ningún cuadro el muslo baja de 6.6 px ni la rodilla
o la pantorrilla de 5.2, con contorno (la referencia baja a 6, 5 y 4);
`tests/cowgirl_walk_art.py` lo mide.
**Cinturón fino:** una fila de cuero entre dos de contorno y hebilla de 3 px, sin cartuchos
(el usuario lo vio exagerado). La funda es compacta, en el costado, con un píxel de
seguimiento como mucho; el pañuelo cuelga detrás y no tapa las piernas. La segunda funda de
las duales (`near_holster`) cuelga **por fuera de la cadera cercana y nunca se dibuja sobre
ella**: el usuario la veía siempre pintada encima del cinturón y del glúteo al caminar.
**De correr a quieta:** `stand` tiene 4 cuadros respirando y 2 de frenado
(`PLAYER_STAND_BREATHS`, `PLAYER_STAND_SETTLES`, `player_stand_frame`); mismo cuerpo,
cinturón y suelas en la misma fila, para que no cambie de personaje al parar. `legs` son sus
piernas de carrera, en 20 cuadros, a la altura de pie, para las acciones al caminar.
Al disparar, el retroceso levanta el brazo y echa los hombros atrás, y vuelve
(`DRAWN`, `SWAY` en `tools/make_flashlight.py`); `player_light_kick` sigue esa lente. La
linterna resuelve el brazo desde el hombro móvil a la mano estable; su lente al caminar va
cuatro píxeles detrás de la de apuntar quieta y `lighting.c` conserva ese origen.
El pelo tiene más volumen pegado a la nuca y la espalda, con mechones que se
estrechan hacia la cadera; no dibujar una masa ondulante ni una franja naranja.
Conservar también la proporción discreta de reflejos de la paleta anterior. El mechón largo
(`mane`) es una sola pieza continua: la raíz va con la cabeza y la punta con un píxel de
retraso. En SIT, el cabello largo cae delante de ambas orejas y las cubre en todos los
cuadros, incluidos respiración, recarga y cabeceo (`tools/make_sit.py`).
Regenera todas sus hojas con `python3 tools/rebuild_cowgirl.py` (y luego
`python3 tools/make_hazmat.py`) y revísalas ampliadas antes de reportarlas;
`tools/preview_cowgirl.py` las junta. Las herramientas de revisión necesitan Pillow; la
regeneración usa solo la biblioteca estándar.

Es la sheriff del pueblo: lleva una **placa** (estrella de latón) sobre el corsé, definida
una sola vez en `TORSO` (`1`, `2`, `3`) para todas sus poses de pie y, de frente, en
`BADGE`/`sheriff_badge` (`tools/rework_cowgirl.py`) para el banco. Un brazo por delante la
tapa; si solo asomara un resto, se ve tela.

`DUALS_FROM_ANY_LEVEL` en `src/config.h` está en 0; ponlo en 1 solo para probar las duales desde el nivel 1.
Las duales son **dos revólveres de ocho balas con contadores independientes**:
`Shot.rounds` es el principal y `other_rounds` el segundo. Recargar rellena solo el
tambor seleccionado (`reload_other`); R encadena ambos incompletos, 1.2 s cada uno.
Q conserva el principal y `StagePlay.dual_rounds` guarda el segundo al enfundarlo;
nunca rellenar munición al cambiar. El HUD muestra ambas cuentas y el esquema de
guardado 8 conserva también el objetivo y la secuencia de recarga. F con duales
consume una bala de cada arma y requiere que ambas tengan munición.
`reload_dual` y `reload_dual_b` tienen 48 cuadros por mano (24 al recargar una
sola arma o la primera, 24 para la segunda de una pareja). `Shot.reload_pair`
conserva el cambio de mano: la primera retiene el cuadro 18 y la segunda empieza
en el 24, con ambas poses idénticas. Enfunda el revólver libre, recarga el otro,
enfunda el cargado y saca el segundo. Mantener 1.2 s por tambor. Nunca usar
`shot_piston_frame` ni las capas de disparo/rebote/linterna sobre la recarga:
su reloj es `shot_reload_progress`, también quieta y mientras recibe daño.
`tests/player_render.c` comprueba los píxeles reales durante ambas recargas,
incluido vaciar el arma tras explotar un barril y quedarse sobre fuego.
Al pulsar de nuevo el disparo durante una recarga doble, se cancela solo la parte
pendiente si algún revólver tiene balas. Mantener el clic espera; con ambos vacíos
no se cancela. `begin_piston_turn` elige una mano con balas si la siguiente está
vacía y reinicia el gesto; cada disparo normal descuenta solo de `other_gun`.
Solo un tambor que termina sus 1.2 s se rellena hasta ocho. La acción entre tiros
usa `weapons/revolver_cycle`, sin el antiguo ruido de recarga de las duales.
La recarga **doble** se trabaja **a la altura del cinturón**, con cañones bajos, codos
debajo de los hombros y el pecho despejado. No volver al gesto encogido delante
del pecho: el usuario lo vio como un brazo roto incluso cuando las longitudes
eran correctas. Los dos hombros permanecen fijos; no usar `FAR_ARM_INSIDE` en
esta recarga. El brazo lejano pasa detrás del torso y su antebrazo sale delante
solo bajo el pecho. `reload_reach` interpola las rotaciones de los dos huesos
para evitar que el codo salte al recoger el cargador; `turn_toward` usa el arco
corto. Hay 24 cuadros por tambor (50 ms cada uno), con transiciones de cinco
cuadros al enfundar y sacar. `tests/cowgirl_reload_art.py` comprueba longitudes,
codos bajos, muñecas, continuidad, pecho despejado y la unión entre hojas.
La recarga simple sale de `tools/cowgirl_reload.py`: cañón vertical junto a la
cara, muñeca alineada con el antebrazo y tambor unido al arma. Su último cuadro
coincide con la pose de apuntar.
`reload_dual_lower` y `reload_dual_b_lower` contienen la máscara completa de la
acción: antebrazos, manos, revólveres y cargador. Al recargar caminando, el render
recorta esa capa a la altura de la cintura y la compone sobre las piernas animadas.
No volver a recortar el generador desde la fila 60: desaparecían partes de las
armas y de las manos entre el corte del torso y esa fila.
Al interrumpir el rebote antes de disparar (R, salto, Q, golpes o trampas), se
limpian `ricochet_armed` y `power_shot`: nunca conservar un poder pendiente para
un clic normal posterior ni descontar de ambos tambores sin la animación del
poder. Tampoco se puede armar mientras enfunda o tiene las manos ocupadas.

## Arte de UI y elementos de apoyo

`python3 tools/rebuild_support_art.py` reconstruye las 22 hojas de `ui`, `vial`,
`mercenary`, `chest`, `bat`, `clues` y `crow`; `--verify` compara sin modificar
los PNG y corre en `build.sh`. Conserva tamaños, pivotes y estados de animación.
Las rampas de `tools/ui_icons.py` usan madera, hierro, latón envejecido y papel
marfil, con contorno oscuro y luz superior izquierda. `tools/support_finishes.py`
aplica detalles propios de cada material, sin ruido uniforme ni ribetes brillantes.
El mercenario sigue anónimo, con rostro cubierto y equipo verde carbón; el vial
conserva su contenido verde y la contraluz de la escena. El cuervo mantiene sus
estados posado/vuelo/caída y el murciélago vuelo/caída/muerto. El cofre tiene seis
poses con la base inmóvil y sale de `tools/make_chest.py`. Las 30 pistas conservan
su orden en `CLUES`. La fuente blanca de UI es una máscara de tinte: conservar
sus glifos y métricas. `weapons.png` usa las armas reales del juego.
Revisar los PNG a escala nativa ampliada y las capturas de HUD, Expediente,
cinemática y cofre antes de dar por terminado un cambio en estas carpetas.

## Tren laboratorio (2-3)

`python3 tools/train_art.py` genera `train`, `train_interior`, `experimental_parts`
(8 × 32 × 32) y `train_gear` (traje colgado y tableta). Son 15 salas (`TRAIN_ROOMS`):
13 vagones, máquinas y control, con 30 infectados (`TRAIN_CREW`); las salas 01-08
conservan su número (la del vagón 07, criogenia, es la del lore). El mobiliario va en
`tools/train_furnishing.py`. Cada unidad del tren se dibuja a su tamaño final: **nunca reescalar**
la locomotora ni otra pieza (se veía cortada y deformada). El interior usa un solo
sistema de materiales y luz de tubos; nada de rellenos planos ni ruido uniforme:
`Room.block()` pinta las piezas grandes como metal trabajado (degradado, cepillado,
bordes gastados, suciedad al pie, doble bisel); el usuario veía el mobiliario de plástico,
y la puerta y la cabina del vagón 01 planas y falsas: van con profundidad (jambas,
riel, vidrio curvo). La tableta del vagón 01 es la llave de la terminal (sin ella no
se lee el Archivo 4) y el mapa con M; P abre el inventario. Ambos pausan el nivel como
la pausa (`PAUSE_VIEW_MAP`, `PAUSE_VIEW_INVENTORY`). Los trajes (E en los ganchos)
protegen del aire de los vagones 03 y 07 (`train_room_toxic`); con uno puesto, la piel
`suit` del personaje (`characters/<id>/suit/`) sustituye a la normal en todas las
animaciones. Esas hojas salen de `python3 tools/make_hazmat.py` (lo comprueba
`build.sh`): regenéralas tras cambiar cualquier hoja de la sheriff o del SWAT. Las piezas
de los trajes están dibujadas en `tools/hazmat_art.py`, con las proporciones medidas en la
referencia del usuario (2026-11-24): capucha de unos 22 px, dos quintos de la altura, con
ventana sobre una mascarilla de dos filtros, guantes azules largos, cinturón con bolsas,
botas de cuero y tanque de aire. La sheriff lleva capucha con caída, reflejo azul en la
ventana y su estrella en un parche; el SWAT, su propio casco con gafas **ámbar** levantadas
sobre capucha sellada, y su chaleco oscuro **con volumen** (tirantes, placa, bolsas
redondeadas y faldón; el usuario vio el anterior como un cubo). El traje de la sheriff **no
se pinta sobre su ropa**: `tools/hazmat_figure.py` compone, cuadro a cuadro, capucha, torso
holgado, tanque y piernas en los lugares de su cuerpo, con las mismas capas de brazos, armas
y objetos de sus hojas pedidas sin cuerpo; las mangas llevan contorno sobre el traje. Así el
tanque está en todos los cuadros y no quedan paños, cortes ni huecos (el usuario los vio).
Sus piernas salen de `tools/hazmat_legs.py`, con las articulaciones de `cowgirl_pose`;
sentada, de piezas de frente (`HOOD_FRONT`, `TORSO_FRONT`). El coche usa sus mismas
articulaciones (`Figure(suit=True)`) y el desmayo es la pose de pie con traje cayendo. El del
SWAT sale de su generador con cada capa etiquetada (`swat_tagged`), y el casco se coloca por
sus lentes: un solo casco por cuadro (las granadas son de otros verdes) y con su inclinación
al caer o agacharse. El traje colgado del vagón 01 (`train_gear`) usa las mismas piezas.
`drop_floating_ink` quita el contorno suelto. Las armas quedan como están. El guardado (esquema 11) conserva tableta, traje y
gases; un intento de 2-3 anterior al esquema 11 se abandona al cargar, conservando
progreso previo, inventario inicial y expediente.
Puerta, cunas, terminal y escotilla se dibujan en las columnas `TRAIN_*_ART` de
`src/game/train.h`; si cambian, cámbialas en ambos lados (lo comprueba
`tests/test_scenery_assets.py`). Dentro, `train_camera` limita la vista a los
extremos del tren. Los objetivos se consultan en la tableta con M, junto al mapa;
no dibujar una tarjeta persistente sobre el escenario. Recoger la tableta con E
abre el mapa una vez; M/P cambian entre mapa e inventario, y la misma tecla o Esc
los cierran. Solo el aviso temporal de pieza va bajo el HUD a la derecha. El mapa
y el inventario tienen arte propio en `tools/make_field_ui.py` (tres hojas UI,
comprobadas en build.sh). El inventario permite enfocar filas con W/S, flechas,
rueda o ratón y activar con Enter/E o el botón. Usar provisiones cierra la consulta
y ejecuta su acción normal; no consumirlas ni completar recargas con el mundo
pausado. Equipar conserva munición; el traje se cambia en sus ganchos. Los avisos
llevan E solo cuando E actúa y, si algo falta,
dicen qué.

El tamaño del tren no cambia la escala humana del equipo: con un personaje de
unos 64 px de alto, refrigerador de 68 px, mesa de 28 px, mostrador de 36 px y
herramientas de 12–23 px. Dibujar cada pieza a esas dimensiones nativas. Los trajes ocultan
anatomía, ropa y pelo: no conservar la cintura de corsé, el escote, encajes ni mechones.
Sin ópticas nocturnas en los trajes. Las armas conservan sus píxeles y se componen delante
del equipo.

`SCENERY_GAP` separa las huellas de objetos de la carretera. El camión de suministros
reserva su dibujo completo (`terrain_front_half_width`); `terrain_prop_clear` evita
que la decoración procedural invada interactuables, fachadas o el tren. Se conserva
la exclusión después de usar/destruir objetos para evitar apariciones repentinas.
Las capturas `THE_MIRACLE_CAPTURE_GROUP=layout` revisan las distribuciones naturales.
Las ruedas de los vehículos en cinemáticas usan las coordenadas nativas finales de
`make_city.VEHICLE_LAYOUT`, no las del sprite anterior a su ampliación.

## Fachadas y barricadas del oeste

Las fachadas del oeste (`terrain/facades`, 288 × 200) se dibujan a ese tamaño en
`terrain_architecture_detail.western_native`; antes se estiraban de 180 × 128 con
`street_scale` y el usuario las veía de plástico y sin entenderse. Cada abertura muestra
su oficio (forja con brasas y yunque, caballo y silla en el establo, campana, rosetón).
Las motos de barricada (`city_terrain.motorcycle`) son una sola moto por cuadro, con
llantas, guardabarros, motor V y escape; nada de rectángulos bajo el motor.

## Cruzar un coche (N)

Pasos, cuadros, tiempos y distancias en `src/game/car_pass.h` (`car_plan`);
`tools/make_car_passage.py` los lee de ahí, así que se cambian en un solo lugar. Cada
hoja `characters/*/car*` tiene dos filas: lo que de ella queda fuera del coche
(encima de él) y lo que queda dentro (debajo de carrocería y puertas). El usuario vio
el coche encima del personaje y el cuerpo girando raro: **nunca girar el sprite
entero** ni dibujar la carrocería sobre ella cuando está fuera. El torso se inclina
desde la cintura, la cabeza va derecha y las caderas no giran. **Sus piernas son las de sus
demás hojas** (`cowgirl_legs`, más llenas y con rodillera y botas grandes en el SWAT): el
usuario las vio flacas y cruzándose de la nada. La raíz de cada cadera va con su pie
(`SPREAD`), así las piernas se adelantan una a otra sin formar una X. El usuario vio luego los
brazos rotos al pasar por la puerta y una animación que no se entendía: cada mano va como
`Arm(ángulo, alcance)` desde su hombro o en un punto a su alcance, nunca por debajo de
`MIN_REACH`, y el codo dobla siempre hacia su lado (`elbow_for`); nada de brazos plegados
ni cruzados sobre el pecho. **Sus brazos miden lo de todas sus hojas** (`ARM_BONE`, 6.5 +
6.5): con huesos más largos se veía estirada. Toma la manija a un brazo de distancia
(`CAR_REACH`). Para
romper el cristal levanta el antebrazo y golpea con el puño; las astillas caen y quedan
en la calle (`terrain/car_glass`, desde `CAR_STRIKE_LAND`). Al quitar el seguro, la mano
queda dentro del hueco de la ventana y el brazo entero va en la fila de fuera. **Cada
cuadro tiene todo su cuerpo en una sola fila de la hoja** (fuera o dentro): el usuario vio
brazos y piernas sueltos en `car.png` (`test_car_frames_are_whole_in_one_row`). Dentro
va sentada en el piso, casi derecha, con la rodilla cercana levantada (`seated`). El
vidrio, entero o roto, se dibuja encima de ella: dentro no se le ve nada salvo por una
puerta abierta (el usuario vio su sombrero por la ventana como si estuviera fuera). No
hundir la cabeza en los hombros ni girar mucho el torso para que quepa: se ve deformado.
Nada por debajo de `FLOOR` ni por encima del techo.

Los vehículos van más grandes que en la vida real junto a ella (a tamaño real se veían de
su altura): autos, patrulla y todoterreno a `CAR_SCALE` 1.2 y el camión militar a
`TRUCK_SCALE` 1.6 (`tools/make_city.py`). Se dibujan nativos a esa escala (`scaler`): nunca
reescalar el PNG. A 1.25 la ventana quedaba fuera del alcance de su brazo. Medidas en
`src/config.h` (`CAR_WRECK_W/H`, `SIREN_FRAME_W/H`, `VEHICLE_FRAME_W/H`) y manijas en
`car_pass.h`; `refine_terrain.vehicle_layout` sitúa cada uno. Un vehículo del camino ocupa
lo que mide su dibujo (`terrain_vehicle_half_width`), no su cuadro.
`tests/player_render.c` lo comprueba en los tres modelos y ambos sentidos, y
`test_car_arms_never_fold_up` los brazos. Regenerar con
`python3 tools/make_car_passage.py` y revisar `THE_MIRACLE_CAPTURE_GROUP=cars`.

## Repositorio

https://github.com/GuillermoSM33/2D-GAME-PROYECT, en la cuenta **personal** del usuario
(GuillermoSM33). No uses la cuenta del trabajo. El usuario escribe en español.
