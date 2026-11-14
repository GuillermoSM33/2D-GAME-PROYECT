# SWAT: mangas y porte del arma

Revisión de 2026-11-13. Las mangas, los codos, los guantes y el agarre se dibujaron como parte del uniforme, usando la herramienta integrada `image_gen` (sin CLI/API). Las cuatro fuentes transparentes se conservan en esta carpeta con sufijo `_authored_source.png`. El alfa original no se modifica.

Las referencias de movimiento aportadas por el usuario son [caminata con arma](https://i.redd.it/e84kxqlcn24e1.gif) y [porte alto](https://i.redd.it/zi56l4kcz4vd1.gif), con crédito visible u/luckynumbersteven. Se estudiaron las uniones de manga y el apoyo de las manos; sus imágenes no se distribuyen como recursos del juego.

`tools/prepare_swat_authored.py` adapta las cuatro fuentes a ocho celdas de 81 × 80 con escala uniforme y una paleta común. Es un paso de autoría con Pillow. `tools/swat_authored.py` y `tools/rebuild_swat.py` componen las hojas finales con biblioteca estándar: cabeza común, piernas animadas, conjunto pintado de torso/mangas/arma y capa baja del cargador. Las hojas `carry` y `carry_shotgun` permiten llevar el arma al caminar sin recortarla al ancho de la plantilla antigua. Los tiempos de acciones se conservan.

En las acciones principales se comparte el casco, cuello y botas. El conjunto superior sigue el apoyo de los pies. La puntería no estira las mangas ni reduce el torso para alcanzar coordenadas. `WeaponDef` conserva los orígenes reales de boca del cañón y linterna para cada arma. Las poses auxiliares de banco, cuidado y granadas conservan el generador por articulaciones.

## Prompts finales

### swat_anatomy_prompt

```text
Use case: precise-object-edit.
Asset type: eight-frame firing sprite atlas for an existing 2D game.
REFERENCE ROLES:
1. The blue-gray SWAT standing on transparent background is the EDIT TARGET / IDENTITY. Preserve exactly its helmet with THREE bright olive night-vision tubes, covered face and warm eye slit, blue-gray charcoal plate carrier, brown harness/pouches, short sturdy tactical trousers, gray kneepads, boots, pixel palette and stylized proportions. Do not redesign this character, enlarge the helmet, fatten the belly, shorten or lengthen his legs.
2. The blue-gray SWAT holding a rifle is a FAILED ARM POSE. Its pasted-looking U-shaped cyan arm loops, circular fists near the face, disconnected shoulder pads and stiff pipe-like sleeves are the exact defects to replace. Keep its outfit, not that arm construction.
3 and 4. The brown/black soldier details are ANATOMICAL PIXEL-ART ARM AND WEAPON-HANDLING REFERENCES, supplied by the user. Study their continuous shoulder-to-sleeve silhouette, a visible upper arm dropping from the shoulder, a supported elbow, forearm going diagonally forward/up to the grip, glove wrapping the weapon, and the far forearm supporting the handguard. Borrow only the believable arm construction and the relaxed cloth folds. Do not copy their red eyes, mask, brown costume, branding or character design.

PRIMARY EDIT: Make the target SWAT's arms look naturally drawn as part of his own uniform. Draw proper cloth sleeves and gloves, as hand-authored pixel-art shapes and light/shadow planes, not cylindrical procedural strokes. Fit the shoulder cap continuously into the clavicle and side of the vest. The arm must have a shoulder, an actual upper arm, a softly bent elbow below the rifle, a forearm and an anatomically placed glove; preserve equal arm segment lengths in every frame. He holds the rifle HIGH at shoulder level like reference 4, stock firmly seated in the shoulder pocket, both elbows down, rear hand on trigger and front hand under handguard. Avoid fists pressed against his cheek, pinched V-shaped arms, floating shoulder plates, tiny upper arms, U-shaped mechanical loops, stretched forearms and naked gaps at the shoulder seam. Arms have natural tactical sleeve thickness, without becoming fat or skeletal. The full torso remains present behind the arm; do not thin or shrink his chest when aiming.

LAYOUT: EXACTLY 8 full-body frames in FOUR columns and TWO equal rows, a completely TRANSPARENT background, no grid lines, no text, no shadows, no labels or watermark. Each cell is the same size. Same SWAT in every frame, facing RIGHT in consistent three-quarter view, torso slightly toward viewer, matching the edit target. Identical helmet/head, height, stance, waist, legs and boots in every frame; only the arms and rifle change pose, with a tiny shoulder recoil. Keep ample room to his right for the rifle, keep all feet and gun barrels within each cell.
Frame order:
1: both hands on rifle at low ready, arms relaxed, muzzle slightly down.
2: raising rifle with relaxed elbows.
3: almost aimed.
4: aimed high, steady, shoulder supported.
5: fire pose, same high aim (NO muzzle flash, bullets or smoke; game adds these).
6: small recoil back into the shoulder, about 5 degrees, elbows flex naturally.
7: settled aim.
8: gently lowering toward ready.
The rifle is the same short gray tactical carbine in every frame; do not change its length, stock, receiver, trigger, magazine or handguard between frames. Hands remain wrapped around the same grip points. No pistol, bayonet flourish or second weapon.

PIXEL GRID AND STYLE: Keep the target's actual native pixel look: design for an 81 x 80 logical-pixel action cell with a 56-pixel tall character, head top near row 11, soles near row 67 and body pivot x31.5. Use crisp square pixel clusters, warm dark outline, blue-gray fabric, gray hard armor, brown leather and olive optics; upper-left light; three or four shades per material. Use broad cloth folds and cuffs like the anatomical references, never smooth vector tubes or shiny 3D armor. The torso, head, legs and boots must match the target's proportions across all eight frames. Render large for inspection while retaining the deliberately low native pixel detail. The result must be production-ready transparent pixel art.
```

### swat_shotgun_edit_prompt

```text
Use case: precise-object-edit. Nonviolent production art for a fictional pixel-art video game, no real people and no targets.
Edit the supplied transparent eight-frame SWAT atlas. Keep the entire character, his natural fabric sleeves and hands, the helmet with three green optics, torso, legs, grounded feet, palette and every frame position unchanged.
Replace only the existing gray rifle prop with a gray pump-action shotgun prop. It should have a full shoulder stock, an under-barrel magazine tube and a ribbed pump where the front hand already rests, without a box magazine. The muzzle tip must remain at the same pixel location in every corresponding frame. Keep the rear hand at the trigger and the front hand under the pump, using the exact existing arm pose. There should be no firing effects, muzzle flashes, projectiles, smoke, ammunition, combat, injury or violence depicted.
Output the same FOUR-column TWO-row atlas of exactly eight full-body poses, transparent background, no text, labels, grid or shadows. Do not redraw the body or move the hands. Preserve the cohesive hand-authored cloth folds and human shoulder/elbow/hand construction already present.
```

### rifle_reload_authored_source.png

```text
Use case: precise-object-edit. Equipment-maintenance animation for a fictional pixel-art video-game character. Use the supplied SWAT sprite atlas as the edit target. Preserve its character, blue-gray uniform, three green night-vision optics, mask, plate carrier, brown pouches, legs, boots, stance, palette, pixel clusters and natural cloth sleeves exactly. Keep his body anchor and head size unchanged in every cell. Draw human connected shoulders, elbows below the equipment, diagonal forearms and gloves wrapped around the objects. No cylindrical robot arms or fists at his face. Exactly EIGHT full-body frames in FOUR columns by TWO rows on a completely transparent background. No flashes, smoke, projectiles, targets, injuries, text, shadows, labels or grid. The hands and equipment move; the head, torso and legs remain consistent. Show a normal magazine change for the same gray rifle prop, supported across his chest by one hand. Eight frames: (1) supported ready; (2) other hand grasps the rectangular magazine; (3) removes it below the receiver; (4) takes a fresh magazine from a belt pouch; (5) brings it up to the magazine well; (6) seats it; (7) operates the charging handle; (8) returns to supported ready. Keep the rifle slightly down so both hands work comfortably between chest and belt. Show one small detached gray magazine in the working hand in frames 3-5. Sleeves and torso must form one cohesive hand-drawn pixel-art silhouette.
```

### shotgun_reload_authored_source.png

```text
Use case: precise-object-edit. Equipment-maintenance animation for a fictional pixel-art video-game character. Use the supplied SWAT sprite atlas as the edit target. Preserve its character, blue-gray uniform, three green night-vision optics, mask, plate carrier, brown pouches, legs, boots, stance, palette, pixel clusters and natural cloth sleeves exactly. Keep his body anchor and head size unchanged in every cell. Draw human connected shoulders, elbows below the equipment, diagonal forearms and gloves wrapped around the objects. No cylindrical robot arms or fists at his face. Exactly EIGHT full-body frames in FOUR columns by TWO rows on a completely transparent background. No flashes, smoke, projectiles, targets, injuries, text, shadows, labels or grid. The hands and equipment move; the head, torso and legs remain consistent. Show the loading gesture for the same gray pump-action shotgun prop, supported across the chest by one hand. Eight frames: (1) steady supported ready; (2) free hand takes one small red/brass cartridge from belt pouch; (3) places it in the port underneath the receiver; (4) takes another from pouch; (5) places it in the port; (6) takes a third; (7) moves the ribbed pump back; (8) moves it forward and returns to supported ready. Small red cartridge between gloved fingers in frames 2-6. Keep the weapon slightly down at chest/belt level, natural connected sleeves and comfortably bent elbows.
```
