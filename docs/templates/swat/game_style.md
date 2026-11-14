# SWAT: misma dirección de arte que la sheriff

La revisión posterior de [mangas pintadas y porte del arma](authored_arms.md)
sustituye los brazos procedimentales de las acciones principales descritas aquí.

Revisión del 2026-11-13 solicitada por el usuario: el diseño anterior resultaba
estrecho y alargado al disparar, y parecía pertenecer a otro juego. Conserva el
casco, gafas verdes, pasamontañas y equipo elegido, con proporciones compactas,
sombras amplias y contraste acordes con los sprites actuales de la vaquera.

Fuente: [game_style_source.png](game_style_source.png), creada con **imagegen
integrada**, modo `style-transfer`. Referencias locales: `cowgirl/stand.png`,
`cowgirl/shoot.png` (estilo principal) y `tactical_walk_source.png` (vestuario).
Los originales anteriores permanecen intactos.

`python3 tools/prepare_swat_style.py` requiere Pillow solo para autoría. Lee
la cuadrícula de cuatro columnas y tres filas; normaliza cada figura completa
a 56 px de alto, con casco alineado en x=21, fila superior 4 y suelas en 59.
No deforma muslos o pantorrillas por separado. El alfa residual exterior se
elimina en los derivados; el original RGBA conserva su transparencia intacta.

La paleta derivada tiene 15 colores: contorno y cuero de la sheriff, sombras
pizarra, medios carbón, piel cálida y ópticas oliva. Los colores se agrupan
por material, sin tramado ni nuevos píxeles verdes sobre la tela. Un mismo
casco/cara se comparte entre caminar, reposo y cuerpo base. Del cuadro sin
brazos se quita solo el resto de manga, conservando el costado del chaleco.

- [Caminata nativa](game_style_walk.png): ocho cuadros de 42 × 67.
- [Reposo](game_style_stand.png) y [cuerpo base sin brazos](game_style_body.png).
- [Referencia de rifle](game_style_rifle_reference.png) y
  [referencia de escopeta](game_style_shotgun_reference.png): guías de pose;
  las armas finales usan las definiciones del juego y su boca de cañón fija.

`python3 tools/rebuild_swat.py` compone las 23 hojas finales. Desde la revisión
de continuidad del 2026-11-13, `game_style_body.png` es el único cuerpo usado
para reposo, caminar y apuntar. `game_style_stand.png` queda como referencia de
autoría. El generador reduce el ancho del cuerpo completo al 94 %, conserva
altura y pivote, restaura la pequeña zona de tela lateral del chaleco y genera
las mangas con `cowgirl_arm.py`. Las siluetas de reposo y disparo ya no salen
de dos imágenes diferentes.

Los cuadros de `game_style_walk.png` aportan las piernas desde la fila 44;
sus manos originales se separan con máscaras antes de superponer los brazos
nuevos. El casco, cuello y chaleco se desplazan juntos siguiendo el apoyo de
los pies. La copia fija de la cabeza durante la importación es solo parte de
la referencia: no se superpone una cabeza inmóvil sobre los cuerpos animados.
`tests/swat_art.py` comprueba la continuidad de cuerpo y movimiento.

## Brazos y ópticas

La revisión de lentes y mangas reutiliza ese cuerpo. `swat_optics.py` marca
las tres lentes con carcasas individuales y cristal verde más visible. Los
brazos y guantes comparten el trazado de `cowgirl_arm.py`, con radios propios
para las mangas acolchadas del SWAT: hombro 2.6, muñeca 1.9 y guante 1.85 px.
Los hombros están en los bordes del chaleco, los codos se abren ligeramente y
los brazos se balancean 7° en sentidos opuestos con una flexión fija.

`tools/rebuild_swat.py` guarda las capas alineadas en [rig/](rig/):
`body`, `head_neck`, `torso`, `legs_walk`, `arm_near_idle`, `arm_far_idle`,
`body_walk`, `arm_near_walk` y `arm_far_walk`. La composición pone el brazo
lejano detrás del cuerpo y el cercano delante. `--verify` compara también
estas nueve capas; las pruebas verifican que al reunirlas producen los PNG
finales y que los brazos mantienen grosor, espacio y balanceo independiente.

## Prompt final

