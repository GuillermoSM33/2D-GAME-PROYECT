#ifndef GAME_PROPS_H
#define GAME_PROPS_H

/* Scenery sprites standing on the ground line, behind the characters
 * (assets/sprites/props, docs/LANDSCAPE.md). A sheet holds its variants as
 * a row of equal frames, each resting on its last row. */
typedef enum {
    PROP_CACTUS,
    PROP_ROCK,
    PROP_FENCE,
    PROP_DEAD_TREE,
    PROP_GRASS,
    PROP_WAGON_WHEEL,
    PROP_SKULL,
    PROP_TOMBSTONE,
    PROP_SIGN,
    PROP_KIND_COUNT
} PropKind;

typedef struct {
    const char *sheet;
    int frame_w, frame_h; /* Art px */
    int variants;         /* Frames in the sheet */
} PropDef;

const PropDef *prop_def(PropKind kind);

#endif
