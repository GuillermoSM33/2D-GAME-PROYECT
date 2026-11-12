#include <math.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>

#include "app/stage.h"
#include "engine/audio.h"
#include "game/camera.h"
#include "game/casefile.h"
#include "game/combat.h"
#include "game/damage.h"
#include "game/hud.h"
#include "game/scene.h"

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

/* Existing zombie recordings remain untouched. The new dog has its own
 * recorded canine voice rather than using a human groan. */
void play_zombie_voice(Zombie *zombie)
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

const WeaponDef *stage_weapon(const StagePlay *play)
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

bool stage_single_fire(const StagePlay *play)
{
    return play->single_fire && stage_weapon(play)->single_magazine > 0;
}

/* The shot sequence takes the gun in hand: timings, burst and magazine (in
 * the fire mode K chose). */
static void equip_weapon(StagePlay *play)
{
    const WeaponDef *w = stage_weapon(play);
    Shot *shot = &play->player.shot;
    shot_set_piston(shot, w->piston);
    if (stage_single_fire(play)) {
        shot_set_reload(shot, w->single_reload);
        shot_set_burst(shot, 1, 0.0f, false);
        shot_set_magazine(shot, w->single_magazine, w->magazine_reload, play->rounds[play->weapon_slot]);
        return;
    }
    shot_set_reload(shot, w->reload_time);
    shot_set_burst(shot, w->burst, w->burst_gap, w->automatic);
    shot_set_magazine(shot, w->magazine, w->magazine_reload, play->rounds[play->weapon_slot]);
}

void stage_refresh_weapons(StagePlay *play, int level)
{
    set_guns(play, level);
    equip_weapon(play);
}

/* K: bursts <-> single shots on a gun that has both. The rounds left carry
 * over (a burst is magazine x burst / single_magazine of them); a shot or a
 * reload under way is dropped, like a swap. */
static void toggle_fire_mode(StagePlay *play)
{
    const WeaponDef *w = stage_weapon(play);
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
    play_sound("weapons/fire_mode");
    hud_popup(play->single_fire ? "TIRO A TIRO" : "RÁFAGAS", COLOR_HUD_PRIMARY, play->player.x,
              BASELINE - PLAYER_HEAD_HEIGHT * SPRITE_SCALE - BADGE_H * BADGE_SCALE - 34, false);
}

void stage_start(StagePlay *play, int index, const CharacterDef *character,
                        const Progress *progress)
{
    audio_stop_all();
    audio_music_play(STAGES[index].music);
    play->music_on = true;
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
    play->request_casefile = false;
    play->clue_count = 0;
    play->clue_toast = -1;
    play->clue_toast_time = 0.0f;
    play->flashlight = STAGES[index].theme->night; /* On by night; L works by day too */
    play->flashlight_since = 10.0f; /* Already on, no stutter */
    play->flashlight_click_pending = false;
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
    play->inventory_at_start = (Inventory){play->player.water, play->run.dynamite};
    crows_start(&play->crows, index, play->player.x, play->run.goal_x - play->player.x);
    bats_start(&play->bats, index, play->player.x, play->run.goal_x - play->player.x, play->run.stage->theme->night);
    weather_start(&play->weather, play->run.stage->weather, camera_left(play->player.x));
    play->weather.paper = play->run.stage->theme->city; /* No tumbleweeds in a town: newspapers */
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
    play->lightning_warning = false;
    play->bat_chirp_wait = 2.0f;
    play->bat_chirp_count = 0;
    play->faint_timer = 0.0f;
    hallucination_clear(&play->visions);
    for (int k = 0; k < RUN_MAX_ZOMBIES; k++)
        play->prev_zombie_x[k] = play->run.zombies[k].x;
}

