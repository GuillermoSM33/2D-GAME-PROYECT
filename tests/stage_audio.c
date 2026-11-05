/* Application-level sound integration without a window or audio device.
 * Link the normal application modules except main.o and audio.o: the real
 * stage code runs, and only the audio boundary is replaced by recording stubs.
 * Keeping this outside test_*.c avoids the pure-logic test linker rule. */
#define SDL_MAIN_HANDLED
#include "app/stage.h"
#include "app/stage_render.h"
#include "app/navigation.h"
#include "engine/audio.h"
#include "game/camera.h"
#include "game/scene.h"
#include "game/hud.h"

#include <math.h>
#include <string.h>

#include "test.h"

typedef enum { CUE_PLAY, CUE_STOP, CUE_LOOP, CUE_STOP_LOOP, CUE_CLEAR,
               CUE_PAUSE, CUE_MASTER, CUE_GROUP } CueKind;
typedef struct {
    CueKind kind;
    const char *name;
    int group, tick;
    float gain;
} Cue;

static Cue cues[8192];
static int cue_count, tick_number;
static StagePlay game;
static Profile profile;
static AppOptions options;

static void record_cue(CueKind kind, const char *name, int group, float gain)
{
    CHECK(cue_count < (int)(sizeof(cues) / sizeof(cues[0])));
    if (cue_count < (int)(sizeof(cues) / sizeof(cues[0])))
        cues[cue_count++] = (Cue){kind, name, group, tick_number, gain};
}

bool audio_init(void) { return true; }
void audio_shutdown(void) {}
void audio_play(const char *name) { audio_play_in(name, SOUND_MASTER); }
void audio_play_in(const char *name, int group) { audio_play_in_gain(name, group, 1.0f); }
void audio_play_in_gain(const char *name, int group, float gain)
{
    if (name)
        record_cue(CUE_PLAY, name, group, gain);
}
void audio_loop_in(const char *name, int group, float gain)
{
    if (name)
        record_cue(CUE_LOOP, name, group, gain);
}
void audio_stop_loop(const char *name)
{
    if (name)
        record_cue(CUE_STOP_LOOP, name, 0, 0.0f);
}
void audio_stop(const char *name)
{
    if (name)
        record_cue(CUE_STOP, name, 0, 0.0f);
}
void audio_stop_all(void) { record_cue(CUE_CLEAR, NULL, 0, 0.0f); }
void audio_pause(bool paused) { record_cue(CUE_PAUSE, NULL, paused ? 1 : 0, 0.0f); }
void audio_set_master(float volume) { record_cue(CUE_MASTER, NULL, 0, volume); }
void audio_set_group(int group, float volume) { record_cue(CUE_GROUP, NULL, group, volume); }

static void clear_cues(void) { cue_count = 0; }

static int cue_matches(CueKind kind, const char *name, int group)
{
    int count = 0;
    for (int i = 0; i < cue_count; i++) {
        const Cue *c = &cues[i];
        bool same_name = name == NULL ? c->name == NULL : c->name && strcmp(name, c->name) == 0;
        count += c->kind == kind && same_name && (group < 0 || c->group == group);
    }
    return count;
}

static int plays(const char *name) { return cue_matches(CUE_PLAY, name, -1); }
static int stops(const char *name) { return cue_matches(CUE_STOP, name, -1); }

static int first_play_tick(const char *name)
{
    for (int i = 0; i < cue_count; i++)
        if (cues[i].kind == CUE_PLAY && cues[i].name && strcmp(cues[i].name, name) == 0)
            return cues[i].tick;
    return -1;
}

static void setup_weapon(WeaponId weapon)
{
    memset(&game, 0, sizeof(game));
    memset(&profile, 0, sizeof(profile));
    progress_init(&profile.progress);
    stage_record_init(&profile.record);
    if (weapon == WEAPON_DUAL)
        profile.progress.level = POWER_LEVEL;
    int character = weapon == WEAPON_PLASMA ? 2 :
                    weapon == WEAPON_RIFLE || weapon == WEAPON_SHOTGUN ? 1 : 0;
    stage_start(&game, 0, &CHARACTERS[character], &profile.progress);
    if (weapon == WEAPON_SHOTGUN)
        stage_swap_weapon(&game);
    CHECK(game.guns[game.weapon_slot] == weapon);
    /* Keep real stage/update code but isolate the requested interaction. */
    terrain_clear(&game.run.terrain);
    game.run.zombie_count = 0;
    memset(&game.crows, 0, sizeof(game.crows));
    memset(&game.bats, 0, sizeof(game.bats));
    weather_start(&game.weather, WEATHER_CLEAR, camera_left(game.player.x));
    tick_number = 0;
    clear_cues();
}

static void step(const InputState *input)
{
    tick_number++;
    CHECK(stage_step(&game, input, &profile, &options));
}

static void idle(void)
{
    const InputState input = {0};
    step(&input);
}

static void press(Action action)
{
    InputState input = {0};
    input.pressed[action] = input.down[action] = true;
    step(&input);
}

static void test_every_weapon_fires_its_own_cues(void)
{
    for (int id = 0; id < WEAPON_COUNT; id++) {
        setup_weapon((WeaponId)id);
        const WeaponDef *w = weapon_def((WeaponId)id);
        stage_fire_weapon(&game, &profile.progress);
        CHECK(cue_matches(CUE_PLAY, w->shot_sound, SOUND_PLAYER) == 1);
        if (w->cycle_sound)
            CHECK(cue_matches(CUE_PLAY, w->cycle_sound, SOUND_PLAYER) == 1);
        if (id != WEAPON_REVOLVER) {
            CHECK(plays("player/shot") == 0);
            CHECK(plays("player/reload") == 0);
        }
        CHECK(bullets_active_count(&game.bullets) == w->pellets);
    }
}

