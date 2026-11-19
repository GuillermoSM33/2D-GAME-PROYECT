# THE MIRACLE

(Antes Vaquera 2D; el repo y la carpeta del proyecto conservan el nombre viejo.)

**Cambio pendiente en la PC de Windows:** desde 2026-11-11 las partidas y preferencias van en
`%APPDATA%\TheMiracle\TheMiracle\` (antes `%APPDATA%\Vaquera2D\Vaquera2D\`). Al abrir este repo
en Windows, si aún existe la carpeta vieja y no la nueva, muévela (en PowerShell:
`New-Item -ItemType Directory -Force "$env:APPDATA\TheMiracle" | Out-Null; Move-Item "$env:APPDATA\Vaquera2D\Vaquera2D" "$env:APPDATA\TheMiracle\TheMiracle"`;
luego borra `%APPDATA%\Vaquera2D` si quedó vacía) y quita este aviso. En Linux ya se hizo.
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

## Arte de la vaquera (la sheriff Dolores Vega)

El usuario pidió el rework visual el 2026-11-12 para acompañar los escenarios y objetos:
materiales terrosos, luz superior izquierda y revólver de ocho balas, recarga de 1.2 s
como el rifle del SWAT. `tools/detail_cowgirl.py` aplica el acabado a todas las hojas
al final del generador. La última referencia del usuario **reemplaza el azul por vino**:
chaquetita/chalequito corto y abierto encima del corsé, con solapas y mangas color vino
tomadas de su foto. `cropped_jacket` en `tools/rework_cowgirl.py` dibuja los paneles en el
cuerpo común antes de derivar las poses; sus etiquetas `JACKET` se conservan al reconstruir
el torso y al sentarse. El corsé conserva el gris pizarra/carbón; el pantalón lleva **dos
tonos de gris**, sin azul. Cuero marrón oscuro y vino en el pañuelo.
El usuario pidió **recuperar el rojo anterior al rework**: conservar exactamente la paleta
original del pelo (`#6b333a`, `#902004`, `#d03305`), sin recolorearla ni añadir reflejos
rosados. Los extremos del encaje se esconden bajo las solapas para que no queden puntos
blancos sobre la chamarra. Lleva dos botones de latón discretos (`JACKET_BUTTON` y
`jacket_buttons`), distintos de la placa; sus colores se conservan al reconstruir el torso.
El busto tiene un aumento sutil en la curva de `TORSO_FRONT` y volumen cubierto por el
corsé con `corset_bust`, compartido por todas las poses. En SIT, el cinturón se deriva del
plano claro de la cara original, y las solapas y botones se dibujan de frente.
La ropa sigue sobria; no añadirle bordes blancos, ribetes luminosos ni halo.
Debe distinguirse del fondo de 1-1 mediante contraste cromático y materiales separados, con
volumen por planos suaves y contorno oscuro. Encaje gris marfil y latón envejecido,
sin blancos ni amarillos intensos en la ropa.
Tiene **un solo cuerpo**
en todas las poses de pie: torso y cinturón salen de las tablas de `tools/rework_cowgirl.py`
(`TORSO_FRONT`, `BELT_FRONT`, `BACK_SIDE`), relativas a la hebilla, que va bajo su barbilla. Cámbialo
ahí, nunca en una sola hoja. La meta es una silueta de reloj de arena: hombros y cadera de ancho
parecido, cintura marcada y sin escalón entre cinturón y pierna; la curva va en tramos de dos filas
para que no salga en escalera.
Sus brazos no vienen de la plantilla: se dibujan aparte sobre el cuerpo completo, con un solo modelo
de brazo y guante (`tools/cowgirl_arm.py`) y **un solo dibujo de pistola**,
`assets/sprites/characters/cowgirl/weapons/pistol.png`, generado por `tools/make_revolver.py`,
para las dos manos; las poses están en `walk_arms`, `jump_arms`
y `ON_HIPS`. Al caminar se balancean los dos, casi rectos y con aire junto a la cintura; solo parada
lleva las manos en la cadera.
El balanceo de caminar conserva una flexión fija de codo y gira solo 4° por lado desde
el hombro (`walk_arms`), sin redondear las articulaciones antes de dibujar. No volver a
resolver el codo en cada cuadro: alternaba entre doblado y recto y parecía un gusano.
La luz de la manga apunta siempre arriba a la izquierda, sin cambiar de lado a mitad del paso.
En SIT, el cabello largo cae delante de ambas orejas y las cubre en todos los cuadros,
incluidos respiración, recarga y cabeceo (`tools/make_sit.py`).
Regenera todas sus hojas con
`python3 tools/rebuild_cowgirl.py` y revísalas ampliadas antes de reportarlas.

Es la sheriff del pueblo: lleva una **placa** (estrella de latón) en el pecho, definida una sola
vez en `tools/rework_cowgirl.py` (`BADGE`, `sheriff_badge`) y usada por todas sus poses: `dress`,
`body_without_arm` de `make_melee.py` (disparo, culatazo, linterna, rebote) y `make_sit.py`.
Solo se pinta sobre el corsé o la chaquetita, así que un brazo por delante la tapa.

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
La recarga se trabaja **a la altura del cinturón**, con cañones bajos, codos
debajo de los hombros y el pecho despejado. No volver al gesto encogido delante
del pecho: el usuario lo vio como un brazo roto incluso cuando las longitudes
eran correctas. Los dos hombros permanecen fijos; no usar `FAR_ARM_INSIDE` en
esta recarga. El brazo lejano pasa detrás del torso y su antebrazo sale delante
solo bajo el pecho. `reload_reach` interpola las rotaciones de los dos huesos
para evitar que el codo salte al recoger el cargador; `turn_toward` usa el arco
corto. Hay 24 cuadros por tambor (50 ms cada uno), con transiciones de cinco
cuadros al enfundar y sacar. `tests/cowgirl_reload_art.py` comprueba longitudes,
codos bajos, muñecas, continuidad, pecho despejado y la unión entre hojas.
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
`build.sh`): regenéralas tras cambiar cualquier hoja de la sheriff o del SWAT. Las armas
quedan como están: las del SWAT se marcan al regenerar su generador y las de la
sheriff se detectan por su acero. El guardado (esquema 11) conserva tableta, traje y
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
comprobadas en build.sh). Los avisos llevan E solo cuando E actúa y, si algo falta,
dicen qué.

El tamaño del tren no cambia la escala humana del equipo: con un personaje de
unos 64 px de alto, refrigerador de 68 px, mesa de 28 px, mostrador de 36 px y
herramientas de 12–23 px. Dibujar cada pieza a esas dimensiones nativas. La sheriff
lleva un overol amarillo holgado con visor azul: silueta neutra que oculta anatomía,
ropa y pelo. No conservar la cintura de corsé, el escote, encajes ni mechones
bajo la capucha. El visor naranja corresponde al SWAT táctico, que mantiene por
fuera placas oscuras, protecciones y botella de aire. Sin ópticas nocturnas en las
capuchas. Las armas conservan sus píxeles y se componen delante del equipo.

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
desde la cintura, la cabeza va derecha y las caderas no giran. El usuario vio luego los
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
