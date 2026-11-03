# Enemigos: catálogo y plantilla de estilo

Especificación del primer enemigo, un zombi con equipo antidisturbios militar, y guía de
estilo para cualquier enemigo nuevo. Siguen las reglas generales de
[`SPRITES.md`](SPRITES.md): PNG RGBA de 8 bits, a 1×, una fila de cuadros y mirando a la
**derecha**.

**La regla principal: que parezca dibujado por la misma mano que la vaquera.** No basta
con igualar la cantidad de detalle. También hay que copiar sus **colores**, sus
**proporciones** y su **forma de sombrear**. Lo que más delata a un sprite de otro estilo
son las proporciones (un cuerpo de barril, un casco enorme) y los colores fríos y apagados.

Las variantes conservan el **estilo de rostro abstracto y su sombra**, sin añadir
ojos grandes, dientes, nariz ni rasgos detallados. Cada profesión utiliza su cabeza,
ropa y equipo completos: la cara del juego no es la careta del antidisturbios.
Solo `riot` es la fuente aprobada de esa careta y sus placas; las demás variantes se
generan desde ella y no deben copiar sus efectos de ataque. `riot_shield` conserva el
equipo como una variante generada. El soldado lleva
casco militar con el rostro descubierto; el bombero lleva su casco propio y el
motociclista su visor de moto, sin heredar el marco del RIOT. Los civiles llevan pelo
y ropa; no reciben hombreras, peto ni rodilleras al cambiar de animación.

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
3. **Números:** `python3 tools/sprite_style.py assets/sprites/zombies/riot/walk.png 72` marca cada
   regla como `OK`, `POCO` o `MUCHO`. Mide cantidades, no estilo: la prueba final siempre
   es verlo junto a ella en pantalla.

## Paleta y referencia real

La hoja RIOT aprobada utiliza **14 colores**, con piel `#4a5240`, `#6f7a5c` y
`#9aa37e`. Esos valores se miden en el PNG y son los que protege el exportador;
los verdes amarillentos del diseño inicial no describen la piel del archivo actual.
La ropa de las variantes añade las rampas cálidas existentes de la vaquera. Se usa
una paleta compartida y limitada, sin introducir tonos arbitrarios por cada imagen.

`sprite_style.py` compara con la vaquera como orientación: incluso el RIOT original
supera su límite de área y tiene menos acentos claros. Esas diferencias no justifican
redibujar un cuerpo aprobado. Se revisan proporciones, agrupación de píxeles y lectura
junto a los originales; `make_zombies.py --verify` comprueba la paleta final permitida.

| Parte | Colores |
| --- | --- |
| Contorno | `#252018` |
| Armadura: los grises del revólver | `#2c2c2c` `#424242` `#505050` `#868689` |
| Brillos cortos en los bordes de las placas y la visera | `#a7a8a8` |
| Tela cálida de las variantes: sombra, base, luz | `#463322` `#684833` `#876439` |
| Piel de zombi original: sombra, base, luz | `#4a5240` `#6f7a5c` `#9aa37e` |
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

Los cuatro originales se conservan **byte por byte** en `assets/sprites/zombies/riot/`.
El élite mantiene copias de ese mismo arte en `assets/sprites/zombies/elite/`, con su
tono propio aplicado por el juego. Todas las profesiones, incluidos ambos, tienen
sus siete hojas en `assets/sprites/zombies/<id>/`; las acciones originales del
antidisturbios no se sustituyen al añadir reposo, carrera y forcejeo:

