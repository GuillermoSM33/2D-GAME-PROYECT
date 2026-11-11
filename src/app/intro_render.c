#include <math.h>
#include <stdio.h>
#include <string.h>

#include "app/intro_render.h"
#include "app/stage_render.h"
#include "engine/assets.h"
#include "engine/pixfont.h"
#include "game/player_render.h"
#include "game/scene.h"
#include "game/themes.h"
#include "game/hud.h"
#include "game/ui.h"
#include "game/zombie_render.h"

/* The cinematic's own images are whole screens at the world's pixel size:
 * one art px is ART window px (tools/make_cinematics.py). */
#define ART 3
#define LAB_W 320              /* Art px: one screen */
#define CORRIDOR_W 480
#define LAB_FLOOR_Y 156        /* Art row the mercenaries walk on, in the corridor */
#define MONITOR_FRAMES 6
#define ALARM_FRAMES 8
#define MERC_W 81
#define MERC_H 80
#define MERC_CENTER 36         /* His body's column, facing right */
#define MERC_GROUND 66         /* His feet's row */
#define MERC_LENS_X 70         /* The flashlight's lens, facing right */
#define MERC_LENS_Y 33
#define MERC_WALK_FRAMES 8      /* light_walk: 8 of walking, then 4 stood breathing */
#define MERC_BREATHS 4
#define MERC_STRIDE 40.0f       /* Art px a whole walk cycle covers, like hers */
#define MERC_SPEED 30.0f        /* Art px per second: a careful advance */
#define FRONT_W 110             /* sprites/mercenary/aim: him facing her camera */
#define FRONT_H 130
#define FRONT_LENS_X 67         /* Its flashlight's lens (tools/make_cinematics.py FRONT_LENS) */
#define FRONT_LENS_Y 81
#define FRONT_LEFT 360          /* Window px: where the first stands in her shot... */
#define FRONT2_LEFT 570         /* ...and the second, right beside him, a step behind */
#define VIAL_W 64
#define VIAL_H 100
#define VAN_W 72
#define VAN_H 34
#define VAN_FRAMES 4

#define CAPTION_Y 30
#define CAPTION_SCALE 3
#define NARRATOR_COLOR COLOR_STORY_TEXT
#define DIALOG_COLOR COLOR_STORY_DIALOG
#define REC_RED 0xe8402a
#define SAND_DUST 0xd7ab57

/* Scene times, seconds into each (they match game/intro.c's script). */
#define REC_CAMERA_ON 1.2f
#define SAMPLE_LENGTH 6.0f
#define SHOT_FLASH 0.35f        /* He fires (the shot's sound is cued here) */
#define SHOT_TUMBLE 0.6f        /* Her camera drops... */
#define SHOT_FALL 1.3f          /* ...hits the floor... */
#define SHOT_SIGNAL_LOST 2.4f   /* ...and dies */
#define TOWN_CROWS_FLY 6.2f
#define GRAVE_A_FROM 1.6f       /* The first grave */
#define GRAVE_A_TO 4.2f
#define COFFIN_SHAKE 2.2f       /* The coffin rattles, then bursts */
#define COFFIN_BURST 3.0f
#define GRAVE_B_FROM 3.3f       /* The second grave */
#define GRAVE_B_TO 5.8f
#define TITLE_WALK_FROM 1.0f
#define TITLE_WALK_TO 3.9f
#define TITLE_DUST_FROM 3.2f
#define TITLE_RISE_FROM 4.6f
#define TITLE_RISE_TO 7.0f
#define TITLE_DUST_HOLD 0.3f    /* How thick the dust stays once the title is up, into the menu */
#define TITLE_SCENE_END 9.0f

static World road_world, town_world, grave_world;
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

static unsigned hash(unsigned h)
{
    h ^= h >> 16;
    h *= 0x7feb352du;
    h ^= h >> 15;
    h *= 0x846ca68bu;
    return h ^ (h >> 16);
}

static void fill(SDL_Renderer *r, int x, int y, int w, int h, unsigned rgb, Uint8 alpha)
{
    SDL_SetRenderDrawBlendMode(r, SDL_BLENDMODE_BLEND);
    SDL_SetRenderDrawColor(r, (Uint8)(rgb >> 16), (Uint8)(rgb >> 8), (Uint8)rgb, alpha);
    SDL_Rect rect = {x, y, w, h};
    SDL_RenderFillRect(r, &rect);
}

static void add_light(SDL_Renderer *r, int x, int y, int w, int h, unsigned rgb)
{
    SDL_SetRenderDrawBlendMode(r, SDL_BLENDMODE_ADD);
    SDL_SetRenderDrawColor(r, (Uint8)(rgb >> 16), (Uint8)(rgb >> 8), (Uint8)rgb, 255);
    SDL_Rect rect = {x, y, w, h};
    SDL_RenderFillRect(r, &rect);
}

/* A disc of light in whole art px rows, added over what is there. */
static void light_disc(SDL_Renderer *r, int cx, int cy, int radius, unsigned rgb)
{
    for (int dy = -radius; dy <= radius; dy += ART) {
        int half = (int)sqrtf((float)(radius * radius - dy * dy)) / ART * ART;
        add_light(r, cx - half, cy + dy, 2 * half, ART, rgb);
    }
}

