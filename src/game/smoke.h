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
} Puff;

typedef struct {
    Puff puffs[SMOKE_MAX_PUFFS];
    unsigned emitted; /* Shots so far: varies each cloud deterministically */
} Smoke;

void smoke_clear(Smoke *smoke);

/* A new cloud at the muzzle (x, y), drifting toward dir (-1 or +1). Puffs of
 * older clouds are reused oldest first when the pool is full. */
void smoke_emit(Smoke *smoke, float x, float y, int dir);

void smoke_update(Smoke *smoke, float dt);

/* Seen once its delay is over. */
bool puff_visible(const Puff *puff);

/* 0..1 along its life. */
float puff_progress(const Puff *puff);

/* Side in art px: grows from SMOKE_PUFF_START_SIZE to SMOKE_PUFF_END_SIZE. */
int puff_size(const Puff *puff);

/* 0..1, fading out toward the end of its life. */
float puff_opacity(const Puff *puff);

int smoke_active_count(const Smoke *smoke);

#endif
