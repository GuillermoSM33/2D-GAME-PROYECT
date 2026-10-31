# Enemigo: zombi antidisturbios

Indicaciones para dibujar (o generar) las hojas del primer enemigo: un zombi con equipo
antidisturbios militar. Siguen las reglas generales de [`SPRITES.md`](SPRITES.md): PNG RGBA
de 8 bits, a 1×, una fila de cuadros y mirando a la **derecha**.

**La regla principal: que parezca dibujado por la misma mano que la vaquera.** No basta
con igualar la cantidad de detalle. También hay que copiar sus **colores**, sus
**proporciones** y su **forma de sombrear** (ver *Estilo de la vaquera*).

| Versión | Problema |
| --- | --- |
| 1 | Granulado: detalle repartido por todo el cuerpo, como un render reducido (22 % de píxeles sueltos) |
| 2 | Plano: bloques grandes de gris medio, sin detalle ni contraste (4 % sueltos, 60 % oscuros) |
| 3 | Buen nivel de detalle, pero **otro estilo**: azules fríos y apagados, cuerpo de barril, casco enorme y piernas gruesas |

La paleta azul de la versión 3 salió de esta misma especificación; ya está corregida.

## Estilo de la vaquera

Medido en `assets/sprites/player/walk.png`:

**Color**
- **Rampas cálidas y saturadas** para todo lo orgánico y la tela: cafés, rojos y crema
  (tono entre 12° y 48°, saturación 0.5–0.97).
- **Grises neutros** (saturación 0) para el metal: `#2c2c2c` `#424242` `#505050` `#868689`
  `#a7a8a8`, los del revólver y el brazo.
- **Ningún color frío ni apagado.** Sus únicos fríos son esos grises neutros.

**Silueta y proporciones**
- **Más ancha arriba y se afina hacia abajo:** 27 px en el ala del sombrero, 18–21 en el
  torso y 8–11 en los pies.
- Cabeza pequeña dentro del sombrero; **las piernas ocupan casi 40 % del alto**.
- Cuerpo delgado, nada de barril.

**Dibujo**
- Cara plana: un bloque de piel con una sombra, **sin rasgos dibujados**.
- Brillos en **trazos cortos** sobre el metal (revólver, brazo), nunca rayas largas en
  diagonal.
- Contorno oscuro `#252018` casi completo (95 %).
- Las formas son irregulares, a mano, sin curvas perfectas ni bloques geométricos.

**Aplicado al zombi**

| | Vaquera | Zombi (versión 3) | Zombi (lo que se pide) |
| --- | --- | --- | --- |
| Lo más ancho | Ala del sombrero, 27 px | Torso, 30 px | Hombrera y peto, **24–26 px** |
| Casco o cabeza | Cabeza ≈ 13 px dentro del sombrero | Casco de 17 px | Casco de **13–14 px** |
| Pies | 8–11 px | 14–19 px | **10–13 px** |
| Armadura | — | Gris azulado | **Los grises del revólver** |
| Uniforme | Cafés cálidos | Azul apagado | **Caqui militar con sus cafés** (o un azul cálido y oscuro, en área pequeña) |
| Cara | Plana, sin rasgos | Perfil con ojos, nariz y boca | Plana, verde, **solo los 2 ojos** y una mancha de sangre |

Una prueba rápida: recolorear la versión 3 con estos colores ya la acerca bastante, pero
la silueta de barril sigue delatándola. Lo que más pesa son las proporciones.

## Concepto

Un antidisturbios convertido en zombi, contado con **pocas formas grandes**:

- **Casco** redondo con visera bajada. Detrás, la cara verdosa y **dos ojos amarillos**,
  que es lo que más se lee.
- **Peto** grande, una sola pieza con un brillo.
- **Una hombrera** (la del lado visible) y **rodilleras**.
- **Uniforme caqui militar** visible en el brazo y entre las piernas.
- **Postura** de zombi: encorvado, cabeza adelantada, un brazo estirado al frente y una
  pierna arrastrando.

Los detalles pequeños sí van, pero **solo en los puntos focales** (ver *Nivel de detalle*).
Lo que se descarta es el ruido repartido: texturas, rayones por toda la armadura y
grietas de telaraña.

Es un diseño propio. Tomamos solo la idea genérica del equipo antidisturbios: nada de logos,
textos ni insignias reales.

