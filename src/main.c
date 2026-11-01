/* Vaquera 2D - a pixel-art cowgirl against zombies, in C + SDL2.
 *
 * Stage select, then stages of zombies with chests between them; XP levels
 * her up across stages. Art and sounds are embedded in the executable at
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
    const char *badges[] = {"sprites/ui/badge_player", "sprites/ui/badge_zombie"};
    for (size_t i = 0; i < sizeof(badges) / sizeof(badges[0]); i++)
        failures += !verify_image(badges[i], BADGE_W, BADGE_H);
    failures += verify_characters();
    const char *blobs[] = {"fonts/DejaVuSansMono", "fonts/DejaVuSansMono-Bold",
                           "sounds/player/shot", "sounds/player/reload", "sounds/zombie/spawn",
                           "sounds/zombie/idle", "sounds/zombie/death"};
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

/* The zombie's three voices, all from one recording (see README, Sonido). */
static void play_zombie_voice(Zombie *zombie)
{
    if (zombie->just_spawned)
        audio_play("zombie/spawn");
    else if (zombie->just_died)
        audio_play("zombie/death");
    else if (zombie->growl_due)
        audio_play("zombie/idle");
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
    SCREEN_CHARACTER, /* Elige tu personaje */
    SCREEN_MENU,      /* Its stages */
    SCREEN_STAGE
} Screen;

/* What each character keeps between stages (no save file yet). */
typedef struct {
    Progress progress;
    StageRecord record;
} Profile;

/* Everything one play of a stage uses, reset when it starts. */
typedef struct {
    const CharacterDef *character;
    int weapon_slot; /* Which of the character's guns is in hand */
    Player player;
    Bullets bullets;
    Zombie zombie;
    Effects effects;
    Smoke smoke;
    StageRun run;
    World world;
} StagePlay;

static const WeaponDef *weapon_in_hand(const StagePlay *play)
{
    return weapon_def(play->character->weapons[play->weapon_slot]);
}

static void start_stage(StagePlay *play, int index, const CharacterDef *character,
                        const Progress *progress)
{
    play->character = character;
    play->weapon_slot = 0;
    player_init(&play->player);
    player_set_stats(&play->player, progress->level, progress_max_health(progress),
                     progress_armor(progress), true);
    shot_set_reload(&play->player.shot, weapon_in_hand(play)->reload_time);
    bullets_clear(&play->bullets);
    effects_clear(&play->effects);
    smoke_clear(&play->smoke);
    hud_clear_popups();
    world_init(&play->world, STAGES[index].theme);
    run_start(&play->run, index, &play->zombie, play->player.x, character_drops_chests(character));
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
                       w->armor_share, w->tint};
    for (int p = 0; p < w->pellets; p++) {
        float dy = ((float)p - (float)(w->pellets - 1) / 2.0f) * w->pellet_gap;
        bullets_fire(&play->bullets, player->x, mx, my + dy, player->facing, &spec);
    }
    smoke_emit(&play->smoke, mx, my, player->facing);
    if (w->shot_sound)
        audio_play(w->shot_sound);
    if (w->reload_sound)
        audio_play(w->reload_sound); /* Starts after a pause: the reload */
}

/* The SWAT's ability: switch guns, but not halfway through a shot. */
static void swap_weapon(StagePlay *play)
{
    if (play->character->weapon_count < 2 || play->player.shot.active || !player_alive(&play->player))
        return;
    play->weapon_slot = (play->weapon_slot + 1) % play->character->weapon_count;
    const WeaponDef *w = weapon_in_hand(play);
    shot_set_reload(&play->player.shot, w->reload_time);
    hud_popup(w->name, COLOR_HUD_PRIMARY, play->player.x,
              BASELINE - PLAYER_HEAD_HEIGHT * SPRITE_SCALE - BADGE_H * BADGE_SCALE - 34, false);
}

/* One fixed step of a stage. Returns false to go back to the stage menu. */
static bool stage_step(StagePlay *play, const InputState *input, Profile *profile)
{
    Player *player = &play->player;
    Progress *progress = &profile->progress;
    if (input->pressed[ACTION_QUIT])
        return false;
    if (play->run.phase == RUN_CLEARED && input->pressed[ACTION_CONFIRM])
        return false;
    if (input->pressed[ACTION_RESET]) {
        start_stage(play, play->run.stage_index, play->character, progress);
        return true;
    }
    if (input->pressed[ACTION_SWAP])
        swap_weapon(play);

    player_update(player, input, FIXED_DT);
    bullets_update(&play->bullets, FIXED_DT, camera_left(player->x));
    if (player->shot_fired)
        fire_weapon(play, progress);
    zombie_update(&play->zombie, player->x, player_alive(player), FIXED_DT);
    effects_update(&play->effects, FIXED_DT);
    smoke_update(&play->smoke, FIXED_DT);
    combat_bullets_vs_zombie(&play->bullets, &play->zombie, &play->effects);
    combat_zombie_vs_player(&play->zombie, player);

    run_update(&play->run, &play->zombie, player, progress, FIXED_DT);
    if (play->run.levels_gained > 0)
        player_set_stats(player, progress->level, progress_max_health(progress),
                         progress_armor(progress), true);
    if (play->run.chest_opened)
        effects_spawn(&play->effects, chest_sparks(), play->run.chest.x, BASELINE, 1);
    announce_rewards(play, progress);
    if (play->run.cleared_now)
        profile->record.cleared[play->run.stage_index] = true;
    play_zombie_voice(&play->zombie);
    hud_update(FIXED_DT);
    return true;
}

