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
    jump->base = jump->height; /* From the ground or from what she stands on */
    return true;
}

void jump_fall(Jump *jump)
{
    if (jump->airborne)
        return;
    /* The arc's top half is skipped: she drops from where she is. */
    jump->airborne = true;
    jump->time = PLAYER_JUMP_TIME / 2.0f;
    jump->base = jump->height - PLAYER_JUMP_HEIGHT;
}

bool jump_update_over(Jump *jump, float dt, float floor)
{
    if (!jump->airborne)
        return false;
    jump->time += dt;
    float t = jump->time;
    jump->height = jump->base + JUMP_VELOCITY * t - 0.5f * JUMP_GRAVITY * t * t;
    bool falling = t >= PLAYER_JUMP_TIME / 2.0f;
    if (falling && jump->height <= floor) {
        jump_reset(jump);
        jump->height = floor;
        return true;
    }
    return false;
}

bool jump_update(Jump *jump, float dt)
{
    return jump_update_over(jump, dt, 0.0f);
}

float jump_progress(const Jump *jump)
{
    if (!jump->airborne)
        return 0.0f;
    float p = jump->time / PLAYER_JUMP_TIME;
    return p < 1.0f ? p : 1.0f;
}
