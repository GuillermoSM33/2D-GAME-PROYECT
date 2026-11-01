#include "game/effects_render.h"

#include <math.h>

#include "config.h"
#include "engine/assets.h"

void effects_render(SDL_Renderer *renderer, const Effects *effects, float camera_x)
{
    for (int i = 0; i < EFFECT_MAX; i++) {
        const Effect *e = &effects->items[i];
        if (!e->active)
            continue;
        const AnimationDef *def = e->anim.def;
        SDL_Texture *sheet = assets_texture(def->sheet);
        if (sheet == NULL)
            continue;
        bool left = e->facing < 0;
        float anchor_x = left ? (float)def->frame_w - def->anchor_x : def->anchor_x;
        SDL_Rect src = {e->anim.frame * def->frame_w, 0, def->frame_w, def->frame_h};
        SDL_Rect dst = {
            (int)lroundf(e->x - camera_x - anchor_x * SPRITE_SCALE),
            (int)lroundf(e->y) - def->ground_y * SPRITE_SCALE,
            def->frame_w * SPRITE_SCALE,
            def->frame_h * SPRITE_SCALE,
        };
        SDL_RenderCopyEx(renderer, sheet, &src, &dst, 0.0, NULL,
                         left ? SDL_FLIP_HORIZONTAL : SDL_FLIP_NONE);
    }
}
