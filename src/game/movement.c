#include "game/movement.h"

#include "config.h"

float movement_min_x(void)
{
    return PLAYER_HALF_WIDTH;
}

float movement_max_x(void)
{
    return WORLD_WIDTH - PLAYER_HALF_WIDTH;
}

float movement_step(float x, int dir, bool run, float dt)
{
    float speed = PLAYER_WALK_SPEED * (run ? PLAYER_RUN_SPEED_MULT : 1.0f);
    x += (float)dir * speed * dt;
    if (x < movement_min_x())
        x = movement_min_x();
    if (x > movement_max_x())
        x = movement_max_x();
    return x;
}
