#include "game/stages.h"

#include <string.h>

#include "config.h"

/* Clearing each stage once (every zombie, every chest) takes her up one level
 * by its end, so she starts each at about its zombies' level. Against that:
 * 1-1, 1-2 and 1-3 are even fights (more zombies, not stronger ones),
 * 1-4 jumps two levels, and 1-5 ends with a zombie one level above the rest.
 * tests/test_progression.c plays this and keeps it winnable. */
/* The landscape darkens with the difficulty: two sunsets, the graveyard for the
 * breather, a moonlit night for the jump, and the ghost town for the boss. */
/* Routes, about 12-20 views long, each with its own things on the road:
 * the sunset ones bottles on fences to shoot and crates, 1-2 bear traps in
 * a group's path; the graveyard coffins that burst open (an ambush) and
 * traps; the night oil lamps over the zombies' way, to knock down into a
 * fire; the ghost town all of it. Each teaches one thing more: 1-1 a low
 * barricade, a box of dynamite before the first wall, a wall with a barrel
 * against it; 1-3 the first elite; 1-4 the wagon's charges carried past two
 * fights; 1-5 the longest, a group of three, three walls, the elite last.
 * Every wall has a way through before it: a charge she can have by then
 * (boxes, the wagon's: stage_supply_dynamite) not spent on another wall,
 * or a barrel set against it (count 2). The wagon sits about half way. */
