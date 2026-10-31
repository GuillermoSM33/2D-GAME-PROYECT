# Vaquera 2D

Demo 2D en **C + SDL2** con el sprite original aprobado: caminata (8 fotogramas de
42 × 67 px), salto (8 de 54 × 82), disparo (8 de 81 × 80) y bala (4 de 8 × 6), más un enemigo: el zombi antidisturbios
(caminata de 8 fotogramas, impacto de 3 y muerte de 8, de 72 × 72). Hacia la izquierda se usa el mismo arte espejado.

## Jugar

```bash
./build.sh          # compila, prueba y deja el ejecutable en dist/
./dist/Vaquera2D
```

| Tecla | Acción |
| --- | --- |
| `D` o `→` | Caminar a la derecha |
| `A` o `←` | Caminar a la izquierda |
| `Shift` + movimiento | Correr |
| `Espacio`, `W` o `↑` | Saltar (también caminando o corriendo) |
| Clic izquierdo | Disparar (de pie; hacia la dirección que tengas presionada) |
| `R` | Volver a la posición inicial (también reinicia al zombi) |
| `Esc` | Salir |

Si se presionan izquierda y derecha a la vez, manda la última que se presionó.

El disparo se hace con los pies plantados: mientras dura no camina. Saltar lo cancela.
En el aire no se dispara. Un clic nuevo después del fogonazo encadena otro disparo
sin volver a desenfundar. La bala sale de la boca del cañón, vuela recta a 900 px/s
y desaparece al salir de la pantalla (hasta 16 a la vez).

## Enemigo y daño

El zombi antidisturbios entra cojeando por la derecha, siempre hacia la vaquera, y se
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
mata lo sacude con chispas y lo derriba (`death.png`, 0.7 s). Queda tendido 1.5 s, se
desvanece y, 1.5 s después, aparece otro en el borde más lejano a la vaquera.

El daño se calcula así (`src/game/damage.c`, valores en `config.h`):

```text
daño del arma  = 20 × (1 + 0.6 × (nivel − 1))      nivel 1: 20   nivel 2: 32   nivel 3: 44
daño recibido  = daño del arma × 100 / (100 + armadura), redondeado y mínimo 1
```

| Enemigo | Vida | Armadura | Balas para matarlo (nivel 1 / 2 / 3) |
| --- | --- | --- | --- |
| Zombi común (sin arte todavía) | 100 | 0 | 5 / 4 / 3 |
| Zombi antidisturbios | 100 | 80 (para el 44 % del daño) | 10 / 6 / 5 |

El arma está en nivel 1 (`WEAPON_LEVEL`) hasta que haya un sistema para subirla.

### Vida de la vaquera

Tiene 100 de vida y 25 de armadura (`PLAYER_HEALTH`, `PLAYER_ARMOR`). La garra del zombi
usa la misma fórmula que el arma, con base 15 (`ZOMBIE_ATTACK_BASE`): en nivel 1 son 15,
que la armadura deja en **12**, así que la derriban **9 zarpazos**. Cada golpe la empuja
hacia atrás unos 29 px y la hace parpadear en rojo 0.4 s. La barra de vida está arriba a
la derecha, con marco metálico por la armadura.

Sin vida, la vaquera queda en pie oscurecida (todavía no hay hoja de muerte), no responde
a los controles, el zombi deja de atacar y aparece «TE ALCANZÓ EL ZOMBI». `R` reinicia todo.

## Requisitos (Ubuntu/Debian)

Para compilar:

```bash
sudo apt install build-essential pkg-config python3 libsdl2-dev libsdl2-ttf-dev
```

