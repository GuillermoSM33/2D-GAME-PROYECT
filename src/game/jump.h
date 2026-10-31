#ifndef GAME_JUMP_H
#define GAME_JUMP_H

#include <stdbool.h>

/* Ballistic jump with a fixed peak height and air time (see config.h).
 * Uses the closed-form arc, so the result does not depend on the step size. */
typedef struct {
    bool airborne;
    float time;   /* Seconds since takeoff */
    float height; /* Window px above the ground */
} Jump;

void jump_reset(Jump *jump);

/* Takes off only from the ground. Returns whether it did. */
bool jump_start(Jump *jump);

/* Advances the arc. Returns true on the step it lands. */
bool jump_update(Jump *jump, float dt);

/* 0 at takeoff, 1 at landing. */
float jump_progress(const Jump *jump);

#endif
