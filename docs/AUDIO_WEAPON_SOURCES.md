# Armas: fuentes y montaje

Los mecanismos del rifle y de la escopeta proceden de grabaciones CC0.
Los disparos conservan el ataque y la resonancia de armas grabadas. Los
originales `player/shot` y `player/reload` siguen intactos y solo pertenecen
al cañón de mano de la vaquera; las duales derivan sus capas en archivos propios.

| Fuente y autor | Licencia | Uso |
| --- | --- | --- |
| [Shotgun Reload Sound Effects — zer0_sol](https://opengameart.org/content/shotgun-reload-sound-effects) | CC0 | `First Shell.mp3`, `Subsequent Shells.mp3`, `Rack.mp3`: inserción de cartuchos y corredera |
| [Gun reload sounds — SpringySpringo](https://opengameart.org/content/gun-reload-sounds) | CC0 | `assaultriflereload1.wav`, `shotguncock.wav`: manejo grabado de réplicas airsoft; cargador y cerrojo del rifle, detalle de lanzamiento |
| [Gun Reload Sound Effects — Brian MacIntosh / BMacZero](https://opengameart.org/content/gun-reload-sound-effects) | CC0 | `clipload1.wav`, `singlebullet1.wav`: cambio de arma y manipulación metálica |
| [AR15 rifle shot — michorvath #427596](https://freesound.org/people/michorvath/sounds/427596/) | CC0 | Transitorio de disparo del rifle |
| [20 gauge shotgun gunshot — michorvath #427595](https://freesound.org/people/michorvath/sounds/427595/) | CC0 | Disparo de escopeta, con una capa leve del cuerpo del cañón legacy |
| [Rifle clip empty — michorvath #427603](https://freesound.org/people/michorvath/sounds/427603/) | CC0 | Gatillo vacío; variantes según el mecanismo |

Las licencias se comprobaron en las páginas primarias el 3 de noviembre de
2026. Los archivos de Freesound son los previews HQ MP3 públicos enlazados en
esas páginas. Las fuentes quedan en `recordings/cc0_weapons/`, fuera del
ejecutable y de Git; el generador incluye sus enlaces de descarga.

## Edición

La escopeta **no cambia de tono ni acelera su mecanismo**. Se colocan dos
inserciones de cartucho en los 1.10 s que ya dura la animación del juego:
`First Shell` 0.32–0.85 s desde 0.01 s, y `Subsequent Shells` 0.65–1.19 s
desde 0.55 s. Se recortan pausas de manipulación, conservando cada gesto.
La corredera va aparte: `Rack` 0.55–1.07 s desde 0.08 s, en un archivo de
0.62 s. No es una grabación de llenar ocho cartuchos en 1.10 s: la mecánica
existente abstrae una recarga completa en ese tiempo y no se alteró.

El rifle usa los cortes 0.18–0.40, 0.94–1.16 y 1.16–1.48 s de su grabación,
colocados en 0.015, 0.51 y 0.84 s. El golpe final del cerrojo coincide con el
final de los 1.20 s de recarga. Las duales conservan dos capas ligeramente
separadas de los sonidos legacy en sus propios WAV. Los gatillos vacíos se
basan en un disparador grabado, sin pitidos.

La anilla/lanzamiento es una composición de manejo metálico, no una
grabación de una granada real. Los efectos de vacío solo se activan cuando
la mecánica de esa arma permite quedarse sin cargador; el cañón de mano, las
duales y el plasma actualmente tienen munición ilimitada.

Todos se guardan como PCM16 mono a 22050 Hz. Filtros suaves a 65–6700 Hz,
entradas/salidas breves y margen de pico conservan los detalles mecánicos y
evitan añadir hiss con una conversión forzada a 8 bits.

```sh
python3 tools/make_weapon_foley.py --fetch
python3 tools/make_weapon_foley.py --only weapons/shotgun_reload weapons/shotgun_cycle
```

## Revisión solicitada

Cada efecto se contrasta con su fuente física y con los legacy. Se comprueba
que el gesto corresponda al evento, que no se convierta en un tono musical,
que conserve el ataque y los detalles, que encaje en la animación y que sus
capas no saturen la mezcla. Se descartó la primera versión electrónica de
la recarga de escopeta y se sustituyó por este montaje de grabaciones.

La verificación de formas de onda, fuentes y sincronía es reproducible.
La herramienta de esta sesión no admite escuchar audio: estas comprobaciones
no se presentan como una aprobación auditiva humana. Los WAV quedan
disponibles para escucharlos y compararlos con sus fuentes.