static void test_magazine_reload_and_jump_cancellation(void)
{
    const WeaponId guns[] = {WEAPON_RIFLE, WEAPON_SHOTGUN};
    for (int id = 0; id < 2; id++) {
        setup_weapon(guns[id]);
        const WeaponDef *w = weapon_def(guns[id]);
        game.player.shot.rounds = 1;
        press(ACTION_RELOAD);
        CHECK(shot_reloading(&game.player.shot));
        CHECK(plays(w->reload_sound) == 1 && plays(w->empty_sound) == 0);
        idle();
        idle();
        CHECK(plays(w->reload_sound) == 1); /* No restart on each update. */
        press(ACTION_JUMP);
        CHECK(game.player.jump.airborne && !shot_reloading(&game.player.shot));
        CHECK(stops(w->reload_sound) >= 1);
        CHECK(game.player.shot.rounds == 1); /* Cancelling never fills the gun. */

        setup_weapon(guns[id]);
        game.player.shot.rounds = 0;
        press(ACTION_SHOOT);
        CHECK(plays(w->empty_sound) == 1 && plays(w->reload_sound) == 1);
        CHECK(plays(w->shot_sound) == 0 && shot_reloading(&game.player.shot));
        for (int ticks = 0; ticks < 5; ticks++)
            idle();
        CHECK(plays(w->empty_sound) == 1 && plays(w->reload_sound) == 1);
    }
}

static void test_last_round_gives_one_empty_cue(void)
{
    const WeaponId guns[] = {WEAPON_RIFLE, WEAPON_SHOTGUN};
    for (int id = 0; id < 2; id++) {
        setup_weapon(guns[id]);
        const WeaponDef *w = weapon_def(guns[id]);
        game.player.shot.rounds = 1;
        press(ACTION_SHOOT);
        for (int guard = 0; guard < 120 && !shot_reloading(&game.player.shot); guard++)
            idle();
        CHECK(shot_reloading(&game.player.shot));
        CHECK(plays(w->empty_sound) == 1 && plays(w->reload_sound) == 1);
        CHECK(plays(w->shot_sound) == (w->burst > 1 ? w->burst : 1));
    }
}

static void test_drink_starts_with_action_and_never_replays_at_completion(void)
{
    setup_weapon(WEAPON_REVOLVER);
    game.player.water = 2; /* A jug acquired in the level; the real spawn starts empty. */
    int water = game.player.water;
    CHECK(water > 0);
    press(ACTION_BANDAGE);
    CHECK(game.player.drink_time > 0.0f && plays("player/drink") == 1);
    CHECK(game.player.water == water && !game.player.drank);
    for (int guard = 0; guard < 120 && !game.player.drank; guard++)
        idle();
    CHECK(game.player.drank && game.player.water == water - 1);
    CHECK(plays("player/drink") == 1 && stops("player/drink") == 0);
    for (int ticks = 0; ticks < 5; ticks++)
        idle();
    CHECK(plays("player/drink") == 1);
}

static void test_melee_swing_precedes_hit_and_does_not_duplicate(void)
{
    setup_weapon(WEAPON_REVOLVER);
    game.run.zombie_count = 1;
    zombie_spawn(&game.run.zombies[0], &ZOMBIE_COMMON, game.player.x + 100.0f);
    game.run.zombies[0].awake = true;
    terrain_add(&game.run.terrain, TERRAIN_CRATE, game.player.x + 100.0f);
    press(ACTION_MELEE);
    CHECK(game.player.state == PLAYER_MELEE && !game.player.struck);
    CHECK(plays("player/melee") == 1);
    CHECK(plays("effects/hit_flesh") == 0 && plays("world/hit_wood") == 0);
    for (int ticks = 0; ticks < 50; ticks++)
        idle();
    CHECK(plays("player/melee") == 1);
    CHECK(plays("effects/hit_flesh") == 1 && plays("world/hit_wood") == 1);
    CHECK(first_play_tick("effects/hit_flesh") > first_play_tick("player/melee"));
}

static void test_rope_and_supply_cancel_reload_after_stage_events(void)
{
    setup_weapon(WEAPON_SHOTGUN);
    const WeaponDef *w = weapon_def(WEAPON_SHOTGUN);
    game.player.shot.rounds = 1;
    press(ACTION_RELOAD);
    clear_cues();
    terrain_add(&game.run.terrain, TERRAIN_NET, game.player.x);
    idle();
    CHECK(game.player.state == PLAYER_CAUGHT && !shot_reloading(&game.player.shot));
    CHECK(stops(w->reload_sound) >= 1 && stops(w->cycle_sound) >= 1);
    CHECK(plays("world/rope") == 1);

    setup_weapon(WEAPON_SHOTGUN);
    game.player.shot.rounds = 1;
    press(ACTION_RELOAD);
    clear_cues();
    terrain_add(&game.run.terrain, TERRAIN_SUPPLY, game.player.x);
    idle();
    CHECK(game.run.supply_taken && !shot_reloading(&game.player.shot));
    CHECK(game.player.shot.rounds == w->magazine);
    CHECK(stops(w->reload_sound) >= 1 && plays("world/supply") == 1);
}

/* E with dynamite while reloading or firing: the charge goes on the wall (or
 * the road) all the same, and the reload stops there, unfilled. */
static void test_dynamite_interrupts_reload_and_shooting(void)
{
    for (int on_wall = 0; on_wall < 2; on_wall++) {
        for (int firing = 0; firing < 2; firing++) {
            setup_weapon(WEAPON_SHOTGUN);
            const WeaponDef *w = weapon_def(WEAPON_SHOTGUN);
            Piece *wall = NULL;
            if (on_wall)
                wall = terrain_add(&game.run.terrain, TERRAIN_WALL, game.player.x +
                                   terrain_half_width(TERRAIN_WALL) + PLAYER_BODY_HALF_WIDTH);
            game.run.dynamite = 1;
            game.player.shot.rounds = firing ? w->magazine : 1;
            press(firing ? ACTION_SHOOT : ACTION_RELOAD);
            CHECK(game.player.shot.active);
            clear_cues();
            press(ACTION_USE);
            CHECK(game.run.dynamite == 0 && plays("world/fuse") == 1);
            if (wall)
                CHECK(wall->fuse > 0.0f);
            CHECK(!game.player.shot.active && !shot_reloading(&game.player.shot));
            if (!firing) {
                CHECK(game.player.shot.rounds == 1); /* Cut short: never filled */
                CHECK(stops(w->reload_sound) >= 1);
            }
        }
    }
}

static void sit_until_reload_starts(void)
{
    game.player.shot.rounds = 1;
    terrain_add(&game.run.terrain, TERRAIN_BENCH, game.player.x);
    press(ACTION_USE);
    CHECK(game.player.state == PLAYER_SIT && plays("world/sit") == 1);
    CHECK(plays("weapons/rifle_reload") == 0);
    for (int guard = 0; guard < 180 && plays("weapons/rifle_reload") == 0; guard++)
        idle();
    CHECK(plays("weapons/rifle_reload") == 1);
    CHECK(game.player.sit_gun == 0 && game.player.shot.rounds == 1);
}