Para solo jugar en otra máquina basta con `libsdl2-2.0-0` y `libsdl2-ttf-2.0-0`.
Los sprites y fuentes van **dentro** del ejecutable: `dist/Vaquera2D` es un solo archivo.

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
  game/                  Lo propio de este juego
    controls.c/.h        Teclas y botones del mouse asignados a cada acción
    player.c/.h          Estados del personaje: idle / walk / run / jump / land / shoot / dead, vida y empujón (sin SDL)
    movement.c/.h        Caminar, correr y límites de pantalla (sin SDL)
    jump.c/.h            Arco del salto: altura y tiempo en el aire fijos (sin SDL)
    shoot.c/.h           Secuencia del disparo: momento de la bala y disparos encadenados (sin SDL)
    bullet.c/.h          Balas en vuelo: grupo fijo, movimiento, salida de pantalla (sin SDL)
    bullet_render.c/.h   Dibujo de las balas
    damage.c/.h          Daño por nivel (arma y garra) y reducción por armadura (sin SDL)
    zombie.c/.h          Zombi: tipos (vida, armadura, garra), avance, ataque, retroceso, muerte y reaparición (sin SDL)
    combat.c/.h          Balas contra el zombi y garra contra la vaquera (sin SDL)
    zombie_render.c/.h   Dibujo del zombi: espejo, desvanecido y barra de vida
    effects.c/.h         Efectos de una sola pasada, como las chispas en la armadura (sin SDL)
    effects_render.c/.h  Dibujo de los efectos
    player_render.c/.h   Dibujo del personaje (recorte del fotograma, espejo, altura, parpadeo rojo)
    health_bar.c/.h      Barra de vida compartida (vaquera y zombi)
    scene.c/.h           Fondo y suelo
    hud.c/.h             Textos de controles, vida de la vaquera y aviso al morir
assets/
  sprites/player/walk.png  Caminata: 8 fotogramas de 42 × 67 en una fila (336 × 67)
  sprites/player/jump.png  Salto: 8 fotogramas de 54 × 82 en una fila (432 × 82)
  sprites/player/shoot.png Disparo: 8 fotogramas de 81 × 80 en una fila (648 × 80)
  sprites/player/bullet.png Bala: 4 fotogramas de 8 × 6 en una fila (32 × 6)
  sprites/zombie/walk.png  Zombi caminando: 8 fotogramas de 72 × 72 en una fila (576 × 72)
  sprites/zombie/hurt.png  Zombi recibiendo un impacto: 3 fotogramas de 72 × 72 (216 × 72)
  sprites/zombie/death.png Zombi cayendo muerto: 8 fotogramas de 72 × 72 (576 × 72)
  sprites/zombie/attack.png Zarpazo del zombi: 6 fotogramas de 72 × 72 (432 × 72)
  sprites/effects/sparks.png Chispas de bala en metal: 2 fotogramas de 20 × 12 (40 × 12)
  fonts/                   DejaVu Sans Mono (+ licencia)
tools/embed_assets.py    Convierte PNG/TTF en datos C (solo biblioteca estándar de Python)
tools/sprite_style.py    Compara el nivel de detalle de una hoja con la vaquera
tests/                   Pruebas de la lógica pura
docs/SPRITES.md          Especificación para dibujar sprites (tamaños, pivotes, paleta)
docs/ZOMBIE.md           Especificación del zombi antidisturbios
legacy/python/           Versión anterior en Python + Tkinter, como referencia
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
4 dispara (aquí sale la bala: `player.shot_fired`), 5–6 humo y 7 enfunda.

## Añadir una mecánica

1. Coloca la hoja en `assets/sprites/player/<nombre>.png` (PNG RGBA de 8 bits,
   fotogramas iguales en una fila, mirando a la derecha). Se incrusta sola al compilar.
2. Crea `src/game/<nombre>.c/.h` con la lógica (sin SDL, para poder probarla) y su
   prueba en `tests/test_<nombre>.c`. Añade el `.c` a `CORE_SRC` en el `Makefile`.
3. Si necesita tecla o botón, agrega la acción en `src/engine/input.h` y la entrada en
   `src/game/controls.c` (`BIND_KEY` para teclas, `BIND_MOUSE` para botones del mouse).
4. En `src/game/player.c`, añade el estado y su `AnimationDef` (tamaño de cuadro,
   fotogramas, fps y pivote), y regístrala en `ANIMATIONS` para que `--verify` la revise.
