#ifndef GAME_STAGES_H
#define GAME_STAGES_H

#include <stdbool.h>

#include "game/themes.h"
#include "game/weather.h"
#include "game/zombie.h"

/* What stands along a stage's route, at a share of its length. */
typedef enum {
    SPOT_ZOMBIES,   /* A group of count riot zombies, asleep until she comes near */
    SPOT_ELITE,     /* One elite zombie; it always leaves a chest */
    SPOT_BARRICADE, /* Crates across the road: zombies claw through, she can climb on */
    SPOT_WALL,      /* A palisade her height: dynamite or a blast; count 2 adds a barrel by it */
    SPOT_DYNAMITE,  /* A box with a charge for a wall */
    SPOT_CRATES,    /* count loose crates: shoot them open for loot */
    SPOT_BOTTLES,   /* Bottles on a fence: a target for XP */
    SPOT_TRAPS,     /* count bear traps in the dirt */
    SPOT_COFFINS,   /* count coffins, a riot zombie shut in each (more often by night) */
    SPOT_AMBUSH,    /* count riot zombies walking in from off screen when she gets here */
    SPOT_RUNNERS,   /* A pack of count runners (fast, frail), asleep like a group */
    SPOT_WIRE,      /* Barbed wire across the road: cut it (shots, blows) or bleed through */
    SPOT_NET,       /* A net trap under the leaves */
    SPOT_SNARE,     /* A snare by a sapling */
    SPOT_SPIKES,    /* count spike plates */
    SPOT_RIVER,     /* A river across the road: slow to wade */
    SPOT_PUDDLES,   /* count puddles */
    SPOT_LAMPS,     /* count oil lamps on posts: shoot one down to set the ground on fire */
    SPOT_REST,      /* A bench and a campfire by it: sit to reload, warm up to heal */
    SPOT_BARRELS,   /* count powder barrels side by side: a shot blows them up */
    SPOT_SUPPLY,    /* The supply wagon: full magazines and some health, once */
    /* The second route, the town: */
    SPOT_SIREN,     /* A patrol car: walked past or hit, it wails and count zombies come as a horde */
    SPOT_TRAIN,     /* A derailed train across the line: a wall (dynamite); count 2 adds a barrel */
    SPOT_BURNERS,   /* count burning oil drums: light; shot over, their oil burns the road */
    SPOT_OUTPOST,   /* An army outpost: E searches it once (a charge, water, magazines, some health) */
    SPOT_HYDRANTS   /* count fire hydrants: shot, one bursts and its water hits and pushes whoever is near */
} SpotKind;

/* Whether a spot of this kind puts count zombies on the road. */
bool spot_has_zombies(SpotKind kind);

/* Whether a spot of this kind is a wall to open (one charge, or its barrel). */
bool spot_is_wall(SpotKind kind);

typedef struct {
    float at;      /* 0 at the start, 1 at the goal */
    SpotKind kind;
    int count;     /* Zombies or barrels; 1 for the rest */
} StageSpot;

/* The stages of the campaign and how hard each one is. Each is a road from
 * where she starts to a gate length px ahead, with its zombies waiting in
 * groups along it. A stage's zombies are not always its own number: some
 * stages give a breather with the previous level, others push one above,
 * and a stage can end with a stronger zombie. */
typedef struct {
    const char *name;     /* "1-1", shown in the menu and the HUD */
    int zombie_level;     /* Level of its zombies */
    int boss_bonus;       /* Extra levels for the mission's last zombie */
    int zombies;          /* Mission: zombies to beat (its spots' zombies and elites) */
    int chest_every;      /* A chest after every this many beaten (the last always has one) */
    float complexity;     /* Scales its chests' rewards */
    const ThemeDef *theme; /* Its landscape */
    float length;         /* Window px from her start to the goal */
    const StageSpot *spots; /* In route order */
    int spot_count;
    Weather weather;        /* Rain, wind, a storm, or clear */
    bool hot;               /* Heat haze over the road; her blows come slower */
    bool cold;              /* A cold night: slower blows and steps, slower to dry */
    const char *music;      /* Its background track (tools/make_music.py) */
} StageDef;

extern const StageDef STAGES[];
extern const int STAGE_COUNT;

/* Level of the stage's zombie number index (0 = first, in route order). */
int stage_zombie_level(const StageDef *stage, int index);

/* Charges of dynamite the supply wagon holds: more the longer the road
 * (1 short, 2 medium, 3 very long). */
int stage_supply_dynamite(const StageDef *stage);

/* Share of the usual XP each of its kills and zombie chests gives (1 for a
 * stage of STAGE_XP_ZOMBIES zombies or fewer, less with more). */
float stage_xp_share(const StageDef *stage);

/* Stable profession/runner stats of this slot. The tutorial and original
 * elites are unchanged; all fifty catalogue variants appear by the final
 * stage, using the same route slots, zombie counts and rewards. */
const ZombieStats *stage_zombie_stats(const StageDef *stage, int index);

/* Whether beating zombie number index (0 = first) leaves a chest, with the
 * cowgirl's ability (the mission's own chest waits at the goal). */
bool stage_chest_after(const StageDef *stage, int index);

/* What the player keeps between stages besides her progress. */
typedef struct {
    bool cleared[16];       /* Room for 16 stages: the saves keep 16 */
    unsigned stars[16];
    unsigned best_ticks[16]; /* Zero until the first completion. */
} StageRecord;

void stage_record_init(StageRecord *record);

/* The first stage is always open; each next one opens once the previous is cleared. */
bool stage_unlocked(const StageRecord *record, int index);

#endif
