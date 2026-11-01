#ifndef GAME_STAGE_RUN_H
#define GAME_STAGE_RUN_H

#include <stdbool.h>

#include "game/chest.h"
#include "game/player.h"
#include "game/progression.h"
#include "game/stages.h"
#include "game/zombie.h"

/* One play of a stage: one zombie at a time; when its body is gone a chest
 * may take its place, and once that is opened and gone the next one comes.
 * Beating the mission's last zombie and opening its chest clears the stage. */
typedef enum {
    RUN_FIGHTING, /* A zombie is out (alive, or falling and fading) */
    RUN_CHEST,    /* Its chest is out */
    RUN_NEXT,     /* Short pause before the next zombie */
    RUN_CLEARED,
    RUN_FAILED    /* She died; R retries */
} RunPhase;

typedef struct {
    int stage_index;
    const StageDef *stage;
    bool drops_chests; /* The character's ability: zombies leave chests, not only the last */
    RunPhase phase;
    int defeated;
    float timer;
    Chest chest;
    /* What happened on the last update, for sounds and popups. */
    int xp_gained;
    int levels_gained;
    bool chest_opened;
    bool cleared_now;
} StageRun;

/* Starts the stage with its first zombie. Without drops_chests (the cowgirl's
 * ability) only the mission's last zombie leaves a chest. */
void run_start(StageRun *run, int stage_index, Zombie *zombie, float player_x, bool drops_chests);

/* Advances the stage after the player and the zombie were updated. XP goes
 * into progress; when it levels her up, apply the new stats to the player. */
void run_update(StageRun *run, Zombie *zombie, const Player *player, Progress *progress, float dt);

#endif