static void draw_stage(Platform *platform, StagePlay *play, const CharacterSkin *skin,
                       const Progress *progress, float alpha, float prev_player_x,
                       float prev_jump, float prev_zombie_x)
{
    Player player_view = play->player;
    player_view.x = interpolate(prev_player_x, play->player.x, alpha);
    player_view.jump.height = interpolate(prev_jump, play->player.jump.height, alpha);
    Zombie zombie_view = play->zombie;
    zombie_view.x = interpolate(prev_zombie_x, play->zombie.x, alpha);

    /* Only the chunks around the view exist; walking streams the rest. */
    float camera_x = camera_left(player_view.x);
    world_stream(&play->world, camera_x);
    scene_draw(platform->renderer, &play->world, camera_x, platform_time());
    chest_render(platform->renderer, &play->run.chest, camera_x);
    /* The claw trail reaches past her, so a swiping zombie goes in front. */
    bool zombie_in_front = play->zombie.state == ZOMBIE_ATTACK;
    if (!zombie_in_front)
        zombie_render(platform->renderer, &zombie_view, camera_x);
    player_render(platform->renderer, &player_view, skin, camera_x);
    if (zombie_in_front)
        zombie_render(platform->renderer, &zombie_view, camera_x);
    bullets_render(platform->renderer, &play->bullets, camera_x);
    effects_render(platform->renderer, &play->effects, camera_x);
    smoke_render(platform->renderer, &play->smoke, camera_x);
    hud_draw_stage(platform->renderer, &player_view, &zombie_view, progress, &play->run, camera_x,
                   weapon_in_hand(play)->name, play->character->weapon_count > 1);
}

static int run_game(bool smoke_mode)
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
    SmokeTest smoke = {.enabled = smoke_mode};
    input_init(&input);
    Screen screen = SCREEN_CHARACTER;
    if (smoke.enabled) {
        /* Straight into 1-1 with the cowgirl. The scripted walk needs the zombie
         * 800 px away; at the view's edge (400 px, she starts centered) it would
         * reach and hit her mid-script. */
        start_stage(&play, 0, &CHARACTERS[0], &profiles[0].progress);
        zombie_spawn(&play.zombie, &ZOMBIE_RIOT, play.player.x + SMOKE_ZOMBIE_GAP);
        screen = SCREEN_STAGE;
    }

    float prev_player_x = play.player.x, prev_jump = 0.0f, prev_zombie_x = play.zombie.x;
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
            prev_zombie_x = play.zombie.x;
            bool down[ACTION_COUNT];
            if (smoke.enabled)
                smoke_override(&smoke, down);
            else
                platform_read_actions(&platform, down);
            input_update(&input, down);

            /* Esc goes back one screen: stage, its menu, character select, quit. */
            if (screen == SCREEN_CHARACTER) {
                if (input.pressed[ACTION_QUIT])
                    running = false;
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
                    prev_zombie_x = play.zombie.x;
                    screen = SCREEN_STAGE;
                }
            } else if (!stage_step(&play, &input, &profiles[hero])) {
                menu_init(&menu, &profiles[hero].record);
                screen = SCREEN_MENU;
            }
            if (smoke.enabled) {
                smoke_observe(&smoke, &play.player, &play.bullets, &play.zombie);
                if (smoke.done)
                    running = false;
            }
            accumulator -= FIXED_DT;
        }

        if (screen == SCREEN_CHARACTER) {
            for (int c = 0; c < CHARACTER_COUNT; c++)
                progress_view[c] = profiles[c].progress;
            hud_draw_characters(platform.renderer, skins, progress_view, char_select.selected);
        } else if (screen == SCREEN_MENU) {
            hud_draw_menu(platform.renderer, CHARACTERS[hero].name, &profiles[hero].progress,
                          &profiles[hero].record, menu.selected);
        } else {
            draw_stage(&platform, &play, &skins[hero], &profiles[hero].progress,
                       accumulator / FIXED_DT, prev_player_x, prev_jump, prev_zombie_x);
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
    printf("Uso: %s [--verify] [--smoke-test]\n"
           "  --verify      Validar los recursos incrustados sin abrir ventana\n"
           "  --smoke-test  Recorrido automático corto; termina con código 0 si todo va bien\n",
           program);
}

int main(int argc, char **argv)
{
    bool smoke = false;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--verify") == 0) {
            return verify_assets();
        } else if (strcmp(argv[i], "--smoke-test") == 0) {
            smoke = true;
        } else if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0) {
            print_usage(argv[0]);
            return 0;
        } else {
            fprintf(stderr, "Opción desconocida: %s\n", argv[i]);
            print_usage(argv[0]);
            return 2;
        }
    }
    return run_game(smoke);
}
