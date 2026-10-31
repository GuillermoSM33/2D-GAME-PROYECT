#include "game/jump.h"

#include <string.h>

#include "config.h"

/* From h = v*t - g*t^2/2 with peak PLAYER_JUMP_HEIGHT at PLAYER_JUMP_TIME / 2. */
#define JUMP_VELOCITY (4.0f * PLAYER_JUMP_HEIGHT / PLAYER_JUMP_TIME)
#define JUMP_GRAVITY (8.0f * PLAYER_JUMP_HEIGHT / (PLAYER_JUMP_TIME * PLAYER_JUMP_TIME))

void jump_reset(Jump *jump)
{
    memset(jump, 0, sizeof(*jump));
}

bool jump_start(Jump *jump)
{
    if (jump->airborne)
        return false;
    jump->airborne = true;
    jump->time = 0.0f;
    jump->height = 0.0f;
    return true;
}

bool jump_update(Jump *jump, float dt)
{
    if (!jump->airborne)
        return false;
    jump->time += dt;
    if (jump->time >= PLAYER_JUMP_TIME) {
        jump_reset(jump);
        return true;
    }
    float t = jump->time;
    jump->height = JUMP_VELOCITY * t - 0.5f * JUMP_GRAVITY * t * t;
    return false;
}

float jump_progress(const Jump *jump)
{
    if (!jump->airborne)
        return 0.0f;
    return jump->time / PLAYER_JUMP_TIME;
}
