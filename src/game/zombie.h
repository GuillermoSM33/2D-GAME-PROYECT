#ifndef GAME_ZOMBIE_H
#define GAME_ZOMBIE_H

#include <stdbool.h>

#include "engine/animation.h"
#include "game/catch.h"

typedef enum {
    ZOMBIE_KIND_RIOT,
    ZOMBIE_KIND_SOLDIER,
    ZOMBIE_KIND_POLICE,
    ZOMBIE_KIND_RIOT_SHIELD,
    ZOMBIE_KIND_CIVIL_MALE_1,
    ZOMBIE_KIND_CIVIL_MALE_2,
    ZOMBIE_KIND_CIVIL_MALE_3,
    ZOMBIE_KIND_CIVIL_MALE_4,
    ZOMBIE_KIND_CIVIL_MALE_5,
    ZOMBIE_KIND_CIVIL_FEMALE_1,
    ZOMBIE_KIND_CIVIL_FEMALE_2,
    ZOMBIE_KIND_CIVIL_FEMALE_3,
    ZOMBIE_KIND_CIVIL_FEMALE_4,
    ZOMBIE_KIND_CIVIL_FEMALE_5,
    ZOMBIE_KIND_BURNED,
    ZOMBIE_KIND_SKELETON,
    ZOMBIE_KIND_DOG,
    ZOMBIE_KIND_SHERIFF,
    ZOMBIE_KIND_COWBOY,
    ZOMBIE_KIND_MOTORCYCLE,
    ZOMBIE_KIND_PRIEST,
    ZOMBIE_KIND_JAILER,
    ZOMBIE_KIND_FIREFIGHTER,
    ZOMBIE_KIND_BUTCHER,
    ZOMBIE_KIND_ELITE,
    /* The city's family (the second route), after the first route's 25: saves
     * and the first route's catalogue count on those staying where they are. */
    ZOMBIE_KIND_CITY_OFFICE,
    ZOMBIE_KIND_CITY_NURSE,
    ZOMBIE_KIND_CITY_WORKER,
    ZOMBIE_KIND_CITY_GUARD,
    ZOMBIE_KIND_CITY_POLICE,
    ZOMBIE_KIND_COUNT
} ZombieKind;

#define ZOMBIE_KINDS_FIRST_ROUTE (ZOMBIE_KIND_ELITE + 1) /* The 25 before the city's */

/* What sets one kind of zombie apart from another, at level 1. Its level
 * scales all three the same way as the player's (progression.c). */
typedef struct {
    int health;
    float armor;
    float attack_base; /* Claw damage at level 1, before the player's armor */
    unsigned tint;     /* 0xRRGGBB multiplied over its sheets: 0xffffff as drawn */
    float speed;       /* Times ZOMBIE_SPEED (and its walk animation) */
    ZombieKind kind;
    bool runner;
} ZombieStats;

typedef struct {
    const char *id; /* sprites/zombies/<id>/... */
    const char *name;
    const char *description;
    const char *armor_profession;
    const ZombieStats *stats; /* Normal variant, level 1 */
} ZombieKindDef;

typedef enum {
    ZOMBIE_ANIM_IDLE, ZOMBIE_ANIM_WALK, ZOMBIE_ANIM_RUN, ZOMBIE_ANIM_ATTACK,
    ZOMBIE_ANIM_HURT, ZOMBIE_ANIM_DEATH, ZOMBIE_ANIM_CAUGHT, ZOMBIE_ANIM_COUNT
} ZombieAnimation;

/* Stable references for every profession and its runner variant. Invalid
 * kind values safely select the original riot profession. */
const ZombieKindDef *zombie_kind_def(ZombieKind kind);
const ZombieStats *zombie_stats(ZombieKind kind, bool runner);
const AnimationDef *zombie_animation(ZombieKind kind, ZombieAnimation action);

extern const ZombieStats ZOMBIE_COMMON; /* Legacy unarmored balance reference */
extern const ZombieStats ZOMBIE_RIOT;   /* Riot gear: same health, 85 armor */
extern const ZombieStats ZOMBIE_ELITE;  /* Heavier riot gear, harder claw, a rusty red tint */
extern const ZombieStats ZOMBIE_RUNNER; /* Legacy light-gear runner; catalogue uses zombie_stats */

typedef enum {
    ZOMBIE_WALK, /* Limping toward the player */
    ZOMBIE_WAIT, /* Within reach, between attacks */
    ZOMBIE_ATTACK, /* Claw swipe; the cooldown starts when it ends */
    ZOMBIE_HURT, /* Recoiling from a hit; stands still */
    ZOMBIE_DEAD  /* Falls, lies still and fades out; then it is gone */
} ZombieState;

