#include "game/weather_render.h"

#include <math.h>

#include "config.h"
#include "engine/assets.h"

static int window_x(float world_x, float camera_x)
{
    return (int)lroundf((world_x - camera_x) * VIEW_SCALE);
}

static int window_y(float view_y)
{
    return (int)lroundf((float)VIEW_TOP + view_y * VIEW_SCALE);
}

static void draw_rain(SDL_Renderer *renderer, const WeatherState *w, float camera_x)
{
    SDL_SetRenderDrawColor(renderer, 0x10, 0x18, 0x30, w->kind == WEATHER_STORM ? 70 : 45);
    SDL_Rect sky_and_world = {0, 0, WINDOW_WIDTH, WINDOW_HEIGHT};
    SDL_RenderFillRect(renderer, &sky_and_world);
    int slant = weather_blows(w) ? 1 : 0;
    for (int i = 0; i < WEATHER_DROPS; i++) {
        int x = window_x(w->drops[i].x, camera_x);
        int y = window_y(w->drops[i].y);
        int width = i % 4 == 0 ? 2 : 1;
        /* Fine short streaks, with a softer tail; no bright solid overlay. */
        for (int k = 0; k < 3; k++) {
            SDL_SetRenderDrawColor(renderer, 0xa8, 0xc4, 0xdc, (Uint8)(135 - k * 30));
            SDL_Rect bit = {x - k * slant, y - k * 2, width, 2};
            SDL_RenderFillRect(renderer, &bit);
        }
    }
    SDL_SetRenderDrawColor(renderer, 0xc8, 0xdc, 0xec, 105);
    for (int i = 0; i < WEATHER_SPLASHES; i++) {
        if (w->splash_age[i] > 0.15f)
            continue;
        int x = window_x(w->splash_x[i], camera_x);
        int y = window_y((float)(BASELINE + (i * 37 % 60)));
        SDL_Rect left = {x - 2, y - 1, 1, 1};
        SDL_Rect right = {x + 2, y - 1, 1, 1};
        SDL_RenderFillRect(renderer, &left);
        SDL_RenderFillRect(renderer, &right);
    }
}

static void draw_wind(SDL_Renderer *renderer, const WeatherState *w, float camera_x)
{
    for (int i = 0; i < WEATHER_DUST; i++) {
        const WeatherBit *bit = &w->dust[i];
        int x = window_x(bit->x, camera_x);
        int y = window_y(bit->y);
        if (bit->leaf) {
            SDL_SetRenderDrawColor(renderer, 0x8a, 0x6a, 0x3a, 55);
            SDL_Rect leaf = {x, y, 2, 1};
            SDL_RenderFillRect(renderer, &leaf);
        } else {
            Uint8 alpha = (Uint8)(25 + (i * 7) % 24);
            SDL_SetRenderDrawColor(renderer, 0xc8, 0xb0, 0x90, alpha);
            SDL_Rect mote = {x, y, 1, 1};
            SDL_RenderFillRect(renderer, &mote);
        }
    }
    SDL_Texture *weed = assets_texture("sprites/effects/tumbleweed");
    if (!w->tumbling || weed == NULL)
        return;
    const int world_size = TUMBLE_FRAME * SPRITE_SCALE;
    int size = (int)lroundf((float)world_size * VIEW_SCALE);
    SDL_Rect src = {(int)(w->tumble_time * 10.0f) % 4 * TUMBLE_FRAME, 0, TUMBLE_FRAME, TUMBLE_FRAME};
    SDL_Rect dst = {window_x(w->tumble_x, camera_x) - size / 2,
                    window_y((float)(BASELINE - world_size) - w->tumble_height), size, size};
    Uint8 previous_alpha;
    SDL_GetTextureAlphaMod(weed, &previous_alpha);
    SDL_SetTextureAlphaMod(weed, 190);
    SDL_RenderCopy(renderer, weed, &src, &dst);
    SDL_SetTextureAlphaMod(weed, previous_alpha);
}

void weather_render(SDL_Renderer *renderer, const WeatherState *weather, float camera_x)
{
    SDL_BlendMode previous_blend;
    Uint8 red, green, blue, alpha;
    SDL_GetRenderDrawBlendMode(renderer, &previous_blend);
    SDL_GetRenderDrawColor(renderer, &red, &green, &blue, &alpha);
    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
    if (weather_rains(weather))
        draw_rain(renderer, weather, camera_x);
    if (weather_blows(weather))
        draw_wind(renderer, weather, camera_x);
    if (weather->flash > 0.0f) {
        SDL_SetRenderDrawColor(renderer, 0xe8, 0xf0, 0xff,
                              (Uint8)lroundf(fminf(1.0f, weather->flash) * 150.0f));
        SDL_Rect all = {0, 0, WINDOW_WIDTH, WINDOW_HEIGHT};
        SDL_RenderFillRect(renderer, &all);
    }
    SDL_SetRenderDrawColor(renderer, red, green, blue, alpha);
    SDL_SetRenderDrawBlendMode(renderer, previous_blend);
}
