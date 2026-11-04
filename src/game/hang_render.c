#include "game/hang_render.h"

#include <math.h>

#include "config.h"
#include "engine/assets.h"
#include "engine/platform.h"

float hang_lift(CatchKind kind, float t)
{
    float k = fminf(1.0f, t / CATCH_RISE_TIME);
    return k * (kind == CATCH_NET ? NET_LIFT : kind == CATCH_SNARE ? SNARE_LIFT : 0.0f);
}

int hang_turn(float t)
{
    return t < CATCH_RISE_TIME / 3.0f ? 0 : t < CATCH_RISE_TIME * 2.0f / 3.0f ? 1 : 2;
}

int hang_sway(float t)
{
    return (int)lroundf(sinf(t * 3.0f) * 1.4f);
}

void hang_rope(SDL_Renderer *renderer, float x0, float y0, float x1, float y1)
{
    /* Art px steps along the line, two tones twisting. */
    int steps = (int)(fmaxf(fabsf(x1 - x0), fabsf(y1 - y0)) / SPRITE_SCALE) + 1;
    for (int i = 0; i <= steps; i++) {
        float t = (float)i / (float)steps;
        int x = (int)lroundf((x0 + (x1 - x0) * t) / SPRITE_SCALE) * SPRITE_SCALE;
        int y = (int)lroundf((y0 + (y1 - y0) * t) / SPRITE_SCALE) * SPRITE_SCALE;
        platform_set_color(renderer, i % 2 ? 0x7a6040 : 0xa88a5c);
        SDL_Rect r = {x, y, SPRITE_SCALE, SPRITE_SCALE};
        SDL_RenderFillRect(renderer, &r);
    }
}

float hang_top(CatchKind kind, float t)
{
    float lift = hang_lift(kind, t);
    if (kind == CATCH_NET)
        return lift - 2.0f * SPRITE_SCALE + NET_BAG_H * SPRITE_SCALE;
    return kind == CATCH_SNARE ? lift + PLAYER_WALK_FRAME_H * SPRITE_SCALE : 0.0f;
}

void hang_net(SDL_Renderer *renderer, float anchor_x, float anchor_y, float x, float bottom_y, float t)
{
    SDL_Texture *bag = assets_texture("sprites/effects/net_bag");
    float top = bottom_y - NET_BAG_H * SPRITE_SCALE;
    hang_rope(renderer, anchor_x, anchor_y, x, top);
    if (bag == NULL)
        return;
    /* Just sprung, its mouth still closing; then swaying. */
    int frame = t < CATCH_RISE_TIME * 0.5f ? 2 : t < CATCH_RISE_TIME ? 3 : sinf(t * 3.0f) > 0.0f;
    SDL_Rect src = {frame * NET_BAG_W, 0, NET_BAG_W, NET_BAG_H};
    SDL_Rect dst = {(int)lroundf(x) - NET_BAG_W * SPRITE_SCALE / 2, (int)lroundf(top),
                    NET_BAG_W * SPRITE_SCALE, NET_BAG_H * SPRITE_SCALE};
    SDL_RenderCopy(renderer, bag, &src, &dst);
}
