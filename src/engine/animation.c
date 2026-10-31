#include "engine/animation.h"

#include <stddef.h>

void animation_play(Animation *anim, const AnimationDef *def)
{
    if (anim->def == def)
        return;
    anim->def = def;
    animation_restart(anim);
}

void animation_restart(Animation *anim)
{
    anim->time = 0.0f;
    anim->finished = false;
    anim->frame = anim->def ? anim->def->first_frame : 0;
}

void animation_update(Animation *anim, float dt)
{
    const AnimationDef *def = anim->def;
    if (def == NULL || def->frame_count <= 1 || def->fps <= 0.0f || anim->finished)
        return;

    anim->time += dt;
    int offset = (int)(anim->time * def->fps);
    if (def->loop) {
        offset %= def->frame_count;
    } else if (offset >= def->frame_count) {
        offset = def->frame_count - 1;
        anim->finished = true;
    }
    anim->frame = def->first_frame + offset;
}

void animation_seek(Animation *anim, int offset)
{
    animation_set_frame(anim, offset);
    if (anim->def && anim->def->fps > 0.0f)
        anim->time = (float)(anim->frame - anim->def->first_frame) / anim->def->fps;
}

void animation_set_frame(Animation *anim, int offset)
{
    const AnimationDef *def = anim->def;
    if (def == NULL || def->frame_count <= 0)
        return;
    if (offset < 0)
        offset = 0;
    if (offset >= def->frame_count)
        offset = def->frame_count - 1;
    anim->frame = def->first_frame + offset;
}

void animation_set_progress(Animation *anim, float progress)
{
    const AnimationDef *def = anim->def;
    if (def == NULL || def->frame_count <= 0)
        return;
    int offset = (int)(progress * (float)def->frame_count);
    if (offset < 0)
        offset = 0;
    if (offset >= def->frame_count)
        offset = def->frame_count - 1;
    anim->frame = def->first_frame + offset;
    anim->finished = progress >= 1.0f;
}
