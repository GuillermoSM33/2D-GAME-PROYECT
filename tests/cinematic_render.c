/* Native-pixel motion: a fixed axle, clockwise rolling, camera easing, and a
 * sheriff who walks beyond the frame instead of stopping before the title. */
#define SDL_MAIN_HANDLED
#include <math.h>
#include <stdint.h>
#include <SDL.h>

#include "app/intro_render.h"
#include "app/story_render.h"
#include "engine/assets.h"
#include "engine/pixfont.h"
#include "game/scene.h"
#include "game/themes.h"
#include "test.h"

static SDL_Renderer *renderer;
static Platform platform;
static CharacterSkin sheriff;
static World title_world;
static Uint32 before[WINDOW_WIDTH * WINDOW_HEIGHT], after[WINDOW_WIDTH * WINDOW_HEIGHT];

static void wheel_snapshot(float travel, Uint32 *pixels)
{
    SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255);
    SDL_RenderClear(renderer);
    cine_wheel(renderer, 48, 48, 12.1f, 2, travel);
    SDL_Rect box = {0, 0, 96, 96};
    CHECK(SDL_RenderReadPixels(renderer, &box, SDL_PIXELFORMAT_ARGB8888, pixels, 96 * 4) == 0);
}

static void rolling_changes_the_surface_without_moving_the_axle_or_outline(void)
{
    wheel_snapshot(0, before);
    wheel_snapshot(12.1f * 2 * 1.57079632679f, after);
    int changed = 0, first_marks = 0, next_marks = 0;
    float first_x = 0, first_y = 0, next_x = 0, next_y = 0;
    for (int y = 0; y < 96; y++) {
        for (int x = 0; x < 96; x++) {
            int i = y * 96 + x;
            Uint32 a = before[i] & 0xffffff, b = after[i] & 0xffffff;
            CHECK((a != 0) == (b != 0)); /* The same circular silhouette. */
            changed += a != b;
            if (a == 0x94886b) { first_x += x - 49; first_y += y - 49; first_marks++; }
            if (b == 0x94886b) { next_x += x - 49; next_y += y - 49; next_marks++; }
        }
    }
    CHECK(changed > 150);
    CHECK(before[48 * 96 + 48] == after[48 * 96 + 48]);
    CHECK(first_marks > 0 && next_marks > 0);
    CHECK(first_x > fabsf(first_y));
    CHECK(next_y > fabsf(next_x)); /* The sidewall mark went right -> down. */
}

static void distance_controls_rotation_and_one_circumference_repeats(void)
{
    wheel_snapshot(0, before);
    wheel_snapshot(6.28318530718f * 12.1f * 2, after);
    CHECK(SDL_memcmp(before, after, 96 * 96 * sizeof(Uint32)) == 0);
    wheel_snapshot(-12.1f * 2 * 1.57079632679f, after);
    float marker_y = 0;
    int marks = 0;
    for (int y = 0; y < 96; y++)
        for (int x = 0; x < 96; x++)
            if ((after[y * 96 + x] & 0xffffff) == 0x94886b) {
                marker_y += y - 49;
                marks++;
            }
    CHECK(marks > 0 && marker_y < 0); /* Reverse travel reverses rolling. */
}

static void camera_eases_at_both_ends_and_keeps_its_framing(void)
{
    CHECK_NEAR(cine_pan(0, 6, 40), 0, .001f);
    CHECK_NEAR(cine_pan(6, 6, 40), 240, .001f);
    CHECK_NEAR(cine_pan(9, 6, 40), 240, .001f);
    float previous = 0;
    for (int k = 0; k <= 60; k++) {
        float p = cine_pan((float)k * .1f, 6, 40);
        CHECK(p >= previous);
        previous = p;
    }
    float start = cine_pan(.1f, 6, 40);
    float middle = cine_pan(3.1f, 6, 40) - cine_pan(3, 6, 40);
    float end = 240 - cine_pan(5.9f, 6, 40);
    CHECK(start < middle * .1f && end < middle * .1f);
}

static float title_start(void)
{
    float start = 0;
    for (int s = 0; s < INTRO_TITLE; s++)
        start += intro_scene_length((IntroScene)s);
    return start;
}

static float sheriff_center(float local)
{
    Intro intro;
    intro_start(&intro, INTRO_FULL);
    intro.time = title_start() + local;
    SDL_Rect screen = {0, 0, WINDOW_WIDTH, WINDOW_HEIGHT};
    intro_render(&platform, &intro, &title_world, NULL);
    CHECK(SDL_RenderReadPixels(renderer, &screen, SDL_PIXELFORMAT_ARGB8888, before, WINDOW_WIDTH * 4) == 0);
    intro_render(&platform, &intro, &title_world, &sheriff);
    CHECK(SDL_RenderReadPixels(renderer, &screen, SDL_PIXELFORMAT_ARGB8888, after, WINDOW_WIDTH * 4) == 0);
    float x = 0;
    int count = 0;
    for (int i = 0; i < WINDOW_WIDTH * WINDOW_HEIGHT; i++)
        if (before[i] != after[i]) { x += (float)(i % WINDOW_WIDTH); count++; }
    return count ? x / (float)count : -1;
}

