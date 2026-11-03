# Vaquera 2D

Juego 2D en **C + SDL2**: una vaquera de pixel art contra zombis, por niveles (1-1 a 1-5)
con cofres de recompensa, experiencia y niveles para ella y para los zombis. Sprites:
caminata (8 fotogramas de 42 × 67 px), salto (8 de 54 × 82), disparo (8 de 81 × 80), bala
(4 de 8 × 6), el zombi antidisturbios (caminata de 8, impacto de 3, muerte de 8 y ataque
de 6, de 72 × 72) y el cofre (6 de 72 × 72), sobre un paisaje del oeste por capas con un tema
por nivel. Hacia la izquierda se usa el mismo arte espejado.

## Jugar

```bash
./build.sh          # compila, prueba y deja el ejecutable en dist/
./dist/Vaquera2D
```

El juego abre en el **menú principal** (Jugar, Controles, Volumen, Salir), todo en pixel art
sobre el paisaje del primer nivel. **Volumen** tiene tres barras: General (todo), Personaje (lo
que hace o provoca: disparos, recargas, explosiones, provisiones) y Zombis (sus voces). Los
controles también se ven en el menú, en **Controles**:

| Tecla | Acción |
| --- | --- |
| `A` / `D` (o `←` / `→`) | Caminar |
| `Shift` + movimiento | Correr |
| `Espacio`, `W` o `↑` | Saltar (y subirse a una barricada baja) |
| Clic izquierdo | Disparar (mantenido: ráfagas del rifle) |
| `R` | Recargar (cuando el cargador no está lleno; tras una derrota, reintentar) |
| `Q` o clic derecho | Cambiar de arma (el SWAT), en cualquier momento |
| `E` | Poner dinamita en un muro alto, sentarse en una banca, o plantar dinamita en el suelo |
| `V` | Culatazo (un mazazo; cada 1.5 s): empuja y hiere a los zombis, corta alambre, rompe cajas; atrapado, golpea la cuerda |
| `U` | Si sangra, vendarse (mantener; detiene el sangrado en 1.5 s, caminando a la mitad de velocidad); si no, beber un galón de agua |
| `N` | Atravesar una barricada baja |
| `F` o clic central | Poder de nivel 3 (cada 15 s): granada del SWAT, disparo de rebote de la vaquera |
| `Esc` | Pausa: Continuar, Reiniciar nivel, Volumen, Controles, Salir al menú |
| `W`/`S`, `Enter` | Moverse y aceptar en los menús (`A`/`D` en personajes y volumen) |

Durante el nivel, el HUD muestra la vida, el arma con sus balas (o `RECARGANDO`), la dinamita,
el oro, los zombis vencidos y los metros a la salida. Mientras recarga puede caminar a media velocidad.
`--capturas DIR` guarda cada pantalla como BMP (menús, una pelea, un muro, la pausa, una
derrota) para revisar el arte sin jugar.

Hay **tres personajes**: la Vaquera (sus zombis sueltan cofres), el SWAT (cambia entre rifle
y escopeta) y el Héroe (cañón de plasma que atraviesa la armadura). Cada uno tiene su propio
nivel y progreso. Detalles, armas y la plantilla para dibujarlos en
[`docs/CHARACTERS.md`](docs/CHARACTERS.md).

Si se presionan izquierda y derecha a la vez, manda la última que se presionó.

El disparo se hace con los pies plantados: mientras dura no camina. Saltar lo cancela.
En el aire no se dispara. Tras cada bala recarga el cañón de mano (0.38 s, con el
arma en alto); un clic al terminar la recarga encadena otro disparo sin volver a
desenfundar, así que sale como máximo una bala cada 0.445 s. Del cañón salen
bocanadas de humo animadas (`smoke.c`) que suben, avanzan, crecen y se desvanecen. La bala sale de la boca del cañón, vuela recta a 900 px/s
y desaparece al salir de la pantalla (hasta 16 a la vez).

## Enemigo y daño

El zombi antidisturbios entra cojeando por el borde de la pantalla más lejano a ella, siempre hacia la vaquera, y se
detiene a 140 px de ella para atacarla con la garra (`attack.png`, 0.6 s): toma impulso
y el zarpazo pega en el cuadro 2, 0.2 s después de empezar. Pega si ella sigue a menos
de 180 px por delante; corriendo hacia atrás se alcanza a esquivar. Entre un ataque y
otro espera 0.8 s. Un disparo que lo hace retroceder le corta el ataque. Cada bala que
lo toca se queda en él y le quita vida, aunque la vaquera esté pegada a él (el choque se
mide en todo el recorrido de la bala, desde la mano). Cada bala saca chispas del peto. La
primera además lo hace retroceder (`hurt.png`, 0.25 s quieto); durante el medio segundo
siguiente las balas solo sacan chispas (`sparks.png`) y él sigue avanzando, para que una
ráfaga no lo deje tieso. La barra de vida
aparece al primer impacto, con marco metálico porque lleva armadura. La bala que lo
mata lo sacude con chispas y lo derriba (`death.png`, 0.7 s). Queda tendido 1.5 s y se
desvanece; lo que sigue lo decide el nivel (ver **Niveles, cofres y experiencia**).

