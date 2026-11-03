/* Window-free SDL integration tests, outside the pure-logic test_*.c set. */
#define SDL_MAIN_HANDLED
#include <math.h>
#include <string.h>

#include <SDL.h>

#include "config.h"
#include "game/weather.h"
#include "game/weather_render.h"
#include "test.h"

static SDL_Surface *surface;
static SDL_Renderer *renderer;
static SDL_Texture *tumbleweed;
static Uint32 baseline[WINDOW_WIDTH * WINDOW_HEIGHT];
static Uint32 actual[WINDOW_WIDTH * WINDOW_HEIGHT];

/* The renderer only needs this one asset lookup. A four-frame texture makes
 * frame selection and preservation of square source pixels observable. */
SDL_Texture *assets_texture(const char *name)
{
    return strcmp(name, "sprites/effects/tumbleweed") == 0 ? tumbleweed : NULL;
}

static void clear(void)
{
    CHECK(SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE) == 0);
    CHECK(SDL_SetRenderDrawColor(renderer, 0x30, 0x40, 0x50, 255) == 0);
    CHECK(SDL_RenderClear(renderer) == 0);
}

static void read_frame(Uint32 *pixels)
{
    CHECK(SDL_RenderReadPixels(renderer, NULL, SDL_PIXELFORMAT_ARGB8888,
                               pixels, WINDOW_WIDTH * (int)sizeof(Uint32)) == 0);
}

static void hide_dust(WeatherState *weather)
{
    for (int i = 0; i < WEATHER_DUST; i++)
        weather->dust[i].x = -100000.0f;
}

static void rain_reaches_the_upper_sky(void)
{
    for (int kind = WEATHER_RAIN; kind <= WEATHER_STORM; kind++) {
        WeatherState weather, no_drops;
        weather_start(&weather, (Weather)kind, 1200.0f);
        no_drops = weather;
        for (int i = 0; i < WEATHER_DROPS; i++)
            no_drops.drops[i].x = -100000.0f;
        clear();
        weather_render(renderer, &no_drops, 1200.0f);
        read_frame(baseline);
        clear();
        weather_render(renderer, &weather, 1200.0f);
        read_frame(actual);
        int top = 0, sky = 0, world = 0;
        for (int y = 0; y < WINDOW_HEIGHT; y++) {
            for (int x = 0; x < WINDOW_WIDTH; x++) {
                if (baseline[y * WINDOW_WIDTH + x] == actual[y * WINDOW_WIDTH + x])
                    continue;
                top += y < 30;
                sky += y < VIEW_TOP;
                world += y >= VIEW_TOP;
            }
        }
        CHECK(top > 0);
        CHECK(sky > 0);
        CHECK(world > 0);
    }
}

static void wind_is_sparse_and_translucent(void)
{
    WeatherState weather;
    weather_start(&weather, WEATHER_WIND, 1200.0f);
    clear();
    read_frame(baseline);
    weather_render(renderer, &weather, 1200.0f);
    read_frame(actual);
    int changed = 0;
    for (int i = 0; i < WINDOW_WIDTH * WINDOW_HEIGHT; i++) {
        if (actual[i] == baseline[i])
            continue;
        Uint8 red, green, blue, alpha;
        SDL_GetRGBA(actual[i], surface->format, &red, &green, &blue, &alpha);
        /* Dust must not become pale opaque streaks or a large screen layer. */
        CHECK(red < 95 && green < 100 && blue < 110);
        CHECK(alpha == 255);
        changed++;
    }
    CHECK(changed > 0);
    CHECK(changed <= 12);
}

static void renderer_state_is_restored(void)
{
    for (int kind = WEATHER_CLEAR; kind <= WEATHER_STORM; kind++) {
        WeatherState weather;
        weather_start(&weather, (Weather)kind, 1200.0f);
        weather.flash = kind == WEATHER_STORM ? 1.0f : 0.0f;
        CHECK(SDL_SetRenderDrawColor(renderer, 7, 8, 9, 10) == 0);
        CHECK(SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_ADD) == 0);
        weather_render(renderer, &weather, 1200.0f);
        Uint8 red, green, blue, alpha;
        SDL_BlendMode blend;
        CHECK(SDL_GetRenderDrawColor(renderer, &red, &green, &blue, &alpha) == 0);
        CHECK(SDL_GetRenderDrawBlendMode(renderer, &blend) == 0);
        CHECK(red == 7 && green == 8 && blue == 9 && alpha == 10);
        CHECK(blend == SDL_BLENDMODE_ADD);
    }
}

