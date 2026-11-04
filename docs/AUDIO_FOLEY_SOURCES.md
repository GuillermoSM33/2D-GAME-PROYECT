# Acciones físicas: grabaciones y edición

Los 25 efectos de esta lista proceden de **grabaciones de objetos reales**.
No contienen osciladores, pitidos, notas musicales ni barridos sintéticos.
Se recortan, se mezclan y se filtran suavemente a una misma paleta: WAV PCM
mono a 22050 Hz, 16 bits, con margen de pico. El contenedor de 16 bits conserva
los detalles de tela y grava sin añadir ruido de cuantización.

## Fuentes CC0

| ID | Autor y paquete | Página que declara la licencia | Descarga original |
| --- | --- | --- | --- |
| `wm` | rubberduck, **100 CC0 metal and wood SFX** | [OpenGameArt: CC0](https://opengameart.org/content/100-cc0-metal-and-wood-sfx) | [100-CC0-wood-metal-SFX.zip](https://opengameart.org/sites/default/files/100-CC0-wood-metal-SFX.zip) |
| `v2` | rubberduck, **100 CC0 SFX #2** | [OpenGameArt: CC0](https://opengameart.org/content/100-cc0-sfx-2) | [sfx_100_v2.zip](https://opengameart.org/sites/default/files/sfx_100_v2.zip) |
| `step` | HaelDB, **Footsteps Leather, Cloth, Armor** | [OpenGameArt: CC0 / OGA-BY 3.0](https://opengameart.org/content/footsteps-leather-cloth-armor) | [footsteps.zip](https://opengameart.org/sites/default/files/footsteps.zip) |

Se elige **CC0** para el paquete de HaelDB, ofrecido también bajo OGA-BY 3.0.
[Texto de la dedicación CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/).
La atribución no es obligatoria bajo CC0; se conservan autoría y procedencia
para poder revisar o cambiar los sonidos después.

Los originales quedan en `recordings/cc0_foley/`, excluidos de Git y del
ejecutable. No se usan los archivos descargados de Kenney: esas solicitudes
devolvieron HTML en lugar de los ZIP esperados.

SHA-256 de los tres archivos originales, verificados por el generador:

```text
100-CC0-wood-metal-SFX.zip be6eba63b03409ac0c77787a956b1503a7c186403d04aef9725c52644a4b7878
sfx_100_v2.zip            0fc61b4494e2e893c0c015ced4877b3f689c7d84a48cb61daecd7ddb52db797b
footsteps.zip             94b5155d119d9378315c2b4457c00098d78a36f2a2c436d5145687d1d3bad257
```

## Montaje

Todas las extensiones de origen son `.ogg`. `v2:foo` significa
`sfx100v2_foo.ogg`; `step:foo` vive dentro de la carpeta `footsteps/` del ZIP.
Las capas, cortes en segundos, velocidades y ganancias exactas están en
`RECIPES` y `Layer` en [make_foley_sfx.py](../tools/make_foley_sfx.py).

| Salida relativa a `assets/sounds/` | Grabaciones utilizadas |
| --- | --- |
| `world/hit_wood` | `wm:wood_hit_06`, `wood_cracking_01` |
| `world/hit_metal` | `wm:metal_hit_03`, `metal_sheet_01` |
| `world/hit_stone` | `v2:stones_02`, `hit_01` |
| `world/hit_sand` | `v2:footstep_01`, `step:step_cloth3` |
| `world/hit_wire` | `wm:metal_sheet_01`, `metal_hit_03` |
| `world/wire` | `wm:metal_sheet_01`, `step:step_cloth2` |
| `world/rope` | `step:step_cloth1`, `step_lth2`, `step_cloth3` |
| `world/trap_escape` | `wm:wood_cracking_01`, `step:step_cloth4`, `v2:footstep_01` |
| `world/footstep`, `_2` a `_4` (suelo seco) | `v2:footstep_02`, `footstep_wood_03`, `footstep_wood_04` |
| `world/run_step`, `_2` a `_4` (suelo seco) | `v2:footstep_02`, `footstep_wood_03`, `footstep_wood_04` |
| `world/footstep_water`, `_2` a `_4` (río o charco) | `v2:footstep_01`, `footstep_02`, `footstep_wood_01`, `footstep_wood_04`, `step:step_lth1`, `step_lth2`, `step_lth33`, `step_lth4` |
| `world/run_step_water`, `_2` a `_4` (río o charco) | `v2:footstep_01`, `footstep_02`, `footstep_wood_01`, `footstep_wood_03`, `footstep_wood_04`, `step:step_lth1`, `step_lth2`, `step_lth33`, `step_lth4`, `step_cloth1` a `step_cloth4` |
| `world/sit` | `step:step_cloth1`, `step_lth2`, `wm:wood_squeak_01` |
| `world/stand` | `step:step_cloth2`, `step_lth1`, `wm:wood_squeak_01` |
| `effects/hit_flesh` | `v2:hit_01`, `footstep_wet_03`, `step:step_cloth4` |
| `effects/hit_armor` | `wm:metal_hit_03`, `step:step_lth1`, `v2:hit_01` |
| `player/melee` | `v2:air_02`, `step:step_lth1`, `wm:wood_hit_06` |
| `weapons/dual_melee` | `v2:air_02`, `step:step_lth2`, `wm:metal_sheet_01` |
| `weapons/rifle_melee` | `v2:air_02`, `step:step_cloth2`, `wm:metal_hit_03` |
| `weapons/shotgun_melee` | `v2:air_02`, `step:step_lth1`, `wm:wood_hit_06` |
| `weapons/plasma_melee` | `v2:air_02`, `step:step_lth2`, `wm:metal_sheet_01` |
| `player/bandage` | `step:step_cloth1`, `step_cloth3`, `step_cloth4` |
| `player/hurt` | `v2:hit_01`, `air_02`, `step:step_cloth4` |
| `player/jump` | `step:step_lth1`, `step_cloth3`, `v2:air_02` |
| `player/land` | `v2:footstep_02`, `hit_01`, `step:step_cloth1` |
| `player/death` | `step:step_cloth1`, `step_lth1`, `step_cloth4`, `v2:hit_02` |
| `player/faint` | `step:step_cloth2`, `step_lth2`, `step_cloth4`, `v2:hit_01` |

El culatazo contiene movimiento de aire, ropa y peso del arma. La colisión
real añade por separado el golpe del material o del zombi. `hurt`, `death`
y `faint` usan impacto corporal y ropa; no sustituyen voces de zombis ni
inventan una voz del personaje.

El proceso elimina silencios de grabación, conserva el ataque, atenúa graves
bajo 65 Hz, aplica un filtro de agudos a 5900 Hz y comprime suavemente los
transitorios. Los pasos tienen menos volumen que los impactos. Cada clip
empieza y termina con una envolvente breve para evitar chasquidos.

## Reproducir la generación

Requiere Python estándar y FFmpeg para decodificar las fuentes OGG. No cambia
las dependencias del juego y funciona en Linux y en Windows/MSYS2 UCRT64.

```sh
python3 tools/make_foley_sfx.py --download
python3 tools/make_foley_sfx.py
python3 tools/make_foley_sfx.py build/foley-preview --only world/hit_wood player/land
```

`--download` (también `--fetch`) solo descarga si falta un original y verifica su SHA-256 antes
de utilizarlo. Sin esa opción, una fuente ausente produce un error claro.
El script solo puede escribir los 39 nombres anteriores. Quedan intactos
`zombie/*.wav`, `player/shot.wav`, `player/reload.wav` y los seis sonidos
legados de `world/` (`wood`, `glass`, `fuse`, `snap`, `explosion`, `supply`).