| Archivo | Hoja | Cuadros | Reproducción | Qué hace cada cuadro |
| --- | --- | --- | --- | --- |
| `idle.png` | 288 × 72 | 4 | Ciclo, 3 fps | Respiración y balanceo de reposo, sin avanzar |
| `walk.png` | 576 × 72 | 8 | Ciclo, 7.95 fps por ritmo base | Paso cojo: 0–3 adelanta la pierna buena, 4–7 arrastra la otra |
| `run.png` | 576 × 72 | 8 | Ciclo, ritmo base por velocidad del corredor | Carrera con apoyo y fase aérea propios; no es acelerar `walk` |
| `attack.png` | 432 × 72 | 6 | Una vez, 11 fps | 0–1 toma impulso, **2 golpe** (la garra llega a x ≈ 56 y el arco a x 63), 3 sostiene, 4–5 regresa |
| `hurt.png` | 216 × 72 | 3 | Una vez, 12 fps | 0 retrocede con **chispas** en el peto, 1 chispas que se apagan, 2 vuelve a la postura |
| `death.png` | 576 × 72 | 8 | Una vez, 10 fps; **el cuadro 7 se queda** | 0–1 sacudida, 2–3 cae de rodillas, 4–6 se desploma, 7 tendido (y 58–66, x 12–71) |
| `caught.png` | 288 × 72 | 4 | Ciclo, 6 fps | Se retuerce en el cepo, la red o el lazo; puede ser levantado o girado por la trampa |

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

## Profesiones y variantes

Hay **25 familias y 50 variantes**: las 24 familias pedidas y el antidisturbios de élite
existente, cada una normal y corredora. Cinco civiles masculinos y cinco femeninos tienen
identidad, ropa y silueta propias. El catálogo de `src/game/zombie.c` es la fuente de los
nombres, descripciones, equipo y estadísticas que utiliza el juego.

Valores a nivel 1. `Vel.` multiplica `ZOMBIE_SPEED = 63.6` píxeles por segundo; `Daño`
es el daño bruto antes de aplicar la armadura del personaje.

| ID | Familia | Vida normal / corredor | Armadura | Daño | Vel. normal | Protección |
| --- | --- | --- | --- | --- | --- | --- |
| `riot` | Antidisturbios | 100 / 55 | 85 | 15 | 1.00 | Peto, casco y rodilleras |
| `soldier` | Soldado | 110 / 61 | 65 | 16 | 1.05 | Chaleco militar y casco |
| `police` | Policía | 95 / 52 | 45 | 14 | 1.10 | Chaleco policial |
| `riot_shield` | Antidisturbios con escudo | 140 / 77 | 110 | 16 | 0.72 | Escudo, casco y peto pesado |
| `civil_male_1` | Jornalero | 90 / 50 | 0 | 12 | 1.00 | Ropa |
| `civil_male_2` | Comerciante | 100 / 55 | 0 | 13 | 0.95 | Ropa |
| `civil_male_3` | Viajero | 85 / 47 | 0 | 12 | 1.10 | Ropa |
| `civil_male_4` | Minero | 110 / 61 | 0 | 14 | 0.90 | Ropa |
| `civil_male_5` | Granjero | 95 / 52 | 0 | 13 | 1.05 | Ropa |
| `civil_female_1` | Viajera | 85 / 47 | 0 | 12 | 1.05 | Ropa |
| `civil_female_2` | Comerciante | 95 / 52 | 0 | 13 | 1.00 | Ropa |
| `civil_female_3` | Costurera | 90 / 50 | 0 | 12 | 1.10 | Ropa |
| `civil_female_4` | Ranchera | 100 / 55 | 0 | 14 | 0.98 | Ropa |
| `civil_female_5` | Pobladora | 88 / 48 | 0 | 12 | 1.08 | Ropa |
| `burned` | Quemado | 80 / 44 | 0 | 13 | 0.95 | Sin protección |
| `skeleton` | Zombi muy degradado | 65 / 36 | 0 | 11 | 1.10 | Sin protección |
| `dog` | Perro infectado | 65 / 36 | 0 | 13 | 1.55 | Sin protección |
| `sheriff` | Sheriff | 110 / 61 | 30 | 16 | 1.05 | Chaleco bajo el abrigo |
| `cowboy` | Vaquero | 105 / 58 | 10 | 15 | 1.10 | Cuero ligero |
| `motorcycle` | Motociclista | 120 / 66 | 55 | 16 | 0.95 | Casco y cuero reforzado |
| `priest` | Sacerdote | 90 / 50 | 0 | 12 | 0.95 | Sotana |
| `jailer` | Carcelero | 130 / 72 | 75 | 17 | 0.85 | Chaleco de guardia |
| `firefighter` | Bombero | 135 / 74 | 45 | 17 | 0.80 | Casco y chaquetón |
| `butcher` | Carnicero | 150 / 83 | 20 | 19 | 0.80 | Delantal de cuero grueso |
| `elite` | Antidisturbios de élite | 150 / 83 | 120 | 20.25 | 1.00 | Armadura reforzada |

