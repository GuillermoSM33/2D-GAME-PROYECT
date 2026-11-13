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
/* Art rows over the ground line where things far off stand, between the far
 * hills and the near ones (tools/make_landscape.py draws that valley). */
#define LAB_VALLEY_ROWS 58
#define FAR_CITY_ROWS 66

static World worlds[STORY_VISUALS];
static bool worlds_ready;
static float shot_origin, shot_length, shot_drift;

/* Different stretches of road give each shot its own architecture and props.
 * Related reverse shots stay near one another rather than revisiting the
 * exact gameplay spawn in every tape. Values are world/view pixels. */
static const float SHOT_ORIGINS[11][STORY_MAX_LINES] = {
    [1] = {6800, 2100, 2700}, [2] = {4700, 9200, 9800},
    [3] = {12800, 15300}, [4] = {0, 0, 0}, /* Keep the lab in its open valley. */
    [5] = {18800, 20200, 18960, 19360}, [6] = {6400, 7000, 7600},
    [7] = {13200, 14300}, [8] = {22400, 22900},
    [9] = {30200, 31800}, [10] = {39000, 39500, 39700},
};

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
    case STORY_AFUERAS: return &THEME_AFUERAS;
    case STORY_CENTRO: return &THEME_CENTRO;
    case STORY_VIAS: return &THEME_VIAS;
    case STORY_CIUDAD_NOCHE: return &THEME_CIUDAD_NOCHE;
    case STORY_BASE: return &THEME_BASE_MILITAR;
    default: return &THEME_ATARDECER;
    }
}

/* A stage's landscape, its camera drifted (view px from the middle of the road). */
static void begin_landscape(SDL_Renderer *r, StoryVisual visual, float drift)
{
    if (!worlds_ready) {
        for (int k = 0; k < STORY_VISUALS; k++)
            world_init(&worlds[k], theme_of((StoryVisual)k));
        worlds_ready = true;
    }
    World *world = &worlds[visual];
    shot_drift = drift;
    float camera_x = PLAYER_START_X - VIEW_WIDTH / 2.0f + shot_origin + drift;
    world_stream(world, camera_x);
    stage_begin_view(r, world->theme);
    scene_draw(r, world, camera_x, platform_time());
}

static void draw_coffin(SDL_Renderer *r, float x, int frame, Uint8 alpha)
{
    x -= shot_drift;
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
    x -= shot_drift;
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
    float base = PLAYER_START_X - VIEW_WIDTH / 2.0f + shot_origin;
    float camera_x = base + shot_drift;
    sheriff.x = base + view_x;
    player_render(r, &sheriff, skin, skin->character->weapons, 0, camera_x);
}

/* ---- The tapes' shots: scene (1-4), line, seconds into the line -------------- */

static const float GRAVES[] = {CINE_X(240.0f), CINE_X(430.0f), CINE_X(620.0f), CINE_X(810.0f), CINE_X(1000.0f)};

static void graves(SDL_Renderer *r, float open)
{
    for (int k = 0; k < 5; k++)
        cine_tombstone(r, GRAVES[k] + TOMBSTONE_GAP - shot_drift, k % 3);
    for (int k = 0; k < 5; k++)
        cine_mound(r, GRAVES[k] - shot_drift, open);
}

static void shot_panteon(SDL_Renderer *r, int line, float t)
{
    if (line == 0) { /* The hospital full: coffins lined up in the street, one after another */
        begin_landscape(r, STORY_PUEBLO, cine_pan(t, shot_length, 10.0f));
        for (int k = 0; k < 5; k++) {
            float a = smooth(0.6f + (float)k * 0.5f, 1.0f + (float)k * 0.5f, t);
            if (a > 0.0f)
                draw_coffin(r, CINE_X(330.0f + (float)k * 140.0f), 0, (Uint8)lroundf(a * 255.0f));
        }
        stage_end_view(r);
    } else if (line == 1) { /* Fresh graves in the old graveyard, the crows already there */
        begin_landscape(r, STORY_CEMENTERIO, cine_pan(t, shot_length, 8.0f));
        graves(r, 0.0f);
        for (int k = 0; k < 3; k++)
            cine_crow(r, (int)(t * 3.0f + (float)k) % 2, CINE_X(1080.0f) + (float)k * 50.0f - shot_drift, 0.0f, 1);
        stage_end_view(r);
    } else { /* That night, one of them stirs; something starts to come up */
        begin_landscape(r, STORY_CEMENTERIO, 40.0f);
        float rise = smooth(1.6f, 4.0f, t);
        if (t > 1.6f) /* Head and shoulders out of the earth, no more yet */
            cine_zombie(r, ZOMBIE_KIND_CIVIL_MALE_2, ZOMBIE_ANIM_IDLE, (int)(t * 6.0f), GRAVES[2] - shot_drift,
                        (int)lroundf(68.0f - rise * 44.0f));
        graves(r, 0.0f);
        cine_mound(r, GRAVES[2] - shot_drift, smooth(1.0f, 1.8f, t));
        cine_clods(r, GRAVES[2] - shot_drift, 1.0f, t, 11u);
        stage_end_view(r);
        ui_dim(r, 90);
        float flash = 1.0f - fabsf(t - 0.6f) / 0.15f;
        if (flash > 0.0f)
            fill(r, 0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, 0xe8f0ff, (Uint8)lroundf(170.0f * flash));
    }
}

