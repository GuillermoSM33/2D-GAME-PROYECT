# Sonidos de las cintas y el expediente

Esta ampliación añade ocho WAV, sin sustituir los 99 efectos anteriores.
Usa grabaciones reales CC0 y la biblioteca de foley existente. La salida es
PCM16 mono a 22050 Hz; el juego sigue usando SDL2_mixer y no necesita FFmpeg
ni acceso a Internet para compilar o jugar.

No se crean osciladores, ruido aleatorio, latidos sintetizados, barridos de
sirena ni voces habladas. El latido conserva el ritmo del corazón grabado.
La alarma y la sirena son aparatos reales grabados, aunque el aparato emita
un tono electrónico. Los cambios de ganancia, filtrado y fundidos no alteran
el tono ni la velocidad del material.

## Fuentes verificadas

Las páginas primarias identifican sus archivos como CC0. Se comprobaron el
11 de noviembre de 2026; los originales descargados y las páginas quedan en
`recordings/cc0_cinematic/`, fuera de Git y del ejecutable. El manifiesto
[AUDIO_CINEMATIC_MANIFEST.json](AUDIO_CINEMATIC_MANIFEST.json) registra URLs,
autores, SHA-256 de descargas, miembros de archivos y salidas terminadas.

| Fuente | Autor, página y procedencia | Uso |
| --- | --- | --- |
| Breath_Woman.wav | [audione, Freesound 108160](https://freesound.org/people/audione/sounds/108160/), respiración femenina grabada, sin diálogo | Respiración baja de Valeria en la escena de la cámara |
| Real Heartbeat (DIY Stethoscope recording) | [modusmogulus, Freesound 831630](https://freesound.org/people/modusmogulus/sounds/831630/), el corazón del propio autor, registrado con estetoscopio casero | Latido de la escena del monitor rojo |
| Walkie Talkie radio static | [SEF7, Freesound 701330](https://freesound.org/people/SEF7/sounds/701330/), estática de un walkie-talkie Cobra capturada con Zoom H4n | Interferencia de la radio y señal perdida de la cámara |
| Ambulance siren | [stereobrother, Freesound 445344](https://freesound.org/people/stereobrother/sounds/445344/), ambulancia en una calle de Manhattan, Zoom H2n | Ambulancia que se aleja por la carretera |
| Fire alarm | [pushkin, Freesound 319413](https://freesound.org/people/pushkin/sounds/319413/), alarma real del edificio del autor | Advertencia del laboratorio |
| Book Page Turn | [Kodack, Freesound 256475](https://freesound.org/people/Kodack/sounds/256475/), páginas grabadas con Sony HDR PJ260V; fuente ya utilizada en el almanaque | Papel bajo el sello del expediente |
| `sfx100v2_loop_machine_01.ogg` | rubberduck, [100 CC0 SFX #2](https://opengameart.org/content/100-cc0-sfx-2), paquete existente | Ambiente de máquinas del laboratorio |
| `wood_hit_06.ogg` | rubberduck, [100 CC0 metal and wood SFX](https://opengameart.org/content/100-cc0-metal-and-wood-sfx), paquete existente | Golpe seco del sello |

Se conserva la atribución aunque [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)
no la exige. Los WAV/FLAC maestros de Freesound requieren una cuenta; se
utilizan sus previews públicos HQ MP3, sin iniciar sesión. Exportarlos como
PCM16 evita otra compresión con pérdida, pero no recupera los datos del
maestro. Las muestras de los paquetes locales provienen de OGG originales.

La estática de cámara **adapta una radio grabada**, sin afirmar que sea la
misma cámara de la historia. El ambiente adapta una máquina real al laboratorio
ficticio. La ambulancia procede de un entorno urbano; el recorte y filtrado
reducen el fondo sin presentar la toma como una grabación aislada de estudio.

## Recortes y mezcla

Todos los tiempos siguientes son absolutos en la fuente decodificada, sin
recortar silencios de manera automática. Las recetas exactas están en
[make_cinematic_sfx.py](../tools/make_cinematic_sfx.py).

| Salida | Duración | Recorte y tratamiento |
| --- | --- | --- |
| `cinematic/breath` | 5.8 s | Respiración 0–5.8 s; HP 80 Hz / LP 4200 Hz, entrada de 35 ms y salida suave de 160 ms |
| `cinematic/lab_hum` | 12 s, bucle | Máquina 01, 0.35–7.35 s, dos tomas colocadas en 0 y 6 s con cruce de 1 s; HP 50 Hz / LP 1800 Hz |
| `cinematic/heartbeat` | 12 s, bucle | Latido 4–17 s; HP 22 Hz / LP 950 Hz, conservando los graves del cuerpo y el ritmo natural |
| `cinematic/lab_alarm` | 12 s, bucle | Alarma 4–17 s; HP 110 Hz / LP 5000 Hz |
| `cinematic/radio_static` | 1.4 s | Walkie-talkie 0.25–1.65 s; HP 300 Hz / LP 4200 Hz |
| `cinematic/camera_static` | 2.6 s | Walkie-talkie 0.4–3 s; HP 200 Hz / LP 5200 Hz; una toma más larga y distinta |
| `cinematic/ambulance_siren` | 8 s | Ambulancia 13.7–21.7 s, tramo después de su paso; HP 180 Hz / LP 3800 Hz, ganancia que baja de 1 a 0.16 y salida de 2 s |
| `ui/stamp` | 0.24 s | Golpe de madera 0–0.15 s colocado en 0.025 s; papel 6.02–6.20 s a ganancia 0.12; HP 75 Hz / LP 4200 Hz |

Los bucles reservan 13 s de material y cierran con un cruce de 1 s. Se resta
la componente continua y se iguala la muestra final a la inicial para evitar
un salto en el borde. No se funden a silencio al repetirse. Los efectos cortos
empiezan y terminan en cero. El ajuste de RMS tiene techo de pico, por lo que
conserva el margen de transitorios cuando no puede alcanzar el RMS objetivo.

## Reproducción y límites de revisión

```sh
python3 tools/make_cinematic_sfx.py --fetch --manifest docs/AUDIO_CINEMATIC_MANIFEST.json
python3 tools/make_cinematic_sfx.py build/cinematic-preview --only cinematic/heartbeat ui/stamp
python3 tools/check_audio.py --report build/audio_check.json
```

Solo `--fetch` accede a la red. Sin esa opción, una fuente ausente o con hash
distinto produce un error. El generador solo puede escribir los ocho nombres
catalogados; no reexporta ni modifica efectos anteriores.

Se comprueban formato, duración, RMS, pico, componente continua, extremos y
unión de bucles. La selección evita fuentes descritas como anuncios o sintonía
de emisoras con habla. La revisión de esta sesión usa procedencia y análisis
técnico; no se presenta como escucha humana ni garantiza por sí sola que un
fondo urbano no tenga algún ruido lejano reconocible.
