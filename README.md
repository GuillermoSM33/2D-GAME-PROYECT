# THE MIRACLE

*(Antes Vaquera 2D.)* La historia está en [docs/LORE.md](docs/LORE.md).

Juego 2D en **C + SDL2**: una vaquera de pixel art contra zombis, por niveles en dos rutas (1-1 a 1-5 en el desierto, 2-1 a 2-5 en la ciudad vecina)
con cofres de recompensa, experiencia y niveles para ella y para los zombis. Sprites:
caminata (8 fotogramas de 42 × 67 px), salto (8 de 54 × 82), disparo (8 de 81 × 80), bala
(4 de 8 × 6), 25 familias de zombis con variantes normales y corredoras (cuadros de
72 × 72) y el cofre (6 de 72 × 72), sobre un paisaje del oeste por capas con un tema
por nivel. Hacia la izquierda se usa el mismo arte espejado.

## Jugar

```bash
./build.sh          # compila, prueba y deja el ejecutable en dist/
./dist/TheMiracle
```

El juego abre en el **menú principal** (Jugar, Almanaque, Controles, Opciones, Salir), todo en pixel art
sobre el paisaje del primer nivel. **Opciones** tiene tres barras de volumen: General (todo), Personaje (lo
que hace o provoca: disparos, recargas, explosiones, provisiones) y Zombis (sus voces), y la fila
**Pantalla** (Ventana o Completa). Los controles también se ven en el menú, en **Controles**:

| Tecla | Acción |
| --- | --- |
| `A` / `D` (o `←` / `→`) | Caminar |
| `Shift` + movimiento | Correr |
| `Espacio`, `W` o `↑` | Saltar |
| Clic izquierdo | Disparar (mantenido: ráfagas del rifle, las duales siguen turnándose) |
| `R` | Recargar (cuando el cargador no está lleno; tras una derrota, reintentar) |
| `Q` o clic derecho | Cambiar de arma (el SWAT), en cualquier momento |
| `E` | Poner dinamita en un muro alto, sentarse en una banca, o plantar dinamita en el suelo |
| `V` | Culatazo (un mazazo; cada 1.5 s): empuja y hiere a los zombis, corta alambre, rompe cajas; atrapado, golpea la cuerda |
| `U` | Si sangra, vendarse (mantener; detiene el sangrado en 1.5 s, caminando a la mitad de velocidad); si no, beber un galón de agua |
| `N` | Saltar una barricada (son más altas que el salto normal; también se pueden romper) |
| `K` | SWAT: rifle en ráfagas o tiro a tiro (15 balas) |
| `F` o clic central | Poder de nivel 3 (cada 15 s): granada del SWAT, disparo de rebote de la vaquera |
| `B` | Abrir el almanaque durante la partida, también mientras está pausada |
| `L` | Encender o apagar la linterna durante el nivel; ilumina hacia donde mira; empieza encendida de noche y de día se ve más tenue |
| `Esc` | Pausa: Continuar, Reiniciar nivel, Almanaque, Opciones, Controles, Salir al menú |
| `F11` | Pantalla completa o ventana, en cualquier momento |
| `W`/`S`, `Enter` | Moverse y aceptar en los menús (`A`/`D` en personajes y opciones) |

