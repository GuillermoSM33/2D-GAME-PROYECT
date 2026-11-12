#include "game/scene.h"

#include <math.h>
#include <stdio.h>

#include "config.h"
#include "engine/assets.h"
#include "engine/platform.h"

/* Background layers and props are pixel art at the sprites' scale. */
#define PX SPRITE_SCALE
#define HOUSES_SHEET "sprites/props/houses"

/* The props' sheets in the current theme's light: copies of the embedded
 * ones, drawn in daylight colors, graded when the theme changes. */
static const ThemeDef *props_theme;
static SDL_Texture *themed_props[PROP_KIND_COUNT];
static SDL_Texture *themed_houses;
static SDL_Texture *foreground;
static int foreground_w, foreground_h;
static SDL_Renderer *foreground_renderer;
static SDL_Texture *previous_target;
static SDL_Rect previous_viewport;
static float previous_scale_x, previous_scale_y;
static bool foreground_active;

static void release_props(void)
{
    for (int k = 0; k < PROP_KIND_COUNT; k++) {
        if (themed_props[k])
            SDL_DestroyTexture(themed_props[k]);
        themed_props[k] = NULL;
    }
    if (themed_houses)
        SDL_DestroyTexture(themed_houses);
    themed_houses = NULL;
    props_theme = NULL;
}

/* A color a share of the way to another (0xRRGGBB). */
static unsigned toward(unsigned from, unsigned to, float share)
{
    unsigned out = 0;
    for (int shift = 16; shift >= 0; shift -= 8) {
        float a = (float)((from >> shift) & 0xFF), b = (float)((to >> shift) & 0xFF);
        out |= (unsigned)lroundf(a + (b - a) * share) << shift;
    }
    return out;
}

static void prepare_props(SDL_Renderer *renderer, const ThemeDef *theme)
{
    if (props_theme == theme)
        return;
    release_props();
    for (int k = 0; k < PROP_KIND_COUNT; k++)
        themed_props[k] = assets_texture_graded(renderer, prop_def(k)->sheet, theme->prop_shadow, theme->prop_light);
    /* The houses stand further off: the air between takes some of their contrast. */
    themed_houses = assets_texture_graded(renderer, HOUSES_SHEET, toward(theme->prop_shadow, theme->haze, HOUSE_HAZE),
                                          toward(theme->prop_light, theme->haze, HOUSE_HAZE));
    props_theme = theme;
}

void scene_shutdown(void)
{
    if (foreground_active && foreground_renderer)
        SDL_SetRenderTarget(foreground_renderer, previous_target);
    if (foreground)
        SDL_DestroyTexture(foreground);
    foreground = NULL;
    foreground_renderer = NULL;
    foreground_active = false;
    release_props();
}

static SDL_Texture *layer_texture(const ThemeDef *theme, const BackgroundLayer *layer)
{
    char name[96];
    snprintf(name, sizeof(name), "backgrounds/%s/%s", theme->name, layer->file);
    return assets_texture(name);
}

/* One layer, scrolled by offset window px and tiled if it repeats. */
static void draw_layer(SDL_Renderer *renderer, SDL_Texture *texture, const BackgroundLayer *layer,
                       float offset)
{
    int w = layer->width * PX, h = layer->height * PX;
    int y = layer->top_row * PX;
    if (!layer->repeat) {
        SDL_Rect dst = {0, y, w, h};
        SDL_RenderCopy(renderer, texture, NULL, &dst);
        /* Wider than the art (the sky): its last column carries on, its bands
         * being level, to the view's edge. */
        if (w < VIEW_WIDTH) {
            SDL_Rect edge = {layer->width - 1, 0, 1, layer->height};
            SDL_Rect rest = {w, y, VIEW_WIDTH - w, h};
            SDL_RenderCopy(renderer, texture, &edge, &rest);
        }
        /* ...and its last row, down to the ground line: what shows through
         * any gap in the land in front of it. */
        if (y + h < GROUND_ROW * PX) {
            SDL_Rect foot = {0, layer->height - 1, layer->width, 1};
            SDL_Rect below = {0, y + h, VIEW_WIDTH > w ? VIEW_WIDTH : w, GROUND_ROW * PX - (y + h)};
            SDL_RenderCopy(renderer, texture, &foot, &below);
        }
        return;
    }
    /* Leftmost tile: where the scrolled strip starts, wrapped into [-w, 0). */
    int x = -(int)lroundf(fmodf(offset, (float)w));
    for (; x < VIEW_WIDTH; x += w) {
        SDL_Rect dst = {x, y, w, h};
        SDL_RenderCopy(renderer, texture, NULL, &dst);
    }
}