static void test_planting_takes_her_hands_for_a_moment(void)
{
    /* E on the road: she stands PLANT_TIME setting the charge, neither
     * walking nor shooting, then goes on. */
    setup_weapon(WEAPON_REVOLVER);
    game.run.dynamite = 1;
    press(ACTION_USE);
    CHECK(game.player.plant_time > 0.0f && game.run.dynamite == 0);
    int frame;
    CHECK(player_care_animation(&game.player, &frame) != NULL && frame == 0);
    float x = game.player.x;
    InputState input = {0};
    input.down[ACTION_RIGHT] = input.down[ACTION_SHOOT] = input.pressed[ACTION_SHOOT] = true;
    step(&input);
    CHECK(game.player.x == x && !game.player.shot.active);
    int ticks = 1;
    while (game.player.plant_time > 0.0f && ticks < 200) {
        step(&input);
        ticks++;
    }
    CHECK_NEAR((float)(ticks + 1) * FIXED_DT, PLANT_TIME, FIXED_DT * 2.0f);
    input.pressed[ACTION_SHOOT] = true;
    step(&input);
    CHECK(game.player.shot.active || game.player.x != x);
}

static void test_q_takes_the_second_pistol_out_and_away(void)
{
    /* The cowgirl: Q swaps gun and plays the hands; no shooting while they're busy. */
    setup_weapon(WEAPON_REVOLVER);
#if DUALS_FROM_ANY_LEVEL
    InputState input = {0};
    input.pressed[ACTION_SWAP] = true;
    step(&input);
    input.pressed[ACTION_SWAP] = false;
    CHECK(game.guns[0] == WEAPON_DUAL && game.player.swap_time > 0.0f && !game.player.swap_back);
    int frame = -1;
    CHECK(player_care_animation(&game.player, &frame) != NULL && frame < PLAYER_SWAP_FRAMES / 2);
    input.pressed[ACTION_SHOOT] = true;
    step(&input);
    input.pressed[ACTION_SHOOT] = false;
    CHECK(!game.player.shot.active);
    input.pressed[ACTION_SWAP] = true; /* Not again halfway through */
    step(&input);
    input.pressed[ACTION_SWAP] = false;
    CHECK(game.guns[0] == WEAPON_DUAL);
    for (int i = 0; i < (int)(PLAYER_SWAP_TIME / FIXED_DT) + 2; i++)
        step(&input);
    CHECK(game.player.swap_time <= 0.0f);
    input.pressed[ACTION_SWAP] = true;
    step(&input);
    CHECK(game.guns[0] == WEAPON_REVOLVER && game.player.swap_back);
#endif
}

static void test_footsteps_are_quiet_and_uneven(void)
{
    /* Walking: steps under the rest of the sounds, the two feet apart. */
    setup_weapon(WEAPON_REVOLVER);
    InputState input = {0};
    input.down[ACTION_RIGHT] = true;
    for (int i = 0; i < 120; i++)
        step(&input);
    float lo = 1.0f, hi = 0.0f;
    int steps = 0;
    for (int i = 0; i < cue_count; i++) {
        if (cues[i].kind != CUE_PLAY || cues[i].name == NULL || strncmp(cues[i].name, "world/footstep", 14) != 0)
            continue;
        steps++;
        lo = fminf(lo, cues[i].gain);
        hi = fmaxf(hi, cues[i].gain);
    }
    CHECK(steps >= 4 && hi <= FOOTSTEP_GAIN + 1e-4f && lo < hi);
}

/* How many steps were heard, checking each is of the given kind (prefix, and
 * water take or not). takes, if given, receives how many different takes. */
static int count_steps(const char *prefix, bool water, int *takes)
{
    const char *seen[8];
    int steps = 0, distinct = 0;
    for (int i = 0; i < cue_count; i++) {
        const char *name = cues[i].name;
        if (cues[i].kind != CUE_PLAY || name == NULL ||
            (strncmp(name, "world/footstep", 14) != 0 && strncmp(name, "world/run_step", 14) != 0))
            continue;
        steps++;
        CHECK(strncmp(name, prefix, strlen(prefix)) == 0);
        CHECK((strstr(name, "_water") != NULL) == water);
        bool known = false;
        for (int k = 0; k < distinct; k++)
            known = known || strcmp(seen[k], name) == 0;
        if (!known && distinct < 8)
            seen[distinct++] = name;
    }
    if (takes)
        *takes = distinct;
    return steps;
}

static void test_footsteps_keep_time_with_the_legs(void)
{
    /* A step only as a foot lands (frames 0 and 4), two per walk cycle:
     * walking 3 a second, running 3.75. */
    const struct { bool run; const char *prefix; float per_second; } cases[] = {
        {false, "world/footstep", PLAYER_WALK_FPS / (PLAYER_WALK_FRAMES / 2)},
        {true, "world/run_step", PLAYER_WALK_FPS * PLAYER_RUN_ANIM_MULT / (PLAYER_WALK_FRAMES / 2)},
    };
    for (int c = 0; c < 2; c++) {
        setup_weapon(WEAPON_REVOLVER);
        InputState input = {0};
        input.down[ACTION_RIGHT] = true;
        input.down[ACTION_RUN] = cases[c].run;
        const int ticks = 240;
        int heard = 0;
        for (int i = 0; i < ticks; i++) {
            step(&input);
            int steps = count_steps(cases[c].prefix, false, NULL);
            if (steps > heard) {
                CHECK(game.player.anim.frame % (PLAYER_WALK_FRAMES / 2) == 0);
                heard = steps;
            }
        }
        /* This stage's wind at her back quickens the legs, and the steps with them. */
        float pace = game.player.wind ? WIND_WITH : 1.0f;
        float expected = cases[c].per_second * pace * (float)ticks * FIXED_DT;
        CHECK(fabsf((float)heard - expected) <= 1.5f);
    }
}

