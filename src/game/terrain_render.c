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
        if (p->variant == FACADE_TRAIN)
            draw(renderer, terrain_train_sheet(), 0, TRAIN_W, TRAIN_H, p->x, camera_x);
        else if (p->variant > FACADE_KINDS) /* The town's fronts: two storeys at her scale */
            draw(renderer, terrain_city_front_sheet(), p->variant - FACADE_KINDS - 1, CITY_FRONT_W, CITY_FRONT_H,
                 p->x, camera_x);
        else if (p->variant > 0)
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
            draw(renderer, terrain_door_sheet(), terrain_door_look(p) * 3 + terrain_frame(p), DOOR_FRAME_W,
                 DOOR_FRAME_H, p->x, camera_x);
        else if (terrain_car_look(p) >= 0) /* A car, a car's size: its look's three states */
            draw(renderer, terrain_car_wreck_sheet(), terrain_frame(p), CAR_WRECK_W, CAR_WRECK_H, p->x, camera_x);
        else if (p->kind == TERRAIN_SUPPLY && p->variant == 1) /* The town's: an army truck */
            draw(renderer, terrain_supply_truck_sheet(), terrain_frame(p), VEHICLE_FRAME_W, VEHICLE_FRAME_H, p->x,
                 camera_x);
        else
            draw(renderer, terrain_sheet(p->kind), terrain_frame(p), w, h, p->x, camera_x);
        if (terrain_hydrant_jetting(p)) /* Its water shooting up out of it */
            draw(renderer, "sprites/effects/hydrant_jet", (int)(p->timer * JET_FPS) % 4, JET_FRAME_W, JET_FRAME_H,
                 p->x, camera_x);
        if (p->fuse > 0.0f && p->kind != TERRAIN_CHARGE) { /* The lit charge at its foot, sparking */
            int spark = (int)(p->fuse * 10.0f) % 2;
            draw(renderer, terrain_charge_sheet(), spark, CHARGE_FRAME_W, CHARGE_FRAME_H, p->x, camera_x);
        }
    }
}

#define LIGHT_W (VIEW_WIDTH / SPRITE_SCALE)
#define LIGHT_H (VIEW_HEIGHT / SPRITE_SCALE)
static SDL_Texture *light_mask;
static SDL_Renderer *light_renderer;
static Uint32 light_pixels[LIGHT_W * LIGHT_H];
static SDL_Texture *beam_mask;
static SDL_Texture *surface_mask;
static float beam_values[LIGHT_W * LIGHT_H];

void terrain_render_shutdown(void)
{
    if (light_mask)
        SDL_DestroyTexture(light_mask);
    light_mask = NULL;
    if (beam_mask)
        SDL_DestroyTexture(beam_mask);
    beam_mask = NULL;
    if (surface_mask)
        SDL_DestroyTexture(surface_mask);
    surface_mask = NULL;
    light_renderer = NULL;
}

static void draw_shadow(SDL_Renderer *renderer, const Lighting *lighting, float foot_x,
                         float height, float half_width, float camera_x)
{
    const WorldLight *strongest = NULL;
    float best = .025f;
    for (int i = 0; i < lighting->count; i++) {
        const WorldLight *light = &lighting->lights[i];
        float value = lighting_strength_at(lighting, light, foot_x, BASELINE - height * .5f);
        if (value > best) { best = value; strongest = light; }
    }
    GroundShadow shadow;
    if (!strongest || !lighting_ground_shadow(strongest, foot_x, height, half_width, &shadow))
        return;
    int rows = (int)ceilf(shadow.depth / SPRITE_SCALE);
    for (int row = 0; row < rows; row++) {
        float t = (float)row / (float)rows;
        float center = shadow.near_x + (shadow.far_x - shadow.near_x) * t - camera_x;
        float half = shadow.half_width + (shadow.far_half_width - shadow.half_width) * t;
        Uint8 alpha = (Uint8)lroundf(shadow.opacity * (1.0f - t) * (1.0f - t) * 255.0f);
        SDL_SetRenderDrawColor(renderer, 12, 9, 15, alpha);
        SDL_Rect stripe = {(int)lroundf(center - half), BASELINE + row * SPRITE_SCALE + 2,
                           (int)lroundf(half * 2.0f), SPRITE_SCALE};
        SDL_RenderFillRect(renderer, &stripe);
    }
}