void stage_start_profile(StagePlay *play, int index, const CharacterDef *character, Profile *profile)
{
    stage_start(play, index, character, &profile->progress);
    play->inventory_at_start = profile->inventory;
    play->player.water = profile->inventory.water;
    play->run.dynamite = profile->inventory.dynamite;
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
void stage_fire_weapon(StagePlay *play, const Progress *progress)
{
    const WeaponDef *w = stage_weapon(play);
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
void stage_swap_weapon(StagePlay *play)
{
    if (play->character->weapon_count < 2 || !player_alive(&play->player))
        return;
    const WeaponDef *before = stage_weapon(play);
    if (play->player.state != PLAYER_SIT)
        audio_stop(before->reload_sound);
    audio_stop(before->cycle_sound);
    if (play->player.shot.active)
        shot_cancel(&play->player.shot);
    play->rounds[play->weapon_slot] = play->player.shot.rounds;
    play->weapon_slot = (play->weapon_slot + 1) % play->character->weapon_count;
    equip_weapon(play);
    play_sound("weapons/switch");
    const WeaponDef *w = stage_weapon(play);
    hud_popup(w->name, COLOR_HUD_PRIMARY, play->player.x,
              BASELINE - PLAYER_HEAD_HEIGHT * SPRITE_SCALE - BADGE_H * BADGE_SCALE - 34, false);
}

bool stage_can_swap_duals(const StagePlay *play, const Progress *progress)
{
    return play->character->power == POWER_DUAL_PISTOLS && (DUALS_FROM_ANY_LEVEL || progress->level >= POWER_LEVEL);
}

/* Q with the duals in reach: the second pistol out of the belt, or back in it. */
static void swap_duals(StagePlay *play, const Progress *progress)
{
    Player *player = &play->player;
    if (!stage_can_swap_duals(play, progress) || !player_alive(player) || player->jump.airborne ||
        player->state == PLAYER_SIT || player->state == PLAYER_CAUGHT || player->swap_time > 0.0f)
        return;
    const WeaponDef *before = stage_weapon(play);
    audio_stop(before->cycle_sound);
    if (player->shot.active)
        shot_cancel(&player->shot);
    play->duals_out = !play->duals_out;
    set_guns(play, progress->level);
    equip_weapon(play);
    player_swap(player, !play->duals_out);
    play_sound("weapons/switch");
    hud_popup(stage_weapon(play)->name, COLOR_HUD_PRIMARY, player->x,
              BASELINE - PLAYER_HEAD_HEIGHT * SPRITE_SCALE - BADGE_H * BADGE_SCALE - 34, false);
}

/* Leaving or retrying: what she earned only counts once the stage is cleared. */
void stage_drop_unearned(StagePlay *play, Profile *profile)
{
    if (play->run.phase != RUN_CLEARED) {
        profile->progress = play->progress_at_start;
        profile->inventory = play->inventory_at_start;
    }
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
static bool pause_step(StagePlay *play, const InputState *input, Profile *profile, AppOptions *options)
{
    if (play->pause_view == PAUSE_VIEW_VOLUME) {
        if (!options_step(options, input))
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
        stage_drop_unearned(play, profile);
        stage_start_profile(play, play->run.stage_index, play->character, profile);
        return true;
    case PAUSE_ALMANAC:
        play->request_almanac = true;
        return true;
    case PAUSE_CASEFILE:
        play->request_casefile = true;
        return true;
    case PAUSE_VOLUME:
        list_menu_init(&options->volume_menu, VOLUME_ROWS);
        play->pause_view = PAUSE_VIEW_VOLUME;
        return true;
    case PAUSE_CONTROLS:
        play->pause_view = PAUSE_VIEW_CONTROLS;
        return true;
    case PAUSE_LEAVE:
        stage_drop_unearned(play, profile);
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
        {RUN_SOUND_GRENADE_BOUNCE, "world/grenade_bounce"},
        {RUN_SOUND_GLASS, "world/glass"},
    };
    unsigned events = run_take_sound_events(run);
    for (size_t s = 0; s < sizeof(sounds) / sizeof(sounds[0]); s++) {
        if (events & sounds[s].event)
            play_sound(sounds[s].name);
    }
}

/* Crows on the first route; sparrows in the town (ThemeDef.city). */
static const char *bird_sound(const StagePlay *play, bool death)
{
    if (play->run.stage->theme->city)
        return death ? "sparrow/death" : "sparrow/chirp";
    return death ? "crow/death" : "crow/caw";
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
    /* The town's own air under it all: mains hum, a far alarm, a shutter. */
    if (play->run.phase == RUN_FIGHTING && play->run.stage->theme->city)
        audio_loop_in("world/city", SOUND_MASTER, 0.5f);
    else
        audio_stop_loop("world/city");
}

/* Only nearby water and fires are audible. A smooth distance curve keeps
 * entering/leaving their range quiet; nearby sources share one loop. */
static void stage_local_sound(const StagePlay *play)
{
    float river = 0.0f, fire = 0.0f, siren = 0.0f;
    if (play->run.phase == RUN_FIGHTING && player_alive(&play->player)) {
        const Terrain *terrain = &play->run.terrain;
        siren = terrain_siren_loudness(terrain, play->player.x);
        for (int i = 0; i < terrain->count; i++) {
            const Piece *p = &terrain->items[i];
            bool water = p->kind == TERRAIN_RIVER;
            bool burning = p->kind == TERRAIN_CAMPFIRE || ((p->kind == TERRAIN_FIRE || p->kind == TERRAIN_BURNER) &&
                                                           !p->spent) || terrain_burner_burning(p);
            if (!water && !burning)
                continue;
            float distance = fabsf(p->x - play->player.x);
            if (water)
                distance = fmaxf(0.0f, distance - terrain_half_width(TERRAIN_RIVER));
            float reach = water ? 500.0f : 420.0f;
            float near = fmaxf(0.0f, 1.0f - distance / reach);
            float gain = near * near * (3.0f - 2.0f * near);
            if (water)
                river = fmaxf(river, gain * 0.28f);
            else
                fire = fmaxf(fire, gain * 0.24f);
        }
    }
    if (river > 0.001f)
        audio_loop_in("world/river", SOUND_MASTER, river);
    else
        audio_stop_loop("world/river");
    if (fire > 0.001f)
        audio_loop_in("world/fire", SOUND_MASTER, fire);
    else
        audio_stop_loop("world/fire");
    if (siren > 0.001f) /* A patrol car wailing: loud by it, fading with distance */
        audio_loop_in("world/siren", SOUND_MASTER, 0.2f + 0.45f * siren * siren);
    else
        audio_stop_loop("world/siren");
}

static void stage_lightning_sound(StagePlay *play, float previous_warning)
{
    const StageRun *run = &play->run;
    bool active = run->phase == RUN_FIGHTING && player_alive(&play->player) && run->bolt_warn > 0.0f;
    if (active && previous_warning <= 0.0f) {
        audio_play_in_gain("weather/lightning_warn", SOUND_MASTER, 0.55f);
        play->lightning_warning = true;
    } else if (!active && play->lightning_warning) {
        audio_stop("weather/lightning_warn");
        play->lightning_warning = false;
    }
}

/* A nearby colony calls occasionally, using an intact recorded bat call.
 * A disturbance delays the next call; the previous one keeps its natural tail. */
static void stage_bat_sound(StagePlay *play, bool disturbed)
{
    if (play->run.phase != RUN_FIGHTING || !player_alive(&play->player)) {
        audio_stop("bat/chirp");
        play->bat_chirp_wait = 2.0f;
        return;
    }
    if (disturbed) {
        play->bat_chirp_wait = 6.0f + (float)(play->bat_chirp_count % 4u);
        return;
    }
    play->bat_chirp_wait = fmaxf(0.0f, play->bat_chirp_wait - FIXED_DT);
    if (play->bat_chirp_wait > 0.0f)
        return;
    float nearest = 401.0f;
    for (int i = 0; i < BATS_MAX; i++) {
        const Bat *bat = &play->bats.items[i];
        if (bat->alive && !bat->fleeing)
            nearest = fminf(nearest, fabsf(bat->x - play->player.x));
    }
    if (nearest > 400.0f)
        return;
    /* They flee inside BAT_SCARE_RANGE; the audible approach spans the
     * remaining distance to 400 px, from a soft .20 to a clear .50. */
    float proximity = fminf(1.0f, fmaxf(0.0f, (400.0f - nearest) / (400.0f - BAT_SCARE_RANGE)));
    audio_play_in_gain("bat/chirp", SOUND_PLAYER, 0.20f + 0.30f * proximity);
    play->bat_chirp_wait = 6.0f + (float)(play->bat_chirp_count++ % 4u);
}

/* Opens the pause menu over the frozen stage. */
/* The clues this step turned up (game/casefile.h): the crate that hides this
 * stage's, the zombie that carries one, the exit chest's. The caller keeps
 * them; a clue already found turns up again, and is ignored there. */
static void collect_clues(StagePlay *play, const bool *was_beaten)
{
    const StageRun *run = &play->run;
    int stage = run->stage_index;
    float road = run->goal_x - run->start_x;
    for (int l = 0; l < run->loot_count && road > 0.0f; l++) {
        int clue = casefile_crate_clue(stage, (run->loot_x[l] - run->start_x) / road);
        if (clue >= 0 && play->clue_count < STAGE_CLUES)
            play->clues_now[play->clue_count++] = clue;
    }
    for (int k = 0; k < run->zombie_count; k++) {
        if (!run->beaten[k] || was_beaten[k])
            continue;
        int clue = casefile_zombie_clue(stage, k, run->zombie_count);
        if (clue >= 0 && play->clue_count < STAGE_CLUES)
            play->clues_now[play->clue_count++] = clue;
    }
    if (run->cleared_now && play->clue_count < STAGE_CLUES) {
        int clue = casefile_mission_clue(stage);
        if (clue >= 0)
            play->clues_now[play->clue_count++] = clue;
    }
}

void stage_pause(StagePlay *play)
{
    play->paused = true;
    play->pause_view = PAUSE_VIEW_LIST;
    list_menu_init(&play->pause_menu, PAUSE_ITEMS);
}

/* One fixed step of a stage. Returns false to go back to the stage menu. */
bool stage_step(StagePlay *play, const InputState *input, Profile *profile, AppOptions *options)
{
    play->clue_count = 0;
    bool was_beaten[RUN_MAX_ZOMBIES];
    memcpy(was_beaten, play->run.beaten, sizeof(was_beaten));
    Player *player = &play->player;
    Progress *progress = &profile->progress;
    if (input->pressed[ACTION_ALMANAC]) {
        play->request_almanac = true;
        return true;
    }
    if (play->paused) {
        hud_update(0.0f);
        return pause_step(play, input, profile, options);
    }
    if (input->pressed[ACTION_LIGHT]) {
        play->flashlight = !play->flashlight;
        play->flashlight_since = 0.0f;
        play->flashlight_click_pending = play->flashlight;
        if (!play->flashlight)
            play_sound("player/flashlight_off");
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
        stage_drop_unearned(play, profile);
        stage_start_profile(play, play->run.stage_index, play->character, profile);
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
        stage_swap_weapon(play);
        swap_duals(play, progress);
    }
    if (input->pressed[ACTION_FIRE_MODE])
        toggle_fire_mode(play);
    /* E: a charge on the wall she is at; a seat on the bench there; else a
     * charge planted on the road. Lighting one cuts a reload or a shot short. */
    if (input->pressed[ACTION_USE]) {
        if (run_search(&play->run, player)) { /* An army outpost's locker */
            refill_guns(play);
            play_sound("world/supply");
        } else if (run_use(&play->run, player)) {
            play_sound("world/fuse");
            player_plant(player);
            /* Lighting it takes her hands: a reload or a shot under way
             * stops there, the gun left as it was (never filled). */
            if (player->shot.active) {
                const WeaponDef *w = stage_weapon(play);
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
        if (player->state == PLAYER_CAUGHT) { /* At the ropes, unless the last blow is under way */
            if (player->catch_blows > 0) {
                play_sound(stage_weapon(play)->melee_sound);
                player_struggle(player);
                play_sound("world/rope");
            }
        } else {
            if (player_melee(player))
                play_sound(stage_weapon(play)->melee_sound);
        }
    }

    for (int k = 0; k < RUN_MAX_ZOMBIES; k++)
        play->prev_zombie_x[k] = play->run.zombies[k].x;
    bool was_reloading = shot_reloading(&player->shot);
    int previous_rounds = player->shot.rounds;
    const WeaponDef *weapon = stage_weapon(play);
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
        stage_fire_weapon(play, progress);
        crows_noise(&play->crows, player->x, CROW_SHOT_RANGE);
    }
    if (crows_shoot(&play->crows, &play->bullets) > 0)
        play_sound(bird_sound(play, true));
    bool bats_died = bats_shoot(&play->bats, &play->bullets) > 0;
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
    float previous_bolt_warning = run->bolt_warn;
    run_update(run, player, progress, FIXED_DT);
    collect_clues(play, was_beaten);
    if (run->phase != RUN_FIGHTING && play->music_on) { /* Won or lost: it makes room */
        audio_music_stop(MUSIC_FADE_MS);
        play->music_on = false;
    }
    if (run->cleared_now && mission_finish(&run->mission, &profile->record, run->stage_index,
                                            player->health, player->max_health)) {
        int xp = run->mission.star_xp + run->mission.record_xp;
        int gold = run->mission.star_gold + run->mission.record_gold;
        run->xp_gained += xp;
        run->levels_gained += progress_add_xp(progress, xp);
        int room = INT_MAX - progress->gold;
        progress->gold += gold < room ? gold : room;
        run->gold_gained += gold < room ? gold : room;
    }
    almanac_observe(&profile->almanac, &play->encounter, run->zombies,
                    run->zombie_count, camera_left(player->x), VIEW_WIDTH);
    if (run->levels_gained > 0) {
        play_sound("world/level_up");
        player_set_stats(player, progress->level, progress_max_health(progress),
                         character_armor(play->character, progress->armor_level), player_alive(player));
        if (player_alive(player)) {
            player->heal_time = HEAL_GLOW_TIME;
            effects_spawn(&play->effects, terrain_heal_effect(), player->x,
                          BASELINE - player->jump.height, 1);
        }
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
            play_sound(bird_sound(play, true));
        if (bats_blast(&play->bats, run->blast_x[b], BARREL_RADIUS) > 0)
            bats_died = true;
    }
    bool moving = player->state == PLAYER_WALK || player->state == PLAYER_RUN ||
                  player->state == PLAYER_JUMP;
    crows_update(&play->crows, player->x, moving, FIXED_DT);
    bats_update(&play->bats, player->x, FIXED_DT);
    bool bats_fled = bats_take_flee_events(&play->bats) > 0;
    stage_bat_sound(play, bats_died || bats_fled);
    if (bats_died)
        play_sound("bat/death");
    if (bats_fled)
        audio_play_in_gain("bat/flee", SOUND_PLAYER, 0.55f);
    if (play->crows.took_off > 0)
        play_sound(bird_sound(play, false));
    stage_lightning_sound(play, previous_bolt_warning);
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
    stage_local_sound(play);
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
    if (run->searched)
        hud_popup("¡PUESTO REGISTRADO!  +1 DINAMITA  +1 AGUA", COLOR_HUD_XP, player->x, above_tag, true);
    for (int f = 0; f < run->flares; f++) { /* A burning drum goes over: its fire flares up */
        effects_spawn(&play->effects, terrain_flare(), run->flare_x[f], BASELINE, 1);
        smoke_rise(&play->smoke, run->flare_x[f], BASELINE - 120.0f, 6, 1.6f);
        play_sound("world/flare");
        crows_noise(&play->crows, run->flare_x[f], CROW_SHOT_RANGE);
    }
    if (run->hydrants_burst > 0) { /* The mains let go */
        play_sound("world/hydrant");
        crows_noise(&play->crows, player->x, CROW_SHOT_RANGE);
    }
    if (run->soaked)
        hud_popup("¡EL CHORRO TE EMPUJA!", COLOR_HUD_DANGER, player->x, above_tag, true);
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
            play_sound(terrain_water_at(&run->terrain, player->x) ? "world/splash" : "player/land");
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
    if (run->siren_tripped) /* The birds go too */
        crows_noise(&play->crows, player->x, CROW_BLAST_RANGE);
    if (run->siren_tripped && !run->horde_came) /* Set off from afar: its horde comes next */
        hud_popup("¡LA SIRENA ATRAE A LOS ZOMBIS!", COLOR_HUD_DANGER, player->x, above_tag, true);
    if (run->horde_came) { /* From both sides at once, and she is afraid: the board says it */
        play_sound("world/horde");
        hud_horde_notice();
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
    if (previous_state == PLAYER_CAUGHT && player->state == PLAYER_JUMP)
        play_sound("world/trap_escape"); /* The last blow has played: it gives way */
    if (player->state == PLAYER_CAUGHT && previous_state != PLAYER_CAUGHT) {
        audio_stop(weapon->reload_sound);
        audio_stop(weapon->cycle_sound);
    }
    for (int k = 0; k < run->zombie_count; k++)
        play_zombie_voice(&run->zombies[k]);
    if (play->flashlight_click_pending) {
        /* The same instant the beam appears in draw_stage, with the weapon
         * now in hand (a swap can change how long raising it takes). */
        float raise_time = stage_weapon(play)->light_time;
        if (raise_time <= 0.0f)
            raise_time = 1.0f;
        if (play->flashlight_since >= raise_time * PLAYER_LIGHT_CLICK) {
            play_sound("player/flashlight_on");
            play->flashlight_click_pending = false;
        }
    }
    hud_update(FIXED_DT);
    profile->inventory = (Inventory){player->water, run->dynamite};
    return true;
}

/* From here on, drawing goes into the view: VIEW_WIDTH x VIEW_HEIGHT world
 * px shrunk to VIEW_SCALE at the window's bottom, the sky's color above. */
