# Sonido

Los efectos físicos nuevos usan grabaciones CC0 de mecanismos, materiales,
agua, cuervos y clima. El montaje, los niveles y un filtrado cálido conservan
el carácter del juego. El pixel art no obliga a usar pitidos electrónicos.

Se conservan **byte por byte los once originales**: `zombie/*`, los seis
archivos legacy de `world/`, `player/shot` y `player/reload`. Estos dos últimos
son exclusivos del cañón de mano de la vaquera. En la ampliación anterior
se reemplazaron `player/drink`, `crow/caw` y `crow/death`.

Los efectos nuevos o rehechos son WAV PCM16 mono a 22050 Hz. Los 16 bits
conservan las colas suaves sin añadir hiss. No se reexportan los originales.
La ampliación de noviembre añade catorce efectos y conserva byte por byte los
85 WAV que ya estaban en el juego.

## Fuentes y montaje

| Familia | Licencias, fuentes, edición y límites |
| --- | --- |
| Disparos y mecanismos | [AUDIO_WEAPON_SOURCES.md](AUDIO_WEAPON_SOURCES.md) |
| Golpes, materiales, pasos, ropa y trampas | [AUDIO_FOLEY_SOURCES.md](AUDIO_FOLEY_SOURCES.md) |
| Beber, cuervos y clima | [AUDIO_NATURE_SOURCES.md](AUDIO_NATURE_SOURCES.md) |
| Explosiones, plasma, cofres, avisos y menús | [AUDIO_DESIGNED_SOURCES.md](AUDIO_DESIGNED_SOURCES.md) |
| Linterna, selector, rebotes, chapoteos, murciélagos, almanaque y ambiente local | [AUDIO_EXPANSION_SOURCES.md](AUDIO_EXPANSION_SOURCES.md) |
| Respiración, laboratorio, latido, radio/cámara, ambulancia y sello del Expediente | [AUDIO_CINEMATIC_SOURCES.md](AUDIO_CINEMATIC_SOURCES.md) |

Las fuentes crudas quedan en `recordings/`, ignoradas por Git y fuera del
ejecutable. Cada generador registra sus URLs y hashes. Las licencias se
verificaron en las páginas primarias. No se extrajo audio de otros juegos.
Plasma, recompensas y algunos avisos son composiciones; no se presentan como
grabaciones literales de un objeto real.

## Música

Cada nivel tiene su tema, compuesto y sintetizado en el propio repositorio, sin material de
terceros: [AUDIO_MUSIC.md](AUDIO_MUSIC.md).

## Generación reproducible

`tools/make_sfx.py` coordina los generadores por familia y comprueba que no
escriban el mismo archivo. Para crear audio se requiere FFmpeg y descargar
las fuentes CC0. **Compilar y jugar no requieren descargas.**

```sh
python3 tools/make_sfx.py --fetch
python3 tools/make_sfx.py
python3 tools/make_sfx.py --only weapons/shotgun_reload weapons/shotgun_cycle
python3 tools/make_sfx.py build/audio-preview
```

Sin `--fetch`, una fuente ausente produce un error sin acceder a la red.
La generación no reintroduce los borradores electrónicos descartados.
`--legacy` crea originales sintetizados que falten, sin reemplazar archivos
existentes. `tools/crush_sfx.py` sigue disponible para grabación manual.

## Integración

