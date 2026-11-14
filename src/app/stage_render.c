#include <math.h>
#include <stdio.h>

#include "app/stage_render.h"
#include "app/stage.h"
#include "engine/assets.h"
#include "game/bullet_render.h"
#include "game/camera.h"
#include "game/chest_render.h"
#include "game/effects_render.h"
#include "game/hud.h"
#include "game/player_render.h"
#include "game/scene.h"
#include "game/smoke_render.h"
#include "game/terrain_render.h"
#include "game/ui.h"
#include "game/weather_render.h"
#include "game/zombie_render.h"

/* Rendering runs at the display's rate and the simulation at a fixed 60 Hz, so
 * a frame often falls between two steps (or gets two, or none). Drawing where
 * things were a fraction alpha of the way from the previous step to the last
 * one keeps motion even; without it the whole scrolling view stutters. */
#define TELEPORT_DISTANCE 100.0f /* px in one step: a reset or respawn, not motion */

static float interpolate(float before, float after, float alpha)
{
    if (fabsf(after - before) > TELEPORT_DISTANCE)
        return after;
    return before + (after - before) * alpha;
}

/* The world is drawn at its own size (VIEW_WIDTH x VIEW_HEIGHT, whole px
 * wherever a thing stands) into a texture, and that is copied into the window
 * at VIEW_SCALE. Scaling each sprite on its own would put half of them on
 * half pixels, their columns uneven as they move. */
static SDL_Texture *view_target;
static SDL_Renderer *view_renderer;
static SDL_Texture *view_parent;
static bool view_active;

void stage_render_shutdown(void)
{
    if (view_active && view_renderer)
        SDL_SetRenderTarget(view_renderer, view_parent);
    if (view_target)
        SDL_DestroyTexture(view_target);
    view_target = NULL;
    view_renderer = NULL;
    view_active = false;
}

void stage_begin_view(SDL_Renderer *renderer, const ThemeDef *theme)
{
    platform_set_color(renderer, scene_sky_top(theme));
    SDL_RenderClear(renderer);
    if (view_renderer != renderer)
        stage_render_shutdown();
    view_renderer = renderer;
    if (view_target == NULL && SDL_RenderTargetSupported(renderer)) {
        view_target = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_RGBA8888, SDL_TEXTUREACCESS_TARGET,
                                        VIEW_WIDTH, VIEW_HEIGHT);
        if (view_target) {
            SDL_SetTextureBlendMode(view_target, SDL_BLENDMODE_NONE);
            SDL_SetTextureScaleMode(view_target, SDL_ScaleModeNearest);
        }
    }
    view_parent = SDL_GetRenderTarget(renderer);
    if (view_target && SDL_SetRenderTarget(renderer, view_target) == 0) {
        view_active = true;
        SDL_RenderSetScale(renderer, 1.0f, 1.0f);
        SDL_RenderSetViewport(renderer, NULL);
        SDL_RenderClear(renderer);
        return;
    }
    /* No render targets here: scaled straight into the window. */
    SDL_RenderSetScale(renderer, VIEW_SCALE, VIEW_SCALE);
    SDL_Rect view = {0, (int)(VIEW_TOP / VIEW_SCALE), VIEW_WIDTH, VIEW_HEIGHT};
    SDL_RenderSetViewport(renderer, &view);
}

void stage_end_view(SDL_Renderer *renderer)
{
    SDL_RenderSetViewport(renderer, NULL);
    SDL_RenderSetScale(renderer, 1.0f, 1.0f);
    if (!view_active)
        return;
    view_active = false;
    SDL_SetRenderTarget(renderer, view_parent);
    SDL_RenderSetViewport(renderer, NULL);
    SDL_RenderSetScale(renderer, 1.0f, 1.0f);
    /* A quarter of a window px up and left: each window px then reads the
     * middle of one world px, never the line between two. */
    SDL_FRect window = {-0.25f, (float)VIEW_TOP - 0.25f, VIEW_WIDTH * VIEW_SCALE, VIEW_HEIGHT * VIEW_SCALE};
    SDL_RenderCopyF(renderer, view_target, NULL, &window);
}

