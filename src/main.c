/* Vaquera 2D - a pixel-art cowgirl against zombies, in C + SDL2.
 *
 * Stage select, then stages: a road to a gate past groups of zombies,
 * barricades, powder barrels and a supply wagon, with chests along the way;
 * XP levels her up across stages. Art and sounds are embedded in the executable at
 * build time (see tools/embed_assets.py).
 */
#include <limits.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

#include "config.h"
#include "engine/assets.h"
#include "engine/audio.h"
#include "engine/input.h"
#include "engine/platform.h"
#include "engine/prefs.h"
#include "engine/text.h"
#include "engine/pixfont.h"
#include "game/controls.h"
#include "game/hud.h"
#include "game/player.h"
#include "game/player_render.h"
#include "game/bullet.h"
#include "game/bullet_render.h"
#include "game/scene.h"
#include "game/combat.h"
#include "game/damage.h"
#include "game/effects.h"
#include "game/effects_render.h"
#include "game/zombie.h"
#include "game/zombie_render.h"
#include "game/bats.h"
#include "game/crows.h"
#include "game/weather.h"
#include "game/weather_render.h"
#include "game/almanac.h"
#include "game/almanac_render.h"
#include "game/lighting.h"
#include "game/hallucination.h"
#include "game/camera.h"
#include "game/props.h"
#include "game/themes.h"
#include "game/world.h"
#include "game/smoke.h"
#include "game/smoke_render.h"
#include "game/chest.h"
#include "game/chest_render.h"
#include "game/menu.h"
#include "game/progression.h"
#include "game/stage_run.h"
#include "game/stages.h"
#include "game/characters.h"
#include "game/character_skin.h"
#include "game/char_select.h"
#include "game/weapons.h"
#include "game/terrain.h"
#include "game/terrain_render.h"
#include "game/settings.h"
#include "game/ui.h"

/* Scripted input for --smoke-test: walk right, jump while walking right,
 * walk left, stop, then shoot once standing and let the bullet leave.
 * Meanwhile the zombie limps in from the right. */
#define SMOKE_RIGHT_START 0.15f
#define SMOKE_JUMP_AT 1.30f
#define SMOKE_LEFT_START 2.25f
#define SMOKE_STOP 2.60f
#define SMOKE_SHOOT_AT 2.70f
#define SMOKE_END 3.70f
#define SMOKE_ZOMBIE_GAP 800.0f

typedef struct {
    bool enabled;
    float time;
    float x_after_right;
    unsigned walk_frames_seen; /* Bit per frame shown, per sheet */
    unsigned jump_frames_seen;
    unsigned shoot_frames_seen;
    int shots_fired;
    int bullets_seen; /* Most bullets alive at once */
    float bullet_start_x;
    float bullet_last_x;
    float x_before_shot;
    float x_after_shot;
    float max_height;
    unsigned zombie_frames_seen;
    float zombie_start_x;
    float zombie_min_x;
    bool faced_left;
    bool done;
    bool passed;
} SmokeTest;

static bool verify_sheet(const AnimationDef *def)
{
    const EmbeddedImage *image = assets_find_image(def->sheet);
    int needed_w = (def->first_frame + def->frame_count) * def->frame_w;
    if (image == NULL) {
        fprintf(stderr, "FALTA: %s\n", def->sheet);
        return false;
    }
    if (image->width % def->frame_w != 0 || image->width < needed_w ||
        image->height != def->frame_h) {
        fprintf(stderr, "TAMAÑO INCORRECTO: %s es %dx%d; con cuadros de %dx%d "
                "el ancho debe ser múltiplo de %d (mínimo %d) y el alto %d\n",
                def->sheet, image->width, image->height, def->frame_w, def->frame_h,
                def->frame_w, needed_w, def->frame_h);
        return false;
    }
    return true;
}

static bool verify_image(const char *name, int width, int height);

/* Characters other than the cowgirl may still be on the stand-in (her art,
 * tinted). Once one has any sheet of its own, it needs all of them, each the
 * same size as hers, so the shared template (pivots, muzzle) still fits. */
static int verify_characters(void)
{
    int failures = 0;
    for (int c = 0; c < CHARACTER_COUNT; c++) {
        int own = 0;
        char names[SKIN_SHEETS][96];
        for (int s = 0; s < SKIN_SHEETS; s++) {
            snprintf(names[s], sizeof(names[s]), "sprites/characters/%s/%s", CHARACTERS[c].id,
                     SKIN_SHEET_NAMES[s]);
            own += assets_find_image(names[s]) != NULL;
        }
        if (own == 0) {
            printf("  %-22s arte provisional (la vaquera teñida)\n", CHARACTERS[c].name);
            continue;
        }
        for (int s = 0; s < SKIN_SHEETS; s++) {
            char template_name[96];
            snprintf(template_name, sizeof(template_name), "sprites/characters/cowgirl/%s",
                     SKIN_SHEET_NAMES[s]);
            const EmbeddedImage *ref = assets_find_image(template_name);
            failures += !verify_image(names[s], ref->width, ref->height);
        }
        /* A gun's own shoot and reload sheets are needed, the size of shoot.png... */
        const EmbeddedImage *shoot = assets_find_image("sprites/characters/cowgirl/shoot");
        /* Its guns, and the one its power gives it. */
        WeaponId guns[CHARACTER_MAX_WEAPONS + 1];
        int gun_count = 0;
        for (int w = 0; w < CHARACTERS[c].weapon_count; w++)
            guns[gun_count++] = CHARACTERS[c].weapons[w];
        if (CHARACTERS[c].power == POWER_DUAL_PISTOLS)
            guns[gun_count++] = CHARACTERS[c].power_weapon;
        for (int w = 0; w < gun_count; w++) { /* Its blow with each gun */
            const WeaponDef *def = weapon_def(guns[w]);
            char name[96];
            snprintf(name, sizeof(name), "sprites/characters/%s/%s", CHARACTERS[c].id,
                     def->melee_sheet ? def->melee_sheet : "melee");
            failures += !verify_image(name, PLAYER_MELEE_FRAMES * PLAYER_SHOOT_FRAME_W, shoot->height);
            if (def->light_sheet) {
                snprintf(name, sizeof(name), "sprites/characters/%s/%s", CHARACTERS[c].id, def->light_sheet);
                failures += !verify_image(name, PLAYER_LIGHT_FRAMES * PLAYER_SHOOT_FRAME_W, shoot->height);
                snprintf(name, sizeof(name), "sprites/characters/%s/%s", CHARACTERS[c].id, def->light_walk_sheet);
                failures += !verify_image(name, (PLAYER_WALK_FRAMES + PLAYER_LIGHT_BREATHS) * PLAYER_SHOOT_FRAME_W, shoot->height);
            }
        }
        {
            char name[96]; /* Its faint (tools/make_faint.py), its drink and bandage */
            snprintf(name, sizeof(name), "sprites/characters/%s/faint", CHARACTERS[c].id);
            failures += !verify_image(name, PLAYER_FAINT_FRAMES * PLAYER_FAINT_FRAME_W, PLAYER_WALK_FRAME_H);
            if (CHARACTERS[c].power == POWER_DUAL_PISTOLS) { /* Its second pistol, out and away */
                snprintf(name, sizeof(name), "sprites/characters/%s/swap", CHARACTERS[c].id);
                failures += !verify_image(name, PLAYER_SWAP_FRAMES * PLAYER_SHOOT_FRAME_W, shoot->height);
                snprintf(name, sizeof(name), "sprites/characters/%s/shoot_dual_b", CHARACTERS[c].id);
                failures += !verify_image(name, PLAYER_PISTON_FRAMES * PLAYER_SHOOT_FRAME_W, shoot->height);
                const char *ricochets[] = {"ricochet", "ricochet_lit", "ricochet_dual", "ricochet_dual_lit"};
                for (int k = 0; k < 4; k++) {
                    snprintf(name, sizeof(name), "sprites/characters/%s/%s", CHARACTERS[c].id, ricochets[k]);
                    failures += !verify_image(name, PLAYER_SHOOT_FRAMES * PLAYER_SHOOT_FRAME_W, shoot->height);
                }
                snprintf(name, sizeof(name), "sprites/characters/%s/stand_dual", CHARACTERS[c].id);
                failures += !verify_image(name, PLAYER_WALK_FRAME_W, PLAYER_WALK_FRAME_H);
                snprintf(name, sizeof(name), "sprites/characters/%s/stand", CHARACTERS[c].id);
                failures += !verify_image(name, PLAYER_WALK_FRAME_W, PLAYER_WALK_FRAME_H);
                snprintf(name, sizeof(name), "sprites/characters/%s/swap_lit", CHARACTERS[c].id);
                failures += !verify_image(name, PLAYER_SWAP_FRAMES * PLAYER_SHOOT_FRAME_W, shoot->height);
            }
            const char *care[] = {"drink", "bandage", "plant"};
            for (int k = 0; k < 3; k++) {
                snprintf(name, sizeof(name), "sprites/characters/%s/%s", CHARACTERS[c].id, care[k]);
                failures += !verify_image(name, PLAYER_CARE_FRAMES * PLAYER_SHOOT_FRAME_W, shoot->height);
            }
        }
        if (CHARACTERS[c].power == POWER_GRENADES) { /* Its throw, on the shoot template */
            char name[96];
            snprintf(name, sizeof(name), "sprites/characters/%s/throw", CHARACTERS[c].id);
            failures += !verify_image(name, PLAYER_THROW_FRAMES * PLAYER_SHOOT_FRAME_W, shoot->height);
        }
        for (int w = 0; w < gun_count; w++) {
            const WeaponDef *def = weapon_def(guns[w]);
            const char *sheets[] = {def->shoot_sheet, def->reload_sheet};
            for (int k = 0; k < 2; k++) {
                char name[96];
                if (sheets[k] == NULL)
                    continue;
                snprintf(name, sizeof(name), "sprites/characters/%s/%s", CHARACTERS[c].id, sheets[k]);
                failures += !verify_image(name, k == 0 && def->piston ? PLAYER_PISTON_FRAMES * PLAYER_SHOOT_FRAME_W : shoot->width, shoot->height);
            }
            if (def->sit_sheet) { /* ...and its sit sheet, the size of sit.png */
                const EmbeddedImage *sit = assets_find_image("sprites/characters/cowgirl/sit");
                char name[96];
                snprintf(name, sizeof(name), "sprites/characters/%s/%s", CHARACTERS[c].id, def->sit_sheet);
                failures += !verify_image(name, sit->width, sit->height);
            }
        }
    }
    return failures;
}

/* An embedded image with exactly this size. */
static bool verify_image(const char *name, int width, int height)
{
    const EmbeddedImage *image = assets_find_image(name);
    if (image == NULL) {
        fprintf(stderr, "FALTA: %s\n", name);
        return false;
    }
    if (image->width != width || image->height != height) {
        fprintf(stderr, "TAMAÑO INCORRECTO: %s es %dx%d; debe ser %dx%d\n", name,
                image->width, image->height, width, height);
        return false;
    }
    return true;
}