static void sheriff_keeps_walking_until_she_leaves_the_picture(void)
{
    float a = sheriff_center(3.8f), b = sheriff_center(4.2f), c = sheriff_center(4.6f);
    CHECK(a > 0 && b > a + 25 && c > b + 20);
    CHECK(sheriff_center(5.7f) < 0);
}

static void the_lab_stays_visible_in_its_valley_through_the_pan(void)
{
    Story story;
    story_start(&story, tape_beat(4));
    float length = story_line_length(story.beat.lines[0]);
    const float moments[] = {.8f, length * .5f, length - .7f};
    SDL_Rect screen = {0, 0, WINDOW_WIDTH, WINDOW_HEIGHT};
    for (int k = 0; k < 3; k++) {
        story.time = moments[k];
        story_render(&platform, &story, NULL, 0, &sheriff);
        CHECK(SDL_RenderReadPixels(renderer, &screen, SDL_PIXELFORMAT_ARGB8888,
                                  after, WINDOW_WIDTH * 4) == 0);
        int windows = 0;
        /* The lab's lit ivory/green windows in the middle-distance valley,
         * below the hills and above the road. A foreground house must not
         * hide this landmark when choosing another camera origin. */
        for (int y = 300; y < 390; y++)
            for (int x = 380; x < 670; x++) {
                Uint32 pixel = after[y * WINDOW_WIDTH + x];
                int r = (pixel >> 16) & 255, g = (pixel >> 8) & 255, b = pixel & 255;
                windows += r > 95 && g > 110 && b > 90 && g > r + 6 && g > b + 5;
            }
        CHECK(windows >= 6);
    }
}

/* Optional actual-scene frames for an artist's motion review, at 24 fps. */
static void preview(const char *directory)
{
    SDL_Surface *shot = SDL_CreateRGBSurfaceWithFormat(0, WINDOW_WIDTH, WINDOW_HEIGHT, 32, SDL_PIXELFORMAT_ARGB8888);
    if (!shot) return;
    SDL_Rect screen = {0, 0, WINDOW_WIDTH, WINDOW_HEIGHT};
    for (int frame = 0; frame < 72; frame++) {
        for (int scene = 0; scene < 3; scene++) {
            float t = (float)frame / 24.0f;
            if (scene == 1) {
                Story story;
                story_start(&story, tape_beat(7));
                story.time = 1.0f + t;
                story_render(&platform, &story, NULL, 0, &sheriff);
            } else {
                Intro intro;
                intro_start(&intro, INTRO_FULL);
                intro.time = scene == 0 ? 44.0f + t : title_start() + 3.2f + t;
                intro_render(&platform, &intro, &title_world, &sheriff);
            }
            char name[512];
            snprintf(name, sizeof(name), "%s/%s_%03d.bmp", directory,
                     scene == 0 ? "ambulancia" : scene == 1 ? "convoy" : "sheriff", frame);
            CHECK(SDL_RenderReadPixels(renderer, &screen, SDL_PIXELFORMAT_ARGB8888, shot->pixels, shot->pitch) == 0);
            CHECK(SDL_SaveBMP(shot, name) == 0);
        }
    }
    SDL_FreeSurface(shot);
}

int main(int argc, char **argv)
{
    SDL_SetMainReady();
    SDL_setenv("SDL_VIDEODRIVER", "dummy", 1);
    CHECK(SDL_Init(SDL_INIT_VIDEO) == 0);
    SDL_Surface *surface = SDL_CreateRGBSurfaceWithFormat(0, VIEW_WIDTH, VIEW_HEIGHT, 32, SDL_PIXELFORMAT_ARGB8888);
    renderer = surface ? SDL_CreateSoftwareRenderer(surface) : NULL;
    CHECK(renderer != NULL);
    if (renderer) {
        platform.renderer = renderer;
        CHECK(assets_load(renderer));
        CHECK(pixfont_init());
        skin_load(&sheriff, renderer, &CHARACTERS[0]);
        world_init(&title_world, &THEME_ATARDECER);
        RUN(rolling_changes_the_surface_without_moving_the_axle_or_outline);
        RUN(distance_controls_rotation_and_one_circumference_repeats);
        RUN(camera_eases_at_both_ends_and_keeps_its_framing);
        RUN(sheriff_keeps_walking_until_she_leaves_the_picture);
        RUN(the_lab_stays_visible_in_its_valley_through_the_pan);
        if (argc == 2) preview(argv[1]);
        scene_shutdown();
        skin_free(&sheriff);
        assets_unload();
        SDL_DestroyRenderer(renderer);
    }
    SDL_FreeSurface(surface);
    SDL_Quit();
    return TEST_EXIT();
}
