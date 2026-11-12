#include "game/props.h"

/* Sized against her (56 px, 1.70 m; 33 px to the metre): a saguaro up to
 * twice her height, a fence to her chest, a dead tree or a pole well over her
 * head, a wagon wheel to her waist. */
static const PropDef PROPS[PROP_KIND_COUNT] = {
    /* The desert's (tools/make_props.py) */
    [PROP_CACTUS] = {"sprites/props/cactus", 44, 100, 4},
    [PROP_ROCK] = {"sprites/props/rock", 48, 24, 3},
    [PROP_FENCE] = {"sprites/props/fence", 72, 40, 2},
    [PROP_DEAD_TREE] = {"sprites/props/dead_tree", 100, 150, 2},
    [PROP_GRASS] = {"sprites/props/grass", 24, 14, 4},
    [PROP_WAGON_WHEEL] = {"sprites/props/wagon_wheel", 44, 44, 2},
    [PROP_SKULL] = {"sprites/props/skull", 34, 18, 2},
    [PROP_TOMBSTONE] = {"sprites/props/tombstone", 28, 40, 4},
    [PROP_SIGN] = {"sprites/props/sign", 36, 62, 2},
    /* The town's (tools/make_props.py, shared materials with the desert) */
    [PROP_HYDRANT] = {"sprites/props/hydrant", 14, 24, 1},
    [PROP_STREETLIGHT] = {"sprites/props/streetlight", 40, 150, 2},
    [PROP_TRASH] = {"sprites/props/trash", 26, 32, 2},
    [PROP_CONE] = {"sprites/props/cone", 16, 24, 1},
    [PROP_TIRES] = {"sprites/props/tires", 40, 34, 1},
    [PROP_SANDBAGS] = {"sprites/props/sandbags", 66, 28, 1},
    [PROP_JERSEY] = {"sprites/props/jersey", 104, 27, 1},
    [PROP_POLE] = {"sprites/props/pole", 44, 160, 1},
    [PROP_LITTER] = {"sprites/props/litter", 20, 6, 3},
    [PROP_SIGNAL] = {"sprites/props/signal", 24, 110, 1},
    [PROP_DRUMS] = {"sprites/props/drums", 48, 34, 1},
    [PROP_FALLEN_POLE] = {"sprites/props/fallen_pole", 150, 26, 1},
    [PROP_TRAFFIC_LIGHT] = {"sprites/props/traffic_light", 60, 140, 2},
    /* More of the desert's */
    [PROP_SHRUB] = {"sprites/props/shrub", 40, 36, 4},
    [PROP_TELEGRAPH] = {"sprites/props/telegraph", 40, 176, 2},
};

const PropDef *prop_def(PropKind kind)
{
    return &PROPS[kind];
}
