/* Software-renderer integration tests; this file deliberately stays outside
 * test_*.c, whose binaries have no SDL dependency. No game images required. */
#define SDL_MAIN_HANDLED
#include <math.h>
#include <string.h>

#include <SDL.h>

#include "config.h"
#include "game/lighting.h"
#include "game/terrain_render.h"
#include "test.h"

static SDL_Surface *surface;
static SDL_Renderer *renderer;
static SDL_Texture *glow;
static Uint32 baseline[VIEW_WIDTH * VIEW_HEIGHT];
static Uint32 actual[VIEW_WIDTH * VIEW_HEIGHT];

SDL_Texture *assets_texture(const char *name)
{
    return strcmp(name, "sprites/effects/glow") == 0 ? glow : NULL;
}

static void clear_frame(void)
{
    CHECK(SDL_RenderSetViewport(renderer, NULL) == 0);
    CHECK(SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE) == 0);
    CHECK(SDL_SetRenderDrawColor(renderer, 180, 180, 180, 255) == 0);
    CHECK(SDL_RenderClear(renderer) == 0);
}

static void read_frame(Uint32 *pixels)
{
    CHECK(SDL_RenderReadPixels(renderer, NULL, SDL_PIXELFORMAT_ARGB8888,
                               pixels, VIEW_WIDTH * (int)sizeof(Uint32)) == 0);
}

static void color_at(const Uint32 *pixels, int x, int y, Uint8 *red, Uint8 *green, Uint8 *blue)
{
    Uint8 alpha;
    SDL_GetRGBA(pixels[y * VIEW_WIDTH + x], surface->format, red, green, blue, &alpha);
    CHECK(alpha == 255);
}

static Lighting night_light(void)
{
    Lighting lighting = {.night = true, .count = 1};
    lighting.lights[0] = (WorldLight){.kind = LIGHT_LANTERN, .x = 640.0f,
                                     .y = 250.0f, .radius = 320.0f, .strength = 0.95f};
    return lighting;
}

static void night_ambient_and_warm_surface_light(void)
{
    Lighting lighting = night_light();
    clear_frame();
    terrain_render_lights(renderer, &lighting, NULL, NULL, 0, 0.0f);
    read_frame(actual);
    Uint8 ar, ag, ab, nr, ng, nb;
    color_at(actual, 40, 40, &ar, &ag, &ab);
    color_at(actual, 640, 250, &nr, &ng, &nb);
    CHECK(ar < 180 && ag < 180 && ab < 180);
    CHECK(ab > ar); /* The unlit world retains a cool night tint. */
    CHECK(nr > ar && ng > ag && nb >= ab);
    CHECK(nr >= ng && ng > nb); /* The nearby lantern warms the surface. */
}

static void daylight_without_glow_keeps_the_surface(void)
{
    Lighting lighting = night_light();
    lighting.night = false;
    Player player;
    player_init(&player);
    player.x = 680.0f;
    clear_frame();
    read_frame(baseline);
    terrain_render_lights(renderer, &lighting, &player, NULL, 0, 0.0f);
    read_frame(actual);
    CHECK(memcmp(baseline, actual, sizeof(actual)) == 0);
}

static void camera_coordinates_match_a_translated_scene(void)
{
    Lighting a = night_light();
    Lighting b = a;
    b.lights[0].x += 1000.0f;
    clear_frame();
    terrain_render_lights(renderer, &a, NULL, NULL, 0, 0.0f);
    read_frame(baseline);
    clear_frame();
    terrain_render_lights(renderer, &b, NULL, NULL, 0, 1000.0f);
    read_frame(actual);
    CHECK(memcmp(baseline, actual, sizeof(actual)) == 0);
}