/* One frame (or a slice, at pan) of a cinematic image, filling the window. */
static void draw_screen(SDL_Renderer *r, const char *name, int src_x, int src_w, int dx)
{
    SDL_Texture *tex = assets_texture(name);
    if (tex == NULL)
        return;
    SDL_Rect src = {src_x, 0, src_w, 180};
    SDL_Rect dst = {dx, 0, src_w * ART, 180 * ART};
    SDL_RenderCopy(r, tex, &src, &dst);
}

/* The corridor through her camera, panned (art px), swaying in her hand. */
static void draw_corridor(SDL_Renderer *r, float pan, float t, bool handheld)
{
    int sway = handheld ? (int)lroundf(sinf(t * 1.7f) * 0.8f + sinf(t * 3.3f) * 0.5f) : 0;
    int p = (int)pan;
    if (p < 2)
        p = 2;
    if (p > CORRIDOR_W - LAB_W - 2)
        p = CORRIDOR_W - LAB_W - 2;
    draw_screen(r, "cinematics/lab/corridor", p - 2, LAB_W + 4, (sway - 2) * ART);
}

/* Her camera's overlay: corners, the blinking REC and its clock. */
static void draw_rec(SDL_Renderer *r, float clock, float t)
{
    const int m = 24, len = 30;
    unsigned ink = 0xe8e6e0;
    int corners[4][2] = {{m, m}, {WINDOW_WIDTH - m, m}, {m, WINDOW_HEIGHT - m}, {WINDOW_WIDTH - m, WINDOW_HEIGHT - m}};
    for (int c = 0; c < 4; c++) {
        int x = corners[c][0], y = corners[c][1];
        int sx = c % 2 ? -1 : 1, sy = c / 2 ? -1 : 1;
        fill(r, sx > 0 ? x : x - len, sy > 0 ? y : y - ART, len, ART, ink, 200);
        fill(r, sx > 0 ? x : x - ART, sy > 0 ? y : y - len, ART, len, ink, 200);
    }
    if (fmodf(t, 1.0f) < 0.6f)
        fill(r, m + 18, m + 18, 4 * ART, 4 * ART, REC_RED, 255);
    pixfont_draw(r, "REC", m + 18 + 6 * ART, m + 14, 2, ink, ANCHOR_NW, 220);
    int seconds = 3 * 3600 + 12 * 60 + 40 + (int)clock;
    char stamp[16];
    snprintf(stamp, sizeof(stamp), "%02d:%02d:%02d", seconds / 3600, seconds / 60 % 60, seconds % 60);
    pixfont_draw(r, stamp, WINDOW_WIDTH - m - 18, WINDOW_HEIGHT - m - 34, 2, ink, ANCHOR_NE, 220);
}

/* A cheap camera's look: scanlines and darker edges. */
static void draw_footage(SDL_Renderer *r)
{
    for (int y = 0; y < WINDOW_HEIGHT; y += ART * 2)
        fill(r, 0, y, WINDOW_WIDTH, 1, 0x000000, 40);
    for (int i = 0; i < 6; i++) {
        int e = (i + 1) * 2 * ART;
        Uint8 a = (Uint8)(14 * (6 - i));
        fill(r, 0, 0, e, WINDOW_HEIGHT, 0x000000, a);
        fill(r, WINDOW_WIDTH - e, 0, e, WINDOW_HEIGHT, 0x000000, a);
        fill(r, 0, 0, WINDOW_WIDTH, e, 0x000000, a);
        fill(r, 0, WINDOW_HEIGHT - e, WINDOW_WIDTH, e, 0x000000, a);
    }
}

/* Snow on a dying camera: grey specks, a different handful every frame. */
static void draw_static(SDL_Renderer *r, float t, Uint8 alpha)
{
    unsigned seed = (unsigned)(t * 30.0f) * 7919u;
    for (int i = 0; i < 700; i++) {
        unsigned h = hash(seed + (unsigned)i);
        int x = (int)(h % (WINDOW_WIDTH / ART)) * ART;
        int y = (int)((h >> 12) % (WINDOW_HEIGHT / ART)) * ART;
        unsigned grey = 0x30 + (h >> 24) % 0xa0;
        fill(r, x, y, ART * (1 + (h >> 8) % 3), ART, grey << 16 | grey << 8 | grey, alpha);
    }
}

/* A mercenary walking left at corridor x (art px), and his beam ahead of him
 * toward her. power: how bright the beam is (0..1). Returns the lens's
 * window position. */