static void draw_prop(SDL_Renderer *renderer, const Prop *prop, float screen_x)
{
    const PropDef *def = prop_def(prop->kind);
    SDL_Texture *sheet = themed_props[prop->kind];
    if (sheet == NULL)
        return;
    /* Resting on its last row, right above the ground line. */
    SDL_Rect src = {prop->variant * def->frame_w, 0, def->frame_w, def->frame_h};
    SDL_Rect dst = {
        (int)lroundf(screen_x + prop->x) - def->frame_w * PX / 2,
        GROUND_ROW * PX - def->frame_h * PX,
        def->frame_w * PX,
        def->frame_h * PX,
    };
    SDL_RenderCopy(renderer, sheet, &src, &dst);
}

static void draw_props(SDL_Renderer *renderer, const World *world, float camera_x)
{
    for (int i = 0; i < WORLD_CACHE_CHUNKS; i++) {
        const Chunk *chunk = &world->ground.slots[i];
        if (!chunk->loaded)
            continue;
        float screen_x = (float)(chunk->index * WORLD_CHUNK_W) - camera_x;
        if (screen_x > VIEW_WIDTH || screen_x + WORLD_CHUNK_W < 0.0f)
            continue; /* Loaded ahead, not on screen yet (props stay inside their chunk) */
        for (int p = 0; p < chunk->prop_count; p++)
            draw_prop(renderer, &chunk->props[p], screen_x);
    }
}

/* Buildings off the road on a strip of their own, behind the props: a slot
 * every HOUSE_SPACING, filled or not and with which one by a hash of the slot,
 * so the same road always shows the same town. */
#define SCENE_MAX_RIVERS 8
static float rivers[SCENE_MAX_RIVERS];
static int river_count;
static float river_half;

void scene_set_rivers(const float *xs, int count, float half)
{
    river_count = count < SCENE_MAX_RIVERS ? count : SCENE_MAX_RIVERS;
    for (int i = 0; i < river_count; i++)
        rivers[i] = xs[i];
    river_half = half;
}

/* A house at strip x (house_x) slides by at HOUSE_PARALLAX of the road: it
 * lines up with a river once, at one camera. If the river is in view then,
 * the house is never drawn (so none pops in or out). */
static bool over_a_river(float house_x, float w)
{
    float reach = w / 2.0f + river_half + 120.0f;
    for (int i = 0; i < river_count; i++) {
        /* Screen gap: (house_x + w/2 - p cam) - (river - cam) = house_x + w/2 - river + (1 - p) cam. */
        float slide = 1.0f - HOUSE_PARALLAX;
        float c0 = (rivers[i] - house_x - w / 2.0f - reach) / slide;
        float c1 = (rivers[i] - house_x - w / 2.0f + reach) / slide;
        /* The river is in view for cameras from river - VIEW_WIDTH - half to river + half. */
        if (c1 >= rivers[i] - (float)VIEW_WIDTH - river_half && c0 <= rivers[i] + river_half)
            return true;
    }
    return false;
}

static void draw_houses(SDL_Renderer *renderer, const ThemeDef *theme, float camera_x)
{
    if (themed_houses == NULL || theme->house_chance <= 0)
        return;
    float strip = camera_x * HOUSE_PARALLAX;
    int w = HOUSE_FRAME_W * PX, h = HOUSE_FRAME_H * PX;
    long first = (long)floorf((strip - (float)w - HOUSE_JITTER) / HOUSE_SPACING);
    long last = (long)floorf((strip + (float)VIEW_WIDTH) / HOUSE_SPACING);
    for (long slot = first; slot <= last; slot++) {
        unsigned hash = (unsigned)slot * 2654435761u;
        hash ^= hash >> 15;
        hash *= 0x2c1b3c6du;
        hash ^= hash >> 12;
        if ((int)(hash % 100u) >= theme->house_chance)
            continue;
        int variant = theme->house_count > 0 ? theme->houses[(hash >> 8) % (unsigned)theme->house_count]
                                             : (int)((hash >> 8) % HOUSE_FRAMES_WEST);
        float jitter = (float)((hash >> 16) % (unsigned)HOUSE_JITTER);
        if (over_a_river((float)slot * HOUSE_SPACING + jitter, (float)w))
            continue;
        SDL_Rect src = {variant * HOUSE_FRAME_W, 0, HOUSE_FRAME_W, HOUSE_FRAME_H};
        SDL_Rect dst = {(int)lroundf((float)slot * HOUSE_SPACING + jitter - strip),
                        GROUND_ROW * PX - h - HOUSE_RAISE * PX, w, h};
        SDL_RenderCopy(renderer, themed_houses, &src, &dst);
    }
}

unsigned scene_sky_top(const ThemeDef *theme)
{
    char name[96];
    snprintf(name, sizeof(name), "backgrounds/%s/%s", theme->name, BACKGROUND_LAYERS[0].file);
    const EmbeddedImage *sky = assets_find_image(name);
    if (sky == NULL)
        return COLOR_BACKGROUND;
    return ((unsigned)sky->rgba[0] << 16) | ((unsigned)sky->rgba[1] << 8) | sky->rgba[2];
}

