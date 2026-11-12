#include "game/themes.h"

#include "config.h"

/* The view is 480 x 270 art px, the ground line on row GROUND_ROW (240). The
 * sky fills it down to the horizon (below its last row, that row carries on);
 * the far land's tops stand on rows 104-150, the far hills' crests on 140-175,
 * the near hills reach down to the ground line (tools/make_landscape.py). */
const BackgroundLayer BACKGROUND_LAYERS[] = {
    {"sky", 0, 0.0f, false, 480, 180},
    {"far", 104, 0.15f, true, 720, 72},
    {"hills_far", 140, 0.35f, true, 720, 70},
    {"hills_near", 176, 0.6f, true, 720, 64},
    {"ground", GROUND_ROW, 1.0f, true, 480, 30},
};

const int BACKGROUND_LAYER_COUNT = (int)(sizeof(BACKGROUND_LAYERS) / sizeof(BACKGROUND_LAYERS[0]));

const BackgroundLayer FOG_LAYER = {"fog", 216, 1.0f, true, 480, 48};

/* Desert at sunset: cacti and rocks most, brush, fences, a lone tree or a
 * telegraph pole now and then. */
const ThemeDef THEME_ATARDECER = {
    .name = "atardecer",
    .prop_weights = {
        [PROP_CACTUS] = 4, [PROP_ROCK] = 3, [PROP_SHRUB] = 3, [PROP_FENCE] = 2, [PROP_DEAD_TREE] = 2,
        [PROP_WAGON_WHEEL] = 1, [PROP_SKULL] = 1, [PROP_SIGN] = 1, [PROP_TELEGRAPH] = 1,
    },
    .prop_shadow = 0x2a1a1c, .prop_light = 0xb07650, .haze = 0x5b3235,
    .house_chance = 35,
};

/* Graveyard at dusk: graves and crosses, bare trees, broken fences; purple. */
const ThemeDef THEME_CEMENTERIO = {
    .name = "cementerio",
    .fog = true,
    .night = true,
    .prop_weights = {
        [PROP_TOMBSTONE] = 6, [PROP_DEAD_TREE] = 2, [PROP_FENCE] = 2, [PROP_ROCK] = 2,
        [PROP_SHRUB] = 1, [PROP_SKULL] = 1, [PROP_SIGN] = 1,
    },
    .prop_shadow = 0x1e1826, .prop_light = 0x8c7c96, .haze = 0x2e2536,
    .house_chance = 25,
};

/* Moonlit desert: cacti, rocks and skulls under a full moon; dark blue. */
const ThemeDef THEME_NOCHE = {
    .name = "noche",
    .fog = true,
    .night = true,
    .prop_weights = {
        [PROP_CACTUS] = 3, [PROP_ROCK] = 3, [PROP_SKULL] = 2, [PROP_SHRUB] = 2, [PROP_DEAD_TREE] = 2,
        [PROP_FENCE] = 1, [PROP_WAGON_WHEEL] = 1, [PROP_TELEGRAPH] = 1,
    },
    .prop_shadow = 0x141a2a, .prop_light = 0x6e82a8, .haze = 0x232a40,
    .house_chance = 30,
};

/* Ghost town under a red moon: signs, wagon wheels and fences; dark red. */
const ThemeDef THEME_PUEBLO_FANTASMA = {
    .name = "pueblo_fantasma",
    .fog = true,
    .night = true,
    .prop_weights = {
        [PROP_SIGN] = 3, [PROP_WAGON_WHEEL] = 3, [PROP_FENCE] = 3, [PROP_ROCK] = 2, [PROP_TELEGRAPH] = 2,
        [PROP_DEAD_TREE] = 1, [PROP_SKULL] = 1, [PROP_TOMBSTONE] = 1, [PROP_SHRUB] = 1,
    },
    .prop_shadow = 0x261216, .prop_light = 0xa2584a, .haze = 0x3a1a1e,
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
        [PROP_TRAFFIC_LIGHT] = 1, [PROP_SHRUB] = 1,
    },
    .prop_shadow = 0x261a24, .prop_light = 0xb07a74, .haze = 0x5a3442,
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
    .prop_shadow = 0x221c1c, .prop_light = 0xa48c74, .haze = 0x4a3a36,
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
    .prop_shadow = 0x28181a, .prop_light = 0xb46e46, .haze = 0x5e2e2e,
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
    .prop_shadow = 0x12121e, .prop_light = 0x686890, .haze = 0x1e1e30,
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
    .prop_shadow = 0x1e0e0e, .prop_light = 0x944840, .haze = 0x2e1618,
    .house_chance = 60,
    .city = true,
    .houses = {18, 19, 20, 17, 19}, .house_count = 5,
    .barricades = {6, 6, 3, 1, 5}, .barricade_count = 5,
    .walls = {CHECKPOINT, CHECKPOINT, POLICE}, .wall_count = 3,
    .vehicles = {3, 4, 3, 4, 2}, .vehicle_count = 5,
};
