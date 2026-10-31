#include "game/effects.h"

#include <string.h>

#include "config.h"

#define SPARKS_SHEET "sprites/effects/sparks"

/* Cut from hurt.png (x 21..40, y 27..38 of its frames 0 and 1). The pivot is
 * the zombie's body center at the height the burst is drawn there, so sparks
 * placed at (zombie x, bullet y) land exactly where the hurt sheet has them. */
static const AnimationDef ANIM_SPARKS = {
    .sheet = SPARKS_SHEET, .frame_w = SPARKS_FRAME_W, .frame_h = SPARKS_FRAME_H,
    .first_frame = 0, .frame_count = SPARKS_FRAMES, .fps = SPARKS_FPS, .loop = false,
    .anchor_x = 6.5f, .ground_y = 6,
};

void effects_clear(Effects *effects)
{
    memset(effects, 0, sizeof(*effects));
}

bool effects_spawn(Effects *effects, const AnimationDef *def, float x, float y, int facing)
{
    for (int i = 0; i < EFFECT_MAX; i++) {
        Effect *e = &effects->items[i];
        if (e->active)
            continue;
        memset(e, 0, sizeof(*e));
        e->active = true;
        e->x = x;
        e->y = y;
        e->facing = facing < 0 ? -1 : 1;
        animation_play(&e->anim, def);
        return true;
    }
    return false;
}

void effects_update(Effects *effects, float dt)
{
    for (int i = 0; i < EFFECT_MAX; i++) {
        Effect *e = &effects->items[i];
        if (!e->active)
            continue;
        /* Finished means the last frame has had its full time. */
        animation_update(&e->anim, dt);
        if (e->anim.finished)
            e->active = false;
    }
}

int effects_active_count(const Effects *effects)
{
    int count = 0;
    for (int i = 0; i < EFFECT_MAX; i++)
        count += effects->items[i].active;
    return count;
}

const AnimationDef *effect_sparks(void)
{
    return &ANIM_SPARKS;
}