/* What a hit did, so the caller can add effects. */
typedef enum {
    HIT_NONE,    /* Already dead */
    HIT_ARMOR,   /* Took damage but kept walking: only the armor shows it */
    HIT_STAGGER, /* Took damage and recoils (the hurt sheet has its own sparks) */
    HIT_KILL     /* Falls (the death sheet has its own sparks too) */
} HitResult;

typedef struct {
    const ZombieStats *stats;
    ZombieKind kind;
    bool runner;
    int level;
    int max_health; /* stats at this level */
    float armor;
    float x;    /* Horizontal center of the body, in world pixels */
    int facing; /* -1 left, +1 right */
    ZombieState state;
    bool awake; /* Asleep it stands where the stage put it until she comes near */
    float idle_time; /* Asleep: its breathing, a slow rise and fall */
    float rouse;     /* Just woken: seconds left of jolting and lurching before it walks */
    bool hidden;     /* Shut in a coffin: not drawn, not hit, until it bursts open */
    float caught;    /* Seconds left held in a trap: it struggles in place */
    CatchKind catch_kind; /* What holds it up while caught (CATCH_NONE: a bear trap) */
    bool wading;          /* In a river: slowed (the stage sets it) */
    float depth;          /* ...and how deep, 0 .. 1 (drawn sunk to the waist) */
    int wind;             /* The wind: +1 blowing right, -1 left, 0 (the stage sets it) */
    float catch_time;     /* Seconds since a hanging trap caught it */
    float catch_anchor_x, catch_anchor_y; /* What the rope hangs from: bough or sapling tip (world x, view y) */
    int health;
    float wound; /* Damage under a whole health point, kept for the next hit */
    float stagger_time; /* While > 0, hits do not make it recoil again */
    float dead_time; /* Seconds since death */
    float attack_cooldown; /* While > 0, it waits instead of attacking */
    bool struck; /* The claw landed its strike frame on this update */
    /* Voice cues: set by the zombie, cleared by whoever plays the sound. */
    bool just_spawned;
    bool growl_due;    /* Every ZOMBIE_GROWL_INTERVAL while alive */
    bool just_died;
    float growl_time;  /* Seconds until the next growl */
    Animation anim;
} Zombie;

/* A fresh zombie at level 1; zombie_set_level makes it stronger. */
void zombie_spawn(Zombie *zombie, const ZombieStats *stats, float x);

/* Scales its health, armor and claw to this level, at full health. */
void zombie_set_level(Zombie *zombie, int level);

/* Where a new zombie enters: near the edge of the view farther from her. */
float zombie_spawn_x(float player_x);

/* An asleep zombie starts its hunt (and its spawn growl): it turns on her
 * and raises its claws for ZOMBIE_ROUSE_TIME, then limps toward her. */
void zombie_wake(Zombie *zombie);

/* Walks toward player_x and, within reach, attacks while the player is
 * alive; asleep it only turns to face her. Once dead it falls, lies and
 * fades; then zombie_gone. The stage may pass a barricade's edge as
 * player_x: it claws its way through that first. */
void zombie_update(Zombie *zombie, float player_x, bool player_alive, float dt);

/* Dead and fully faded out: the stage can place a chest or the next one. */
bool zombie_gone(const Zombie *zombie);

/* Dead and done falling: lying on the ground (it fades later). */
bool zombie_down(const Zombie *zombie);

/* Its walk, for what looks like one (a hallucination). */
const AnimationDef *zombie_walk_animation(void);

/* Damage of one claw strike, before the target's armor. */
float zombie_attack_damage(const Zombie *zombie);

/* Applies one hit of raw damage through the armor. A hit that does not kill
 * makes it recoil, unless it just did: that way a stream of bullets cannot
 * keep it frozen in place. */
HitResult zombie_hit(Zombie *zombie, float damage);

/* The same, counting only armor_share of its armor (1 all of it). */
HitResult zombie_hit_through(Zombie *zombie, float damage, float armor_share);

bool zombie_alive(const Zombie *zombie);

/* Whether a horizontal path from x0 to x1 at height y crosses the body. */
bool zombie_overlaps(const Zombie *zombie, float x0, float x1, float y);

/* Collision dimensions in world/window pixels. The large hound is lower
 * and wider than a human, while its head still meets the normal gun line. */
float zombie_body_height(const Zombie *zombie);
float zombie_body_half_width(const Zombie *zombie);

/* Art px it rises while asleep, breathing: 0 or 1. */
int zombie_breath(const Zombie *zombie);

/* Art px it shakes sideways while it jolts awake (0 otherwise). */
int zombie_shudder(const Zombie *zombie);

/* 1 while alive and while the body lies, then fading to 0. */
float zombie_opacity(const Zombie *zombie);

/* Every animation the zombie uses, so their sheets can be validated. */
const AnimationDef *const *zombie_animations(int *count);

#endif
