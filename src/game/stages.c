#include "game/stages.h"

#include <string.h>

/* Clearing each stage once (every zombie, every chest) takes her up one level
 * by its end, so she starts each at about its zombies' level. Against that:
 * 1-1 and 1-2 are even fights, 1-3 is a breather with the previous level,
 * 1-4 jumps two levels, and 1-5 ends with a zombie one level above the rest.
 * tests/test_progression.c plays this and keeps it winnable. */
/* The landscape darkens with the difficulty: two sunsets, the graveyard for the
 * breather, a moonlit night for the jump, and the ghost town for the boss. */
const StageDef STAGES[] = {
    {"1-1", 1, 0, 3, 1, 1.00f, &THEME_ATARDECER},
    {"1-2", 2, 0, 4, 1, 1.10f, &THEME_ATARDECER},
    {"1-3", 2, 0, 5, 1, 1.20f, &THEME_CEMENTERIO},
    {"1-4", 4, 0, 5, 1, 1.35f, &THEME_NOCHE},
    {"1-5", 5, 1, 6, 1, 1.50f, &THEME_PUEBLO_FANTASMA},
};

const int STAGE_COUNT = (int)(sizeof(STAGES) / sizeof(STAGES[0]));

int stage_zombie_level(const StageDef *stage, int index)
{
    return stage->zombie_level + (index == stage->zombies - 1 ? stage->boss_bonus : 0);
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
