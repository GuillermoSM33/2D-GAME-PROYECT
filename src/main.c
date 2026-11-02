/* Vaquera 2D - a pixel-art cowgirl against zombies, in C + SDL2.
 *
 * Stage select, then stages: a road to a gate past groups of zombies,
 * barricades, powder barrels and a supply wagon, with chests along the way;
 * XP levels her up across stages. Art and sounds are embedded in the executable at
 * build time (see tools/embed_assets.py).
 */
#include <math.h>
#include <stdio.h>
#include <string.h>

#include "config.h"
#include "engine/assets.h"
#include "engine/audio.h"
#include "engine/input.h"
#include "engine/platform.h"
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
                failures += !verify_image(name, shoot->width, shoot->height);
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
    const AnimationDef *anims[32];
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
    failures += verify_characters();
    const char *blobs[] = {"fonts/DejaVuSansMono", "fonts/DejaVuSansMono-Bold",
                           "sounds/player/shot", "sounds/player/reload", "sounds/zombie/spawn",
                           "sounds/zombie/idle", "sounds/zombie/death", "sounds/world/explosion",
                           "sounds/world/supply", "sounds/world/fuse",
                           "sounds/world/glass", "sounds/world/wood", "sounds/world/snap"};
    for (size_t i = 0; i < sizeof(blobs) / sizeof(blobs[0]); i++) {
        if (assets_find_blob(blobs[i]) == NULL) {
            fprintf(stderr, "FALTA: %s\n", blobs[i]);
            failures++;
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
    audio_play_in(name, SOUND_PLAYER);
}

/* The options screen, while open. Returns false once it is left. A changed
 * volume plays a sample of what it controls. */
static bool volume_step(const InputState *input)
{
    int row = volume_menu_update(&volume_menu, &volumes, input);
    if (row == VOLUME_BACK)
        return false;
    if (row >= 0) {
        apply_volumes();
        if (row == VOLUME_ZOMBIE)
            audio_play_in("zombie/idle", SOUND_ZOMBIE);
        else
            play_sound(row == VOLUME_PLAYER ? "player/shot" : "player/reload");
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
            else
                play_sound(zone.index == VOLUME_PLAYER ? "player/shot" : "player/reload");
        }
        break;
    }
}

/* The zombie's three voices, all from one recording (see README, Sonido). */
static void play_zombie_voice(Zombie *zombie)
{
    if (zombie->just_spawned)
        audio_play_in("zombie/spawn", SOUND_ZOMBIE);
    else if (zombie->just_died)
        audio_play_in("zombie/death", SOUND_ZOMBIE);
    else if (zombie->growl_due)
        audio_play_in("zombie/idle", SOUND_ZOMBIE);
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
    SCREEN_TITLE,     /* Jugar, Controles, Volumen, Salir */
    SCREEN_CONTROLS,
    SCREEN_VOLUME,
    SCREEN_CHARACTER, /* Elige tu personaje */
    SCREEN_MENU,      /* Its stages */
    SCREEN_STAGE
} Screen;

/* What the pause shows: its list, or the volume or controls screen opened from it. */
typedef enum { PAUSE_VIEW_LIST, PAUSE_VIEW_VOLUME, PAUSE_VIEW_CONTROLS } PauseView;

/* What each character keeps between stages (no save file yet). */
typedef struct {
    Progress progress;
    StageRecord record;
} Profile;

/* Everything one play of a stage uses, reset when it starts. */
typedef struct {
    const CharacterDef *character;
    int weapon_slot; /* Which of the character's guns is in hand */
    WeaponId guns[CHARACTER_MAX_WEAPONS]; /* Its guns at its level (a power may change one) */
    float power_cooldown; /* Seconds until F works again */
    bool ricochet_armed;  /* The next shot's bullets glance on to a second target */
    int rounds[CHARACTER_MAX_WEAPONS]; /* Shots left in each gun's magazine while put away */
    Player player;
    Bullets bullets;
    Effects effects;
    Smoke smoke;
    StageRun run; /* The road: its zombies, terrain and chests */
    World world;
    float prev_zombie_x[RUN_MAX_ZOMBIES]; /* Before the last step, to draw in between */
    float smoke_timer; /* Seconds until fires puff smoke again */
    /* Her progress when the stage began: a retry or leaving before clearing
     * it puts this back, so replaying a stage can't farm its XP. */
    Progress progress_at_start;
    bool paused;     /* Esc: the pause menu, the stage frozen behind it */
    ListMenu pause_menu;
    PauseView pause_view;
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
    return play->guns[play->weapon_slot] != before;
}