static int verify_assets(void)
{
    const AnimationDef *anims[ZOMBIE_KIND_COUNT * ZOMBIE_ANIM_COUNT + 64];
    int player_count;
    const AnimationDef *const *player_anims = player_animations(&player_count);
    int anim_count = 0;
    for (int i = 0; i < player_count; i++)
        anims[anim_count++] = player_anims[i];
    anims[anim_count++] = bullet_animation();
    int zombie_count;
    const AnimationDef *const *zombie_anims = zombie_animations(&zombie_count);
    for (int i = 0; i < zombie_count; i++)
        anims[anim_count++] = zombie_anims[i];
    anims[anim_count++] = effect_sparks();
    anims[anim_count++] = chest_animation();
    anims[anim_count++] = chest_sparks();
    anims[anim_count++] = terrain_explosion();
    anims[anim_count++] = terrain_heal_effect();

    int failures = 0;
    for (int i = 0; i < anim_count; i++)
        failures += !verify_sheet(anims[i]);
    for (int s = 0; s < STAGE_COUNT; s++) {
        for (int i = 0; i < BACKGROUND_LAYER_COUNT; i++) {
            const BackgroundLayer *layer = &BACKGROUND_LAYERS[i];
            char name[96];
            snprintf(name, sizeof(name), "backgrounds/%s/%s", STAGES[s].theme->name, layer->file);
            failures += !verify_image(name, layer->width, layer->height);
        }
        if (STAGES[s].theme->fog) {
            char name[96];
            snprintf(name, sizeof(name), "backgrounds/%s/%s", STAGES[s].theme->name, FOG_LAYER.file);
            failures += !verify_image(name, FOG_LAYER.width, FOG_LAYER.height);
        }
    }
    for (int k = 0; k < PROP_KIND_COUNT; k++) {
        const PropDef *def = prop_def(k);
        failures += !verify_image(def->sheet, def->frame_w * def->variants, def->frame_h);
    }
    for (int k = 0; k < TERRAIN_KINDS; k++) {
        int w, h, frames;
        terrain_frame_size(k, &w, &h, &frames);
        failures += !verify_image(terrain_sheet(k), frames * w, h);
    }
    failures += !verify_image(terrain_charge_sheet(), 2 * CHARGE_FRAME_W, CHARGE_FRAME_H);
    failures += !verify_image(terrain_ruins_sheet(), WALL_RUINS_W, WALL_RUINS_H);
    failures += !verify_image(terrain_facade_sheet(), FACADE_KINDS * FACADE_W, FACADE_H);
    failures += !verify_image(terrain_door_sheet(), 3 * DOOR_FRAME_W, DOOR_FRAME_H);
    failures += !verify_image("sprites/weapons/grenade", 4 * GRENADE_FRAME, GRENADE_FRAME);
    failures += !verify_image("sprites/effects/blood", 4 * 8, 4);
    failures += !verify_image("sprites/terrain/wire", 3 * WIRE_FRAME_W, WIRE_FRAME_H);
    failures += !verify_image("sprites/terrain/net", 3 * NET_FRAME_W, NET_FRAME_H);
    failures += !verify_image("sprites/terrain/snare", 3 * SNARE_FRAME_W, SNARE_FRAME_H);
    failures += !verify_image("sprites/terrain/spikes", 3 * SPIKES_FRAME_W, SPIKES_FRAME_H);
    failures += !verify_image("sprites/effects/net_bag", 4 * NET_BAG_W, NET_BAG_H);
    failures += !verify_image("sprites/crow/crow", CROW_FRAMES * CROW_FRAME_W, CROW_FRAME_H);
    failures += !verify_image("sprites/bat/bat", BAT_FRAMES * BAT_FRAME_W, BAT_FRAME_H);
    failures += !verify_image("sprites/terrain/river", 4 * RIVER_FRAME_W, RIVER_FRAME_H);
    failures += !verify_image("sprites/terrain/river_front", 4 * RIVER_FRAME_W, RIVER_FRONT_H);
    failures += !verify_image("sprites/terrain/puddle", 4 * PUDDLE_FRAME_W, PUDDLE_FRAME_H);
    failures += !verify_image("sprites/terrain/sign", SIGN_FRAME_W, SIGN_FRAME_H);
    failures += !verify_image("sprites/effects/splash", SPLASH_FRAMES * SPLASH_FRAME_W, SPLASH_FRAME_H);
    failures += !verify_image("sprites/effects/tumbleweed", 4 * TUMBLE_FRAME, TUMBLE_FRAME);
    failures += !verify_image("sprites/terrain/barricade", 3 * BARRICADE_KINDS * BARRICADE_FRAME_W,
                              BARRICADE_FRAME_H);
    failures += !verify_image("sprites/props/houses", HOUSE_FRAMES * HOUSE_FRAME_W, HOUSE_FRAME_H);
    failures += !verify_image("sprites/effects/glow", GLOW_SIZE, GLOW_SIZE);
    const char *badges[] = {"sprites/ui/badge_player", "sprites/ui/badge_zombie"};
    for (size_t i = 0; i < sizeof(badges) / sizeof(badges[0]); i++)
        failures += !verify_image(badges[i], BADGE_W, BADGE_H);
    /* The interface kit (tools/make_ui.py) and its font. */
    const struct {
        const char *name;
        int w, h;
    } kit[] = {
        {"sprites/ui/panel", 24, 24}, {"sprites/ui/button", 32, 16}, {"sprites/ui/key", 14, 14},
        {"sprites/ui/pip", 12, 10}, {"sprites/ui/bar", 12, 8},
        {"sprites/ui/icons", ICON_COUNT * UI_ICON_SIZE, UI_ICON_SIZE},
        {"sprites/ui/weapons", (WEAPON_COUNT + 1) * UI_WEAPON_W, UI_WEAPON_H}, /* + the grenade */
    };
    for (size_t i = 0; i < sizeof(kit) / sizeof(kit[0]); i++)
        failures += !verify_image(kit[i].name, kit[i].w, kit[i].h);
    if (!pixfont_init()) {
        fprintf(stderr, "FALTA o INCOMPLETA: sprites/ui/font (corre tools/make_ui.py)\n");
        failures++;
    }
    if (!hud_verify_layout()) {
        fprintf(stderr, "HUD: elementos fuera de sus límites o texto sin espacio.\n");
        failures++;
    }
    failures += verify_characters();
    const char *blobs[] = {"fonts/DejaVuSansMono", "fonts/DejaVuSansMono-Bold",
                           "sounds/player/shot", "sounds/player/reload", "sounds/zombie/spawn",
                           "sounds/zombie/idle", "sounds/zombie/death", "sounds/world/explosion",
                           "sounds/world/supply", "sounds/world/fuse",
                           "sounds/world/glass", "sounds/world/wood", "sounds/world/snap",
                           "sounds/player/drink", "sounds/crow/caw", "sounds/crow/death",
                           "sounds/dog/spawn", "sounds/dog/idle", "sounds/dog/death",
                           "sounds/player/hurt", "sounds/player/jump", "sounds/player/land",
                           "sounds/player/death", "sounds/player/bandage", "sounds/player/faint",
                           "sounds/effects/hit_flesh", "sounds/effects/hit_armor",
                           "sounds/world/hit_wood", "sounds/world/hit_metal", "sounds/world/hit_stone",
                           "sounds/world/hit_wire", "sounds/world/hit_sand", "sounds/world/wire",
                           "sounds/world/rope", "sounds/world/trap_escape", "sounds/world/ambush",
                           "sounds/world/grenade_explosion", "sounds/world/dynamite_explosion",
                           "sounds/world/footstep", "sounds/world/footstep_2", "sounds/world/footstep_3",
                           "sounds/world/footstep_4", "sounds/world/run_step", "sounds/world/run_step_2",
                           "sounds/world/run_step_3", "sounds/world/run_step_4",
                           "sounds/world/footstep_water", "sounds/world/footstep_water_2",
                           "sounds/world/footstep_water_3", "sounds/world/footstep_water_4",
                           "sounds/world/run_step_water", "sounds/world/run_step_water_2",
                           "sounds/world/run_step_water_3", "sounds/world/run_step_water_4",
                           "sounds/world/sit",
                           "sounds/world/stand", "sounds/world/chest", "sounds/world/level_up",
                           "sounds/world/victory", "sounds/weather/wind", "sounds/weather/rain",
                           "sounds/weather/thunder", "sounds/ui/move", "sounds/ui/confirm",
                           "sounds/ui/back", "sounds/weapons/switch", "sounds/weapons/grenade_throw",
                           "sounds/weapons/ricochet"};
    for (size_t i = 0; i < sizeof(blobs) / sizeof(blobs[0]); i++) {
        if (assets_find_blob(blobs[i]) == NULL) {
            fprintf(stderr, "FALTA: %s\n", blobs[i]);
            failures++;
        }
    }
    for (int id = 0; id < WEAPON_COUNT; id++) {
        const WeaponDef *w = weapon_def((WeaponId)id);
        const char *paths[] = {w->shot_sound, w->cycle_sound, w->reload_sound,
                              w->empty_sound, w->melee_sound};
        for (size_t s = 0; s < sizeof(paths) / sizeof(paths[0]); s++) {
            if (!paths[s])
                continue;
            char name[128];
            snprintf(name, sizeof(name), "sounds/%s", paths[s]);
            if (!assets_find_blob(name)) {
                fprintf(stderr, "FALTA: %s (%s)\n", name, w->name);
                failures++;
            }
        }
    }
    if (failures)
        return 1;
    printf("OK: %d imagen(es) y %d fuente(s)/sonido(s) incrustados.\n",
           embedded_image_count, embedded_blob_count);
    for (int i = 0; i < anim_count; i++) {
        const AnimationDef *def = anims[i];
        printf("  %-22s frames %d-%d de %d × %d px\n", def->sheet, def->first_frame,
               def->first_frame + def->frame_count - 1, def->frame_w, def->frame_h);
    }
    printf("Escala: %d×\n", SPRITE_SCALE);
    return 0;
}

static void smoke_override(const SmokeTest *smoke, bool down[ACTION_COUNT])
{
    memset(down, 0, sizeof(bool) * ACTION_COUNT);
    if (smoke->time >= SMOKE_RIGHT_START && smoke->time < SMOKE_LEFT_START)
        down[ACTION_RIGHT] = true;
    if (smoke->time >= SMOKE_JUMP_AT && smoke->time < SMOKE_JUMP_AT + 2 * FIXED_DT)
        down[ACTION_JUMP] = true;
    if (smoke->time >= SMOKE_LEFT_START && smoke->time < SMOKE_STOP)
        down[ACTION_LEFT] = true;
    /* A single-step click, like a quick real one. */
    if (smoke->time >= SMOKE_SHOOT_AT && smoke->time < SMOKE_SHOOT_AT + FIXED_DT)
        down[ACTION_SHOOT] = true;
}

static void smoke_observe(SmokeTest *smoke, const Player *player, const Bullets *bullets,
                          const Zombie *zombie)
{
    if (smoke->zombie_start_x == 0.0f)
        smoke->zombie_start_x = smoke->zombie_min_x = zombie->x;
    if (zombie->x < smoke->zombie_min_x)
        smoke->zombie_min_x = zombie->x;
    if (zombie->state == ZOMBIE_WALK)
        smoke->zombie_frames_seen |= 1u << zombie->anim.frame;
    int alive = bullets_active_count(bullets);
    if (alive > smoke->bullets_seen)
        smoke->bullets_seen = alive;
    if (alive > 0) {
        for (int i = 0; i < BULLET_MAX; i++) {
            if (!bullets->items[i].active)
                continue;
            if (smoke->bullet_start_x == 0.0f)
                smoke->bullet_start_x = bullets->items[i].x;
            smoke->bullet_last_x = bullets->items[i].x;
        }
    }
    if (player->state == PLAYER_WALK || player->state == PLAYER_RUN)
        smoke->walk_frames_seen |= 1u << player->anim.frame;
    if (player->state == PLAYER_JUMP || player->state == PLAYER_LAND)
        smoke->jump_frames_seen |= 1u << player->anim.frame;
    if (player->state == PLAYER_SHOOT)
        smoke->shoot_frames_seen |= 1u << player->anim.frame;
    if (player->shot_fired)
        smoke->shots_fired++;
    if (smoke->time < SMOKE_SHOOT_AT)
        smoke->x_before_shot = player->x;
    else
        smoke->x_after_shot = player->x;
    if (player->jump.height > smoke->max_height)
        smoke->max_height = player->jump.height;
    if (smoke->time < SMOKE_LEFT_START)
        smoke->x_after_right = player->x;
    if (player->facing == FACING_LEFT)
        smoke->faced_left = true;

    smoke->time += FIXED_DT;
    if (smoke->time < SMOKE_END)
        return;

    unsigned all_walk = (1u << PLAYER_WALK_FRAMES) - 1;
    unsigned all_jump = (1u << PLAYER_JUMP_FRAMES) - 1;
    unsigned all_shoot = (1u << PLAYER_SHOOT_FRAMES) - 1;
    bool advanced = smoke->x_after_right > PLAYER_START_X + 20.0f;
    bool came_back = player->x < smoke->x_after_right - 20.0f;
    bool walk_seen = (smoke->walk_frames_seen & all_walk) == all_walk;
    bool jump_seen = (smoke->jump_frames_seen & all_jump) == all_jump;
    bool jumped = smoke->max_height > PLAYER_JUMP_HEIGHT * 0.95f;
    bool shoot_seen = (smoke->shoot_frames_seen & all_shoot) == all_shoot;
    bool shot_ok = smoke->shots_fired == 1 && smoke->x_after_shot == smoke->x_before_shot;
    /* Fired facing left, from the muzzle, and gone once off-screen. */
    bool bullet_ok = smoke->bullets_seen == 1 && alive == 0 &&
                     smoke->bullet_last_x < smoke->bullet_start_x &&
                     smoke->bullet_start_x < player->x - PLAYER_MUZZLE_DX * SPRITE_SCALE + 1.0f;
    unsigned all_zombie = (1u << ZOMBIE_WALK_FRAMES) - 1;
    bool zombie_ok = (smoke->zombie_frames_seen & all_zombie) == all_zombie &&
                     smoke->zombie_min_x < smoke->zombie_start_x - 50.0f &&
                     zombie->health == zombie->max_health;
    bool stopped = player->state == PLAYER_IDLE && player->anim.frame == 0 &&
                   !player->jump.airborne;
    smoke->passed = advanced && came_back && walk_seen && jump_seen && jumped &&
                    shoot_seen && shot_ok && bullet_ok && smoke->faced_left && zombie_ok &&
                    stopped;
    smoke->done = true;
    printf("SMOKE TEST: pos_derecha=%.1f avance=%d regreso=%d caminata=%s salto=%s "
           "altura=%.1f disparo=%s balas=%d trayectoria=%d izquierda=%d zombi=%s detenida=%d -> %s\n",
           smoke->x_after_right, advanced, came_back, walk_seen ? "8/8" : "incompleta",
           jump_seen ? "8/8" : "incompleto", smoke->max_height,
           shoot_seen ? "8/8" : "incompleto", smoke->shots_fired, bullet_ok, smoke->faced_left,
           zombie_ok ? "8/8" : "FALLO", stopped,
           smoke->passed ? "OK" : "FALLO");
}

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

/* Display refreshes are evenly spaced even when the loop wakes up a little
 * early or late; feeding that noise to the interpolation shakes the view. */
static float snap_frame_time(float frame_time)
{
    static const float targets[] = {FIXED_DT / 2.0f, FIXED_DT, FIXED_DT * 2.0f};
    for (size_t i = 0; i < sizeof(targets) / sizeof(targets[0]); i++) {
        if (fabsf(frame_time - targets[i]) < targets[i] * FRAME_SNAP_TOLERANCE)
            return targets[i];
    }
    return frame_time;
}

/* The options' volumes, for the whole session. */
static Volumes volumes;
static Platform *display; /* The window, for the options screen's full-screen row */
static bool remember_display; /* Off in the automated runs, so they never change it */

#define PREF_FULLSCREEN "pantalla_completa"

static void set_fullscreen(bool on)
{
    platform_set_fullscreen(display, on);
    volumes.fullscreen = display->fullscreen;
    if (remember_display)
        prefs_set_bool(PREF_FULLSCREEN, volumes.fullscreen);
}
static ListMenu volume_menu;

static void apply_volumes(void)
{
    audio_set_master(volume_share(volumes.master));
    audio_set_group(SOUND_PLAYER, volume_share(volumes.player));
    audio_set_group(SOUND_ZOMBIE, volume_share(volumes.zombie));
}

/* Something the character does or sets off. */
static void play_sound(const char *name)
{
    if (name)
        audio_play_in(name, SOUND_PLAYER);
}

