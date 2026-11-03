# Recursos: dónde va cada cosa

Todo lo que el juego dibuja o reproduce vive en `assets/`. Al compilar,
`tools/embed_assets.py` lo mete **dentro del ejecutable**, así que `dist/` no necesita
carpetas sueltas. En el código, un recurso se nombra por su **ruta dentro de `assets/`, sin
extensión**: `assets/sprites/zombie/walk.png` es `"sprites/zombie/walk"` y
`assets/sounds/player/shot.wav` es `"player/shot"` (los sonidos van sin el `sounds/`).

## Estructura

```text
assets/
  fonts/                 Fuentes del texto (DejaVu Sans Mono) y su licencia
  sounds/<entidad>/      Efectos de sonido (.wav, .ogg)
    player/              shot, reload
    zombie/              spawn, idle, death
    world/               explosion, supply, fuse, glass, wood, snap (lo que pasa en el camino)
  sprites/<entidad>/     Hojas de animación e imágenes de cada cosa del juego
    characters/<id>/     walk, jump, shoot, sit (y shoot_dual, throw, sit_shotgun...) de cada personaje jugable (cowgirl, swat; hero cuando tenga arte),
                         y shoot_<arma> / reload_<arma> si un arma tiene hoja propia
                         (swat/shoot_shotgun, swat/reload, swat/reload_shotgun)
    zombie/              walk, hurt, death, attack
    crow/                crow (picotea, vuela, cae y queda muerto; tools/make_terrain.py)
    weapons/             bullet (una para todas las armas, teñida por cada una), grenade
    chest/               open, sparks
    effects/             armor_sparks, explosion, heal, glow (efectos que no son de una sola entidad)
    terrain/             barricade, wall, wall_ruins, barrel, dynamite, charge, crate, bottles, trap, coffin,
                         lamp, fire, bench, campfire, supply, goal: lo que hay en el camino
    props/               Decorados del paisaje, compartidos por todos los temas
    ui/                  badge_player, badge_zombie (placas de nivel); font, panel, button, key,
                         pip, bar, icons, weapons (la interfaz)
  backgrounds/<tema>/    Capas del fondo de un tema: sky, far, hills_far, hills_near, ground (y fog)
    atardecer/  cementerio/  noche/  pueblo_fantasma/
```

**Reglas**

- **Una carpeta por entidad** (`characters/<id>`, `zombie`, `chest`…), tanto en `sprites/`
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

## Qué lo genera y qué lo comprueba

