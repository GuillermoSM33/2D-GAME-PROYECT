#ifndef GAME_JUMP_H
#define GAME_JUMP_H

#include <stdbool.h>

/* Ballistic jump with a fixed peak height and air time (see config.h).
 * Uses the closed-form arc, so the result does not depend on the step size.
 * It starts from whatever she stands on (the ground or a barricade) and ends
 * on whatever is under her when she comes down. */
typedef struct {
    bool airborne;
    float time;   /* Seconds since takeoff */
    float height; /* Window px above the ground; on a barricade, its top while standing */
    float base;   /* Height the arc started from */
    float lift;   /* The arc's height times this (a vault's is higher); 0 = 1 */
} Jump;

void jump_reset(Jump *jump);

/* Takes off only from where she stands. Returns whether it did. */
bool jump_start(Jump *jump);

/* Walked off an edge (or what she stood on broke): drops from the current
 * height as from the top of a jump. */
void jump_fall(Jump *jump);

/* Advances the arc over ground at height floor (0 = the ground). Returns true
 * on the step it lands, at height floor. */
bool jump_update_over(Jump *jump, float dt, float floor);

/* The same over the ground. */
bool jump_update(Jump *jump, float dt);

/* 0 at takeoff, 1 at landing on the ground (held at 1 if the drop is longer). */
float jump_progress(const Jump *jump);

#endif
