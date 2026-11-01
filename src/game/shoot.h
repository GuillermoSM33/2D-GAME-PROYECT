#ifndef GAME_SHOOT_H
#define GAME_SHOOT_H

#include <stdbool.h>

/* Standing shot: draw, aim, fire, recoil, holster (see config.h). After the
 * bullet she reloads: the recoil frame holds until the next ball is in. */
typedef struct {
    bool active;
    bool fired;      /* The bullet already left during this shot */
    int start_frame; /* 0 for a fresh shot, the aim frame for a follow-up */
    float time;      /* Seconds since start_frame */
    float reload;    /* Seconds left until the next shot can start */
    float reload_time; /* The gun's: what reload restarts at after each bullet */
} Shot;

/* Idle, with the revolver's reload time. */
void shot_reset(Shot *shot);

/* Ends the shot in progress (a jump, a death), keeping the gun's reload time. */
void shot_cancel(Shot *shot);

/* The gun changed: this is its reload time from the next bullet on. */
void shot_set_reload(Shot *shot, float reload_time);

/* Starts a shot. While one is active, a new shot is only accepted once the
 * previous bullet is out, its muzzle flash was shown and she reloaded; it then
 * skips the draw and restarts already aimed. Returns whether it started. */
bool shot_start(Shot *shot);

/* Advances the sequence. Returns true on the step the bullet fires. */
bool shot_update(Shot *shot, float dt);

/* Sheet frame to show, 0 .. PLAYER_SHOOT_FRAMES - 1. */
int shot_frame(const Shot *shot);

#endif
