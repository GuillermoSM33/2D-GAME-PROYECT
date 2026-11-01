#include "game/bullet_render.h"

#include <math.h>

#include "config.h"
#include "engine/assets.h"

void bullets_render(SDL_Renderer *renderer, const Bullets *bullets, float camera_x)
{
    const AnimationDef *def = bullet_animation();
    SDL_Texture *sheet = assets_texture(def->sheet);
    if (sheet == NULL)
        return;

    for (int i = 0; i < BULLET_MAX; i++) {
        const Bullet *b = &bullets->items[i];
        if (!b->active)
            continue;
        bool left = b->dir < 0;
        float anchor_x = left ? (float)def->frame_w - def->anchor_x : def->anchor_x;
        SDL_Rect src = {b->anim.frame * def->frame_w, 0, def->frame_w, def->frame_h};
        SDL_Rect dst = {
            (int)lroundf(b->x - camera_x - anchor_x * SPRITE_SCALE),
            (int)lroundf(b->y) - def->ground_y * SPRITE_SCALE,
            def->frame_w * SPRITE_SCALE,
            def->frame_h * SPRITE_SCALE,
        };
        /* Mirrored when flying left, so the spin follows the direction. */
        unsigned tint = b->spec.tint;
        SDL_SetTextureColorMod(sheet, (tint >> 16) & 0xFF, (tint >> 8) & 0xFF, tint & 0xFF);
        SDL_RenderCopyEx(renderer, sheet, &src, &dst, 0.0, NULL,
                         left ? SDL_FLIP_HORIZONTAL : SDL_FLIP_NONE);
        SDL_SetTextureColorMod(sheet, 255, 255, 255);
    }
}