El daño se calcula así (`src/game/damage.c`, valores en `config.h`):

```text
daño del arma  = 20 × (1 + 0.6 × (nivel − 1))      nivel 1: 20   nivel 2: 32   nivel 3: 44
daño recibido  = daño del arma × 100 / (100 + armadura)
```

Los zombis guardan la fracción de cada golpe (10.8 quita 10 y deja 0.8 para el siguiente),
así que ningún arma pierde daño al redondear, por ligeras que sean sus balas. En nivel 1, el
zombi común (sin arte todavía: 100 de vida, sin armadura) cae con 5 balas y el
antidisturbios (100 de vida, 85 de armadura, que para el 46 % del daño) con 10. Con el nivel
crecen su vida, su armadura y su garra (ver abajo).

### Vida de la vaquera

En nivel 1 tiene 100 de vida y 25 de armadura (`PLAYER_HEALTH`, `PLAYER_ARMOR`). La garra
del zombi usa la misma fórmula que el arma, con base 15 (`ZOMBIE_ATTACK_BASE`): en nivel 1
son 15, que la armadura deja en **12**, así que la derriban **9 zarpazos**. Cada golpe la empuja
hacia atrás unos 29 px y la hace parpadear en rojo 0.4 s. La barra de vida está arriba a
la derecha, con marco metálico por la armadura.

Sin vida, la vaquera queda en pie oscurecida (todavía no hay hoja de muerte), no responde
a los controles, el zombi deja de atacar y aparece «TE ALCANZÓ EL ZOMBI». `R` reintenta
el nivel y `Esc` vuelve al menú.

## Niveles, cofres y experiencia

Al abrir el juego aparece el **menú** con los niveles 1-1 a 1-5: cuántos zombis tiene cada
uno, de qué nivel, y si está completado o bloqueado. Cada nivel se abre al completar el
anterior. El progreso dura mientras el juego está abierto (todavía no se guarda).

Cada nivel es un **camino** hacia una salida (un portón con faroles) a 12–20 vistas de donde
empieza el personaje (19 000–31 000 px); el HUD muestra cuántos metros faltan. El mundo se
dibuja a 3 px por píxel de arte (`VIEW_SCALE`), así que se ve un tercio más de camino, y la
cámara deja al personaje en el primer tercio: unos 870 px por delante. Arriba, en la franja de
cielo, va el HUD. Lo que hay en cada camino está en la tabla de su nivel (`src/game/stages.c`),
distinta por tema:

- **Grupos de zombis** dormidos, de pie y respirando a la vista; despiertan juntos cuando hasta
  el más lejano está en pantalla, se giran hacia ella, se sacuden al despertar y dan un primer paso tambaleante.
  Mientras un grupo pelea no se puede seguir (`¡ACABA CON ELLOS!`); al vencerlo, `¡ADELANTE! →`.
  Cuando la rodean se forman en fila.
- **Zombi de élite** (desde 1-3): más blindado, garra más dura, tono rojizo; siempre deja cofre.
- **Corredores** (desde 1-2): manadas de zombis verdosos, frágiles y casi el doble de rápidos.
- **Emboscadas** (`¡EMBOSCADA!`): al llegar a ciertos puntos (casi siempre antes de un muro) entran zombis caminando desde fuera de la pantalla, por detrás y, si
  el camino está libre, por delante. Hasta vencerlos no se puede seguir, pero queda espacio
  para moverse (560 px más allá del punto).
- **Ataúdes** (de día y de noche; de noche hay más: 85 % de los sitios contra 40 %): un zombi encerrado que revienta la tapa cuando ella
  se acerca o le dispara. Cuenta en la misión. Mientras sigue dentro no se mueve ni se ve.
- **Barricadas bajas** de cuatro tipos: cajas, sacos de arena, troncos con estacas y valla de
  acero (aguantan más zarpazos en ese orden; la valla, el doble que las cajas). Se saltan, se
  sube uno encima (fuera del alcance de la garra) o se **atraviesan con N**. Los zombis las
  rompen a zarpazos y ella a culatazos.
- **Alambre de púas**: no detiene, pero si lo cruza sin cortarlo (por debajo de 70 px) la
  muerde cada 0.8 s: herida, sangrado y cojera. Se corta con 4 balazos o 2 culatazos (o una
  explosión). Al acercarse, el aviso dice qué hacer.
