#include <math.h>

#include "app/intro_render.h"
#include "app/stage_render.h"
#include "app/story_render.h"
#include "engine/assets.h"
#include "engine/pixfont.h"
#include "game/casefile_render.h"
#include "game/player_render.h"
#include "game/scene.h"
#include "game/themes.h"
#include "game/ui.h"

#define CAPTION_SCALE 3
#define CAPTION_Y 30
#define CAPTION_COLOR COLOR_STORY_TEXT
#define ART 3 /* Window px per art px in the cinematic images */
#define LAMP_W 14
#define LAMP_H 76

static World worlds[4];
static bool worlds_ready;

static float clamp01(float v)
{
    return v < 0.0f ? 0.0f : v > 1.0f ? 1.0f : v;
}

static float smooth(float edge0, float edge1, float t)
{
    float k = clamp01((t - edge0) / (edge1 - edge0));
    return k * k * (3.0f - 2.0f * k);
}

static void fill(SDL_Renderer *r, int x, int y, int w, int h, unsigned rgb, Uint8 alpha)
{
    SDL_SetRenderDrawBlendMode(r, SDL_BLENDMODE_BLEND);
    SDL_SetRenderDrawColor(r, (Uint8)(rgb >> 16), (Uint8)(rgb >> 8), (Uint8)rgb, alpha);
    SDL_Rect rect = {x, y, w, h};
    SDL_RenderFillRect(r, &rect);
}

static const ThemeDef *theme_of(StoryVisual visual)
{
    switch (visual) {
    case STORY_CEMENTERIO: return &THEME_CEMENTERIO;
    case STORY_NOCHE: return &THEME_NOCHE;
    case STORY_PUEBLO: return &THEME_PUEBLO_FANTASMA;
    default: return &THEME_ATARDECER;
    }
}

/* A stage's landscape, its camera drifted (view px from the middle of the road). */
static void begin_landscape(SDL_Renderer *r, StoryVisual visual, float drift)
{
    if (!worlds_ready) {
        for (int k = 0; k < 4; k++)
            world_init(&worlds[k], theme_of((StoryVisual)k));
        worlds_ready = true;
    }
    World *world = &worlds[visual];
    float camera_x = PLAYER_START_X - VIEW_WIDTH / 2.0f + drift;
    world_stream(world, camera_x);
    stage_begin_view(r, world->theme);
    scene_draw(r, world, camera_x, platform_time());
}

static void draw_coffin(SDL_Renderer *r, float x, int frame, Uint8 alpha)
{
    SDL_Texture *tex = assets_texture("sprites/terrain/coffin");
    if (tex == NULL)
        return;
    SDL_Rect src = {frame * 32, 0, 32, 68};
    SDL_Rect dst = {(int)lroundf(x) - 16 * SPRITE_SCALE, BASELINE - 68 * SPRITE_SCALE, 32 * SPRITE_SCALE,
                    68 * SPRITE_SCALE};
    SDL_SetTextureAlphaMod(tex, alpha);
    SDL_RenderCopy(r, tex, &src, &dst);
    SDL_SetTextureAlphaMod(tex, 255);
}

/* An oil lamp on its post; lit, it throws a warm glow around its head. */
static void draw_lamp(SDL_Renderer *r, float x, bool lit)
{
    SDL_Texture *tex = assets_texture("sprites/terrain/lamp");
    if (tex == NULL)
        return;
    SDL_Rect src = {0, 0, LAMP_W, LAMP_H};
    SDL_Rect dst = {(int)lroundf(x) - LAMP_W * SPRITE_SCALE / 2, BASELINE - LAMP_H * SPRITE_SCALE,
                    LAMP_W * SPRITE_SCALE, LAMP_H * SPRITE_SCALE};
    if (!lit)
        SDL_SetTextureColorMod(tex, 90, 90, 110);
    SDL_RenderCopy(r, tex, &src, &dst);
    SDL_SetTextureColorMod(tex, 255, 255, 255);
    SDL_Texture *glow = assets_texture("sprites/effects/glow");
    if (lit && glow) {
        int size = 32 * SPRITE_SCALE * 2;
        SDL_Rect g = {(int)lroundf(x) - size / 2, dst.y + 10 * SPRITE_SCALE - size / 2, size, size};
        SDL_SetTextureBlendMode(glow, SDL_BLENDMODE_ADD);
        SDL_RenderCopy(r, glow, NULL, &g);
    }
}

