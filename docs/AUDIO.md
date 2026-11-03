# Sonido

Los efectos físicos nuevos usan grabaciones CC0 de mecanismos, materiales,
agua, cuervos y clima. El montaje, los niveles y un filtrado cálido conservan
el carácter del juego. El pixel art no obliga a usar pitidos electrónicos.

Se conservan **byte por byte los once originales**: `zombie/*`, los seis
archivos legacy de `world/`, `player/shot` y `player/reload`. Estos dos últimos
son exclusivos del cañón de mano de la vaquera. Los únicos anteriores
reemplazados son `player/drink`, `crow/caw` y `crow/death`.

Los 60 efectos nuevos o rehechos son WAV PCM16 mono a 22050 Hz. Los 16 bits
conservan las colas suaves sin añadir hiss. No se reexportan los originales.

## Fuentes y montaje

| Familia | Licencias, fuentes, edición y límites |
| --- | --- |
| Disparos y mecanismos | [AUDIO_WEAPON_SOURCES.md](AUDIO_WEAPON_SOURCES.md) |
| Golpes, materiales, pasos, ropa y trampas | [AUDIO_FOLEY_SOURCES.md](AUDIO_FOLEY_SOURCES.md) |
| Beber, cuervos y clima | [AUDIO_NATURE_SOURCES.md](AUDIO_NATURE_SOURCES.md) |
| Explosiones, plasma, cofres, avisos y menús | [AUDIO_DESIGNED_SOURCES.md](AUDIO_DESIGNED_SOURCES.md) |

Las fuentes crudas quedan en `recordings/`, ignoradas por Git y fuera del
ejecutable. Cada generador registra sus URLs y hashes. Las licencias se
verificaron en las páginas primarias. No se extrajo audio de otros juegos.
Plasma, recompensas y algunos avisos son composiciones; no se presentan como
grabaciones literales de un objeto real.

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
| Perro infectado | Ladrido, gruñido y quejido caninos propios; las voces originales de los zombis se conservan |
| Interfaz y progreso | Clics mecánicos discretos, cofre, emboscada, nivel y victoria |

Las armas con munición ilimitada no producen falsos avisos de cargador vacío.
Las recargas de banco retrasan el inicio del sonido para que su cierre
coincida con la animación, manteniendo la velocidad natural del mecanismo.
El volumen afecta inmediatamente a los canales activos. Pausar congela los
sonidos de la partida y permite los clics del menú; salir o reiniciar limpia
los sonidos anteriores.

## Comprobaciones

```sh
python3 tools/check_audio.py --report build/audio_check.json
./build.sh
```

Se comprueban cobertura, referencias, formato, silencio, picos, componente
continua, extremos, bucles, tiempos y los once hashes registrados en
`AUDIO_LEGACY_SHA256.json`. Las pruebas SDL usan dispositivos `dummy`.
`build.sh` ejecuta las pruebas, verifica los recursos incrustados y realiza
la prueba de humo del juego.

Para generar comparaciones de fuentes y resultados fuera de `assets/`:

```sh
python3 tools/make_nature_sfx.py --review build/nature_review
python3 tools/make_designed_sfx.py --review
```

La revisión considera correspondencia física, ausencia de pitidos genéricos,
coherencia con los legacy, mejoras posibles y contraste con la fuente real.
Las herramientas de esta sesión no admiten escucha de audio: las pruebas
técnicas y las fuentes grabadas no se presentan como aprobación auditiva humana.