- **Red** (bajo las hojas): salta del suelo y se cierra alrededor de quien la pisa, que queda
  colgando y pataleando; ella sale con 3 culatazos a la cuerda (`V`) mientras los zombis la
  atacan; un zombi cuelga 4 s y cae herido.
- **Lazo**: el arbolito doblado se endereza de golpe y la levanta de un pie (un cuarto de vuelta
  y queda cabeza abajo); sale con 2 culatazos. Un zombi cuelga 5 s.
- **Placas de púas**: al pisarlas, 0.35 s después salen púas durante 0.8 s y hieren (con
  sangrado) a quien esté encima; luego se esconden y se rearman. Se evitan saltando.
- **Muros altos**: una empalizada que cierra el hueco entre las ruinas de una casa o, uno de
  cada dos, la puerta atrancada de un edificio que cruza el camino (iglesia, comisaría,
  herrería, establo; la fachada es decorado y queda tras volar la puerta); no se saltan y
  paran las balas. Se vuelan con **dinamita** (`E`; mecha de 2.5 s,
  hay que alejarse) o con un barril al lado; los zombis tardan mucho en tirarlos. La dinamita
  sale de cajas, de cajas de madera rotas y de la carreta. Lejos de muros y bancas, `E` la
  planta en el suelo: estalla como un barril, buena para un grupo que se acerca.
- **Barriles de pólvora**: un disparo los hace estallar; hieren a los zombis cerca (320 px hasta
  el borde del cuerpo), encienden barriles vecinos y rompen barricadas, muros, cajas y faroles;
  también la lastiman a ella. Dejan fuego en el suelo unos 2 s, que quema a quien lo pise.
- **Cajas de suministros**: llevan pintado en una etiqueta lo que tienen (bala, cruz roja,
  dinamita o moneda). 3 balazos o culatazos (o una explosión) y sueltan su botín: balas para el
  arma en mano, 20 % de vida (no si las rompe una explosión), una dinamita u oro (que se ve en
  el HUD y da experiencia). En 1-1 y 1-2 un aviso pide dispararles. El rebote de la vaquera
  atraviesa la primera caja y sigue a la siguiente.
- **Botellas en la cerca** (atardecer, pueblo): tiro al blanco; las tres dan experiencia.
- **Trampas para osos**: atrapan 3 s al zombi que las pisa y lo hieren; si las pisa ella, la muerden,
  sangra 5 s (pierde vida cada segundo aunque tenga armadura) y cojea 4 s; deja un rastro de
  sangre y el HUD muestra cuánto le queda de cada cosa. Se pueden saltar.
- **Faroles de aceite** (noche, pueblo): iluminan; derribados de un disparo dejan el suelo
  ardiendo 5 s, que quema a los zombis que pasan (y a ella).
- **Carreta de provisiones**: una vez por nivel, cargadores llenos, 35 % de vida y dinamita
  según el largo del nivel (1 corto, 2 medio, 3 muy largo).
- **Descanso**: una **banca** (`E` para sentarse) y, a unos pasos, una **fogata** (una de cada
  dos con una olla colgada de un palo sobre horquetas). Sentada recarga, una tras
  otra y con el arma en el regazo (2 s cada una), cada arma a la que le falte una bala, todas
  las veces que se siente; la primera vez
  en cada banca cura de 5 a 15. Junto a la fogata cura 1.5 cada 3 s. Cada curación muestra un
  aura verde con un `+`. Si se queda sentada un rato, empieza a cabecear. Se levanta al moverse,
  saltar, disparar o recibir un golpe.

**Clima** por nivel: viento en 1-1 y 1-4 (polvo, hojas y alguna planta rodadora), lluvia en
1-2 y 1-3 (gotas inclinadas que salpican en el camino, el cielo más oscuro) y tormenta en 1-5
(lluvia con viento y relámpagos).

**Estados** (bajo la vida en el HUD, como íconos pequeños con los segundos que quedan; al
pasar el mouse sobre uno se abre con su nombre y explicación): sangrado y lentitud de las
trampas, **rapidez** con el viento a favor y **lentitud** en contra (también a los zombis; el
viento sopla hacia la derecha), **lentitud** en el río (más contra la corriente), **calor** en 1-1
(reflejos de calor sobre el camino; el culatazo tarda 2.1 s en volver) y **mal presagio**: antes
del 38 % de las emboscadas avisa que puede haber una cerca. Algunas trampas (una de cada cuatro)
tienen un **cartel de cuidado** antes; si es de las que hacen sangrar, el aviso recuerda que `U`
la venda. Al vendarse su mano enrolla la venda en el muslo, vuelta a vuelta (`bandage.png` de cada
personaje).

