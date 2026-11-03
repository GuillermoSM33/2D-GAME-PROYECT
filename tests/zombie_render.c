/* Offscreen renderer regression: an unfinished new skin must not make the
 * original riot enemy, its elite or a runner disappear. No assets are read.
 * Link the core plus zombie_render/health_bar/hang_render and SDL, replacing
 * only the texture lookup and platform color boundary below. */
#define SDL_MAIN_HANDLED
#include <math.h>
#include <stdlib.h>
#include <string.h>

#include <SDL.h>

#include "config.h"
#include "game/zombie.h"
#include "game/zombie_render.h"
#include "test.h"

static SDL_Surface *canvas;
static SDL_Renderer *renderer;
static SDL_Texture *legacy[4], *owned;
static bool owned_available;
static Uint32 pixels[VIEW_WIDTH * VIEW_HEIGHT];

static const char *const legacy_names[] = {
    "sprites/zombies/riot/walk", "sprites/zombies/riot/attack", "sprites/zombies/riot/hurt", "sprites/zombies/riot/death"
};

SDL_Texture *assets_texture(const char *name)
{
    if (!name)
        return NULL;
    for (int i = 0; i < 4; i++)
        if (strcmp(name, legacy_names[i]) == 0)
            return legacy[i];
    if (owned_available && strcmp(name, "sprites/zombies/soldier/idle") == 0)
        return owned;
    return NULL;
}

void platform_set_color(SDL_Renderer *r, unsigned rgb)
{
    SDL_SetRenderDrawColor(r, (Uint8)(rgb >> 16), (Uint8)(rgb >> 8), (Uint8)rgb, 255);
}

static SDL_Texture *fixture(int frames, bool custom)
{
    SDL_Surface *strip = SDL_CreateRGBSurfaceWithFormat(0, frames * 72, 72, 32,
                                                       SDL_PIXELFORMAT_ARGB8888);
    CHECK(strip != NULL);
    if (!strip)
        return NULL;
    SDL_FillRect(strip, NULL, SDL_MapRGBA(strip->format, 0, 0, 0, 0));
    for (int frame = 0; frame < frames; frame++) {
        SDL_Rect body = {frame * 72 + 18, 10, 28, 58};
        Uint32 color = SDL_MapRGBA(strip->format, custom ? 40 : 40 + frame * 20,
                                   custom ? 220 : 80, custom ? 80 : 232, 255);
        CHECK(SDL_FillRect(strip, &body, color) == 0);
    }
    SDL_Texture *texture = SDL_CreateTextureFromSurface(renderer, strip);
    CHECK(texture != NULL);
    if (texture)
        CHECK(SDL_SetTextureBlendMode(texture, SDL_BLENDMODE_BLEND) == 0);
    SDL_FreeSurface(strip);
    return texture;
}

static void clear(void)
{
    CHECK(SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE) == 0);
    CHECK(SDL_SetRenderDrawColor(renderer, 8, 17, 26, 255) == 0);
    CHECK(SDL_RenderClear(renderer) == 0);
}

static int render_body_pixels(const Zombie *zombie)
{
    int frame = zombie->anim.frame;
    SDL_Texture *texture = zombie_animation_texture(zombie->anim.def, &frame);
    bool custom = texture == owned;
    int source_r = custom ? 40 : 40 + frame * 20;
    int source_g = custom ? 220 : 80;
    int source_b = custom ? 80 : 232;
    unsigned tint = zombie->stats ? zombie->stats->tint : 0xffffff;
    int expected_r = source_r * (int)((tint >> 16) & 255) / 255;
    int expected_g = source_g * (int)((tint >> 8) & 255) / 255;
    int expected_b = source_b * (int)(tint & 255) / 255;
    clear();
    zombie_render(renderer, zombie, 0.0f);
    CHECK(SDL_RenderReadPixels(renderer, NULL, SDL_PIXELFORMAT_ARGB8888, pixels,
                               VIEW_WIDTH * (int)sizeof(Uint32)) == 0);
    int body = 0;
    for (int i = 0; i < VIEW_WIDTH * VIEW_HEIGHT; i++) {
        Uint8 r, g, b, a;
        SDL_GetRGBA(pixels[i], canvas->format, &r, &g, &b, &a);
        /* Ropes and health bars have different colors; they cannot make an
         * invisible body accidentally pass this check. Allow SDL rounding. */
        body += abs((int)r - expected_r) <= 1 && abs((int)g - expected_g) <= 1 &&
                abs((int)b - expected_b) <= 1;
    }
    return body;
}

static void requested_frame_resolves_to_the_correct_original_strip(void)
{
    const ZombieAnimation actions[] = {ZOMBIE_ANIM_WALK, ZOMBIE_ANIM_IDLE, ZOMBIE_ANIM_RUN,
                                       ZOMBIE_ANIM_ATTACK, ZOMBIE_ANIM_HURT,
                                       ZOMBIE_ANIM_DEATH, ZOMBIE_ANIM_CAUGHT};
    const int expected[] = {0, 0, 0, 1, 2, 3, 2};
    for (int kind = 0; kind < ZOMBIE_KIND_COUNT; kind++)
        for (int action = 0; action < 7; action++) {
            int frame = 0;
            CHECK(zombie_animation_texture(zombie_animation((ZombieKind)kind, actions[action]), &frame)
                  == legacy[expected[action]]);
        }
    int caught = 3;
    CHECK(zombie_animation_texture(zombie_animation(ZOMBIE_KIND_RIOT, ZOMBIE_ANIM_CAUGHT), &caught)
          == legacy[2]);
    CHECK(caught == 2); /* The fallback hurt strip has only frames 0, 1, 2. */
    int negative = -9;
    CHECK(zombie_animation_texture(zombie_animation(ZOMBIE_KIND_ELITE, ZOMBIE_ANIM_RUN), &negative)
          == legacy[0]);
    CHECK(negative == 0);
    CHECK(zombie_animation_texture(NULL, &caught) == NULL);
    CHECK(zombie_animation_texture(zombie_walk_animation(), NULL) == NULL);
}