/* Which take a step uses: walking or running, on dry ground or in water. */
static const char *footstep_sound(bool running, bool water, unsigned step)
{
    static const char *const TAKES[2][2][4] = {
        {{"world/footstep", "world/footstep_2", "world/footstep_3", "world/footstep_4"},
         {"world/footstep_water", "world/footstep_water_2", "world/footstep_water_3", "world/footstep_water_4"}},
        {{"world/run_step", "world/run_step_2", "world/run_step_3", "world/run_step_4"},
         {"world/run_step_water", "world/run_step_water_2", "world/run_step_water_3", "world/run_step_water_4"}},
    };
    return TAKES[running][water][step % 4];
}

/* The options screen, while open. Returns false once it is left. A changed
 * volume plays a sample of what it controls. */
static bool volume_step(const InputState *input)
{
    int row = volume_menu_update(&volume_menu, &volumes, input);
    if (row == VOLUME_BACK)
        return false;
    if (row == VOLUME_FULLSCREEN) {
        set_fullscreen(volumes.fullscreen);
        audio_play("ui/confirm");
    } else if (row >= 0) {
        apply_volumes();
        if (row == VOLUME_ZOMBIE)
            audio_play_in("zombie/idle", SOUND_ZOMBIE);
        else if (row == VOLUME_PLAYER)
            play_sound("player/shot");
        else
            audio_play("ui/confirm");
    }
    return true;
}

/* The mouse over what the screen last drew: pointing at an item selects it
 * (*selected, when the screen has a list), clicking it confirms; clicking a
 * hint's key does what the key does; clicking a volume bar sets it there. */
static void apply_pointer(InputState *input, int *selected)
{
    HudZone zone;
    if (!(input->pointer_moved || input->pointer_clicked) ||
        !hud_zone_at(input->pointer_x, input->pointer_y, &zone))
        return;
    if ((zone.kind == HUD_ZONE_ITEM || zone.kind == HUD_ZONE_VOLUME) && selected)
        *selected = zone.index;
    if (!input->pointer_clicked)
        return;
    switch (zone.kind) {
    case HUD_ZONE_ITEM:
    case HUD_ZONE_ACCEPT:
        input->pressed[ACTION_CONFIRM] = true;
        break;
    case HUD_ZONE_BACK:
        input->pressed[ACTION_QUIT] = true;
        break;
    case HUD_ZONE_RETRY:
        input->pressed[ACTION_RELOAD] = true;
        break;
    case HUD_ZONE_VOLUME:
        if (volume_set(&volumes, zone.index, (int)lroundf(zone.share * VOLUME_STEPS))) {
            apply_volumes();
            if (zone.index == VOLUME_ZOMBIE)
                audio_play_in("zombie/idle", SOUND_ZOMBIE);
            else if (zone.index == VOLUME_PLAYER)
                play_sound("player/shot");
            else
                audio_play("ui/confirm");
        }
        break;
    }
}

/* Existing zombie recordings remain untouched. The new dog has its own
 * recorded canine voice rather than using a human groan. */
static void play_zombie_voice(Zombie *zombie)
{
    bool dog = zombie->kind == ZOMBIE_KIND_DOG;
    if (zombie->just_spawned)
        audio_play_in(dog ? "dog/spawn" : "zombie/spawn", SOUND_ZOMBIE);
    else if (zombie->just_died)
        audio_play_in(dog ? "dog/death" : "zombie/death", SOUND_ZOMBIE);
    else if (zombie->growl_due)
        audio_play_in(dog ? "dog/idle" : "zombie/idle", SOUND_ZOMBIE);
    zombie->just_spawned = zombie->just_died = zombie->growl_due = false;
}

static void set_window_icon(SDL_Window *window)
{
    SDL_Surface *icon = assets_surface_region("sprites/characters/cowgirl/walk", 0, 0,
                                              PLAYER_WALK_FRAME_W, PLAYER_WALK_FRAME_H);
    if (icon) {
        SDL_SetWindowIcon(window, icon);
        SDL_FreeSurface(icon);
    }
}

typedef enum {
    SCREEN_TITLE,     /* Jugar, Almanaque, Controles, Volumen, Salir */
    SCREEN_CONTROLS,
    SCREEN_VOLUME,
    SCREEN_CHARACTER, /* Elige tu personaje */
    SCREEN_MENU,      /* Its stages */
    SCREEN_ALMANAC,
    SCREEN_STAGE
} Screen;

/* What the pause shows: its list, or the volume or controls screen opened from it. */
typedef enum { PAUSE_VIEW_LIST, PAUSE_VIEW_VOLUME, PAUSE_VIEW_CONTROLS } PauseView;

/* What each character keeps between stages (no save file yet). */
typedef struct {
    Progress progress;
    StageRecord record;
    Almanac almanac;
} Profile;

/* Everything one play of a stage uses, reset when it starts. */
typedef struct {
    const CharacterDef *character;
    int weapon_slot; /* Which of the character's guns is in hand */
    bool single_fire; /* K: guns with a single mode fire one round per click */
    WeaponId guns[CHARACTER_MAX_WEAPONS]; /* Its guns at its level (a power may change one) */
    bool duals_out;  /* Its power's second pistol in hand (Q takes it out and away) */
    float power_cooldown; /* Seconds until F works again */
    bool ricochet_armed;  /* The next shot's bullets glance on to a second target */
    bool ricochet_fired;  /* ...and it has gone: her hands part when the shot ends */
    int rounds[CHARACTER_MAX_WEAPONS]; /* Shots left in each gun's magazine while put away */
    Player player;
    Bullets bullets;
    Effects effects;
    Smoke smoke;
    StageRun run; /* The road: its zombies, terrain and chests */
    AlmanacEncounter encounter;
    World world;
    float prev_zombie_x[RUN_MAX_ZOMBIES]; /* Before the last step, to draw in between */
    float smoke_timer; /* Seconds until fires puff smoke again */
    Crows crows;
    Bats bats; /* At night, along the road */
    float faint_timer; /* Seconds since she fainted: the stage starts over at FAINT_RESTART */
    WeatherState weather;
    Hallucination visions; /* What her thirst makes her see */
    float splash_timer; /* Seconds until the walkers in water splash again */
    int footstep_phase;       /* Half of the walk cycle her feet are on, -1 when not walking */
    unsigned footstep_count;  /* Steps taken: left and right feet sound apart */
    float thunder_wait; /* Delay between lightning and its thunder; -1 = none */
    /* Her trail of blood while she bleeds: drops on the road drying away. */
    float blood_x[BLOOD_DROPS], blood_age[BLOOD_DROPS];
    int blood_next;
    float blood_timer;
    /* Her progress when the stage began: a retry or leaving before clearing
     * it puts this back, so replaying a stage can't farm its XP. */
    Progress progress_at_start;
    bool paused;     /* Esc: the pause menu, the stage frozen behind it */
    ListMenu pause_menu;
    PauseView pause_view;
    bool request_almanac;
    bool flashlight;
    float flashlight_since; /* Seconds since its switch was flipped */
} StagePlay;

static const WeaponDef *weapon_in_hand(const StagePlay *play)
{
    return weapon_def(play->guns[play->weapon_slot]);
}

/* Its guns at this level; true if the one in hand changed. */
static bool set_guns(StagePlay *play, int level)
{
    WeaponId before = play->guns[play->weapon_slot];
    for (int w = 0; w < play->character->weapon_count; w++)
        play->guns[w] = character_weapon(play->character, w, level);
    if (play->character->power == POWER_DUAL_PISTOLS)
        play->guns[0] = play->duals_out ? play->character->power_weapon : play->character->weapons[0];
    return play->guns[play->weapon_slot] != before;
}

static bool single_fire(const StagePlay *play)
{
    return play->single_fire && weapon_in_hand(play)->single_magazine > 0;
}

/* The shot sequence takes the gun in hand: timings, burst and magazine (in
 * the fire mode K chose). */
static void equip_weapon(StagePlay *play)
{
    const WeaponDef *w = weapon_in_hand(play);
    Shot *shot = &play->player.shot;
    shot_set_piston(shot, w->piston);
    if (single_fire(play)) {
        shot_set_reload(shot, w->single_reload);
        shot_set_burst(shot, 1, 0.0f, false);
        shot_set_magazine(shot, w->single_magazine, w->magazine_reload, play->rounds[play->weapon_slot]);
        return;
    }
    shot_set_reload(shot, w->reload_time);
    shot_set_burst(shot, w->burst, w->burst_gap, w->automatic);
    shot_set_magazine(shot, w->magazine, w->magazine_reload, play->rounds[play->weapon_slot]);
}

/* K: bursts <-> single shots on a gun that has both. The rounds left carry
 * over (a burst is magazine x burst / single_magazine of them); a shot or a
 * reload under way is dropped, like a swap. */
static void toggle_fire_mode(StagePlay *play)
{
    const WeaponDef *w = weapon_in_hand(play);
    Shot *shot = &play->player.shot;
    if (w->single_magazine <= 0 || !player_alive(&play->player))
        return;
    audio_stop(w->reload_sound);
    if (shot->active)
        shot_cancel(shot);
    int per_burst = w->single_magazine / (w->magazine > 0 ? w->magazine : 1);
    int rounds = shot->rounds;
    play->single_fire = !play->single_fire;
    play->rounds[play->weapon_slot] = play->single_fire ? rounds * per_burst : rounds / per_burst;
    if (!play->single_fire && rounds > 0 && play->rounds[play->weapon_slot] == 0)
        play->rounds[play->weapon_slot] = 1; /* A stray round or two still makes a burst */
    equip_weapon(play);
    play_sound("weapons/switch");
    hud_popup(play->single_fire ? "TIRO A TIRO" : "RÁFAGAS", COLOR_HUD_PRIMARY, play->player.x,
              BASELINE - PLAYER_HEAD_HEIGHT * SPRITE_SCALE - BADGE_H * BADGE_SCALE - 34, false);
}

static void start_stage(StagePlay *play, int index, const CharacterDef *character,
                        const Progress *progress)
{
    audio_stop_all();
    play->character = character;
    play->weapon_slot = 0;
    play->single_fire = false;
    play->power_cooldown = 0.0f;
    play->ricochet_armed = false;
    play->ricochet_fired = false;
    play->duals_out = progress->level >= POWER_LEVEL;
    for (int d = 0; d < BLOOD_DROPS; d++)
        play->blood_age[d] = BLOOD_LIFE; /* None yet */
    play->blood_next = 0;
    play->blood_timer = 0.0f;
    set_guns(play, progress->level);
    play->progress_at_start = *progress;
    play->paused = false;
    play->request_almanac = false;
    play->flashlight = STAGES[index].theme->night; /* On by night; L works by day too */
    play->flashlight_since = 10.0f; /* Already on, no stutter */
    almanac_encounter_start(&play->encounter);
    player_init(&play->player);
    player_set_stats(&play->player, progress->level, progress_max_health(progress),
                     character_armor(play->character, progress->armor_level), true);
    for (int w = 0; w < CHARACTER_MAX_WEAPONS; w++)
        play->rounds[w] = -1; /* Full magazines */
    equip_weapon(play);
    bullets_clear(&play->bullets);
    effects_clear(&play->effects);
    smoke_clear(&play->smoke);
    hud_clear_popups();
    world_init(&play->world, STAGES[index].theme);
    run_start(&play->run, index, play->player.x, character_drops_chests(character));
    crows_start(&play->crows, index, play->player.x, play->run.goal_x - play->player.x);
    bats_start(&play->bats, index, play->player.x, play->run.goal_x - play->player.x, play->run.stage->theme->night);
    weather_start(&play->weather, play->run.stage->weather, camera_left(play->player.x));
    float river_xs[8];
    int rivers = 0;
    for (int i = 0; i < play->run.terrain.count && rivers < 8; i++) {
        if (play->run.terrain.items[i].kind == TERRAIN_RIVER)
            river_xs[rivers++] = play->run.terrain.items[i].x;
    }
    scene_set_rivers(river_xs, rivers, terrain_half_width(TERRAIN_RIVER));
    play->splash_timer = 0.0f;
    play->footstep_phase = -1;
    play->thunder_wait = -1.0f;
    play->faint_timer = 0.0f;
    hallucination_clear(&play->visions);
    for (int k = 0; k < RUN_MAX_ZOMBIES; k++)
        play->prev_zombie_x[k] = play->run.zombies[k].x;
}

/* Popups above her head: XP earned on this update and any level reached. */
static void announce_rewards(const StagePlay *play, const Progress *progress)
{
    char str[48];
    /* Clear of her level badge (hud.c), which hangs over her hat. */
    int above_tag = BASELINE - PLAYER_HEAD_HEIGHT * SPRITE_SCALE - BADGE_H * BADGE_SCALE - 14;
    if (play->run.xp_gained > 0) {
        snprintf(str, sizeof(str), "+%d XP", play->run.xp_gained);
        hud_popup(str, COLOR_HUD_XP, play->player.x, above_tag - 20, false);
    }
    if (play->run.levels_gained > 0) {
        snprintf(str, sizeof(str), "¡NIVEL %d!", progress->level);
        hud_popup(str, COLOR_HUD_LEVEL, play->player.x, above_tag - 56, true);
    }
}

/* The gun in hand fires: its pellets stacked around the muzzle, each with the
 * gun's damage at her weapon level. */