**Agua**: **charcos** (sobre todo con lluvia) que salpican y hacen ondas al pisarlos, y **ríos**
que cruzan el camino con su corriente animada, poco profundos (el agua a los tobillos, el lecho
de arena a la vista) y siempre a 25 m o más de cualquier edificio (las casas del fondo tampoco
quedan sobre ellos): vadearlos va a la mitad de velocidad, para ella y para los zombis, con
el agua tapándoles los tobillos y salpicando a cada paso. Al salir del río queda **húmeda**
(gotea) hasta secarse: 8 s con calor, 11 s normal, 15 s con frío y 6 s junto a una fogata.

**Frío** (1-3 y 1-4, de noche): el culatazo tarda más y camina un poco más lento. Junto a una
fogata hay **calor agradable**: cura poco a poco. Pero con calor (1-1) la fogata no cura: da
**fatiga**; a los 10 s se mueve, golpea y dispara más lento, a los 15 s le da un **golpe de
calor** (la vista se nubla y arde) y a los 20 s se desmaya (se tambalea, se le doblan las rodillas y cae de bruces:
`faint.png`, `tools/make_faint.py`) y el nivel empieza de nuevo. Un **galón de agua**
(de las cajas con la etiqueta del galón, o uno en la carreta; se guarda en el inventario, junto
al oro en el HUD) se bebe con `U` cuando no sangra: 1.2 s llevándose el galón a la boca
(`drink.png` de cada personaje), caminando al 25 % de la velocidad; quita la fatiga y la deja **refrescada**
20 s, sin los efectos del calor. Mientras está **hidratada** se mueve un poco más rápido.

**Sed**: crece con el tiempo (el doble con calor, menos con frío) y un galón la quita. A los
40 (unos 40 s con calor) está **sedienta** (boca seca); a los 70, **deshidratada** (algo más
lenta, empieza a alucinar); a los 100, **alucinación**: zombis falsos, pálidos y parpadeantes,
entran caminando desde los bordes y se desvanecen al llegar a ella o al dispararles (la bala se
pierde), y a ratos se ve a sí misma, adelante, mirándola.

**Cuervos**: bandadas picoteando el camino. Se van volando, lejos de ella, si se acerca
caminando o al oír un disparo (900 px) o una explosión (1800 px). Se les puede disparar (en
vuelo cruzan la línea de tiro): caen, quedan en el suelo y se desvanecen; una explosión cerca
también los mata.

Lejos del camino, detrás, se ven casas (saloon, chozas, graneros, casas caídas, tanques de agua), más en el pueblo
fantasma; son solo fondo. El fuego, la fogata y las explosiones sueltan humo que sube; los faroles, el fuego y la fogata
iluminan alrededor.

Al vencer a un zombi, en cuanto cae al suelo, deja un **cofre** si el personaje tiene esa
habilidad (la vaquera; según `chest_every`), también el último del nivel. El cofre se abre al acercarse (`chest/open.png`, 6
cuadros) soltando chispas doradas (`sparks.png`: luz por la rendija, estallido de rayos y
destellos que suben), da su experiencia, se queda abierto un momento y se desvanece. Vencidos
todos (la **misión**), aparece el **cofre de la misión** en la salida; abrirlo completa el nivel.
La experiencia de un nivel solo cuenta al completarlo: reiniciar (`R`) o salir (`ESC`) antes
devuelve el progreso a como estaba al entrar, así que repetir un nivel a medias no sube de nivel.

El nivel se muestra en una **placa de pixel art en forma de pirámide invertida**: una franja
con remaches donde el juego escribe el número y, debajo, facetas con arista central que bajan
hasta una punta que señala a su dueño. Latón y cuero con estrella para la vaquera
(`sprites/ui/badge_player.png`), hierro oxidado y sangre seca con calavera para los zombis
(`sprites/ui/badge_zombie.png`); 17 × 19 px, dibujadas a 2 px por píxel. Va sobre cada cabeza, junto a
la barra de experiencia (arriba a la derecha, bajo la vida) y en el menú (apagada si el
nivel está bloqueado). Arriba a la izquierda, el nivel y la misión (zombis vencidos).

**Todo escala igual para los dos lados** (`src/game/progression.c`, valores en `config.h`):

| Con el nivel N | Vaquera | Zombi antidisturbios |
| --- | --- | --- |
| Vida | 100 × (1 + 0.6 × (N − 1)) | 100 × (1 + 0.6 × (N − 1)) |
| Armadura | 25 + 5 × (N − 1) | 85 + 8 × (N − 1) |
| Ataque | arma de nivel N: 20 × (1 + 0.6 × (N − 1)) | garra de nivel N: 15 × (1 + 0.6 × (N − 1)) |

