# Arte de las cinemáticas

El laboratorio comparte hierro gastado, vidrio verdoso, pintura envejecida y
papel marfil con los objetos del escenario. Las lámparas cálidas recortan planos
fríos; los monitores conservan el verde de MRC-1 y la alarma el rojo. La luz cae
en grupos de píxeles y los detalles siguen el material: juntas y desconchones en
los paneles, reflejos en el vidrio, cepillado en el metal. Sin ruido uniforme ni
suavizado. El exterior usa los propios paisajes y personajes de la partida.

`tools/make_cinematics.py` dibuja la composición, los datos de los monitores y
las poses. `tools/cinematic_art.py` contiene las rampas de material, el decorado
de cada plano y sus luces estáticas. `src/app/intro_render.c` añade luces de
emergencia locales, polvo suspendido y el acabado de cámara; comparte el
tratamiento de bordes y las luces del pasillo con las cintas de
`src/app/story_render.c`. Los textos se dibujan encima del acabado.

## Mercenario y rifle

El uniforme sigue oscuro y el rostro oculto. El acero del rifle tiene una rampa
propia, mate y algo más fría que el chaleco: culata, cajón de mecanismos, cargador,
mira, guardamanos perforado y cañón deben poder leerse por separado. La mano de
apoyo queda al lado de la boca del cañón. La linterna tiene un halo contenido.
Los brazos se dibujan junto al arma: la culata entra en el hombro, la mano
cercana cubre el agarre y el antebrazo lejano sostiene el guardamanos. El torso,
las manos y el rifle comparten el desplazamiento de cada paso y respiración.

| Recurso | Cuadros | Anclas en cada cuadro |
| --- | --- | --- |
| `sprites/mercenary/walk` | 12 de 81 × 80; 8 de caminar y 4 de respiración | centro x=36, suelo y=66, linterna (70, 33) |
| `sprites/mercenary/aim` | 4 de 110 × 130; 2 apuntando, disparo y recuperación | boca (54, 72), linterna (67, 81) |
| `cinematics/lab/corridor` | 1 de 480 × 180, con paneo | vista de 320 × 180 |
| `cinematics/lab/monitors` | 6 de 320 × 180 | ciclo |
| `cinematics/lab/alarm` | 8 de 320 × 180 | división y mutación; alterna los dos últimos |

En el disparo, las anclas de frente suben 2 píxeles; en la recuperación, 1.
En el perfil, la linterna suma a su fila los desplazamientos
`0, 0, 1, 0, 0, 0, 1, 0, 0, -1, -1, 0` de los doce cuadros.
Cada píxel de estos recursos ocupa 3 píxeles de ventana. Mantener las anclas
evita que los haces o el fogonazo se separen de sus fuentes.

## Movimiento y encuadres

La cámara acelera y frena al inicio y al final de cada paneo. El pasillo conserva
el dibujo nítido y permite desplazamientos de un píxel de ventana entre columnas
de arte. Las cintas tienen un origen distinto por plano (`SHOT_ORIGINS` en
`story_render.c`), para mostrar otros edificios y decorados. Los objetos quietos
se desplazan con la cámara y permanecen sobre el suelo del escenario.
El plano lejano del laboratorio conserva el origen de su valle abierto, para
que las casas del primer término no oculten el edificio durante el paneo.

La sheriff sigue caminando hasta salir por el borde derecho del plano del título.
Sus pasos de audio continúan y se atenúan al alejarse; la introducción corta
omite esa caminata y sus sonidos.

Las ruedas de la ambulancia, del todoterreno y de los camiones en movimiento se
dibujan en `cine_wheel`: eje y silueta fijos, rin y dibujo del neumático giratorios,
luz superior estable. El ángulo depende de la distancia sobre el camino y del
radio de la rueda, incluyendo el avance de cámara cuando corresponde. Las luces
de emergencia siguen su propia animación. Los vehículos estacionados conservan
sus ruedas quietas durante los paneos.

La casa en ruinas de `make_houses.py` comparte cimiento entre el muro y el hogar
de mampostería; las vigas rotas llegan al collar de la chimenea.

## Reconstruir y revisar

```bash
python3 tools/make_cinematics.py --only lab mercenary
python3 tools/make_cinematics.py --only lab mercenary --verify
./build.sh
mkdir -p build/cinematic-captures
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy ./dist/TheMiracle --capturas build/cinematic-captures
```

`--only` acepta `lab`, `mercenary`, `vial` y `ambulance`. Sin esa opción genera
los siete recursos; un directorio de destino opcional va antes de `--only`.
El cuerpo de perfil toma como fuente el SWAT de `assets/` del proyecto.
`--verify` reconstruye en un directorio temporal y compara sin modificar el
destino. `build.sh` comprueba los fondos del laboratorio y el reparto de apoyo.

Las capturas `0a` a `0f` revisan el laboratorio, la llegada de los mercenarios,
el vial y el disparo; `0d1_intro_mercenarios_cerca` enseña los rifles de perfil.
Las `0g` a `0m` revisan la transición al exterior y al título. Las
`0s_cinta_4_*` muestran el mismo laboratorio en las cintas del Expediente.

[Comparación de los planos](img/cinematic_rework.png) ·
[Rifle y animaciones](img/mercenary_rework.gif).

Las pruebas de `tests/cinematic_render.c` revisan el giro y su dirección, la
silueta fija, la suavidad del paneo, la salida de la sheriff y la visibilidad
del laboratorio durante todo su plano. Para exportar
secuencias de la escena real a 24 fps:

```bash
make build/tests/cinematic_render
mkdir -p build/motion-preview
./build/tests/cinematic_render build/motion-preview
```

[Movimiento de vehículos y sheriff](img/cinematic_motion.gif) ·
[Unión de la chimenea](img/ruin_connected.png).
