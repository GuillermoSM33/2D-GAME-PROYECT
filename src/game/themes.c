#include "game/themes.h"

/* Measured on the approved sunset reference: mesa tops on rows 47-55, the
 * far hills' lit crests on 61-75, the near hills down to the ground line. */
const BackgroundLayer BACKGROUND_LAYERS[] = {
    {"sky", 0, 0.0f, false, 240, 117},
    {"far", 43, 0.15f, true, 360, 24},
    {"hills_far", 60, 0.35f, true, 360, 40},
    {"hills_near", 80, 0.6f, true, 360, 38},
    {"ground", 117, 1.0f, true, 120, 18},
};

const int BACKGROUND_LAYER_COUNT = (int)(sizeof(BACKGROUND_LAYERS) / sizeof(BACKGROUND_LAYERS[0]));

const BackgroundLayer FOG_LAYER = {"fog", 105, 1.0f, true, 240, 24};

/* The props' six colors, as drawn for the sunset. The other themes map each
 * to theirs, measured on their approved previews (docs/img). */
#define DARK 0x312224        /* Body of every prop */
#define MID 0x4f2b2a         /* Wood and stone */
#define CACTUS_MID 0x45332a
#define FENCE_LIT 0x5e302a
#define CACTUS_LIT 0x6d3d1f
#define LIT 0x5a4334         /* Light on the sun's side */

/* Desert at sunset: cacti and rocks most, fences, a lone tree now and then. */
const ThemeDef THEME_ATARDECER = {
    .name = "atardecer",
    .prop_weights = {
        [PROP_CACTUS] = 4, [PROP_ROCK] = 3, [PROP_FENCE] = 2, [PROP_DEAD_TREE] = 2,
        [PROP_WAGON_WHEEL] = 1, [PROP_SKULL] = 1, [PROP_SIGN] = 1,
    },
    .house_chance = 35,
};

/* Graveyard at dusk: graves and crosses, bare trees, broken fences; purple. */
const ThemeDef THEME_CEMENTERIO = {
    .name = "cementerio",
    .fog = true,
    .night = true,
    .prop_weights = {
        [PROP_TOMBSTONE] = 5, [PROP_DEAD_TREE] = 2, [PROP_FENCE] = 2, [PROP_ROCK] = 2,
        [PROP_SKULL] = 1, [PROP_SIGN] = 1,
    },
    .prop_recolor = {
        {DARK, 0x2c212e}, {MID, 0x3d2e40}, {CACTUS_MID, 0x3a2c3d}, {FENCE_LIT, 0x423148},
        {CACTUS_LIT, 0x4c3a50}, {LIT, 0x453449},
    },
    .prop_recolor_count = 6,
    .house_chance = 25,
};

/* Moonlit desert: cacti, rocks and skulls under a full moon; dark blue. */
const ThemeDef THEME_NOCHE = {
    .name = "noche",
    .fog = true,
    .night = true,
    .prop_weights = {
        [PROP_CACTUS] = 3, [PROP_ROCK] = 3, [PROP_SKULL] = 3, [PROP_DEAD_TREE] = 2,
        [PROP_FENCE] = 1, [PROP_WAGON_WHEEL] = 1,
    },
    .prop_recolor = {
        {DARK, 0x1c2331}, {MID, 0x263144}, {CACTUS_MID, 0x283346}, {FENCE_LIT, 0x2e3a50},
        {CACTUS_LIT, 0x34425b}, {LIT, 0x34425c},
    },
    .prop_recolor_count = 6,
    .house_chance = 30,
};

/* Ghost town under a red moon: signs, wagon wheels and fences; dark red. */
const ThemeDef THEME_PUEBLO_FANTASMA = {
    .name = "pueblo_fantasma",
    .fog = true,
    .night = true,
    .prop_weights = {
        [PROP_SIGN] = 3, [PROP_WAGON_WHEEL] = 3, [PROP_FENCE] = 3, [PROP_ROCK] = 2,
        [PROP_DEAD_TREE] = 1, [PROP_SKULL] = 1, [PROP_TOMBSTONE] = 1,
    },
    .prop_recolor = {
        {DARK, 0x2d171a}, {MID, 0x3f2023}, {CACTUS_MID, 0x3b1e21}, {FENCE_LIT, 0x482428},
        {CACTUS_LIT, 0x5c2e33}, {LIT, 0x562b30},
    },
    .prop_recolor_count = 6,
    .house_chance = 70, /* A town: buildings all along */
};
