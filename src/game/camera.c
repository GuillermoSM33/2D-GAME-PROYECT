#include "game/camera.h"

#include <math.h>

#include "config.h"

float camera_left(float player_x)
{
    float left = player_x - VIEW_WIDTH * CAMERA_PLAYER_SHARE;
    return fminf(WORLD_WIDTH - VIEW_WIDTH, fmaxf(0.0f, left));
}