#define SPOTS(a) a, (int)(sizeof(a) / sizeof(a[0]))
static const StageSpot ROUTE_1_1[] = {
    {0.06f, SPOT_ZOMBIES, 1}, {0.09f, SPOT_CRATES, 2}, {0.12f, SPOT_BARRICADE, 1},
    {0.18f, SPOT_ZOMBIES, 2}, {0.22f, SPOT_BOTTLES, 1}, {0.26f, SPOT_DYNAMITE, 1},
    {0.275f, SPOT_AMBUSH, 1}, {0.31f, SPOT_WALL, 1}, {0.38f, SPOT_BARRELS, 1},
    {0.41f, SPOT_ZOMBIES, 2}, {0.46f, SPOT_CRATES, 1}, {0.48f, SPOT_WIRE, 1},
    {0.5f, SPOT_SUPPLY, 1}, {0.52f, SPOT_SPIKES, 1}, {0.54f, SPOT_REST, 1},
    {0.58f, SPOT_BARRICADE, 1}, {0.62f, SPOT_ZOMBIES, 1}, {0.66f, SPOT_WALL, 2},
    {0.7f, SPOT_BOTTLES, 1}, {0.75f, SPOT_COFFINS, 1}, {0.775f, SPOT_RIVER, 1},
    {0.8f, SPOT_CRATES, 2}, {0.86f, SPOT_BARRICADE, 1}, {0.92f, SPOT_ZOMBIES, 2},
};
static const StageSpot ROUTE_1_2[] = {
    {0.05f, SPOT_ZOMBIES, 1}, {0.07f, SPOT_PUDDLES, 2}, {0.08f, SPOT_BOTTLES, 1},
    {0.11f, SPOT_BARRELS, 2}, {0.14f, SPOT_ZOMBIES, 2}, {0.22f, SPOT_BARRICADE, 1},
    {0.25f, SPOT_SPIKES, 1}, {0.26f, SPOT_TRAPS, 1}, {0.28f, SPOT_ZOMBIES, 2},
    {0.31f, SPOT_PUDDLES, 3}, {0.315f, SPOT_AMBUSH, 2}, {0.35f, SPOT_WALL, 2},
    {0.4f, SPOT_CRATES, 2}, {0.44f, SPOT_DYNAMITE, 1}, {0.47f, SPOT_BARRICADE, 1},
    {0.5f, SPOT_SUPPLY, 1}, {0.53f, SPOT_REST, 1}, {0.57f, SPOT_COFFINS, 2}, {0.6f, SPOT_CRATES, 1},
    {0.63f, SPOT_WALL, 1}, {0.65f, SPOT_NET, 1}, {0.67f, SPOT_RUNNERS, 2}, {0.72f, SPOT_BARRELS, 1},
    {0.73f, SPOT_TRAPS, 1}, {0.75f, SPOT_ZOMBIES, 2}, {0.78f, SPOT_RIVER, 1},
    {0.82f, SPOT_BOTTLES, 1}, {0.84f, SPOT_PUDDLES, 2}, {0.86f, SPOT_BARRICADE, 1},
    {0.88f, SPOT_WIRE, 1}, {0.91f, SPOT_ZOMBIES, 1},
};
static const StageSpot ROUTE_1_3[] = {
    {0.05f, SPOT_ZOMBIES, 1}, {0.08f, SPOT_PUDDLES, 3}, {0.12f, SPOT_BARRICADE, 1},
    {0.16f, SPOT_COFFINS, 2}, {0.22f, SPOT_CRATES, 1}, {0.24f, SPOT_WIRE, 1},
    {0.26f, SPOT_DYNAMITE, 1}, {0.285f, SPOT_AMBUSH, 1}, {0.32f, SPOT_WALL, 1},
    {0.35f, SPOT_SNARE, 1}, {0.37f, SPOT_CRATES, 2}, {0.4f, SPOT_TRAPS, 1},
    {0.42f, SPOT_ZOMBIES, 2}, {0.44f, SPOT_RIVER, 1}, {0.46f, SPOT_RUNNERS, 2},
    {0.5f, SPOT_SUPPLY, 1}, {0.53f, SPOT_REST, 1}, {0.56f, SPOT_TRAPS, 1}, {0.58f, SPOT_NET, 1},
    {0.62f, SPOT_COFFINS, 2}, {0.66f, SPOT_TRAPS, 2}, {0.68f, SPOT_PUDDLES, 2},
    {0.685f, SPOT_AMBUSH, 2}, {0.72f, SPOT_WALL, 1}, {0.76f, SPOT_SPIKES, 2}, {0.8f, SPOT_WALL, 2},
    {0.84f, SPOT_CRATES, 1}, {0.9f, SPOT_ELITE, 1},
};
static const StageSpot ROUTE_1_4[] = {
    {0.05f, SPOT_LAMPS, 1}, {0.08f, SPOT_ZOMBIES, 2}, {0.12f, SPOT_NET, 1},
    {0.15f, SPOT_DYNAMITE, 1}, {0.18f, SPOT_CRATES, 1}, {0.19f, SPOT_WIRE, 1},
    {0.205f, SPOT_LAMPS, 1}, {0.22f, SPOT_ZOMBIES, 2}, {0.255f, SPOT_AMBUSH, 2},
    {0.29f, SPOT_WALL, 1}, {0.36f, SPOT_BARRICADE, 1}, {0.39f, SPOT_RIVER, 1},
    {0.42f, SPOT_ZOMBIES, 2}, {0.46f, SPOT_RUNNERS, 2}, {0.48f, SPOT_SNARE, 1},
    {0.5f, SPOT_SUPPLY, 1}, {0.52f, SPOT_REST, 1}, {0.54f, SPOT_CRATES, 2},
    {0.56f, SPOT_PUDDLES, 1}, {0.565f, SPOT_LAMPS, 1}, {0.58f, SPOT_ZOMBIES, 2},
    {0.62f, SPOT_TRAPS, 1}, {0.625f, SPOT_AMBUSH, 1}, {0.66f, SPOT_WALL, 1},
    {0.7f, SPOT_RUNNERS, 3}, {0.72f, SPOT_SPIKES, 2}, {0.74f, SPOT_BARRICADE, 1},
    {0.765f, SPOT_AMBUSH, 2}, {0.8f, SPOT_WALL, 2}, {0.84f, SPOT_CRATES, 1}, {0.86f, SPOT_WIRE, 1},
    {0.88f, SPOT_LAMPS, 1}, {0.9f, SPOT_ELITE, 1},
};
static const StageSpot ROUTE_1_5[] = {
    {0.04f, SPOT_ZOMBIES, 1}, {0.06f, SPOT_PUDDLES, 2}, {0.09f, SPOT_BARRELS, 2},
    {0.12f, SPOT_ZOMBIES, 2}, {0.17f, SPOT_BOTTLES, 1}, {0.19f, SPOT_BARRICADE, 1},
    {0.21f, SPOT_WIRE, 1}, {0.24f, SPOT_DYNAMITE, 1}, {0.255f, SPOT_AMBUSH, 2},
    {0.26f, SPOT_NET, 1}, {0.29f, SPOT_WALL, 1}, {0.33f, SPOT_LAMPS, 1}, {0.35f, SPOT_ZOMBIES, 3},
    {0.38f, SPOT_RIVER, 1}, {0.4f, SPOT_RUNNERS, 2}, {0.43f, SPOT_BARRICADE, 1},
    {0.45f, SPOT_TRAPS, 2}, {0.47f, SPOT_CRATES, 2}, {0.49f, SPOT_SUPPLY, 1}, {0.52f, SPOT_REST, 1},
    {0.55f, SPOT_COFFINS, 3}, {0.57f, SPOT_SNARE, 1}, {0.575f, SPOT_AMBUSH, 1},
    {0.61f, SPOT_WALL, 1}, {0.64f, SPOT_RUNNERS, 3}, {0.67f, SPOT_BARRELS, 1},
    {0.69f, SPOT_PUDDLES, 2}, {0.7f, SPOT_ZOMBIES, 2}, {0.72f, SPOT_SPIKES, 2},
    {0.735f, SPOT_AMBUSH, 2}, {0.74f, SPOT_CRATES, 1}, {0.77f, SPOT_WALL, 1}, {0.79f, SPOT_NET, 1},
    {0.8f, SPOT_TRAPS, 1}, {0.81f, SPOT_WIRE, 1}, {0.83f, SPOT_BARRICADE, 1}, {0.85f, SPOT_REST, 1},
    {0.87f, SPOT_RIVER, 1}, {0.88f, SPOT_LAMPS, 1}, {0.91f, SPOT_ELITE, 1},
};

