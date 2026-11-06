# Recursos: dónde va cada cosa

Todo lo que el juego dibuja o reproduce vive en `assets/`. Al compilar,
`tools/embed_assets.py` lo mete **dentro del ejecutable**, así que `dist/` no necesita
carpetas sueltas. En el código, un recurso se nombra por su **ruta dentro de `assets/`, sin
extensión**: `assets/sprites/zombies/riot/walk.png` es `"sprites/zombies/riot/walk"` y
`assets/sounds/player/shot.wav` es `"player/shot"` (los sonidos van sin el `sounds/`).

## Estructura

```text
assets/
  fonts/                 Fuentes del texto (DejaVu Sans Mono) y su licencia
  music/                 El tema de los menús (menu.ogg) y el de cada nivel (ruta_1_1.ogg ... ruta_1_5.ogg, en stages.c)
  sounds/<entidad>/      Efectos de sonido (.wav, .ogg)
    player/              shot, reload (cañón original), drink, melee, empty, hurt, jump, land, bandage, death, faint; flashlight_on, flashlight_off
    zombie/              spawn, idle, death
    crow/                caw, death (grabaciones de cuervo y alas)
    bat/                 chirp, flee, death (chirridos de murciélagos reales)
    dog/                 spawn, idle, death (voces caninas grabadas)
    weapons/             disparo, recarga, vacío y culatazo propios por arma; switch, fire_mode, grenade_throw, ricochet
    weather/             wind, rain (bucles), thunder, lightning_warn
    effects/             hit_flesh, hit_armor
    ui/                  move, confirm, back; book_open, book_close, book_page
    world/               explosion, supply, fuse, glass, wood, snap (originales), impactos, trampas, movimiento y avisos; grenade_bounce, splash, river y fire (bucles locales)
  sprites/<entidad>/     Hojas de animación e imágenes de cada cosa del juego
    characters/<id>/     walk, jump, shoot, sit (y shoot_dual, throw, sit_shotgun...) de cada personaje jugable (cowgirl, swat; hero cuando tenga arte),
                         y shoot_<arma> / reload_<arma> si un arma tiene hoja propia
                         (swat/shoot_shotgun, swat/reload, swat/reload_shotgun)
    zombies/<id>/        idle, walk, run, attack, hurt, death, caught; una carpeta por cada una de las 25 familias
                         riot, soldier, police, riot_shield, civil_male_1..5, civil_female_1..5,
                         burned, skeleton, dog, sheriff, cowboy, motorcycle, priest, jailer,
                         firefighter, butcher, elite
    crow/                crow (picoteo, vuelo y caída en una sola hoja)
    bat/                 bat (aleteo, caída y muerto; solo de noche)
    weapons/             bullet (una para todas las armas, teñida por cada una), grenade
    chest/               open, sparks
    effects/             armor_sparks, explosion, heal, glow (efectos que no son de una sola entidad)
    characters/cowgirl/walk_dual, jump_dual  Caminar y saltar con las duales: una funda en cada cadera
    characters/cowgirl/weapons/bullet  La bala del rebote (14 × 20 × 16, tools/make_ricochet.py): 0-3 en vuelo, 4-7 girando tras rebotar, 8-13 el impacto
    characters/cowgirl/ricochet, ricochet_dual, y sus _lit  El rebote (F): 8 cuadros de plantilla de shoot, las dos manos juntas y dos balas, con una o con las dos armas
    characters/cowgirl/weapons/pistol  Su pistola sola: el mismo dibujo en las dos manos y en todas las hojas; se cambia aquí y se regeneran con tools/rebuild_cowgirl.py. La mano la toma por la empuñadura (GRIP_AT en tools/cowgirl_arm.py)
    characters/cowgirl/swap_far, light_dual_far  Solo su brazo lejano y su pistola, en los cuadros de swap y light_dual que la lleva: se dibujan enteros sobre las piernas al caminar
    characters/cowgirl/legs, legs_dual  Su caminar sin brazos (8 cuadros como walk): las piernas bajo otra pose mientras camina
    characters/cowgirl/stand, stand_dual  De pie, quieta: las manos en la cadera (1 cuadro del tamaño de walk; sin ella, el primer cuadro de walk)
    characters/cowgirl/shoot_dual, shoot_dual_b  Las duales turnándose (16 cuadros de plantilla de shoot por turno, `PLAYER_PISTON_FRAMES`): la cercana dispara desde el hombro y sube en retroceso; la lejana baja junto a la pierna y dispara desde la cadera, cada brazo en un arco continuo a lo largo de los dos turnos
    characters/cowgirl/melee_lit, melee_dual_lit  El culatazo con la linterna en el arma; termina en la pose con linterna
    characters/cowgirl/shoot_dual_lit, shoot_dual_b_lit  Los mismos turnos con la linterna encendida: su pistola sigue arriba y la otra dispara desde la cadera
    characters/cowgirl/swap, swap_lit  Sacar la segunda pistola de la funda, bajarla por fuera de la pierna y volver a guardarla (12 cuadros, plantilla de shoot; swap_lit con la linterna puesta)
    characters/*/light*  Encender la linterna (16 cuadros, plantilla de shoot; el último se mantiene), light_walk* caminando con ella (8) y de pie respirando (4); cowgirl/flashlight: la linterna sola sobre shoot
    terrain/             barricade, wall, wall_ruins, barrel, dynamite, charge, crate, bottles, trap, coffin,
                         lamp, fire, bench, campfire, supply, goal: lo que hay en el camino
    props/               Decorados del paisaje, compartidos por todos los temas
    ui/                  badge_player, badge_zombie (placas de nivel); font, panel, button, key,
                         pip, bar, icons, weapons, notice_dev (la interfaz)
  backgrounds/<tema>/    Capas del fondo de un tema: sky, far, hills_far, hills_near, ground (y fog)
    atardecer/  cementerio/  noche/  pueblo_fantasma/
```

