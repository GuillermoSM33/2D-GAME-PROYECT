# Explosiones, plasma, recompensas e interfaz

`tools/make_designed_sfx.py` sustituye trece efectos nuevos mediante edición
y mezcla de grabaciones de mecanismos y materiales, junto con los sonidos
originales del juego. No utiliza secuencias de notas ni ondas cuadradas para
representar las acciones físicas.

La salida es WAV PCM de 16 bits, mono a 22050 Hz. Los 16 bits evitan que las
colas de metal y los clics suaves acumulen ruido de cuantización; el carácter
de los sonidos originales sigue presente en sus capas. El disparo original
de la vaquera tiene RMS cercano a 0.30 y su recarga, a 0.118; estos son los
puntos de referencia de volumen. Los sonidos pequeños quedan por debajo y
los picos nuevos no superan 0.90.

## Fuentes

Las capas mecánicas externas proceden de **rubberduck**, paquete
[100 CC0 metal and wood SFX](https://opengameart.org/content/100-cc0-metal-and-wood-sfx),
publicado con licencia **CC0** en OpenGameArt. Su
[archivo original](https://opengameart.org/sites/default/files/100-CC0-wood-metal-SFX.zip)
se guarda, sin modificaciones, en
`recordings/cc0_foley/100-CC0-wood-metal-SFX.zip`. No se necesita para jugar ni
para compilar: solamente para volver a editar los sonidos.

La capa principal de ambas explosiones procede de **Félix Blume**,
[Dynamite explosion in the mountain](https://freesound.org/people/felix.blume/sounds/251401/),
una grabación de dinamita usada para romper roca en Chacaltaya, Bolivia.
La página confirma licencia **CC0**. Se conserva su
[MP3 de preescucha de alta calidad](https://cdn.freesound.org/previews/251/251401_1661766-hq.mp3)
en `recordings/cc0_foley/dynamite_source.mp3` y la página de licencia en
`recordings/cc0_foley/dynamite_page.html`. Se utilizan los segundos 0.025 a
1.90: ataque real y primeras reflexiones, sin los treinta segundos de ambiente
posterior. SHA-256 del MP3:
`03ede4462a6657fdd181fa65f9aab9d6fcc181be6cdbb2fb461ee2aa638da318`.
La granada es una adaptación de esa detonación con fragmentación de metal:
no se presenta como una grabación documental de una granada.

Grabaciones de rubberduck utilizadas: `lock_open_01`, `keys_01`, `metal_close_01`,
`metal_falling_01`, `metal_hit_01`, `metal_hit_02`, `metal_spring_01`,
`metal_slam_01`, `wood_breaking_01`, `wood_falling_01`, `wood_close_01` y
`wood_squeak_01` (todos `.ogg`). Los cambios consisten en cortes, cambios de
velocidad, filtrado, envolventes, superposición y ajuste de volumen.

Las otras capas derivan de los recursos internos ya existentes:
`player/shot`, `player/reload`, `world/explosion`, `world/wood`, `world/glass`
y `world/fuse`. Se leen sin escribirlos. El generador comprueba por SHA-256
que los once archivos protegidos del personaje, mundo y zombis se mantienen.
La autoría de las nuevas mezclas es del proyecto; las grabaciones base de
rubberduck siguen siendo CC0. No se atribuye a este paquete el material
interno anterior ni se altera su procedencia.

## Qué se escucha

| Archivo | Diseño |
| --- | --- |
| `world/grenade_explosion` | Detonación real acortada con fragmentos de carcasa metálica y una capa tenue del barril original |
| `world/dynamite_explosion` | Dinamita real sobre roca, presión grave y escombros que caen después |
| `world/ambush` | Tensión de resorte, golpe de chapa grave y madera, sin una voz de zombi añadida |
| `world/chest` | Desenganche del cerrojo, bisagra de madera y cierre con piezas pequeñas de metal |
| `world/level_up` | Mecanismo de insignia, golpe metálico y piezas que se asientan |
| `world/victory` | Golpe de madera, metal más largo y tintineo de llaves/piezas |
| `weapons/plasma_shot` | Ataque y masa del cañón original, arco áspero de alta frecuencia y carcasa resonante |
| `weapons/plasma_reload` | Apertura, venteo de energía y cierre de celda, sin arpegio |
| `weapons/plasma_empty` | Mecanismo seco que falla, resorte y chisporroteo corto |
| `weapons/ricochet` | Impacto metálico y rebote agudo de resorte con fragmentos |
| `ui/move`, `ui/confirm`, `ui/back` | Clics de cerrojo y cierre mecánico; cada gesto tiene orden y peso propios |

Las resonancias breves del plasma son filtros amortiguados excitados por un
impacto real de metal. No se sintetiza una melodía ni se usa un oscilador
cuadrado como fuente dominante.

## Reproducir la edición

Requiere Python 3 y ffmpeg, disponibles tanto en Linux como en MSYS2 UCRT64.
Desde la raíz del repositorio:

```sh
python3 tools/make_designed_sfx.py
python3 tools/make_designed_sfx.py --only world/chest weapons/plasma_reload
python3 tools/make_designed_sfx.py build/audio-designed-preview
python3 tools/make_designed_sfx.py --review --manifest docs/AUDIO_DESIGNED_MANIFEST.json
python3 tools/make_designed_sfx.py --fetch
```

La carpeta alternativa sirve para escuchar una revisión antes de copiarla
al juego. `--source-assets` permite elegir los originales, y `--foley-zip`,
el paquete CC0. Cada salida incluye su duración, RMS y pico. Después se usa
`./build.sh` para incrustar los WAV en el ejecutable.

`--fetch` descarga únicamente las dos fuentes CC0 que falten y comprueba sus
SHA-256 antes de guardarlas. Si ya existen y coinciden, no hay tráfico de red;
si un archivo tiene otro hash se conserva para revisión en lugar de sobrescribirlo.

`--review` escribe trece comparaciones A/B en `build/designed_review/`, cada
una con una fuente real seguida por el resultado propuesto, y un índice con
los tiempos. En plasma, cuya descarga no existe en la realidad, A es el cañón
original del juego o el mecanismo real que sirve de base. El manifiesto
registra autores, licencias, hashes de fuentes y resultados, formato y niveles.

## Auditoría de realismo

Se aplicaron las seis comprobaciones solicitadas. No se declara una escucha
humana que no se haya realizado: las comparaciones se prepararon para poder
escuchar, y las revisiones automáticas comprueban fuentes y estructura.

1. **¿Realmente suena así en la vida real?** El cerrojo, la bisagra, el metal y
   la detonación proceden de grabaciones de esas acciones. La granada es una
   adaptación de dinamita, los premios son señales de juego y el plasma es
   ficción; estos casos se identifican sin atribuirles autenticidad documental.
2. **¿Lo que hice suena sintético o real?** Las acciones físicas tienen material
   grabado como fuente dominante. En plasma se admite diseño eléctrico; su
   cuerpo deriva del cañón y su mecanismo sigue siendo grabado. Ningún efecto
   nuevo de este grupo se representa mediante pitidos o arpegios.
3. **¿Cumple el estándar anterior?** Los originales protegidos conservan sus
   bytes y las mezclas nuevas mantienen mono a 22050 Hz y niveles contenidos.
   Guardar a 16 bits conserva las colas de las grabaciones sin añadir hiss.
4. **¿Puedo mejorarlo?** Se reemplazó una primera mezcla de explosiones basada
   sobre todo en el barril por una detonación real. Se corrigieron también los
   cortes del cerrojo: su apertura fuerte ocurre a 0.447 s, y el fragmento
   0.38–0.57 s conserva el gesto que se perdía al tomar solo el principio.
5. **¿Lo comprobé frente a sonido real?** Se compararon las fuentes grabadas y
   los cortes usados: el resorte dura 0.331 s; el golpe metálico 0.116 s; la
   bisagra 0.279 s. Se conservaron sus ataques y se situaron según la acción,
   sin estirar un clic hasta cubrir una animación completa. Hay trece WAV A/B
   para una comprobación perceptiva adicional; no se sustituye esa escucha
   por una conclusión basada únicamente en RMS.
6. **¿Tomé el tiempo necesario?** Se revisaron dos versiones de las explosiones
   y los puntos de corte mecánicos antes de generar la versión entregada.
   El resultado se puede regenerar y revisar por separado sin tocar originales.

| Función | Fuente y gesto comprobable | Clasificación |
| --- | --- | --- |
| `grenade` | Dinamita real, evento comprimido en tiempo; carcasa metálica después del ataque | Adaptación física, no registro específico de granada |
| `dynamite` | Detonación real contra roca y reflexiones; escombros discretos | Base física grabada |
| `ambush` | Tensión de resorte y golpe de chapa grave | Señal dramática formada por objetos reales |
| `chest` | Cerrojo 0.38–0.57 s de su fuente; bisagra; madera apoyada; piezas pequeñas | Foley físico compuesto |
| `level_up` | Cierre de mecanismo, golpe de insignia y llaves | Señal de recompensa formada por objetos reales |
| `victory` | Madera, metal y piezas que se asientan | Señal de recompensa formada por objetos reales |
| `plasma_shot` | Cañón original, mecha filtrada y carcasa metálica grabada | Ficción diseñada; sin pretensión de realismo documental |
| `plasma_reload` | Cerrojo, venteo y cierre de celda | Mecanismo grabado con energía ficticia |
| `plasma_empty` | Mecanismo seco y resorte; chispa breve | Mecanismo grabado con energía ficticia |
| `ricochet` | Ataque metálico y resorte agudo, cola breve | Adaptación física de rebote |
| `ui_move` | Solo la apertura efectiva del cerrojo, sin el manejo inicial de llaves | Interfaz mecánica |
| `ui_confirm` | Cerrojo seguido de cierre, dos gestos breves | Interfaz mecánica |
| `ui_back` | Cierre y liberación en orden inverso | Interfaz mecánica |