static void draw_mercenary(SDL_Renderer *r, float x, float pan, float t, float phase,
                           float power, bool walking, int *lens_x, int *lens_y)
{
    SDL_Texture *tex = assets_texture("sprites/mercenary/walk");
    /* Steps matched to his pace, so his feet don't slide; stopped, he breathes. */
    int frame = walking ? (int)(t * MERC_WALK_FRAMES * MERC_SPEED / MERC_STRIDE + phase * 3.0f) % MERC_WALK_FRAMES
                        : MERC_WALK_FRAMES + (int)(t * 2.2f + phase) % MERC_BREATHS;
    int left = (int)lroundf((x - pan) * ART) - (MERC_W - MERC_CENTER) * ART;
    int top = LAB_FLOOR_Y * ART - MERC_GROUND * ART;
    if (tex) {
        SDL_Rect src = {frame * MERC_W, 0, MERC_W, MERC_H};
        SDL_Rect dst = {left, top, MERC_W * ART, MERC_H * ART};
        SDL_RenderCopyEx(r, tex, &src, &dst, 0.0, NULL, SDL_FLIP_HORIZONTAL);
    }
    int lx = left + (MERC_W - 1 - MERC_LENS_X) * ART, ly = top + MERC_LENS_Y * ART;
    if (lens_x)
        *lens_x = lx;
    if (lens_y)
        *lens_y = ly;
    if (power <= 0.0f)
        return;
    /* The beam: a cone of light widening to the left in whole art px, swaying. */
    float sway = sinf(t * 1.3f + phase * 2.0f);
    for (int k = 1; k < 34; k++) {
        int seg_x = lx - k * 4 * ART;
        if (seg_x + 4 * ART < 0)
            break;
        int half = (1 + k * 2 / 3) * ART;
        int cy = ly + (int)lroundf(sway * (float)k * 0.6f) / ART * ART + k / 3 * ART;
        unsigned v = (unsigned)lroundf(power * (float)(40 - k));
        unsigned core = v / 2;
        add_light(r, seg_x, cy - half, 4 * ART, 2 * half, v << 16 | v << 8 | (v * 7 / 8));
        if (half / 3 >= ART)
            add_light(r, seg_x, cy - half / 3 / ART * ART, 4 * ART, 2 * (half / 3 / ART * ART),
                      core << 16 | core << 8 | core);
    }
    light_disc(r, lx, ly, 3 * ART, 0x605a50);
}

static void draw_caption(SDL_Renderer *r, const Intro *intro)
{
    char buf[160];
    float alpha;
    bool dialog;
    if (!intro_caption(intro, buf, sizeof(buf), &alpha, &dialog))
        return;
    /* A single line sits where two would be centered */
    const char *whole = intro_caption_text(intro_scene(intro, NULL));
    int y = CAPTION_Y + (whole && strchr(whole, '\n') == NULL ? (pixfont_height(CAPTION_SCALE) + 2) / 2 : 0);
    char *line = buf;
    bool emphasis = false;
    while (line) {
        char *next = strchr(line, '\n');
        if (next)
            *next++ = '\0';
        pixfont_draw_rich(r, line, WINDOW_WIDTH / 2, y, CAPTION_SCALE, dialog ? DIALOG_COLOR : NARRATOR_COLOR,
                          COLOR_STORY_EMPHASIS, ANCHOR_N, (Uint8)lroundf(alpha * 255.0f), true, &emphasis);
        y += pixfont_height(CAPTION_SCALE) + 2;
        line = next;
    }
}

/* ---- The lab, through her camera ---------------------------------------- */

static void scene_rec(SDL_Renderer *r, float t, float clock)
{
    if (t < REC_CAMERA_ON) { /* Black: the camera is off */
        fill(r, 0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, 0x000000, 255);
        return;
    }
    float walk = (t - REC_CAMERA_ON) / (7.0f - REC_CAMERA_ON);
    draw_corridor(r, 4.0f + walk * 146.0f, t, true);
    if (t < REC_CAMERA_ON + 0.25f) /* It comes on with a jolt of white */
        fill(r, 0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, 0xffffff, (Uint8)(200.0f * (1.0f - (t - REC_CAMERA_ON) / 0.25f)));
    draw_footage(r);
    draw_rec(r, clock, t);
}

static void scene_monitors(SDL_Renderer *r, float t, float clock)
{
    int frame = (int)(t * 6.0f) % MONITOR_FRAMES;
    draw_screen(r, "cinematics/lab/monitors", frame * LAB_W, LAB_W, 0);
    draw_footage(r);
    draw_rec(r, clock, t);
}

static void scene_alarm(SDL_Renderer *r, float t, float clock)
{
    int frame = (int)(t / 0.7f);
    if (frame >= ALARM_FRAMES)
        frame = ALARM_FRAMES - 2 + (int)(t * 4.0f) % 2; /* Seething on its last two */
    draw_screen(r, "cinematics/lab/alarm", frame * LAB_W, LAB_W, 0);
    float pulse = 0.5f + 0.5f * sinf(t * 7.0f);
    fill(r, 0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, 0xff2000, (Uint8)(18.0f * pulse));
    draw_footage(r);
    draw_rec(r, clock, t);
}

#define MERCS_PAN 150.0f
#define MERC1_STOP 360.0f       /* Where each has got to when the scene ends (corridor x) */
#define MERC2_STOP 404.0f

static void scene_mercs(SDL_Renderer *r, float t, float clock)
{
    draw_corridor(r, MERCS_PAN, t, true);
    fill(r, 0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, 0x000000, 110); /* She has backed into the dark */
    float lights = smooth(0.8f, 1.0f, t);
    float lights2 = smooth(1.3f, 1.5f, t);
    /* Their lights come first, from beyond the frame; then they do. */
    draw_mercenary(r, MERC1_STOP + (8.0f - t) * MERC_SPEED, MERCS_PAN, t, 0.0f, lights, true, NULL, NULL);
    draw_mercenary(r, MERC2_STOP + (8.0f - t) * MERC_SPEED, MERCS_PAN, t, 1.0f, lights2, true, NULL, NULL);
    draw_footage(r);
    draw_rec(r, clock, t);
}