```text
Use case: style-transfer.
Asset type: production low-resolution pixel-art character sprites for THE MIRACLE, an existing 2D game.
INPUT ROLES: The tiny cowgirl stand sprite and long cowgirl shooting strip are the PRIMARY AND STRICT ART STYLE REFERENCE. Match their chunky native-pixel clusters, large expressive head-to-body ratio, short legs, warm one-pixel outlines, restrained three-tone shading and readable stylized silhouette. The large eight-frame black tactical SWAT sheet is ONLY THE OUTFIT / IDENTITY REFERENCE: retain its charcoal helmet with three olive-green mounted optics, balaclava and warm eye slit, fitted gray plate carrier, brown webbing, magazine pouches, dark cargo uniform, kneepads, gloves and boots. Its tall thin realistic proportions, very dark noisy shading and tiny head have been REJECTED and must be changed.
PRIMARY REQUEST: redraw the male SWAT as a compact, solidly built sprite that clearly belongs in the SAME GAME AND SAME PIXEL ART STYLE as the cowgirl. The same apparent total height as her, with a similarly generous head, broad connected shoulders, a sturdy 16-18 logical pixel wide chest/vest, visible waist, short thick but proportional thighs and calves, two equally sized boots. Readable adult human, stylized like the cowgirl, not a realistic slender soldier. Keep his tactical identity. The helmet/masked head together occupy about 22 of his 56 logical pixels of height; shoulders around body row 29, belt around row 44, soles around row 60. Torso and hip mass remain consistent in every pose, particularly aiming; he must NEVER become a thin vertical column when raising his arms. The chest stays broad behind the arms. Shoulders meet the neck naturally, no staircase-shaped silhouette, no box on sticks.
STYLE: exact crisp square pixels suitable for a 42 x 67 native character cell, clearly readable at native size. Simple connected 2-5 pixel clusters, few details, no dither, no noise, no photographic textures, no blur, no glossy rim lighting. Warm dark outline #252018, gray/slate uniform midtones #41494a and #697174, shadow #29343b, gray plate highlights #77807b, brown straps #6f4d33 and #916c48, muted warm skin #d7a786, olive optics #607536 and #9daf50. Broad visible midtone planes like the cowgirl's corset and boots, without disappearing into black. Upper-left diffuse light.
LAYOUT: exactly TWELVE full-body poses in FOUR equal columns by THREE equal rows, on a completely TRANSPARENT background. Every cell has the same dimensions and generous margins, no overlap. Recommended canvas 1620 x 1200 = four 81 x 80 logical cells at 5x. NO text, labels, gridlines, shadows or watermark. All poses face RIGHT in the same three-quarter view, torso partly toward viewer like the cowgirl. All heads have the same size and helmet design. Put each body's centerline at 40% of its cell width and feet on the same baseline, with room for the guns on its right.
POSE ORDER left to right, then next row:
1-8: a smooth complete eight-frame WALK cycle, empty hands and relaxed opposite arm swing. Short comfortable step, knees flex naturally, feet pass under hips, equal limb lengths. No rigid march, no twisting or crossed/dislocated shins.
9: a neutral STANDING IDLE, both equal legs visibly grounded under the hips, relaxed arms beside body, modest spacing, head/body exactly the same size as walking.
10: the SAME NEUTRAL IDLE BODY, with BOTH ARMS OMITTED for layered game animation. Draw the COMPLETE head, collar, connected shoulder/clavicle silhouette, broad vest, side fabric, waist, hips, both legs and boots; do not remove chest width along with arms. No arm stumps and no extra limbs. This is a clean animator's arm-free body base, not a different narrower character.
11: the SAME BODY aiming a short gray tactical rifle rightward at shoulder height, stock seated at shoulder, bent compact elbows, rear hand on trigger and front hand under handguard. His chest and both legs MUST keep the same width as pose 9; do not stretch arms forward or thin torso to make room.
12: the SAME BODY aiming a pump shotgun rightward, same body and compact bent elbows. Clear chunky weapon silhouette like the cowgirl's gun, minimal detail.
FINAL CHECK: All twelve poses are the identical compact SWAT in identical pixel style and palette. Preserve the tactical kit, replace the slender proportions with the cowgirl game's proportions. Export only the finished transparent sheet.
```