/* A tumbleweed bounding along: a tangle of dry twigs, in whole art px. */
static void draw_tumbleweed(SDL_Renderer *r, float x, float t)
{
    const int px = SPRITE_SCALE;
    int bounce = (int)lroundf(fabsf(sinf(t * 5.0f)) * 18.0f);
    int cx = (int)lroundf(x) / px * px, cy = BASELINE - 9 * px - bounce / px * px;
    float spin = t * 7.0f;
    for (int k = 0; k < 70; k++) {
        float a = spin + (float)k * 0.61f, d = (float)(k % 8 + 2);
        int tx = cx + (int)lroundf(cosf(a) * d) * px, ty = cy + (int)lroundf(sinf(a) * d) * px;
        fill(r, tx, ty, px, px, k % 3 ? 0x7a5a32 : 0x9c7a46, 255);
    }
}

static void draw_sheriff(SDL_Renderer *r, const CharacterSkin *skin, float view_x)
{
    if (skin == NULL)
        return;
    static Player sheriff;
    player_init(&sheriff);
    float camera_x = PLAYER_START_X - VIEW_WIDTH / 2.0f;
    sheriff.x = camera_x + view_x;
    player_render(r, &sheriff, skin, skin->character->weapons, 0, camera_x);
}

/* ---- The tapes' shots: scene (1-4), line, seconds into the line -------------- */

static const float GRAVES[] = {240.0f, 430.0f, 620.0f, 810.0f, 1000.0f};

static void graves(SDL_Renderer *r, float open)
{
    for (int k = 0; k < 5; k++)
        cine_tombstone(r, GRAVES[k] + 88.0f, k % 3);
    for (int k = 0; k < 5; k++)
        cine_mound(r, GRAVES[k], open);
}

static void shot_panteon(SDL_Renderer *r, int line, float t)
{
    if (line == 0) { /* The hospital full: coffins lined up in the street, one after another */
        begin_landscape(r, STORY_PUEBLO, t * 10.0f);
        for (int k = 0; k < 5; k++) {
            float a = smooth(0.6f + (float)k * 0.5f, 1.0f + (float)k * 0.5f, t);
            if (a > 0.0f)
                draw_coffin(r, 330.0f + (float)k * 140.0f, 0, (Uint8)lroundf(a * 255.0f));
        }
        stage_end_view(r);
    } else if (line == 1) { /* Fresh graves in the old graveyard, the crows already there */
        begin_landscape(r, STORY_CEMENTERIO, t * 8.0f);
        graves(r, 0.0f);
        for (int k = 0; k < 3; k++)
            cine_crow(r, (int)(t * 3.0f + (float)k) % 2, 1080.0f + (float)k * 50.0f - t * 8.0f, 0.0f, 1);
        stage_end_view(r);
    } else { /* That night, one of them stirs; something starts to come up */
        begin_landscape(r, STORY_CEMENTERIO, 40.0f);
        float rise = smooth(1.6f, 4.0f, t);
        if (t > 1.6f) /* Head and shoulders out of the earth, no more yet */
            cine_zombie(r, ZOMBIE_KIND_CIVIL_MALE_2, ZOMBIE_ANIM_IDLE, (int)(t * 6.0f), GRAVES[2],
                        (int)lroundf(68.0f - rise * 44.0f));
        graves(r, 0.0f);
        cine_mound(r, GRAVES[2], smooth(1.0f, 1.8f, t));
        cine_clods(r, GRAVES[2], 1.0f, t, 11u);
        stage_end_view(r);
        ui_dim(r, 90);
        float flash = 1.0f - fabsf(t - 0.6f) / 0.15f;
        if (flash > 0.0f)
            fill(r, 0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, 0xe8f0ff, (Uint8)lroundf(170.0f * flash));
    }
}