Vida y daño crecen igual, así que **dos del mismo nivel pelean lo mismo en el nivel 1 que en
el 9** (unas 10 balas y 9 zarpazos). La dificultad la da la **diferencia de niveles**. El
arma y la armadura tienen su propio nivel (`weapon_level`, `armor_level`); por ahora siguen
al de la vaquera, pero las recompensas podrán subirlos aparte.

**Experiencia:** pasar del nivel N al N + 1 pide `120 × N^1.5` (120, 339, 624, 960…).

- **Matar un zombi** da `16 × su nivel`, con +25 % por cada nivel que esté por encima de
  ella y −25 % por cada uno por debajo (entre ×0.25 y ×1.75). Así repetir niveles fáciles
  rinde poco.
- **Un cofre** da una parte de lo que pide su nivel actual: `10 % × complejidad del nivel`,
  más cuanto más avanzada va la misión (×0.75 el primero, ×1.25 el último), con el mismo
  ajuste por diferencia de niveles. El último cofre de la misión vale el doble.

**Dificultad por nivel** (`src/game/stages.c`). No es lineal:

| Nivel | Zombis | Nivel de zombis | Complejidad | Pensado para |
| --- | --- | --- | --- | --- |
| 1-1 | 3 | 1 | 1.00 | Pelea pareja, para aprender |
| 1-2 | 4 | 2 | 1.10 | Pareja |
| 1-3 | 5 | **2** (uno menos) | 1.20 | Respiro: llega con nivel 3 |
| 1-4 | 5 | **4** (salta dos) | 1.35 | Subida de dificultad |
| 1-5 | 6 | 5, el último **6** (jefe) | 1.50 | El más exigente |

Jugando cada nivel una vez (todos los zombis y cofres), la vaquera sube un nivel por nivel
completado y llega a cada uno con el nivel de sus zombis o uno más: entre 7 y 12 balas
por zombi y entre 9 y 13 zarpazos para caer. `tests/test_progression.c` juega la campaña
y falla si algún nivel queda imposible o trivial; si cambias números, corre las pruebas.

## Requisitos (Ubuntu/Debian)

Para compilar:

```bash
sudo apt install build-essential pkg-config python3 libsdl2-dev libsdl2-ttf-dev libsdl2-mixer-dev
```

En Windows (MSYS2 UCRT64): `pacman -S mingw-w64-ucrt-x86_64-SDL2 mingw-w64-ucrt-x86_64-SDL2_ttf mingw-w64-ucrt-x86_64-SDL2_mixer`.

Para solo jugar en otra máquina basta con `libsdl2-2.0-0`, `libsdl2-ttf-2.0-0` y `libsdl2-mixer-2.0-0`
(en Windows, `build.sh` deja las DLL necesarias en `dist/`).
Los sprites, fuentes y sonidos van **dentro** del ejecutable: `dist/Vaquera2D` es un solo archivo.

## Compilación

`./build.sh` ejecuta en orden, y se detiene en el primer fallo sin tocar `dist/`:

1. Comprueba herramientas y SDL2.
2. `make test` — pruebas de lógica (entrada, animación, personaje), sin ventana.
3. `make` — compila `build/bin/Vaquera2D`.
4. `--verify` — valida los recursos incrustados.
5. `--smoke-test` — recorrido automático: caminar a la derecha, saltar caminando,
   regresar a la izquierda, detenerse, disparar una vez y seguir la bala hasta que
   sale de la pantalla, mientras el zombi avanza (sin ventana).
6. Copia el ejecutable a `dist/Vaquera2D`.

`./build.sh --clean` compila desde cero. Durante el desarrollo también sirven
`make`, `make test`, `make run` y `make clean`.

### Desarrollo con recarga automática

```bash
make watch
```

Compila, abre el juego y se queda vigilando `src/`, `tests/`, `assets/`, `tools/` y el
`Makefile`. Cada vez que guardas un archivo (código o PNG) recompila, corre las pruebas
y reabre el juego con el cambio. Si algo falla, muestra el error y deja abierta la
versión anterior. `Ctrl+C` lo detiene y cierra el juego. No toca `dist/`: cuando
quieras publicar, usa `./build.sh`.

### Windows (VS Code)

1. Editas código en `src/`.
2. `Ctrl+Shift+B` (**Compilar**) para comprobar que compila.
3. **Jugar** o `F5` para probarlo.
4. Cuando quieras generar la versión final en `dist/`, corres la tarea
   **Build completo (build.sh)**, que es el equivalente a `./build.sh` de Linux.

## Sonido

