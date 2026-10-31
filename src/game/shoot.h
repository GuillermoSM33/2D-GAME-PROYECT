#ifndef GAME_SHOOT_H
#define GAME_SHOOT_H

#include <stdbool.h>

/* Standing shot: draw, aim, fire, smoke, holster (see config.h). */
typedef struct {
    bool active;
    bool fired;      /* The bullet already left during this shot */
    int start_frame; /* 0 for a fresh shot, the aim frame for a follow-up */
    float time;      /* Seconds since start_frame */
} Shot;

void shot_reset(Shot *shot);

/* Starts a shot. While one is active, a new shot is only accepted once the
 * previous bullet is out and its muzzle flash was shown; it then skips the
 * draw and restarts already aimed. Returns whether it started. */
bool shot_start(Shot *shot);

/* Advances the sequence. Returns true on the step the bullet fires. */
bool shot_update(Shot *shot, float dt);

/* Sheet frame to show, 0 .. PLAYER_SHOOT_FRAMES - 1. */
int shot_frame(const Shot *shot);

#endif
