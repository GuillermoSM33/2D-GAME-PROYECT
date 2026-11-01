#include "game/shoot.h"

#include <math.h>
#include <string.h>

#include "config.h"

void shot_reset(Shot *shot)
{
    memset(shot, 0, sizeof(*shot));
    shot->reload_time = PLAYER_SHOOT_RELOAD_TIME;
}

void shot_cancel(Shot *shot)
{
    float reload_time = shot->reload_time;
    memset(shot, 0, sizeof(*shot));
    shot->reload_time = reload_time;
}

void shot_set_reload(Shot *shot, float reload_time)
{
    shot->reload_time = reload_time;
}

static int raw_frame(const Shot *shot)
{
    return shot->start_frame + (int)(shot->time * PLAYER_SHOOT_FPS);
}

bool shot_start(Shot *shot)
{
    bool follow_up = shot->active;
    if (follow_up && (raw_frame(shot) <= PLAYER_SHOOT_FIRE_FRAME || shot->reload > 0.0f))
        return false;
    shot->active = true;
    shot->fired = false;
    shot->start_frame = follow_up ? PLAYER_SHOOT_AIM_FRAME : 0;
    shot->time = 0.0f;
    return true;
}

bool shot_update(Shot *shot, float dt)
{
    if (!shot->active)
        return false;
    shot->time += dt;
    shot->reload = fmaxf(0.0f, shot->reload - dt);
    int frame = raw_frame(shot);
    if (shot->fired && shot->reload > 0.0f && frame > PLAYER_SHOOT_RELOAD_FRAME) {
        /* Reloading: stay mid-frame on the recoil until the ball is in. */
        shot->time = ((float)(PLAYER_SHOOT_RELOAD_FRAME - shot->start_frame) + 0.5f) / PLAYER_SHOOT_FPS;
        frame = PLAYER_SHOOT_RELOAD_FRAME;
    }
    if (frame >= PLAYER_SHOOT_FRAMES) {
        shot_cancel(shot);
        return false;
    }
    if (!shot->fired && frame >= PLAYER_SHOOT_FIRE_FRAME) {
        shot->fired = true;
        shot->reload = shot->reload_time;
        return true;
    }
    return false;
}

int shot_frame(const Shot *shot)
{
    int frame = raw_frame(shot);
    return frame < PLAYER_SHOOT_FRAMES ? frame : PLAYER_SHOOT_FRAMES - 1;
}
