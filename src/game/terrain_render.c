#include "game/terrain_render.h"

#include <math.h>

#include "config.h"
#include "engine/assets.h"

static void draw_sunk(SDL_Renderer *renderer, const char *sheet_name, int frame, int w, int h, float x,
                      float camera_x, int sink)
{
    SDL_Texture *sheet = assets_texture(sheet_name);
    float left = x - camera_x - (float)(w * SPRITE_SCALE) / 2.0f;
    if (sheet == NULL || left > VIEW_WIDTH || left + (float)(w * SPRITE_SCALE) < 0.0f)
        return;
    SDL_Rect src = {frame * w, 0, w, h};
    /* Its last row on the ground line, like the props. */
    SDL_Rect dst = {(int)lroundf(left), (GROUND_ROW + sink - h) * SPRITE_SCALE, w * SPRITE_SCALE,
                    h * SPRITE_SCALE};
    SDL_RenderCopy(renderer, sheet, &src, &dst);
}

/* Its last row on the ground line, like the props. */
static void draw(SDL_Renderer *renderer, const char *sheet_name, int frame, int w, int h, float x,
                 float camera_x)
{
    draw_sunk(renderer, sheet_name, frame, w, h, x, camera_x, 0);
}

static bool water(const Piece *p)
{
    return p->kind == TERRAIN_RIVER || p->kind == TERRAIN_PUDDLE;
}

void terrain_render_front(SDL_Renderer *renderer, const Terrain *terrain, float camera_x)
{
    SDL_Texture *front = assets_texture("sprites/terrain/river_front");
    if (front == NULL)
        return;
    SDL_SetTextureAlphaMod(front, 210);
    for (int i = 0; i < terrain->count; i++) {
        const Piece *p = &terrain->items[i];
        if (p->kind != TERRAIN_RIVER)
            continue;
        /* The surface rows of the river (its rows 2-4), over the ankles in it. */
        int top = GROUND_ROW + RIVER_SINK - RIVER_FRAME_H + 2;
        draw_sunk(renderer, "sprites/terrain/river_front", terrain_frame(p), RIVER_FRAME_W, RIVER_FRONT_H,
                  p->x, camera_x, top + RIVER_FRONT_H - GROUND_ROW);
    }
    SDL_SetTextureAlphaMod(front, 255);
}

void terrain_render(SDL_Renderer *renderer, const Terrain *terrain, float camera_x)
{
    for (int i = 0; i < terrain->count; i++) { /* Behind everything: what a wall closes, water */
        const Piece *p = &terrain->items[i];
        if (water(p)) {
            int w, h, frames;
            terrain_frame_size(p->kind, &w, &h, &frames);
            draw_sunk(renderer, terrain_sheet(p->kind), terrain_frame(p), w, h, p->x, camera_x,
                      terrain_sink(p->kind));
            continue;
        }
        if (p->kind != TERRAIN_WALL)
            continue;
        if (p->variant > 0)
            draw(renderer, terrain_facade_sheet(), p->variant - 1, FACADE_W, FACADE_H, p->x, camera_x);
        else
            draw(renderer, terrain_ruins_sheet(), 0, WALL_RUINS_W, WALL_RUINS_H, p->x, camera_x);
    }
    for (int i = 0; i < terrain->count; i++) {
        const Piece *p = &terrain->items[i];
        bool gone = p->spent && (p->kind == TERRAIN_BARREL || p->kind == TERRAIN_DYNAMITE ||
                                 p->kind == TERRAIN_FIRE || p->kind == TERRAIN_CHARGE);
        if (gone || water(p))
            continue;
        int w, h, frames;
        terrain_frame_size(p->kind, &w, &h, &frames);
        if (p->kind == TERRAIN_WALL && p->variant > 0) /* A building's door in its doorway */
            draw(renderer, terrain_door_sheet(), terrain_frame(p), DOOR_FRAME_W, DOOR_FRAME_H, p->x, camera_x);
        else
            draw(renderer, terrain_sheet(p->kind), terrain_frame(p), w, h, p->x, camera_x);
        if (p->fuse > 0.0f && p->kind != TERRAIN_CHARGE) { /* The lit charge at its foot, sparking */
            int spark = (int)(p->fuse * 10.0f) % 2;
            draw(renderer, terrain_charge_sheet(), spark, CHARGE_FRAME_W, CHARGE_FRAME_H, p->x, camera_x);
        }
    }
}

void terrain_render_lights(SDL_Renderer *renderer, const Terrain *terrain, float camera_x, double time)
{
    SDL_Texture *glow = assets_texture("sprites/effects/glow");
    if (glow == NULL)
        return;
    float xs[TERRAIN_MAX], sizes[TERRAIN_MAX];
    int n = terrain_lights(terrain, xs, sizes, TERRAIN_MAX);
    SDL_SetTextureBlendMode(glow, SDL_BLENDMODE_ADD);
    for (int i = 0; i < n; i++) {
        /* A flame's flicker: two slow waves, a little different per light. */
        float flicker = 0.85f + 0.1f * (float)sin(time * 7.0 + xs[i] * 0.01) +
                        0.05f * (float)sin(time * 13.0 + xs[i] * 0.03);
        int size = (int)(sizes[i] * flicker);
        SDL_Rect dst = {(int)lroundf(xs[i] - camera_x) - size / 2, BASELINE - size * 2 / 3, size, size};
        SDL_SetTextureAlphaMod(glow, (Uint8)(150.0f * flicker));
        SDL_RenderCopy(renderer, glow, NULL, &dst);
    }
    SDL_SetTextureAlphaMod(glow, 255);
}
