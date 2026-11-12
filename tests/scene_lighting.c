/* Local light must not relight the distant sky or erase transparent pixels. */
#define SDL_MAIN_HANDLED
#include <string.h>

#include <SDL.h>

#include "config.h"
#include "engine/assets.h"
#include "game/scene.h"
#include "game/terrain_render.h"
#include "test.h"

static SDL_Surface *surface;
static SDL_Renderer *renderer;

SDL_Texture *assets_texture(const char *name) { (void)name; return NULL; }
const EmbeddedImage *assets_find_image(const char *name) { (void)name; return NULL; }
SDL_Texture *assets_texture_graded(SDL_Renderer *r, const char *name, unsigned shadow, unsigned light)
{
    (void)r; (void)name; (void)shadow; (void)light;
    return NULL;
}

static void clear_scene(void)
{
    SDL_RenderSetScale(renderer, 1, 1);
    SDL_RenderSetViewport(renderer, NULL);
    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);
    SDL_SetRenderDrawColor(renderer, 25, 35, 55, 255);
    SDL_RenderClear(renderer);
}

static Uint32 pixel(int x, int y)
{
    Uint32 value = 0;
    SDL_Rect rect = {x, y, 1, 1};
    CHECK(SDL_RenderReadPixels(renderer, &rect, SDL_PIXELFORMAT_ARGB8888, &value, sizeof(value)) == 0);
    return value;
}

static void nearby_blast_lights_the_foreground_without_lighting_the_sky(void)
{
    clear_scene();
    Uint32 sky = pixel(160, 100);
    CHECK(scene_begin_foreground(renderer));
    SDL_SetRenderDrawColor(renderer, 200, 160, 100, 255);
    SDL_RenderFillRect(renderer, &(SDL_Rect){100, 280, 120, 100});
    Lighting lighting = {.night = true, .count = 1};
    lighting.lights[0] = (WorldLight){.kind = LIGHT_EXPLOSION, .x = 160, .y = 315,
                                     .radius = 480, .strength = 1.65f};
    terrain_render_surface_lights(renderer, &lighting, NULL, NULL, 0, 0);
    scene_end_foreground(renderer);
    CHECK(pixel(160, 100) == sky);
    CHECK(pixel(160, 315) != sky);
    Uint8 r, g, b, a;
    SDL_GetRGBA(pixel(160, 315), surface->format, &r, &g, &b, &a);
    CHECK(r >= 190 && r > g && g > b && a == 255);
}

static void an_empty_near_layer_keeps_the_complete_background(void)
{
    clear_scene();
    Uint32 before = pixel(430, 330);
    CHECK(scene_begin_foreground(renderer));
    Lighting lighting = {.night = true};
    terrain_render_surface_lights(renderer, &lighting, NULL, NULL, 0, 0);
    scene_end_foreground(renderer);
    CHECK(pixel(430, 330) == before);
    CHECK(pixel(40, 40) == before);
}

static void viewport_scale_and_parent_target_are_preserved(void)
{
    clear_scene();
    SDL_Rect viewport = {12, 24, 700, 430}, actual;
    SDL_RenderSetScale(renderer, VIEW_SCALE, VIEW_SCALE);
    SDL_RenderSetViewport(renderer, &viewport);
    CHECK(scene_begin_foreground(renderer));
    CHECK(!scene_begin_foreground(renderer)); /* Nesting cannot lose the parent target. */
    scene_end_foreground(renderer);
    SDL_RenderGetViewport(renderer, &actual);
    float x, y;
    SDL_RenderGetScale(renderer, &x, &y);
    CHECK(memcmp(&viewport, &actual, sizeof(viewport)) == 0);
    CHECK_NEAR(x, VIEW_SCALE, .001f);
    CHECK_NEAR(y, VIEW_SCALE, .001f);
    CHECK(SDL_GetRenderTarget(renderer) == NULL);
}

static void shutdown_restores_an_active_parent_and_allows_recreation(void)
{
    clear_scene();
    CHECK(scene_begin_foreground(renderer));
    scene_shutdown();
    CHECK(SDL_GetRenderTarget(renderer) == NULL);
    CHECK(scene_begin_foreground(renderer));
    scene_end_foreground(renderer);
    scene_shutdown();
}

int main(void)
{
    SDL_setenv("SDL_VIDEODRIVER", "dummy", 1);
    CHECK(SDL_Init(SDL_INIT_VIDEO) == 0);
    surface = SDL_CreateRGBSurfaceWithFormat(0, WINDOW_WIDTH, WINDOW_HEIGHT, 32,
                                             SDL_PIXELFORMAT_ARGB8888);
    CHECK(surface != NULL);
    renderer = surface ? SDL_CreateSoftwareRenderer(surface) : NULL;
    CHECK(renderer != NULL);
    if (renderer) {
        RUN(nearby_blast_lights_the_foreground_without_lighting_the_sky);
        RUN(an_empty_near_layer_keeps_the_complete_background);
        RUN(viewport_scale_and_parent_target_are_preserved);
        RUN(shutdown_restores_an_active_parent_and_allows_recreation);
        terrain_render_shutdown();
        scene_shutdown();
        SDL_DestroyRenderer(renderer);
    }
    SDL_FreeSurface(surface);
    SDL_Quit();
    return TEST_EXIT();
}