static void test_footsteps_sound_by_the_ground(void)
{
    /* Dry takes on dry ground, the fuller ones in a river or a puddle, and
     * the takes take turns. */
    const struct { bool run; TerrainKind water; bool wet; const char *prefix; } cases[] = {
        {false, TERRAIN_KINDS, false, "world/footstep"},
        {true, TERRAIN_KINDS, false, "world/run_step"},
        {false, TERRAIN_RIVER, true, "world/footstep_water"},
        {true, TERRAIN_RIVER, true, "world/run_step_water"},
        {false, TERRAIN_PUDDLE, true, "world/footstep_water"},
    };
    for (size_t c = 0; c < sizeof(cases) / sizeof(cases[0]); c++) {
        setup_weapon(WEAPON_REVOLVER);
        if (cases[c].wet) /* Right under her feet */
            terrain_add(&game.run.terrain, cases[c].water, game.player.x);
        InputState input = {0};
        input.down[ACTION_RIGHT] = true;
        input.down[ACTION_RUN] = cases[c].run;
        float start = game.player.x;
        for (int i = 0; i < 240; i++) {
            game.player.x = start; /* Walking on the spot, not out of a small puddle */
            step(&input);
        }
        int takes = 0;
        CHECK(count_steps(cases[c].prefix, cases[c].wet, &takes) >= 4);
        CHECK(takes == 4);
    }
}

static void test_blocked_feet_stay_quiet(void)
{
    /* Her legs go on against the edge of the stage, but no foot lands anywhere new. */
    setup_weapon(WEAPON_REVOLVER);
    game.player.x = game.player.min_x;
    InputState input = {0};
    input.down[ACTION_LEFT] = true;
    for (int i = 0; i < 120; i++)
        step(&input);
    CHECK(count_steps("world/footstep", false, NULL) == 0);
}

static void test_bench_latch_aligns_with_completion_and_swap_keeps_it(void)
{
    setup_weapon(WEAPON_RIFLE);
    sit_until_reload_starts();
    int began = first_play_tick("weapons/rifle_reload");
    CHECK((float)began * FIXED_DT > .9f); /* Sit-down and the silent early handling. */
    press(ACTION_SWAP);
    CHECK(game.player.state == PLAYER_SIT && game.player.sit_gun == 0);
    CHECK(game.guns[game.weapon_slot] == WEAPON_SHOTGUN);
    CHECK(stops("weapons/rifle_reload") == 0 && plays("weapons/switch") == 1);
    for (int guard = 0; guard < 180 && !game.player.sit_reloaded; guard++)
        idle();
    CHECK(game.player.sit_reloaded && game.player.sit_reloaded_gun == 0);
    CHECK(game.rounds[0] == -1); /* Full after the actual sitting reload completes. */
    CHECK_NEAR((float)(tick_number - began) * FIXED_DT,
               weapon_def(WEAPON_RIFLE)->magazine_reload, FIXED_DT * 3.0f);
    CHECK(plays("weapons/rifle_reload") == 1 && stops("weapons/rifle_reload") == 0);

    setup_weapon(WEAPON_RIFLE);
    sit_until_reload_starts();
    press(ACTION_RIGHT);
    CHECK(game.player.state != PLAYER_SIT);
    CHECK(stops("weapons/rifle_reload") == 1 && plays("world/stand") == 1);
}

static int bullets_from_one_click(void)
{
    int fired = 0;
    InputState input = {0};
    input.pressed[ACTION_SHOOT] = input.down[ACTION_SHOOT] = true;
    step(&input);
    fired += bullets_active_count(&game.bullets);
    for (int i = 0; i < 40; i++)
        idle();
    return bullets_active_count(&game.bullets) > fired ? bullets_active_count(&game.bullets) : fired;
}

static void test_rifle_fire_mode_toggles_on_k_keeping_its_rounds(void)
{
    /* K: three-round bursts from 5 into single shots from 15 and back; the
     * rounds left carry over, and the shotgun has no such mode. */
    setup_weapon(WEAPON_RIFLE);
    CHECK(game.player.shot.magazine == 5 && game.player.shot.burst == 3);
    game.player.shot.rounds = 4;
    press(ACTION_FIRE_MODE);
    CHECK(game.single_fire && game.player.shot.magazine == 15);
    CHECK(game.player.shot.burst == 1 && !game.player.shot.automatic);
    CHECK(game.player.shot.rounds == 12 && plays("weapons/fire_mode") == 1);
    CHECK(plays("weapons/switch") == 0);
    bullets_clear(&game.bullets);
    CHECK(bullets_from_one_click() == 1 && game.player.shot.rounds == 11);
    press(ACTION_FIRE_MODE);
    CHECK(!game.single_fire && game.player.shot.magazine == 5 && game.player.shot.rounds == 3);
    bullets_clear(&game.bullets);
    CHECK(bullets_from_one_click() == 3);

    setup_weapon(WEAPON_SHOTGUN);
    press(ACTION_FIRE_MODE);
    CHECK(!game.single_fire && game.player.shot.magazine == weapon_def(WEAPON_SHOTGUN)->magazine);
    CHECK(plays("weapons/fire_mode") == 0);
}

static void start_bleeding(void)
{
    game.player.bleeding = true;
    game.player.bleed_tick = 10.0f; /* Test wrapping, separately from blood loss. */
}

static void test_bandage_starts_once_and_stops_only_when_cancelled(void)
{
    setup_weapon(WEAPON_REVOLVER);
    start_bleeding();
    press(ACTION_BANDAGE);
    CHECK(game.player.bandage > 0.0f && plays("player/bandage") == 1);
    idle(); /* Releasing U cancels the wrap. */
    CHECK(game.player.bandage == 0.0f && stops("player/bandage") == 1);

    setup_weapon(WEAPON_REVOLVER);
    start_bleeding();
    press(ACTION_BANDAGE);
    const InputState holding = {.down = {[ACTION_BANDAGE] = true}};
    for (int guard = 0; guard < 180 && !game.player.bandaged; guard++)
        step(&holding);
    CHECK(game.player.bandaged && !game.player.bleeding);
    CHECK(plays("player/bandage") == 1 && stops("player/bandage") == 0);
    CHECK(plays("player/drink") == 0);
}

static void test_player_volume_preview_uses_player_group(void)
{
    volumes_init(&options.volumes);
    list_menu_init(&options.volume_menu, VOLUME_ROWS);
    options.volume_menu.selected = VOLUME_PLAYER;
    clear_cues();
    InputState input = {0};
    input.pressed[ACTION_LEFT] = true;
    CHECK(options_step(&options, &input));
    CHECK(cue_matches(CUE_PLAY, "player/shot", SOUND_PLAYER) == 1);
    CHECK(cue_matches(CUE_PLAY, "player/shot", SOUND_MASTER) == 0);
}