/* Her trail of blood on the road (effects/blood), each drop fading as it dries. */
static void draw_blood(SDL_Renderer *renderer, const StagePlay *play, float camera_x)
{
    SDL_Texture *sheet = assets_texture("sprites/effects/blood");
    if (sheet == NULL)
        return;
    for (int d = 0; d < BLOOD_DROPS; d++) {
        float age = play->blood_age[d];
        if (age >= BLOOD_LIFE)
            continue;
        SDL_Rect src = {(d % 4) * 8, 0, 8, 4};
        SDL_Rect dst = {(int)lroundf(play->blood_x[d] - camera_x) - 4 * SPRITE_SCALE,
                        BASELINE - 3 * SPRITE_SCALE, 8 * SPRITE_SCALE, 4 * SPRITE_SCALE};
        float left = 1.0f - age / BLOOD_LIFE;
        SDL_SetTextureAlphaMod(sheet, (Uint8)(255.0f * fminf(1.0f, left * 2.0f)));
        SDL_RenderCopy(renderer, sheet, &src, &dst);
    }
    SDL_SetTextureAlphaMod(sheet, 255);
}

/* Heat haze over a hot road: pale wavering streaks rising off the ground,
 * drifting with the view, in whole art px. */
void stage_draw_heat(SDL_Renderer *renderer, float camera_x, double time)
{
    const int px = SPRITE_SCALE;
    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
    for (int row = 0; row < 5; row++) {
        int y = BASELINE - 2 * px - row * 2 * px;
        float t = (float)time * 2.2f + (float)row * 0.9f;
        Uint8 alpha = (Uint8)(16 - row * 2);
        SDL_SetRenderDrawColor(renderer, 0xff, 0xec, 0xc8, alpha);
        for (int i = 0; i < 5; i++) {
            /* Streaks spaced along the road, each wobbling sideways. */
            float world = (float)(i * 290 + row * 61) - fmodf(camera_x * 0.9f, 290.0f * 5.0f);
            int x = (int)lroundf((world + sinf(t + (float)i * 1.7f) * 3.0f * px) / px) * px;
            x = ((x % (VIEW_WIDTH + 200)) + VIEW_WIDTH + 200) % (VIEW_WIDTH + 200) - 100;
            int len = (2 + (i * 5 + row) % 4) * px;
            SDL_Rect r = {x, y + (int)lroundf(sinf(t * 1.3f + (float)i)) * px, len, px};
            SDL_RenderFillRect(renderer, &r);
        }
    }
}

/* A heatstroke (her fatigue past FATIGUE_STROKE): the view swims, warm and
 * blurred, more the closer she is to fainting, the edges going dark. */
static void draw_heatstroke(SDL_Renderer *renderer, float fatigue, double time)
{
    if (fatigue < FATIGUE_STROKE)
        return;
    float k = fminf(1.0f, (fatigue - FATIGUE_STROKE) / (FATIGUE_FAINT - FATIGUE_STROKE));
    const int px = SPRITE_SCALE;
    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
    /* Blur: rows of the view smeared sideways by pale wavering bands. */
    for (int y = 0; y < VIEW_HEIGHT; y += 2 * px) {
        float wave = sinf((float)time * 3.0f + (float)y * 0.05f);
        SDL_SetRenderDrawColor(renderer, 0xff, 0xd8, 0xa8, (Uint8)lroundf((30.0f + 40.0f * k) * (0.5f + 0.5f * wave)));
        SDL_Rect band = {(int)lroundf(wave * 6.0f * px), y, VIEW_WIDTH, px};
        SDL_RenderFillRect(renderer, &band);
    }
    SDL_SetRenderDrawColor(renderer, 0xff, 0x90, 0x40, (Uint8)lroundf(30.0f + 50.0f * k));
    SDL_Rect all = {0, 0, VIEW_WIDTH, VIEW_HEIGHT};
    SDL_RenderFillRect(renderer, &all);
    for (int i = 0; i < 6; i++) { /* The edges darkening in */
        int edge = (i + 1) * 3 * px;
        SDL_SetRenderDrawColor(renderer, 0x20, 0x08, 0x00, (Uint8)lroundf((20.0f + 25.0f * k) * (6 - i) / 6.0f));
        SDL_Rect l = {0, 0, edge, VIEW_HEIGHT}, r = {VIEW_WIDTH - edge, 0, edge, VIEW_HEIGHT};
        SDL_Rect t = {0, 0, VIEW_WIDTH, edge}, b = {0, VIEW_HEIGHT - edge, VIEW_WIDTH, edge};
        SDL_RenderFillRect(renderer, &l);
        SDL_RenderFillRect(renderer, &r);
        SDL_RenderFillRect(renderer, &t);
        SDL_RenderFillRect(renderer, &b);
    }
}

