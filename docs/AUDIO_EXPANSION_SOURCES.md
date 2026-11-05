# Audio de las acciones nuevas

Esta ampliación añade **14 WAV** y conserva byte por byte los **85 WAV** que
ya tenía el juego. Usa SDL2_mixer y el mismo formato de los efectos grabados:
PCM16 mono a 22050 Hz. No añade dependencias al juego ni sintetiza ondas,
ruido, melodías, chirridos o barridos de tono.

## Fuentes

Las licencias CC0 se comprobaron en las páginas primarias el 5 de noviembre
de 2026. Las fuentes y las mezclas tienen SHA-256 en
[AUDIO_EXPANSION_MANIFEST.json](AUDIO_EXPANSION_MANIFEST.json).

| Fuente | Autor y procedencia | Uso |
| --- | --- | --- |
| `switch_01/02`, `stones_02`, `footstep_wet_02/03`, `loop_water_01/03` | rubberduck, [100 CC0 SFX #2](https://opengameart.org/content/100-cc0-sfx-2), biblioteca ya utilizada por el proyecto | Interruptores, rebote, chapoteo y agua corriente |
| `metal_close_01`, `metal_hit_03`, `wood_hit_06` | rubberduck, [100 CC0 metal and wood SFX](https://opengameart.org/content/100-cc0-metal-and-wood-sfx), biblioteca existente | Selector, carcasa de granada y tapa del libro |
| `step_lth1/2` | HaelDB, [Footsteps Leather, Cloth, Armor](https://opengameart.org/content/footsteps-leather-cloth-armor), opción CC0 de la biblioteca existente | Cuero al abrir el libro y detalle de bota en agua |
| `Book Page Turn` | [Kodack, Freesound #256475](https://freesound.org/people/Kodack/sounds/256475/), libro grabado con Sony HDR PJ260V | Hojas del almanaque |
| `Bat Screeches`, FLAC `bat_01/02/03` | [AntumDeluge, OpenGameArt](https://opengameart.org/content/bat-screeches), extraídos y limpiados de [fruit_bats3.wav de polymorpheva, #104205](https://freesound.org/people/polymorpheva/sounds/104205/) | Tres llamadas distintas de murciélago, para huida, chirrido cercano e impacto |
| `Electric Sparks.wav` | [kev_durr, Freesound #396470](https://freesound.org/people/kev_durr/sounds/396470/), chispas grabadas de una fuente eléctrica de alta tensión | Advertencia del rayo |
| `Fireplace Sound loop` | [PagDev, OpenGameArt](https://opengameart.org/content/fireplace-sound-loop), fuego de leña | Ambiente de fogatas y aceite ardiendo |

Se conserva la autoría aunque CC0 no exige atribución. La licencia es
[CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
Las fuentes Freesound de papel y electricidad son los previews HQ MP3
públicos; guardarlas en PCM16 evita una nueva compresión con pérdida, pero no
recupera datos del maestro. El fuego es el WAV original. Las voces de
murciélago proceden de los **FLAC sin pérdida** del paquete `bat.zip`.

La grabación original de murciélagos se realizó con Zoom H2 en un parque de
Sídney e identifica murciélagos frugívoros. Son llamadas audibles reales,
no ultrasonidos transpuestos ni voces de pájaro. AntumDeluge aisló las llamadas
y eliminó el fondo de una fuente de agua; nuestro montaje conserva su tono
y velocidad. Las asignaciones a huida e impacto son convenciones del juego:
**no se afirma que sean grabaciones de animales heridos o muriendo**.

## Montaje

Los tiempos de archivos sueltos son absolutos en segundos. Los nombres del
ZIP reutilizan el recorte de silencio del generador de foley existente.
Las recetas exactas, colocaciones y ganancias están en
[make_expansion_sfx.py](../tools/make_expansion_sfx.py).

| Salida en `assets/sounds/` | Duración | Montaje y comportamiento |
| --- | --- | --- |
| `player/flashlight_on` | 0.15 s | `switch_01` a velocidad natural; coincide con el interruptor de la animación de cada arma |
| `player/flashlight_off` | 0.15 s | `switch_02`; apagado inmediato, cancela un encendido pendiente |
| `weapons/fire_mode` | 0.17 s | Interruptor y cierre metálico tenue; solo al cambiar efectivamente el selector K |
| `world/grenade_bounce` | 0.24 s | Piedra y carcasa metálica; solo impactos apreciables en suelo/pared, sin repeticiones al reposar |
| `world/splash` | 0.48 s | Dos tomas mojadas distintas y cuero tenue; aterrizaje sobre río o charco |
| `bat/flee` | 1.47 s | Llamada completa `bat_01`, 0–1.428662 s; una señal por huida del grupo |
| `bat/death` | 1.40 s | Llamada completa `bat_03`, 0–1.361270 s; reacción al impacto, sin graznido ni voz artificial |
| `bat/chirp` | 1.79 s | Llamada completa `bat_02`, 0–1.747302 s; cerca de murciélagos vivos que aún no huyen, con pausas de 6–9 s |
| `ui/book_open` | 0.69 s | Papel 0.18–0.77 s con manejo de cubierta de cuero |
| `ui/book_close` | 0.64 s | Papel 8.02–8.56 s y pequeño golpe amortiguado de cubierta |
| `ui/book_page` | 0.59 s | Papel 6.02–6.55 s; al cambiar página o abrir/cerrar una ficha, con ratón o teclado |
| `weather/lightning_warn` | 1.00 s | Chispas 3.25–4.25 s; una vez al comenzar la advertencia, cancelada al caer el rayo o terminar la partida |
| `world/river` | 12.00 s | Agua 03, 0–9.4 s, y agua 01, 0.4–5.5 s, unidas en el segundo 8.4 con cruce de 1 s; bucle continuo por proximidad |
| `world/fire` | 12.00 s | Fuego 5–18 s, con unión cruzada de 1 s; bucle continuo por proximidad |

El aviso eléctrico es una señal de peligro formada con electricidad grabada,
no una afirmación de que todos los rayos tengan un aviso audible previo.
El ambiente de fuego adapta leña grabada tanto a fogatas como al fuego del
suelo. El agua corriente adapta las tomas de la biblioteca al río del juego.

El filtro común corta graves bajo 75 Hz y suaviza agudos sobre 6200 Hz.
**Las tres voces de murciélago conservan agudos hasta 9800 Hz** para mantener
sus chirridos, sin alterar tono ni velocidad. Papel, agua y fuego reciben
compresión suave 2:1; interruptores y voces conservan su dinámica. La
normalización tiene un objetivo RMS y un techo de pico: no sube un chasquido
aislado hasta forzar el mismo RMS que un ambiente continuo. Los efectos
tienen entradas y salidas breves; los bucles cruzan la unión sin apagarse.

El mezclador reserva cuatro canales para viento, lluvia, río y fuego, además
de 28 para efectos. Los ambientes locales bajan suavemente con la distancia;
varias fogatas cercanas comparten un bucle para no sumar volumen. Pausa,
salida y reinicio mantienen la limpieza de canales existente. Las roturas de
cada botella y farol reutilizan `world/glass`, sin crear un duplicado.

## Regeneración y revisión

Las fuentes están en `recordings/cc0_expansion/` y `recordings/cc0_foley/`,
fuera de Git y del ejecutable. Solo `--fetch` permite descargar fuentes; cada
archivo se verifica antes de usarse. Los FLAC de murciélago se leen como
miembros nombrados del ZIP, sin extraer sus rutas a disco; también se
comprueba su hash individual.

```sh
python3 tools/make_expansion_sfx.py --fetch
python3 tools/make_expansion_sfx.py --manifest docs/AUDIO_EXPANSION_MANIFEST.json
python3 tools/make_expansion_sfx.py build/audio-preview --only bat/flee bat/death bat/chirp
python3 tools/make_expansion_sfx.py --review build/expansion_review
python3 tools/check_audio.py --report build/audio_check.json
./build.sh
```

`--review` prepara 14 comparaciones: recorte de fuente sin ensamblar, pausa
de 350 ms y mezcla del juego. El recorte fuente ya pasa por el filtro de
decodificación. No se presenta como una escucha humana realizada por la
herramienta. La comprobación automática verifica formato, niveles, extremos,
uniones, referencias, hashes e integración; no certifica por sí sola la
semejanza perceptiva con un animal u objeto. Los WAV y las comparaciones
quedan disponibles para esa revisión auditiva.