static void test_field_guide_request_and_light_preserve_stage_state(void)
{
    setup_weapon(WEAPON_RIFLE);
    game.player.shot.rounds = 2;
    float x = game.player.x;
    press(ACTION_ALMANAC);
    CHECK(game.request_almanac && game.player.x == x && game.player.shot.rounds == 2);
    CHECK(cue_count == 0);
    game.request_almanac = false;
    CHECK(!game.flashlight); /* By day it starts off */
    press(ACTION_LIGHT);
    CHECK(game.flashlight && game.player.x == x && game.player.shot.rounds == 2);
    CHECK(plays("player/flashlight_on") == 0); /* The switch is reached near the end of raising it. */
    press(ACTION_LIGHT);
    CHECK(!game.flashlight);
    CHECK(cue_matches(CUE_PLAY, "player/flashlight_off", SOUND_PLAYER) == 1);
    CHECK(plays("ui/confirm") == 0);
    game.paused = true;
    game.pause_view = PAUSE_VIEW_LIST;
    list_menu_init(&game.pause_menu, PAUSE_ITEMS);
    game.pause_menu.selected = PAUSE_ALMANAC;
    press(ACTION_CONFIRM);
    CHECK(game.request_almanac && game.paused);
}

static void test_flashlight_click_follows_the_beam_and_cancels_with_the_switch(void)
{
    for (int id = 0; id < WEAPON_COUNT; id++) {
        setup_weapon((WeaponId)id);
        float raise_time = stage_weapon(&game)->light_time;
        float click_at = (raise_time > 0.0f ? raise_time : 1.0f) * PLAYER_LIGHT_CLICK;
        press(ACTION_LIGHT);
        CHECK(game.flashlight && plays("player/flashlight_on") == 0);
        for (int guard = 0; guard < 240 && plays("player/flashlight_on") == 0; guard++)
            idle();
        CHECK(cue_matches(CUE_PLAY, "player/flashlight_on", SOUND_PLAYER) == 1);
        CHECK_NEAR(game.flashlight_since, click_at, FIXED_DT * 1.1f);
        for (int ticks = 0; ticks < 10; ticks++)
            idle();
        CHECK(plays("player/flashlight_on") == 1);
        press(ACTION_LIGHT);
        CHECK(!game.flashlight && plays("player/flashlight_off") == 1);
    }

    setup_weapon(WEAPON_RIFLE);
    press(ACTION_LIGHT);
    game.paused = true;
    float paused_at = game.flashlight_since;
    for (int ticks = 0; ticks < 120; ticks++)
        idle();
    CHECK(game.flashlight_since == paused_at && plays("player/flashlight_on") == 0);
    game.paused = false;
    press(ACTION_LIGHT); /* Off before reaching the switch: no delayed on-click. */
    for (int ticks = 0; ticks < 180; ticks++)
        idle();
    CHECK(plays("player/flashlight_off") == 1 && plays("player/flashlight_on") == 0);
}

static void test_landing_uses_water_only_on_wet_ground(void)
{
    const TerrainKind ground[] = {TERRAIN_KINDS, TERRAIN_RIVER, TERRAIN_PUDDLE};
    for (int i = 0; i < 3; i++) {
        setup_weapon(WEAPON_REVOLVER);
        if (i > 0)
            terrain_add(&game.run.terrain, ground[i], game.player.x);
        press(ACTION_JUMP);
        CHECK(game.player.jump.airborne);
        for (int guard = 0; guard < 120 && game.player.jump.airborne; guard++)
            idle();
        CHECK(!game.player.jump.airborne);
        CHECK(plays("world/splash") == (i > 0 ? 1 : 0));
        CHECK(plays("player/land") == (i == 0 ? 1 : 0));
        for (int ticks = 0; ticks < 5; ticks++)
            idle();
        CHECK(plays("world/splash") + plays("player/land") == 1);
    }
}

static void test_lightning_warning_starts_once_and_stops_on_impact_or_failure(void)
{
    for (int end = 0; end < 3; end++) {
        setup_weapon(WEAPON_REVOLVER);
        StageDef storm = *game.run.stage;
        storm.weather = WEATHER_STORM;
        game.run.stage = &storm;
        weather_start(&game.weather, WEATHER_STORM, camera_left(game.player.x));
        game.run.bolt_wait = 0.0f;
        idle();
        CHECK(game.run.bolt_warn > 0.0f && game.lightning_warning);
        CHECK(cue_matches(CUE_PLAY, "weather/lightning_warn", SOUND_MASTER) == 1);
        for (int ticks = 0; ticks < 5; ticks++)
            idle();
        CHECK(plays("weather/lightning_warn") == 1 && stops("weather/lightning_warn") == 0);
        if (end == 0) {
            for (int guard = 0; guard < 120 && !game.run.bolt_struck; guard++)
                idle();
            CHECK(game.run.bolt_struck && plays("weather/thunder") == 1);
        } else {
            game.run.phase = end == 1 ? RUN_FAILED : RUN_CLEARED;
            idle();
            CHECK(plays("weather/thunder") == 0);
        }
        CHECK(stops("weather/lightning_warn") == 1 && !game.lightning_warning);
        idle();
        CHECK(plays("weather/lightning_warn") == 1 && stops("weather/lightning_warn") == 1);
    }
}

static float last_loop_gain(const char *name)
{
    for (int i = cue_count - 1; i >= 0; i--)
        if (cues[i].kind == CUE_LOOP && strcmp(cues[i].name, name) == 0) {
            CHECK(cues[i].group == SOUND_MASTER);
            return cues[i].gain;
        }
    return 0.0f;
}

static void test_local_ambience_follows_distance_and_stops_with_the_stage(void)
{
    setup_weapon(WEAPON_REVOLVER);
    float x = game.player.x;
    terrain_add(&game.run.terrain, TERRAIN_RIVER, x);
    terrain_add(&game.run.terrain, TERRAIN_CAMPFIRE, x + 80.0f);
    idle();
    float near_river = last_loop_gain("world/river"), near_fire = last_loop_gain("world/fire");
    CHECK(near_river > 0.0f && near_river <= 0.28f);
    CHECK(near_fire > 0.0f && near_fire <= 0.24f);
    game.player.x += 550.0f;
    clear_cues();
    idle();
    CHECK(last_loop_gain("world/river") > 0.0f && last_loop_gain("world/river") < near_river);
    CHECK(cue_matches(CUE_STOP_LOOP, "world/fire", -1) == 1);
    game.player.x = x;
    game.run.phase = RUN_CLEARED;
    clear_cues();
    idle();
    CHECK(cue_matches(CUE_LOOP, "world/river", -1) == 0);
    CHECK(cue_matches(CUE_LOOP, "world/fire", -1) == 0);
    CHECK(cue_matches(CUE_STOP_LOOP, "world/river", -1) == 1);
    CHECK(cue_matches(CUE_STOP_LOOP, "world/fire", -1) == 1);
}