| Evento | Comportamiento |
| --- | --- |
| Armas | Disparo, ciclo, recarga, vacío y culatazo propios. Corredera e inserción de cartuchos son efectos separados |
| Impactos | Carne, armadura, madera, metal, piedra, sacos y alambre según el objetivo |
| Explosiones | Barril conserva su original; granada y dinamita tienen montajes distintos |
| Trampas | Cepo conserva `world/snap`; alambre, cuerda/red y liberación tienen eventos propios |
| Acciones | Beber y vendarse suenan al comenzar; el culatazo empieza antes del impacto. Interrumpir una recarga cancela su sonido |
| Clima | Viento y lluvia en bucles de 12 s, con canales reservados. El trueno sigue al relámpago |
| Ambiente local | Río y fuego en bucles de 12 s, con volumen según la cercanía y canales reservados |
| Perro infectado | Ladrido, gruñido y quejido caninos propios; las voces originales de los zombis se conservan |
| Murciélagos | Chirridos agudos de murciélagos reales al volar cerca, huir y recibir un impacto. Conservan el tono y la velocidad de la grabación; el efecto de impacto adapta una llamada, sin presentarla como una muerte grabada |
| Linterna y selector | Clics grabados al encender/apagar la linterna y cambiar el modo de fuego |
| Granada y agua | Rebote de la granada contra el suelo y chapoteo al aterrizar en el agua |
| Almanaque | Apertura, cierre y paso de página discretos, además de los clics de navegación existentes |
| Aviso de rayo | Señal física breve durante la advertencia previa al impacto |
| Interfaz y progreso | Clics mecánicos discretos, cofre, emboscada, nivel y victoria |
| Intro | Respiración discreta, zumbido de maquinaria, latido real y alarma grabada; radio sin voz, interferencia al caer la cámara y sirena de ambulancia. La muestra conserva su silencio de tensión |
| Cintas de historia | Ataúdes, tierra, zombis, pasos, cuervos y apagado de faroles siguen el reloj de cada toma. El laboratorio tiene sus propios ambientes |
| Expediente | Papel al abrir, examinar y cerrar; navegación y respuestas con una sola señal; golpe de sello a los 0.55 s, sin rotura de madera |

Las armas con munición ilimitada no producen falsos avisos de cargador vacío.
Las recargas de banco retrasan el inicio del sonido para que su cierre
coincida con la animación, manteniendo la velocidad natural del mecanismo.
El volumen afecta inmediatamente a los canales activos. Pausar congela los
sonidos de la partida y permite los clics del menú; salir o reiniciar limpia
los sonidos anteriores.

La ampliación de cinemáticas añade **ocho efectos** y conserva los **99 WAV anteriores y las seis músicas**
sin reexportarlos. Los sonidos nuevos usan grabaciones reales y montajes discretos,
sin añadir voces ni doblaje. Los cues dependen de la simulación, no de cuántas veces
se dibuja una imagen. Saltar la intro limpia sus efectos y bucles; acelerar una frase
de una cinta omite los sonidos de las acciones saltadas. Cada cambio de toma termina
los sonidos anteriores, y el fin de la cinta conserva la música del menú.

## Comprobaciones

```sh
python3 tools/check_audio.py --report build/audio_check.json
./build.sh
```

Se comprueban cobertura, referencias, formato, silencio, picos, componente
continua, extremos, bucles, tiempos y los once hashes registrados en
`AUDIO_LEGACY_SHA256.json`. El catálogo se obtiene de los generadores y las
referencias se buscan en todo `src/`; los manifiestos de diseño y ampliación
deben cubrir sus salidas y coincidir con sus hashes. Las pruebas SDL usan dispositivos `dummy`.
`build.sh` ejecuta las pruebas, verifica los recursos incrustados y realiza
la prueba de humo del juego.

Para generar comparaciones de fuentes y resultados fuera de `assets/`:

```sh
python3 tools/make_nature_sfx.py --review build/nature_review
python3 tools/make_designed_sfx.py --review
python3 tools/make_expansion_sfx.py --review build/expansion_review
python3 tools/make_cinematic_sfx.py build/cinematic_review --only cinematic/heartbeat ui/stamp
```

La revisión considera correspondencia física, ausencia de pitidos genéricos,
coherencia con los legacy, mejoras posibles y contraste con la fuente real.
Las herramientas de esta sesión no admiten escucha de audio: las pruebas
técnicas y las fuentes grabadas no se presentan como aprobación auditiva humana.
