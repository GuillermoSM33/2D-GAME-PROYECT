#include "game/chest.h"

#include <math.h>
#include <string.h>

#include "config.h"

/* Body on x 15..57 in every frame, resting on row 66 like the zombie. */
static const AnimationDef ANIM_CHEST = {
    .sheet = "sprites/chest/open", .frame_w = CHEST_FRAME_W, .frame_h = CHEST_FRAME_H,
    .first_frame = 0, .frame_count = CHEST_FRAMES, .fps = CHEST_FPS, .loop = false,
    .anchor_x = 36.5f, .ground_y = 68,
};

/* Drawn over the chest on the same template: light through the seam, a burst
 * of rays, then sparkles rising and fading (tools/make_sprites.py). */
static const AnimationDef ANIM_SPARKS = {
    .sheet = "sprites/chest/sparks", .frame_w = CHEST_FRAME_W, .frame_h = CHEST_FRAME_H,
    .first_frame = 0, .frame_count = CHEST_SPARKS_FRAMES, .fps = CHEST_SPARKS_FPS, .loop = false,
    .anchor_x = 36.5f, .ground_y = 68,
};

void chest_clear(Chest *chest)
{
    memset(chest, 0, sizeof(*chest));
}

void chest_place(Chest *chest, float x, int reward_xp)
{
    chest_clear(chest);
    chest->state = CHEST_CLOSED;
    chest->x = x;
    chest->reward_xp = reward_xp;
    animation_play(&chest->anim, &ANIM_CHEST);
}

static void enter(Chest *chest, ChestState state)
{
    chest->state = state;
    chest->time = 0.0f;
}

void chest_update(Chest *chest, float player_x, bool player_alive, float dt)
{
    chest->just_opened = false;
    chest->time += dt;
    switch (chest->state) {
    case CHEST_NONE:
        break;
    case CHEST_CLOSED:
        if (player_alive && fabsf(player_x - chest->x) <= CHEST_OPEN_RANGE) {
            enter(chest, CHEST_OPENING);
            chest->just_opened = true;
        }
        break;
    case CHEST_OPENING:
        animation_update(&chest->anim, dt);
        if (chest->anim.finished)
            enter(chest, CHEST_OPEN);
        break;
    case CHEST_OPEN:
        if (chest->time >= CHEST_STAY_TIME)
            enter(chest, CHEST_FADING);
        break;
    case CHEST_FADING:
        if (chest->time >= CHEST_FADE_TIME)
            chest_clear(chest);
        break;
    }
}

bool chest_present(const Chest *chest)
{
    return chest->state != CHEST_NONE;
}

float chest_opacity(const Chest *chest)
{
    if (chest->state != CHEST_FADING)
        return chest_present(chest) ? 1.0f : 0.0f;
    return fmaxf(0.0f, 1.0f - chest->time / CHEST_FADE_TIME);
}

const AnimationDef *chest_animation(void)
{
    return &ANIM_CHEST;
}

const AnimationDef *chest_sparks(void)
{
    return &ANIM_SPARKS;
}
