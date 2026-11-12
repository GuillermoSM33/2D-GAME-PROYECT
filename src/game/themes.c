#include "game/themes.h"

#include "config.h"

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

/* ---- The second route: the neighbouring town and its army post ---------------
 * Wall looks: FACADE_KINDS + 1 store, + 2 police station, + 3 flats, + 4 the
 * checkpoint. Vehicles to walk past: 0-2 sedans (green, red, burnt), 3 a jeep, 4 an army
 * truck. Barricades: 1 sandbags, 3 steel barrier, 4 a wrecked car, 5
 * police sawhorses, 6 the army's jersey barrier, 7 motorcycles. Houses: 13 billboard, 14 gas
 * station, 15 shops, 16 flats, 17 warehouse, 18 hangar, 19 watchtower, 20 radar. */
#define STORE (FACADE_KINDS + 1)
#define POLICE (FACADE_KINDS + 2)
#define FLATS (FACADE_KINDS + 3)
#define CHECKPOINT (FACADE_KINDS + 4)

/* The outskirts at dawn: cars left on the road, poles, hydrants, cones. */
const ThemeDef THEME_AFUERAS = {
    .name = "afueras",
    .prop_weights = {
        [PROP_POLE] = 3, [PROP_HYDRANT] = 1, [PROP_TRASH] = 2, [PROP_CONE] = 1,
        [PROP_TIRES] = 1, [PROP_STREETLIGHT] = 2, [PROP_FENCE] = 1, [PROP_FALLEN_POLE] = 1,
        [PROP_TRAFFIC_LIGHT] = 1,
    },
    .prop_recolor = {
        {DARK, 0x2a1c24}, {MID, 0x3e2632}, {CACTUS_MID, 0x382430}, {FENCE_LIT, 0x4a2a38},
        {CACTUS_LIT, 0x5a3040}, {LIT, 0x5a3a44},
    },
    .prop_recolor_count = 6,
    .house_chance = 55,
    .city = true,
    .houses = {13, 14, 15, 16, 17}, .house_count = 5,
    .barricades = {4, 5, 7, 1, 4, 3}, .barricade_count = 6,
    .walls = {STORE, FLATS, POLICE}, .wall_count = 3,
    .vehicles = {0, 1, 0, 2, 1}, .vehicle_count = 5,
};

/* Downtown on a smoggy afternoon: streetlights, cars, trash, hydrants. */
const ThemeDef THEME_CENTRO = {
    .name = "centro",
    .prop_weights = {
        [PROP_STREETLIGHT] = 3, [PROP_TRASH] = 3, [PROP_HYDRANT] = 1, [PROP_CONE] = 2,
        [PROP_DRUMS] = 1, [PROP_TRAFFIC_LIGHT] = 3, [PROP_FALLEN_POLE] = 1,
    },
    .prop_recolor = {
        {DARK, 0x262020}, {MID, 0x3a2e2a}, {CACTUS_MID, 0x342a28}, {FENCE_LIT, 0x463630},
        {CACTUS_LIT, 0x54402e}, {LIT, 0x524034},
    },
    .prop_recolor_count = 6,
    .house_chance = 75,
    .city = true,
    .houses = {15, 16, 13, 16, 14}, .house_count = 5,
    .barricades = {5, 4, 7, 3, 5, 1}, .barricade_count = 6,
    .walls = {STORE, POLICE, FLATS}, .wall_count = 3,
    .vehicles = {1, 0, 2, 0, 1, 3}, .vehicle_count = 6,
};

/* The rail yard at dusk: signals, drums, tires, poles. */
const ThemeDef THEME_VIAS = {
    .name = "vias",
    .prop_weights = {
        [PROP_SIGNAL] = 3, [PROP_DRUMS] = 3, [PROP_TIRES] = 2, [PROP_POLE] = 2, [PROP_ROCK] = 2,
        [PROP_TRASH] = 1, [PROP_FALLEN_POLE] = 1,
    },
    .prop_recolor = {
        {DARK, 0x2a1a1c}, {MID, 0x40221e}, {CACTUS_MID, 0x3a201e}, {FENCE_LIT, 0x4e2a24},
        {CACTUS_LIT, 0x60321e}, {LIT, 0x5a3626},
    },
    .prop_recolor_count = 6,
    .house_chance = 45,
    .city = true,
    .houses = {17, 13, 17, 14}, .house_count = 4,
    .barricades = {3, 4, 1, 3}, .barricade_count = 4,
    .walls = {STORE, FLATS}, .wall_count = 2,
    .vehicles = {4, 2, 3}, .vehicle_count = 3,
};

/* Downtown by night: patrol cars, cones, barriers; dark blue, fog. */
const ThemeDef THEME_CIUDAD_NOCHE = {
    .name = "ciudad_noche",
    .fog = true,
    .night = true,
    .prop_weights = {
        [PROP_STREETLIGHT] = 3, [PROP_CONE] = 2, [PROP_TRASH] = 2, [PROP_JERSEY] = 1,
        [PROP_HYDRANT] = 1, [PROP_DRUMS] = 1, [PROP_TRAFFIC_LIGHT] = 2, [PROP_FALLEN_POLE] = 1,
    },
    .prop_recolor = {
        {DARK, 0x161624}, {MID, 0x22223a}, {CACTUS_MID, 0x1e1e32}, {FENCE_LIT, 0x2a2a44},
        {CACTUS_LIT, 0x34344e}, {LIT, 0x343452},
    },
    .prop_recolor_count = 6,
    .house_chance = 75,
    .city = true,
    .houses = {16, 15, 16, 13}, .house_count = 4,
    .barricades = {5, 7, 4, 6, 5, 3}, .barricade_count = 6,
    .walls = {POLICE, FLATS, STORE}, .wall_count = 3,
    .vehicles = {0, 3, 2, 1, 4, 2}, .vehicle_count = 6,
};

/* The army post by night: sandbags, jersey barriers, drums; alarm red. */
const ThemeDef THEME_BASE_MILITAR = {
    .name = "base_militar",
    .fog = true,
    .night = true,
    .prop_weights = {
        [PROP_SANDBAGS] = 4, [PROP_JERSEY] = 3, [PROP_DRUMS] = 2, [PROP_TIRES] = 1, [PROP_STREETLIGHT] = 1,
        [PROP_CONE] = 1,
    },
    .prop_recolor = {
        {DARK, 0x22100f}, {MID, 0x361818}, {CACTUS_MID, 0x301616}, {FENCE_LIT, 0x421c1c},
        {CACTUS_LIT, 0x542420}, {LIT, 0x4e2622},
    },
    .prop_recolor_count = 6,
    .house_chance = 60,
    .city = true,
    .houses = {18, 19, 20, 17, 19}, .house_count = 5,
    .barricades = {6, 6, 3, 1, 5}, .barricade_count = 5,
    .walls = {CHECKPOINT, CHECKPOINT, POLICE}, .wall_count = 3,
    .vehicles = {3, 4, 3, 4, 2}, .vehicle_count = 5,
};