Efectos de 8 bits con SDL2_mixer. `tools/make_sfx.py` los sintetiza (ruido tipo LFSR y
ondas cuadradas, como un chip de consola) y escribe `assets/sounds/player/*.wav` y
`assets/sounds/world/*.wav` (la explosión de un barril y las provisiones); al compilar se
incrustan en el ejecutable. Suenan el disparo (`player/shot`) y, enseguida, la
recarga del cañón de mano (`player/reload`: baqueta, bala asentada y martillo), que
dura lo mismo que la espera entre disparos (`PLAYER_SHOOT_RELOAD_TIME`). El zombi tiene
tres voces, todas sacadas de una misma grabación con `tools/crush_sfx.py` (ver abajo): al
aparecer (`zombie/spawn`), cada 6 s mientras vive (`zombie/idle`,
`ZOMBIE_GROWL_INTERVAL`) y al morir (`zombie/death`, con el tono cayendo). Se
regeneran así desde `recordings/zombie_growl.wav`:

```bash
CLEAN="--bits 16 --rate 22050 --gate -20"   # Voz limpia: sin triturar
python3 tools/crush_sfx.py convert recordings/zombie_growl.wav zombie/spawn --pitch -4 $CLEAN
python3 tools/crush_sfx.py convert recordings/zombie_growl.wav zombie/idle --start 0.35 --end 1.05 --pitch -7 --fade 0.15 $CLEAN
python3 tools/crush_sfx.py convert recordings/zombie_growl.wav zombie/death --pitch -2 --glide -12 --fade 0.4 $CLEAN
```
 Para cambiar los sintetizados, edita su función en `tools/make_sfx.py`, corre `python3 tools/make_sfx.py`
y recompila. El volumen está en `SFX_VOLUME` (`src/config.h`). Si no hay dispositivo
de audio, el juego sigue sin sonido.

### Grabar tus propios sonidos

`tools/crush_sfx.py` graba del micrófono (o toma un mp4, m4a, mp3, wav...) y lo
convierte en efecto de 8 bits: recorta el silencio, cambia el tono, normaliza el
volumen y lo "tritura" (menos niveles y menos muestras por segundo). Necesita ffmpeg
(`sudo apt install ffmpeg` o, en MSYS2, `pacman -S mingw-w64-ucrt-x86_64-ffmpeg`).

```bash
python3 tools/crush_sfx.py record zombie/growl --pitch -4 --play      # Enter para terminar
python3 tools/crush_sfx.py convert grabacion.mp4 zombie/growl --bits 4
python3 tools/crush_sfx.py devices                                    # Micrófonos
```

`--pitch` en semitonos (negativo: más grave y lento), `--bits` de 2 a 8 (menos: más
áspero; 16 guarda en 16 bits, sin nada de grano, para voces limpias), `--rate` en Hz (menos: más granulado), `--start`/`--end` para quedarse con un
tramo (en segundos, ya sin el silencio), `--glide` para que el tono siga cayendo (o
subiendo) mientras suena `--fade` para la duración del desvanecido final y `--gate` para la puerta de ruido (baja lo que
queda N dB por debajo de lo más fuerte; -30 por defecto). Antes de reducir la frecuencia
filtra los agudos que no caben, para que no se doblen como interferencia. Antes de
procesar quita el golpe de encendido del micrófono y los graves por debajo de 90 Hz.
El resultado queda en
`assets/sounds/<carpeta>/<nombre>.wav` y entra al juego al recompilar. La grabación original se guarda
en `recordings/` (no se sube a git) para volver a procesarla con otras opciones. En VS Code:
tareas **Grabar sonido (8 bits)** y **Convertir archivo a sonido (8 bits)**.

## Mundo

El nivel es una franja de 96 000 px (unas 100 pantallas) dividida en tramos de 480 px.
La vaquera empieza a la mitad y la cámara la sigue centrada (se detiene en los extremos).
Cada tramo se genera a partir de `WORLD_SEED`, su número y el **tema** del nivel: hasta dos
decorados grandes (cactus, rocas, cercas, árboles secos…) y matas de pasto. Solo existen en
memoria los tramos a la vista más uno a cada lado: al caminar a la izquierda se cargan los
de la izquierda y se descartan los que quedaron atrás, y al revés. Volver a un lugar lo
genera idéntico. Tamaños y semilla en `src/config.h` (`WORLD_*`).

Detrás, el **paisaje** del tema (`assets/backgrounds/<tema>/`): cielo, mesetas, colinas
lejanas y cercanas, y el suelo, cada capa con su paralaje (0, 0.15, 0.35, 0.6 y 1), y niebla
en los temas nocturnos. 1-1 y 1-2 son al **atardecer**, 1-3 en el **cementerio**, 1-4 de
**noche** y 1-5 en el **pueblo fantasma**; los decorados cambian de paleta con el tema. Todo
en [`docs/LANDSCAPE.md`](docs/LANDSCAPE.md).

## Estructura

