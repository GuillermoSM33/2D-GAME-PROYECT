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
  sprites/<entidad>/     Hojas de animación e imágenes de cada cosa del juego
    characters/<id>/     walk, jump, shoot de cada personaje jugable (cowgirl; swat y hero cuando tengan arte)
    zombie/              walk, hurt, death, attack
    weapons/             bullet (una para todas las armas, teñida por cada una)
    chest/               open, sparks
    effects/             armor_sparks (efectos que no son de una sola entidad)
    props/               Decorados del paisaje, compartidos por todos los temas
    ui/                  badge_player, badge_zombie (placas de nivel)
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
| `sprites/characters/<id>/*` (walk, jump, shoot) | Dibujado sobre la base de `docs/templates/character_base/` | [CHARACTERS.md](CHARACTERS.md) | Los de la vaquera: 336 × 67, 432 × 82, 648 × 80 |
| `sprites/weapons/bullet.png` | Dibujado | [SPRITES.md](SPRITES.md) | 4 cuadros de 8 × 6 |
| `sprites/zombie/*` (walk, hurt, death, attack) | Dibujado | [ZOMBIE.md](ZOMBIE.md) | 72 × 72 por cuadro |
| `sprites/chest/open.png` | Dibujado | este documento | 6 cuadros de 72 × 72 |
| `sprites/effects/armor_sparks.png` | Recortado de `zombie/hurt.png` | [ZOMBIE.md](ZOMBIE.md) | 2 cuadros de 20 × 12 |
| `sprites/ui/badge_*.png`, `sprites/chest/sparks.png` | `tools/make_sprites.py` | el propio script | 17 × 19; 8 cuadros de 72 × 72 |
| `sprites/props/*` | Dibujado | [LANDSCAPE.md](LANDSCAPE.md) | Tabla de `src/game/props.c` |
| `backgrounds/<tema>/*` | Dibujado; se revisa con `tools/check_landscape.py` | [LANDSCAPE.md](LANDSCAPE.md) | Tabla de `src/game/themes.c` |
| `sounds/player/*` | `tools/make_sfx.py` | el propio script | — |
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
