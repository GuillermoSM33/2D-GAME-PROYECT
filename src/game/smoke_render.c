#include "game/smoke_render.h"

#include <math.h>

#include "config.h"

static Uint8 channel(unsigned rgb, int shift)
{
    return (Uint8)((rgb >> shift) & 0xFF);
}

/* Fresh smoke is light; it darkens toward the old smoke grey as it spreads. */
static void puff_color(const Puff *puff, Uint8 *r, Uint8 *g, Uint8 *b)
{
    float t = puff_progress(puff);
    *r = (Uint8)lroundf(channel(COLOR_SMOKE_FRESH, 16) + (channel(COLOR_SMOKE_OLD, 16) - channel(COLOR_SMOKE_FRESH, 16)) * t);
    *g = (Uint8)lroundf(channel(COLOR_SMOKE_FRESH, 8) + (channel(COLOR_SMOKE_OLD, 8) - channel(COLOR_SMOKE_FRESH, 8)) * t);
    *b = (Uint8)lroundf(channel(COLOR_SMOKE_FRESH, 0) + (channel(COLOR_SMOKE_OLD, 0) - channel(COLOR_SMOKE_FRESH, 0)) * t);
}

void smoke_render(SDL_Renderer *renderer, const Smoke *smoke, float camera_x)
{
    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
    for (int i = 0; i < SMOKE_MAX_PUFFS; i++) {
        const Puff *p = &smoke->puffs[i];
        if (!puff_visible(p))
            continue;
        Uint8 r, g, b;
        puff_color(p, &r, &g, &b);
        SDL_SetRenderDrawColor(renderer, r, g, b,
                               (Uint8)lroundf(SMOKE_MAX_ALPHA * puff_opacity(p)));
        /* A square with its corners cut, snapped to the art grid like the sprites. */
        int size = puff_size(p) * SPRITE_SCALE;
        int cut = size >= 3 * SPRITE_SCALE ? SPRITE_SCALE : 0;
        int x = (int)floorf((p->x - camera_x) / SPRITE_SCALE) * SPRITE_SCALE - size / 2;
        int y = (int)floorf(p->y / SPRITE_SCALE) * SPRITE_SCALE - size / 2;
        SDL_Rect wide = {x, y + cut, size, size - 2 * cut};
        SDL_RenderFillRect(renderer, &wide);
        if (cut) {
            SDL_Rect tall = {x + cut, y, size - 2 * cut, cut};
            SDL_RenderFillRect(renderer, &tall);
            tall.y = y + size - cut;
            SDL_RenderFillRect(renderer, &tall);
        }
    }
    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);
}