/* Zombies that aren't there: pale, see-through and flickering, walking. */
static void draw_phantoms(SDL_Renderer *renderer, const Hallucination *h, float camera_x, double time)
{
    const AnimationDef *def = zombie_walk_animation();
    SDL_Texture *sheet = assets_texture(def->sheet);
    if (sheet == NULL)
        return;
    for (int i = 0; i < PHANTOMS_MAX; i++) {
        const Phantom *p = &h->phantoms[i];
        if (!p->active)
            continue;
        bool left = p->facing < 0;
        float anchor_x = left ? (float)def->frame_w - def->anchor_x : def->anchor_x;
        int frame = (int)(p->time * def->fps) % def->frame_count;
        SDL_Rect src = {frame * def->frame_w, 0, def->frame_w, def->frame_h};
        SDL_Rect dst = {(int)lroundf(p->x - camera_x - anchor_x * SPRITE_SCALE),
                        BASELINE - def->ground_y * SPRITE_SCALE, def->frame_w * SPRITE_SCALE,
                        def->frame_h * SPRITE_SCALE};
        float flicker = 0.75f + 0.25f * sinf((float)time * 13.0f + (float)i * 2.0f);
        SDL_SetTextureColorMod(sheet, 200, 230, 210);
        SDL_SetTextureAlphaMod(sheet, (Uint8)lroundf(140.0f * p->fade * flicker));
        SDL_RenderCopyEx(renderer, sheet, &src, &dst, 0.0, NULL, left ? SDL_FLIP_HORIZONTAL : SDL_FLIP_NONE);
    }
    SDL_SetTextureColorMod(sheet, 255, 255, 255);
    SDL_SetTextureAlphaMod(sheet, 255);
}

/* The crows: pecking on the road, flapping off up and away, or dead. */
static void draw_crows(SDL_Renderer *renderer, const Crows *crows, float camera_x, bool sparrows)
{
    /* In the town they are sparrows: the same frames, their own sheet. */
    SDL_Texture *sheet = assets_texture(sparrows ? "sprites/sparrow/sparrow" : "sprites/crow/crow");
    if (sheet == NULL)
        return;
    for (int i = 0; i < crows->count; i++) {
        const Crow *c = &crows->items[i];
        if (c->gone)
            continue;
        SDL_Rect src = {crow_frame(c) * CROW_FRAME_W, 0, CROW_FRAME_W, CROW_FRAME_H};
        SDL_Rect dst = {(int)lroundf(c->x - camera_x) - CROW_FRAME_W * SPRITE_SCALE / 2,
                        BASELINE - (int)lroundf(c->height) - CROW_FRAME_H * SPRITE_SCALE,
                        CROW_FRAME_W * SPRITE_SCALE, CROW_FRAME_H * SPRITE_SCALE};
        SDL_SetTextureAlphaMod(sheet, (Uint8)lroundf(crow_opacity(c) * 255.0f));
        SDL_RenderCopyEx(renderer, sheet, &src, &dst, 0.0, NULL,
                         c->facing < 0 ? SDL_FLIP_HORIZONTAL : SDL_FLIP_NONE);
    }
    SDL_SetTextureAlphaMod(sheet, 255);
}

/* A storm's lightning: the ground crackling where it will come down, then
 * the bolt itself, jagged from the top of the view, in whole art px. */