**Reglas**

- **Una carpeta por entidad** (`characters/<id>`, `zombies/<id>`, `chest`…), tanto en `sprites/`
  como en `sounds/`. Lo de una entidad nueva va en su propia carpeta. Lo que comparten varias
  va en una carpeta de su tipo: `weapons/`, `effects/`, `props/`, `ui/`.
- **Nombres en inglés, minúsculas y `_`**, como el código: `badge_player.png`, `hills_far.png`.
  El tema va en español porque es como lo llamamos en el diseño (`atardecer`, `cementerio`).
- **El nombre dice qué es, no de dónde salió:** `armor_sparks`, no `sparks2` ni
  `hurt_cut`. Si dos cosas se pueden confundir (`chest/sparks` y `effects/armor_sparks`), el
  nombre lo aclara.
- **Nada que el juego no use:** vistas previas, ZIP, manifiestos y bocetos van a `docs/img/`
  (si sirven de referencia) o no se guardan. Todo lo que hay en `assets/` termina dentro del
  ejecutable.
- **Grabaciones crudas** en `recordings/` (fuera de git), nunca en `assets/`.

Las 25 familias de zombis utilizan **50 variantes de juego** (normal y corredora).
Comparten la carpeta de su profesión: `walk` y `run` dan sus ciclos de movimiento,
y las otras acciones conservan la identidad. El almanaque reutiliza estas hojas,
el candado y las piezas existentes de `sprites/ui/` para sus tarjetas y fichas.
Se abre con `B` durante la partida y desde las opciones de los menús principal y pausa.

Las cuatro hojas originales del antidisturbios se mantienen byte por byte en
`sprites/zombies/riot/`; el élite dispone de sus copias utilizadas en su propia carpeta.
Las voces originales siguen compartidas en `sounds/zombie/`, sin cambios.

## Qué lo genera y qué lo comprueba