static void shot_toque(SDL_Renderer *r, int line, float t, const CharacterSkin *sheriff)
{
    static const float LAMPS[] = {260.0f, 620.0f, 980.0f};
    if (line == 0) { /* Out of the opened graves, walking toward the town */
        begin_landscape(r, STORY_CEMENTERIO, t * 12.0f);
        graves(r, 1.0f);
        static const ZombieKind WHO[] = {ZOMBIE_KIND_CIVIL_MALE_3, ZOMBIE_KIND_CIVIL_FEMALE_4, ZOMBIE_KIND_CIVIL_MALE_1};
        for (int k = 0; k < 3; k++) {
            const AnimationDef *walk = zombie_animation(WHO[k], ZOMBIE_ANIM_WALK);
            cine_zombie(r, WHO[k], ZOMBIE_ANIM_WALK, (int)(t * walk->fps * 0.5f) + k * 3,
                        200.0f + (float)k * 260.0f + t * 36.0f, 0);
        }
        stage_end_view(r);
        ui_dim(r, 70);
    } else { /* The town at night under its lamps, the sheriff out in it; then the lamps die */
        begin_landscape(r, STORY_NOCHE, 0.0f);
        for (int k = 0; k < 3; k++)
            draw_lamp(r, LAMPS[k], line == 1 || t < 1.0f + (float)k * 0.9f);
        if (line == 1) {
            draw_sheriff(r, sheriff, 470.0f);
        } else {
            for (int k = 0; k < 2; k++) { /* Shapes coming out of the dark */
                ZombieKind who = k ? ZOMBIE_KIND_CIVIL_MALE_4 : ZOMBIE_KIND_CIVIL_FEMALE_2;
                const AnimationDef *walk = zombie_animation(who, ZOMBIE_ANIM_WALK);
                cine_zombie(r, who, ZOMBIE_ANIM_WALK, (int)(t * walk->fps * 0.5f) + k * 4,
                            -60.0f + (float)k * 180.0f + t * 45.0f, 0);
            }
        }
        stage_end_view(r);
        if (line == 2)
            ui_dim(r, (Uint8)lroundf(40.0f + 130.0f * smooth(0.8f, 3.6f, t)));
    }
}

static void shot_pueblo(SDL_Renderer *r, int line, float t)
{
    begin_landscape(r, STORY_PUEBLO, t * (line == 0 ? 20.0f : 8.0f));
    if (line == 0) { /* Nobody in the street: a tumbleweed, the crows leaving */
        draw_tumbleweed(r, -80.0f + t * 220.0f, t);
        for (int k = 0; k < 3; k++) {
            float f = t - 1.6f - (float)k * 0.2f;
            if (f < 0.0f)
                cine_crow(r, (int)(t * 3.0f + (float)k) % 2, 820.0f + (float)k * 50.0f, 0.0f, 1);
            else
                cine_crow(r, 2 + (int)(f * 12.0f) % 4, 820.0f + (float)k * 50.0f + f * 240.0f, f * 170.0f, 1);
        }
    } else { /* The ones still in its streets, swaying where they stand */
        static const ZombieKind WHO[] = {ZOMBIE_KIND_CIVIL_MALE_2, ZOMBIE_KIND_SHERIFF, ZOMBIE_KIND_CIVIL_FEMALE_1,
                                         ZOMBIE_KIND_PRIEST};
        for (int k = 0; k < 4; k++)
            cine_zombie(r, WHO[k], ZOMBIE_ANIM_IDLE, (int)(t * 3.0f) + k, 220.0f + (float)k * 270.0f, 0);
    }
    stage_end_view(r);
    ui_dim(r, 40);
}

static void shot_lab(SDL_Renderer *r, int line, float t)
{
    if (line == 0) { /* The desert road at night; far off on the horizon, the lab */
        if (!worlds_ready)
            begin_landscape(r, STORY_NOCHE, 0.0f), stage_end_view(r);
        World *world = &worlds[STORY_NOCHE];
        float drift = t * 40.0f, camera_x = PLAYER_START_X - VIEW_WIDTH / 2.0f + drift;
        world_stream(world, camera_x);
        stage_begin_view(r, world->theme);
        scene_draw_layers(r, world, camera_x, 0, 1); /* Sky and the far mesas */
        /* The lab on the mesas, as far as they are (their parallax), its base
         * behind the far hills: a dark block, windows lit, a red light blinking */
        const int px = SPRITE_SCALE;
        /* Moved exactly as its layer is (scene.c draw_layer: whole view px, not
         * art px), so it glides with the mesas instead of stepping across them */
        float parallax = BACKGROUND_LAYERS[1].parallax, start = PLAYER_START_X - VIEW_WIDTH / 2.0f;
        int bx = 900 + (int)lroundf(start * parallax) - (int)lroundf(camera_x * parallax), base = 62 * px;
        fill(r, bx, base - 9 * px, 34 * px, 9 * px, 0x161a26, 255);
        fill(r, bx + 24 * px, base - 13 * px, 6 * px, 4 * px, 0x161a26, 255);
        for (int row = 0; row < 2; row++)
            for (int k = 0; k < 8; k++)
                if ((k + row) % 3 != 1)
                    fill(r, bx + 2 * px + k * 4 * px, base - 7 * px + row * 3 * px, 2 * px, px, 0xc8d8b8, 150);
        if (fmodf(t, 1.0f) < 0.5f)
            fill(r, bx + 26 * px, base - 15 * px, px, px, 0xe8402a, 255);
        scene_draw_layers(r, world, camera_x, 2, BACKGROUND_LAYER_COUNT - 2); /* The hills in front of it */
        scene_draw_near(r, world, camera_x, platform_time());
        stage_end_view(r);
    } else if (line == 1) { /* Its corridor, under the emergency lights */
        SDL_Texture *tex = assets_texture("cinematics/lab/corridor");
        if (tex) {
            int pan = 40 + (int)lroundf(smooth(0.0f, 6.0f, t) * 110.0f);
            SDL_Rect src = {pan, 0, 320, 180};
            SDL_Rect dst = {0, 0, 320 * ART, 180 * ART};
            SDL_RenderCopy(r, tex, &src, &dst);
        }
        ui_dim(r, 90);
        fill(r, 0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, 0xff2010, (Uint8)lroundf(28.0f * (0.5f + 0.5f * sinf(t * 4.0f))));
    } else { /* The monitors still running, and someone at them */
        SDL_Texture *tex = assets_texture("cinematics/lab/monitors");
        if (tex) {
            int frame = (int)(t * 6.0f) % 6;
            SDL_Rect src = {frame * 320, 0, 320, 180};
            SDL_Rect dst = {0, 0, 320 * ART, 180 * ART};
            SDL_RenderCopy(r, tex, &src, &dst);
        }
        SDL_Texture *who = assets_texture("sprites/mercenary/walk");
        if (who) { /* A figure at the desk, breathing */
            int frame = 8 + (int)(t * 2.2f) % 4;
            SDL_Rect src = {frame * 81, 0, 81, 80};
            SDL_Rect dst = {360, WINDOW_HEIGHT - 66 * ART, 81 * ART, 80 * ART}; /* Standing at the desk */
            SDL_RenderCopy(r, who, &src, &dst);
        }
        ui_dim(r, 60);
    }
}

