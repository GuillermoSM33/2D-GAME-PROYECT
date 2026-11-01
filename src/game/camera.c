#include "game/camera.h"

#include <math.h>

#include "config.h"

float camera_left(float player_x)
{
    float left = player_x - WINDOW_WIDTH / 2.0f;
    return fminf(WORLD_WIDTH - WINDOW_WIDTH, fmaxf(0.0f, left));
}
