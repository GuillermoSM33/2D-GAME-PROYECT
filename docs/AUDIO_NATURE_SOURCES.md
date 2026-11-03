# Naturaleza, cuervos, beber y voces caninas: fuentes y edición

Estos nueve efectos se construyen a partir de **grabaciones físicas CC0**.
No contienen osciladores, ondas cuadradas, pitidos, ruido generado ni una capa
de sonido de chip. El carácter común con el juego se consigue mediante
recortes breves, niveles moderados, mezcla mono y un filtrado cálido.

Se conserva el audio de los zombis y los archivos originales del mundo.
`player/shot` y `player/reload` tampoco los modifica esta herramienta.

## Fuentes

Licencia comprobada en las páginas primarias de Freesound y OpenGameArt el 3 de noviembre
de 2026: **Creative Commons 0, CC0 1.0 Universal**. La licencia permite editar y
redistribuir, también en proyectos comerciales. Se conservan los créditos
para documentar el origen. [Texto de CC0](https://creativecommons.org/publicdomain/zero/1.0/).

| Clave | Autor y grabación | Qué aporta |
| --- | --- | --- |
| `drink` | [thatkellytrna — Drinking Water.wav, #425772](https://freesound.org/people/thatkellytrna/sounds/425772/) | Deglución de una persona bebiendo de una botella |
| `flask` | [qubodup — Water Bottle Gulp, #792933](https://freesound.org/people/qubodup/sounds/792933/) | Agua real al voltear un termo; grabada con Shure SM7B |
| `crow` | [egomassive — Caw.ogg, #536732](https://freesound.org/people/egomassive/sounds/536732/) | Dos graznidos reales; la página acredita la grabación original CC0 de Nigel Coop |
| `wings` | [Godowan — wings.wav, #240476](https://freesound.org/people/Godowan/sounds/240476/) | Aleteo rápido de un pájaro pequeño |
| `wind` | [naturenotesuk — Wind Blowing Leaves in Tree, #442824](https://freesound.org/people/naturenotesuk/sounds/442824/) | Viento en hojas grabado con Zoom H5 |
| `rain` | [xkeril — Clean rain in a courtyard, #612817](https://freesound.org/people/xkeril/sounds/612817/) | Lluvia real sobre superficies de un patio, grabada con Zoom H5 |
| `thunder` | [cognito perceptu — thunder dry crack rumble.wav, #536903](https://freesound.org/people/cognito%20perceptu/sounds/536903/) | Trueno real con ataque y retumbo; sin lluvia ni viento añadidos |
| `dog_bark` | [pauliuw — Dog sounds](https://opengameart.org/content/dog-sounds), miembro `Dog/Dog Bark 2.wav` | Un ladrido ya separado por su autor, dentro de su paquete de nueve sonidos caninos |
| `dog_growl` | [bonebrah — Dog Growl](https://opengameart.org/content/dog-growl), `dog-growl.ogg` | Gruñido de su perro grabado con un Pixel 4; el autor identifica expresamente la acción |
| `dog_whine` | [pauliuw — Dog sounds](https://opengameart.org/content/dog-sounds), miembro `Dog/Sad Dog 1.wav` | Quejido canino normal; no es una grabación de un perro muriendo |

Para las fuentes de Freesound se descargaron los **previews HQ MP3 públicos** enlazados por esas páginas,
no los archivos maestros cuyo acceso requiere iniciar sesión. Convertirlos a
PCM16 evita introducir otra compresión con pérdida; no recupera información
descartada en el MP3. Los enlaces de descarga exactos y sus SHA256 están en
`SOURCES` dentro de [make_nature_sfx.py](../tools/make_nature_sfx.py).

OpenGameArt proporciona el OGG original de `Dog Growl` y el archivo `dog.7z` del
paquete de pauliuw. Este último tiene SHA256
`ecee65b849048790e963952dd15c74889c89d7c948a629e041caa631886d7662`.
La herramienta verifica el paquete y lee únicamente los dos miembros seleccionados
por la salida estándar de `bsdtar`; comprueba además el SHA256 de cada WAV antes de
guardarlo. No extrae las rutas del archivo a disco ni incorpora otras tomas.
Los nombres, enlaces y hashes de los miembros están en `SOURCES` y `ARCHIVES`.

Las grabaciones originales, el paquete y las copias HTML disponibles de las páginas están en
`recordings/cc0_nature/`, carpeta ignorada por Git y excluida del ejecutable.
Los nueve WAV finales sí viven en `assets/sounds/` y se incrustan al compilar.

## Montaje de cada efecto

Los tiempos de origen se expresan en segundos dentro del preview HQ o archivo original indicado. Los
filtros son de FFmpeg y se aplican antes de convertir a 22050 Hz para evitar
aliasing. Todo termina en WAV PCM16, mono: 8 bits añadiría ruido de
cuantización a la lluvia y a las colas suaves de estas grabaciones.

| Archivo final | Cortes y montaje | Tratamiento |
| --- | --- | --- |
| `player/drink.wav`, 1.180 s | `flask` 0–0.202 s en 0.065, 0.405 y 0.755 s; `drink` 7.08–7.40 s en 0.25 s y 17.08–17.35 s en 0.83 s | Agua con paso alto 75 Hz y paso bajo 6500 Hz. Deglución a 110–3000 Hz con puerta suave, umbral 0.004, ratio 2.5. Tres movimientos de agua con intensidad decreciente y deglución entre ellos; sin confirmación musical |
| `crow/caw.wav`, 1.835 s | `crow` 0.035–1.870 s, con ambas llamadas y su pausa natural | Paso alto 75 Hz, paso bajo 6500 Hz; entrada 8 ms, cola 75 ms. Sin cambio de tono |
| `crow/death.wav`, 0.980 s | Segunda llamada de `crow`, 1.19–1.64 s, más `wings` 0.035–0.925 s desde 0.075 s | Graznido acortado y aleteo descendente en volumen. Alas a 85–4800 Hz. No es una grabación de un animal muriendo: es una composición para sugerir sorpresa y pérdida de vuelo, sin pitido ni barrido tonal |
| `weather/wind.wav`, 12.000 s | `wind` 40–53 s | Paso alto 85 Hz, paso bajo 5300 Hz. Unión cruzada de 1 s para formar bucle de 12 s |
| `weather/rain.wav`, 12.000 s | `rain` 20–33 s | Paso alto 110 Hz, paso bajo 6200 Hz. Unión cruzada de 1 s para formar bucle de 12 s |
| `weather/thunder.wav`, 7.670 s | `thunder` 2.18–9.85 s | Paso alto 38 Hz, paso bajo 6100 Hz; entrada 7 ms y salida 900 ms. Mantiene el retumbo largo de la grabación |
| `dog/spawn.wav`, 0.333 s | `dog_bark` 0–0.333 s, una llamada del archivo `Dog Bark 2.wav` | Paso alto 65 Hz, paso bajo 6700 Hz; entrada 6 ms y salida 45 ms; pico máximo 0.70 |
| `dog/idle.wav`, 0.608 s | `dog_growl` 0–0.608 s, grabación identificada como gruñido por su autor | Paso alto 65 Hz, paso bajo 6700 Hz; entrada 9 ms y salida 75 ms; pico máximo 0.60 |
| `dog/death.wav`, 0.720 s | `dog_whine` 0.94–1.66 s, una frase del archivo `Sad Dog 1.wav` y su caída de intensidad | Paso alto 65 Hz, paso bajo 6700 Hz; entrada 9 ms y salida 150 ms; pico máximo 0.62. Quejido natural con decaimiento breve para la acción del juego, sin simular el registro real de una muerte |

Las tres voces caninas conservan el tono y la duración de sus recortes: no se
ralentizan ni se convierten en voces humanas o monstruosas. Una puerta suave de
FFmpeg (`agate`, umbral 0.004, ratio 1.5, ataque 5 ms, salida 65 ms) reduce el fondo
durante los valles. El paquete incluye otras tomas con ruido y picos saturados;
se eligieron `Dog Bark 2.wav` y `Sad Dog 1.wav` por sus nombres y mediciones de señal,
sin afirmar una escucha humana. El gruñido procede de una segunda fuente claramente
etiquetada para evitar atribuir ese gesto a los archivos ambiguos `Dog 1.wav` y
`Dog 2.wav`. Los seis efectos anteriores se conservan byte por byte.

Los bucles conservan la variación propia de las grabaciones. La unión usa
curvas complementarias de coseno y el primer y último valor PCM coinciden.
Los sonidos de acción tienen colas suaves y un pico máximo de 0.76 de la
escala PCM; viento y lluvia se limitan a 0.36 para dejar espacio al combate.

## Regenerar y comparar

Se necesita Python estándar y FFmpeg (`apt install ffmpeg` en Debian/Ubuntu,
`pacman -S mingw-w64-ucrt-x86_64-ffmpeg` en MSYS2 UCRT64). Para descargar y abrir
el paquete canino por primera vez se necesita además `bsdtar` (`apt install
libarchive-tools` / `pacman -S libarchive`); no se usa al regenerar con las dos
fuentes WAV ya guardadas. Estas herramientas solo intervienen en la autoría:
compilar y jugar utilizan los WAV terminados. Si las fuentes ya
están en `recordings/cc0_nature/`, estos comandos no acceden a la red:

```sh
python3 tools/make_nature_sfx.py
python3 tools/make_nature_sfx.py --only player/drink crow/caw crow/death
python3 tools/make_nature_sfx.py --only dog/spawn dog/idle dog/death --review build/dog_audio_review
python3 tools/make_nature_sfx.py --review build/nature_review
```

Para recuperar fuentes faltantes desde los enlaces CC0 verificados:

```sh
python3 tools/make_nature_sfx.py --fetch
```

`--fetch` es explícito; una ejecución normal nunca descarga. La herramienta
comprueba los SHA256 antes de usar una grabación. Una descarga distinta o un
archivo modificado provoca un error y no se incorpora automáticamente.
También se acepta una carpeta de recursos de salida alternativa y la API
`generate(assets_dir: Path, only: list[str] | None = None)`.

`build/nature_review/index.html` ofrece nueve comparaciones para escuchar.
La selección de las tres voces también genera `build/dog_audio_review/index.html`.
En cada WAV se oye primero el montaje de fuentes sin los filtros de acabado,
después 0.7 s de silencio y finalmente el efecto final. Los volúmenes se
ajustan para facilitar la comparación. Estos archivos de revisión permanecen
fuera de los recursos del juego.

## Revisión: seis criterios

La revisión técnica comprueba formato PCM16 mono 22050 Hz, duraciones, ausencia
de saturación, extremos suaves, continuidad de los bucles y reproducción
determinista. También se verificaron los SHA256 de los once sonidos originales
protegidos: permanecieron sin cambios.

`tests/audio_assets.py` comprueba además que un paquete canino alterado se rechaza
antes de extraer, que un miembro con hash diferente no se guarda y que solo se lee
el nombre seleccionado por salida estándar. No descarga fuentes al ejecutar pruebas.

**No se realizó una escucha humana ni se certificó reconocimiento auditivo.**
Las mediciones y el origen de las fuentes permiten justificar el montaje,
pero no sustituyen comprobar el resultado con oído. La página de comparación
permite evaluar los siguientes seis puntos:

1. **Qué objeto o acción se reconoce.** Comprobar que beber se identifica como
   agua y deglución, caw como cuervo, death como cuervo sorprendido con alas, y
   cada clima como viento, lluvia o trueno; las tres voces del perro como ladrido,
   gruñido y quejido. El origen está documentado; la
   identificación por un oyente queda pendiente.
2. **Qué partes son grabadas.** Todas las capas proceden de grabaciones
   físicas; el script no añade sintetizadores ni ruido generado. Escuchar si
   recortes o repeticiones hacen que alguna composición resulte artificial.
3. **Qué tan convincente suena.** Verificar cuerpo, transitorios, cola y nivel
   dentro del juego. Una forma de onda válida no certifica calidad perceptiva.
4. **Cómo convive con el estándar original.** Comparar con `player/shot`,
   `player/reload` y el mundo original. El filtrado, mono y margen de volumen
   buscan una mezcla coherente; este ajuste requiere escucha en contexto.
5. **Qué todavía puede mejorar.** Valorar si beber necesita menos repetición
   de la misma toma, si death pide otra interpretación de la caída o si el
   clima precisa más o menos brillo. Antes de editar, comprobar los ejemplos
   naturales para distinguir una mala fuente de un filtrado excesivo.
6. **Qué cambió frente a la grabación.** Usar cada comparación fuente/final
   para decidir si se conserva la identidad física y si la edición aporta
   claridad. Los enlaces primarios permiten revisar además los previews
   completos con su contexto original.