Un corredor conserva la profesión, la protección y el daño de su familia. Su vida base
es el **55 %**, redondeada al entero más cercano, y su velocidad es **1.8 veces** la normal.
No se le añade armadura genérica: un civil corredor sigue sin protección. Las distintas
familias corren con su hoja `run` y conservan sus propias hojas de ataque, daño y muerte.

## Escalado y encuentros

Se reutilizan `level_health`, `level_armor` y `damage_at_level`, con las constantes del
juego:

```text
factor por nivel = 1 + 0.6 × (nivel − 1)
vida             = redondear(vida base × factor)
daño bruto       = daño base × factor
armadura equipada= armadura base + 8 × (nivel − 1)
sin protección   = 0, en todos los niveles
daño recibido    = daño bruto × 100 / (100 + armadura)
velocidad        = velocidad de la profesión × 63.6 [× 1.8 si es corredor]
```

La **velocidad no aumenta con el nivel**. Viento, río y trampas pueden modificar su
movimiento como antes. El nivel se limita al intervalo de 1 a `MAX_LEVEL` (50) antes
de calcular vida, daño y armadura. Los civiles y criaturas sin equipo llaman
`level_armor(0, 0, nivel)`.

Las referencias antiguas `ZOMBIE_COMMON` y `ZOMBIE_RUNNER` se mantienen para compatibilidad
y pruebas del equilibrio previo; sus valores y escalado no se usan para inventar
protección en el catálogo nuevo. `ZOMBIE_RIOT` y `ZOMBIE_ELITE` conservan sus valores y
referencias originales.

La ruta 1-1 conserva sus diez antidisturbios originales. Las rutas siguientes introducen
las otras profesiones y los corredores de forma determinista, incluyendo todas las
50 variantes antes de terminar 1-5. Los espacios `SPOT_RUNNERS` siempre contienen
corredores. Se conservan los **78 enemigos**, las tres apariciones originales del élite,
los niveles de misión, los cofres y las fórmulas de experiencia. El corredor de élite
es una variante de encuentro, sin añadir una nueva recompensa de jefe.

El perro ocupa el mismo cuadro de 72 × 72 y mantiene el suelo en y 68, con un cuerpo
cuadrúpedo ancho y cabeza de hasta 38–40 píxeles de alto. Su colisión mide **38 píxeles
de alto y 22 de semiancho**, antes de multiplicar por `SPRITE_SCALE`. La línea normal
de disparo queda dentro de esa altura: no exige cambiar la puntería ni disparar al aire.

`tests/test_zombie_catalog.c` comprueba las 50 variantes, el escalado, las 179 entradas
del registro de animación (los cuatro alias del antidisturbios apuntan a sus originales),
la sincronía del ataque, el cuerpo muerto
en el cuadro 7, la liberación de trampas y la cobertura de toda la campaña. La prueba
de progresión recorre la economía de los cinco niveles y mantiene sus límites de combate.

`tests/zombie_render.c` usa un renderer SDL en memoria y únicamente las cuatro texturas
originales de prueba: confirma que las acciones nuevas ausentes no vuelven invisible al
enemigo ni al élite, que el cuadro se limita a la hoja disponible y que una nueva hoja
presente tiene prioridad sobre la sustitución temporal. No reemplaza una revisión visual.