## Tamaño

| Medida | Zombi | Vaquera |
| --- | --- | --- |
| Alto, del casco a la suela | **58 px** (232 en pantalla) | 56 px |
| Ancho máximo, sin el brazo estirado | **24–26 px**, en la hombrera | 27 px, en el ala del sombrero |
| Ancho con el brazo estirado | **40 px como máximo** | — |
| Píxeles visibles por cuadro | **≈ 1150 como máximo** | ≈ 920 |

Más pesado que la vaquera, pero no el doble: la primera versión tenía 1450 px por cuadro
y 45–52 de ancho, y por eso se veía enorme a su lado.

## Nivel de detalle

Medido en las hojas de la vaquera con `tools/sprite_style.py`. Son **rangos**: quedarse
corto se ve tan mal como pasarse.

| Regla | Rango | Vaquera |
| --- | --- | --- |
| Colores del cuerpo | **13–16** | 16 |
| Píxeles sueltos (sin vecino del mismo color) | **11–17 %** | 15 % |
| Tonos oscuros (luminancia < 85) | **65–90 %** del cuerpo | 85 % |
| Acentos claros (luminancia > 120) | **8–20 %** del cuerpo | 14 % |
| Contorno | **Oscuro y completo** (`#252018`), solo se interrumpe donde la luz pega fuerte | 95 % oscuro |

Los efectos (chispas, fogonazo) no cuentan para los colores: `shoot.png` tiene 25 por
el fogonazo.

**Dónde va el detalle de 1 px** (es lo que da calidad):

- **Visera:** borde claro de 1 px arriba y un reflejo diagonal de 2–3 px.
- **Cara:** ojos de 1 px muy claros, sombra bajo la visera, boca o dientes de 1–2 px y
  un hilo de sangre.
- **Placas de armadura:** una línea de luz de 1 px en el borde superior de cada placa
  (casco, hombrera, peto, rodillera) y una línea oscura de 1 px donde se juntan dos piezas.
- **Mano estirada:** 2–3 dedos separados por 1 px.
- **Cinturón y correas:** una hebilla clara de 1–2 px; una correa oscura en el muslo.
- **Piernas:** pliegues del uniforme y la línea de la suela, como en las botas de la
  vaquera (ahí tiene su 22 % de píxeles sueltos).
- **Daño:** una abolladura en el casco, una sola grieta corta en el peto, una rasgadura
  del uniforme que deja ver piel.

**Dónde no va:** dentro de las placas grandes. El centro del peto y del casco se queda en
2–3 tonos limpios. Así el detalle se agrupa y no se vuelve granulado.

**Valores:** casi todo el cuerpo en tonos oscuros (sombra y base de la armadura, uniforme,
botas). La luz de la armadura y los brillos solo en los bordes que miran hacia arriba y
al frente. Los ojos, la piel y los brillos son lo único claro, igual que la piel y el
metal del revólver en la vaquera.

Dos pruebas rápidas en Aseprite:

1. **Silueta:** rellena el cuadro de un solo color. Debe reconocerse el casco, el brazo
   estirado y la postura encorvada.
2. **Junto a ella:** pon el cuadro al lado de `assets/sprites/player/walk.png` a 100 %.
   Si el zombi se ve granulado, sobra detalle repartido; si se ve plano o de juguete, faltan
   detalles de 1 px en los puntos focales o la armadura está demasiado clara.

## Paleta (16 colores, casi todos de la vaquera)

| Parte | Colores |
| --- | --- |
| Contorno | `#252018` |
| Armadura: los grises del revólver | `#2c2c2c` `#424242` `#505050` `#868689` |
| Brillos cortos en los bordes de las placas y la visera | `#a7a8a8` |
| Uniforme caqui: sombra, base, luz (sus cafés) | `#463322` `#684833` `#876439` |
| Piel de zombi: sombra, base, luz (verde cálido y saturado) | `#4d5a1c` `#76862c` `#a9b956` |
| Sangre | `#6b333a` `#902004` |
| Ojos | `#fff1a0`, 1 px por ojo |
| Hebilla | `#9c8526` |

Si prefieres mantener el uniforme azul, usa solo 2 tonos oscuros y algo cálidos
(`#2b3550` `#3e4d72`) y que ocupe poco: debajo de la armadura, no como mancha grande.