| Recurso | Origen | Especificación | Tamaño exacto |
| --- | --- | --- | --- |
| `sprites/characters/<id>/*` (walk, jump, shoot, shoot_<arma>, reload_<arma>) | Dibujado sobre la base de `docs/templates/character_base/` | [CHARACTERS.md](CHARACTERS.md) | Los de la vaquera: 336 × 67, 432 × 82, 648 × 80 (shoot_<arma> y reload_<arma> como shoot) |
| `sprites/weapons/bullet.png` | Dibujado | [SPRITES.md](SPRITES.md) | 4 cuadros de 8 × 6 |
| `sprites/characters/cowgirl/shoot_dual.png`, `sprites/weapons/grenade.png` | `tools/make_powers.py` | el propio script | shoot_dual como shoot.png; granada 4 × 8 × 8 |
| `sprites/characters/swat/throw.png` | `tools/make_swat.py` | el propio script | 8 × 81 × 80, plantilla de disparo |
| `sprites/characters/cowgirl/melee.png`, `melee_dual.png` | `tools/make_melee.py` | su hoja de disparo | 7 × 81 × 80, plantilla de disparo; con las duales, una pistola en cada mano |
| `sprites/characters/cowgirl/drink.png`, `bandage.png` | `tools/make_care.py` | su hoja de disparo | 6 × 81 × 80, plantilla de disparo: beber del galón; vendarse el muslo (5 vueltas y la venda puesta) |
| `sprites/characters/swat/drink.png`, `bandage.png` | `tools/make_swat.py` | el propio script | 6 × 81 × 80, igual |
| `sprites/characters/<id>/faint.png` (cowgirl, swat) | `tools/make_faint.py` | su hoja de caminar | 8 × 80 × 67, pivote en la columna 40, suelo en la fila 61 |
| `sprites/characters/swat/melee.png`, `melee_shotgun.png` | `tools/make_swat.py` | el propio script | 7 × 81 × 80, plantilla de disparo; una por arma (`WeaponDef.melee_sheet`) |
| `sprites/zombie/*` (walk, hurt, death, attack) | Dibujado | [ZOMBIE.md](ZOMBIE.md) | 72 × 72 por cuadro |
| `sprites/chest/open.png` | Dibujado | este documento | 6 cuadros de 72 × 72 |
| `sprites/effects/armor_sparks.png` | Recortado de `zombie/hurt.png` | [ZOMBIE.md](ZOMBIE.md) | 2 cuadros de 20 × 12 |
| `sprites/characters/swat/*` | `tools/make_swat.py`, a partir de `docs/templates/swat/walk_source.png` | [CHARACTERS.md](CHARACTERS.md#el-swat) | Los de la vaquera |
| `sprites/ui/{font,panel,button,key,pip,bar,icons,weapons}.png` | `tools/make_ui.py` | el propio script | font: 6 × 10 por letra en el orden de `pixfont.c`; el resto, `--verify` |
| `sprites/ui/badge_*.png`, `sprites/chest/sparks.png` | `tools/make_sprites.py` | el propio script | 17 × 19; 8 cuadros de 72 × 72 |
| `sprites/props/*` | Dibujado | [LANDSCAPE.md](LANDSCAPE.md) | Tabla de `src/game/props.c` |
| `sprites/props/houses.png` | `tools/make_terrain.py`, en los colores de los props (cada tema los recolorea) | el propio script | 9 × 80 × 64 (5 casas y las 4 estructuras); casas de fondo, `HOUSE_*` en `config.h`, `house_chance` por tema |
| `sprites/characters/{cowgirl,swat}/sit.png`, `swat/sit_shotgun.png` | `tools/make_sit.py`, de frente, en sus colores, con el arma de `ui/weapons.png` (una hoja por arma: `WeaponDef.sit_sheet`) | el propio script | 14 cuadros de 72 × 67, pivote 35.5 |
| `sprites/terrain/*`, `sprites/effects/{explosion,heal,glow}.png` | `tools/make_terrain.py` | el propio script | crow (`sprites/crow/crow.png`) 8 × 16 × 12, sign 22 × 30, river 4 × 120 × 22 (18 filas bajo la línea del suelo) y river_front 4 × 120 × 6 (su superficie sobre los pies), puddle 4 × 36 × 5, splash 5 × 20 × 12, tumbleweed 4 × 14 × 14, barricade 12 × 68 × 26 (4 tipos × entera, rota, destruida), wire 3 × 80 × 22, net 3 × 40 × 30 (puesta, saltando, vacía), snare 3 × 48 × 64 (doblado, enderezándose, derecho), spikes 3 × 32 × 16, net_bag 4 × 44 × 66 (2 de vaivén, 2 cerrándose), crate 11 × 32 × 28 (5 botines —balas, vida, dinamita, oro, agua— × entera y rota, más rota), trap 3 × 32 × 12 (abierta, cerrándose, cerrada), coffin 4 × 28 × 60 (día y noche), blood 4 × 8 × 4, wall 3 × 44 × 72, wall_ruins 180 × 84, facades 4 × 180 × 128 (iglesia, comisaría, herrería, establo), door 3 × 44 × 64, barrel 26 × 36, bench 76 × 32, campfire 8 × 48 × 44 (4 sola, 4 con olla), supply 2 × 100 × 56, goal 108 × 96; explosión 8 × 72 × 72, heal 12 × 64 × 96 (`config.h`) |
| `backgrounds/<tema>/*` | Dibujado; se revisa con `tools/check_landscape.py`; el sol de atardecer y pueblo fantasma lo pinta `tools/make_sun.py` | [LANDSCAPE.md](LANDSCAPE.md) | Tabla de `src/game/themes.c` |
| `sounds/player/*`, `sounds/world/*` | `tools/make_sfx.py` | el propio script | — |
| `sounds/zombie/*` | Voz grabada, `tools/crush_sfx.py` | [README](../README.md#sonido) | — |

`./build.sh` corre `--verify`, que falla si falta algo de lo que el código usa o si una
imagen no tiene su tamaño exacto: las hojas de animación (por su `AnimationDef`), las placas
de nivel, **cada capa del fondo de cada tema que usan los niveles** y **cada hoja de
decorados**. Así, un PNG mal exportado se detecta al compilar y no jugando.

## Formato

- Imágenes: **PNG RGBA de 8 bits, sin entrelazado**, a 1× (el juego escala a 4× sin
  suavizado). `embed_assets.py` rechaza otros formatos.
- Sonidos: WAV (8 o 16 bits) u OGG.
- Las hojas con varios cuadros los ponen **en una fila**, todos del mismo tamaño.

## Agregar algo

| Quiero agregar… | Dónde | Además |
| --- | --- | --- |
| Un personaje | `sprites/characters/<id>/` (walk, jump, shoot) | Su fila en `characters.c` ([CHARACTERS.md](CHARACTERS.md#agregar-un-personaje)) |
| Una animación del zombi | `sprites/zombie/<acción>.png` | Su `AnimationDef` en `zombie.c` |
| Un decorado nuevo | `sprites/props/<nombre>.png` | Una fila en `props.c` y su peso en los temas que lo usen (`themes.c`) |
| Un tema de paisaje | `backgrounds/<tema>/` con sus capas | Revisarlas con `tools/check_landscape.py`, un `ThemeDef` en `themes.c` y asignarlo a niveles en `stages.c` ([LANDSCAPE.md](LANDSCAPE.md#agregar-un-tema)) |
| Un sonido | `sounds/<entidad>/<nombre>.wav` | `audio_play("<entidad>/<nombre>")` donde suene, y agregarlo a `--verify` en `main.c` |

## Cofre (`sprites/chest/open.png`)

6 cuadros de 72 × 72, de cerrado a abierto, a 10 fps. Mismo cuadro que el zombi: cuerpo
centrado en x 36.5 (ocupa x 15–57) y apoyado en la fila 66. Las chispas
(`chest/sparks.png`) usan la misma plantilla y se dibujan encima.