```text
Makefile, build.sh
src/
  main.c                 Arranque, ciclo del juego (paso fijo de 60 Hz), --verify, --smoke-test
  config.h               Constantes: ventana, escala, velocidades, colores
  engine/                Motor reutilizable
    platform.c/.h        Ventana, renderer, vsync, lectura de teclado y mouse (SDL)
    input.c/.h           Acciones, flancos de tecla, prioridad de dirección (sin SDL)
    animation.c/.h       Animaciones por fotogramas en una hoja de sprites (sin SDL)
    assets.c/.h          Texturas a partir de los recursos incrustados
    text.c/.h            Texto pre-renderizado con SDL2_ttf
    audio.c/.h           Efectos de sonido con SDL2_mixer, con volumen general y por grupo (silencio si no hay audio)
    pixfont.c/.h         Fuente pixel propia (sprites/ui/font): mayúsculas con acentos, escalas enteras
  game/                  Lo propio de este juego
    controls.c/.h        Teclas y botones del mouse asignados a cada acción
    player.c/.h          Estados del personaje: idle / walk / run / jump / land / shoot / dead, vida y empujón (sin SDL)
    movement.c/.h        Caminar, correr y límites de pantalla (sin SDL)
    jump.c/.h            Arco del salto: altura y tiempo fijos, desde y hacia lo que pisa (sin SDL)
    shoot.c/.h           Secuencia del disparo: momento de la bala y disparos encadenados (sin SDL)
    bullet.c/.h          Balas en vuelo con el daño, alcance y color de su arma (sin SDL)
    bullet_render.c/.h   Dibujo de las balas
    damage.c/.h          Daño por nivel (arma y garra) y reducción por armadura (sin SDL)
    zombie.c/.h          Zombi: tipos y nivel (vida, armadura, garra), avance, ataque, retroceso y muerte (sin SDL)
    combat.c/.h          Balas contra el zombi y garra contra la vaquera (sin SDL)
    zombie_render.c/.h   Dibujo del zombi: espejo, desvanecido y barra de vida
    effects.c/.h         Efectos de una sola pasada, como las chispas en la armadura (sin SDL)
    effects_render.c/.h  Dibujo de los efectos
    player_render.c/.h   Dibujo del personaje con su arte (recorte del fotograma, espejo, altura, parpadeo rojo)
    health_bar.c/.h      Barra de vida compartida (vaquera y zombi)
    smoke.c/.h           Humo del disparo: bocanadas que suben, avanzan, crecen y se desvanecen (sin SDL)
    smoke_render.c/.h    Dibujo del humo en la cuadrícula de pixel art
    camera.c/.h          Cámara centrada en la vaquera, limitada a los extremos del mundo (sin SDL)
    world.c/.h           Tramos procedurales: decorados por semilla y tema, carga/descarga según la vista (sin SDL)
    props.c/.h           Los decorados: hoja, tamaño de cuadro y variantes de cada uno (sin SDL)
    themes.c/.h          Capas del fondo (fila, paralaje, tamaño) y los temas con sus decorados (sin SDL)
    scene.c/.h           Dibujo del paisaje: capas del tema con paralaje y decorados de los tramos cargados
    hud.c/.h             Menú principal, controles, volumen, personajes, niveles, pausa y HUD del nivel, en pixel art
    ui.c/.h              Piezas de la interfaz: tableros, botones, teclas, iconos, barras y texto pixel
    settings.c/.h        Volúmenes por grupo y listas de menú (sin SDL)
    progression.c/.h     Niveles y experiencia: estadísticas por nivel, curva de XP y recompensas (sin SDL)
    stages.c/.h          Los niveles 1-1 a 1-5: su camino (grupos, élite, terreno), nivel, cofres y complejidad (sin SDL)
    stage_run.c/.h       Una partida de un nivel: el camino, grupos que despiertan y detienen, cofres, XP y salida (sin SDL)
    terrain.c/.h         Barricadas, barriles de pólvora, carreta de provisiones y salida (sin SDL)
    terrain_render.c/.h  Dibujo del terreno del camino
    chest.c/.h           Cofre: cerrado, abriéndose al acercarse, abierto y desvanecido (sin SDL)
    chest_render.c/.h    Dibujo del cofre
    menu.c/.h            Selección de nivel en el menú (sin SDL)
    characters.c/.h      Los personajes: habilidad, armas y carpeta de su arte (sin SDL)
    weapons.c/.h         Las armas: daño, recarga, perdigones, alcance, armadura y color (sin SDL)
    char_select.c/.h     Selección de personaje (sin SDL)
    character_skin.c/.h  Hojas de cada personaje: las suyas o, si faltan, las de la vaquera teñidas
assets/                  Sprites, fondos, sonidos y fuentes: mapa completo en docs/ASSETS.md
tools/embed_assets.py    Convierte PNG/TTF/WAV en datos C (solo biblioteca estándar de Python)
tools/sprite_style.py    Compara el nivel de detalle de una hoja con la vaquera
tools/make_sfx.py        Sintetiza los efectos de 8 bits en assets/sounds/
tools/crush_sfx.py       Graba o convierte audio a efecto de 8 bits (usa ffmpeg)
tools/make_sprites.py    Genera en pixel art las placas de nivel y las chispas del cofre
tools/make_terrain.py    Genera el terreno del camino (barricadas, muro, barriles, dinamita, cajas, botellas,
                         trampas, ataúdes, faroles, fuego, banca, fogata, carreta, salida) y efectos
tools/make_ui.py         Genera la fuente pixel y el kit de interfaz (tableros, botones, teclas, iconos, armas)
tools/make_sit.py        Genera las hojas de sentado, de frente (sentarse, descansar, recargar sentada, cabecear)
tools/make_sun.py        Pinta el sol entero en los cielos de atardecer y pueblo fantasma
tools/make_terrain.py    (también el cuervo: sprites/crow/crow.png)
tools/make_care.py       Beber y vendarse de la vaquera (drink.png, bandage.png) a partir de su hoja de disparo
tools/make_faint.py      El desmayo de la vaquera y el SWAT (faint.png) a partir de su hoja de caminar
tools/make_melee.py      El culatazo de la vaquera (melee.png) a partir de su hoja de disparo
tools/make_powers.py     Arte de los poderes de nivel 3: las pistolas duales de la vaquera y la granada
tools/make_character_base.py  Genera la base (maniquí) de los personajes y sus guías
tools/check_landscape.py Revisa las capas de un tema de paisaje antes de usarlas
tests/                   Pruebas de la lógica pura
docs/ASSETS.md           Mapa de recursos: carpetas, nombres, qué los genera y qué comprueba --verify
docs/SPRITES.md          Especificación para dibujar sprites (tamaños, pivotes, paleta)
docs/LANDSCAPE.md        Especificación del paisaje: capas con paralaje, paletas y temas por nivel
docs/ZOMBIE.md           Especificación del zombi antidisturbios
docs/CHARACTERS.md       Personajes: habilidades, armas, plantilla, base y cómo dibujar uno nuevo
docs/templates/          La base de los personajes (la vaquera en grises), para dibujar encima
build/                   Generado (temporales)
dist/                    Generado (ejecutable final)
```

