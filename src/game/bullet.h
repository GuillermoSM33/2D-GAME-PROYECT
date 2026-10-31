#ifndef GAME_BULLET_H
#define GAME_BULLET_H

#include <stdbool.h>

#include "config.h"
#include "engine/animation.h"

typedef struct {
    bool active;
    float x, y;   /* Center of the ball, in window pixels */
    float prev_x; /* Where the last step started: it swept prev_x..x */
    int dir;    /* -1 left, +1 right */
    Animation anim;
} Bullet;

/* Fixed pool: no allocation while playing. */
typedef struct {
    Bullet items[BULLET_MAX];
} Bullets;

void bullets_clear(Bullets *bullets);

/* from_x is where the shot starts (the gun hand), x where the ball appears (the
 * muzzle): anything in between is hit too, even at point-blank range.
 * Returns false when the pool is full (the shot still happens, without a ball). */
bool bullets_spawn(Bullets *bullets, float from_x, float x, float y, int dir);

/* Moves every bullet and removes the ones that left the window. */
void bullets_update(Bullets *bullets, float dt);

int bullets_active_count(const Bullets *bullets);

const AnimationDef *bullet_animation(void);

#endif