| Recurso | Origen | Especificación | Tamaño exacto |
| --- | --- | --- | --- |
| `sprites/characters/<id>/*` (walk, jump, shoot, shoot_<arma>, reload_<arma>) | Dibujado sobre la base de `docs/templates/character_base/` | [CHARACTERS.md](CHARACTERS.md) | Los de la vaquera: 336 × 67, 432 × 82, 648 × 80 (shoot_<arma> y reload_<arma> como shoot) |
| `sprites/weapons/bullet.png` | `tools/make_powers.py` y `tools/ui_icons.py` | [SPRITES.md](SPRITES.md) | 4 cuadros de 8 × 6 |
| `sprites/characters/cowgirl/shoot_dual*.png` | `tools/make_flashlight.py` | el propio script | 16 × 81 × 80, plantilla de disparo |
| `sprites/weapons/grenade.png` | `tools/make_powers.py` | el propio script | granada 4 × 8 × 8 |
| `sprites/characters/swat/throw.png` | `tools/make_swat.py` | el propio script | 8 × 81 × 80, plantilla de disparo |
| `sprites/characters/cowgirl/melee.png` | `tools/make_flashlight.py` (poses en `tools/make_melee.py`; brazo, guante y las dos pistolas en `tools/cowgirl_arm.py`) | su hoja de disparo | 7 × 81 × 80, plantilla de disparo |
| `sprites/characters/cowgirl/melee_dual.png` | `tools/make_flashlight.py` | su hoja de disparo | 7 × 81 × 80; golpea con una pistola y la otra queda junto a su pierna |
| `sprites/characters/cowgirl/drink.png`, `bandage.png` | `tools/make_care.py` | su hoja de disparo | 6 × 81 × 80, plantilla de disparo: beber del galón; vendarse el muslo (5 vueltas y la venda puesta) |
| `sprites/characters/swat/drink.png`, `bandage.png` | `tools/make_swat.py` | el propio script | 6 × 81 × 80, igual |
| `sprites/characters/cowgirl/plant.png`, `swat/plant.png` | `tools/make_plant.py` | su hoja de disparo / el cuerpo del SWAT | 6 × 81 × 80, plantilla de disparo: saca un cartucho de dinamita, lo deja abajo con la mecha encendida y vuelve la mano (`PLANT_TIME`, 0.45 s) |
| `sprites/characters/<id>/faint.png` (cowgirl, swat) | `tools/make_faint.py` | su hoja de caminar | 8 × 80 × 67, pivote en la columna 40, suelo en la fila 61 |
| `sprites/characters/swat/melee.png`, `melee_shotgun.png` | `tools/make_swat.py` | el propio script | 7 × 81 × 80, plantilla de disparo; una por arma (`WeaponDef.melee_sheet`) |
| `sprites/zombies/riot/{walk,hurt,death,attack}.png` | Originales preservados; las cuatro hojas del élite mantienen el mismo arte base | [ZOMBIE.md](ZOMBIE.md) | 72 × 72 por cuadro; 8/3/8/6 cuadros respectivamente |
| `sprites/zombies/<id>/{idle,walk,run,attack,hurt,death,caught}.png` | Prendas y equipo editados sobre la base original en `docs/templates/zombies/`; exportación nativa con `tools/make_zombies.py` | [ZOMBIE.md](ZOMBIE.md), `tests/test_zombie_catalog.c`, `tests/test_zombie_assets.py` | 72 × 72 por cuadro: idle/caught 4, walk/run/death 8, attack 6, hurt 3 |
| `sprites/chest/open.png` | Dibujado | este documento | 6 cuadros de 72 × 72 |
| `sprites/effects/armor_sparks.png` | Recortado de `zombies/riot/hurt.png` | [ZOMBIE.md](ZOMBIE.md) | 2 cuadros de 20 × 12 |
| `sprites/characters/swat/*` | `tools/make_swat.py`, a partir de `docs/templates/swat/walk_source.png` | [CHARACTERS.md](CHARACTERS.md#el-swat) | Los de la vaquera |
| `music/*.ogg` | `tools/make_music.py`, compuesta y sintetizada aquí | [AUDIO_MUSIC.md](AUDIO_MUSIC.md) | Vorbis estéreo, 22050 Hz, bucle continuo |
| `sprites/ui/{font,panel,button,key,pip,bar,icons,icons_hd,weapons,weapons_hd,notice_dev}.png` | `tools/make_ui.py` y `tools/ui_icons.py` | el propio script | font: 6 × 10 por letra en el orden de `pixfont.c`; el resto, `--verify` |
| `sprites/ui/badge_*.png`, `sprites/chest/sparks.png` | `tools/make_sprites.py` | el propio script | 17 × 19; 8 cuadros de 72 × 72 |
| `sprites/props/*` | Dibujado | [LANDSCAPE.md](LANDSCAPE.md) | Tabla de `src/game/props.c` |
| `sprites/props/houses.png` | `tools/make_terrain.py`, en los colores de los props (cada tema los recolorea) | el propio script | 13 × 80 × 64 (5 casas, las 5 estructuras con el banco, y el almacén, la casa de adobe y el silo caído); casas de fondo, `HOUSE_*` en `config.h`, `house_chance` por tema |
| `sprites/characters/{cowgirl,swat}/sit.png`, `swat/sit_shotgun.png` | `tools/make_sit.py`, de frente, en sus colores, con el arma de `ui/weapons.png` (una hoja por arma: `WeaponDef.sit_sheet`) | el propio script | 14 cuadros de 72 × 67, pivote 35.5 |
| `sprites/terrain/*`, `sprites/effects/{explosion,heal,glow}.png` | `tools/make_terrain.py` | el propio script | crow (`sprites/crow/crow.png`) 8 × 16 × 12, bat (`sprites/bat/bat.png`) 6 × 16 × 10, sign 22 × 30, river 4 × 200 × 22 (18 filas bajo la línea del suelo; el centro hondo, `RIVER_DEEP_SHARE`) y river_front 4 × 200 × 17 (sus filas desde la superficie, sobre quien vadea: hasta la cintura en lo hondo), puddle 4 × 64 × 6, splash 5 × 20 × 12, tumbleweed 4 × 14 × 14, barricade 12 × 68 × 36 (4 tipos × entera, rota, destruida; bajo su cara y más alta que el salto: se pasa con N), wire 3 × 112 × 30, net 3 × 84 × 128 (árbol seco con la red bajo hojas, saltando, vacía), snare 3 × 72 × 124 (oculto en un arbusto, enderezándose, derecho), spikes 3 × 40 × 22, net_bag 4 × 44 × 66 (2 de vaivén, 2 cerrándose), crate 11 × 32 × 36 (5 botines —balas, vida, dinamita, oro, agua— × entera y rota, más rota), trap 3 × 48 × 18 (abierta, cerrándose, cerrada), coffin 4 × 32 × 68 (día y noche), blood 4 × 8 × 4, wall 3 × 44 × 72, wall_ruins 180 × 84, facades 5 × 180 × 128 (iglesia, comisaría, herrería, establo, banco), door 3 × 44 × 64, barrel 26 × 36, bench 2 × 76 × 44 (madera, hierro forjado), campfire 8 × 48 × 56 (4 sola, 4 con olla), supply 2 × 100 × 56, goal 108 × 96; explosión 8 × 72 × 72, heal 12 × 64 × 96 (`config.h`) |
| `backgrounds/<tema>/*` | Dibujado; se revisa con `tools/check_landscape.py`; el sol de atardecer y pueblo fantasma lo pinta `tools/make_sun.py` | [LANDSCAPE.md](LANDSCAPE.md) | Tabla de `src/game/themes.c` |
| Efectos nuevos de `sounds/` | `tools/make_sfx.py`, grabaciones CC0 y capas originales | [AUDIO.md](AUDIO.md), fuentes y generadores por familia | PCM16 mono, 22050 Hz |
| Sonidos legacy de `player/` y `world/` | Originales conservados, sin regeneración automática | [AUDIO.md](AUDIO.md) y hashes de referencia | Sin cambios |

Todo `sprites/ui` y `sprites/weapons` sigue una sola regla, para que parezca de la misma mano:
los materiales de `tools/ui_icons.py` (rampas de cinco tonos: latón, hierro, madera, hueso...),
contorno de tinta de 1 px y luz siempre desde arriba a la izquierda. Un recurso nuevo para estas
carpetas toma sus colores de ahí, no de una paleta propia.

`sprites/ui/icons_hd.png` tiene 29 celdas de 24 × 24 px, dibujadas en `tools/ui_icons.py`;
`ui_icon` las usa desde la escala 2 (se ven nítidas en 2, 4 y 6). `sprites/ui/icons.png` son los
mismos iconos en 12 × 12 para los huecos sin espacio (escala 1); `make_icons` de `tools/make_ui.py`
rechaza uno descentrado o con el contorno abierto. Ambas usan el orden de `UiIcon` en
`src/game/ui.h`. Las armas del HUD son **las del juego**: `weapons.png` (36 × 14) son los propios sprites
(`cowgirl/weapons/pistol.png` y las plantillas de `tools/make_swat.py`, con la linterna y la
bayoneta), y `weapons_hd.png` (72 × 28) los traza con detalle en `tools/ui_icons.py`, pieza por
pieza y en las coordenadas de esos sprites. Si un arma cambia en el juego, cambia en los dos.

`./build.sh` corre `--verify`, que falla si falta algo de lo que el código usa o si una
imagen no tiene su tamaño exacto: las hojas de animación (por su `AnimationDef`), las placas
de nivel, **cada capa del fondo de cada tema que usan los niveles** y **cada hoja de
decorados**. Así, un PNG mal exportado se detecta al compilar y no jugando.
La tabla de texturas se reserva según el número real de imágenes incrustadas:
no tiene el límite anterior de 128. `tests/assets_loader.c` comprueba un catálogo
de 160 imágenes, su reproducción y la liberación de recursos al recargar.

Las fuentes de edición de ropa (`<id>_walk_clothes_source.png`) y sus prompts quedan en
`docs/templates/zombies/`. Son personajes completos: su cabeza, silueta, prendas y equipo
son la referencia al exportar. La careta y las placas del RIOT no forman parte del cuerpo
de las otras profesiones. El exportador conserva la escala y registra la cabeza y el
equipo con su propia pose, sin proyectar sombreros o cuellos sobre todo el cuerpo.
Los archivos finales de `assets/` siempre tienen celdas nativas de 72 × 72.
`riot_run_source.png` aporta los apoyos y suspensiones de la carrera humanoide;
el perro y el zombi degradado conservan sus propias fuentes de carrera. La ropa y el equipo de cada familia
se registran sobre esos movimientos, manteniendo su identidad entre acciones.

La iluminación utiliza las fuentes del terreno y las explosiones: `lighting.c` calcula
la altura, la obstrucción y las sombras; `terrain_render.c` las compone sobre el mundo.
La linterna nocturna se alterna con `L`. El clima usa partículas de `weather.c` y la
planta rodadora existente; `weather_render.c` dibuja lluvia, polvo, hojas y relámpagos
sobre cielo y camino antes del HUD. Los paneles y estados del HUD se comprueban con
sus métricas de texto y pruebas de renderizado, sin crear retratos o fondos duplicados.

## Formato

- Imágenes: **PNG RGBA de 8 bits, sin entrelazado**, a 1× (el juego escala a 4× sin
  suavizado). `embed_assets.py` rechaza otros formatos.
- Sonidos: WAV (8 o 16 bits) u OGG.
- Las hojas con varios cuadros los ponen **en una fila**, todos del mismo tamaño.

## Agregar algo

| Quiero agregar… | Dónde | Además |
| --- | --- | --- |
| Un personaje | `sprites/characters/<id>/` (walk, jump, shoot) | Su fila en `characters.c` ([CHARACTERS.md](CHARACTERS.md#agregar-un-personaje)) |
| Una familia de zombi | `sprites/zombies/<id>/`, con las siete hojas | Su fila de catálogo en `zombie.c`, estadísticas y variante corredora; asignación en `stages.c` y ficha del almanaque |
| Una animación del zombi | `sprites/zombies/<id>/<acción>.png` | Su `AnimationDef` en `zombie.c`, las medidas de [ZOMBIE.md](ZOMBIE.md) y las pruebas del catálogo |
| Un decorado nuevo | `sprites/props/<nombre>.png` | Una fila en `props.c` y su peso en los temas que lo usen (`themes.c`) |
| Un tema de paisaje | `backgrounds/<tema>/` con sus capas | Revisarlas con `tools/check_landscape.py`, un `ThemeDef` en `themes.c` y asignarlo a niveles en `stages.c` ([LANDSCAPE.md](LANDSCAPE.md#agregar-un-tema)) |
| Un sonido | `sounds/<entidad>/<nombre>.wav` | `audio_play("<entidad>/<nombre>")` donde suene, y agregarlo a `--verify` en `app/verify.c` |

## Cofre (`sprites/chest/open.png`)

6 cuadros de 72 × 72, de cerrado a abierto, a 10 fps. Mismo cuadro que el zombi: cuerpo
centrado en x 36.5 (ocupa x 15–57) y apoyado en la fila 66. Las chispas
(`chest/sparks.png`) usan la misma plantilla y se dibujan encima.