const StageDef STAGES[] = {
    {"1-1", 1, 0, 10, 1, 1.00f, &THEME_ATARDECER, 19000.0f, SPOTS(ROUTE_1_1), WEATHER_WIND, true, false, "music/ruta_1_1"},
    {"1-2", 2, 0, 14, 1, 1.10f, &THEME_ATARDECER, 21500.0f, SPOTS(ROUTE_1_2), WEATHER_RAIN, false, false, "music/ruta_1_2"},
    {"1-3", 3, 0, 13, 1, 1.20f, &THEME_CEMENTERIO, 25000.0f, SPOTS(ROUTE_1_3), WEATHER_RAIN, false, true, "music/ruta_1_3"},
    {"1-4", 4, 0, 19, 1, 1.35f, &THEME_NOCHE, 26500.0f, SPOTS(ROUTE_1_4), WEATHER_WIND, false, true, "music/ruta_1_4"},
    {"1-5", 5, 1, 22, 1, 1.50f, &THEME_PUEBLO_FANTASMA, 31000.0f, SPOTS(ROUTE_1_5), WEATHER_STORM, false, false, "music/ruta_1_5"},
};

const int STAGE_COUNT = (int)(sizeof(STAGES) / sizeof(STAGES[0]));

int stage_supply_dynamite(const StageDef *stage)
{
    return 1 + (stage->length > SUPPLY_DYNAMITE_MEDIUM) + (stage->length > SUPPLY_DYNAMITE_LONG);
}

float stage_xp_share(const StageDef *stage)
{
    return stage->zombies > STAGE_XP_ZOMBIES ? STAGE_XP_ZOMBIES / (float)stage->zombies : 1.0f;
}

int stage_zombie_level(const StageDef *stage, int index)
{
    return stage->zombie_level + (index == stage->zombies - 1 ? stage->boss_bonus : 0);
}

const ZombieStats *stage_zombie_stats(const StageDef *stage, int index)
{
    if (!stage || index < 0 || index >= stage->zombies)
        return &ZOMBIE_RIOT;
    /* Keep the tutorial and the original elite encounters intact. Other
     * existing slots introduce every profession and then its runner. No
     * extra bodies, XP or chests are inserted into the route. Runner spots
     * always contain runners; later ordinary spots finish their catalogue. */
    int next_normal = 1; /* Riot normal already appears throughout 1-1. */
    int next_runner = 0;
    int repeat = 0;
    for (int mission = 0; mission < STAGE_COUNT; mission++) {
        const StageDef *route = &STAGES[mission];
        int k = 0;
        for (int s = 0; s < route->spot_count; s++) {
            const StageSpot *spot = &route->spots[s];
            if (spot->kind != SPOT_ZOMBIES && spot->kind != SPOT_ELITE && spot->kind != SPOT_COFFINS &&
                spot->kind != SPOT_AMBUSH && spot->kind != SPOT_RUNNERS)
                continue;
            for (int body = 0; body < spot->count; body++, k++) {
                const ZombieStats *stats;
                if (spot->kind == SPOT_ELITE) {
                    stats = &ZOMBIE_ELITE;
                } else if (mission == 0) {
                    stats = &ZOMBIE_RIOT;
                } else if (spot->kind == SPOT_RUNNERS) {
                    stats = zombie_stats((ZombieKind)(next_runner++ % ZOMBIE_KIND_COUNT), true);
                } else if (next_normal < ZOMBIE_KIND_ELITE) {
                    stats = zombie_stats((ZombieKind)next_normal++, false);
                } else if (next_runner < ZOMBIE_KIND_COUNT) {
                    stats = zombie_stats((ZombieKind)next_runner++, true);
                } else {
                    /* Repeat a mixture after all fifty are represented.
                     * Normal elites remain reserved for their original spots. */
                    ZombieKind kind = (ZombieKind)((repeat / 2) % ZOMBIE_KIND_ELITE);
                    stats = zombie_stats(kind, (repeat++ % 2) != 0);
                }
                if (stage == route && index == k)
                    return stats;
            }
        }
    }
    /* Standalone/custom route definitions keep the original spot contract. */
    int k = 0;
    for (int s = 0; s < stage->spot_count; s++) {
        const StageSpot *spot = &stage->spots[s];
        if (spot->kind != SPOT_ZOMBIES && spot->kind != SPOT_ELITE && spot->kind != SPOT_COFFINS &&
            spot->kind != SPOT_AMBUSH && spot->kind != SPOT_RUNNERS)
            continue;
        if (index < k + spot->count)
            return spot->kind == SPOT_ELITE ? &ZOMBIE_ELITE :
                   spot->kind == SPOT_RUNNERS ? &ZOMBIE_RUNNER : &ZOMBIE_RIOT;
        k += spot->count;
    }
    return &ZOMBIE_RIOT;
}

bool stage_chest_after(const StageDef *stage, int index)
{
    bool last = index == stage->zombies - 1;
    return last || (stage->chest_every > 0 && (index + 1) % stage->chest_every == 0);
}

void stage_record_init(StageRecord *record)
{
    memset(record, 0, sizeof(*record));
}

bool stage_unlocked(const StageRecord *record, int index)
{
    return index == 0 || (index > 0 && index < STAGE_COUNT && record->cleared[index - 1]);
}