/* A flashlight straight into her lens: a hot core and a streak across it. */
static void lens_glare(SDL_Renderer *r, int x, int y, float power)
{
    for (int ring = 6; ring >= 1; ring--) {
        unsigned v = (unsigned)lroundf(power * (float)(7 - ring) * 7.0f);
        light_disc(r, x, y, ring * 2 * ART, v << 16 | v << 8 | (v * 7 / 8));
    }
    unsigned s1 = (unsigned)lroundf(power * 26.0f), s2 = (unsigned)lroundf(power * 14.0f);
    add_light(r, x - 46 * ART, y - ART / 2, 92 * ART, ART, s1 << 16 | s1 << 8 | s1);
    add_light(r, x - 80 * ART, y - ART / 2, 160 * ART, ART, s2 << 16 | s2 << 8 | s2);
}

/* One of them square to her camera (a frame of sprites/mercenary/aim), the
 * second mirrored and dimmer. Returns where his lens is. */
static void draw_front(SDL_Renderer *r, int left, int top, int frame, bool second, int *lx, int *ly)
{
    SDL_Texture *front = assets_texture("sprites/mercenary/aim");
    if (front) {
        SDL_Rect src = {frame * FRONT_W, 0, FRONT_W, FRONT_H};
        SDL_Rect dst = {left, top, FRONT_W * ART, FRONT_H * ART};
        if (second)
            SDL_SetTextureColorMod(front, 150, 150, 160);
        SDL_RenderCopyEx(r, front, &src, &dst, 0.0, NULL, second ? SDL_FLIP_HORIZONTAL : SDL_FLIP_NONE);
        SDL_SetTextureColorMod(front, 255, 255, 255);
    }
    int lift = frame == 2 ? 2 : frame == 3 ? 1 : 0;
    int col = second ? FRONT_W - 1 - FRONT_LENS_X : FRONT_LENS_X;
    *lx = left + col * ART + ART / 2;
    *ly = top + (FRONT_LENS_Y - lift) * ART + ART / 2;
}

/* Her shot of them, the sample up in her fist: both square to her camera,
 * side by side, rifles up; the first fires (front_frame of
 * sprites/mercenary/aim). ox, oy shake the whole picture (window px). */
static void sample_shot(SDL_Renderer *r, float t, float clock, int front_frame, int ox, int oy)
{
    draw_corridor(r, MERCS_PAN - (float)ox / ART, t, true);
    fill(r, 0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, 0x000000, 150);
    int top = WINDOW_HEIGHT - FRONT_H * ART + 30 + oy;
    int l2x, l2y, l1x, l1y;
    draw_front(r, FRONT2_LEFT + ox, top - 4 * ART, (int)(t * 1.1f + 0.5f) % 2, true, &l2x, &l2y);
    draw_front(r, FRONT_LEFT + ox, top, front_frame, false, &l1x, &l1y);
    float flicker = 0.85f + 0.15f * sinf(t * 9.0f);
    lens_glare(r, l2x, l2y, 0.6f * flicker);
    lens_glare(r, l1x, l1y, flicker);
    /* Her fist comes up into the shot with the sample, trembling */
    SDL_Texture *vial = assets_texture("sprites/vial/held");
    if (vial) {
        float rise = smooth(0.2f, 0.9f, t);
        int tremble = (int)(hash((unsigned)(t * 9.0f)) % 3) - 1;
        int x = 110 + tremble * ART + ox;
        int y = WINDOW_HEIGHT + 20 - (int)lroundf(rise * 300.0f) / ART * ART + oy;
        SDL_Rect dst = {x, y, VIAL_W * ART, VIAL_H * ART};
        SDL_RenderCopy(r, vial, NULL, &dst);
    }
    draw_footage(r);
    draw_rec(r, clock, t);
}

static void scene_sample(SDL_Renderer *r, float t, float clock)
{
    sample_shot(r, t, clock, (int)(t * 1.2f) % 2, 0, 0); /* Aiming, breathing */
}