static void fire_weapon(StagePlay *play, const Progress *progress)
{
    const WeaponDef *w = weapon_in_hand(play);
    const Player *player = &play->player;
    float mx, my;
    player_muzzle(player, &mx, &my);
    if (player->shot.other_gun && w->shoot_other_sheet) { /* Her far gun is nearer and lower than the near one */
        mx -= (float)player->facing * PLAYER_FAR_GUN_BACK * SPRITE_SCALE;
        my += PLAYER_FAR_GUN_ROWS * SPRITE_SCALE;
    }
    BulletSpec spec = {progress_damage(progress) * w->damage_mult, w->speed, w->range,
                       w->armor_share, w->tint, 0.0f, false};
    if (play->ricochet_armed) { /* F: both hands together, two bullets that glance on to a second target */
        spec.ricochet = true;
        spec.tint = 0xffffff; /* Gold on her own sprite */
        spec.damage *= RICOCHET_SHARE;
        play->ricochet_armed = false;
        play->ricochet_fired = true;
        float nx, ny;
        player_muzzle(player, &nx, &ny);
        bool both = w->shoot_other_sheet != NULL;
        for (int k = 0; k < 2; k++) {
            int back = both && k ? PLAYER_POWER_FAR_BACK : PLAYER_POWER_BACK;
            int rows = both ? (k ? PLAYER_POWER_FAR_ROWS : PLAYER_POWER_ROWS)
                            : PLAYER_POWER_ROWS + (k ? PLAYER_POWER_GAP : -PLAYER_POWER_GAP);
            float x = nx - (float)player->facing * (float)(back * SPRITE_SCALE);
            float y = ny + (float)(rows * SPRITE_SCALE);
            bullets_fire(&play->bullets, player->x, x, y, player->facing, &spec);
            smoke_emit(&play->smoke, x, y, player->facing, w->smoke_puffs, w->smoke_scale);
        }
        if (w->shot_sound)
            play_sound(w->shot_sound);
        return;
    }
    for (int p = 0; p < w->pellets; p++) {
        float side = (float)p - (float)(w->pellets - 1) / 2.0f;
        spec.slope = side * w->pellet_spread;
        bullets_fire(&play->bullets, player->x, mx, my + side * w->pellet_gap, player->facing, &spec);
    }
    smoke_emit(&play->smoke, mx, my, player->facing, w->smoke_puffs, w->smoke_scale);
    if (w->shot_sound)
        play_sound(w->shot_sound);
    if (w->cycle_sound)
        play_sound(w->cycle_sound); /* The action between shots, not a new magazine */
}

/* The supply wagon: every gun's magazine full again (a reload going on is done). */
static void refill_guns(StagePlay *play)
{
    for (int w = 0; w < CHARACTER_MAX_WEAPONS; w++)
        play->rounds[w] = -1;
    if (shot_reloading(&play->player.shot))
        shot_cancel(&play->player.shot);
    equip_weapon(play);
}

/* Whether any of her guns with a magazine is missing a round (a bench reloads them). */
static unsigned guns_need_reload(const StagePlay *play)
{
    const CharacterDef *c = play->character;
    unsigned guns = 0;
    for (int w = 0; w < c->weapon_count; w++) {
        const WeaponDef *gun = weapon_def(play->guns[w]);
        int magazine = play->single_fire && gun->single_magazine > 0 ? gun->single_magazine : gun->magazine;
        int rounds = w == play->weapon_slot ? play->player.shot.rounds : play->rounds[w];
        if (magazine > 0 && rounds >= 0 && rounds < magazine)
            guns |= 1u << w;
    }
    return guns;
}

/* One gun's magazine full (a reload of it going on is done). */
static void refill_gun(StagePlay *play, int slot)
{
    play->rounds[slot] = -1;
    if (slot != play->weapon_slot)
        return;
    if (shot_reloading(&play->player.shot))
        shot_cancel(&play->player.shot);
    equip_weapon(play);
}

/* A crate's ammunition: the gun in hand's magazine full (a reload going on is done). */
static void refill_gun_in_hand(StagePlay *play)
{
    play->rounds[play->weapon_slot] = -1;
    if (shot_reloading(&play->player.shot))
        shot_cancel(&play->player.shot);
    equip_weapon(play);
}

/* The SWAT's ability: switch guns at any moment. A shot or a magazine reload
 * in progress is dropped: the gun keeps what it had (an unfinished reload
 * left it empty), so swapping never reloads for free. */
static void swap_weapon(StagePlay *play)
{
    if (play->character->weapon_count < 2 || !player_alive(&play->player))
        return;
    const WeaponDef *before = weapon_in_hand(play);
    if (play->player.state != PLAYER_SIT)
        audio_stop(before->reload_sound);
    audio_stop(before->cycle_sound);
    if (play->player.shot.active)
        shot_cancel(&play->player.shot);
    play->rounds[play->weapon_slot] = play->player.shot.rounds;
    play->weapon_slot = (play->weapon_slot + 1) % play->character->weapon_count;
    equip_weapon(play);
    play_sound("weapons/switch");
    const WeaponDef *w = weapon_in_hand(play);
    hud_popup(w->name, COLOR_HUD_PRIMARY, play->player.x,
              BASELINE - PLAYER_HEAD_HEIGHT * SPRITE_SCALE - BADGE_H * BADGE_SCALE - 34, false);
}

static bool can_swap_duals(const StagePlay *play, const Progress *progress)
{
    return play->character->power == POWER_DUAL_PISTOLS && (DUALS_FROM_ANY_LEVEL || progress->level >= POWER_LEVEL);
}

/* Q with the duals in reach: the second pistol out of the belt, or back in it. */
static void swap_duals(StagePlay *play, const Progress *progress)
{
    Player *player = &play->player;
    if (!can_swap_duals(play, progress) || !player_alive(player) || player->jump.airborne ||
        player->state == PLAYER_SIT || player->state == PLAYER_CAUGHT || player->swap_time > 0.0f)
        return;
    const WeaponDef *before = weapon_in_hand(play);
    audio_stop(before->cycle_sound);
    if (player->shot.active)
        shot_cancel(&player->shot);
    play->duals_out = !play->duals_out;
    set_guns(play, progress->level);
    equip_weapon(play);
    player_swap(player, !play->duals_out);
    play_sound("weapons/switch");
    hud_popup(weapon_in_hand(play)->name, COLOR_HUD_PRIMARY, player->x,
              BASELINE - PLAYER_HEAD_HEIGHT * SPRITE_SCALE - BADGE_H * BADGE_SCALE - 34, false);
}

/* Leaving or retrying: what she earned only counts once the stage is cleared. */
static void drop_unearned(StagePlay *play, Progress *progress)
{
    if (play->run.phase != RUN_CLEARED)
        *progress = play->progress_at_start;
}

/* F: the character's level-3 power, if it has come and is ready. The SWAT
 * throws a grenade; the cowgirl fires a ricochet shot right away (input gets
 * the trigger). Either then waits POWER_COOLDOWN. */
static void use_power(StagePlay *play, InputState *input, const Progress *progress)
{
    const CharacterDef *c = play->character;
    Player *player = &play->player;
    if (play->power_cooldown > 0.0f || progress->level < POWER_LEVEL || !player_alive(player) ||
        play->run.phase != RUN_FIGHTING)
        return;
    if (c->power == POWER_GRENADES) {
        if (player_throw(player))
            play->power_cooldown = POWER_COOLDOWN;
    } else if (c->power == POWER_DUAL_PISTOLS) {
        if (player->shot.active || player->jump.airborne)
            return;
        play->ricochet_armed = true;
        player->power_shot = true;
        play->power_cooldown = POWER_COOLDOWN;
        input->pressed[ACTION_SHOOT] = true;
    }
}

/* The pause menu, while paused. Returns false to go back to the stage menu. */
static bool pause_step(StagePlay *play, const InputState *input, Progress *progress)
{
    if (play->pause_view == PAUSE_VIEW_VOLUME) {
        if (!volume_step(input))
            play->pause_view = PAUSE_VIEW_LIST;
        return true;
    }
    if (play->pause_view == PAUSE_VIEW_CONTROLS) {
        if (input->pressed[ACTION_QUIT] || input->pressed[ACTION_CONFIRM])
            play->pause_view = PAUSE_VIEW_LIST;
        return true;
    }
    if (input->pressed[ACTION_QUIT]) {
        play->paused = false;
        return true;
    }
    switch (list_menu_update(&play->pause_menu, input)) {
    case PAUSE_CONTINUE:
        play->paused = false;
        return true;
    case PAUSE_RETRY:
        drop_unearned(play, progress);
        start_stage(play, play->run.stage_index, play->character, progress);
        return true;
    case PAUSE_ALMANAC:
        play->request_almanac = true;
        return true;
    case PAUSE_VOLUME:
        list_menu_init(&volume_menu, VOLUME_ROWS);
        play->pause_view = PAUSE_VIEW_VOLUME;
        return true;
    case PAUSE_CONTROLS:
        play->pause_view = PAUSE_VIEW_CONTROLS;
        return true;
    case PAUSE_LEAVE:
        drop_unearned(play, progress);
        return false;
    default:
        return true;
    }
}

/* Drain the events only after bullets, blows and the stage have all run.
 * A bit per material prevents a shotgun's pellets multiplying the volume. */
static void play_run_sounds(StageRun *run)
{
    static const struct { unsigned event; const char *name; } sounds[] = {
        {RUN_SOUND_HIT_WOOD, "world/hit_wood"},
        {RUN_SOUND_HIT_METAL, "world/hit_metal"},
        {RUN_SOUND_HIT_STONE, "world/hit_stone"},
        {RUN_SOUND_HIT_SAND, "world/hit_sand"},
        {RUN_SOUND_HIT_WIRE, "world/hit_wire"},
        {RUN_SOUND_HIT_FLESH, "effects/hit_flesh"},
        {RUN_SOUND_HIT_ARMOR, "effects/hit_armor"},
        {RUN_SOUND_TRAP_BEAR, "world/snap"},
        {RUN_SOUND_TRAP_ROPE, "world/rope"},
        {RUN_SOUND_TRAP_SPIKES, "world/hit_metal"},
    };
    unsigned events = run_take_sound_events(run);
    for (size_t s = 0; s < sizeof(sounds) / sizeof(sounds[0]); s++) {
        if (events & sounds[s].event)
            play_sound(sounds[s].name);
    }
}

static void stage_weather_sound(StagePlay *play)
{
    if (play->run.phase == RUN_FIGHTING && weather_blows(&play->weather))
        audio_loop_in("weather/wind", SOUND_MASTER, play->weather.kind == WEATHER_STORM ? 0.60f : 0.45f);
    else
        audio_stop_loop("weather/wind");
    if (play->run.phase == RUN_FIGHTING && weather_rains(&play->weather))
        audio_loop_in("weather/rain", SOUND_MASTER, play->weather.kind == WEATHER_STORM ? 0.65f : 0.45f);
    else
        audio_stop_loop("weather/rain");
}

/* Opens the pause menu over the frozen stage. */
static void stage_pause(StagePlay *play)
{
    play->paused = true;
    play->pause_view = PAUSE_VIEW_LIST;
    list_menu_init(&play->pause_menu, PAUSE_ITEMS);
}

