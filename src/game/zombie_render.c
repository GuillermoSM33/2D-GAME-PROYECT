#include "game/zombie_render.h"

#include <math.h>

#include "config.h"
#include "engine/assets.h"
#include "game/health_bar.h"

#define BAR_W 64
#define BAR_H 6
#define BAR_GAP 14 /* Window px between the helmet and the bar */

static void draw_health_bar(SDL_Renderer *renderer, const Zombie *zombie)
{
    int x = (int)lroundf(zombie->x) - BAR_W / 2;
    int y = BASELINE - (int)(ZOMBIE_HEIGHT * SPRITE_SCALE) - BAR_GAP;
    health_bar_draw(renderer, x, y, BAR_W, BAR_H, zombie->health, zombie->stats->health,
                    zombie->stats->armor > 0.0f);
}

void zombie_render(SDL_Renderer *renderer, const Zombie *zombie)
{
    const AnimationDef *def = zombie->anim.def;
    SDL_Texture *sheet = def ? assets_texture(def->sheet) : NULL;
    float opacity = zombie_opacity(zombie);
    if (sheet == NULL || opacity <= 0.0f)
        return;

    bool left = zombie->facing < 0;
    float anchor_x = left ? (float)def->frame_w - def->anchor_x : def->anchor_x;
    SDL_Rect src = {zombie->anim.frame * def->frame_w, 0, def->frame_w, def->frame_h};
    SDL_Rect dst = {
        (int)lroundf(zombie->x - anchor_x * SPRITE_SCALE),
        BASELINE - def->ground_y * SPRITE_SCALE,
        def->frame_w * SPRITE_SCALE,
        def->frame_h * SPRITE_SCALE,
    };
    SDL_RendererFlip flip = left ? SDL_FLIP_HORIZONTAL : SDL_FLIP_NONE;
    SDL_SetTextureAlphaMod(sheet, (Uint8)lroundf(opacity * 255.0f));
    SDL_RenderCopyEx(renderer, sheet, &src, &dst, 0.0, NULL, flip);
    SDL_SetTextureAlphaMod(sheet, 255);

    if (zombie_alive(zombie) && zombie->health < zombie->stats->health)
        draw_health_bar(renderer, zombie);
}