static void draw_lightning(SDL_Renderer *renderer, const StageRun *run, float camera_x, double now)
{
    const int px = SPRITE_SCALE;
    int x0 = (int)lroundf(run->bolt_x - camera_x) / px * px;
    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
    if (run->bolt_warn > 0.0f) { /* Sparks jumping off the road, quicker as it nears */
        unsigned h = (unsigned)(now * (14.0 + 30.0 * (1.0 - run->bolt_warn / LIGHTNING_WARN)));
        for (int i = 0; i < 7; i++) {
            h = h * 1103515245u + 12345u;
            int dx = (int)((h >> 16) % 13u) - 6, dy = (int)((h >> 8) % 9u);
            SDL_SetRenderDrawColor(renderer, i % 2 ? 0xd8 : 0xff, i % 2 ? 0xe8 : 0xff, 0xff, 230);
            SDL_Rect r = {x0 + dx * px, BASELINE - (dy + 1) * px, px, px};
            SDL_RenderFillRect(renderer, &r);
        }
        SDL_SetRenderDrawColor(renderer, 0x9c, 0xc8, 0xff, 70); /* A glow on the ground */
        SDL_Rect glow = {x0 - 10 * px, BASELINE - 2 * px, 21 * px, 2 * px};
        SDL_RenderFillRect(renderer, &glow);
    }
    if (run->bolt_show > 0.0f) {
        Uint8 alpha = (Uint8)lroundf(255.0f * run->bolt_show / LIGHTNING_SHOW);
        unsigned h = (unsigned)(run->bolt_x * 7.0f) | 1u;
        int x = x0;
        for (int y = 0; y < BASELINE; y += 3 * px) { /* Jagged down to the strike */
            h = h * 1103515245u + 12345u;
            int step = ((int)((h >> 16) % 5u) - 2) * px;
            int target = y + 3 * px >= BASELINE ? x0 : x + step;
            SDL_SetRenderDrawColor(renderer, 0x9c, 0xc8, 0xff, (Uint8)(alpha / 2));
            SDL_Rect halo = {(x < target ? x : target) - 2 * px, y, abs(target - x) + 5 * px, 3 * px};
            SDL_RenderFillRect(renderer, &halo);
            SDL_SetRenderDrawColor(renderer, 0xff, 0xff, 0xff, alpha);
            SDL_Rect core = {(x < target ? x : target), y, abs(target - x) + px, 3 * px};
            SDL_RenderFillRect(renderer, &core);
            if ((h >> 10) % 7u == 0u) { /* A fork off it */
                SDL_SetRenderDrawColor(renderer, 0xd8, 0xe8, 0xff, (Uint8)(alpha * 3 / 4));
                for (int k = 1; k <= 4; k++) {
                    SDL_Rect fork = {x + ((h >> 4) & 1u ? k : -k) * px * 2, y + k * px * 2, px, 2 * px};
                    SDL_RenderFillRect(renderer, &fork);
                }
            }
            x = target;
        }
        SDL_SetRenderDrawColor(renderer, 0xff, 0xf4, 0xc0, alpha); /* Where it hit */
        SDL_Rect burst = {x0 - 6 * px, BASELINE - 2 * px, 13 * px, 2 * px};
        SDL_RenderFillRect(renderer, &burst);
    }
}

/* The bats: flitting, flying off, or shot down. */
static void draw_bats(SDL_Renderer *renderer, const Bats *bats, float camera_x)
{
    SDL_Texture *sheet = assets_texture("sprites/bat/bat");
    if (sheet == NULL)
        return;
    for (int i = 0; i < BATS_MAX; i++) {
        const Bat *b = &bats->items[i];
        if (!bat_present(b))
            continue;
        SDL_Rect src = {bat_frame(b) * BAT_FRAME_W, 0, BAT_FRAME_W, BAT_FRAME_H};
        SDL_Rect dst = {(int)lroundf(b->x - camera_x) - BAT_FRAME_W * SPRITE_SCALE / 2,
                        BASELINE - (int)lroundf(b->height) - BAT_FRAME_H * SPRITE_SCALE,
                        BAT_FRAME_W * SPRITE_SCALE, BAT_FRAME_H * SPRITE_SCALE};
        SDL_SetTextureAlphaMod(sheet, (Uint8)lroundf(bat_opacity(b) * 255.0f));
        SDL_RenderCopyEx(renderer, sheet, &src, &dst, 0.0, NULL,
                         b->facing < 0 ? SDL_FLIP_HORIZONTAL : SDL_FLIP_NONE);
    }
    SDL_SetTextureAlphaMod(sheet, 255);
}