static void shot_toque(SDL_Renderer *r, int line, float t, const CharacterSkin *sheriff)
{
    static const float LAMPS[] = {CINE_X(260.0f), CINE_X(620.0f), CINE_X(980.0f)};
    if (line == 0) { /* Out of the opened graves, walking toward the town */
        begin_landscape(r, STORY_CEMENTERIO, cine_pan(t, shot_length, 12.0f));
        graves(r, 1.0f);
        static const ZombieKind WHO[] = {ZOMBIE_KIND_CIVIL_MALE_3, ZOMBIE_KIND_CIVIL_FEMALE_4, ZOMBIE_KIND_CIVIL_MALE_1};
        for (int k = 0; k < 3; k++) {
            const AnimationDef *walk = zombie_animation(WHO[k], ZOMBIE_ANIM_WALK);
            cine_zombie(r, WHO[k], ZOMBIE_ANIM_WALK, (int)(t * walk->fps * 0.5f) + k * 3,
                        CINE_X(200.0f + (float)k * 260.0f) + t * 36.0f, 0);
        }
        stage_end_view(r);
        ui_dim(r, 70);
    } else { /* The town at night under its lamps, the sheriff out in it; then the lamps die */
        begin_landscape(r, STORY_NOCHE, 0.0f);
        for (int k = 0; k < 3; k++)
            draw_lamp(r, LAMPS[k], line == 1 || t < 1.0f + (float)k * 0.9f);
        if (line == 1) {
            draw_sheriff(r, sheriff, CINE_X(470.0f));
        } else {
            for (int k = 0; k < 2; k++) { /* Shapes coming out of the dark */
                ZombieKind who = k ? ZOMBIE_KIND_CIVIL_MALE_4 : ZOMBIE_KIND_CIVIL_FEMALE_2;
                const AnimationDef *walk = zombie_animation(who, ZOMBIE_ANIM_WALK);
                cine_zombie(r, who, ZOMBIE_ANIM_WALK, (int)(t * walk->fps * 0.5f) + k * 4,
                            CINE_X(-60.0f + (float)k * 180.0f) + t * 45.0f, 0);
            }
        }
        stage_end_view(r);
        if (line == 2)
            ui_dim(r, (Uint8)lroundf(40.0f + 130.0f * smooth(0.8f, 3.6f, t)));
    }
}

