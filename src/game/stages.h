#ifndef GAME_STAGES_H
#define GAME_STAGES_H

#include <stdbool.h>

#include "game/themes.h"

/* The stages of the campaign and how hard each one is. A stage's zombies are
 * not always its own number: some stages give a breather with the previous
 * level, others push one above, and a stage can end with a stronger zombie. */
typedef struct {
    const char *name;     /* "1-1", shown in the menu and the HUD */
    int zombie_level;     /* Level of its zombies */
    int boss_bonus;       /* Extra levels for the mission's last zombie */
    int zombies;          /* Mission: zombies to beat */
    int chest_every;      /* A chest after every this many beaten (the last always has one) */
    float complexity;     /* Scales its chests' rewards */
    const ThemeDef *theme; /* Its landscape */
} StageDef;

extern const StageDef STAGES[];
extern const int STAGE_COUNT;

/* Level of the stage's zombie number index (0 = first). */
int stage_zombie_level(const StageDef *stage, int index);

/* Whether beating zombie number index (0 = first) leaves a chest. */
bool stage_chest_after(const StageDef *stage, int index);

/* What the player keeps between stages besides her progress. */
typedef struct {
    bool cleared[16];
} StageRecord;

void stage_record_init(StageRecord *record);

/* The first stage is always open; each next one opens once the previous is cleared. */
bool stage_unlocked(const StageRecord *record, int index);

#endif