**Pantalla:** la ventana abre al 85 % del área útil del monitor y se puede agrandar o
maximizar; el juego se escala sin suavizado y conserva su forma (con franjas si el monitor
tiene otra proporción). La pantalla completa usa la resolución del escritorio, sin cambiar
el modo de video, y se recuerda entre partidas en `~/.local/share/TheMiracle/TheMiracle/`
(Linux) o `%APPDATA%\TheMiracle\TheMiracle\` (Windows).

**Pausa automática:** si la ventana pierde el foco durante un nivel (clic fuera de ella,
`Alt+Tab`, minimizarla), el nivel se pausa como con `Esc`.

Durante el nivel, el HUD ocupa solo la franja del cielo, en tres columnas: a la izquierda
tu nivel, vida y experiencia, con los suministros y los estados debajo; al centro la ruta,
el reloj y lo que falta, con las alertas graves debajo; a la derecha el arma y sus balas, con
el cambio de arma (`Q`), el poder (`F`) y el aviso de guardado debajo. Lo secundario aparece
solo cuando aplica. Los estados llevan icono y explicación al pasar el mouse, y el mouse sobre
la misión abre las metas de sus tres estrellas. Los números muy largos reducen su escala para
no salirse del panel.
Mientras recarga puede caminar a media velocidad.
`--capturas DIR` guarda pantallas como BMP para revisar el arte sin jugar: menús,
combate, obstáculos, pausa, derrota, clima, farol, linterna y destello de explosión,
además de las siete páginas completas del catálogo (`23_catalogo_01` a `23_catalogo_07`).
El arte del laboratorio, el rifle de los mercenarios y las herramientas para
trabajar las cinemáticas están en [docs/CINEMATICS.md](docs/CINEMATICS.md).
`52_sheriff_rework`, `52_sheriff_disparo` y `52_sheriff_recarga_0` a `_7` muestran
la sheriff y la recarga del revólver dentro del escenario.

Hay **tres personajes**: la Vaquera (sus zombis sueltan cofres), el SWAT (cambia entre rifle
y escopeta) y el Héroe (cañón de plasma que atraviesa la armadura; aún en desarrollo, todavía no
se puede jugar). Cada uno tiene su propio
nivel y progreso. Detalles, armas y la plantilla para dibujarlos en
[`docs/CHARACTERS.md`](docs/CHARACTERS.md).

Si se presionan izquierda y derecha a la vez, manda la última que se presionó.

El disparo se hace con los pies plantados: mientras dura no camina. Saltar lo cancela.
En el aire no se dispara. La sheriff lleva un **revólver de 8 balas**: entre tiros
acciona el mecanismo (0.285 s) y puede encadenarlos sin volver a desenfundar.
Al vaciar el tambor lo recarga en **1.2 s, igual que el rifle del SWAT**; `R` permite
recargar antes. Abre el tambor, expulsa los casquillos, introduce un cargador rápido
y lo cierra. Mientras recarga puede caminar a media velocidad; saltar interrumpe
la recarga y conserva la munición anterior. El HUD muestra las balas restantes.
Con las duales, **cada revólver conserva su propio tambor de 8 balas**; el HUD
muestra los dos contadores. Se recarga el arma que se vació; `R` recarga los
tambores incompletos uno tras otro, **1.2 s por arma**. Guardar el segundo
revólver con `Q` conserva ambas cuentas. El rebote con las dos armas gasta una
bala de cada una.
La recarga de las duales tiene poses propias: enfunda el arma libre, carga la
primera, la enfunda, saca y carga la segunda, y termina con ambas en la mano.
La secuencia se ve también quieta o mientras recibe daño por fuego.
Un clic nuevo puede cortar la recarga y disparar con un revólver que aún tenga
balas; el tambor que quedó a medias conserva su cuenta. Mantener el clic espera
a que termine la recarga. Si ambos están vacíos, debe completarse al menos una.
Su arte y todas sus poses usan cuero gastado, tela, latón y acero con la misma luz
superior izquierda del escenario (`tools/rebuild_cowgirl.py`). Del cañón salen
bocanadas de humo animadas (`smoke.c`) que suben, avanzan, crecen y se desvanecen. La bala sale de la boca del cañón, vuela recta a 900 px/s
y desaparece al salir de la pantalla (hasta 16 a la vez).

## Enemigo y daño

Hay **25 familias y 50 variantes**: antidisturbios, soldado, policía, antidisturbios con
escudo, cinco civiles hombres y cinco mujeres, quemado, zombi degradado, perro infectado,
sheriff, vaquero, motociclista a pie, sacerdote, carcelero, bombero, carnicero y el
antidisturbios de élite. Cada familia tiene una variante normal y otra corredora.
La ropa y el equipo determinan la protección; los civiles y criaturas sin equipo
mantienen armadura cero al subir de nivel. El corredor conserva su protección y daño,
tiene el 55 % de la vida base y se mueve 1.8 veces más rápido que su familia normal.
La velocidad propia de la profesión no sube con el nivel.

Cada familia cuenta con siete hojas: reposo (`idle`, 4 cuadros), caminar (`walk`, 8),
correr (`run`, 8), atacar (`attack`, 6), recibir un golpe (`hurt`, 3), morir (`death`, 8)
y forcejear atrapado (`caught`, 4). El ataque impacta en el cuadro 2 y el cuerpo muerto
permanece en el cuadro 7. Los recursos se organizan en
`assets/sprites/zombies/<id>/`; el antidisturbios conserva sus cuatro hojas originales.
La plantilla, las profesiones y sus valores están en [docs/ZOMBIE.md](docs/ZOMBIE.md).

El **almanaque** se abre con `B` en la partida o mediante su opción en el menú principal
y en la pausa. Registra por separado las 50 variantes: los desconocidos muestran un
candado hasta encontrarlos, y las fichas conocidas enseñan su animación, profesión,
protección, encuentros, bajas y estadísticas de nivel 1 y del mayor nivel observado.
`WASD` o flechas recorren la galería; clic o `Enter` abre la ficha; `Esc` vuelve primero
a la galería y después a la pantalla anterior. Consultarlo detiene la partida y sus
sonidos. Los registros pertenecen a cada personaje y se conservan entre sesiones,
incluidos los descubrimientos realizados durante los reintentos.

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
zombi común de referencia usado en las pruebas (100 de vida, sin armadura) cae con 5 balas y el
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

Al abrir el juego aparece el **menú** con los niveles 1-1 a 2-5 (se desplaza con W/S): cuántos zombis tiene cada
uno, de qué nivel, y si está completado o bloqueado. Cada nivel se abre al completar el
anterior. El autoguardado conserva el progreso entre sesiones y permite continuar
una misión pendiente con el mismo personaje.

Antes de entrar a la primera misión de cada sesión aparece el aviso de autoguardado.
Se guarda cada **15 minutos de juego activo**, al subir de nivel, al completar una
misión y al cerrar el juego. Un pequeño icono de disquete indica el estado sin
detener la partida. El agua y la dinamita sobrantes pasan al siguiente nivel;
reiniciar o abandonar una misión devuelve el inventario a su estado de entrada.
Cerrar la aplicación conserva la misión en curso, con su inventario y reloj.

El **reloj** del HUD cuenta el tiempo activo de misión; pausa y almanaque lo detienen.
Al pasar el cursor muestra los objetivos de tiempo y salud de ese nivel. Se pueden
ganar hasta **3 estrellas**: los límites se ajustan al recorrido, enemigos y obstáculos.
Al terminar se muestra la salud final, el tiempo, las estrellas y las recompensas.
Cada estrella añade **25 % de la recompensa base** de XP y oro; mejorar el récord
personal con **100 % de vida** añade otro **50 %**. La primera victoria establece
el récord. Se conservan las mejores estrellas y el mejor tiempo de cada personaje.
Consulta los valores y el formato del guardado en [docs/PROGRESS.md](docs/PROGRESS.md).

Cada nivel es un **camino** hacia una salida (un portón con faroles) a 12–20 vistas de donde
empieza el personaje (19 000–31 000 px); el HUD muestra cuántos metros faltan. El mundo se
dibuja a 2 px por píxel de arte (`VIEW_SCALE`), con una vista de 480 × 270 píxeles de arte.
La cámara mantiene al personaje centrado, con 960 unidades de mundo a cada lado; el HUD
ocupa la franja superior del cielo. Lo que hay en cada camino está en la tabla de su nivel (`src/game/stages.c`),
distinta por tema:

- **Grupos de zombis** dormidos, de pie y respirando a la vista; despiertan juntos cuando hasta
  el más lejano está en pantalla, se giran hacia ella, se sacuden al despertar y dan un primer paso tambaleante.
  Mientras un grupo pelea no se puede seguir (`¡ACABA CON ELLOS!`); al vencerlo, `¡ADELANTE! →`.
  Cuando la rodean se forman en fila.
- **Zombi de élite** (desde 1-3): más blindado, garra más dura, tono rojizo; siempre deja cofre.
- **Corredores** (desde 1-2): variantes de todas las profesiones, con menos vida y 1.8 veces
  la velocidad de su familia. Hay civiles, criaturas y enemigos equipados entre ellos.
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
- **Red** (bajo las hojas, al pie de un árbol seco): salta del suelo y se cierra alrededor de quien
  la pisa, que queda colgando de la rama y pataleando; ella sale con 3 culatazos a la cuerda (`V`) mientras los zombis la
  atacan; un zombi cuelga 4 s y cae herido.
- Por el camino hay árboles secos y arbustos que son solo paisaje, idénticos a los de estas dos
  trampas: de lejos no se sabe cuál es cuál.
- **Lazo** (oculto en un arbusto): el arbolito doblado se endereza de golpe y la levanta de un pie (un cuarto de vuelta
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
- **Faroles de aceite** (noche, pueblo): iluminan; la bala pasa bajo el vidrio, así que se derriban
  con un culatazo o una explosión, y dejan el suelo
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
La lluvia atraviesa el cielo y llega hasta el camino; el viento lleva polvo y hojas
pequeños y translúcidos, y la planta rodadora conserva sus píxeles de origen. Los truenos
llegan poco después del relámpago. Los efectos del clima se dibujan antes del HUD, que
conserva sus textos e iconos legibles.

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
fantasma; son solo fondo. El fuego, la fogata y las explosiones sueltan humo que sube.
Los faroles iluminan desde su altura, las llamas desde el suelo y las explosiones
producen un destello que se apaga. La luz alcanza el terreno y proyecta sombras hacia
el lado opuesto de cada fuente; los muros y barricadas bloquean su paso.

La **linterna** va en el arma y abre un haz hacia donde mira
el personaje: la vaquera la saca del cinturón y la engancha a la pistola; el SWAT enciende la
que traen su rifle y su escopeta. `L` alterna su encendido (parpadea al prender; con las manos
ocupadas, como al recargar o dar un culatazo, no alumbra); empieza encendida solo en los temas nocturnos. Las
fuentes cálidas tienen una intensidad que varía suavemente. Esta iluminación modifica
la presentación del mundo, sin cambiar daño, colisiones ni visibilidad de la interfaz.

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
Subir de nivel rellena toda la vida hasta el nuevo máximo; no elimina sangrado ni quemaduras.

- **Matar un zombi** da `16 × su nivel`, con +25 % por cada nivel que esté por encima de
  ella y −25 % por cada uno por debajo (entre ×0.25 y ×1.75). Así repetir niveles fáciles
  rinde poco.
- **Un cofre** da una parte de lo que pide su nivel actual: `10 % × complejidad del nivel`,
  más cuanto más avanzada va la misión (×0.75 el primero, ×1.25 el último), con el mismo
  ajuste por diferencia de niveles.
- **Completar la misión** da una base fija según la dificultad: `25 % × XP para
  subir desde el nivel de los zombis × complejidad`, y `25 × complejidad` de oro.
  El cofre de salida entrega esa base una vez; al finalizar se suman los bonos
  por estrellas y récord con vida completa.

**Dificultad por nivel** (`src/game/stages.c`). No es lineal:

| Nivel | Zombis | Nivel de zombis | Complejidad | Pensado para |
| --- | --- | --- | --- | --- |
| 1-1 | 10 | 1 | 1.00 | Antidisturbios originales, para aprender |
| 1-2 | 14 | 2 | 1.10 | Presenta profesiones y corredores |
| 1-3 | 13 | 3 | 1.20 | Ataúdes, trampas y primer élite |
| 1-4 | 19 | 4 | 1.35 | Más corredores y combate nocturno |
| 1-5 | 22 | 5, el último **6** (jefe) | 1.50 | Completa las variantes y combina los peligros |
| 2-1 | 28 | 6 | 1.60 | Las afueras: patrullas con sirena y su **horda**, barriles ardiendo, autos y vallas |
| 2-2 | 31 | 7 | 1.70 | El centro con lluvia: hordas mayores, escaparates cerrados y un élite |
| 2-3 | 33 | 8 | 1.80 | Las vías: tres **trenes averiados** cortan el paso (dinamita o barril) |
| 2-4 | 36 | 9 | 1.90 | El centro de noche, con frío y tormenta: dos hordas |
| 2-5 | 38 | 10, el último **11** (jefe) | 2.00 | La base militar: alambre, retenes, dos élites |

**Ruta 2: la ciudad (Santa Brasa y el Puesto Cerro Gris).** Los caminos son más largos (34 000 a
44 000 px) y todo está a escala de la sheriff: un auto mide lo que un auto, los edificios son
de dos plantas y los bidones le llegan a la cintura.

- **Patrulla con sirena** (`SPOT_SIREN`): si pasa junto a ella, o le dispara, golpea o le
  explota algo cerca, la sirena suena y llega una **horda** por ambos lados; además despierta a
  los grupos dormidos cercanos. Tres tiros más le rompen las luces y la callan. Un letrero con
  su propio ícono avisa la horda y el HUD cuenta los que quedan.
- **Temor** (debuff, ícono propio): mientras dura una horda y unos segundos después, camina y
  corre más rápido (`FEAR_PACE`), pero recarga más lento (`FEAR_RELOAD_MULT`) y, con balas
  infinitas, dispara más lento (`FEAR_FIRE_MULT`).
- **Barriles ardiendo** (`SPOT_BURNERS`): iluminan la calle; un tiro o un golpe los tumba con un
  **fogonazo** que quema a quien esté cerca, y siguen ardiendo tirados mientras su aceite quema el piso.
- **Hidrantes** (`SPOT_HYDRANTS`): un tiro los revienta; el chorro dura 2 s, **daña y empuja** a
  zombis y a la jugadora (la moja) y deja un charco.
- **Autos y motos como barricada** (tres modelos de cada uno): se saltan con N (el auto, de un
  brinco largo) y **explotan** con 6 tiros (auto) o 4 (moto), al ser destrozados o por otra
  explosión, con la misma explosión de los barriles.
- **Tren averiado** (`SPOT_TRAIN`): un muro hecho de dos vagones; se abre con dinamita.
- **Puesto de avanzada** (`SPOT_OUTPOST`): con E se registra una vez (dinamita, agua, cargadores
  llenos y algo de vida) y se enciende su reflector.
- **Vehículos de paso**: autos, un todoterreno militar y camiones del ejército quedan sobre el
  camino; se atraviesan como la patrulla. El punto de provisiones es un **camión militar** (la
  carreta queda para la ruta 1).
- Frentes de tienda, comisaría, edificio y retén a tamaño real, con grafitis de **los Buitres**
  (saqueadores: se presentan en la fase 3); vallas de policía y barrera militar; descansos con
  banca de hierro y bidón ardiendo. Hay **gorriones** en vez de cuervos y periódicos en lugar de
  plantas rodadoras.
- **Zombis de ciudad** (5 tipos nuevos, cada uno normal y corredor): guardia de seguridad,
  enfermera, patrullero, obrero y oficinista, dibujados por oficio (`tools/make_city_zombies.py`).
- **Historia**: 15 pistas y 3 casos nuevos (*El cordón*, *El convoy*, *Cerro Gris*), una cinta
  antes de 2-1 (*Las luces de Santa Brasa*) y otra al terminar cada nivel. La meta de la ruta es
  el **Archivo 4**. Todo en [docs/LORE.md](docs/LORE.md).
- **Música y ambiente propios**: bajo eléctrico, batería, guitarra distorsionada, piano
  eléctrico y sintetizadores, más un tema de menú de la fase 2 y un ambiente de ciudad.

**Menú de niveles**: una pestaña por fase (FASE 1 · Ojo de Cuervo, FASE 2 · Santa Brasa; A/D o
clic), la rueda del mouse recorre los niveles, cada nivel con cinta vista tiene su botón CINTA
(clic o E) y con Q se elige el fondo de los menús entre las fases alcanzadas (cambia también
la música del menú).

Jugando cada nivel una vez (todos los zombis y cofres), la vaquera sube un nivel por nivel
completado y llega a cada uno cerca del nivel de sus zombis. Las profesiones frágiles,
blindadas y corredoras requieren distintas cantidades de disparos. La campaña mantiene
78 enemigos y tres encuentros de élite, con las mismas fórmulas de experiencia y cofres.
`tests/test_progression.c` juega la campaña
y falla si algún nivel queda imposible o trivial; si cambias números, corre las pruebas.

## Requisitos (Ubuntu/Debian)

Para compilar:

```bash
sudo apt install build-essential pkg-config python3 libsdl2-dev libsdl2-ttf-dev libsdl2-mixer-dev
```

En Windows, instala las herramientas y SDL en una terminal **MSYS2 UCRT64**:

```bash
pacman -S --needed make mingw-w64-ucrt-x86_64-gcc mingw-w64-ucrt-x86_64-pkgconf mingw-w64-ucrt-x86_64-python mingw-w64-ucrt-x86_64-SDL2 mingw-w64-ucrt-x86_64-SDL2_ttf mingw-w64-ucrt-x86_64-SDL2_mixer
```

Para solo jugar en otra máquina basta con `libsdl2-2.0-0`, `libsdl2-ttf-2.0-0` y `libsdl2-mixer-2.0-0`
(en Windows, `build.sh` deja las DLL necesarias en `dist/`).
Los sprites, fuentes y sonidos van **dentro** del ejecutable: `dist/TheMiracle` es un solo archivo.

## Compilación

`./build.sh` ejecuta en orden, y se detiene en el primer fallo sin tocar `dist/`:

1. Comprueba herramientas y SDL2.
2. `make test` — pruebas de lógica (entrada, animación, personaje), sin ventana.
3. `make` — compila `build/bin/TheMiracle`.
4. `--verify` — valida los recursos incrustados.
5. `--smoke-test` — recorrido automático: caminar a la derecha, saltar caminando,
   regresar a la izquierda, detenerse, disparar una vez y seguir la bala hasta que
   sale de la pantalla, mientras el zombi avanza (sin ventana).
6. Copia el ejecutable a `dist/TheMiracle`.

`./build.sh --clean` compila desde cero. Durante el desarrollo también sirven
`make`, `make test`, `make run` y `make clean`.

### Zip para jugadores

```bash
./dist.sh
```

Pide la versión, corre `build.sh` completo y deja el zip del sistema actual en
`dist/linux/` o `dist/windows/`, reemplazando el que hubiera en esa carpeta. Cada zip
se genera en su propio sistema; si algo falla, el anterior se conserva. Solo contiene el
ejecutable y sus bibliotecas (`lib/` en Linux, las DLL en Windows). En VS Code es la
tarea *Generar zip para jugadores*.

En Windows usa el mismo `./dist.sh`: genera
`dist/windows/TheMiracle-<versión>-windows.zip`, listo para descomprimir y abrir
`TheMiracle.exe`. El script activa UCRT64 si lo ejecutas desde otra terminal de
MSYS2 o desde Git Bash. Desde Git Bash busca MSYS2 en `C:/msys64`; si está en otra
carpeta, indica la ruta con `MSYS2_ROOT`, por ejemplo:

```bash
MSYS2_ROOT='D:/Herramientas/msys64' ./dist.sh
```

Las partidas no viajan en el zip: el juego las guarda en la carpeta de datos del usuario
(`~/.local/share/TheMiracle/TheMiracle` en Linux, `%APPDATA%\TheMiracle\TheMiracle` en
Windows), así que cada cuenta de cada computadora tiene su propio avance.

### Desarrollo con recarga automática

```bash
make watch
```

Compila, abre el juego y se queda vigilando `src/`, `tests/`, `assets/`, `tools/` y el
`Makefile`. Cada vez que guardas un archivo (código o PNG) recompila, corre las pruebas
y reabre el juego con el cambio. Si algo falla, muestra el error y deja abierta la
versión anterior. `Ctrl+C` lo detiene y cierra el juego. No toca `dist/`: cuando
quieras publicar, usa `./build.sh`.

### VS Code (Windows y Linux)

La carpeta `.vscode/` ya trae tareas, depurador e IntelliSense para los dos sistemas. Al abrir
el proyecto, VS Code ofrece instalar las extensiones recomendadas (C/C++ y Python). En Windows
las tareas y la terminal usan MSYS2 UCRT64; para depurar instala también `gdb`:
`pacman -S mingw-w64-ucrt-x86_64-gdb`.

1. Editas código en `src/`.
2. `Ctrl+Shift+B` (**Compilar**) para comprobar que compila.
3. Tarea **Jugar** para probarlo, o `F5` para abrirlo con el depurador (compila sin optimizar en
   `build/debug/`). Con un archivo de `tests/` abierto, **Depurar la prueba abierta** hace lo mismo con él.
4. Cuando quieras generar la versión final en `dist/`, corres la tarea
   **Build completo (build.sh)**, que es el equivalente a `./build.sh`.

Las demás están en *Terminal > Ejecutar tarea*: **Pruebas**, **Vigilar cambios (make watch)**,
**Regenerar hojas de la vaquera** y las de sonido.

## Sonido

**Música:** los menús y cada nivel tienen su tema original, compuesto y sintetizado en el
repositorio, sin material de terceros, con su barra de volumen en Opciones ([docs/AUDIO_MUSIC.md](docs/AUDIO_MUSIC.md)).

**Efectos:** Audio con SDL2_mixer: los once sonidos legacy se conservan y los efectos nuevos se
montan con grabaciones CC0 y capas de los originales. `tools/make_sfx.py` coordina su
generación; fuentes, edición y comprobaciones en [docs/AUDIO.md](docs/AUDIO.md).
Todos se incrustan en el ejecutable. La sheriff conserva el disparo (`player/shot`)
y usa `weapons/revolver_cycle` para el mecanismo y `weapons/revolver_reload` para
la recarga completa de 1.2 s (`tools/make_revolver.py --audio`). La antigua baqueta
(`player/reload`) queda preservada como recurso histórico. El zombi tiene
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
Para regenerar los nuevos, usa `python3 tools/make_sfx.py --fetch` la primera vez y
`python3 tools/make_sfx.py` después; necesita FFmpeg solo al crear audio. Compilar y jugar
usan los WAV terminados. El volumen está en `SFX_VOLUME` (`src/config.h`). Si no hay dispositivo
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
**noche** y 1-5 en el **pueblo fantasma**; en la ruta 2, 2-1 en las **afueras** al amanecer, 2-2 en
el **centro**, 2-3 en las **vías**, 2-4 en la **ciudad de noche** y 2-5 en la **base militar** (suelo de
asfalto, concreto o balasto con rieles). Los decorados cambian de paleta con el tema. Todo
en [`docs/LANDSCAPE.md`](docs/LANDSCAPE.md).

## Estructura

```text
Makefile, build.sh
src/
  main.c                 Entrada y opciones de línea de comandos
  config.h               Constantes: ventana, escala, velocidades, colores
  app/                   Coordina motor, reglas y presentación
    application.c/.h     Ciclo del juego (paso fijo de 60 Hz) y cambios de pantalla
    state.h              Estado de partida y perfiles por personaje
    autosave.c/.h        Calendario de autoguardado y señales del HUD
    savegame.c/.h        Formato versionado, validación y recuperación de la misión
    stage.c/.h           Entrada de la partida, armas, pausa y eventos de audio
    stage_render.c/.h    Dibujo de la partida e interpolación visual
    options.c/.h         Ajustes de ventana y volumen, con estado explícito por aplicación
    navigation.c/.h      Sonidos de navegación del almanaque y del Expediente
    story_audio.c/.h     Audio sincronizado de las cintas; limpia efectos al saltar
    verify.c/.h          Recursos incrustados y contratos de --verify
    smoke.c/.h           Entrada y observación de --smoke-test
    capture.c/.h         Escenas de revisión de --capturas
  engine/                Motor reutilizable
    platform.c/.h        Ventana, renderer, vsync, lectura de teclado y mouse (SDL)
    input.c/.h           Acciones, flancos de tecla, prioridad de dirección (sin SDL)
    animation.c/.h       Animaciones por fotogramas en una hoja de sprites (sin SDL)
    assets.c/.h          Texturas a partir de los recursos incrustados
    storage.c/.h         Escritura en segundo plano con dos copias y comprobación CRC
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
    zombie.c/.h          Catálogo de 25 familias/50 variantes, estadísticas y siete animaciones por familia (sin SDL)
    combat.c/.h          Balas contra el zombi y garra contra la vaquera (sin SDL)
    zombie_render.c/.h   Dibujo del zombi: espejo, desvanecido y barra de vida
    almanac.c/.h         Encuentros y bajas por variante, desbloqueos, estadísticas y navegación del almanaque (sin SDL)
    almanac_render.c/.h  Galería y fichas del almanaque, con animaciones y estadísticas comparadas
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
    mission.c/.h         Reloj, metas por nivel, estrellas, récords y bonos (sin SDL)
    stages.c/.h          Los niveles 1-1 a 2-5: su camino (grupos, élite, terreno), nivel, cofres y complejidad (sin SDL)
    stage_run.c/.h       Una partida de un nivel: el camino, grupos que despiertan y detienen, cofres, XP y salida (sin SDL)
    terrain.c/.h         Barricadas, barriles de pólvora, carreta de provisiones y salida (sin SDL)
    terrain_render.c/.h  Dibujo del terreno del camino
    lighting.c/.h        Fuentes a su altura real, bloqueo de luz y proyección de sombras (sin SDL)
    weather.c/.h         Estado y partículas de viento, lluvia y tormenta (sin SDL)
    weather_render.c/.h  Composición del clima sobre cielo y mundo, conservando el estado del renderer
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
tools/make_sfx.py        Coordina los efectos grabados CC0 y las capas originales en assets/sounds/
tools/crush_sfx.py       Graba o convierte audio a efecto de 8 bits (usa ffmpeg)
tools/make_sprites.py    Genera en pixel art las placas de nivel y las chispas del cofre
tools/make_terrain.py    Genera el terreno del camino (barricadas, muro, barriles, dinamita, cajas, botellas,
                         trampas, ataúdes, faroles, fuego, banca, fogata, carreta, salida) y efectos