**Contraste:** el fondo es `#202229`. Una masa oscura se lee bien sobre él si tiene el
contorno completo y acentos claros, como la vaquera.

## Plantilla de cuadro (todas las hojas)

| Medida | Valor |
| --- | --- |
| Cuadro | **72 × 72** |
| Cuerpo de pie | centrado en x **27.5**, de la punta del casco (y 9) a la última fila de la bota (**y 66**) |
| Pivote en código | `anchor_x = 27.5`, `ground_y = 68` (igual que la vaquera: 2 filas debajo de la bota) |
| Espacio al frente | hasta x 71 para el brazo del ataque y la caída |

Usar el mismo cuadro en todas las hojas evita tener que medir pivotes distintos. Si
respetas la plantilla, el código no cambia.

## Hojas

| Archivo | Hoja | Cuadros | Reproducción | Qué hace cada cuadro |
| --- | --- | --- | --- | --- |
| `walk.png` | 576 × 72 | 8 | Ciclo, **6 fps** (lento) | Paso cojo: 0–3 adelanta la pierna buena, 4–7 arrastra la otra. El brazo estirado se balancea poco. El cuerpo sube y baja 1 px |
| `attack.png` | 432 × 72 | 6 | Una vez, 10 fps | 0–1 toma impulso hacia atrás, **2 golpe** (la garra llega a x ≈ 66), 3 sostiene, 4–5 regresa a la postura de caminar |
| `hurt.png` | 216 × 72 | 3 | Una vez, 12 fps | 0 retrocede 2 px con **chispas** en el peto (la bala rebota en la armadura), 1 chispas que se apagan, 2 vuelve a la postura |
| `death.png` | 576 × 72 | 8 | Una vez, 10 fps; **el cuadro 7 se queda** | 0–1 sacudida, 2–3 cae de rodillas, 4–6 se desploma hacia adelante, 7 tendido en el suelo (y 58–66, x 12–71) |
| `idle.png` *(opcional)* | 288 × 72 | 4 | Ciclo, 4 fps | Balanceo de 1 px y respiración. Si no existe, se usa el cuadro 0 de `walk` |

Ubicación: `assets/sprites/zombie/<acción>.png`.

**Cuadros clave para el código:** golpe en `attack` 2, fin de la animación de daño en `hurt` 2
y cuerpo tendido en `death` 7.

**Estado:** la versión 4 de `walk.png` está en el juego y ya se ve del mismo estilo que
la vaquera: formas a mano, masa oscura y brillos cortos. Mide 14 colores, 17 % de píxeles
sueltos y 87 % de tonos oscuros. Es más grande que el máximo (≈ 1340 px por cuadro), lo
cual se aceptó porque es un enemigo blindado y pesado. Sus acentos claros son pocos (4 %);
si se pierde contra el fondo, sube los ojos, el borde de la visera y los brillos del casco
y la hombrera.
`hurt.png` también está en el juego. El primer impacto lo hace retroceder: muestra el
cuadro 0 al instante y se queda quieto los 3 cuadros (0.25 s). Durante los 0.5 s
siguientes, las balas le quitan vida y sacan chispas del peto pero no lo frenan.

**Chispas (`assets/sprites/effects/sparks.png`):** recortadas de los cuadros 0 y 1 de
`hurt.png` (x 21–40, y 27–38), solo los píxeles `#fff1a0` y `#fbaa38`. Son 2 cuadros de
20 × 12 a 12 fps. Se dibujan encima del zombi en el mismo lugar que en `hurt.png`, así
que el impacto se ve igual camine o retroceda. Si redibujas las chispas de `hurt.png`,
vuelve a recortarlas o dibuja esta hoja aparte; el pivote es (6.5, 6): el centro del
cuerpo, a la altura de la bala.
`death.png` también está en el juego. La bala que lo mata empieza en el cuadro 1 (la
sacudida con chispas), porque el cuadro 0 es la misma pose de caminar y retrasaría el
impacto. Cae en 0.7 s, se queda tendido en el cuadro 7 durante 1.5 s
(`ZOMBIE_CORPSE_TIME`), se desvanece en 0.6 s y luego aparece otro. `attack.png` está en el juego. Lo generé por script a partir del cuadro 0 de `walk`, siguiendo el boceto del usuario. Las piernas no cambian, y la garra llega a x ≈ 56 y el arco del zarpazo a x 63, no a 66. El brazo se ve más liso que el resto del cuerpo, así que vale la pena retocar a mano los cuadros 1–2. El zarpazo pega en el cuadro 2.