static void shot_pueblo(SDL_Renderer *r, int line, float t)
{
    begin_landscape(r, STORY_PUEBLO, cine_pan(t, shot_length, line == 0 ? 20.0f : 8.0f));
    if (line == 0) { /* Nobody in the street: a tumbleweed, the crows leaving */
        draw_tumbleweed(r, CINE_X(-80.0f + t * 220.0f), t);
        for (int k = 0; k < 3; k++) {
            float f = t - 1.6f - (float)k * 0.2f;
            if (f < 0.0f)
                cine_crow(r, (int)(t * 3.0f + (float)k) % 2, CINE_X(820.0f) + (float)k * 50.0f, 0.0f, 1);
            else
                cine_crow(r, 2 + (int)(f * 12.0f) % 4, CINE_X(820.0f) + (float)k * 50.0f + f * 240.0f, f * 170.0f, 1);
        }
    } else { /* The ones still in its streets, swaying where they stand */
        static const ZombieKind WHO[] = {ZOMBIE_KIND_CIVIL_MALE_2, ZOMBIE_KIND_SHERIFF, ZOMBIE_KIND_CIVIL_FEMALE_1,
                                         ZOMBIE_KIND_PRIEST};
        for (int k = 0; k < 4; k++)
            cine_zombie(r, WHO[k], ZOMBIE_ANIM_IDLE, (int)(t * 3.0f) + k, CINE_X(220.0f + (float)k * 270.0f), 0);
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
        float drift = cine_pan(t, shot_length, 40.0f);
        float camera_x = PLAYER_START_X - VIEW_WIDTH / 2.0f + shot_origin + drift;
        world_stream(world, camera_x);
        stage_begin_view(r, world->theme);
        scene_draw_layers(r, world, camera_x, 0, 2); /* Mountains behind the valley */
        /* The lab stands on a flat valley floor below the mountain crests,
         * between the distant hills and the nearer ridge. */
        const int px = SPRITE_SCALE;
        /* Its depth lies between hills_far (.35) and hills_near (.6). Match
         * draw_layer's whole-view-pixel camera rounding throughout the pan. */
        float parallax = 0.45f, start = PLAYER_START_X - VIEW_WIDTH / 2.0f + shot_origin;
        int bx = (int)CINE_X(700.0f) + (int)lroundf(start * parallax) - (int)lroundf(camera_x * parallax);
        int base = (GROUND_ROW - LAB_VALLEY_ROWS) * px;
        fill(r, bx - 6 * px, base, 46 * px, 2 * px, 0x262c3a, 255); /* Low concrete apron */
        fill(r, bx - 4 * px, base, 42 * px, px, 0x303646, 255);
        fill(r, bx - px, base + px, 36 * px, px, 0x10141e, 255); /* Contact shadow */
        fill(r, bx, base - 9 * px, 34 * px, 9 * px, 0x161a26, 255);
        fill(r, bx + 24 * px, base - 13 * px, 6 * px, 4 * px, 0x161a26, 255);
        for (int row = 0; row < 2; row++)
            for (int k = 0; k < 8; k++)
                if ((k + row) % 3 != 1)
                    fill(r, bx + 2 * px + k * 4 * px, base - 7 * px + row * 3 * px, 2 * px, px, 0xc8d8b8, 150);
        if (fmodf(t, 1.0f) < 0.5f)
            fill(r, bx + 26 * px, base - 15 * px, px, px, 0xe8402a, 255);
        scene_draw_layers(r, world, camera_x, 3, BACKGROUND_LAYER_COUNT - 2); /* Near ridge in front */
        scene_draw_near(r, world, camera_x, platform_time());
        stage_end_view(r);
    } else if (line == 1) { /* Its corridor, under the emergency lights */
        SDL_Texture *tex = assets_texture("cinematics/lab/corridor");
        if (tex) {
            float pan = 40.0f + smooth(0.0f, shot_length, t) * 110.0f;
            int whole = (int)floorf(pan);
            SDL_Rect src = {whole - 2, 0, 324, 180};
            SDL_Rect dst = {-2 * ART + (int)lroundf(((float)whole - pan) * ART), 0, 324 * ART, 180 * ART};
            SDL_RenderCopy(r, tex, &src, &dst);
            cine_lab_atmosphere(r, pan, t, true);
        }
        ui_dim(r, 70);
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

/* ---- The second route's tapes ------------------------------------------------ */

/* A frame of a sheet standing on the road at view x (its middle). */
static void draw_piece(SDL_Renderer *r, const char *sheet, int frame, int w, int h, float x)
{
    SDL_Texture *tex = assets_texture(sheet);
    if (tex == NULL)
        return;
    SDL_Rect src = {frame * w, 0, w, h};
    SDL_Rect dst = {(int)lroundf(x) - w * SPRITE_SCALE / 2, BASELINE - h * SPRITE_SCALE, w * SPRITE_SCALE,
                    h * SPRITE_SCALE};
    SDL_RenderCopy(r, tex, &src, &dst);
}

/* A fire far off: a flickering tongue, its glow, a column of smoke leaning away. */
static void far_fire(SDL_Renderer *r, int x, int base, float t, int seed, int size)
{
    const int px = SPRITE_SCALE;
    int flick = (int)(t * 9.0f + (float)seed * 1.7f) % 3;
    fill(r, x - (2 + size) * px, base - px, (5 + 2 * size) * px, px, 0xd0581a, 120);
    fill(r, x - size * px, base - (2 + size + flick) * px, (1 + 2 * size) * px, (2 + size + flick) * px, 0xf08a24, 255);
    fill(r, x, base - (1 + size) * px, px, (1 + size) * px, 0xffd23c, 255);
    for (int k = 0; k < 9 + size * 3; k++) { /* Smoke */
        float rise = (float)k + fmodf(t * 1.5f + (float)seed, 1.0f);
        int sx = x + (int)lroundf(rise * 0.8f) * px, sy = base - (int)lroundf(4.0f + (float)size + rise * 1.6f) * px;
        fill(r, sx, sy, (2 + k / 4) * px, px, 0x2a2228, (Uint8)(150 - k * 9 > 20 ? 150 - k * 9 : 20));
    }
}

/* Santa Brasa seen from the last rise of Ojo de Cuervo: a low line of lit
 * windows on the horizon, its glow in the sky, and things burning in it. */
static void far_city(SDL_Renderer *r, float camera_x, float t, float zoom)
{
    const int px = SPRITE_SCALE;
    float start = PLAYER_START_X - VIEW_WIDTH / 2.0f + shot_origin, parallax = 0.3f;
    int bx = (int)CINE_X(420.0f) + (int)lroundf(start * parallax) - (int)lroundf(camera_x * parallax);
    int base = (GROUND_ROW - FAR_CITY_ROWS) * px;
    int unit = (int)lroundf(zoom);
    for (int k = 0; k < 6; k++) { /* Its glow in the sky: a low dome, brighter toward the roofs */
        int half = (62 - k * 9) * unit * px, cx = bx + 55 * px * unit;
        fill(r, cx - half, base - (3 + k * 2) * unit * px, 2 * half, 2 * unit * px, 0xe07a34, (Uint8)(34 - k * 5));
    }
    unsigned h = 77u;
    for (int k = 0; k < 22; k++) { /* The skyline, its windows */
        h = h * 1103515245u + 12345u;
        int w = (3 + (int)((h >> 16) % 4u)) * unit, tall = (3 + (int)((h >> 20) % 7u)) * unit;
        int x = bx + k * 5 * px * unit;
        fill(r, x, base - tall * px, w * px, tall * px, 0x1a1418, 255);
        for (int wy = 1; wy < tall - 1; wy += 2)
            for (int wx = 1; wx < w - 1; wx += 2)
                if (((h >> (wx + wy)) & 3u) == 0u)
                    fill(r, x + wx * px, base - (tall - wy) * px, px, px, 0xf0c870,
                         (Uint8)(fmodf(t * 0.7f + (float)(k + wx), 5.0f) < 4.6f ? 220 : 60));
    }
    far_fire(r, bx + 18 * px * unit, base - 4 * px * unit, t, 1, unit);
    far_fire(r, bx + 52 * px * unit, base - 7 * px * unit, t, 2, unit);
    far_fire(r, bx + 88 * px * unit, base - 3 * px * unit, t, 3, unit);
}

/* "Las luces de Santa Brasa": the sheriff on the rise, the city's light far
 * off and its fires; closer; her deciding; her taking the road. */
static void shot_luces(SDL_Renderer *r, int line, float t, const CharacterSkin *sheriff)
{
    if (!worlds_ready)
        begin_landscape(r, STORY_PUEBLO, 0.0f), stage_end_view(r);
    World *world = &worlds[line == 1 ? STORY_NOCHE : STORY_PUEBLO];
    float drift = cine_pan(t, shot_length, line == 1 ? 30.0f : line == 3 ? 60.0f : 10.0f);
    shot_drift = drift;
    float camera_x = PLAYER_START_X - VIEW_WIDTH / 2.0f + shot_origin + drift;
    world_stream(world, camera_x);
    stage_begin_view(r, world->theme);
    scene_draw_layers(r, world, camera_x, 0, 2);
    far_city(r, camera_x, t, line == 1 ? 2.0f : 1.0f);
    scene_draw_layers(r, world, camera_x, 3, BACKGROUND_LAYER_COUNT - 2);
    scene_draw_near(r, world, camera_x, platform_time());
    if (line != 1 && sheriff) {
        static Player her;
        static float her_time = -1.0f;
        static int her_line = -1;
        if (her_line != line || t < her_time) { /* A new shot: stood looking at it */
            player_init(&her);
            her.x = PLAYER_START_X - VIEW_WIDTH / 2.0f + shot_origin + CINE_X(300.0f);
            her_time = 0.0f;
            her_line = line;
        }
        while (line == 3 && her_time + FIXED_DT <= t) { /* The last line: she walks off toward it */
            bool down[ACTION_COUNT] = {false};
            InputState input = {0};
            down[ACTION_RIGHT] = line == 3 && her_time > 0.8f;
            input_update(&input, down);
            player_update(&her, &input, FIXED_DT);
            her_time += FIXED_DT;
        }
        player_render(r, &her, sheriff, sheriff->character->weapons, 0, camera_x);
    }
    stage_end_view(r);
    ui_dim(r, line == 1 ? 30 : 50);
}

/* The city's tapes (scenes 6-10): its landscape and what the lines tell. */
static void shot_city(SDL_Renderer *r, int scene, int line, float t, const CharacterSkin *sheriff)
{
    static const StoryVisual WHERE[] = {STORY_AFUERAS, STORY_CENTRO, STORY_VIAS, STORY_CIUDAD_NOCHE, STORY_BASE};
    StoryVisual visual = WHERE[scene - 6];
    if (scene == 9 && line == 1)
        visual = STORY_BASE; /* The post up on its hill, its alarm lit */
    begin_landscape(r, visual, cine_pan(t, shot_length, line == 0 ? 24.0f : 10.0f));
    int flash = 1 + (int)(t * 6.0f) % 2;
    switch (scene) {
    case 6: /* The closed city: the checkpoints, the sirens still calling */
        if (line == 0) {
            draw_piece(r, "sprites/terrain/vehicles", 0, VEHICLE_FRAME_W, VEHICLE_FRAME_H, CINE_X(300.0f) - shot_drift);
            draw_piece(r, "sprites/terrain/vehicles", 2, VEHICLE_FRAME_W, VEHICLE_FRAME_H, CINE_X(1100.0f) - shot_drift);
        } else if (line == 1) {
            draw_piece(r, "sprites/terrain/vehicles", 4, VEHICLE_FRAME_W, VEHICLE_FRAME_H, CINE_X(420.0f) - shot_drift);
            draw_piece(r, "sprites/terrain/barricade", 15, BARRICADE_FRAME_W, BARRICADE_FRAME_H, CINE_X(900.0f) - shot_drift);
            draw_piece(r, "sprites/terrain/barricade", 15, BARRICADE_FRAME_W, BARRICADE_FRAME_H, CINE_X(1180.0f) - shot_drift);
        } else {
            draw_piece(r, "sprites/terrain/siren_car", flash, SIREN_FRAME_W, SIREN_FRAME_H, CINE_X(640.0f) - shot_drift);
            static const ZombieKind WHO[] = {ZOMBIE_KIND_CITY_POLICE, ZOMBIE_KIND_CITY_NURSE, ZOMBIE_KIND_CITY_WORKER};
            for (int k = 0; k < 3; k++) {
                const AnimationDef *walk = zombie_animation(WHO[k], ZOMBIE_ANIM_WALK);
                cine_zombie(r, WHO[k], ZOMBIE_ANIM_WALK, (int)(t * walk->fps * 0.5f) + k * 3,
                            CINE_X(-80.0f + (float)k * 150.0f) + t * 40.0f, 0);
            }
        }
        break;
    case 7: /* The convoy through downtown, stopping for no one */
        for (int k = 0; k < 3; k++) {
            int vehicle = k == 1 ? 3 : 4;
            float speed = line == 0 ? 190.0f : 240.0f;
            float x = CINE_X(-500.0f + (float)k * 820.0f + t * speed) - shot_drift;
            float travel = CINE_X(t * speed);
            draw_piece(r, "sprites/terrain/vehicles", vehicle, VEHICLE_FRAME_W, VEHICLE_FRAME_H, x);
            cine_vehicle_wheels(r, vehicle, x, travel);
        }
        if (line == 1) {
            static const ZombieKind WHO[] = {ZOMBIE_KIND_CITY_OFFICE, ZOMBIE_KIND_CITY_GUARD};
            for (int k = 0; k < 2; k++)
                cine_zombie(r, WHO[k], ZOMBIE_ANIM_IDLE, (int)(t * 3.0f) + k, CINE_X(180.0f + (float)k * 620.0f), 0);
        }
        break;
    case 8: /* The train off its rails; its load going on by truck */
        draw_piece(r, "sprites/terrain/train", 0, TRAIN_W, TRAIN_H, CINE_X(560.0f) - shot_drift);
        draw_piece(r, "sprites/terrain/door", 3, DOOR_FRAME_W, DOOR_FRAME_H, CINE_X(560.0f) - shot_drift);
        if (line == 1) {
            float x = CINE_X(700.0f + t * 150.0f) - shot_drift;
            draw_piece(r, "sprites/terrain/vehicles", 4, VEHICLE_FRAME_W, VEHICLE_FRAME_H, x);
            cine_vehicle_wheels(r, 4, x, CINE_X(t * 150.0f));
        }
        break;
    case 9: /* Every track climbs the same hill; the post's alarm still lit */
        if (line == 0) {
            draw_piece(r, "sprites/terrain/vehicles", 2, VEHICLE_FRAME_W, VEHICLE_FRAME_H, CINE_X(360.0f) - shot_drift);
            draw_piece(r, "sprites/terrain/siren_car", 3, SIREN_FRAME_W, SIREN_FRAME_H, CINE_X(960.0f) - shot_drift);
        } else {
            draw_piece(r, "sprites/terrain/outpost", 1, OUTPOST_FRAME_W, OUTPOST_FRAME_H, CINE_X(520.0f) - shot_drift);
            draw_piece(r, "sprites/terrain/vehicles", 3, VEHICLE_FRAME_W, VEHICLE_FRAME_H, CINE_X(1040.0f) - shot_drift);
        }
        break;
    default: /* The director gone before dawn; what he left in the bunker */
        draw_piece(r, "sprites/terrain/city_fronts", 3, CITY_FRONT_W, CITY_FRONT_H, CINE_X(620.0f) - shot_drift);
        if (line == 0) { /* His helicopter, climbing away */
            const int px = SPRITE_SCALE;
            /* Over the wall, well up in the sky */
            int hx = (int)CINE_X(500.0f) / px * px + (int)lroundf(t * 70.0f - shot_drift) / px * px;
            int hy = BASELINE - 2 - 150 * px - (int)lroundf(t * 34.0f) / px * px;
            fill(r, hx, hy, 22 * px, 7 * px, 0x10080a, 255);
            fill(r, hx - 14 * px, hy + 2 * px, 14 * px, 2 * px, 0x10080a, 255);
            fill(r, hx - 16 * px, hy - px, 3 * px, 5 * px, 0x10080a, 255);
            fill(r, hx + 10 * px, hy - 3 * px, px, 3 * px, 0x10080a, 255);
            int blade = (int)(t * 20.0f) % 2 ? 26 : 12;
            fill(r, hx + 10 * px - blade * px, hy - 4 * px, 2 * blade * px, px, 0x10080a, 200);
            if ((int)(t * 4.0f) % 2)
                fill(r, hx + 20 * px, hy + 5 * px, px, px, 0xe8402a, 255);
        } else if (line == 1) {
            draw_piece(r, "sprites/terrain/door", 3, DOOR_FRAME_W, DOOR_FRAME_H, CINE_X(620.0f) - shot_drift);
        } else {
            draw_piece(r, "sprites/terrain/door", 5, DOOR_FRAME_W, DOOR_FRAME_H, CINE_X(620.0f) - shot_drift);
            draw_sheriff(r, sheriff, CINE_X(620.0f) - 190.0f);
        }
        break;
    }
    stage_end_view(r);
    ui_dim(r, 50);
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
    int scene = story->beat.scene;
    shot_origin = scene >= 0 && scene < 11 ? SHOT_ORIGINS[scene][line] : 0.0f;
    shot_length = story_line_length(story->beat.lines[line]);
    shot_drift = 0.0f;
    switch (story->beat.scene) {
    case 1: shot_panteon(r, line, t); break;
    case 2: shot_toque(r, line, t, sheriff); break;
    case 3: shot_pueblo(r, line, t); break;
    case 5: shot_luces(r, line, t, sheriff); break;
    case 6: case 7: case 8: case 9: case 10: shot_city(r, story->beat.scene, line, t, sheriff); break;
    default: shot_lab(r, line, t); break;
    }
    cine_frame(r);
    /* Each shot fades in from black and out to it, between the lines */
    float len = shot_length;
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
