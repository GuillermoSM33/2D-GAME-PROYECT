# SWAT: concepto de vestuario anterior

El usuario aprobó el concepto de esta hoja el 2026-11-13. Después pidió ajustar
las proporciones y el estilo a la vaquera; la versión actual está en
[game_style.md](game_style.md). Este documento conserva la procedencia del
concepto anterior. Se generó con la herramienta integrada
**imagegen**, en modo `style-transfer`, usando sus referencias adjuntas; no se usó
el CLI ni una API externa. La referencia de vestuario fue el operador superior
derecho de la cuadrícula de u/lbcher: casco carbón, ópticas verdes, pasamontañas,
chaleco oscuro y correas marrones.

- [Original generado, RGBA con su transparencia intacta](tactical_walk_source.png):
  1448 × 1086, cuatro columnas y dos filas.
- [Adaptación nativa](tactical_walk_native.png): ocho cuadros de 42 × 67.
- `walk_source.png` conserva además el dibujo anterior sin sobrescribirlo.

`python3 tools/prepare_swat_art.py` prepara la adaptación (requiere Pillow solo
para esta tarea de autoría). Aplica la misma escala `56 / 418` y el mismo origen
`(-6, -5)` a los ocho recortes de 362 × 543; elimina el alfa residual exterior y
reduce la hoja completa a una paleta común de 32 colores, sin tramado. No cambia
la longitud de ninguna pierna ni reconstruye las articulaciones. El PNG original
permanece intacto. La compilación solo necesita la biblioteca estándar de Python.

`python3 tools/rebuild_swat.py` deriva las 23 hojas del juego desde el PNG nativo.
Caminar conserva exactamente sus píxeles. Los brazos de las acciones se dibujan
aparte sobre el casco, chaleco y piernas extraídos del mismo personaje. El reposo
usa el primer cuadro. Sentado conserva el torso y la cabeza en tres cuartos.

## Prompt final usado

```text
Use case: style-transfer. Asset type: production pixel-art character walking sprite sheet for a 2D game.
REFERENCE ROLES: The image containing a 3-by-2 grid of torso designs with a credit at the bottom is the OUTFIT REFERENCE. Use ONLY the THIRD / TOP-RIGHT black tactical operator from that grid: charcoal helmet, raised green tactical optical goggles, black balaclava, tiny warm eye opening, charcoal plate carrier, brown harness straps, magazine pouches, dark tactical trousers, knee pads, gloves, reinforced black boots. Other attached images showing the current game's character labelled walk/shoot or stand/walk/shoot/sit are FAILED RESULTS; do not preserve their proportions or their alien head, angular staircase shoulders, box chest, unequal legs or twisted knees.
PRIMARY REQUEST: Redraw this SWAT as a believable human adult tactical operator in cohesive hand-drawn pixel art, wearing the selected third outfit. Human anatomy: modest compact helmet/head, sloping natural shoulders, visible neck-to-shoulder connection under the balaclava, a fitted chest following a ribcage, a waist and hips, TWO equally long and equally muscular legs and proportional boots. Avoid chibi, oversized head, skeleton-thin limbs, swollen shorts, conical alien mask, literal stair-shaped shoulders, rigid robotic gait, asymmetric thigh sizes. Both legs use the SAME limb model and differ only by walking pose. The gear should describe a real SWAT operator at low resolution.
LAYOUT: exactly EIGHT full-body walk frames arranged in a 4-column by 2-row uniform grid on a completely TRANSPARENT background. No labels, no grid lines, no shadows, no text, no watermark, no branding. Each cell has the same dimensions and enough empty margin; no overlap or missing feet. The exact same character and costume in each cell, always facing RIGHT in a consistent three-quarter side view. Frame order left to right top row then left to right bottom row. A smooth natural full 8-frame walking cycle with alternating foot contacts, small lift of the swinging foot, soft knee flexion, weight shift and subtle opposite arm swing. Arms hang naturally with relaxed, slightly flexed elbows and empty gloved hands, so weapons can be added by the game. NO weapons in the sheet. Small stride, feet pass under the hips, equal limb lengths, identical boots. Head/torso remain stable with at most one logical pixel of vertical bob. Last frame must transition naturally into the first.
PIXEL STYLE AND SCALE: Design for a 42 by 67 LOGICAL PIXEL cell, character 56 logical pixels tall with helmet top near row 4 and both grounded soles at row 59. Render every logical pixel as a large, consistent crisp square; a recommended 8x sheet canvas is 1344 by 1072 pixels. Keep anatomy readable at that small original game scale, with clustered pixel shapes, natural silhouettes, restrained dark outlines and 24-32 muted colors. Upper-left light, warm charcoal, desaturated gunmetal, dark brown leather, small olive-green optic glass accents. No blurred outlines, no shiny 3D plastic, no anti-aliased painting, no gradients in the background. Produce only the finished transparent sprite sheet.
```
