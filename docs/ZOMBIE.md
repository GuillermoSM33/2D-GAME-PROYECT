# Enemigo: zombi antidisturbios

Especificación del primer enemigo, un zombi con equipo antidisturbios militar, y guía de
estilo para cualquier enemigo nuevo. Siguen las reglas generales de
[`SPRITES.md`](SPRITES.md): PNG RGBA de 8 bits, a 1×, una fila de cuadros y mirando a la
**derecha**.

**La regla principal: que parezca dibujado por la misma mano que la vaquera.** No basta
con igualar la cantidad de detalle. También hay que copiar sus **colores**, sus
**proporciones** y su **forma de sombrear**. Lo que más delata a un sprite de otro estilo
son las proporciones (un cuerpo de barril, un casco enorme) y los colores fríos y apagados.

## Estilo de la vaquera

Medido en `assets/sprites/characters/cowgirl/walk.png`:

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

| | Vaquera | Zombi |
| --- | --- | --- |
| Lo más ancho | Ala del sombrero, 27 px | Hombrera y peto, **24–26 px** |
| Casco o cabeza | Cabeza ≈ 13 px dentro del sombrero | Casco de **13–14 px** |
| Pies | 8–11 px | **10–13 px** |
| Metal | Grises del revólver | **Los mismos grises** en la armadura |
| Tela | Cafés cálidos | **Caqui militar con sus cafés** |
| Cara | Plana, sin rasgos | Plana, verde, **solo los 2 ojos** y una mancha de sangre |

## Concepto

Un antidisturbios convertido en zombi, contado con **pocas formas grandes**:

- **Casco** redondo con visera bajada. Detrás, la cara verdosa y **dos ojos amarillos**,
  que es lo que más se lee.
- **Peto** grande, una sola pieza con un brillo.
- **Una hombrera** (la del lado visible) y **rodilleras**.
- **Uniforme caqui militar** visible en el brazo y entre las piernas.
- **Postura** de zombi: encorvado, cabeza adelantada, un brazo estirado al frente y una
  pierna arrastrando.

Es un diseño propio: nada de logos, textos ni insignias reales.

## Tamaño

| Medida | Zombi | Vaquera |
| --- | --- | --- |
| Alto, del casco a la suela | **58 px** (232 en pantalla) | 56 px |
| Ancho máximo, sin el brazo estirado | **24–26 px**, en la hombrera | 27 px, en el ala del sombrero |
| Ancho con el brazo estirado | **40 px como máximo** | — |
| Píxeles visibles por cuadro | ≈ 1150 (la hoja actual llega a 1340, aceptado por ser blindado) | ≈ 920 |

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

Los efectos (chispas, fogonazo) no cuentan para los colores.

**Dónde va el detalle de 1 px** (es lo que da calidad):

- **Visera:** borde claro de 1 px arriba y un reflejo diagonal de 2–3 px.
- **Cara:** ojos de 1 px muy claros, sombra bajo la visera, boca o dientes de 1–2 px y
  un hilo de sangre.
- **Placas de armadura:** una línea de luz de 1 px en el borde superior de cada placa
  (casco, hombrera, peto, rodillera) y una línea oscura de 1 px donde se juntan dos piezas.
- **Mano estirada:** 2–3 dedos separados por 1 px.
- **Cinturón y correas:** una hebilla clara de 1–2 px; una correa oscura en el muslo.
- **Piernas:** pliegues del uniforme y la línea de la suela, como en las botas de la vaquera.
- **Daño:** una abolladura en el casco, una sola grieta corta en el peto, una rasgadura
  del uniforme que deja ver piel.

**Dónde no va:** dentro de las placas grandes. El centro del peto y del casco se queda en
2–3 tonos limpios. Así el detalle se agrupa y no se vuelve granulado.

**Valores:** casi todo el cuerpo en tonos oscuros. La luz de la armadura y los brillos solo
en los bordes que miran hacia arriba y al frente. Los ojos, la piel y los brillos son lo
único claro.

Pruebas rápidas:

1. **Silueta:** rellena el cuadro de un solo color. Debe reconocerse el casco, el brazo
   estirado y la postura encorvada.
2. **Junto a ella:** pon el cuadro al lado de `walk.png` de la vaquera a 100 %. Si se ve
   granulado, sobra detalle repartido; si se ve plano, faltan detalles de 1 px en los puntos
   focales.
3. **Números:** `python3 tools/sprite_style.py assets/sprites/zombie/walk.png 72` marca cada
   regla como `OK`, `POCO` o `MUCHO`. Mide cantidades, no estilo: la prueba final siempre
   es verlo junto a ella en pantalla.

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

## Plantilla de cuadro (todas las hojas)

| Medida | Valor |
| --- | --- |
| Cuadro | **72 × 72** |
| Cuerpo de pie | centrado en x **27.5**, de la punta del casco (y 9) a la última fila de la bota (**y 66**) |
| Pivote en código | `anchor_x = 27.5`, `ground_y = 68` (igual que la vaquera: 2 filas debajo de la bota) |
| Espacio al frente | hasta x 71 para el brazo del ataque y la caída |

Usar el mismo cuadro en todas las hojas evita medir pivotes distintos. El cofre usa la misma
plantilla.

## Hojas

En `assets/sprites/zombie/`, todas en el juego:

| Archivo | Hoja | Cuadros | Reproducción | Qué hace cada cuadro |
| --- | --- | --- | --- | --- |
| `walk.png` | 576 × 72 | 8 | Ciclo, 7.5 fps | Paso cojo: 0–3 adelanta la pierna buena, 4–7 arrastra la otra |
| `attack.png` | 432 × 72 | 6 | Una vez, 10 fps | 0–1 toma impulso, **2 golpe** (la garra llega a x ≈ 56 y el arco a x 63), 3 sostiene, 4–5 regresa |
| `hurt.png` | 216 × 72 | 3 | Una vez, 12 fps | 0 retrocede con **chispas** en el peto, 1 chispas que se apagan, 2 vuelve a la postura |
| `death.png` | 576 × 72 | 8 | Una vez, 10 fps; **el cuadro 7 se queda** | 0–1 sacudida, 2–3 cae de rodillas, 4–6 se desploma, 7 tendido (y 58–66, x 12–71) |

**Cuadros clave para el código:** golpe en `attack` 2, fin del retroceso en `hurt` 2 y cuerpo
tendido en `death` 7. La bala que lo mata empieza la muerte en el cuadro 1, porque el 0 es la
pose de caminar y retrasaría el impacto.

**Chispas de la armadura** (`assets/sprites/effects/armor_sparks.png`): recortadas de los
cuadros 0 y 1 de `hurt.png` (x 21–40, y 27–38), solo los píxeles `#fff1a0` y `#fbaa38`. 2
cuadros de 20 × 12 a 12 fps, pivote (6.5, 6): se dibujan encima del zombi a la altura de la
bala, camine o retroceda. Si se redibuja `hurt.png`, hay que volver a recortarlas.

**Pendiente:** los cuadros 1–2 de `attack.png` se generaron por script a partir de `walk` y el
brazo se ve más liso que el resto; conviene retocarlos a mano.

Vida, armadura, daño y cómo escalan con el nivel: [README](../README.md#niveles-cofres-y-experiencia).