## Hojas de sprites: cómo se separan los fotogramas

Tamaños, pivotes, paleta y formato para dibujar sprites nuevos: [`docs/SPRITES.md`](docs/SPRITES.md).

El PNG no tiene marcas entre fotogramas: es una tira de cuadros **del mismo tamaño**
pegados en una fila. El código sabe el tamaño del cuadro (`config.h`) y recorta el
fotograma `i` como el rectángulo `(i × ancho, 0, ancho, alto)` al dibujar
(`player_render.c`). Por eso el ancho de la hoja debe ser exactamente
`ancho del cuadro × número de fotogramas`; `--verify` lo comprueba.

Cada animación (`AnimationDef` en `src/game/player.c`) indica además su **pivote**:
`anchor_x`, el centro horizontal del cuerpo, y `ground_y`, la fila donde las botas
tocan el suelo. Así hojas de distinto tamaño quedan alineadas y el cuerpo no se
desplaza al espejarlo.

El salto usa la misma hoja en dos animaciones: los fotogramas 0–5 siguen el arco
(el fotograma depende de qué tanto avanzó el salto, no del tiempo) y los 6–7 son
el aterrizaje. El disparo elige su fotograma desde `shoot.c`: 0–2 desenfunda, 3 apunta,
4 dispara (aquí sale la bala: `player.shot_fired`), 5–6 retroceso (el humo no va en la
hoja: lo dibuja `smoke.c`) y 7 enfunda.

## Añadir una mecánica

1. Coloca la hoja en `assets/sprites/characters/cowgirl/<nombre>.png` (PNG RGBA de 8 bits,
   fotogramas iguales en una fila, mirando a la derecha), y la de cada personaje con el mismo
   nombre en su carpeta. Se incrusta sola al compilar.
2. Crea `src/game/<nombre>.c/.h` con la lógica (sin SDL, para poder probarla) y su
   prueba en `tests/test_<nombre>.c`. Añade el `.c` a `CORE_SRC` en el `Makefile`.
3. Si necesita tecla o botón, agrega la acción en `src/engine/input.h` y la entrada en
   `src/game/controls.c` (`BIND_KEY` para teclas, `BIND_MOUSE` para botones del mouse).
4. En `src/game/player.c`, añade el estado y su `AnimationDef` (tamaño de cuadro,
   fotogramas, fps y pivote), y regístrala en `ANIMATIONS` para que `--verify` la revise.