static void scene_shot(SDL_Renderer *r, float t, float clock)
{
    if (t < SHOT_FALL) {
        /* He fires: the flash, the recoil, her camera jolted out of her hand */
        int frame = t < SHOT_FLASH ? 0 : t < SHOT_FLASH + 0.10f ? 2 : t < SHOT_FLASH + 0.25f ? 3 : 0;
        int ox = 0, oy = 0;
        if (t >= SHOT_FLASH) {
            float k = t - SHOT_FLASH;
            float amp = 22.0f * expf(-k * 3.0f);
            ox = (int)lroundf(sinf(k * 61.0f) * amp) / ART * ART;
            oy = (int)lroundf(cosf(k * 47.0f) * amp) / ART * ART;
            if (t > SHOT_TUMBLE) /* Falling out of her hand */
                oy += (int)lroundf((t - SHOT_TUMBLE) * (t - SHOT_TUMBLE) * 1100.0f) / ART * ART;
        }
        sample_shot(r, SAMPLE_LENGTH + t, clock, frame, ox, oy);
        if (t >= SHOT_FLASH && t < SHOT_FLASH + 0.08f) /* The muzzle flash dazzles the lens */
            fill(r, 0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, 0xfff4d8,
                 (Uint8)lroundf(80.0f * (1.0f - (t - SHOT_FLASH) / 0.08f)));
        if (t > SHOT_TUMBLE)
            draw_static(r, t, (Uint8)lroundf(140.0f * smooth(SHOT_TUMBLE, SHOT_FALL, t)));
        return;
    }
    fill(r, 0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, 0x000000, 255);
    if (t < SHOT_SIGNAL_LOST) {
        /* The camera on the floor: the corridor tilted, seen from low, flickering.
         * The tilt is a shear in whole art-px columns (rotating pixel art
         * would smear it). */
        SDL_Texture *tex = assets_texture("cinematics/lab/corridor");
        bool on = hash((unsigned)(t * 20.0f)) % 6 != 0;
        if (tex && on) {
            SDL_SetTextureColorMod(tex, 110, 110, 120);
            for (int col = 0; col < LAB_W; col += 2) {
                int lift = (col - LAB_W / 2) / 4;                 /* About 14 degrees */
                SDL_Rect src = {150 + col, 0, 2, 180};
                SDL_Rect dst = {col * ART, (10 - lift) * ART, 2 * ART, 180 * ART};
                SDL_RenderCopy(r, tex, &src, &dst);
            }
            SDL_SetTextureColorMod(tex, 255, 255, 255);
        }
        draw_static(r, t, (Uint8)(110.0f + 110.0f * smooth(SHOT_FALL, SHOT_SIGNAL_LOST, t)));
        draw_footage(r);
        draw_rec(r, clock, t);
    } else if (t < SHOT_SIGNAL_LOST + 0.3f) {
        draw_static(r, t, 230);
    } else {
        /* The feed is gone and stays gone */
        const char *label = "NO SIGNAL";
        int w = pixfont_width(label, 3) + 12 * ART, h = pixfont_height(3) + 6 * ART;
        int x = (WINDOW_WIDTH - w) / 2, y = (WINDOW_HEIGHT - h) / 2;
        bool shown = fmodf(t - SHOT_SIGNAL_LOST, 1.4f) < 1.0f;
        fill(r, x, y, w, h, 0x101418, 255);
        fill(r, x, y, w, ART, 0x8a96a2, 255);
        fill(r, x, y + h - ART, w, ART, 0x8a96a2, 255);
        fill(r, x, y, ART, h, 0x8a96a2, 255);
        fill(r, x + w - ART, y, ART, h, 0x8a96a2, 255);
        if (shown)
            pixfont_draw(r, label, WINDOW_WIDTH / 2, y + 3 * ART, 3, 0xe8e6e0, ANCHOR_N, 255);
    }
}

/* ---- Outside: the stages' own landscapes ---------------------------------- */

static void ready_worlds(void)
{
    if (worlds_ready)
        return;
    world_init(&road_world, &THEME_ATARDECER);
    world_init(&town_world, &THEME_PUEBLO_FANTASMA);
    world_init(&grave_world, &THEME_CEMENTERIO);
    worlds_ready = true;
}

static void begin_world(SDL_Renderer *r, World *world, float camera_x)
{
    world_stream(world, camera_x);
    stage_begin_view(r, world->theme);
    scene_draw(r, world, camera_x, platform_time());
}

/* A zombie's sheet frame at view x, facing, sunk rows below the ground. */
static void draw_zombie_frame(SDL_Renderer *r, ZombieKind kind, ZombieAnimation action, int frame_offset,
                              float view_x, int facing, int sunk)
{
    const AnimationDef *def = zombie_animation(kind, action);
    int frame = def->first_frame + frame_offset % def->frame_count;
    SDL_Texture *sheet = zombie_animation_texture(def, &frame);
    if (sheet == NULL)
        return;
    int rows = def->ground_y - sunk;
    if (rows <= 0)
        return;
    bool left = facing < 0;
    float anchor = left ? (float)def->frame_w - def->anchor_x : def->anchor_x;
    SDL_Rect src = {frame * def->frame_w, 0, def->frame_w, rows};
    SDL_Rect dst = {(int)lroundf(view_x - anchor * SPRITE_SCALE), BASELINE - rows * SPRITE_SCALE,
                    def->frame_w * SPRITE_SCALE, rows * SPRITE_SCALE};
        SDL_RenderCopyEx(r, sheet, &src, &dst, 0.0, NULL, left ? SDL_FLIP_HORIZONTAL : SDL_FLIP_NONE);
}

static void scene_road(SDL_Renderer *r, float t)
{
    float camera_x = PLAYER_START_X - VIEW_WIDTH / 2.0f + t * 60.0f;
    begin_world(r, &road_world, camera_x);
    float vx = -320.0f + t * 200.0f;
    int frame = (int)(t * 10.0f) % VAN_FRAMES;
    /* Dust kicked up behind it */
    for (int i = 0; i < 14; i++) {
        unsigned h = hash((unsigned)i * 31u);
        float age = fmodf(t * 1.6f + (float)(h % 100) / 100.0f, 1.0f);
        int x = (int)lroundf(vx - age * 180.0f - (float)(h % 40)) / SPRITE_SCALE * SPRITE_SCALE;
        int y = BASELINE - (int)lroundf(age * 40.0f + (float)((h >> 8) % 16)) / SPRITE_SCALE * SPRITE_SCALE;
        fill(r, x, y, 2 * SPRITE_SCALE, 2 * SPRITE_SCALE, SAND_DUST, (Uint8)(150.0f * (1.0f - age)));
    }
    SDL_Texture *van = assets_texture("sprites/ambulance/drive");
    if (van) {
        SDL_Rect src = {frame * VAN_W, 0, VAN_W, VAN_H};
        SDL_Rect dst = {(int)lroundf(vx), BASELINE - VAN_H * SPRITE_SCALE + SPRITE_SCALE, VAN_W * SPRITE_SCALE,
                        VAN_H * SPRITE_SCALE};
        SDL_RenderCopy(r, van, &src, &dst);
    }
    stage_end_view(r);
}