void scene_draw_layers(SDL_Renderer *renderer, const World *world, float camera_x, int first, int last)
{
    const ThemeDef *theme = world->theme;
    prepare_props(renderer, theme);
    if (last > BACKGROUND_LAYER_COUNT - 2)
        last = BACKGROUND_LAYER_COUNT - 2;
    for (int i = first < 0 ? 0 : first; i <= last; i++) {
        const BackgroundLayer *layer = &BACKGROUND_LAYERS[i];
        SDL_Texture *texture = layer_texture(theme, layer);
        if (texture)
            draw_layer(renderer, texture, layer, camera_x * layer->parallax);
    }
    if (last == BACKGROUND_LAYER_COUNT - 2) /* The houses stand in front of the nearest hills */
        draw_houses(renderer, theme, camera_x);
}

void scene_draw_distant(SDL_Renderer *renderer, const World *world, float camera_x)
{
    scene_draw_layers(renderer, world, camera_x, 0, BACKGROUND_LAYER_COUNT - 2);
}

void scene_draw_near(SDL_Renderer *renderer, const World *world, float camera_x, double time)
{
    const ThemeDef *theme = world->theme;
    prepare_props(renderer, theme);
    draw_props(renderer, world, camera_x);
    const BackgroundLayer *ground = &BACKGROUND_LAYERS[BACKGROUND_LAYER_COUNT - 1];
    SDL_Texture *texture = layer_texture(theme, ground);
    if (texture)
        draw_layer(renderer, texture, ground, camera_x * ground->parallax);
    if (theme->fog) {
        SDL_Texture *fog = layer_texture(theme, &FOG_LAYER);
        /* Wrapped to one tile's worth of drift, so a long session keeps float precision. */
        float drift = (float)fmod(time * FOG_DRIFT, (double)(FOG_LAYER.width * PX));
        if (fog)
            draw_layer(renderer, fog, &FOG_LAYER, camera_x * FOG_LAYER.parallax + drift);
    }
}

void scene_draw(SDL_Renderer *renderer, const World *world, float camera_x, double time)
{
    scene_draw_distant(renderer, world, camera_x);
    scene_draw_near(renderer, world, camera_x, time);
}

bool scene_begin_foreground(SDL_Renderer *renderer)
{
    if (!renderer || foreground_active || !SDL_RenderTargetSupported(renderer))
        return false;
    /* As large as what it is drawn over: the view's own texture, or the window. */
    int out_w = WINDOW_WIDTH, out_h = WINDOW_HEIGHT;
    SDL_GetRendererOutputSize(renderer, &out_w, &out_h);
    if (foreground_renderer != renderer || !foreground || out_w != foreground_w || out_h != foreground_h) {
        if (foreground)
            SDL_DestroyTexture(foreground);
        foreground = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_RGBA8888,
                                       SDL_TEXTUREACCESS_TARGET, out_w, out_h);
        foreground_renderer = renderer;
        foreground_w = out_w;
        foreground_h = out_h;
        if (!foreground)
            return false;
        SDL_SetTextureBlendMode(foreground, SDL_BLENDMODE_BLEND);
    }
    previous_target = SDL_GetRenderTarget(renderer);
    SDL_RenderGetViewport(renderer, &previous_viewport);
    SDL_RenderGetScale(renderer, &previous_scale_x, &previous_scale_y);
    Uint8 r, g, b, a;
    SDL_GetRenderDrawColor(renderer, &r, &g, &b, &a);
    if (SDL_SetRenderTarget(renderer, foreground) != 0)
        return false;
    SDL_RenderSetScale(renderer, 1.0f, 1.0f);
    SDL_RenderSetViewport(renderer, NULL);
    SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0);
    SDL_RenderClear(renderer);
    SDL_SetRenderDrawColor(renderer, r, g, b, a);
    SDL_RenderSetScale(renderer, previous_scale_x, previous_scale_y);
    SDL_RenderSetViewport(renderer, &previous_viewport);
    foreground_active = true;
    return true;
}

void scene_end_foreground(SDL_Renderer *renderer)
{
    if (!foreground_active || renderer != foreground_renderer)
        return;
    SDL_SetRenderTarget(renderer, previous_target);
    SDL_RenderSetScale(renderer, 1.0f, 1.0f);
    SDL_RenderSetViewport(renderer, NULL);
    SDL_RenderCopy(renderer, foreground, NULL, NULL); /* The same size: over all of it */
    SDL_RenderSetScale(renderer, previous_scale_x, previous_scale_y);
    SDL_RenderSetViewport(renderer, &previous_viewport);
    foreground_active = false;
}