static void tumbleweed_keeps_its_source_pixels(void)
{
    SDL_Surface *source = SDL_CreateRGBSurfaceWithFormat(0, TUMBLE_FRAME * 4, TUMBLE_FRAME,
                                                        32, SDL_PIXELFORMAT_ARGB8888);
    CHECK(source != NULL);
    if (source == NULL)
        return;
    Uint32 colors[4] = {
        SDL_MapRGBA(source->format, 200, 80, 60, 255),
        SDL_MapRGBA(source->format, 80, 200, 60, 255),
        SDL_MapRGBA(source->format, 60, 80, 200, 255),
        SDL_MapRGBA(source->format, 200, 180, 60, 255),
    };
    CHECK(SDL_FillRect(source, NULL, 0) == 0);
    for (int frame = 0; frame < 4; frame++) {
        SDL_Rect pixel = {frame * TUMBLE_FRAME + 2, 2, 1, 1};
        CHECK(SDL_FillRect(source, &pixel, colors[frame]) == 0);
    }
    tumbleweed = SDL_CreateTextureFromSurface(renderer, source);
    SDL_FreeSurface(source);
    CHECK(tumbleweed != NULL);
    if (tumbleweed == NULL)
        return;
    CHECK(SDL_SetTextureBlendMode(tumbleweed, SDL_BLENDMODE_BLEND) == 0);
    CHECK(SDL_SetTextureAlphaMod(tumbleweed, 213) == 0);
    for (int frame = 0; frame < 4; frame++) {
        WeatherState weather;
        weather_start(&weather, WEATHER_WIND, 1000.0f);
        hide_dust(&weather);
        weather.tumbling = true;
        weather.tumble_x = 1200.0f;
        weather.tumble_height = 20.0f;
        weather.tumble_time = (float)frame / 10.0f + 0.001f;
        clear();
        read_frame(baseline);
        weather_render(renderer, &weather, 1000.0f);
        read_frame(actual);
        int pixel_scale = (int)lroundf(SPRITE_SCALE * VIEW_SCALE);
        int size = TUMBLE_FRAME * pixel_scale;
        int left = (int)lroundf(200.0f * VIEW_SCALE) - size / 2 + 2 * pixel_scale;
        int top = (int)lroundf((float)VIEW_TOP +
                             ((float)BASELINE - TUMBLE_FRAME * SPRITE_SCALE - 20.0f) * VIEW_SCALE) +
                  2 * pixel_scale;
        Uint32 color = actual[top * WINDOW_WIDTH + left];
        int changed = 0;
        for (int y = 0; y < WINDOW_HEIGHT; y++) {
            for (int x = 0; x < WINDOW_WIDTH; x++) {
                int at = y * WINDOW_WIDTH + x;
                bool in_pixel = x >= left && x < left + pixel_scale &&
                                y >= top && y < top + pixel_scale;
                CHECK(in_pixel ? actual[at] == color : actual[at] == baseline[at]);
                changed += actual[at] != baseline[at];
            }
        }
        CHECK(changed == pixel_scale * pixel_scale);
        Uint8 red, green, blue, alpha, texture_alpha;
        SDL_GetRGBA(color, surface->format, &red, &green, &blue, &alpha);
        CHECK(SDL_GetTextureAlphaMod(tumbleweed, &texture_alpha) == 0);
        CHECK(texture_alpha == 213);
        CHECK(alpha == 255);
        CHECK(frame == 0 ? red > green && red > blue :
              frame == 1 ? green > red && green > blue :
              frame == 2 ? blue > red && blue > green : red > blue && green > blue);
    }
    SDL_DestroyTexture(tumbleweed);
    tumbleweed = NULL;
}

static void clear_weather_keeps_the_frame(void)
{
    WeatherState weather;
    weather_start(&weather, WEATHER_CLEAR, 1200.0f);
    clear();
    read_frame(baseline);
    weather_render(renderer, &weather, 1200.0f);
    read_frame(actual);
    CHECK(memcmp(actual, baseline, sizeof(actual)) == 0);
}

int main(void)
{
    SDL_SetMainReady();
    CHECK(SDL_setenv("SDL_VIDEODRIVER", "dummy", 1) == 0);
    CHECK(SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "0") == SDL_TRUE);
    CHECK(SDL_Init(SDL_INIT_VIDEO) == 0);
    if (test_failures)
        return TEST_EXIT();
    surface = SDL_CreateRGBSurfaceWithFormat(0, WINDOW_WIDTH, WINDOW_HEIGHT, 32,
                                             SDL_PIXELFORMAT_ARGB8888);
    CHECK(surface != NULL);
    if (surface != NULL)
        renderer = SDL_CreateSoftwareRenderer(surface);
    CHECK(renderer != NULL);
    if (renderer != NULL) {
        RUN(rain_reaches_the_upper_sky);
        RUN(wind_is_sparse_and_translucent);
        RUN(renderer_state_is_restored);
        RUN(tumbleweed_keeps_its_source_pixels);
        RUN(clear_weather_keeps_the_frame);
    }
    SDL_DestroyRenderer(renderer);
    SDL_FreeSurface(surface);
    SDL_Quit();
    return TEST_EXIT();
}