static void book_step(AlmanacView *view, const InputState *input)
{
    AlmanacView before = *view;
    bool open = almanac_view_update(view, input);
    CHECK(play_almanac_sounds(SCREEN_ALMANAC, open ? SCREEN_ALMANAC : SCREEN_STAGE, &before, view));
}

static void test_book_mouse_and_keyboard_share_paper_cues_without_hover_repeats(void)
{
    AlmanacView view;
    almanac_view_init(&view);
    clear_cues();
    CHECK(play_almanac_sounds(SCREEN_STAGE, SCREEN_ALMANAC, &view, &view));
    CHECK(plays("ui/book_open") == 1);
    InputState pointer = {.pointer_moved = true, .pointer_x = ALMANAC_GRID_X + 4,
                          .pointer_y = ALMANAC_GRID_Y + 4};
    book_step(&view, &pointer);
    book_step(&view, &pointer);
    CHECK(cue_count == 1); /* No rustle every frame while hovering. */
    pointer.pointer_clicked = true;
    book_step(&view, &pointer);
    CHECK(view.detail && plays("ui/book_page") == 1);
    InputState back = {.pressed = {[ACTION_QUIT] = true}};
    book_step(&view, &back);
    CHECK(!view.detail && plays("ui/book_page") == 2);
    almanac_view_select(&view, ALMANAC_PAGE_SIZE - 1);
    InputState next = {.pressed = {[ACTION_RIGHT] = true}};
    book_step(&view, &next);
    CHECK(view.scroll == ALMANAC_PAGE_SIZE && plays("ui/book_page") == 3);
    book_step(&view, &next);
    CHECK(plays("ui/move") == 1 && plays("ui/book_page") == 3);
    book_step(&view, &back);
    CHECK(plays("ui/book_close") == 1);
    CHECK(plays("ui/confirm") == 0 && plays("ui/back") == 0);
}

static void test_bats_have_their_own_cues(void)
{
    setup_weapon(WEAPON_REVOLVER);
    Bat *bat = &game.bats.items[0];
    *bat = (Bat){.alive = true, .x = game.player.x + 100.0f,
                 .home = game.player.x + 100.0f, .height = 100.0f, .base = 100.0f};
    idle();
    CHECK(bat->fleeing && plays("bat/flee") == 1 && plays("crow/caw") == 0);
    idle();
    CHECK(plays("bat/flee") == 1);

    setup_weapon(WEAPON_REVOLVER);
    bat = &game.bats.items[0];
    float x = game.player.x + 180.0f;
    *bat = (Bat){.alive = true, .x = x, .home = x, .height = 100.0f, .base = 100.0f};
    CHECK(bullets_spawn(&game.bullets, x - 20.0f, x,
                       BASELINE - 100.0f - BAT_FRAME_H * SPRITE_SCALE / 2.0f, 1));
    idle();
    CHECK(bat->dead && plays("bat/death") == 1 && plays("crow/death") == 0);
}

static void nearby_colony(void)
{
    /* Opposite phases keep one of two naturally flitting bats in earshot,
     * while neither enters the 300 px range that makes it flee. */
    for (int i = 0; i < 2; i++) {
        float x = game.player.x + 400.0f;
        game.bats.items[i] = (Bat){.alive = true, .x = x, .home = x,
                                  .height = 120.0f, .base = 120.0f,
                                  .time = i ? 3.14159265f / 1.3f : 0.0f};
    }
}

static void test_bat_calls_are_nearby_occasional_and_pause_with_the_stage(void)
{
    setup_weapon(WEAPON_REVOLVER);
    nearby_colony();
    CHECK_NEAR(game.bat_chirp_wait, 2.0f, 1e-4f);
    for (int i = 0; i < 90; i++)
        idle();
    CHECK(plays("bat/chirp") == 0);
    game.paused = true;
    float waiting = game.bat_chirp_wait;
    for (int i = 0; i < 180; i++)
        idle();
    CHECK(game.bat_chirp_wait == waiting && plays("bat/chirp") == 0);
    game.paused = false;
    for (int guard = 0; guard < 120 && plays("bat/chirp") == 0; guard++)
        idle();
    CHECK(cue_matches(CUE_PLAY, "bat/chirp", SOUND_PLAYER) == 1);
    int first = first_play_tick("bat/chirp");
    for (int i = 0; i < 300; i++)
        idle();
    CHECK(plays("bat/chirp") == 1); /* A full call, never an every-frame chirp. */
    for (int guard = 0; guard < 240 && plays("bat/chirp") < 2; guard++)
        idle();
    CHECK(plays("bat/chirp") == 2);
    int second = -1;
    for (int i = 0; i < cue_count; i++) {
        if (cues[i].kind == CUE_PLAY && strcmp(cues[i].name, "bat/chirp") == 0) {
            CHECK(cues[i].gain >= 0.20f && cues[i].gain <= 0.50f);
            second = cues[i].tick;
        }
    }
    CHECK((float)(second - first) * FIXED_DT >= 6.0f - FIXED_DT);
    CHECK((float)(second - first) * FIXED_DT <= 9.0f + FIXED_DT);
    game.run.phase = RUN_CLEARED;
    clear_cues();
    idle();
    CHECK(plays("bat/chirp") == 0 && stops("bat/chirp") == 1);

    setup_weapon(WEAPON_REVOLVER);
    game.bats.items[0] = (Bat){.alive = true, .x = game.player.x + 700.0f,
                              .home = game.player.x + 700.0f, .height = 120.0f, .base = 120.0f};
    for (int i = 0; i < 240; i++)
        idle();
    CHECK(plays("bat/chirp") == 0); /* A distant colony stays quiet. */
    game.bats.items[0].alive = false;
    game.bats.items[0].dead = true;
    game.bats.items[0].x = game.player.x + 350.0f;
    idle();
    CHECK(plays("bat/chirp") == 0);
    nearby_colony();
    idle();
    CHECK(plays("bat/chirp") == 1); /* The elapsed wait does not create a loop. */
}

