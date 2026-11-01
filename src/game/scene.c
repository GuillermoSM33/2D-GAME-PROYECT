#include "game/scene.h"

#include <math.h>
#include <stdio.h>

#include "config.h"
#include "engine/assets.h"
#include "engine/platform.h"

/* Background layers and props are pixel art at the sprites' scale. */
#define PX SPRITE_SCALE

/* The props' sheets in the current theme's colors: the embedded ones for the
 * sunset, palette-swapped copies for the others (made when the theme changes). */
static const ThemeDef *props_theme;
static SDL_Texture *themed_props[PROP_KIND_COUNT];
static bool themed_owned; /* The copies are ours to destroy */

static void release_props(void)
{
    for (int k = 0; k < PROP_KIND_COUNT; k++) {
        if (themed_owned && themed_props[k])
            SDL_DestroyTexture(themed_props[k]);
        themed_props[k] = NULL;
    }
    themed_owned = false;
    props_theme = NULL;
}

static void prepare_props(SDL_Renderer *renderer, const ThemeDef *theme)
{
    if (props_theme == theme)
        return;
    release_props();
    themed_owned = theme->prop_recolor_count > 0;
    for (int k = 0; k < PROP_KIND_COUNT; k++) {
        const char *sheet = prop_def(k)->sheet;
        themed_props[k] = themed_owned
                              ? assets_texture_recolored(renderer, sheet, theme->prop_recolor,
                                                         theme->prop_recolor_count)
                              : assets_texture(sheet);
    }
    props_theme = theme;
}

void scene_shutdown(void)
{
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
        return;
    }
    /* Leftmost tile: where the scrolled strip starts, wrapped into [-w, 0). */
    int x = -(int)lroundf(fmodf(offset, (float)w));
    for (; x < WINDOW_WIDTH; x += w) {
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
        if (screen_x > WINDOW_WIDTH || screen_x + WORLD_CHUNK_W < 0.0f)
            continue; /* Loaded ahead, not on screen yet (props stay inside their chunk) */
        for (int p = 0; p < chunk->prop_count; p++)
            draw_prop(renderer, &chunk->props[p], screen_x);
    }
}

void scene_draw(SDL_Renderer *renderer, const World *world, float camera_x, double time)
{
    const ThemeDef *theme = world->theme;
    prepare_props(renderer, theme);
    platform_set_color(renderer, COLOR_BACKGROUND);
    SDL_RenderClear(renderer);

    /* Back to front; the props stand between the hills and the ground. */
    for (int i = 0; i < BACKGROUND_LAYER_COUNT; i++) {
        const BackgroundLayer *layer = &BACKGROUND_LAYERS[i];
        if (i == BACKGROUND_LAYER_COUNT - 1)
            draw_props(renderer, world, camera_x);
        SDL_Texture *texture = layer_texture(theme, layer);
        if (texture)
            draw_layer(renderer, texture, layer, camera_x * layer->parallax);
    }
    if (theme->fog) {
        SDL_Texture *fog = layer_texture(theme, &FOG_LAYER);
        /* Wrapped to one tile's worth of drift, so a long session keeps float precision. */
        float drift = (float)fmod(time * FOG_DRIFT, (double)(FOG_LAYER.width * PX));
        if (fog)
            draw_layer(renderer, fog, &FOG_LAYER, camera_x * FOG_LAYER.parallax + drift);
    }
}
