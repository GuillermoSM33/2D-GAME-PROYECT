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
};

const PropDef *prop_def(PropKind kind)
{
    return &PROPS[kind];
}