static void draw_crow(SDL_Renderer *r, int frame, float view_x, float height, int facing)
{
    SDL_Texture *sheet = assets_texture("sprites/crow/crow");
    if (sheet == NULL)
        return;
    SDL_Rect src = {frame * CROW_FRAME_W, 0, CROW_FRAME_W, CROW_FRAME_H};
    SDL_Rect dst = {(int)lroundf(view_x) - CROW_FRAME_W * SPRITE_SCALE / 2,
                    BASELINE - (int)lroundf(height) - CROW_FRAME_H * SPRITE_SCALE, CROW_FRAME_W * SPRITE_SCALE,
                    CROW_FRAME_H * SPRITE_SCALE};
    SDL_RenderCopyEx(r, sheet, &src, &dst, 0.0, NULL, facing < 0 ? SDL_FLIP_HORIZONTAL : SDL_FLIP_NONE);
}

static void scene_town(SDL_Renderer *r, float t)
{
    float camera_x = PLAYER_START_X - VIEW_WIDTH / 2.0f + t * 18.0f;
    begin_world(r, &town_world, camera_x);
    /* Someone staggering down the empty street */
    const AnimationDef *walk = zombie_animation(ZOMBIE_KIND_CIVIL_FEMALE_2, ZOMBIE_ANIM_WALK);
    float zx = 120.0f + t * 34.0f;
    draw_zombie_frame(r, ZOMBIE_KIND_CIVIL_FEMALE_2, ZOMBIE_ANIM_WALK, (int)(t * walk->fps * 0.55f), zx, 1, 0);
    static const float crows_x[] = {760.0f, 830.0f, 880.0f};
    for (int i = 0; i < 3; i++) {
        float x = crows_x[i] - t * 18.0f; /* They stay put while the view drifts */
        if (t < TOWN_CROWS_FLY + (float)i * 0.15f) {
            draw_crow(r, (int)(t * 3.0f + (float)i) % 2, x, 0.0f, 1);
        } else {
            float f = t - TOWN_CROWS_FLY - (float)i * 0.15f;
            draw_crow(r, 2 + (int)(f * 12.0f) % 4, x + f * 240.0f, f * 170.0f + f * f * 40.0f, 1);
        }
    }
    stage_end_view(r);
}

/* A heap of fresh earth on a grave, in front of whoever climbs out of it;
 * open (0..1) splits its top into a black hole. */
static void draw_mound(SDL_Renderer *r, float x, float open)
{
    const int px = SPRITE_SCALE;
    static const int half[] = {17, 16, 14, 11, 7};
    int cx = (int)lroundf(x) / px * px;
    for (int row = 0; row < 5; row++) {
        int y = BASELINE - (row + 1) * px;
        fill(r, cx - half[row] * px, y, 2 * half[row] * px, px, row == 4 ? 0x684833 : 0x463322, 255);
        fill(r, cx - half[row] * px, y, px, px, 0x2c2218, 255);           /* Its shaded left edge */
    }
    for (int k = -12; k <= 12; k += 5)                                     /* Lighter clods on top */
        fill(r, cx + k * px, BASELINE - 5 * px, px, px, 0x876439, 255);
    int hole = (int)lroundf(open * 9.0f);
    if (hole > 0) {
        fill(r, cx - hole * px, BASELINE - 5 * px, 2 * hole * px, 2 * px, 0x120c08, 255);
        fill(r, cx - (hole - 1) * px, BASELINE - 3 * px, 2 * (hole - 1) * px, px, 0x120c08, 255);
    }
}

static void draw_tombstone(SDL_Renderer *r, float x, int variant)
{
    SDL_Texture *tex = assets_texture("sprites/props/tombstone");
    if (tex == NULL)
        return;
    SDL_Rect src = {variant * 14, 0, 14, 18};
    SDL_Rect dst = {(int)lroundf(x) - 7 * SPRITE_SCALE, BASELINE - 18 * SPRITE_SCALE, 14 * SPRITE_SCALE, 18 * SPRITE_SCALE};
    SDL_SetTextureColorMod(tex, 150, 140, 160);
    SDL_RenderCopy(r, tex, &src, &dst);
    SDL_SetTextureColorMod(tex, 255, 255, 255);
}

/* Earth thrown up out of a grave from `from`, falling back. */
static void draw_clods(SDL_Renderer *r, float x, float from, float t, unsigned seed)
{
    const int px = SPRITE_SCALE;
    for (int i = 0; i < 14; i++) {
        unsigned h = hash((unsigned)i * 97u + seed);
        float f = t - from - (float)(h % 100) / 100.0f * 1.2f;
        if (f < 0.0f)
            continue;
        float vx = ((float)((h >> 8) % 120) - 60.0f) * 2.5f, vy = 240.0f + (float)((h >> 16) % 160);
        float height = vy * f - 700.0f * f * f;
        if (height < 0.0f)
            continue;
        int cx = (int)lroundf(x + vx * f) / px * px;
        int cy = BASELINE - (int)lroundf(height) / px * px - 6 * px;
        fill(r, cx, cy, 2 * px, 2 * px, h % 2 ? 0x463322 : 0x684833, 255);
    }
}