static void original_families_and_runners_remain_visible_in_every_state(void)
{
    const ZombieKind kinds[] = {ZOMBIE_KIND_RIOT, ZOMBIE_KIND_ELITE};
    for (int kind = 0; kind < 2; kind++)
        for (int fast = 0; fast < 2; fast++) {
            Zombie z;
            zombie_spawn(&z, zombie_stats(kinds[kind], fast != 0), 520.0f);
            zombie_update(&z, 1000.0f, true, .1f);
            CHECK(render_body_pixels(&z) > 100); /* Walk or runner sheet. */
            z.awake = false;
            zombie_update(&z, 1000.0f, true, .5f);
            CHECK(render_body_pixels(&z) > 100); /* Missing idle sheet. */
            z.awake = true;
            zombie_update(&z, z.x, true, FIXED_DT);
            zombie_update(&z, z.x, true, .2f);
            CHECK(z.state == ZOMBIE_ATTACK && render_body_pixels(&z) > 100);
            zombie_hit(&z, 1.0f);
            CHECK(z.state == ZOMBIE_HURT && render_body_pixels(&z) > 100);
            for (int trap = CATCH_NONE; trap <= CATCH_SNARE; trap++) {
                z.caught = 2.0f;
                z.catch_kind = (CatchKind)trap;
                z.catch_time = CATCH_RISE_TIME + .1f;
                z.catch_anchor_x = z.x;
                z.catch_anchor_y = BASELINE - 220.0f;
                zombie_update(&z, z.x + 100.0f, true, .1f);
                animation_set_frame(&z.anim, 3); /* Exercises the real 4-to-3 fallback clamp. */
                CHECK(render_body_pixels(&z) > 100);
            }
            zombie_hit(&z, 1000000.0f);
            for (int i = 0; i < 60; i++)
                zombie_update(&z, 1000.0f, false, FIXED_DT);
            CHECK(z.anim.frame == 7 && render_body_pixels(&z) > 100);
        }
}

static void an_available_new_sheet_has_priority_over_legacy_fallback(void)
{
    owned_available = true;
    int frame = 3;
    CHECK(zombie_animation_texture(zombie_animation(ZOMBIE_KIND_SOLDIER, ZOMBIE_ANIM_IDLE), &frame) == owned);
    CHECK(frame == 3);
    Zombie soldier;
    zombie_spawn(&soldier, zombie_stats(ZOMBIE_KIND_SOLDIER, false), 520.0f);
    soldier.awake = false;
    zombie_update(&soldier, 1000.0f, true, 1.0f);
    CHECK(soldier.anim.frame == 3 && render_body_pixels(&soldier) > 100);
    owned_available = false;
}

static void hidden_and_faded_bodies_draw_no_pixels(void)
{
    Zombie z;
    zombie_spawn(&z, &ZOMBIE_RIOT, 520.0f);
    z.hidden = true;
    CHECK(render_body_pixels(&z) == 0);
    z.hidden = false;
    zombie_hit(&z, 1000000.0f);
    z.dead_time = 100.0f;
    CHECK(zombie_opacity(&z) == 0.0f && render_body_pixels(&z) == 0);
}

int main(void)
{
    printf("zombie_render (offscreen legacy-art regression)\n");
    SDL_SetMainReady();
    CHECK(SDL_setenv("SDL_VIDEODRIVER", "dummy", 1) == 0);
    CHECK(SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "0") == SDL_TRUE);
    CHECK(SDL_Init(SDL_INIT_VIDEO) == 0);
    canvas = SDL_CreateRGBSurfaceWithFormat(0, VIEW_WIDTH, VIEW_HEIGHT, 32, SDL_PIXELFORMAT_ARGB8888);
    CHECK(canvas != NULL);
    if (canvas)
        renderer = SDL_CreateSoftwareRenderer(canvas);
    CHECK(renderer != NULL);
    if (renderer) {
        const int frames[] = {8, 6, 3, 8};
        for (int i = 0; i < 4; i++)
            legacy[i] = fixture(frames[i], false);
        owned = fixture(4, true);
        if (!test_failures) {
            RUN(requested_frame_resolves_to_the_correct_original_strip);
            RUN(original_families_and_runners_remain_visible_in_every_state);
            RUN(an_available_new_sheet_has_priority_over_legacy_fallback);
            RUN(hidden_and_faded_bodies_draw_no_pixels);
        }
    }
    for (int i = 0; i < 4; i++)
        SDL_DestroyTexture(legacy[i]);
    SDL_DestroyTexture(owned);
    SDL_DestroyRenderer(renderer);
    SDL_FreeSurface(canvas);
    SDL_Quit();
    return TEST_EXIT();
}