/* What its light falls on, in art-sized steps; stops at what blocks it. */
static void measure_beam(const Lighting *lighting, const WorldLight *light, float camera_x)
{
    for (int y = 0; y < LIGHT_H; y++)
        for (int x = 0; x < LIGHT_W; x++)
            beam_values[y * LIGHT_W + x] =
                floorf(fminf(1.0f, lighting_strength_at(lighting, light, camera_x + x * SPRITE_SCALE + SPRITE_SCALE / 2.0f,
                                                        y * SPRITE_SCALE + SPRITE_SCALE / 2.0f)) * 14.0f) / 14.0f;
}

static void beam_to_pixels(float gain)
{
    for (int i = 0; i < LIGHT_W * LIGHT_H; i++) {
        float v = fminf(1.0f, beam_values[i] * gain);
        light_pixels[i] = 0xff000000u | ((Uint32)lroundf(v * 255.0f) << 16) |
                          ((Uint32)lroundf(v * 232.0f) << 8) | (Uint32)lroundf(v * 168.0f);
    }
}

static SDL_Texture *beam_texture(SDL_Renderer *renderer, SDL_Texture **texture)
{
    if (light_renderer != renderer) {
        terrain_render_shutdown();
        light_renderer = renderer;
    }
    if (!*texture)
        *texture = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_STREAMING,
                                     LIGHT_W, LIGHT_H);
    return *texture;
}

/* Lighting up what it falls on: each pixel of the road, the props and the
 * bodies brighter by its own colour, the way a light does. Nothing where
 * there is nothing, so only solid things show it. */
static void light_surfaces(SDL_Renderer *renderer, const Lighting *lighting, const WorldLight *light, float camera_x)
{
    SDL_Texture *mask = beam_texture(renderer, &surface_mask);
    if (!mask)
        return;
    SDL_BlendMode brighten = SDL_ComposeCustomBlendMode(SDL_BLENDFACTOR_DST_COLOR, SDL_BLENDFACTOR_ONE, SDL_BLENDOPERATION_ADD,
                                                        SDL_BLENDFACTOR_ZERO, SDL_BLENDFACTOR_ONE, SDL_BLENDOPERATION_ADD);
    if (SDL_SetTextureBlendMode(mask, brighten) != 0)
        SDL_SetTextureBlendMode(mask, SDL_BLENDMODE_ADD); /* A renderer without it: a plain glow */
    measure_beam(lighting, light, camera_x);
    beam_to_pixels(1.5f);
    SDL_UpdateTexture(mask, NULL, light_pixels, LIGHT_W * sizeof(Uint32));
    SDL_Rect dst = {0, 0, VIEW_WIDTH, VIEW_HEIGHT};
    SDL_RenderCopy(renderer, mask, NULL, &dst);
}