static void test_bat_disturbances_preserve_call_tails_and_restart_the_wait(void)
{
    for (int dies = 0; dies < 2; dies++) {
        setup_weapon(WEAPON_REVOLVER);
        float x = game.player.x + 350.0f;
        Bat *bat = &game.bats.items[0];
        *bat = (Bat){.alive = true, .x = x, .home = x, .height = 120.0f, .base = 120.0f};
        game.bat_chirp_wait = 0.0f;
        idle();
        CHECK(plays("bat/chirp") == 1);
        clear_cues();
        if (dies) {
            CHECK(bullets_spawn(&game.bullets, bat->x - 20.0f, bat->x,
                               BASELINE - bat->height - BAT_FRAME_H * SPRITE_SCALE / 2.0f, 1));
        } else {
            bat->x = game.player.x + 100.0f;
        }
        idle();
        CHECK(stops("bat/chirp") == 0 && plays("bat/chirp") == 0);
        CHECK(plays(dies ? "bat/death" : "bat/flee") == 1);
        CHECK(game.bat_chirp_wait >= 6.0f);
        nearby_colony();
        for (int i = 0; i < 120; i++)
            idle();
        CHECK(plays("bat/chirp") == 0);
    }
}

static void test_grenade_bounces_and_each_glass_break_has_one_cue(void)
{
    setup_weapon(WEAPON_RIFLE);
    game.run.grenades[0] = (Grenade){.active = true, .x = game.player.x + 250.0f,
                                  .height = 1.0f, .vx = 80.0f, .vy = -180.0f, .fuse = 3.0f};
    idle();
    CHECK(plays("world/grenade_bounce") == 1);
    game.run.grenades[0].height = game.run.grenades[0].vy = 0.0f;
    for (int i = 0; i < 5; i++)
        idle();
    CHECK(plays("world/grenade_bounce") == 1);

    const TerrainKind glass[] = {TERRAIN_BOTTLES, TERRAIN_LAMP};
    for (int kind = 0; kind < 2; kind++) {
        setup_weapon(WEAPON_REVOLVER);
        float x = game.player.x + 220.0f;
        Piece *piece = terrain_add(&game.run.terrain, glass[kind], x);
        int count = kind == 0 ? BOTTLE_COUNT : 1;
        for (int hit = 0; hit < count; hit++) {
            CHECK(bullets_spawn(&game.bullets, x - 20.0f, x,
                               BASELINE - LAMP_GLASS_ROWS * SPRITE_SCALE - 5.0f, 1));
            idle();
            CHECK(plays("world/glass") == hit + 1);
            idle();
            CHECK(plays("world/glass") == hit + 1);
        }
        CHECK(piece->spent);
    }
}

static void test_discoveries_and_kills_survive_a_stage_restart(void)
{
    setup_weapon(WEAPON_REVOLVER);
    almanac_init(&profile.almanac);
    game.run.zombie_count = 1;
    zombie_spawn(&game.run.zombies[0], zombie_stats(ZOMBIE_KIND_POLICE, true), game.player.x + 300.0f);
    idle();
    int entry = almanac_index(ZOMBIE_KIND_POLICE, true);
    CHECK(profile.almanac.entries[entry].discovered && profile.almanac.entries[entry].seen == 1);
    zombie_hit(&game.run.zombies[0], 100000.0f);
    idle();
    idle();
    CHECK(profile.almanac.entries[entry].defeated == 1);
    stage_start(&game, 0, &CHARACTERS[0], &profile.progress);
    CHECK(profile.almanac.entries[entry].discovered && profile.almanac.entries[entry].defeated == 1);
    CHECK(game.encounter.entry[0] == -1);
}

static void test_heat_haze_is_subtle_and_stays_on_the_road(void)
{
    SDL_setenv("SDL_VIDEODRIVER", "dummy", 1);
    CHECK(SDL_InitSubSystem(SDL_INIT_VIDEO) == 0);
    SDL_Surface *surface = SDL_CreateRGBSurfaceWithFormat(0, VIEW_WIDTH, VIEW_HEIGHT, 32,
                                                          SDL_PIXELFORMAT_ARGB8888);
    CHECK(surface != NULL);
    SDL_Renderer *renderer = surface ? SDL_CreateSoftwareRenderer(surface) : NULL;
    CHECK(renderer != NULL);
    if (renderer) {
        SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255);
        SDL_RenderClear(renderer);
        stage_draw_heat(renderer, 0.0f, .5);
        SDL_RenderPresent(renderer);
        int changed = 0, highest = VIEW_HEIGHT, peak = 0;
        for (int y = 0; y < VIEW_HEIGHT; y++) {
            const Uint32 *row = (const Uint32 *)((const unsigned char *)surface->pixels + y * surface->pitch);
            for (int x = 0; x < VIEW_WIDTH; x++) {
                Uint8 r, g, b, a;
                SDL_GetRGBA(row[x], surface->format, &r, &g, &b, &a);
                if (r || g || b) {
                    changed++;
                    if (y < highest) highest = y;
                    if (r > peak) peak = r;
                }
            }
        }
        CHECK(changed > 0 && changed < 3200);
        CHECK(highest >= BASELINE - 48 && peak <= 16);
        SDL_DestroyRenderer(renderer);
    }
    SDL_FreeSurface(surface);
    SDL_QuitSubSystem(SDL_INIT_VIDEO);
}

static void test_canine_voices_do_not_replace_any_existing_zombie_voice(void)
{
    static const char *const original[] = {"zombie/spawn", "zombie/idle", "zombie/death"};
    static const char *const canine[] = {"dog/spawn", "dog/idle", "dog/death"};
    for (int kind = 0; kind < ZOMBIE_KIND_COUNT; kind++)
        for (int runner = 0; runner < 2; runner++)
            for (int event = 0; event < 3; event++) {
                Zombie zombie;
                zombie_spawn(&zombie, zombie_stats((ZombieKind)kind, runner != 0), 0.0f);
                zombie.just_spawned = event == 0;
                zombie.growl_due = event == 1;
                zombie.just_died = event == 2;
                clear_cues();
                play_zombie_voice(&zombie);
                const char *expected = kind == ZOMBIE_KIND_DOG ? canine[event] : original[event];
                CHECK(cue_matches(CUE_PLAY, expected, SOUND_ZOMBIE) == 1 && cue_count == 1);
                CHECK(!zombie.just_spawned && !zombie.just_died && !zombie.growl_due);
                play_zombie_voice(&zombie);
                CHECK(cue_count == 1);
            }
}

