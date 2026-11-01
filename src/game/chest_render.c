#include "game/chest_render.h"

#include <math.h>

#include "config.h"
#include "engine/assets.h"

void chest_render(SDL_Renderer *renderer, const Chest *chest, float camera_x)
{
    const AnimationDef *def = chest->anim.def;
    SDL_Texture *sheet = def ? assets_texture(def->sheet) : NULL;
    float opacity = chest_opacity(chest);
    if (sheet == NULL || opacity <= 0.0f)
        return;
    SDL_Rect src = {chest->anim.frame * def->frame_w, 0, def->frame_w, def->frame_h};
    SDL_Rect dst = {
        (int)lroundf(chest->x - camera_x - def->anchor_x * SPRITE_SCALE),
        BASELINE - def->ground_y * SPRITE_SCALE,
        def->frame_w * SPRITE_SCALE,
        def->frame_h * SPRITE_SCALE,
    };
    SDL_SetTextureAlphaMod(sheet, (Uint8)lroundf(opacity * 255.0f));
    SDL_RenderCopy(renderer, sheet, &src, &dst);
    SDL_SetTextureAlphaMod(sheet, 255);
}
