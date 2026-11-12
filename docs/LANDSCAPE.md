# Paisaje, edificios y objetos del mapa

Los diez niveles usan nueve temas (1-1 y 1-2 comparten atardecer). El paisaje y
los objetos son pixel art nativo, PNG RGBA de 8 bits sin entrelazado. Los dibujos
procedurales se conservan en `tools/` y usan solamente la biblioteca estándar.

| Tema | Niveles | Ambiente |
| --- | --- | --- |
| `atardecer` | 1-1, 1-2 | Desierto, mesetas y cielo naranja |
| `cementerio` | 1-3 | Panteón morado, creciente y niebla |
| `noche` | 1-4 | Desierto azul, luna llena y niebla |
| `pueblo_fantasma` | 1-5 | Pueblo en ruinas, cielo rojo |
| `afueras` | 2-1 | Amanecer, viviendas y gasolinera |
| `centro` | 2-2 | Torres, azoteas y esmog |
| `vias` | 2-3 | Patio ferroviario al atardecer |
| `ciudad_noche` | 2-4 | Edificios oscuros, ventanas y niebla |
| `base_militar` | 2-5 | Retén, hangares y focos de alarma |

## Escala y cámara

El mundo mide 1920 × 1080 unidades (`VIEW_WIDTH`, `VIEW_HEIGHT`), con cuatro
unidades por píxel de arte. Se dibuja en una textura y se presenta a 0.5×:
la ventana lógica de 960 × 540 muestra **480 × 270 píxeles de arte**, dos
píxeles de ventana por píxel de arte, sin suavizado.

La cámara mantiene a la protagonista en el centro: **960 unidades de mundo a
cada lado**, con el mismo espacio para emboscadas por delante y por detrás.
La línea del suelo está en la fila 240 del arte (y = 480 de ventana); el HUD
usa los primeros 135 píxeles de ventana. La referencia de escala es la sheriff:
56 píxeles de arte equivalen aproximadamente a 1.70 m. Las puertas miden unos
60 píxeles; los postes y árboles pasan sobre su cabeza y caben completos en la vista.

## Materiales y profundidad

La luz llega desde arriba a la izquierda. Cada material conserva detalles
propios: juntas, veta y clavos en la madera; bloques, grietas y mortero en la
piedra; costuras y pliegues en sacos y lona; bordes, remaches y óxido en el metal;
costillas y espinas en los cactus; ramas, corteza y masas de hojas en la vegetación.
Evitar superficies plásticas, rectángulos sin estructura y ruido uniforme.

Los personajes se leen contra las capas cercanas oscuras. El contraste disminuye
con la distancia: edificios y decorados usan los tonos `prop_shadow`, `prop_light`
y `haze` de `ThemeDef`. Los originales se dibujan en colores diurnos y
`assets_texture_graded` los adapta al tema, conservando el detalle entre tonos.
Las casas reciben además `HOUSE_HAZE` de neblina atmosférica. Los píxeles de luces
propias se marcan con alfa 254 (`Canvas.light`): el juego los convierte en opacos
y conserva su color. No se usa ese alfa para transparencia normal.

Los objetos interactivos tienen algo más de contraste y sus estados conservan
las mismas siluetas, pivotes y dimensiones de colisión. La iluminación local
de faroles, linterna y explosiones se aplica al primer plano.

El foco del outpost permanece apagado hasta registrar sus suministros. Al
encenderse usa el mismo haz direccional que la linterna: nace en la lente,
apunta al camino hacia la izquierda, pierde intensidad con la distancia y
respeta los obstáculos. El sprite conserva solo la lente encendida; el haz
se calcula en la escena. El foco y la linterna pueden iluminar simultáneamente.

## Capas

`tools/landscape_kit.py:LAYERS` comparte geometría entre el generador y el
validador. Coincide con `BACKGROUND_LAYERS` en `src/game/themes.c`; `--verify`
comprueba los recursos incrustados contra la tabla del juego.

| Archivo | Tamaño nativo | Filas del arte | Paralaje | Repite |
| --- | --- | --- | --- | --- |
| `sky.png` | 480 × 180 | 0–179, última fila extendida al suelo | 0 | No |
| `far.png` | 720 × 72 | 104–175 | 0.15 | Sí |
| `hills_far.png` | 720 × 70 | 140–209 | 0.35 | Sí |
| `hills_near.png` | 720 × 64 | 176–239 | 0.6 | Sí |
| `ground.png` | 480 × 30 | 240–269 | 1 | Sí |
| `fog.png` (opcional) | 480 × 48 | 216–263 | 1 + deriva | Sí |

La niebla tiene un solo color, dos niveles de alfa entre 30 y 100 y deriva
de 24 unidades de mundo por segundo. Las capas recortadas usan alfa 0 fuera de
su silueta. El validador informa costuras y exceso de píxeles sueltos para revisión
visual; no modifica el arte. En la banda del HUD la luminancia recomendada es
≤ 55; detrás de los cuerpos (184–239), ≤ 62, con acentos de luz de hasta 120.