static void test_level_up_refills_health_for_each_character_without_curing_conditions(void)
{
    const WeaponId weapons[] = {WEAPON_REVOLVER, WEAPON_RIFLE, WEAPON_PLASMA};
    for (int i = 0; i < 3; i++) {
        setup_weapon(weapons[i]);
        profile.progress.xp = xp_to_next(profile.progress.level) - 1;
        game.player.health = 9;
        game.player.bleeding = true;
        game.player.bleed_tick = BLEED_TICK;
        game.player.burned = true;
        chest_place(&game.run.chests[0], game.player.x, 2);
        idle();
        CHECK(profile.progress.level == 2);
        CHECK(game.player.health == progress_max_health(&profile.progress));
        CHECK(game.player.health == game.player.max_health && game.player.heal_time > 0.0f);
        CHECK(game.player.bleeding && game.player.burned);
        CHECK(plays("world/level_up") == 1);
    }
}

static void test_inventory_carries_between_levels_and_retry_restores_its_start(void)
{
    setup_weapon(WEAPON_REVOLVER);
    game.player.water = 4;
    game.run.dynamite = 3;
    idle();
    CHECK(profile.inventory.water == 4 && profile.inventory.dynamite == 3);
    stage_start_profile(&game, 1, &CHARACTERS[0], &profile);
    CHECK(game.player.water == 4 && game.run.dynamite == 3);
    CHECK(game.inventory_at_start.water == 4 && game.inventory_at_start.dynamite == 3);
    game.player.water = 7;
    game.run.dynamite = 5;
    idle();
    CHECK(profile.inventory.water == 7 && profile.inventory.dynamite == 5);
    stage_pause(&game);
    game.pause_menu.selected = PAUSE_RETRY;
    press(ACTION_CONFIRM);
    CHECK(game.player.water == 4 && game.run.dynamite == 3);
    CHECK(profile.inventory.water == 4 && profile.inventory.dynamite == 3);
}

static void test_mission_clock_stops_in_pause_book_and_after_completion(void)
{
    setup_weapon(WEAPON_REVOLVER);
    idle();
    CHECK(game.run.mission.ticks == 1);
    game.paused = true;
    for (int i = 0; i < 30; i++) idle();
    CHECK(game.run.mission.ticks == 1);
    game.paused = false;
    press(ACTION_ALMANAC);
    CHECK(game.run.mission.ticks == 1 && game.request_almanac);
    game.request_almanac = false;
    game.run.phase = RUN_CLEARED;
    idle();
    CHECK(game.run.mission.ticks == 1);
}

static void test_completion_pays_base_and_star_record_extras_exactly_once(void)
{
    setup_weapon(WEAPON_REVOLVER);
    game.run.defeated = game.run.stage->zombies;
    game.player.x = game.run.goal_x;
    int before_xp = profile.progress.xp, before_gold = profile.progress.gold;
    for (int i = 0; i < 600 && game.run.phase == RUN_FIGHTING; i++) idle();
    CHECK(game.run.phase == RUN_CLEARED && game.run.mission.claimed);
    const MissionReport *m = &game.run.mission;
    CHECK(m->stars == 3 && m->new_record && m->health_percent == 100);
    CHECK(profile.progress.xp - before_xp == m->base_xp + m->star_xp + m->record_xp);
    CHECK(profile.progress.gold - before_gold == m->base_gold + m->star_gold + m->record_gold);
    CHECK(profile.record.stars[0] == 3 && profile.record.best_ticks[0] > 0);
    int after_xp = profile.progress.xp, after_gold = profile.progress.gold;
    for (int i = 0; i < 10; i++) idle();
    CHECK(profile.progress.xp == after_xp && profile.progress.gold == after_gold);
}

int main(void)
{
    printf("stage_audio (real application stage, recording audio boundary)\n");
    RUN(test_every_weapon_fires_its_own_cues);
    RUN(test_magazine_reload_and_jump_cancellation);
    RUN(test_last_round_gives_one_empty_cue);
    RUN(test_drink_starts_with_action_and_never_replays_at_completion);
    RUN(test_melee_swing_precedes_hit_and_does_not_duplicate);
    RUN(test_rope_and_supply_cancel_reload_after_stage_events);
    RUN(test_dynamite_interrupts_reload_and_shooting);
    RUN(test_planting_takes_her_hands_for_a_moment);
    RUN(test_bench_latch_aligns_with_completion_and_swap_keeps_it);
    RUN(test_q_takes_the_second_pistol_out_and_away);
    RUN(test_footsteps_are_quiet_and_uneven);
    RUN(test_footsteps_keep_time_with_the_legs);
    RUN(test_footsteps_sound_by_the_ground);
    RUN(test_blocked_feet_stay_quiet);
    RUN(test_rifle_fire_mode_toggles_on_k_keeping_its_rounds);
    RUN(test_bandage_starts_once_and_stops_only_when_cancelled);
    RUN(test_player_volume_preview_uses_player_group);
    RUN(test_field_guide_request_and_light_preserve_stage_state);
    RUN(test_flashlight_click_follows_the_beam_and_cancels_with_the_switch);
    RUN(test_landing_uses_water_only_on_wet_ground);
    RUN(test_lightning_warning_starts_once_and_stops_on_impact_or_failure);
    RUN(test_local_ambience_follows_distance_and_stops_with_the_stage);
    RUN(test_book_mouse_and_keyboard_share_paper_cues_without_hover_repeats);
    RUN(test_bats_have_their_own_cues);
    RUN(test_bat_calls_are_nearby_occasional_and_pause_with_the_stage);
    RUN(test_bat_disturbances_preserve_call_tails_and_restart_the_wait);
    RUN(test_grenade_bounces_and_each_glass_break_has_one_cue);
    RUN(test_discoveries_and_kills_survive_a_stage_restart);
    RUN(test_heat_haze_is_subtle_and_stays_on_the_road);
    RUN(test_canine_voices_do_not_replace_any_existing_zombie_voice);
    RUN(test_level_up_refills_health_for_each_character_without_curing_conditions);
    RUN(test_inventory_carries_between_levels_and_retry_restores_its_start);
    RUN(test_mission_clock_stops_in_pause_book_and_after_completion);
    RUN(test_completion_pays_base_and_star_record_extras_exactly_once);
    return TEST_EXIT();
}
