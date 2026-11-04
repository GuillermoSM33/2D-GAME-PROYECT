#ifndef GAME_BATS_H
#define GAME_BATS_H

#include <stdbool.h>

#include "config.h"
#include "game/bullet.h"

/* Bats at night: now and then one, or a few, flit across the view from one
 * side to the other, rising and dipping. They don't attack; a bullet or a
 * blast kills one: it drops, lies on the road and fades. No SDL. */
typedef struct {
    float x;      /* World px */
    float height; /* Window px over the ground */
    float base;   /* The height it flits about */
    float vx, vy; /* Px per second; vy up (only falling) */
    int facing;   /* -1 left, +1 right */
    bool alive;   /* In flight */
    bool dead;    /* Shot: falling, then lying on the road */
    float dead_time;
    float time;   /* Seconds since it came */
} Bat;

typedef struct {
    Bat items[BATS_MAX];
    float wait;     /* Seconds until the next ones come */
    unsigned seed;
    int killed;     /* Killed on the last update or shot/blast call */
} Bats;

/* No bats yet; the first come a while in. Same every time for a stage. */
void bats_start(Bats *bats, int stage_index);

/* At night more come every so often from a side of the view (view_left ..
 * + VIEW_WIDTH); each flits across and is gone past the other side. */
void bats_update(Bats *bats, bool night, float view_left, float dt);

/* Bullets against them: a hit kills it and the bullet is spent. Returns the hits. */
int bats_shoot(Bats *bats, Bullets *bullets);

/* A blast at x: bats within radius (and low enough) die. Returns the kills. */
int bats_blast(Bats *bats, float x, float radius);

/* Its frame in sprites/bat/bat: 0-3 the wingbeat, 4 falling, 5 lying dead. */
int bat_frame(const Bat *bat);

/* 1 while flying or fresh dead, fading to 0 before it is gone. */
float bat_opacity(const Bat *bat);

/* Whether it is drawn (flying, falling or lying there). */
bool bat_present(const Bat *bat);

#endif