/* A zombie climbing out of a grave at x between from and to, then standing. */
static void grave_zombie(SDL_Renderer *r, ZombieKind kind, float x, float from, float to, float t)
{
    if (t < from)
        return;
    const AnimationDef *def = zombie_animation(kind, ZOMBIE_ANIM_IDLE);
    int sunk = (int)lroundf((1.0f - smooth(from, to, t)) * (float)def->ground_y);
    int frame = t < to ? (int)(t * 6.0f) : (int)(t * def->fps);
    /* Facing right: mirrored sprites shift inside the scaled view in SDL's
     * software renderer (the captures), so the intro keeps them unmirrored. */
    draw_zombie_frame(r, kind, ZOMBIE_ANIM_IDLE, frame, x, 1, sunk);
}

static void scene_grave(SDL_Renderer *r, float t)
{
    float camera_x = PLAYER_START_X - VIEW_WIDTH / 2.0f;
    begin_world(r, &grave_world, camera_x);
    const float grave_a = 330.0f, coffin_x = 690.0f, grave_b = 1010.0f;
    draw_tombstone(r, grave_a + 92.0f, 1);
    draw_tombstone(r, grave_b + 92.0f, 0);
    /* The coffin stood against the dark: rattling, then burst open */
    SDL_Texture *coffin = assets_texture("sprites/terrain/coffin");
    if (coffin) {
        bool open = t >= COFFIN_BURST;
        int shake = t >= COFFIN_SHAKE && !open ? ((int)(t * 24.0f) % 2 ? 1 : -1) * SPRITE_SCALE : 0;
        SDL_Rect src = {(open ? 3 : 2) * 32, 0, 32, 68};
        SDL_Rect dst = {(int)coffin_x - 16 * SPRITE_SCALE + shake, BASELINE - 68 * SPRITE_SCALE, 32 * SPRITE_SCALE,
                        68 * SPRITE_SCALE};
        SDL_RenderCopy(r, coffin, &src, &dst);
    }
    grave_zombie(r, ZOMBIE_KIND_CIVIL_MALE_3, grave_a, GRAVE_A_FROM, GRAVE_A_TO, t);
    grave_zombie(r, ZOMBIE_KIND_CIVIL_MALE_1, grave_b, GRAVE_B_FROM, GRAVE_B_TO, t);
    if (t >= COFFIN_BURST) { /* Out of the coffin and down the row toward the others */
        const AnimationDef *walk = zombie_animation(ZOMBIE_KIND_CIVIL_FEMALE_4, ZOMBIE_ANIM_WALK);
        float f = t - COFFIN_BURST;
        draw_zombie_frame(r, ZOMBIE_KIND_CIVIL_FEMALE_4, ZOMBIE_ANIM_WALK, (int)(f * walk->fps * 0.5f),
                          coffin_x + 10.0f + f * 26.0f, 1, 0);
        for (int i = 0; i < 10; i++) { /* Splinters and dust off the lid */
            unsigned h = hash((unsigned)i * 131u + 7u);
            float g = f - (float)(h % 30) / 100.0f;
            if (g < 0.0f || g > 0.8f)
                continue;
            int x = (int)lroundf(coffin_x + ((float)(h % 90) - 45.0f) * g * 3.0f) / SPRITE_SCALE * SPRITE_SCALE;
            int y = BASELINE - (int)lroundf(40.0f * (float)SPRITE_SCALE - 300.0f * g * g + (float)((h >> 8) % 40) * g * 4.0f);
            fill(r, x, y, SPRITE_SCALE, SPRITE_SCALE, h % 3 ? 0x5a4a3a : 0x8a7a64, (Uint8)(255.0f * (1.0f - g / 0.8f)));
        }
    }
    draw_mound(r, grave_a, smooth(GRAVE_A_FROM - 0.6f, GRAVE_A_FROM + 0.4f, t));
    draw_mound(r, grave_b, smooth(GRAVE_B_FROM - 0.6f, GRAVE_B_FROM + 0.4f, t));
    draw_clods(r, grave_a, GRAVE_A_FROM, t, 5u);
    draw_clods(r, grave_b, GRAVE_B_FROM, t, 23u);
    stage_end_view(r);
    fill(r, 0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, 0x05081a, 70); /* Night coming down */
    /* Lightning: two flashes over the graves */
    float flash = fmaxf(1.0f - fabsf(t - 0.40f) / 0.12f, 0.6f * (1.0f - fabsf(t - 0.72f) / 0.08f));
    if (flash > 0.0f)
        fill(r, 0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, 0xe8f0ff, (Uint8)(180.0f * clamp01(flash)));
}

/* ---- The sheriff, and the title out of the dust ---------------------------- */

void intro_draw_dust(SDL_Renderer *r, float t, float thick)
{
    static const unsigned sand[] = {0xd7ab57, 0xc89a6a, 0x9c7a4a, 0xe8c890};
    for (int i = 0; i < 220; i++) {
        unsigned h = hash((unsigned)i * 2654435761u);
        float speed = 120.0f + (float)(h % 160);
        float x = fmodf((float)(h % 1200) + t * speed, 1200.0f) - 120.0f;
        float y = 10.0f + (float)((h >> 10) % 190) + sinf(t * 2.0f + (float)i) * 6.0f;
        int w = (h >> 20) % 4 == 0 ? 2 * ART : ART;
        Uint8 a = (Uint8)lroundf(thick * (float)(90 + (h >> 24) % 120));
        if (a > 0)
            fill(r, (int)x / ART * ART, (int)y / ART * ART, w, ART, sand[(h >> 4) % 4], a);
    }
    SDL_SetRenderDrawBlendMode(r, SDL_BLENDMODE_NONE);
}