/* One fixed step of a stage. Returns false to go back to the stage menu. */
static bool stage_step(StagePlay *play, const InputState *input, Profile *profile)
{
    Player *player = &play->player;
    Progress *progress = &profile->progress;
    if (input->pressed[ACTION_ALMANAC]) {
        play->request_almanac = true;
        return true;
    }
    if (play->paused) {
        hud_update(0.0f);
        return pause_step(play, input, progress);
    }
    if (input->pressed[ACTION_LIGHT]) {
        play->flashlight = !play->flashlight;
        play->flashlight_since = 0.0f;
        audio_play("ui/confirm");
    }
    play->flashlight_since += FIXED_DT;
    almanac_observe(&profile->almanac, &play->encounter, play->run.zombies,
                    play->run.zombie_count, camera_left(player->x), VIEW_WIDTH);
    bool cleared = play->run.phase == RUN_CLEARED;
    if (cleared && (input->pressed[ACTION_CONFIRM] || input->pressed[ACTION_QUIT]))
        return false;
    if (input->pressed[ACTION_QUIT]) {
        stage_pause(play);
        return true;
    }
    if (play->run.phase == RUN_FAILED && play->player.fainted) /* Out cold: it starts over by itself */
        play->faint_timer += FIXED_DT;
    if (play->run.phase == RUN_FAILED &&
        (input->pressed[ACTION_RELOAD] || input->pressed[ACTION_CONFIRM] || play->faint_timer >= FAINT_RESTART)) {
        drop_unearned(play, progress);
        start_stage(play, play->run.stage_index, play->character, progress);
        return true;
    }
    PlayerState previous_state = player->state;
    bool was_alive = player_alive(player);
    bool was_airborne = player->jump.airborne;
    int previous_health = player->health;
    float previous_hurt = player->hurt_time;
    float previous_x = player->x;
    int previous_sit_gun = player->sit_gun;
    float previous_sit_reload = player->sit_gun_time;
    float previous_drink = player->drink_time;
    float previous_bandage = player->bandage;
    if (input->pressed[ACTION_SWAP]) {
        swap_weapon(play);
        swap_duals(play, progress);
    }
    if (input->pressed[ACTION_FIRE_MODE])
        toggle_fire_mode(play);
    /* E: a charge on the wall she is at; a seat on the bench there; else a
     * charge planted on the road. Lighting one cuts a reload or a shot short. */
    if (input->pressed[ACTION_USE]) {
        if (run_use(&play->run, player)) {
            play_sound("world/fuse");
            player_plant(player);
            /* Lighting it takes her hands: a reload or a shot under way
             * stops there, the gun left as it was (never filled). */
            if (player->shot.active) {
                const WeaponDef *w = weapon_in_hand(play);
                if (shot_reloading(&player->shot) && w->reload_sound)
                    audio_stop(w->reload_sound);
                if (w->cycle_sound)
                    audio_stop(w->cycle_sound);
                shot_cancel(&player->shot);
            }
        } else if (run_sit(&play->run, player, guns_need_reload(play))) {
            play_sound("world/sit");
        }
    }
    if (input->pressed[ACTION_VAULT])
        run_vault(&play->run, player);
    if (input->pressed[ACTION_MELEE] && play->run.phase == RUN_FIGHTING) {
        if (player->state == PLAYER_CAUGHT) { /* At the ropes */
            play_sound(weapon_in_hand(play)->melee_sound);
            play_sound(player_struggle(player) ? "world/trap_escape" : "world/rope");
        } else {
            if (player_melee(player))
                play_sound(weapon_in_hand(play)->melee_sound);
        }
    }

    for (int k = 0; k < RUN_MAX_ZOMBIES; k++)
        play->prev_zombie_x[k] = play->run.zombies[k].x;
    bool was_reloading = shot_reloading(&player->shot);
    int previous_rounds = player->shot.rounds;
    const WeaponDef *weapon = weapon_in_hand(play);
    run_place_player(&play->run, player);
    InputState in = *input;
    play->power_cooldown = fmaxf(0.0f, play->power_cooldown - FIXED_DT);
    if (in.pressed[ACTION_POWER])
        use_power(play, &in, progress);
    player_update(player, &in, FIXED_DT);
    if (player->threw) {
        run_throw(&play->run, player);
        play_sound("weapons/grenade_throw");
    }
    if (player->struck) {
        run_melee(&play->run, player, progress);
    }
    for (int d = 0; d < BLOOD_DROPS; d++)
        play->blood_age[d] += FIXED_DT;
    play->blood_timer -= FIXED_DT;
    if (player->bleeding && play->blood_timer <= 0.0f) { /* A drop where she is */
        play->blood_timer = BLOOD_EVERY;
        float jitter = (float)((play->blood_next * 37) % 9 - 4) * SPRITE_SCALE;
        play->blood_x[play->blood_next] = player->x + jitter;
        play->blood_age[play->blood_next] = 0.0f;
        play->blood_next = (play->blood_next + 1) % BLOOD_DROPS;
    }
    if (shot_reloading(&player->shot) && !was_reloading)
        play_sound(weapon->reload_sound);
    if (was_reloading && input->pressed[ACTION_JUMP])
        audio_stop(weapon->cycle_sound);
    if (weapon->magazine > 0 &&
        ((previous_rounds > 0 && player->shot.rounds == 0) ||
         (previous_rounds == 0 && input->pressed[ACTION_SHOOT] && !was_reloading)))
        play_sound(weapon->empty_sound);
    bullets_update(&play->bullets, FIXED_DT, camera_left(player->x));
    if (player->shot_fired) {
        fire_weapon(play, progress);
        crows_noise(&play->crows, player->x, CROW_SHOT_RANGE);
    }
    if (crows_shoot(&play->crows, &play->bullets) > 0)
        play_sound("crow/death");
    if (bats_shoot(&play->bats, &play->bullets) > 0)
        play_sound("crow/death"); /* A screech and wings: it serves a bat too */
    hallucination_shoot(&play->visions, &play->bullets); /* A bullet wasted on nothing */
    run_bullets(&play->run, &play->bullets, &play->effects);
    if (play->bullets.glances > 0) {
        play_sound("weapons/ricochet");
        play->bullets.glances = 0;
    }
    /* Her ricochet over: her hands part, for the shot that ended or the next turn. */
    if (player->power_shot && !play->ricochet_armed && (!player->shot.active || (play->ricochet_fired && !player->shot.fired))) {
        player->power_shot = false;
        play->ricochet_fired = false;
    }
    effects_update(&play->effects, FIXED_DT);
    smoke_update(&play->smoke, FIXED_DT);

    StageRun *run = &play->run;
    run_update(run, player, progress, FIXED_DT);
    almanac_observe(&profile->almanac, &play->encounter, run->zombies,
                    run->zombie_count, camera_left(player->x), VIEW_WIDTH);
    if (run->levels_gained > 0) { /* Stronger, but her wounds stay: only rests heal */
        play_sound("world/level_up");
        player_set_stats(player, progress->level, progress_max_health(progress),
                         character_armor(play->character, progress->armor_level), false);
        if (progress->level - run->levels_gained < POWER_LEVEL && progress->level >= POWER_LEVEL)
            play->duals_out = true; /* Its power's gun, from now on */
        if (set_guns(play, progress->level))
            equip_weapon(play);
        if (progress->level - run->levels_gained < POWER_LEVEL && progress->level >= POWER_LEVEL &&
            play->character->power_name) {
            int above = BASELINE - PLAYER_HEAD_HEIGHT * SPRITE_SCALE - BADGE_H * BADGE_SCALE - 110;
            hud_popup(play->character->power_name, COLOR_HUD_XP, player->x, above, true);
        }
    }
    if (run->chests_opened > 0)
        play_sound("world/chest");
    for (int c = 0; c < run->chests_opened; c++)
        effects_spawn(&play->effects, chest_sparks(), run->opened_x[c], BASELINE, 1);
    for (int b = 0; b < run->blasts; b++) {
        effects_spawn(&play->effects, terrain_explosion(), run->blast_x[b], BASELINE, 1);
        const char *blast_sound = run->blast_kind[b] == BLAST_GRENADE ? "world/grenade_explosion" :
                                  run->blast_kind[b] == BLAST_DYNAMITE ? "world/dynamite_explosion" :
                                  "world/explosion";
        play_sound(blast_sound);
        if (crows_blast(&play->crows, run->blast_x[b], BARREL_RADIUS) > 0)
            play_sound("crow/death");
        if (bats_blast(&play->bats, run->blast_x[b], BARREL_RADIUS) > 0)
            play_sound("crow/death"); /* A screech and wings: it serves a bat too */
    }
    bool moving = player->state == PLAYER_WALK || player->state == PLAYER_RUN ||
                  player->state == PLAYER_JUMP;
    crows_update(&play->crows, player->x, moving, FIXED_DT);
    bats_update(&play->bats, player->x, FIXED_DT);
    if (play->crows.took_off > 0)
        play_sound("crow/caw");
    if (run->bolt_struck) { /* Right overhead: light and thunder at once */
        play->weather.flash = 1.0f;
        audio_play_in_gain("weather/thunder", SOUND_MASTER, 1.0f);
        if (run->bolt_hit_her)
            hud_popup("¡QUEMADURA!", COLOR_HUD_DANGER, player->x,
                      BASELINE - PLAYER_HEAD_HEIGHT * SPRITE_SCALE - BADGE_H * BADGE_SCALE - 34, false);
    }
    float previous_flash_wait = play->weather.flash_wait;
    weather_update(&play->weather, camera_left(player->x), FIXED_DT);
    if (play->weather.kind == WEATHER_STORM && play->weather.flash_wait > previous_flash_wait)
        play->thunder_wait = 0.28f; /* A little distance between light and sound */
    if (play->thunder_wait >= 0.0f) {
        play->thunder_wait -= FIXED_DT;
        if (play->thunder_wait <= 0.0f) {
            audio_play_in_gain("weather/thunder", SOUND_MASTER, 0.85f);
            play->thunder_wait = -1.0f;
        }
    }
    stage_weather_sound(play);
    hallucination_update(&play->visions, player_thirst_level(player) >= 3 && player_alive(player), player->x,
                         player->facing, camera_left(player->x), FIXED_DT);
    for (int v = 0; v < play->visions.vanished; v++) /* Gone like smoke */
        smoke_rise(&play->smoke, play->visions.vanished_x[v], BASELINE - 120.0f, 3, 1.0f);
    /* Feet in water: a splash now and then under whoever walks there. */
    play->splash_timer -= FIXED_DT;
    if (play->splash_timer <= 0.0f) {
        play->splash_timer = SPLASH_EVERY;
        if (moving && player->jump.height <= 0.0f && terrain_splash(&run->terrain, player->x))
            effects_spawn(&play->effects, effect_splash(), player->x, BASELINE, player->facing);
        for (int k = 0; k < run->zombie_count; k++) {
            const Zombie *z = &run->zombies[k];
            if (z->awake && !z->hidden && zombie_alive(z) && z->state == ZOMBIE_WALK && z->caught <= 0.0f &&
                terrain_splash(&run->terrain, z->x))
                effects_spawn(&play->effects, effect_splash(), z->x, BASELINE, z->facing);
        }
    }
    int above_tag = BASELINE - PLAYER_HEAD_HEIGHT * SPRITE_SCALE - BADGE_H * BADGE_SCALE - 34;
    if (run->supply_taken) {
        refill_guns(play);
        play_sound("world/supply");
        char str[48];
        snprintf(str, sizeof(str), "¡PROVISIONES!  +%d DINAMITA  +%d AGUA", stage_supply_dynamite(run->stage),
                 SUPPLY_WATER);
        hud_popup(str, COLOR_HUD_XP, player->x, above_tag, true);
    }
    if (run->dynamite_taken) {
        play_sound("world/supply");
        hud_popup("+1 DINAMITA", COLOR_HUD_TITLE, player->x, above_tag, true);
    }
    static const char *const LOOT_TEXT[] = {"+BALAS", "+VIDA", "+1 DINAMITA", "+ORO", "+1 AGUA"};
    static const unsigned LOOT_RGB[] = {COLOR_HUD_PRIMARY, COLOR_HUD_XP, COLOR_HUD_TITLE, COLOR_HUD_TITLE,
                                        COLOR_HUD_PRIMARY};
    for (int l = 0; l < run->loot_count; l++) {
        play_sound("world/wood");
        if (run->loot[l] == LOOT_AMMO)
            refill_gun_in_hand(play);
        char gold[24];
        snprintf(gold, sizeof(gold), "+%d ORO", run_crate_gold(run));
        const char *text = run->loot[l] == LOOT_GOLD ? gold : LOOT_TEXT[run->loot[l]];
        hud_popup(text, LOOT_RGB[run->loot[l]], run->loot_x[l], above_tag + 40, false);
    }
    for (int b = 0; b < run->bottles_hit; b++) {
        play_sound("world/glass");
        hud_popup("¡BUEN TIRO!", COLOR_HUD_TITLE, player->x, above_tag, true);
    }
    play_run_sounds(run);
    if (run->coffins_burst > 0)
        play_sound("world/wood");
    if (run->wire_bit)
        play_sound("world/wire");
    if (previous_drink <= 0.0f && player->drink_time > 0.0f)
        play_sound("player/drink");
    if (previous_drink > 0.0f && player->drink_time <= 0.0f && !player->drank)
        audio_stop("player/drink");
    if (player->drank) {
        hud_popup("¡HIDRATADO!", COLOR_HUD_XP, player->x, above_tag, true);
    }
    if (previous_bandage <= 0.0f && player->bandage > 0.0f)
        play_sound("player/bandage");
    if (previous_bandage > 0.0f && player->bandage <= 0.0f && !player->bandaged)
        audio_stop("player/bandage");
    if (player->bandaged) {
        hud_popup("SANGRADO DETENIDO", COLOR_HUD_XP, player->x, above_tag, true);
    }
    if (player->sit_reloaded) { /* A gun's sitting reload is done; the next starts */
        refill_gun(play, player->sit_reloaded_gun);
    }
    if (player->state == PLAYER_SIT && player->sit_gun >= 0 && player->sit_gun_time > 0.0f) {
        const WeaponDef *sat_weapon = weapon_def(play->guns[player->sit_gun]);
        /* The bench's animation is longer than the standing reload. Keep
         * the actual mechanism at its natural speed; its final latch lands
         * when this gun finishes, rather than speeding up its recording. */
        float sound_at = fmaxf(0.0f, SIT_RELOAD_TIME - sat_weapon->magazine_reload);
        if (player->sit_gun_time >= sound_at &&
            (previous_sit_gun != player->sit_gun || previous_sit_reload < sound_at ||
             previous_sit_reload <= 0.0f))
            play_sound(sat_weapon->reload_sound);
    }
    if (previous_state == PLAYER_SIT && player->state != PLAYER_SIT) {
        if (player_alive(player) && player->state != PLAYER_CAUGHT)
            play_sound("world/stand");
        if (previous_sit_gun >= 0)
            audio_stop(weapon_def(play->guns[previous_sit_gun])->reload_sound);
    }
    if (was_alive && !player_alive(player)) {
        audio_stop(weapon->cycle_sound);
        audio_stop(weapon->reload_sound);
        audio_stop("player/drink");
        audio_stop("player/bandage");
        play_sound(player->fainted ? "player/faint" : "player/death");
    } else if (player_alive(player) &&
               (player->health < previous_health || player->hurt_time > previous_hurt)) {
        play_sound("player/hurt");
    }
    if (was_alive && player_alive(player)) {
        if (!was_airborne && player->jump.airborne && player->state != PLAYER_CAUGHT &&
            (input->pressed[ACTION_JUMP] || input->pressed[ACTION_VAULT])) {
            audio_stop(weapon->cycle_sound);
            play_sound("player/jump");
        }
        if (was_airborne && !player->jump.airborne && player->state != PLAYER_CAUGHT)
            play_sound("player/land");
        /* While reloading on the move, her legs are the ones walking. */
        const Animation *feet = player->reload_walk ? &player->legs : &player->anim;
        if ((player->state == PLAYER_WALK || player->state == PLAYER_RUN) && !player->jump.airborne &&
            feet->def != NULL && feet->def->frame_w == PLAYER_WALK_FRAME_W) {
            /* A foot lands on frames 0 and 4 of the walk, so the steps keep
             * time with the legs whatever slows them (a river, the wind). */
            int phase = (feet->frame - feet->def->first_frame) / (PLAYER_WALK_FRAMES / 2);
            if (play->footstep_phase >= 0 && phase != play->footstep_phase && player->x != previous_x) {
                /* Under everything else, and never twice the same: one foot
                 * lands a little harder than the other, and now and then a
                 * step is lighter, as on uneven dirt. Feet stuck against
                 * something stay quiet. */
                bool running = player->state == PLAYER_RUN;
                play->footstep_count++;
                float gain = running ? FOOTSTEP_RUN_GAIN : FOOTSTEP_GAIN;
                gain *= play->footstep_count % 2 ? 1.0f : 0.8f;
                if (play->footstep_count % 5 == 3)
                    gain *= 0.75f;
                audio_play_in_gain(footstep_sound(running, terrain_water_at(&run->terrain, player->x),
                                                  play->footstep_count),
                                   SOUND_PLAYER, gain);
            }
            play->footstep_phase = phase;
        } else {
            play->footstep_phase = -1;
        }
    }
    if (run->healed > 0) { /* A green aura and a + off her head */
        char str[16];
        snprintf(str, sizeof(str), "+%d", run->healed);
        effects_spawn(&play->effects, terrain_heal_effect(), player->x, BASELINE - player->jump.height, 1);
        player->heal_time = HEAL_GLOW_TIME;
        hud_popup(str, COLOR_HUD_XP, player->x, above_tag + 20, true);
        play_sound("world/supply");
        run->healed = 0;
    }
    /* Smoke rising off fires and campfires; a cloud off every blast. */
    play->smoke_timer -= FIXED_DT;
    if (play->smoke_timer <= 0.0f) {
        play->smoke_timer += SMOKE_EVERY;
        float xs[TERRAIN_MAX];
        int n = terrain_smokes(&run->terrain, xs, TERRAIN_MAX);
        for (int i = 0; i < n; i++)
            smoke_rise(&play->smoke, xs[i], BASELINE - 50.0f, 1, 1.0f);
    }
    for (int b = 0; b < run->blasts; b++)
        smoke_rise(&play->smoke, run->blast_x[b], BASELINE - 80.0f, 10, 2.0f);
    if (run->elite_woke)
        hud_popup("¡ZOMBI DE ÉLITE!", COLOR_HUD_DANGER, player->x, above_tag, true);
    if (run->ambushed) { /* They walk in from off screen: no sliding in from their old spot */
        play_sound("world/ambush");
        hud_popup("¡EMBOSCADA!", COLOR_HUD_DANGER, player->x, above_tag, true);
        for (int k = 0; k < run->zombie_count; k++)
            play->prev_zombie_x[k] = run->zombies[k].x;
    }
    if (run->crate_hint)
        hud_popup("¡DISPARA A LAS CAJAS: TIENEN PREMIO!", COLOR_HUD_TITLE, player->x, above_tag - 40, true);
    if (run->group_beaten && run->defeated < run->stage->zombies)
        hud_popup("¡ADELANTE!  →", COLOR_HUD_TITLE, player->x, above_tag, true);
    announce_rewards(play, progress);
    if (run->cleared_now) {
        play_sound("world/victory");
        profile->record.cleared[run->stage_index] = true;
    }
    /* A pickup or a rope trap can cancel a reload inside run_update, after
     * player_update has already run. Check after all those events as well. */
    if (was_reloading && !shot_reloading(&player->shot))
        audio_stop(weapon->reload_sound);
    if (player->state == PLAYER_CAUGHT && previous_state != PLAYER_CAUGHT) {
        audio_stop(weapon->reload_sound);
        audio_stop(weapon->cycle_sound);
    }
    for (int k = 0; k < run->zombie_count; k++)
        play_zombie_voice(&run->zombies[k]);
    hud_update(FIXED_DT);
    return true;
}

