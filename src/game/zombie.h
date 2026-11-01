#ifndef GAME_ZOMBIE_H
#define GAME_ZOMBIE_H

#include <stdbool.h>

#include "engine/animation.h"

/* What sets one kind of zombie apart from another, at level 1. Its level
 * scales all three the same way as the player's (progression.c). */
typedef struct {
    int health;
    float armor;
    float attack_base; /* Claw damage at level 1, before the player's armor */
} ZombieStats;

extern const ZombieStats ZOMBIE_COMMON; /* Reference for balance; no art yet */
extern const ZombieStats ZOMBIE_RIOT;   /* Riot gear: same health, 80 armor */

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
    int level;
    int max_health; /* stats at this level */
    float armor;
    float x;    /* Horizontal center of the body, in world pixels */
    int facing; /* -1 left, +1 right */
    ZombieState state;
    int health;
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

/* Walks toward player_x and, within reach, attacks while the player is
 * alive. Once dead it falls, lies and fades; then zombie_gone. */
void zombie_update(Zombie *zombie, float player_x, bool player_alive, float dt);

/* Dead and fully faded out: the stage can place a chest or the next one. */
bool zombie_gone(const Zombie *zombie);

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

/* 1 while alive and while the body lies, then fading to 0. */
float zombie_opacity(const Zombie *zombie);

/* Every animation the zombie uses, so their sheets can be validated. */
const AnimationDef *const *zombie_animations(int *count);

#endif
