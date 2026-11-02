#include "game/stages.h"

#include <string.h>

#include "config.h"

/* Clearing each stage once (every zombie, every chest) takes her up one level
 * by its end, so she starts each at about its zombies' level. Against that:
 * 1-1 and 1-2 are even fights, 1-3 is a breather with the previous level,
 * 1-4 jumps two levels, and 1-5 ends with a zombie one level above the rest.
 * tests/test_progression.c plays this and keeps it winnable. */
/* The landscape darkens with the difficulty: two sunsets, the graveyard for the
 * breather, a moonlit night for the jump, and the ghost town for the boss. */
/* Routes, about 12-20 views long, each with its own things on the road:
 * the sunset ones bottles on fences to shoot and crates, 1-2 bear traps in
 * a group's path; the graveyard coffins that burst open (an ambush) and
 * traps; the night oil lamps over the zombies' way, to shoot down into a
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
    {0.31f, SPOT_WALL, 1}, {0.38f, SPOT_BARRELS, 1}, {0.41f, SPOT_ZOMBIES, 2},
    {0.46f, SPOT_CRATES, 1}, {0.50f, SPOT_SUPPLY, 1}, {0.54f, SPOT_REST, 1},
    {0.58f, SPOT_BARRICADE, 1}, {0.66f, SPOT_WALL, 2}, {0.70f, SPOT_BOTTLES, 1}, {0.75f, SPOT_ZOMBIES, 1},
    {0.80f, SPOT_CRATES, 2}, {0.86f, SPOT_BARRICADE, 1},
};
static const StageSpot ROUTE_1_2[] = {
    {0.05f, SPOT_ZOMBIES, 1}, {0.08f, SPOT_BOTTLES, 1}, {0.11f, SPOT_BARRELS, 2},
    {0.14f, SPOT_ZOMBIES, 2}, {0.22f, SPOT_BARRICADE, 1}, {0.26f, SPOT_TRAPS, 1},
    {0.28f, SPOT_ZOMBIES, 2}, {0.35f, SPOT_WALL, 2}, {0.40f, SPOT_CRATES, 2},
    {0.44f, SPOT_DYNAMITE, 1}, {0.50f, SPOT_SUPPLY, 1}, {0.53f, SPOT_REST, 1},
    {0.57f, SPOT_ZOMBIES, 1},
    {0.60f, SPOT_CRATES, 1}, {0.63f, SPOT_WALL, 1}, {0.72f, SPOT_BARRELS, 1},
    {0.73f, SPOT_TRAPS, 1}, {0.75f, SPOT_ZOMBIES, 2}, {0.82f, SPOT_BOTTLES, 1},
    {0.86f, SPOT_BARRICADE, 1},
};
static const StageSpot ROUTE_1_3[] = {
    {0.05f, SPOT_ZOMBIES, 1}, {0.12f, SPOT_BARRICADE, 1}, {0.16f, SPOT_COFFINS, 1},
    {0.22f, SPOT_CRATES, 1}, {0.26f, SPOT_DYNAMITE, 1}, {0.32f, SPOT_WALL, 1},
    {0.37f, SPOT_CRATES, 2}, {0.40f, SPOT_TRAPS, 1}, {0.42f, SPOT_ZOMBIES, 1},
    {0.50f, SPOT_SUPPLY, 1}, {0.53f, SPOT_REST, 1}, {0.56f, SPOT_TRAPS, 1},
    {0.62f, SPOT_COFFINS, 2},
    {0.72f, SPOT_WALL, 1}, {0.80f, SPOT_WALL, 2}, {0.84f, SPOT_CRATES, 1},
    {0.90f, SPOT_ELITE, 1},
};
static const StageSpot ROUTE_1_4[] = {
    {0.05f, SPOT_LAMPS, 1}, {0.08f, SPOT_ZOMBIES, 2}, {0.15f, SPOT_DYNAMITE, 1},
    {0.18f, SPOT_CRATES, 1}, {0.205f, SPOT_LAMPS, 1}, {0.22f, SPOT_ZOMBIES, 2},
    {0.29f, SPOT_WALL, 1}, {0.36f, SPOT_BARRICADE, 1}, {0.42f, SPOT_ZOMBIES, 2},
    {0.50f, SPOT_SUPPLY, 1}, {0.52f, SPOT_REST, 1}, {0.54f, SPOT_CRATES, 2},
    {0.565f, SPOT_LAMPS, 1},
    {0.58f, SPOT_ZOMBIES, 2}, {0.66f, SPOT_WALL, 1}, {0.74f, SPOT_BARRICADE, 1},
    {0.80f, SPOT_WALL, 2}, {0.84f, SPOT_CRATES, 1}, {0.88f, SPOT_LAMPS, 1},
    {0.90f, SPOT_ELITE, 1},
};
static const StageSpot ROUTE_1_5[] = {
    {0.04f, SPOT_ZOMBIES, 1}, {0.09f, SPOT_BARRELS, 2}, {0.12f, SPOT_ZOMBIES, 2},
    {0.17f, SPOT_BOTTLES, 1}, {0.19f, SPOT_BARRICADE, 1}, {0.24f, SPOT_DYNAMITE, 1},
    {0.29f, SPOT_WALL, 1}, {0.33f, SPOT_LAMPS, 1}, {0.35f, SPOT_ZOMBIES, 3},
    {0.43f, SPOT_BARRICADE, 1}, {0.46f, SPOT_CRATES, 2}, {0.49f, SPOT_SUPPLY, 1},
    {0.52f, SPOT_REST, 1}, {0.55f, SPOT_COFFINS, 2}, {0.61f, SPOT_WALL, 1}, {0.67f, SPOT_BARRELS, 1},
    {0.70f, SPOT_ZOMBIES, 2}, {0.74f, SPOT_CRATES, 1}, {0.77f, SPOT_WALL, 1},
    {0.80f, SPOT_TRAPS, 1}, {0.83f, SPOT_BARRICADE, 1}, {0.85f, SPOT_REST, 1},
    {0.88f, SPOT_LAMPS, 1}, {0.91f, SPOT_ELITE, 1},
};

const StageDef STAGES[] = {
    {"1-1", 1, 0, 6, 1, 1.00f, &THEME_ATARDECER, 19000.0f, SPOTS(ROUTE_1_1)},
    {"1-2", 2, 0, 8, 1, 1.10f, &THEME_ATARDECER, 21500.0f, SPOTS(ROUTE_1_2)},
    {"1-3", 2, 0, 6, 1, 1.20f, &THEME_CEMENTERIO, 25000.0f, SPOTS(ROUTE_1_3)},
    {"1-4", 4, 0, 9, 1, 1.35f, &THEME_NOCHE, 26500.0f, SPOTS(ROUTE_1_4)},
    {"1-5", 5, 1, 11, 1, 1.50f, &THEME_PUEBLO_FANTASMA, 31000.0f, SPOTS(ROUTE_1_5)},
};

const int STAGE_COUNT = (int)(sizeof(STAGES) / sizeof(STAGES[0]));

int stage_supply_dynamite(const StageDef *stage)
{
    return 1 + (stage->length > SUPPLY_DYNAMITE_MEDIUM) + (stage->length > SUPPLY_DYNAMITE_LONG);
}

int stage_zombie_level(const StageDef *stage, int index)
{
    return stage->zombie_level + (index == stage->zombies - 1 ? stage->boss_bonus : 0);
}

const ZombieStats *stage_zombie_stats(const StageDef *stage, int index)
{
    int k = 0;
    for (int s = 0; s < stage->spot_count; s++) {
        const StageSpot *spot = &stage->spots[s];
        if (spot->kind != SPOT_ZOMBIES && spot->kind != SPOT_ELITE && spot->kind != SPOT_COFFINS)
            continue;
        if (index < k + spot->count)
            return spot->kind == SPOT_ELITE ? &ZOMBIE_ELITE : &ZOMBIE_RIOT;
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