void terrain_render_surface_lights(SDL_Renderer *renderer, const Lighting *lighting,
                            const Player *player, const Zombie *zombies, int zombie_count,
                            float camera_x)
{
    if (!renderer || !lighting)
        return;
    Uint8 old_r, old_g, old_b, old_a;
    SDL_BlendMode old_mode;
    SDL_GetRenderDrawColor(renderer, &old_r, &old_g, &old_b, &old_a);
    SDL_GetRenderDrawBlendMode(renderer, &old_mode);
    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
    if (lighting->night) {
        if (player && player_alive(player))
            draw_shadow(renderer, lighting, player->x, PLAYER_HEAD_HEIGHT * SPRITE_SCALE,
                        PLAYER_BODY_HALF_WIDTH * .75f, camera_x);
        for (int i = 0; zombies && i < zombie_count; i++) {
            const Zombie *z = &zombies[i];
            if (zombie_alive(z) && !z->hidden && z->caught <= 0.0f &&
                z->x > camera_x - 180.0f && z->x < camera_x + VIEW_WIDTH + 180.0f)
                draw_shadow(renderer, lighting, z->x, zombie_body_height(z),
                            zombie_body_half_width(z) * .70f, camera_x);
        }
        if (light_renderer != renderer) {
            terrain_render_shutdown();
            light_renderer = renderer;
        }
        if (!light_mask) {
            light_mask = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ARGB8888,
                                          SDL_TEXTUREACCESS_STREAMING, LIGHT_W, LIGHT_H);
            if (light_mask)
                SDL_SetTextureBlendMode(light_mask, SDL_BLENDMODE_MOD);
        }
        if (light_mask) {
            for (int y = 0; y < LIGHT_H; y++)
                for (int x = 0; x < LIGHT_W; x++)
                    light_pixels[y * LIGHT_W + x] = 0xff000000u |
                        lighting_color_at(lighting, camera_x + x * SPRITE_SCALE + SPRITE_SCALE / 2.0f,
                                          y * SPRITE_SCALE + SPRITE_SCALE / 2.0f);
            SDL_UpdateTexture(light_mask, NULL, light_pixels, LIGHT_W * sizeof(Uint32));
            SDL_Rect dst = {0, 0, VIEW_WIDTH, VIEW_HEIGHT};
            SDL_RenderCopy(renderer, light_mask, NULL, &dst);
        }
    }
    for (int i = 0; i < lighting->count; i++)
        if (lighting->lights[i].kind == LIGHT_FLASHLIGHT && lighting->lights[i].strength > .01f)
            light_surfaces(renderer, lighting, &lighting->lights[i], camera_x);
    SDL_SetRenderDrawColor(renderer, old_r, old_g, old_b, old_a);
    SDL_SetRenderDrawBlendMode(renderer, old_mode);
}

/* The beam itself, in the air: faint, as light in dust is, with a few motes
 * drifting in it and the glare of the lens. */
static void draw_beam(SDL_Renderer *renderer, const Lighting *lighting, const WorldLight *light, float camera_x)
{
    SDL_Texture *mask = beam_texture(renderer, &beam_mask);
    if (!mask)
        return;
    SDL_SetTextureBlendMode(mask, SDL_BLENDMODE_ADD);
    /* Another light or the surface pass may have used the shared scratch
     * pixels. Always measure this beam, including standalone bloom calls. */
    measure_beam(lighting, light, camera_x);
    beam_to_pixels(lighting->night ? .26f : .2f);
    float c = cosf(light->tilt), s = sinf(light->tilt);
    for (int i = 0; i < 16; i++) { /* Dust, drifting out along the beam */
        float t = (float)fmod(lighting->time * (.035 + .012 * (i % 3)) + i * .618, 1.0);
        float along = 50.0f + t * light->radius * .8f;
        float across = (float)sin(lighting->time * .7 + i * 2.4) * (8.0f + along * .2f);
        float wx = light->x + (float)light->direction * (along * c - across * s);
        float wy = light->y + along * s + across * c;
        float bright = lighting_strength_at(lighting, light, wx, wy);
        int px = (int)((wx - camera_x) / SPRITE_SCALE), py = (int)(wy / SPRITE_SCALE);
        if (bright > .03f && px >= 0 && px < LIGHT_W && py >= 0 && py < LIGHT_H) {
            Uint32 add = (Uint32)fminf(140.0f, 60.0f + bright * 300.0f);
            light_pixels[py * LIGHT_W + px] = 0xff000000u | (add << 16) | (add << 8) | (add * 3 / 4);
        }
    }
    SDL_UpdateTexture(mask, NULL, light_pixels, LIGHT_W * sizeof(Uint32));
    SDL_Rect dst = {0, 0, VIEW_WIDTH, VIEW_HEIGHT};
    SDL_RenderCopy(renderer, mask, NULL, &dst);
    SDL_Texture *glow = assets_texture("sprites/effects/glow");
    if (glow) {
        Uint8 alpha, red, green, blue;
        SDL_BlendMode blend;
        SDL_GetTextureAlphaMod(glow, &alpha);
        SDL_GetTextureColorMod(glow, &red, &green, &blue);
        SDL_GetTextureBlendMode(glow, &blend);
        SDL_SetTextureBlendMode(glow, SDL_BLENDMODE_ADD);
        SDL_SetTextureColorMod(glow, 255, 236, 180);
        SDL_SetTextureAlphaMod(glow, (Uint8)fminf(255.0f, 190.0f * light->strength));
        int size = (int)(58.0f + 8.0f * light->strength);
        SDL_Rect lens = {(int)lroundf(light->x - camera_x) - size / 2, (int)lroundf(light->y) - size / 2, size, size};
        SDL_RenderCopy(renderer, glow, NULL, &lens);
        SDL_SetTextureAlphaMod(glow, alpha);
        SDL_SetTextureColorMod(glow, red, green, blue);
        SDL_SetTextureBlendMode(glow, blend);
    }
}