/* The shot sequence takes the gun in hand: timings, burst and magazine. */
static void equip_weapon(StagePlay *play)
{
    const WeaponDef *w = weapon_in_hand(play);
    Shot *shot = &play->player.shot;
    shot_set_reload(shot, w->reload_time);
    shot_set_burst(shot, w->burst, w->burst_gap, w->automatic);
    shot_set_magazine(shot, w->magazine, w->magazine_reload, play->rounds[play->weapon_slot]);
}

static void start_stage(StagePlay *play, int index, const CharacterDef *character,
                        const Progress *progress)
{
    play->character = character;
    play->weapon_slot = 0;
    play->power_cooldown = 0.0f;
    play->ricochet_armed = false;
    set_guns(play, progress->level);
    play->progress_at_start = *progress;
    play->paused = false;
    player_init(&play->player);
    player_set_stats(&play->player, progress->level, progress_max_health(progress),
                     progress_armor(progress), true);
    for (int w = 0; w < CHARACTER_MAX_WEAPONS; w++)
        play->rounds[w] = -1; /* Full magazines */
    equip_weapon(play);
    bullets_clear(&play->bullets);
    effects_clear(&play->effects);
    smoke_clear(&play->smoke);
    hud_clear_popups();
    world_init(&play->world, STAGES[index].theme);
    run_start(&play->run, index, play->player.x, character_drops_chests(character));
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
    BulletSpec spec = {progress_damage(progress) * w->damage_mult, w->speed, w->range,
                       w->armor_share, w->tint, 0.0f, false};
    if (play->ricochet_armed) { /* F: these glance on to a second target */
        spec.ricochet = true;
        spec.tint = RICOCHET_TINT;
        play->ricochet_armed = false;
    }
    for (int p = 0; p < w->pellets; p++) {
        float side = (float)p - (float)(w->pellets - 1) / 2.0f;
        spec.slope = side * w->pellet_spread;
        bullets_fire(&play->bullets, player->x, mx, my + side * w->pellet_gap, player->facing, &spec);
    }
    smoke_emit(&play->smoke, mx, my, player->facing, w->smoke_puffs, w->smoke_scale);
    if (w->shot_sound)
        play_sound(w->shot_sound);
    if (w->reload_sound)
        play_sound(w->reload_sound); /* Starts after a pause: the reload */
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
        int magazine = weapon_def(play->guns[w])->magazine;
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
    if (play->player.shot.active)
        shot_cancel(&play->player.shot);
    play->rounds[play->weapon_slot] = play->player.shot.rounds;
    play->weapon_slot = (play->weapon_slot + 1) % play->character->weapon_count;
    equip_weapon(play);
    const WeaponDef *w = weapon_in_hand(play);
    shot_set_burst(&play->player.shot, w->burst, w->burst_gap, w->automatic);
    hud_popup(w->name, COLOR_HUD_PRIMARY, play->player.x,
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

/* One fixed step of a stage. Returns false to go back to the stage menu. */
static bool stage_step(StagePlay *play, const InputState *input, Profile *profile)
{
    Player *player = &play->player;
    Progress *progress = &profile->progress;
    if (play->paused) {
        hud_update(0.0f);
        return pause_step(play, input, progress);
    }
    bool cleared = play->run.phase == RUN_CLEARED;
    if (cleared && (input->pressed[ACTION_CONFIRM] || input->pressed[ACTION_QUIT]))
        return false;
    if (input->pressed[ACTION_QUIT]) {
        play->paused = true;
        play->pause_view = PAUSE_VIEW_LIST;
        list_menu_init(&play->pause_menu, PAUSE_ITEMS);
        return true;
    }
    if (play->run.phase == RUN_FAILED &&
        (input->pressed[ACTION_RELOAD] || input->pressed[ACTION_CONFIRM])) {
        drop_unearned(play, progress);
        start_stage(play, play->run.stage_index, play->character, progress);
        return true;
    }
    if (input->pressed[ACTION_SWAP])
        swap_weapon(play);
    /* E: a charge on the wall she is at; else a seat on the bench there. */
    if (input->pressed[ACTION_USE]) {
        if (run_use(&play->run, player)) {
            play_sound("world/fuse");
        } else if (run_sit(&play->run, player, guns_need_reload(play))) {
            if (player->sit_gun >= 0)
                play_sound("player/reload");
        }
    }
    if (input->pressed[ACTION_VAULT])
        run_vault(&play->run, player);

    for (int k = 0; k < RUN_MAX_ZOMBIES; k++)
        play->prev_zombie_x[k] = play->run.zombies[k].x;
    bool was_reloading = shot_reloading(&player->shot);
    run_place_player(&play->run, player);
    InputState in = *input;
    play->power_cooldown = fmaxf(0.0f, play->power_cooldown - FIXED_DT);
    if (in.pressed[ACTION_POWER])
        use_power(play, &in, progress);
    player_update(player, &in, FIXED_DT);
    if (player->threw)
        run_throw(&play->run, player);
    if (shot_reloading(&player->shot) && !was_reloading)
        play_sound("player/reload"); /* A new magazine going in */
    bullets_update(&play->bullets, FIXED_DT, camera_left(player->x));
    if (player->shot_fired)
        fire_weapon(play, progress);
    run_bullets(&play->run, &play->bullets, &play->effects);
    effects_update(&play->effects, FIXED_DT);
    smoke_update(&play->smoke, FIXED_DT);

    StageRun *run = &play->run;
    run_update(run, player, progress, FIXED_DT);
    if (run->levels_gained > 0) {
        player_set_stats(player, progress->level, progress_max_health(progress),
                         progress_armor(progress), true);
        if (set_guns(play, progress->level))
            equip_weapon(play); /* Its power's gun, from now on */
        if (progress->level - run->levels_gained < POWER_LEVEL && progress->level >= POWER_LEVEL &&
            play->character->power_name) {
            int above = BASELINE - PLAYER_HEAD_HEIGHT * SPRITE_SCALE - BADGE_H * BADGE_SCALE - 110;
            hud_popup(play->character->power_name, COLOR_HUD_XP, player->x, above, true);
        }
    }
    for (int c = 0; c < run->chests_opened; c++)
        effects_spawn(&play->effects, chest_sparks(), run->opened_x[c], BASELINE, 1);
    for (int b = 0; b < run->blasts; b++) {
        effects_spawn(&play->effects, terrain_explosion(), run->blast_x[b], BASELINE, 1);
        play_sound("world/explosion");
    }
    int above_tag = BASELINE - PLAYER_HEAD_HEIGHT * SPRITE_SCALE - BADGE_H * BADGE_SCALE - 34;
    if (run->supply_taken) {
        refill_guns(play);
        play_sound("world/supply");
        char str[48];
        snprintf(str, sizeof(str), "¡PROVISIONES!  +%d DINAMITA", stage_supply_dynamite(run->stage));
        hud_popup(str, COLOR_HUD_XP, player->x, above_tag, true);
    }
    if (run->dynamite_taken) {
        play_sound("world/supply");
        hud_popup("+1 DINAMITA", COLOR_HUD_TITLE, player->x, above_tag, true);
    }
    static const char *const LOOT_TEXT[] = {"+BALAS", "+VIDA", "+1 DINAMITA", "+ORO"};
    static const unsigned LOOT_RGB[] = {COLOR_HUD_PRIMARY, COLOR_HUD_XP, COLOR_HUD_TITLE, COLOR_HUD_TITLE};
    for (int l = 0; l < run->loot_count; l++) {
        play_sound("world/wood");
        if (run->loot[l] == LOOT_AMMO)
            refill_gun_in_hand(play);
        hud_popup(LOOT_TEXT[run->loot[l]], LOOT_RGB[run->loot[l]], run->loot_x[l], above_tag + 40, false);
    }
    for (int b = 0; b < run->bottles_hit; b++) {
        play_sound("world/glass");
        hud_popup("¡BUEN TIRO!", COLOR_HUD_TITLE, player->x, above_tag, true);
    }
    if (run->traps_sprung > 0)
        play_sound("world/snap");
    if (player->sit_reloaded) { /* A gun's sitting reload is done; the next starts */
        refill_gun(play, player->sit_reloaded_gun);
        if (player->sit_gun >= 0)
            play_sound("player/reload");
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
    if (run->group_beaten && run->defeated < run->stage->zombies)
        hud_popup("¡ADELANTE!  →", COLOR_HUD_TITLE, player->x, above_tag, true);
    announce_rewards(play, progress);
    if (run->cleared_now)
        profile->record.cleared[run->stage_index] = true;
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
    scene_draw(platform->renderer, &play->world, camera_x, platform_time());
    terrain_render(platform->renderer, &play->run.terrain, camera_x);
    for (int c = 0; c < RUN_MAX_CHESTS; c++)
        chest_render(platform->renderer, &play->run.chests[c], camera_x);
    /* The claw trail reaches past her, so a swiping zombie goes in front. */
    for (int k = 0; k < zombie_count; k++) {
        if (zombie_view[k].state != ZOMBIE_ATTACK)
            zombie_render(platform->renderer, &zombie_view[k], camera_x);
    }
    player_render(platform->renderer, &player_view, skin, play->guns, play->weapon_slot, camera_x);
    draw_grenades(platform->renderer, &play->run, camera_x);
    for (int k = 0; k < zombie_count; k++) {
        if (zombie_view[k].state == ZOMBIE_ATTACK)
            zombie_render(platform->renderer, &zombie_view[k], camera_x);
    }
    terrain_render_lights(platform->renderer, &play->run.terrain, camera_x, platform_time());
    bullets_render(platform->renderer, &play->bullets, camera_x);
    effects_render(platform->renderer, &play->effects, camera_x);
    smoke_render(platform->renderer, &play->smoke, camera_x);
    end_view(platform->renderer);
    const CharacterDef *c = play->character;
    const WeaponDef *w = weapon_in_hand(play);
    HudWeapon gun = {
        .id = play->guns[play->weapon_slot], .name = w->name, .rounds = play->player.shot.rounds,
        .magazine = w->magazine, .reloading = shot_reloading(&play->player.shot),
        .can_swap = c->weapon_count > 1,
        .other_id = play->guns[(play->weapon_slot + 1) % c->weapon_count],
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

    play.paused = true;
    play.pause_view = PAUSE_VIEW_LIST;
    list_menu_init(&play.pause_menu, PAUSE_ITEMS);
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
    platform_set_bindings(&platform, CONTROLS, CONTROLS_COUNT);
    for (int c = 0; c < CHARACTER_COUNT; c++)
        skin_load(&skins[c], platform.renderer, &CHARACTERS[c]);

    /* Each character's own progress, kept for the whole session. */
    static Profile profiles[8];
    Progress progress_view[8];
    for (int c = 0; c < CHARACTER_COUNT; c++) {
        progress_init(&profiles[c].progress);
        stage_record_init(&profiles[c].record);
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
            apply_pointer(&input, selected);

            /* Esc goes back one screen: the stage's pause, its menu, character
             * select, the title. */
            if (screen == SCREEN_TITLE) {
                switch (list_menu_update(&title, &input)) {
                case TITLE_PLAY:
                    char_select_init(&char_select, hero);
                    screen = SCREEN_CHARACTER;
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
            } else if (!stage_step(&play, &input, &profiles[hero])) {
                menu_init(&menu, &profiles[hero].record);
                screen = SCREEN_MENU;
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
        } else {
            draw_stage(&platform, &play, &skins[hero], &profiles[hero].progress,
                       accumulator / FIXED_DT, prev_player_x, prev_jump);
        }
        SDL_RenderPresent(platform.renderer);
        if (!platform.vsync)
            SDL_Delay(1);
    }
    status = (smoke.enabled && !smoke.passed) ? 1 : 0;

cleanup:
    for (int c = 0; c < CHARACTER_COUNT; c++)
        skin_free(&skins[c]);
    scene_shutdown();
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
