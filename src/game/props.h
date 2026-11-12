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
    /* The town (tools/make_props.py) */
    PROP_HYDRANT,
    PROP_STREETLIGHT,
    PROP_TRASH,
    PROP_CONE,
    PROP_TIRES,
    PROP_SANDBAGS,
    PROP_JERSEY,
    PROP_POLE,
    PROP_LITTER,  /* Strewn like the grass tufts in a city theme */
    PROP_SIGNAL,
    PROP_DRUMS,
    PROP_FALLEN_POLE,
    PROP_TRAFFIC_LIGHT,
    /* More of the desert (tools/make_props.py) */
    PROP_SHRUB,     /* Sagebrush, a yucca, a prickly pear, a dry bush */
    PROP_TELEGRAPH, /* A telegraph pole: whole, leaning with its wire down */
    PROP_KIND_COUNT
} PropKind;

typedef struct {
    const char *sheet;
    int frame_w, frame_h; /* Art px */
    int variants;         /* Frames in the sheet */
} PropDef;

const PropDef *prop_def(PropKind kind);

#endif