void story_render(Platform *platform, const Story *story, const CaseFile *file, float time,
                  const CharacterSkin *sheriff)
{
    SDL_Renderer *r = platform->renderer;
    (void)file;
    (void)time;
    SDL_SetRenderDrawColor(r, 0, 0, 0, 255);
    SDL_RenderClear(r);
    if (story->beat.count <= 0)
        return;
    int line = story->line < story->beat.count ? story->line : story->beat.count - 1;
    float t = story->time;
    switch (story->beat.scene) {
    case 1: shot_panteon(r, line, t); break;
    case 2: shot_toque(r, line, t, sheriff); break;
    case 3: shot_pueblo(r, line, t); break;
    default: shot_lab(r, line, t); break;
    }
    /* Each shot fades in from black and out to it, between the lines */
    float len = story_line_length(story->beat.lines[line]);
    float black = fmaxf(1.0f - t / 0.5f, (t - (len - 0.5f)) / 0.5f);
    if (black > 0.0f)
        fill(r, 0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, 0x000000, (Uint8)lroundf(clamp01(black) * 255.0f));
    char buf[160];
    float alpha;
    if (story_caption(story, buf, sizeof(buf), &alpha)) {
        /* Wrapped on the whole line, so the words don't jump as it types */
        char whole[4][96], typed[4][96];
        int lines = casefile_wrap(story->beat.lines[story->line], CAPTION_SCALE, WINDOW_WIDTH - 100, whole, 4);
        int left = (int)SDL_strlen(buf);
        int y = CAPTION_Y + (lines == 1 ? (pixfont_height(CAPTION_SCALE) + 2) / 2 : 0);
        bool emphasis = false;
        for (int k = 0; k < lines && left > 0; k++) {
            int len_k = (int)SDL_strlen(whole[k]);
            int take = left < len_k ? left : len_k;
            SDL_memcpy(typed[k], whole[k], (size_t)take);
            typed[k][take] = '\0';
            left -= len_k + 1; /* And the space the wrap took */
            int x = (WINDOW_WIDTH - pixfont_width(whole[k], CAPTION_SCALE)) / 2;
            pixfont_draw_rich(r, typed[k], x, y, CAPTION_SCALE, CAPTION_COLOR, COLOR_STORY_EMPHASIS, ANCHOR_NW,
                              (Uint8)lroundf(alpha * 255.0f), true, &emphasis);
            y += pixfont_height(CAPTION_SCALE) + 2;
        }
    }
    pixfont_draw(r, "ENTER: SIGUIENTE    ESC: SALTAR", WINDOW_WIDTH / 2, WINDOW_HEIGHT - 26, 2, 0xb0aaa0,
                 ANCHOR_N, 120);
    SDL_SetRenderDrawBlendMode(r, SDL_BLENDMODE_NONE);
}