static void viewport_protects_the_surrounding_ui_band(void)
{
    Lighting lighting = night_light();
    clear_frame();
    read_frame(baseline);
    SDL_Rect viewport = {16, 28, VIEW_WIDTH - 32, VIEW_HEIGHT - 44};
    CHECK(SDL_RenderSetViewport(renderer, &viewport) == 0);
    terrain_render_lights(renderer, &lighting, NULL, NULL, 0, 0.0f);
    SDL_Rect after;
    SDL_RenderGetViewport(renderer, &after);
    CHECK(SDL_RectEquals(&after, &viewport));
    CHECK(SDL_RenderSetViewport(renderer, NULL) == 0);
    read_frame(actual);
    int protected_changed = 0, world_changed = 0;
    for (int y = 0; y < VIEW_HEIGHT; y++) {
        for (int x = 0; x < VIEW_WIDTH; x++) {
            if (actual[y * VIEW_WIDTH + x] == baseline[y * VIEW_WIDTH + x])
                continue;
            bool inside = x >= viewport.x && x < viewport.x + viewport.w &&
                          y >= viewport.y && y < viewport.y + viewport.h;
            if (inside)
                world_changed++;
            else
                protected_changed++;
        }
    }
    CHECK(world_changed > 0 && protected_changed == 0);
}

static void ground_shadows_render_and_hidden_bodies_do_not_cast(void)
{
    Lighting lighting = night_light();
    lighting.lights[0].x = 500.0f;
    lighting.lights[0].radius = 650.0f;
    Zombie zombie;
    zombie_spawn(&zombie, zombie_stats(ZOMBIE_KIND_DOG, false), 650.0f);
    clear_frame();
    terrain_render_lights(renderer, &lighting, NULL, NULL, 0, 0.0f);
    read_frame(baseline);
    clear_frame();
    terrain_render_lights(renderer, &lighting, NULL, &zombie, 1, 0.0f);
    read_frame(actual);
    int ground_changes = 0, sky_changes = 0;
    for (int y = 0; y < VIEW_HEIGHT; y++) {
        for (int x = 0; x < VIEW_WIDTH; x++) {
            if (actual[y * VIEW_WIDTH + x] == baseline[y * VIEW_WIDTH + x])
                continue;
            if (y > BASELINE)
                ground_changes++;
            else
                sky_changes++;
        }
    }
    CHECK(ground_changes > 0 && sky_changes == 0);
    zombie.hidden = true;
    clear_frame();
    terrain_render_lights(renderer, &lighting, NULL, &zombie, 1, 0.0f);
    read_frame(actual);
    CHECK(memcmp(baseline, actual, sizeof(actual)) == 0);
    zombie.hidden = false;
    zombie.caught = 1.0f;
    clear_frame();
    terrain_render_lights(renderer, &lighting, NULL, &zombie, 1, 0.0f);
    read_frame(actual);
    CHECK(memcmp(baseline, actual, sizeof(actual)) == 0);
    zombie.caught = 0.0f;
    zombie.state = ZOMBIE_DEAD;
    clear_frame();
    terrain_render_lights(renderer, &lighting, NULL, &zombie, 1, 0.0f);
    read_frame(actual);
    CHECK(memcmp(baseline, actual, sizeof(actual)) == 0);
}

static void make_glow(void)
{
    SDL_Surface *source = SDL_CreateRGBSurfaceWithFormat(0, 16, 16, 32, SDL_PIXELFORMAT_ARGB8888);
    CHECK(source != NULL);
    if (!source)
        return;
    for (int y = 0; y < 16; y++) {
        Uint32 *row = (Uint32 *)((Uint8 *)source->pixels + y * source->pitch);
        for (int x = 0; x < 16; x++) {
            float dx = x - 7.5f, dy = y - 7.5f;
            float strength = fmaxf(0.0f, 1.0f - sqrtf(dx * dx + dy * dy) / 8.0f);
            row[x] = SDL_MapRGBA(source->format, 255, 255, 255, (Uint8)lroundf(strength * 255.0f));
        }
    }
    glow = SDL_CreateTextureFromSurface(renderer, source);
    SDL_FreeSurface(source);
    CHECK(glow != NULL);
}