/* Grenades in the air or rolling, tumbling as they go. */
static void draw_grenades(SDL_Renderer *renderer, const StageRun *run, float camera_x)
{
    SDL_Texture *sheet = assets_texture("sprites/weapons/grenade");
    if (sheet == NULL)
        return;
    for (int g = 0; g < RUN_MAX_GRENADES; g++) {
        const Grenade *n = &run->grenades[g];
        if (!n->active)
            continue;
        int frame = (int)(n->fuse * 12.0f) % 4;
        SDL_Rect src = {frame * GRENADE_FRAME, 0, GRENADE_FRAME, GRENADE_FRAME};
        int size = GRENADE_FRAME * SPRITE_SCALE;
        SDL_Rect dst = {(int)lroundf(n->x - camera_x) - size / 2, BASELINE - (int)lroundf(n->height) - size,
                        size, size};
        SDL_RenderCopy(renderer, sheet, &src, &dst);
    }
}

void stage_draw(Platform *platform, StagePlay *play, const CharacterSkin *skin,
                       const Progress *progress, float alpha, float prev_player_x,
                       float prev_jump, const AppOptions *options)
{
    Player player_view = play->player;
    player_view.light_on = play->flashlight;
    player_view.light_since = play->flashlight_since;
    player_view.light_time = stage_weapon(play)->light_time;
    player_view.light_rows = stage_weapon(play)->light_rows;
    player_view.light_dx = stage_weapon(play)->light_dx;
    player_view.light_swings = stage_weapon(play)->melee_lit_sheet != NULL;
    player_view.x = interpolate(prev_player_x, play->player.x, alpha);
    player_view.jump.height = interpolate(prev_jump, play->player.jump.height, alpha);
    static Zombie zombie_view[RUN_MAX_ZOMBIES];
    int zombie_count = play->run.zombie_count;
    for (int k = 0; k < zombie_count; k++) {
        zombie_view[k] = play->run.zombies[k];
        zombie_view[k].x = interpolate(play->prev_zombie_x[k], play->run.zombies[k].x, alpha);
    }

    /* Only the chunks around the view exist; walking streams the rest. */
    float camera_x = camera_left(player_view.x);
    world_stream(&play->world, camera_x);
    stage_begin_view(platform->renderer, play->world.theme);
    bool separated_light = false;
    float flashlight_time = stage_weapon(play)->light_time > 0.0f ? stage_weapon(play)->light_time : 1.0f;
    float flashlight = lighting_flashlight_power(play->flashlight, play->flashlight
                                                     ? play->flashlight_since - flashlight_time * PLAYER_LIGHT_CLICK
                                                     : play->flashlight_since);
    Lighting lighting;
    lighting_build(&lighting, &play->run.terrain, &play->effects, &player_view,
                    play->world.theme->night, flashlight, camera_x, platform_time());
    bool directional_light = false;
    for (int i = 0; i < lighting.count; i++)
        directional_light |= lighting.lights[i].kind == LIGHT_FLASHLIGHT;
    if (play->world.theme->night || directional_light) { /* What it lights apart from the far land */
        scene_draw_distant(platform->renderer, &play->world, camera_x);
        separated_light = scene_begin_foreground(platform->renderer);
        scene_draw_near(platform->renderer, &play->world, camera_x, platform_time());
    } else {
        scene_draw(platform->renderer, &play->world, camera_x, platform_time());
    }
    terrain_render(platform->renderer, &play->run.terrain, camera_x);
    draw_blood(platform->renderer, play, camera_x);
    draw_crows(platform->renderer, &play->crows, camera_x, play->run.stage->theme->city);
    draw_bats(platform->renderer, &play->bats, camera_x);
    for (int c = 0; c < RUN_MAX_CHESTS; c++)
        chest_render(platform->renderer, &play->run.chests[c], camera_x);
    /* The claw trail reaches past her, so a swiping zombie goes in front. */
    for (int k = 0; k < zombie_count; k++) {
        if (zombie_view[k].state != ZOMBIE_ATTACK)
            zombie_render(platform->renderer, &zombie_view[k], camera_x);
    }
    draw_phantoms(platform->renderer, &play->visions, camera_x, platform_time());
    if (play->visions.double_on) { /* Herself, ahead, looking back at her */
        Player twin = player_view;
        twin.ghost = true;
        twin.x = play->visions.double_x;
        twin.facing = play->visions.double_facing < 0 ? FACING_LEFT : FACING_RIGHT;
        twin.bandage = twin.bandage_shown = twin.drink_time = twin.wet = 0.0f;
        player_render(platform->renderer, &twin, skin, play->guns, play->weapon_slot, camera_x);
    }
    player_render(platform->renderer, &player_view, skin, play->guns, play->weapon_slot, camera_x);
    draw_grenades(platform->renderer, &play->run, camera_x);
    for (int k = 0; k < zombie_count; k++) {
        if (zombie_view[k].state == ZOMBIE_ATTACK)
            zombie_render(platform->renderer, &zombie_view[k], camera_x);
    }
    terrain_render_front(platform->renderer, &play->run.terrain, camera_x);
    bullets_render(platform->renderer, &play->bullets, camera_x);
    draw_lightning(platform->renderer, &play->run, camera_x, platform_time());
    effects_render(platform->renderer, &play->effects, camera_x);
    smoke_render(platform->renderer, &play->smoke, camera_x);
    if (separated_light)
        terrain_render_surface_lights(platform->renderer, &lighting, &player_view, zombie_view, zombie_count, camera_x);
    else
        terrain_render_lights(platform->renderer, &lighting, &player_view, zombie_view, zombie_count, camera_x);
    if (play->run.stage->hot)
        stage_draw_heat(platform->renderer, camera_x, platform_time());
    draw_heatstroke(platform->renderer, play->player.fatigue, platform_time());
    if (separated_light) {
        scene_end_foreground(platform->renderer);
        terrain_render_light_bloom(platform->renderer, &lighting, camera_x);
    }
    stage_end_view(platform->renderer);
    weather_render(platform->renderer, &play->weather, camera_x);
    const CharacterDef *c = play->character;
    const WeaponDef *w = stage_weapon(play);
    char gun_name[40];
    if (w->single_magazine > 0)
        snprintf(gun_name, sizeof(gun_name), "%s %s", w->name, stage_single_fire(play) ? "1x1" : "AUTO");
    else
        snprintf(gun_name, sizeof(gun_name), "%s", w->name);
    HudWeapon gun = {
        .id = play->guns[play->weapon_slot], .name = gun_name, .rounds = play->player.shot.rounds,
        .other_rounds = play->player.shot.other_rounds,
        .magazine = play->player.shot.magazine, .reloading = shot_reloading(&play->player.shot),
        .can_swap = c->weapon_count > 1 || stage_can_swap_duals(play, progress),
        .other_id = c->weapon_count > 1 ? play->guns[(play->weapon_slot + 1) % c->weapon_count]
                    : play->duals_out ? c->weapons[0] : c->power_weapon,
        .power = progress->level >= POWER_LEVEL ? (int)c->power : POWER_NONE,
        .power_wait = play->power_cooldown,
    };
    hud_draw_stage(platform->renderer, &player_view, zombie_view, zombie_count, progress,
                   &play->run, camera_x, &gun);
    if (!play->paused)
        return;
    if (play->pause_view == PAUSE_VIEW_LIST) {
        hud_draw_pause(platform->renderer, &play->pause_menu);
        return;
    }
    ui_dim(platform->renderer, 170);
    if (play->pause_view == PAUSE_VIEW_VOLUME)
        hud_draw_volume(platform->renderer, &options->volume_menu, &options->volumes);
    else
        hud_draw_controls(platform->renderer);
}

/* When the menus' landscape started drifting: the intro's last scene holds it
 * still at PLAYER_START_X, and the title screen carries on from there. */
static double backdrop_since;

void stage_backdrop_restart(void)
{
    backdrop_since = platform_time();
}

double stage_backdrop_seconds(void)
{
    return platform_time() - backdrop_since;
}

void stage_draw_backdrop_at(Platform *platform, World *world, float camera_x, float dim)
{
    world_stream(world, camera_x);
    stage_begin_view(platform->renderer, world->theme);
    scene_draw(platform->renderer, world, camera_x, platform_time());
    stage_end_view(platform->renderer);
    if (dim > 0.0f)
        ui_dim(platform->renderer, (Uint8)(dim * 255.0f));
}

/* Behind the menus: the first stage's landscape, drifting slowly by. */
void stage_draw_backdrop(Platform *platform, World *world, float dim)
{
    double drift = (platform_time() - backdrop_since) * MENU_DRIFT_SPEED;
    stage_draw_backdrop_at(platform, world, PLAYER_START_X + (float)fmod(drift, 20000.0), dim);
}
