# Especificación de sprites — THE MIRACLE

Medidas tomadas del arte de la vaquera (`assets/sprites/characters/cowgirl/`), que es la
plantilla de todos los personajes ([`CHARACTERS.md`](CHARACTERS.md)). Todas las medidas están en
**píxeles del arte (1×)** salvo que diga "en pantalla" (4×).

## Reglas para cualquier hoja

| Regla | Valor |
| --- | --- |
| Formato | **PNG RGBA de 8 bits, sin entrelazado.** No uses modo indexado ni paleta: `tools/embed_assets.py` lo rechaza. En Aseprite: *Color Mode → RGBA*. |
| Escala | Dibuja a 1×. El juego escala a 4× sin suavizado. |
| Distribución | Una sola fila de cuadros del mismo tamaño, pegados y sin separación. El espacio vacío dentro de cada cuadro no importa. |
| Tamaño de la hoja | Ancho = ancho del cuadro × número de cuadros. Alto = alto del cuadro exacto. `--verify` lo comprueba. |
| Dirección | Solo mirando a la **derecha**. La izquierda se genera espejando. |
| Bordes | Sin difuminado ni suavizado. Se permite semitransparencia. |
| Ubicación | `assets/sprites/<entidad>/<acción>.png`, por ejemplo `assets/sprites/zombies/riot/idle.png`. Ver [`ASSETS.md`](ASSETS.md). |

## Cuerpo de la vaquera (medido)

| Medida | Arte | En pantalla |
| --- | --- | --- |
| Ancho del cuerpo | **27 px** (hasta 29 en el paso más abierto) | 108 px |
| Alto, de la punta del sombrero a la suela | **56 px** | 224 px |
| Salto agachada | 50–53 px | 200–212 px |
| Línea de suelo | 2 filas debajo de la última fila de la bota | — |

## Hojas actuales

| Hoja | Cuadro | Cuadros | Cuerpo en el cuadro (x) | Última fila de bota | Pivote en código (`anchor_x`, `ground_y`) |
| --- | --- | --- | --- | --- | --- |
| `walk.png` | 42 × 67 | 8, en ciclo, 12 fps (15 corriendo) | 6–32 | 59 | 19.5, 61 |
| `jump.png` | 54 × 82 | 0–5 siguen el arco, 6–7 aterrizaje | 12–38 | 67 | 25.5, 69 |
| `shoot.png` | 81 × 80 | 8, una vez, 16 fps | 18–44 | 66 | 31.5, 68 |
| `bullet.png` | 8 × 6 | 4, en ciclo, 12 fps | bola en 1–6 | — | 4, 3 (centro de la bola) |

Cuadros del disparo: 0–2 desenfunda, 3 apunta, **4 dispara** (sale la bala), 5–6 retroceso,
7 enfunda. El humo no se dibuja en la hoja: lo anima el juego (`src/game/smoke.c`).

### Plantilla recomendada para hojas nuevas

Usa el cuadro de **81 × 80** de `shoot.png`, con el cuerpo en **x 18–44** y la última fila
de la bota en **y 66**. Así se reutiliza el pivote tal cual (`31.5, 68`) sin medir nada,
y hay 36 px libres al frente para armas, efectos o golpes.

Si usas otro tamaño también funciona: el pivote se mide y se anota en el `AnimationDef`
de `src/game/player.c`.

## Arma (medida en `shoot.png`)

El revólver está dibujado dentro de cada cuadro, no es un sprite aparte. Separarlo solo
vale la pena para armas intercambiables, y eso implica dibujar también el brazo aparte.

| Medida | Cuadro 3 (apunta) | Cuadro 4 (dispara) |
| --- | --- | --- |
| Arma completa | x 45–63, y 30–42 (19 × 13 px) | igual |
| Cañón | 4 filas de grosor (y 31–34), punta en x 63 | igual |
| **Boca del cañón** | **x 64, y 32.5** | — |
| Fogonazo | — | x 64–79, y 29–38 (16 × 10 px) |

Respecto al pivote del cuerpo, la boca del cañón está **32.5 px adelante y 35.5 px arriba
del suelo**, que en pantalla son 130 px adelante y 142 px arriba. De ahí sale la bala.

## Bala (`bullet.png`)

| Medida | Valor |
| --- | --- |
| Hoja | **32 × 6**: 4 cuadros de **8 × 6** |
| Bola | **6 × 6 px**, redonda, en x 1–6 de cada cuadro (centro en 4, 3) |
| Alineación | Centrada en el cañón: ocupa y 30–35 del disparo, 1 fila más que el cañón (31–34) arriba y abajo. Su borde trasero nace en la punta (x 64) |
| Animación | 4 cuadros en ciclo a 12 fps (gira); brillo cálido en los cuadros 1 y 3 |
| Colores | Contorno en grises medios (`#696867`, `#868689`) para que se vea sobre el fondo oscuro; interior `#424242`–`#a7a8a8` |
| En juego | Sale de la boca del cañón en el cuadro 4, a 900 px/s, y desaparece al salir de la pantalla |

**Por qué 6 × 6 y no 5 × 5:** el centro del cañón cae entre dos filas; una bola de altura
par queda centrada exacta, una impar queda medio píxel chueca.

**Contraste:** detrás de los personajes el paisaje es oscuro (luminancia ≤ 62, ver
[`LANDSCAPE.md`](LANDSCAPE.md)). Los colores muy oscuros (`#252018`, `#2c2c2c`) desaparecen
sobre él; para cualquier objeto pequeño usa un contorno gris medio o más claro.

Otras balas o proyectiles: mismo formato de cuadro (8 × 6) si son del mismo calibre.

**Ojo:** exporta siempre a 1×. Un sprite exportado a 4× se vería a 16× en el juego.

## Pantalla (fondos y enemigos)

| Medida | En pantalla | Arte (÷4) |
| --- | --- | --- |
| Ventana | 960 × 540 | **240 × 135** |
| Línea del suelo | y = 470 | y ≈ 117 |
| Altura de la vaquera | 224 px | 56 de los 135 de alto |

- Los fondos se dibujan en un lienzo de 240 × 135 a 1×. Capas, medidas, paletas y temas por
  nivel: [`LANDSCAPE.md`](LANDSCAPE.md).
- Los enemigos van a la misma escala que la vaquera: un humano de unos 56 px de alto. Estilo
  y plantilla: [`ZOMBIE.md`](ZOMBIE.md).
- Dónde va cada archivo y cómo se nombra: [`ASSETS.md`](ASSETS.md).

## Paleta (23 colores en uso)

```text
#252018 #463322 #2c2c2c #424242 #684833 #d99a5b #902004 #fedca3
#6b333a #89411f #868689 #a7a8a8 #9c8526 #505050 #876439 #696867
#d03305 #e55d22 #999a9c #8a4322 #fbaa38 #fff1a0 #d7ab57
```

Los naranjas y amarillos (`#d03305`, `#e55d22`, `#fbaa38`, `#fff1a0`) son los del
fogonazo y sirven para la bala.

## Qué indicar al entregar una hoja nueva

1. Nombre del archivo y número de cuadros.
2. Qué hace cada cuadro, sobre todo el **cuadro clave**: en cuál sale la bala, pega el
   golpe, termina la acción, etc.
3. Si se repite en ciclo (como caminar) o se reproduce una sola vez (como disparar).
4. Si no usaste la plantilla de 81 × 80, dónde quedó el cuerpo dentro del cuadro.
