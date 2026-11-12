#include "game/props.h"

static const PropDef PROPS[PROP_KIND_COUNT] = {
    [PROP_CACTUS] = {"sprites/props/cactus", 24, 56, 3},
    [PROP_ROCK] = {"sprites/props/rock", 26, 12, 3},
    [PROP_FENCE] = {"sprites/props/fence", 44, 26, 2},
    [PROP_DEAD_TREE] = {"sprites/props/dead_tree", 48, 70, 2},
    [PROP_GRASS] = {"sprites/props/grass", 20, 12, 3},
    [PROP_WAGON_WHEEL] = {"sprites/props/wagon_wheel", 16, 16, 1},
    [PROP_SKULL] = {"sprites/props/skull", 12, 7, 1},
    [PROP_TOMBSTONE] = {"sprites/props/tombstone", 14, 18, 3},
    [PROP_SIGN] = {"sprites/props/sign", 20, 22, 1},
    /* The town's, at her scale (tools/make_city.py) */
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
};

const PropDef *prop_def(PropKind kind)
{
    return &PROPS[kind];
}