/* From here on, drawing goes into the view: VIEW_WIDTH x VIEW_HEIGHT world
 * px shrunk to VIEW_SCALE at the window's bottom, the sky's color above. */
static void begin_view(SDL_Renderer *renderer, const ThemeDef *theme)
{
    SDL_Rect band = {0, 0, WINDOW_WIDTH, VIEW_TOP + 1};
    platform_set_color(renderer, scene_sky_top(theme));
    SDL_RenderClear(renderer);
    SDL_RenderFillRect(renderer, &band);
    SDL_RenderSetScale(renderer, VIEW_SCALE, VIEW_SCALE);
    SDL_Rect view = {0, (int)(VIEW_TOP / VIEW_SCALE), VIEW_WIDTH, VIEW_HEIGHT};
    SDL_RenderSetViewport(renderer, &view);
}

static void end_view(SDL_Renderer *renderer)
{
    SDL_RenderSetViewport(renderer, NULL);
    SDL_RenderSetScale(renderer, 1.0f, 1.0f);
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
static void draw_heat(SDL_Renderer *renderer, float camera_x, double time)
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
static void draw_crows(SDL_Renderer *renderer, const Crows *crows, float camera_x)
{
    SDL_Texture *sheet = assets_texture("sprites/crow/crow");
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

static void draw_stage(Platform *platform, StagePlay *play, const CharacterSkin *skin,
                       const Progress *progress, float alpha, float prev_player_x,
                       float prev_jump)
{
    Player player_view = play->player;
    player_view.light_on = play->flashlight;
    player_view.light_since = play->flashlight_since;
    player_view.light_time = weapon_in_hand(play)->light_time;
    player_view.light_rows = weapon_in_hand(play)->light_rows;
    player_view.light_swings = weapon_in_hand(play)->melee_lit_sheet != NULL;
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
    begin_view(platform->renderer, play->world.theme);
    bool separated_light = false;
    float flashlight_time = weapon_in_hand(play)->light_time > 0.0f ? weapon_in_hand(play)->light_time : 1.0f;
    float flashlight = lighting_flashlight_power(play->flashlight, play->flashlight
                                                     ? play->flashlight_since - flashlight_time * PLAYER_LIGHT_CLICK
                                                     : play->flashlight_since);
    if (play->world.theme->night || flashlight > 0.0f) { /* What it lights apart from the far land */
        scene_draw_distant(platform->renderer, &play->world, camera_x);
        separated_light = scene_begin_foreground(platform->renderer);
        scene_draw_near(platform->renderer, &play->world, camera_x, platform_time());
    } else {
        scene_draw(platform->renderer, &play->world, camera_x, platform_time());
    }
    terrain_render(platform->renderer, &play->run.terrain, camera_x);
    draw_blood(platform->renderer, play, camera_x);
    draw_crows(platform->renderer, &play->crows, camera_x);
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
    Lighting lighting;
    lighting_build(&lighting, &play->run.terrain, &play->effects, &player_view,
                    play->world.theme->night, flashlight, camera_x, platform_time());
    if (separated_light)
        terrain_render_surface_lights(platform->renderer, &lighting, &player_view, zombie_view, zombie_count, camera_x);
    else
        terrain_render_lights(platform->renderer, &lighting, &player_view, zombie_view, zombie_count, camera_x);
    if (play->run.stage->hot)
        draw_heat(platform->renderer, camera_x, platform_time());
    draw_heatstroke(platform->renderer, play->player.fatigue, platform_time());
    if (separated_light) {
        scene_end_foreground(platform->renderer);
        terrain_render_light_bloom(platform->renderer, &lighting, camera_x);
    }
    end_view(platform->renderer);
    weather_render(platform->renderer, &play->weather, camera_x);
    const CharacterDef *c = play->character;
    const WeaponDef *w = weapon_in_hand(play);
    char gun_name[40];
    if (w->single_magazine > 0)
        snprintf(gun_name, sizeof(gun_name), "%s %s", w->name, single_fire(play) ? "1x1" : "AUTO");
    else
        snprintf(gun_name, sizeof(gun_name), "%s", w->name);
    HudWeapon gun = {
        .id = play->guns[play->weapon_slot], .name = gun_name, .rounds = play->player.shot.rounds,
        .magazine = play->player.shot.magazine, .reloading = shot_reloading(&play->player.shot),
        .can_swap = c->weapon_count > 1 || can_swap_duals(play, progress),
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
        hud_draw_volume(platform->renderer, &volume_menu, &volumes);
    else
        hud_draw_controls(platform->renderer);
}

/* Behind the menus: the first stage's landscape, drifting slowly by. */
static void draw_backdrop(Platform *platform, World *world, float dim)
{
    float camera_x = PLAYER_START_X + (float)fmod(platform_time() * 40.0, 20000.0);
    world_stream(world, camera_x);
    begin_view(platform->renderer, world->theme);
    scene_draw(platform->renderer, world, camera_x, platform_time());
    end_view(platform->renderer);
    if (dim > 0.0f)
        ui_dim(platform->renderer, (Uint8)(dim * 255.0f));
}

/* Saves what the renderer holds to dir/name.bmp (--capturas). */
static void save_capture(SDL_Renderer *renderer, const char *dir, const char *name)
{
    SDL_Surface *shot = SDL_CreateRGBSurfaceWithFormat(0, WINDOW_WIDTH, WINDOW_HEIGHT, 32,
                                                       SDL_PIXELFORMAT_ARGB8888);
    if (shot == NULL)
        return;
    char path[512];
    snprintf(path, sizeof(path), "%s/%s.bmp", dir, name);
    if (SDL_RenderReadPixels(renderer, NULL, SDL_PIXELFORMAT_ARGB8888, shot->pixels, shot->pitch) == 0 &&
        SDL_SaveBMP(shot, path) == 0)
        printf("captura: %s\n", path);
    SDL_FreeSurface(shot);
}

/* Steps a stage n times with no keys down. */
static void idle_steps(StagePlay *play, Profile *profile, InputState *input, int n)
{
    bool down[ACTION_COUNT] = {0};
    for (int i = 0; i < n; i++) {
        input_update(input, down);
        stage_step(play, input, profile);
    }
}

/* --capturas: every screen drawn once into dir, to check the interface's
 * art without playing (the menus, a fight, a wall, the pause, a defeat). */
static void capture_screens(Platform *platform, const char *dir, CharacterSkin *skins,
                            Profile *profiles, World *menu_world)
{
    SDL_Renderer *r = platform->renderer;
    static StagePlay play;
    InputState input;
    input_init(&input);
    ListMenu list;
    list_menu_init(&list, TITLE_ITEMS);
    Progress progress[8];
    for (int c = 0; c < CHARACTER_COUNT; c++)
        progress[c] = profiles[c].progress;

    draw_backdrop(platform, menu_world, 0.15f);
    hud_draw_title(r, &list);
    save_capture(r, dir, "1_titulo");
    draw_backdrop(platform, menu_world, 0.5f);
    hud_draw_controls(r);
    save_capture(r, dir, "2_controles");
    list_menu_init(&volume_menu, VOLUME_ROWS);
    draw_backdrop(platform, menu_world, 0.5f);
    hud_draw_volume(r, &volume_menu, &volumes);
    save_capture(r, dir, "3_volumen");
    draw_backdrop(platform, menu_world, 0.45f);
    hud_draw_characters(r, skins, progress, 1);
    save_capture(r, dir, "4_personajes");
    profiles[1].record.cleared[0] = true;
    draw_backdrop(platform, menu_world, 0.45f);
    hud_draw_menu(r, CHARACTERS[1].name, &profiles[1].progress, &profiles[1].record, 1);
    save_capture(r, dir, "5_niveles");
    profiles[1].record.cleared[0] = false;

    /* The SWAT in 1-1, the first zombie woken and coming. */
    start_stage(&play, 0, &CHARACTERS[1], &profiles[1].progress);
    play.player.x = play.run.zombies[0].x - ROUTE_WAKE_DISTANCE + 20.0f;
    idle_steps(&play, &profiles[1], &input, 150);
    draw_stage(platform, &play, &skins[1], &profiles[1].progress, 1.0f, play.player.x,
               play.player.jump.height);
    save_capture(r, dir, "6_pelea");

    /* At the first wall with a box of dynamite. */
    for (int i = 0; i < play.run.terrain.count; i++) {
        const Piece *piece = &play.run.terrain.items[i];
        if (piece->kind == TERRAIN_WALL) {
            play.player.x = piece->x - terrain_half_width(TERRAIN_WALL) - PLAYER_BODY_HALF_WIDTH;
            break;
        }
    }
    for (int k = 0; k < play.run.zombie_count; k++) { /* Out of this picture */
        play.run.zombies[k].x = play.run.goal_x + 1e4f;
        play.run.zombies[k].awake = false;
    }
    play.run.dynamite = 1;
    idle_steps(&play, &profiles[1], &input, 2);
    draw_stage(platform, &play, &skins[1], &profiles[1].progress, 1.0f, play.player.x,
               play.player.jump.height);
    save_capture(r, dir, "7_muro");

    stage_pause(&play);
    draw_stage(platform, &play, &skins[1], &profiles[1].progress, 1.0f, play.player.x,
               play.player.jump.height);
    save_capture(r, dir, "8_pausa");
    play.paused = false;
    player_hit(&play.player, 1e6f, 1);
    idle_steps(&play, &profiles[1], &input, 2);
    draw_stage(platform, &play, &skins[1], &profiles[1].progress, 1.0f, play.player.x,
               play.player.jump.height);
    save_capture(r, dir, "9_derrota");

    /* 1-4 at night: sat on the bench by the campfire, dozing off. */
    start_stage(&play, 3, &CHARACTERS[1], &profiles[1].progress);
    for (int k = 0; k < play.run.zombie_count; k++) {
        play.run.zombies[k].x = play.run.goal_x + 1e4f;
        play.run.zombies[k].awake = false;
    }
    int bench = -1;
    for (int i = 0; i < play.run.terrain.count && bench < 0; i++) {
        if (play.run.terrain.items[i].kind == TERRAIN_BENCH)
            bench = i;
    }
    if (bench >= 0) {
        play.player.x = play.run.terrain.items[bench].x;
        play.player.health = play.player.max_health / 2;
        run_sit(&play.run, &play.player, 0);
        idle_steps(&play, &profiles[1], &input, (int)((SIT_DOWN_TIME + SIT_DOZE_TIME) / FIXED_DT) + 40);
        draw_stage(platform, &play, &skins[1], &profiles[1].progress, 1.0f, play.player.x,
                   play.player.jump.height);
        save_capture(r, dir, "10_descanso");
    }
    /* Reproducible visual checks: each weather at its real stage, including
     * the upper sky, then a crowded HUD with a reload and several ailments. */
    static const char *const weather_names[] = {NULL, "11_viento", "12_lluvia", "13_tormenta"};
    for (int kind = WEATHER_WIND; kind <= WEATHER_STORM; kind++) {
        int stage = 0;
        for (int s = 0; s < STAGE_COUNT; s++) {
            if ((int)STAGES[s].weather == kind) {
                stage = s;
                break;
            }
        }
        start_stage(&play, stage, &CHARACTERS[0], &profiles[0].progress);
        weather_start(&play.weather, (Weather)kind, camera_left(play.player.x));
        for (int step = 0; step < 150; step++)
            weather_update(&play.weather, camera_left(play.player.x), FIXED_DT);
        if (kind == WEATHER_STORM)
            play.weather.flash = 0.0f; /* Inspect the rain rather than a white flash */
        draw_stage(platform, &play, &skins[0], &profiles[0].progress, 1.0f,
                   play.player.x, play.player.jump.height);
        save_capture(r, dir, weather_names[kind]);
    }
    Progress veteran = profiles[1].progress;
    veteran.level = POWER_LEVEL;
    veteran.gold = 123456;
    start_stage(&play, 2, &CHARACTERS[1], &veteran);
    swap_weapon(&play);
    play.player.health = 27;
    play.player.water = 12;
    play.player.bleeding = true;
    play.player.slow_time = 3.0f;
    play.player.thirst = DEHYDRATED;
    play.player.wet = 1.0f;
    play.run.dynamite = 12;
    play.player.shot.rounds = 0;
    shot_reload_now(&play.player.shot);
    draw_stage(platform, &play, &skins[1], &veteran, 1.0f,
               play.player.x, play.player.jump.height);
    save_capture(r, dir, "14_hud_estados_recarga");
    veteran.gold = veteran.xp = INT_MAX;
    play.player.health = 123456789;
    play.player.max_health = INT_MAX;
    play.player.water = INT_MAX;
    play.player.cold = true;
    play.player.fatigue = FATIGUE_STROKE;
    play.run.omen = true;
    play.run.dynamite = INT_MAX;
    play.power_cooldown = 9.0f;
    draw_stage(platform, &play, &skins[1], &veteran, 1.0f,
               play.player.x, play.player.jump.height);
    save_capture(r, dir, "15_hud_contadores_largos");

    Almanac review_book;
    AlmanacView review_view;
    almanac_init(&review_book);
    almanac_view_init(&review_view);
    almanac_discover(&review_book, ZOMBIE_KIND_RIOT, false, 3);
    almanac_discover(&review_book, ZOMBIE_KIND_SOLDIER, true, 5);
    almanac_discover(&review_book, ZOMBIE_KIND_RIOT_SHIELD, false, 7);
    almanac_discover(&review_book, ZOMBIE_KIND_CIVIL_FEMALE_1, false, 2);
    almanac_view_select(&review_view, almanac_index(ZOMBIE_KIND_RIOT_SHIELD, false));
    draw_backdrop(platform, menu_world, .70f);
    almanac_render(r, &review_book, &review_view, .25f);
    save_capture(r, dir, "16_almanaque");
    review_view.detail = true;
    draw_backdrop(platform, menu_world, .70f);
    almanac_render(r, &review_book, &review_view, .25f);
    save_capture(r, dir, "17_almanaque_ficha");

    /* One fixed night scene isolates light height, occlusion and the
     * difference between a high lantern, a hand-held beam and a blast. */
    start_stage(&play, 3, &CHARACTERS[1], &profiles[1].progress);
    terrain_clear(&play.run.terrain);
    terrain_add(&play.run.terrain, TERRAIN_LAMP, play.player.x + 170.0f);
    terrain_add(&play.run.terrain, TERRAIN_BARREL, play.player.x + 320.0f);
    terrain_add(&play.run.terrain, TERRAIN_WALL, play.player.x + 520.0f);
    terrain_add(&play.run.terrain, TERRAIN_BENCH, play.player.x - 220.0f);
    play.run.zombie_count = 1;
    zombie_spawn(&play.run.zombies[0], &ZOMBIE_RIOT, play.player.x + 350.0f);
    play.prev_zombie_x[0] = play.run.zombies[0].x;
    weather_start(&play.weather, WEATHER_CLEAR, camera_left(play.player.x));
    play.flashlight = false;
    draw_stage(platform, &play, &skins[1], &profiles[1].progress, 1.0f, play.player.x, 0.0f);
    save_capture(r, dir, "18_luz_farol");
    play.flashlight = true;
    draw_stage(platform, &play, &skins[1], &profiles[1].progress, 1.0f, play.player.x, 0.0f);
    save_capture(r, dir, "19_luz_linterna");
    play.flashlight = false;
    effects_spawn(&play.effects, terrain_explosion(), play.player.x + 300.0f, BASELINE, 1);
    draw_stage(platform, &play, &skins[1], &profiles[1].progress, 1.0f, play.player.x, 0.0f);
    save_capture(r, dir, "20_luz_explosion");
    effects_update(&play.effects, .4f);
    draw_stage(platform, &play, &skins[1], &profiles[1].progress, 1.0f, play.player.x, 0.0f);
    save_capture(r, dir, "21_luz_explosion_cola");
    effects_clear(&play.effects);
    play.run.terrain.items[0].spent = true;
    terrain_add(&play.run.terrain, TERRAIN_FIRE, play.run.terrain.items[0].x);
    draw_stage(platform, &play, &skins[1], &profiles[1].progress, 1.0f, play.player.x, 0.0f);
    save_capture(r, dir, "22_farol_roto");

    /* The road's obstacles side by side (a barricade over her head, the
     * hidden snare and net), then caught by the snare, hanging. */
    start_stage(&play, 0, &CHARACTERS[0], &profiles[0].progress);
    terrain_clear(&play.run.terrain);
    play.run.zombie_count = 0;
    terrain_add(&play.run.terrain, TERRAIN_BARRICADE, play.player.x + 260.0f);
    terrain_add(&play.run.terrain, TERRAIN_SNARE, play.player.x + 560.0f);
    terrain_add(&play.run.terrain, TERRAIN_NET, play.player.x + 800.0f);
    terrain_add(&play.run.terrain, TERRAIN_SPIKES, play.player.x - 240.0f);
    weather_start(&play.weather, WEATHER_CLEAR, camera_left(play.player.x));
    draw_stage(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f);
    save_capture(r, dir, "24_obstaculos");
    Piece *wire = terrain_add(&play.run.terrain, TERRAIN_WIRE, play.player.x + 130.0f);
    draw_stage(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f);
    save_capture(r, dir, "24_alambre");
    wire->spent = true;
    play.player.x = play.run.terrain.items[1].x;
    idle_steps(&play, &profiles[0], &input, 90);
    draw_stage(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x,
               play.player.jump.height);
    save_capture(r, dir, "25_lazo");
    play.player.x = play.run.terrain.items[2].x;
    play.player.state = PLAYER_IDLE;
    play.player.jump.height = 0.0f;
    idle_steps(&play, &profiles[0], &input, 90);
    draw_stage(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x,
               play.player.jump.height);
    save_capture(r, dir, "26_red");
    play.player.catch_shake = CATCH_SHAKE_TIME * 0.5f; /* Mid-swing at the ropes */
    draw_stage(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x,
               play.player.jump.height);
    save_capture(r, dir, "26_red_golpe");
    play.player.catch_shake = 0.0f;

    /* The road's props at their size beside her: the bottles' table, a
     * crate, both benches with a campfire, a lamp and a coffin. */
    start_stage(&play, 0, &CHARACTERS[0], &profiles[0].progress);
    terrain_clear(&play.run.terrain);
    play.run.zombie_count = 0;
    float px = play.player.x;
    terrain_add(&play.run.terrain, TERRAIN_BOTTLES, px + 140.0f);
    terrain_add(&play.run.terrain, TERRAIN_CRATE, px + 270.0f);
    terrain_add(&play.run.terrain, TERRAIN_LAMP, px + 360.0f);
    terrain_add(&play.run.terrain, TERRAIN_BENCH, px + 520.0f);
    Piece *iron = terrain_add(&play.run.terrain, TERRAIN_BENCH, px + 780.0f);
    if (iron)
        iron->variant = 1;
    terrain_add(&play.run.terrain, TERRAIN_CAMPFIRE, px + 950.0f);
    terrain_add(&play.run.terrain, TERRAIN_COFFIN, px - 150.0f);
    weather_start(&play.weather, WEATHER_CLEAR, camera_left(px));
    draw_stage(platform, &play, &skins[0], &profiles[0].progress, 1.0f, px + 300.0f, 0.0f);
    save_capture(r, dir, "27_props");

    /* Wading the river's deep middle, to the waist; a puddle on the bank. */
    terrain_clear(&play.run.terrain);
    Piece *river = terrain_add(&play.run.terrain, TERRAIN_RIVER, px + 200.0f);
    terrain_add(&play.run.terrain, TERRAIN_PUDDLE, px - 380.0f);
    scene_set_rivers(&river->x, 1, terrain_half_width(TERRAIN_RIVER));
    play.player.x = river->x + 40.0f;
    play.run.zombie_count = 1;
    zombie_spawn(&play.run.zombies[0], &ZOMBIE_RIOT, river->x + 300.0f);
    play.prev_zombie_x[0] = play.run.zombies[0].x;
    idle_steps(&play, &profiles[0], &input, 4);
    draw_stage(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f);
    save_capture(r, dir, "28_rio");
    play.flashlight = true; /* Her gun and its light sunk with her */
    play.flashlight_since = 10.0f;
    draw_stage(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f);
    save_capture(r, dir, "28_rio_linterna");
    play.flashlight = false;

    /* Every shipped identity at its real gallery size. This fixture does not
     * reveal entries in the player's profile or alter campaign encounters. */
    for (int kind = 0; kind < ZOMBIE_KIND_COUNT; kind++)
        for (int runner = 0; runner < 2; runner++)
            almanac_discover(&review_book, (ZombieKind)kind, runner != 0, 5);
    review_view.detail = false;
    for (int page = 0; page < almanac_pages(); page++) {
        char name[64];
        almanac_view_select(&review_view, page * ALMANAC_PAGE_SIZE);
        draw_backdrop(platform, menu_world, .70f);
        almanac_render(r, &review_book, &review_view, .45f);
        snprintf(name, sizeof(name), "23_catalogo_%02d", page + 1);
        save_capture(r, dir, name);
    }

    /* By day, on the things in its way. */
    start_stage(&play, 1, &CHARACTERS[0], &profiles[0].progress);
    terrain_clear(&play.run.terrain);
    play.run.zombie_count = 1;
    zombie_spawn(&play.run.zombies[0], &ZOMBIE_RIOT, play.player.x + 420.0f);
    play.prev_zombie_x[0] = play.run.zombies[0].x;
    terrain_add(&play.run.terrain, TERRAIN_CRATE, play.player.x + 220.0f);
    weather_start(&play.weather, WEATHER_CLEAR, camera_left(play.player.x));
    play.flashlight = true;
    play.flashlight_since = 10.0f;
    draw_stage(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f);
    save_capture(r, dir, "29_linterna_de_dia");

    /* The flashlight: each one turning it on, then lit and walking. */
    for (int c = 0; c < 2; c++) {
        static const float MOMENTS[] = {.5f, 1.1f, 1.5f, 1.9f};
        start_stage(&play, 3, &CHARACTERS[c], &profiles[c].progress);
        terrain_clear(&play.run.terrain);
        play.run.zombie_count = 0;
        weather_start(&play.weather, WEATHER_CLEAR, camera_left(play.player.x));
        char name[64];
        for (int m = 0; m < 4; m++) {
            play.flashlight_since = MOMENTS[m];
            draw_stage(platform, &play, &skins[c], &profiles[c].progress, 1.0f, play.player.x, 0.0f);
            snprintf(name, sizeof(name), "29_linterna_%d_%d", c, m);
            save_capture(r, dir, name);
        }
        bool down[ACTION_COUNT] = {0};
        down[ACTION_RIGHT] = true;
        for (int i = 0; i < 40; i++) {
            input_update(&input, down);
            stage_step(&play, &input, &profiles[c]);
        }
        draw_stage(platform, &play, &skins[c], &profiles[c].progress, 1.0f, play.player.x, 0.0f);
        snprintf(name, sizeof(name), "29_linterna_%d_caminando", c);
        save_capture(r, dir, name);
    }

    /* The cowgirl with both guns holstered, walking. */
    start_stage(&play, 0, &CHARACTERS[0], &profiles[0].progress);
    terrain_clear(&play.run.terrain);
    play.run.zombie_count = 0;
    weather_start(&play.weather, WEATHER_CLEAR, camera_left(play.player.x));
    play.duals_out = true;
    set_guns(&play, profiles[0].progress.level);
    equip_weapon(&play);
    play.flashlight = false;
    play.flashlight_since = 10.0f;
    bool walking[ACTION_COUNT] = {0};
    walking[ACTION_RIGHT] = true;
    for (int i = 0; i < 24; i++) {
        input_update(&input, walking);
        stage_step(&play, &input, &profiles[0]);
    }
    draw_stage(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f);
    save_capture(r, dir, "31_duales_caminando");
    /* Her ricochet, in the engine, on two zombies: with both guns, then one. */
    for (int guns_out = 1; guns_out >= 0; guns_out--) {
        Progress kept = profiles[0].progress;
        start_stage(&play, 0, &CHARACTERS[0], &profiles[0].progress);
        terrain_clear(&play.run.terrain);
        weather_start(&play.weather, WEATHER_CLEAR, camera_left(play.player.x));
        profiles[0].progress.level = POWER_LEVEL;
        play.duals_out = guns_out;
        set_guns(&play, POWER_LEVEL);
        equip_weapon(&play);
        play.flashlight = false;
        play.flashlight_since = 10.0f;
        play.run.zombie_count = 2;
        for (int k = 0; k < 2; k++) {
            zombie_spawn(&play.run.zombies[k], &ZOMBIE_RIOT, play.player.x + 300.0f + (float)k * 170.0f);
            play.run.zombies[k].awake = false;
        }
        bool power[ACTION_COUNT] = {0};
        for (int i = 0; i < 40; i++) {
            power[ACTION_POWER] = i == 0;
            input_update(&input, power);
            stage_step(&play, &input, &profiles[0]);
            if (i % 4 == 3) {
                char shot_name[64];
                draw_stage(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f);
                snprintf(shot_name, sizeof(shot_name), "33_rebote_%d_%02d", guns_out, i);
                save_capture(r, dir, shot_name);
            }
        }
        profiles[0].progress = kept;
    }
    /* ...and taking the second out on the way: only her far hand and pistol over the legs. */
    for (int f = 0; f < 4; f++) {
        char swap_name[64];
        play.player.swap_time = PLAYER_SWAP_TIME * (1.0f - (float)(3 + 2 * f) / (float)PLAYER_SWAP_FRAMES);
        play.player.swap_back = false;
        draw_stage(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f);
        snprintf(swap_name, sizeof(swap_name), "32_cambio_caminando_%d", f);
        save_capture(r, dir, swap_name);
    }
    play.player.swap_time = 0.0f;

    /* The cowgirl with it on, one gun and two: her blow, and the duals' turns. */
    start_stage(&play, 3, &CHARACTERS[0], &profiles[0].progress);
    terrain_clear(&play.run.terrain);
    play.run.zombie_count = 0;
    weather_start(&play.weather, WEATHER_CLEAR, camera_left(play.player.x));
    play.flashlight = true;
    play.flashlight_since = 10.0f;
    for (int duals = 0; duals < 2; duals++) {
        char name[64];
        play.duals_out = duals == 1;
        set_guns(&play, profiles[0].progress.level);
        equip_weapon(&play);
        play.player.melee_wait = 0.0f;
        player_melee(&play.player);
        for (int f = 1; f < 5; f++) {
            animation_set_frame(&play.player.anim, f);
            draw_stage(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f);
            snprintf(name, sizeof(name), "30_golpe_linterna_%d_%d", duals, f);
            save_capture(r, dir, name);
        }
        play.player.state = PLAYER_IDLE;
    }
    bool trigger[ACTION_COUNT] = {0};
    trigger[ACTION_SHOOT] = true;
    input_update(&input, trigger);
    stage_step(&play, &input, &profiles[0]);
    for (int turn = 0; turn < 2; turn++) {
        char name[64];
        play.player.shot.other_gun = turn == 1;
        for (int f = 4; f < 6; f++) {
            animation_set_frame(&play.player.anim, f);
            draw_stage(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f);
            snprintf(name, sizeof(name), "30_disparo_linterna_%d_%d", turn, f);
            save_capture(r, dir, name);
        }
    }
}

static int run_game(bool smoke_mode, const char *capture_dir)
{
    Platform platform;
    if (!platform_init(&platform, WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT))
        return 1;

    int status = 1;
    bool text_ready = false;
    static CharacterSkin skins[8];
    if (!assets_load(platform.renderer))
        goto cleanup;
    if (!(text_ready = text_system_init()) || !hud_init(platform.renderer))
        goto cleanup;
    set_window_icon(platform.window);
    audio_init();
    volumes_init(&volumes);
    apply_volumes();
    display = &platform;
    remember_display = !smoke_mode && capture_dir == NULL;
    if (remember_display && prefs_get_bool(PREF_FULLSCREEN, false))
        set_fullscreen(true);
    platform_set_bindings(&platform, CONTROLS, CONTROLS_COUNT);
    for (int c = 0; c < CHARACTER_COUNT; c++)
        skin_load(&skins[c], platform.renderer, &CHARACTERS[c]);

    /* Each character's own progress, kept for the whole session. */
    static Profile profiles[8];
    Progress progress_view[8];
    for (int c = 0; c < CHARACTER_COUNT; c++) {
        progress_init(&profiles[c].progress);
        stage_record_init(&profiles[c].record);
        almanac_init(&profiles[c].almanac);
    }
    int hero = 0; /* The character being played */
    CharSelect char_select;
    Menu menu;
    char_select_init(&char_select, hero);
    menu_init(&menu, &profiles[hero].record);

    InputState input;
    static StagePlay play; /* Large; static keeps it off the stack */
    static World menu_world;
    world_init(&menu_world, STAGES[0].theme);
    ListMenu title;
    list_menu_init(&title, TITLE_ITEMS);
    SmokeTest smoke = {.enabled = smoke_mode};
    input_init(&input);
    Screen screen = SCREEN_TITLE;
    Screen almanac_return = SCREEN_TITLE;
    AlmanacView almanac_view;
    almanac_view_init(&almanac_view);
    if (capture_dir) {
        capture_screens(&platform, capture_dir, skins, profiles, &menu_world);
        status = 0;
        goto cleanup;
    }
    if (smoke.enabled) {
        /* Straight into 1-1 with the cowgirl. The scripted walk needs the zombie
         * 800 px away; at the view's edge (400 px, she starts centered) it would
         * reach and hit her mid-script. */
        start_stage(&play, 0, &CHARACTERS[0], &profiles[0].progress);
        zombie_spawn(&play.run.zombies[0], &ZOMBIE_RIOT, play.player.x + SMOKE_ZOMBIE_GAP);
        play.prev_zombie_x[0] = play.run.zombies[0].x;
        screen = SCREEN_STAGE;
    }

    float prev_player_x = play.player.x, prev_jump = 0.0f;
    double previous = platform_time();
    float accumulator = 0.0f;
    bool running = true;
    while (running) {
        platform_poll_events(&platform);
        if (platform.quit_requested)
            break;
        if (platform.fullscreen_toggled) { /* F11 */
            platform.fullscreen_toggled = false;
            set_fullscreen(platform.fullscreen);
        }

        double now = platform_time();
        float frame_time = (float)(now - previous);
        previous = now;
        if (frame_time > MAX_FRAME_TIME)
            frame_time = MAX_FRAME_TIME;
        if (platform.vsync)
            frame_time = snap_frame_time(frame_time);
        accumulator += frame_time;

        while (accumulator >= FIXED_DT && running) {
            prev_player_x = play.player.x;
            prev_jump = play.player.jump.height;
            bool down[ACTION_COUNT];
            if (smoke.enabled)
                smoke_override(&smoke, down);
            else
                platform_read_actions(&platform, down);
            input_update(&input, down);
            platform_read_pointer(&platform, &input);
            hud_set_pointer(input.pointer_x, input.pointer_y);
            int *selected = NULL; /* The list the mouse picks from, on this screen */
            if (screen == SCREEN_TITLE)
                selected = &title.selected;
            else if (screen == SCREEN_VOLUME)
                selected = &volume_menu.selected;
            else if (screen == SCREEN_CHARACTER)
                selected = &char_select.selected;
            else if (screen == SCREEN_MENU)
                selected = &menu.selected;
            else if (screen == SCREEN_STAGE && play.paused)
                selected = play.pause_view == PAUSE_VIEW_LIST     ? &play.pause_menu.selected
                           : play.pause_view == PAUSE_VIEW_VOLUME ? &volume_menu.selected
                                                                  : NULL;
            Screen previous_screen = screen;
            bool was_paused = (screen == SCREEN_STAGE && play.paused) ||
                              (screen == SCREEN_ALMANAC && almanac_return == SCREEN_STAGE);
            int previous_selection = selected ? *selected : -1;
            apply_pointer(&input, selected);

            /* Esc goes back one screen: the stage's pause, its menu, character
             * select, the title. */
            if (screen == SCREEN_TITLE) {
                switch (list_menu_update(&title, &input)) {
                case TITLE_PLAY:
                    char_select_init(&char_select, hero);
                    screen = SCREEN_CHARACTER;
                    break;
                case TITLE_ALMANAC:
                    almanac_return = SCREEN_TITLE;
                    almanac_view_init(&almanac_view);
                    screen = SCREEN_ALMANAC;
                    break;
                case TITLE_CONTROLS:
                    screen = SCREEN_CONTROLS;
                    break;
                case TITLE_VOLUME:
                    list_menu_init(&volume_menu, VOLUME_ROWS);
                    screen = SCREEN_VOLUME;
                    break;
                case TITLE_QUIT:
                    running = false;
                    break;
                default:
                    break;
                }
            } else if (screen == SCREEN_CONTROLS) {
                if (input.pressed[ACTION_QUIT] || input.pressed[ACTION_CONFIRM])
                    screen = SCREEN_TITLE;
            } else if (screen == SCREEN_VOLUME) {
                if (!volume_step(&input))
                    screen = SCREEN_TITLE;
            } else if (screen == SCREEN_CHARACTER) {
                if (input.pressed[ACTION_QUIT])
                    screen = SCREEN_TITLE;
                int chosen = char_select_update(&char_select, &input);
                if (chosen >= 0) {
                    hero = chosen;
                    menu_init(&menu, &profiles[hero].record);
                    screen = SCREEN_MENU;
                }
            } else if (screen == SCREEN_MENU) {
                if (input.pressed[ACTION_QUIT]) {
                    char_select_init(&char_select, hero);
                    screen = SCREEN_CHARACTER;
                }
                int chosen = menu_update(&menu, &input, &profiles[hero].record);
                if (chosen >= 0) {
                    start_stage(&play, chosen, &CHARACTERS[hero], &profiles[hero].progress);
                    prev_player_x = play.player.x;
                    screen = SCREEN_STAGE;
                }
            } else if (screen == SCREEN_ALMANAC) {
                int before = almanac_view.selected;
                if (!almanac_view_update(&almanac_view, &input))
                    screen = almanac_return;
                else if (before != almanac_view.selected)
                    audio_play("ui/move");
            } else if (!stage_step(&play, &input, &profiles[hero])) {
                menu_init(&menu, &profiles[hero].record);
                screen = SCREEN_MENU;
            }
            /* Clicking outside the window (or switching away) pauses a stage
             * in play, like Esc; a cleared stage has nothing left to pause.
             * The scripted run has no real window to keep focused. */
            if (platform.focus_lost) {
                platform.focus_lost = false;
                if (!smoke.enabled && screen == SCREEN_STAGE && !play.paused &&
                    play.run.phase != RUN_CLEARED)
                    stage_pause(&play);
            }
            if (screen == SCREEN_STAGE && play.request_almanac) {
                play.request_almanac = false;
                almanac_return = SCREEN_STAGE;
                almanac_view_init(&almanac_view);
                screen = SCREEN_ALMANAC;
            }
            bool now_paused = (screen == SCREEN_STAGE && play.paused) ||
                              (screen == SCREEN_ALMANAC && almanac_return == SCREEN_STAGE);
            if (previous_screen == SCREEN_STAGE && screen != SCREEN_STAGE && screen != SCREEN_ALMANAC)
                audio_stop_all();
            else if (was_paused != now_paused)
                audio_pause(now_paused);
            bool menu_input = previous_screen != SCREEN_STAGE || was_paused || now_paused;
            /* The click that started or resumed the stage is not a shot. */
            if (screen == SCREEN_STAGE && !now_paused && menu_input)
                platform_block_mouse(&platform);
            if (menu_input) {
                if (input.pressed[ACTION_QUIT])
                    audio_play("ui/back");
                else if (input.pressed[ACTION_CONFIRM])
                    audio_play("ui/confirm");
                else if (selected && *selected != previous_selection)
                    audio_play("ui/move");
            }
            if (smoke.enabled) {
                smoke_observe(&smoke, &play.player, &play.bullets, &play.run.zombies[0]);
                if (smoke.done)
                    running = false;
            }
            accumulator -= FIXED_DT;
        }

        hud_zones_clear();
        if (screen == SCREEN_TITLE) {
            draw_backdrop(&platform, &menu_world, 0.15f);
            hud_draw_title(platform.renderer, &title);
        } else if (screen == SCREEN_CONTROLS) {
            draw_backdrop(&platform, &menu_world, 0.5f);
            hud_draw_controls(platform.renderer);
        } else if (screen == SCREEN_VOLUME) {
            draw_backdrop(&platform, &menu_world, 0.5f);
            hud_draw_volume(platform.renderer, &volume_menu, &volumes);
        } else if (screen == SCREEN_CHARACTER) {
            for (int c = 0; c < CHARACTER_COUNT; c++)
                progress_view[c] = profiles[c].progress;
            draw_backdrop(&platform, &menu_world, 0.45f);
            hud_draw_characters(platform.renderer, skins, progress_view, char_select.selected);
        } else if (screen == SCREEN_MENU) {
            draw_backdrop(&platform, &menu_world, 0.45f);
            hud_draw_menu(platform.renderer, CHARACTERS[hero].name, &profiles[hero].progress,
                          &profiles[hero].record, menu.selected);
        } else if (screen == SCREEN_ALMANAC) {
            draw_backdrop(&platform, &menu_world, 0.70f);
            almanac_render(platform.renderer, &profiles[hero].almanac, &almanac_view, (float)platform_time());
        } else {
            draw_stage(&platform, &play, &skins[hero], &profiles[hero].progress,
                       accumulator / FIXED_DT, prev_player_x, prev_jump);
        }
        platform_present(&platform);
        if (!platform.vsync)
            SDL_Delay(1);
    }
    status = (smoke.enabled && !smoke.passed) ? 1 : 0;

cleanup:
    for (int c = 0; c < CHARACTER_COUNT; c++)
        skin_free(&skins[c]);
    scene_shutdown();
    terrain_render_shutdown();
    audio_shutdown();
    hud_shutdown();
    if (text_ready)
        text_system_shutdown();
    assets_unload();
    platform_shutdown(&platform);
    return status;
}

static void print_usage(const char *program)
{
    printf("Uso: %s [--verify] [--smoke-test] [--capturas DIR]\n"
           "  --verify         Validar los recursos incrustados sin abrir ventana\n"
           "  --smoke-test     Recorrido automático corto; termina con código 0 si todo va bien\n"
           "  --capturas DIR   Guardar cada pantalla (menús, pelea, muro, pausa) como BMP en DIR\n",
           program);
}

int main(int argc, char **argv)
{
    bool smoke = false;
    const char *capture_dir = NULL;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--verify") == 0) {
            return verify_assets();
        } else if (strcmp(argv[i], "--smoke-test") == 0) {
            smoke = true;
        } else if (strcmp(argv[i], "--capturas") == 0 && i + 1 < argc) {
            capture_dir = argv[++i];
        } else if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0) {
            print_usage(argv[0]);
            return 0;
        } else {
            fprintf(stderr, "Opción desconocida: %s\n", argv[i]);
            print_usage(argv[0]);
            return 2;
        }
    }
    return run_game(smoke, capture_dir);
}
