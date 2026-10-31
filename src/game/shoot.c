#include "game/shoot.h"

#include <string.h>

#include "config.h"

void shot_reset(Shot *shot)
{
    memset(shot, 0, sizeof(*shot));
}

static int raw_frame(const Shot *shot)
{
    return shot->start_frame + (int)(shot->time * PLAYER_SHOOT_FPS);
}

bool shot_start(Shot *shot)
{
    bool follow_up = shot->active;
    if (follow_up && raw_frame(shot) <= PLAYER_SHOOT_FIRE_FRAME)
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
    int frame = raw_frame(shot);
    if (frame >= PLAYER_SHOOT_FRAMES) {
        shot_reset(shot);
        return false;
    }
    if (!shot->fired && frame >= PLAYER_SHOOT_FIRE_FRAME) {
        shot->fired = true;
        return true;
    }
    return false;
}

int shot_frame(const Shot *shot)
{
    int frame = raw_frame(shot);
    return frame < PLAYER_SHOOT_FRAMES ? frame : PLAYER_SHOOT_FRAMES - 1;
}
