#ifndef GAME_BATS_H
#define GAME_BATS_H

#include <stdbool.h>

#include "config.h"
#include "game/bullet.h"

/* Bats at night, like the crows: small colonies along the road, each flitting
 * over its spot through her line of fire. They don't attack and fly off when
 * she walks up to them or at a blast, away from her and up out of the view. A
 * bullet or a blast kills one: it drops, lies on the road and fades. No SDL. */
typedef struct {
    float x;      /* World px */
    float home;   /* The spot it flits over */
    float height; /* Window px over the ground */
    float base;   /* The height it flits about */
    float vx, vy; /* Px per second; vy up (only falling) */
    int facing;   /* -1 left, +1 right */
    bool alive;   /* In flight */
    bool fleeing; /* Flying off, up out of the view */
    bool dead;    /* Shot: falling, then lying on the road */
    float dead_time;
    float time;   /* Seconds it has been flitting */
} Bat;

typedef struct {
    Bat items[BATS_MAX];
} Bats;

/* Colonies along the road from start_x to start_x + length, the same for a
 * stage every time; none by day. */
void bats_start(Bats *bats, int stage_index, float start_x, float length, bool night);

/* She is at player_x: close enough, they go. */
void bats_update(Bats *bats, float player_x, float dt);

/* Bullets against them: a hit kills it, the bullet is spent and the others
 * near it fly off. Returns the hits. */
int bats_shoot(Bats *bats, Bullets *bullets);

/* A blast at x: bats within radius (and low enough) die, the rest take off.
 * Returns the kills. */
int bats_blast(Bats *bats, float x, float radius);

/* Its frame in sprites/bat/bat: 0-3 the wingbeat, 4 falling, 5 lying dead. */
int bat_frame(const Bat *bat);

/* 1 while flying or fresh dead, fading to 0 before it is gone. */
float bat_opacity(const Bat *bat);

/* Whether it is drawn (flying, falling or lying there). */
bool bat_present(const Bat *bat);

#endif
