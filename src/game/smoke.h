#ifndef GAME_SMOKE_H
#define GAME_SMOKE_H

#include <stdbool.h>

#include "config.h"

/* Gun smoke: after each shot a few puffs leave the muzzle one after another,
 * rise and drift ahead, grow and fade. They live in the world, so they stay
 * where the shot was if she walks away. */
typedef struct {
    bool active;
    float delay;  /* Seconds before it appears */
    float age;    /* Seconds since it appeared */
    float life;   /* Seconds it takes to fade out completely */
    float x, y;   /* World px, center */
    float vx, vy; /* px per second; vy < 0 rises */
    float phase;  /* Offset of the sideways wobble */
    float scale;  /* Size of its cloud: 1 the revolver's, more for bigger guns */
} Puff;

typedef struct {
    Puff puffs[SMOKE_MAX_PUFFS];
    unsigned emitted; /* Shots so far: varies each cloud deterministically */
} Smoke;

void smoke_clear(Smoke *smoke);

/* A new cloud of `puffs` puffs at the muzzle (x, y), drifting toward dir (-1
 * or +1). `scale` sizes the cloud: its puffs grow bigger and last longer
 * (1 is the revolver's). Puffs of older clouds are reused oldest first when
 * the pool is full. */
void smoke_emit(Smoke *smoke, float x, float y, int dir, int puffs, float scale);

/* Smoke rising off a fire or a blast at (x, y): puffs going straight up,
 * wavering, slower to fade than a shot's. */
void smoke_rise(Smoke *smoke, float x, float y, int puffs, float scale);

void smoke_update(Smoke *smoke, float dt);

/* Seen once its delay is over. */
bool puff_visible(const Puff *puff);

/* 0..1 along its life. */
float puff_progress(const Puff *puff);

/* Side in art px: grows from SMOKE_PUFF_START_SIZE to SMOKE_PUFF_END_SIZE,
 * times its cloud's scale. */
int puff_size(const Puff *puff);

/* 0..1, fading out toward the end of its life. */
float puff_opacity(const Puff *puff);

int smoke_active_count(const Smoke *smoke);

#endif
