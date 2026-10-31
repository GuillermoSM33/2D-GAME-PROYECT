#include "game/scene.h"

#include "config.h"
#include "engine/platform.h"

static const SDL_FPoint HILLS[] = {
    {0, 425}, {130, 380}, {290, 427}, {450, 374}, {650, 425}, {810, 388}, {WINDOW_WIDTH, 422},
};

static void fill_rect(SDL_Renderer *renderer, int x, int y, int w, int h, unsigned rgb)
{
    SDL_Rect rect = {x, y, w, h};
    platform_set_color(renderer, rgb);
    SDL_RenderFillRect(renderer, &rect);
}

static void draw_hills(SDL_Renderer *renderer)
{
    SDL_Color color = {(COLOR_HILLS >> 16) & 0xFF, (COLOR_HILLS >> 8) & 0xFF,
                       COLOR_HILLS & 0xFF, 0xFF};
    int count = (int)(sizeof(HILLS) / sizeof(HILLS[0]));
    /* Each ridge segment becomes a quad down to the baseline. */
    for (int i = 0; i + 1 < count; i++) {
        SDL_FPoint a = HILLS[i], b = HILLS[i + 1];
        SDL_Vertex v[6] = {
            {a, color, {0, 0}}, {b, color, {0, 0}}, {{b.x, BASELINE}, color, {0, 0}},
            {a, color, {0, 0}}, {{b.x, BASELINE}, color, {0, 0}}, {{a.x, BASELINE}, color, {0, 0}},
        };
        SDL_RenderGeometry(renderer, NULL, v, 6, NULL, 0);
    }
}

void scene_draw(SDL_Renderer *renderer)
{
    platform_set_color(renderer, COLOR_BACKGROUND);
    SDL_RenderClear(renderer);

    fill_rect(renderer, 0, 280, WINDOW_WIDTH, BASELINE - 280, COLOR_SKY_BAND);
    draw_hills(renderer);
    fill_rect(renderer, 0, BASELINE - 2, WINDOW_WIDTH, 4, COLOR_GROUND_LINE);
    fill_rect(renderer, 0, BASELINE + 3, WINDOW_WIDTH, WINDOW_HEIGHT - BASELINE - 3, COLOR_GROUND);
    fill_rect(renderer, 0, BASELINE + 15, WINDOW_WIDTH, 2, COLOR_GROUND_STRIPE);
    for (int i = 0; i < WINDOW_WIDTH; i += 56)
        fill_rect(renderer, i + 10, BASELINE + 27 + (i % 3) * 3, 24, 3, COLOR_GROUND_STONES);
}
