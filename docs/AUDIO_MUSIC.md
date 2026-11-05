# Música de los niveles

Cada nivel tiene su propio tema, y los menús el suyo, en `assets/music/`. El del nivel suena en
bucle durante la partida, sigue durante la pausa (para ajustar su volumen de oído) y se desvanece
al ganar o perder. El del menú continúa de una pantalla a otra. El volumen es la barra **MÚSICA** de
Opciones (desde el menú principal o desde la pausa), y se guarda con la partida.

| Nivel | Archivo | Título | Paisaje y momento | Carácter |
| --- | --- | --- | --- | --- |
| Menús | `menu.ogg` | Fogata en el rancho | Calma antes de salir | Guitarra de dedos junto al fuego, silbido y armónica |
| 1-1 | `ruta_1_1.ogg` | Polvo al ocaso | Atardecer, viento; el comienzo | Western melancólico sin prisa: guitarra al galope, contrabajo y silbido con eco |
| 1-2 | `ruta_1_2.ogg` | Lluvia de plomo | Atardecer, lluvia; más zombis | Más rápido y tenso: guitarra corrida, tambor, sonaja y armónica |
| 1-3 | `ruta_1_3.ogg` | Campo santo | Cementerio; el respiro del juego | Muy lento e inquietante: armonio, cuerda grave, campana lejana y silbido |
| 1-4 | `ruta_1_4.ogg` | Luna sin dueño | Noche, viento; el salto de dificultad | Guitarra en trémolo sobre cuerda grave, latido y silbido alto |
| 1-5 | `ruta_1_5.ogg` | Último duelo | Pueblo fantasma, tormenta; el jefe | Duelo final: rasgueos, tambores de guerra y trompeta |

## Derechos

Los seis temas se componen y se sintetizan en `tools/make_music.py`: las notas están escritas
en ese archivo y cada sonido se calcula ahí (cuerda pulsada Karplus-Strong, armónicos, ruido
filtrado). No usan grabaciones, bancos de sonidos ni fragmentos de otras obras, así que no hay
licencias de terceros que cumplir ni atribuciones que dar. Toman de la música western solo el
estilo y la instrumentación; las melodías y sus armonías son propias de este proyecto.

## Regenerar

```sh
python3 tools/make_music.py                  # Los seis
python3 tools/make_music.py --only ruta_1_3  # Uno
```

Tarda unos minutos y necesita FFmpeg con libvorbis, solo para codificar. **Compilar y jugar no
lo necesitan:** los `.ogg` están en el repositorio y se incrustan en el ejecutable. El generador
actualiza `AUDIO_MUSIC_MANIFEST.json`, y `tools/check_audio.py` comprueba en cada compilación que
cada nivel tenga un tema distinto y que cada archivo coincida con su hash.

## Técnica

Vorbis estéreo a 22050 Hz, calidad 3: unos 550 KB por tema. Para que el bucle no se note:

- **En la música:** el último compás lleva al primero (bajo que camina, nota de anticipación,
  redoble), y su acorde resuelve en el del inicio.
- **En la mezcla:** lo que sobrepasa el final (una nota, un eco, la reverberación) sigue al principio.
- **En el archivo:** el corte cae en el instante más silencioso antes del primer tiempo, no sobre
  un ataque, con 4 ms de fundido. `make_music.py` decodifica cada archivo y lo rechaza si su duración
  no es exacta o sus bordes no están en silencio.

Se reproducen con
`audio_music_play` (`src/engine/audio.h`), por transmisión desde la memoria, sin ocupar canales de
efectos. `MUSIC_VOLUME` en `src/config.h` fija cuánto queda por debajo de los efectos.

Las comprobaciones son técnicas (nivel, picos, costura, bandas de frecuencia). Si un tema no
convence al oído, se ajusta en su función de `make_music.py`: tempo, acordes, melodía y volúmenes
de cada instrumento están ahí.