void terrain_render_light_bloom(SDL_Renderer *renderer, const Lighting *lighting, float camera_x)
{
    if (!renderer || !lighting)
        return;
    for (int i = 0; i < lighting->count; i++)
        if (lighting->lights[i].kind == LIGHT_FLASHLIGHT && lighting->lights[i].strength > .01f)
            draw_beam(renderer, lighting, &lighting->lights[i], camera_x);
    SDL_Texture *glow = assets_texture("sprites/effects/glow");
    if (glow) {
        Uint8 alpha, red, green, blue;
        SDL_BlendMode blend;
        SDL_GetTextureAlphaMod(glow, &alpha);
        SDL_GetTextureColorMod(glow, &red, &green, &blue);
        SDL_GetTextureBlendMode(glow, &blend);
        SDL_SetTextureBlendMode(glow, SDL_BLENDMODE_ADD);
        SDL_SetTextureColorMod(glow, 255, 172, 77);
        for (int i = 0; i < lighting->count; i++) {
            const WorldLight *light = &lighting->lights[i];
            if (light->kind == LIGHT_FLASHLIGHT)
                continue; /* Its cone is drawn by draw_beam. */
            float size = light->kind == LIGHT_EXPLOSION ? light->radius * .70f : light->radius * .45f;
            SDL_Rect halo = {(int)lroundf(light->x - camera_x - size * .5f),
                             (int)lroundf(light->y - size * .5f), (int)size, (int)size};
            SDL_SetTextureAlphaMod(glow, (Uint8)fminf(100.0f,
                (lighting->night ? 53.0f : 15.0f) * light->strength));
            SDL_RenderCopy(renderer, glow, NULL, &halo);
            /* The lit ground is an ellipse in perspective, centred under
             * the source, not another upright glowing ball. */
            float width = light->radius * 1.4f;
            SDL_Rect pool = {(int)lroundf(light->x - camera_x - width * .5f), BASELINE - 15,
                             (int)width, 48};
            SDL_SetTextureAlphaMod(glow, (Uint8)fminf(45.0f,
                (lighting->night ? 26.0f : 7.0f) * light->strength));
            SDL_RenderCopy(renderer, glow, NULL, &pool);
        }
        SDL_SetTextureAlphaMod(glow, alpha);
        SDL_SetTextureColorMod(glow, red, green, blue);
        SDL_SetTextureBlendMode(glow, blend);
    }
}

void terrain_render_lights(SDL_Renderer *renderer, const Lighting *lighting,
                            const Player *player, const Zombie *zombies, int zombie_count,
                            float camera_x)
{
    terrain_render_surface_lights(renderer, lighting, player, zombies, zombie_count, camera_x);
    terrain_render_light_bloom(renderer, lighting, camera_x);
}