## Resistencia

80 de armadura dejan pasar el 56 % del daño (`100 / (100 + 80)`). Con la misma vida que
un zombi común (100), necesita 10 balas del arma de nivel 1 en vez de 5. Las fórmulas
están en el [README](../README.md#enemigo-y-daño).

## Indicación para un generador de imágenes

**Lo más importante: dale al generador la hoja de la vaquera como imagen de referencia
de estilo** (`assets/sprites/player/walk.png`, ampliada a 8× con vecino más cercano). Sin
referencia, cada generación sale con un estilo distinto. Si tu herramienta permite editar
una imagen, mejor aún: pide que transforme a la vaquera en el zombi, así hereda el trazo y
las proporciones.

Los generadores entienden mejor el inglés:

```text
Use the attached cowgirl sprite as the exact style reference: same pixel size, same
proportions, same dark outline, same warm saturated color ramps and neutral gray metal,
same flat faces and short highlight strokes. The new character must look drawn by the
same artist for the same game.
Pixel art sprite sheet, side view facing right, single row of 8 frames on a transparent
background, each frame 72x72 pixels, character 58 pixels tall, slim build like the
reference: widest at the shoulder pad (about 25 px), tapering down to narrow feet.
Character: a zombie riot-control soldier. Small round dark gray metal helmet with a lowered
visor, flat green zombie face with two tiny yellow eyes, one gray chest plate and one
shoulder pad, knee pads, khaki brown military uniform, dark boots, a few blood stains.
Pose: hunched forward, head pushed ahead, one arm reaching forward, dragging one leg.
Animation: slow limping walk cycle, 8 frames.
No blue tones, no cold desaturated colors, no noise, no dithering, no anti-aliasing,
no text, no logos, no insignia.
```

Para las otras hojas, cambia la línea `Animation:` y el número de cuadros:

- `attack`: `lunging claw attack, 6 frames: wind up, wind up, strike with the arm fully extended, hold, recover, recover`.
- `hurt`: `hit reaction, 3 frames: recoil with a few bright sparks bouncing off the chest plate, sparks fading, back to stance`.
- `death`: `death, 8 frames: jolt, jolt, drop to knees, knees, collapse forward, collapse, collapse, lying face down on the ground`.

## Limpieza después de generar

Los generadores casi nunca respetan la cuadrícula ni la paleta. Antes de entregar la hoja:

1. Reduce la imagen a 1× con *vecino más cercano*, de modo que 1 px del arte sea 1 px.
2. **Fuerza la paleta:** en Aseprite, carga los 16 colores de arriba y usa
   *Sprite → Color Mode → Indexed* con *Dithering: None*. Esto quita los colores de
   sobra y gran parte del ruido. Luego vuelve a *RGBA*.
3. Limpia a mano: borra el ruido dentro de las placas grandes y conserva o añade los
   detalles de 1 px de los puntos focales.
4. Ajusta cada cuadro a 72 × 72 con la bota en la fila **66** y el centro del cuerpo en
   **x 27.5**. Si el cuerpo baila entre cuadros, el zombi se verá temblar.
5. El fondo debe ser transparente de verdad (alfa 0). Exporta en *RGBA*.
6. Mídela contra la vaquera:

   ```bash
   python3 tools/sprite_style.py assets/sprites/zombie/walk.png 72
   ```

   Revisa colores, píxeles sueltos, área y equilibrio de tonos, y marca cada uno como
   `OK`, `POCO` o `MUCHO`. La vaquera da `OK` en todo.

   **Ojo:** mide cantidades, no estilo. La versión 3 dio `OK` en todo y aun así no se veía
   del mismo juego. La prueba final siempre es ponerlo junto a ella en pantalla.

## Al entregar

Basta con dejar los PNG en `assets/sprites/zombie/` y avisar:

1. Qué hojas hay y cuántos cuadros tiene cada una.
2. Si moviste el cuadro clave del golpe o la plantilla de 72 × 72.