static void draw_and_texture_state_are_restored(void)
{
    make_glow();
    if (!glow)
        return;
    Lighting lighting = night_light();
    lighting.count = 2;
    lighting.lights[1] = (WorldLight){.kind = LIGHT_EXPLOSION, .x = 200.0f,
                                     .y = 300.0f, .radius = 400.0f, .strength = 1.5f};
    CHECK(SDL_SetTextureColorMod(glow, 7, 18, 29) == 0);
    CHECK(SDL_SetTextureAlphaMod(glow, 77) == 0);
    CHECK(SDL_SetTextureBlendMode(glow, SDL_BLENDMODE_MOD) == 0);
    for (int night = 0; night < 2; night++) {
        lighting.night = night != 0;
        clear_frame();
        CHECK(SDL_SetRenderDrawColor(renderer, 31, 42, 53, 64) == 0);
        CHECK(SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_ADD) == 0);
        terrain_render_lights(renderer, &lighting, NULL, NULL, 0, 0.0f);
        Uint8 red, green, blue, alpha;
        SDL_BlendMode blend;
        CHECK(SDL_GetRenderDrawColor(renderer, &red, &green, &blue, &alpha) == 0);
        CHECK(red == 31 && green == 42 && blue == 53 && alpha == 64);
        CHECK(SDL_GetRenderDrawBlendMode(renderer, &blend) == 0 && blend == SDL_BLENDMODE_ADD);
        CHECK(SDL_GetTextureColorMod(glow, &red, &green, &blue) == 0);
        CHECK(red == 7 && green == 18 && blue == 29);
        CHECK(SDL_GetTextureAlphaMod(glow, &alpha) == 0 && alpha == 77);
        CHECK(SDL_GetTextureBlendMode(glow, &blend) == 0 && blend == SDL_BLENDMODE_MOD);
        if (!night) {
            read_frame(actual);
            for (int i = 0; i < VIEW_WIDTH * VIEW_HEIGHT; i++) {
                SDL_GetRGBA(actual[i], surface->format, &red, &green, &blue, &alpha);
                CHECK(red >= 180 && green >= 180 && blue >= 180 && alpha == 255);
            }
        }
    }
    SDL_DestroyTexture(glow);
    glow = NULL;
}

static void shutdown_and_resource_recreation_keep_the_result(void)
{
    Lighting lighting = night_light();
    clear_frame();
    terrain_render_lights(renderer, &lighting, NULL, NULL, 0, 0.0f);
    read_frame(baseline);
    terrain_render_shutdown();
    terrain_render_shutdown();
    clear_frame();
    terrain_render_lights(renderer, &lighting, NULL, NULL, 0, 0.0f);
    read_frame(actual);
    CHECK(memcmp(baseline, actual, sizeof(actual)) == 0);
    terrain_render_shutdown();
    SDL_DestroyRenderer(renderer);
    renderer = SDL_CreateSoftwareRenderer(surface);
    CHECK(renderer != NULL);
    if (!renderer)
        return;
    clear_frame();
    terrain_render_lights(renderer, &lighting, NULL, NULL, 0, 0.0f);
    read_frame(actual);
    CHECK(memcmp(baseline, actual, sizeof(actual)) == 0);
}

int main(void)
{
    SDL_SetMainReady();
    CHECK(SDL_setenv("SDL_VIDEODRIVER", "dummy", 1) == 0);
    CHECK(SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "0") == SDL_TRUE);
    CHECK(SDL_Init(SDL_INIT_VIDEO) == 0);
    if (test_failures)
        return TEST_EXIT();
    surface = SDL_CreateRGBSurfaceWithFormat(0, VIEW_WIDTH, VIEW_HEIGHT, 32, SDL_PIXELFORMAT_ARGB8888);
    CHECK(surface != NULL);
    if (surface)
        renderer = SDL_CreateSoftwareRenderer(surface);
    CHECK(renderer != NULL);
    if (renderer) {
        RUN(night_ambient_and_warm_surface_light);
        RUN(daylight_without_glow_keeps_the_surface);
        RUN(camera_coordinates_match_a_translated_scene);
        RUN(viewport_protects_the_surrounding_ui_band);
        RUN(ground_shadows_render_and_hidden_bodies_do_not_cast);
        RUN(draw_and_texture_state_are_restored);
        RUN(shutdown_and_resource_recreation_keep_the_result);
    }
    terrain_render_shutdown();
    SDL_DestroyTexture(glow);
    SDL_DestroyRenderer(renderer);
    SDL_FreeSurface(surface);
    SDL_Quit();
    return TEST_EXIT();
}