## Decorados

`tools/make_props.py` genera todas las hojas de `sprites/props/` salvo casas.
Cada variante ocupa un cuadro, se apoya en su última fila y se centra en él.
`src/game/props.c` es la tabla que usa el juego.

| Hoja | Cuadro | Variantes |
| --- | --- | --- |
| cactus | 44 × 100 | 4 |
| rock | 48 × 24 | 3 |
| fence | 72 × 40 | 2 |
| dead_tree | 100 × 150 | 2 |
| grass | 24 × 14 | 4 |
| wagon_wheel | 44 × 44 | 2 |
| skull | 34 × 18 | 2 |
| tombstone | 28 × 40 | 4 |
| sign | 36 × 62 | 2 |
| shrub | 40 × 36 | 4 |
| telegraph | 40 × 176 | 2 |
| hydrant | 14 × 24 | 1 |
| streetlight | 40 × 150 | 2 |
| trash | 26 × 32 | 2 |
| cone | 16 × 24 | 1 |
| tires | 40 × 34 | 1 |
| sandbags | 66 × 28 | 1 |
| jersey | 104 × 27 | 1 |
| pole | 44 × 160 | 1 |
| litter | 20 × 6 | 3 |
| signal | 24 × 110 | 1 |
| drums | 48 × 34 | 1 |
| fallen_pole | 150 × 26 | 1 |
| traffic_light | 60 × 140 | 2 |

Cada tramo de 960 unidades tiene cuatro sitios posibles para objetos grandes,
elegidos por los pesos del tema y separados según su ancho, más 2–6 matas de
pasto (basura en los temas urbanos). La semilla y el camino determinan la distribución.

## Edificios

`tools/make_houses.py` genera `sprites/props/houses.png`: **21 cuadros de
256 × 192**, hoja de **5376 × 192**. No mezclar los recortes con la hoja histórica
de 80 × 64. Todos comparten suelo y escala de puertas.

| Cuadros | Diseño |
| --- | --- |
| 0–4 | Saloon, cabaña, granero, casa derrumbada, tanque de agua |
| 5–9 | Iglesia, sheriff, herrería, establo, banco |
| 10–12 | Almacén, casa de adobe, silo caído |
| 13–17 | Espectacular, gasolinera, tiendas, departamentos, bodega |
| 18–20 | Hangar, torre de vigilancia, radar |

Los edificios pasan a 0.8 del movimiento del camino. Hay un sitio cada 1200
unidades con variación de posición de hasta 176: los cuadros no se superponen.
Los temas urbanos eligen sus edificios mediante `ThemeDef.houses`.

## Objetos interactivos

`tools/refine_terrain.py` reconstruye los objetos desde las funciones de
`make_terrain.py`, `city_terrain.py` y `make_city.py`, y agrega detalles según su
material. Siempre empieza desde el dibujo fuente: ejecutarlo varias veces no
acumula texturas. Los módulos `terrain_architecture_detail.py`,
`terrain_vehicle_detail.py`, `terrain_object_detail.py` y `terrain_water_detail.py`
dibujan la construcción, el volumen y los acabados de cada familia. Conservan
cuadros de animación, roturas, huecos de paso, luces, posiciones y colisiones.
Incluye barricadas, cajas, barriles, muros,
fachadas, fogatas, trampas, carros, autos, tren y estructuras militares.

El agua conserva una superficie compartida entre `river` y `river_front`:
reflejos largos y espuma siguen la corriente, con lecho y piedras visibles en
las orillas. El fuego tiene lenguas curvas que cambian de forma entre los
cuatro cuadros y una base de aceite y brasa; sus medidas de daño no cambian.

Los árboles y arbustos que ocultan trampas se comparten con los señuelos
inofensivos del camino; deben seguir siendo visualmente indistinguibles.

## Regenerar y comprobar

```bash
python3 tools/rebuild_scenery.py
python3 tools/check_landscape.py assets/backgrounds/*
./build.sh
./build/bin/TheMiracle --capturas build/scenery-captures
```

Se pueden ejecutar por separado `make_landscape.py`, `make_props.py`,
`make_houses.py` y `refine_terrain.py`, todos con un directorio de assets opcional.
Los puntos de entrada históricos `make_city.py` y `make_terrain.py` usan los
generadores nuevos para no volver a exportar las hojas antiguas.

`--verify` valida todos los tamaños; las capturas `50_escenario_*` muestran los
diez temas con la protagonista y objetos a ambos lados. Revisar también faroles,
linterna, explosiones, trampas y estados rotos antes de aprobar arte nuevo.
Las capturas `51_outpost_apagado`, `51_outpost_encendido` y
`51_outpost_y_linterna` revisan el foco y ambos haces juntos.

Para agregar un tema, crear sus capas y parámetros en `landscape_west.py` o
`landscape_city.py`, registrar el `ThemeDef` y asignarlo en `stages.c`. El
laboratorio de las cintas se coloca en el valle entre las colinas lejanas y
cercanas, con paralaje 0.45 (`app/story_render.c`).
