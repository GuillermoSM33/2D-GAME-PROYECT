#ifndef GAME_STAGE_RUN_H
#define GAME_STAGE_RUN_H

#include <stdbool.h>

#include "config.h"
#include "game/bullet.h"
#include "game/chest.h"
#include "game/effects.h"
#include "game/player.h"
#include "game/progression.h"
#include "game/stages.h"
#include "game/terrain.h"
#include "game/zombie.h"

/* One play of a stage: a road from her start to a gate. Its zombies wait
 * along it in groups, asleep; a group wakes when she comes near and holds
 * her there (she can't go past it) until it is beaten. Barricades, powder
 * barrels and a supply wagon stand between them. Once every zombie is
 * beaten the mission's chest appears at the gate; opening it clears the
 * stage. With the cowgirl's ability every zombie leaves a chest too, and an
 * elite always does. */
typedef enum {
    RUN_FIGHTING, /* On the road */
    RUN_CLEARED,
    RUN_FAILED    /* She died; R retries */
} RunPhase;

#define RUN_MAX_BLASTS 4
#define RUN_MAX_GRENADES 3

/* A thrown grenade: flying, bouncing, then going off. */
typedef struct {
    bool active;
    float x, height; /* World x; window px over the ground */
    float vx, vy;    /* Px per second; vy up */
    float fuse;      /* Seconds left */
} Grenade;

typedef struct {
    int stage_index;
    const StageDef *stage;
    bool drops_chests; /* The character's ability: every zombie leaves a chest */
    RunPhase phase;
    int defeated;
    int dynamite;    /* Charges she carries */
    Zombie zombies[RUN_MAX_ZOMBIES]; /* In route order */
    int zombie_count;
    int group_of[RUN_MAX_ZOMBIES];   /* Which group each zombie belongs to */
    bool beaten[RUN_MAX_ZOMBIES];     /* Counted as defeated */
    bool chest_done[RUN_MAX_ZOMBIES]; /* Its chest (if any) was placed */
    Chest chests[RUN_MAX_CHESTS];
    int mission_chest;               /* Index into chests, -1 until it appears */
    Terrain terrain;
    float start_x, goal_x;
    float wall_x; /* She can't go right of this while a group fights; 0 = free */
    float target_x; /* Where the zombies are heading this update (her x) */
    int holding;    /* The group holding her after the last update, or -1 */
    /* What happened on the last update, for sounds, effects and popups. */
    int xp_gained;
    int levels_gained;
    int chests_opened;
    float opened_x[RUN_MAX_CHESTS];
    bool cleared_now;
    bool group_beaten;  /* A woken group was just beaten: the road is open */
    bool elite_woke;
    bool supply_taken;
    bool dynamite_taken;
    bool charge_lit;
    /* Crates broken open on this update: what each gave, and where. */
    Loot loot[TERRAIN_EVENTS];
    float loot_x[TERRAIN_EVENTS];
    int loot_count;
    int bottles_hit;   /* Fences cleared of their bottles on this update */
    int coffins_burst; /* Coffins that burst open on this update */
    int traps_sprung;  /* Bear traps that snapped on this update */
    float fire_tick;   /* Seconds until the fires burn again */
    float warmth;      /* Seconds by a campfire toward its next heal */
    float heal_carry;  /* Health earned but under a whole point */
    int healed;        /* Health a bench or a campfire gave: the caller shows it and clears it */
    int blasts;
    float blast_x[RUN_MAX_BLASTS];
    Grenade grenades[RUN_MAX_GRENADES];
} StageRun;

/* Lays out the stage's road ahead of player_x: zombies asleep in their
 * groups, terrain, the gate. Without drops_chests (the cowgirl's ability)
 * only elites and the mission leave chests. */
void run_start(StageRun *run, int stage_index, float player_x, bool drops_chests);

/* Before she moves: what she stands on and how far she may walk. */
void run_place_player(const StageRun *run, Player *player);

/* Bullets against the zombies and the barrels. Returns how many hit. */
int run_bullets(StageRun *run, Bullets *bullets, Effects *effects);

/* Advances the stage after she moved: wakes groups, moves the zombies (round
 * barricades, claws on her or the crates), blasts, supplies, chests, the
 * goal. XP goes into progress; when it levels her up, apply the new stats to
 * the player. Barrels hit as hard as her weapon level (progress). */
void run_update(StageRun *run, Player *player, Progress *progress, float dt);

/* N: leaps over the low barricade right ahead of her, if there is one. */
bool run_vault(StageRun *run, Player *player);

/* E at a bench: sits her down (reloading if needs_reload). The first sit on
 * each bench heals a little (healed). Returns whether she sat. */
bool run_sit(StageRun *run, Player *player, unsigned reload_guns);

/* The grenade leaves her hand (player.threw): it flies ahead the way she
 * faces, bounces off the ground and walls and goes off when its fuse ends,
 * like a barrel (blast_x) but without opening walls. */
void run_throw(StageRun *run, const Player *player);

/* E: lights a charge on the wall she is at, if she carries one. */
bool run_use(StageRun *run, const Player *player);

/* Zombies still to beat in the group holding her, or 0. */
int run_fight_left(const StageRun *run);

#endif
