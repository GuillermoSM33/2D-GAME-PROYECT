#include "game/health_bar.h"

#include "config.h"
#include "engine/platform.h"

void health_bar_draw(SDL_Renderer *renderer, int x, int y, int w, int h,
                     int health, int max, bool armored)
{
    int fill = max > 0 ? w * health / max : 0;
    if (armored) {
        platform_set_color(renderer, COLOR_HEALTH_ARMOR);
        SDL_RenderFillRect(renderer, &(SDL_Rect){x - 2, y - 2, w + 4, h + 4});
    }
    platform_set_color(renderer, COLOR_HEALTH_BACK);
    SDL_RenderFillRect(renderer, &(SDL_Rect){x, y, w, h});
    platform_set_color(renderer, COLOR_HEALTH_FILL);
    SDL_RenderFillRect(renderer, &(SDL_Rect){x, y, fill, h});
}