void intro_draw_title_dust(SDL_Renderer *r, double since)
{
    intro_draw_dust(r, TITLE_SCENE_END + (float)fmod(since, 3600.0), TITLE_DUST_HOLD);
}

static Player sheriff_view;
static float sheriff_time = -1.0f;

static void step_sheriff(float t)
{
    if (sheriff_time < 0.0f || t < sheriff_time) {
        player_init(&sheriff_view);
        sheriff_view.x = PLAYER_START_X + 640.0f; /* Mid-view, looking at the town */
        sheriff_time = 0.0f;
    }
    InputState input;
    input_init(&input);
    while (sheriff_time + FIXED_DT <= t) {
        bool down[ACTION_COUNT] = {false};
        down[ACTION_RIGHT] = sheriff_time >= TITLE_WALK_FROM && sheriff_time < TITLE_WALK_TO;
        input_update(&input, down);
        player_update(&sheriff_view, &input, FIXED_DT);
        sheriff_time += FIXED_DT;
    }
}

static void scene_title(SDL_Renderer *r, float t, World *title_world, const CharacterSkin *sheriff, bool full)
{
    float camera_x = PLAYER_START_X;
    world_stream(title_world, camera_x);
    stage_begin_view(r, title_world->theme);
    scene_draw(r, title_world, camera_x, platform_time());
    if (full && sheriff && t < TITLE_WALK_TO + 0.5f) {
        step_sheriff(t);
        player_render(r, &sheriff_view, sheriff, sheriff->character->weapons, 0, camera_x);
    }
    stage_end_view(r);
    /* The menus' dim comes up as the title does, so the title screen matches */
    ui_dim(r, (Uint8)lroundf(0.15f * 255.0f * smooth(TITLE_DUST_FROM, TITLE_RISE_TO, t)));
    /* Dust blown across the sky band, thickest as the title forms; it keeps
     * blowing, thinner, behind the title screen (intro_draw_dust). */
    float thick = smooth(TITLE_DUST_FROM, 4.6f, t) * (1.0f - (1.0f - TITLE_DUST_HOLD) * smooth(6.4f, 8.6f, t));
    intro_draw_dust(r, t, thick);
    Uint8 title_a = (Uint8)lroundf(255.0f * smooth(TITLE_RISE_FROM, TITLE_RISE_TO, t));
    if (title_a > 0)
        pixfont_draw(r, TITLE_TEXT, WINDOW_WIDTH / 2, TITLE_Y, TITLE_SCALE, COLOR_HUD_TITLE, ANCHOR_N, title_a);
    Uint8 sub_a = (Uint8)lroundf(255.0f * smooth(6.6f, 7.8f, t));
    if (sub_a > 0)
        pixfont_draw(r, TITLE_TAGLINE, WINDOW_WIDTH / 2, TITLE_TAGLINE_Y, 2, COLOR_HUD_PRIMARY, ANCHOR_N, sub_a);
}

void intro_render(Platform *platform, const Intro *intro, World *title_world, const CharacterSkin *sheriff)
{
    SDL_Renderer *r = platform->renderer;
    ready_worlds();
    float local;
    IntroScene scene = intro_scene(intro, &local);
    float clock = intro->time;
    SDL_SetRenderDrawColor(r, 0, 0, 0, 255);
    SDL_RenderClear(r);
    switch (scene) {
    case INTRO_REC: scene_rec(r, local, clock); break;
    case INTRO_MONITORS: scene_monitors(r, local, clock); break;
    case INTRO_ALARM: scene_alarm(r, local, clock); break;
    case INTRO_MERCS: scene_mercs(r, local, clock); break;
    case INTRO_SAMPLE: scene_sample(r, local, clock); break;
    case INTRO_SHOT: scene_shot(r, local, clock); break;
    case INTRO_ROAD: scene_road(r, local); break;
    case INTRO_TOWN: scene_town(r, local); break;
    case INTRO_GRAVE: scene_grave(r, local); break;
    default: scene_title(r, local, title_world, sheriff, intro->mode == INTRO_FULL); break;
    }
    draw_caption(r, intro);
    float black = intro_black(intro);
    if (black > 0.0f)
        fill(r, 0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, 0x000000, (Uint8)lroundf(black * 255.0f));
    if (!(scene == INTRO_TITLE && local > TITLE_RISE_FROM - 0.6f))
        pixfont_draw(r, "ENTER: SALTAR", WINDOW_WIDTH / 2, WINDOW_HEIGHT - 26, 2, 0xb0aaa0, ANCHOR_N, 110);
    SDL_SetRenderDrawBlendMode(r, SDL_BLENDMODE_NONE);
}

/* ---- Pieces shared with the tapes' shots (app/story_render.c) ---------------- */

void cine_zombie(SDL_Renderer *r, ZombieKind kind, ZombieAnimation action, int frame, float view_x, int sunk)
{
    draw_zombie_frame(r, kind, action, frame, view_x, 1, sunk);
}

void cine_mound(SDL_Renderer *r, float x, float open)
{
    draw_mound(r, x, open);
}

void cine_tombstone(SDL_Renderer *r, float x, int variant)
{
    draw_tombstone(r, x, variant);
}

void cine_clods(SDL_Renderer *r, float x, float from, float t, unsigned seed)
{
    draw_clods(r, x, from, t, seed);
}

void cine_crow(SDL_Renderer *r, int frame, float view_x, float height, int facing)
{
    draw_crow(r, frame, view_x, height, facing);
}