tools/make_ui.py         Genera la fuente pixel y el kit de interfaz (tableros, botones, teclas, iconos, armas)
tools/make_sit.py        Genera las hojas de sentado, de frente (sentarse, descansar, recargar sentada, cabecear)
tools/make_sun.py        Pinta el sol entero en los cielos de atardecer y pueblo fantasma
tools/rebuild_cowgirl.py Regenera todas las hojas de la vaquera en orden (empieza por rework_cowgirl y termina en finish_cowgirl)
tools/finish_cowgirl.py  Cierra el contorno de la vaquera y tapa los huecos de un pixel en todas sus hojas
tools/make_flashlight.py La linterna de la vaquera: engancharla a la pistola (light.png, light_dual.png) y sobre shoot (flashlight.png); también los turnos de las duales (shoot_dual*.png)
tools/make_terrain.py    (también el cuervo: sprites/crow/crow.png)
tools/make_care.py       Beber y vendarse de la vaquera (drink.png, bandage.png) a partir de su hoja de disparo
tools/make_plant.py      Plantar dinamita (plant.png) de la vaquera y del SWAT, 0.45 s
tools/make_faint.py      El desmayo de la vaquera y el SWAT (faint.png) a partir de su hoja de caminar
tools/make_melee.py      Las poses del culatazo de la vaquera (las hojas las dibuja make_flashlight.py)
tools/make_powers.py     Arte de los poderes de nivel 3: las pistolas duales de la vaquera y la granada
tools/make_zombies.py    Compone prendas editadas sobre el cuerpo nativo y exporta las siete hojas por familia
tools/make_character_base.py  Genera la base (maniquí) de los personajes y sus guías
tools/check_landscape.py Revisa las capas de un tema de paisaje antes de usarlas
tools/check_architecture.py Comprueba capas, fuentes del Makefile y lógica sin SDL
tools/clean_project.py   Elimina build/ y cachés; conserva dist/ y fuentes de recursos
tests/                   Pruebas de la lógica pura
docs/ASSETS.md           Mapa de recursos: carpetas, nombres, qué los genera y qué comprueba --verify
docs/SPRITES.md          Especificación para dibujar sprites (tamaños, pivotes, paleta)
docs/LANDSCAPE.md        Especificación del paisaje: capas con paralaje, paletas y temas por nivel
docs/ZOMBIE.md           Catálogo, escalado y plantilla de estilo compartida de los zombis
docs/CHARACTERS.md       Personajes: habilidades, armas, plantilla, base y cómo dibujar uno nuevo
docs/LORE.md             Historia de THE MIRACLE: personajes, intro, pistas y fases
docs/templates/          La base de los personajes (la vaquera en grises), para dibujar encima
build/                   Generado (temporales)
dist/                    Generado (ejecutable final)
```

Las dependencias y las comprobaciones están en [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
`make check-architecture` revisa los límites de las capas; `make test` y `./build.sh`
también lo ejecutan. Para retirar temporales y cachés usa `make tidy`: conserva el
juego de `dist/`, las grabaciones fuente, las plantillas y los ajustes del editor.
`python3 tools/clean_project.py --dry-run` permite ver qué retiraría.

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
