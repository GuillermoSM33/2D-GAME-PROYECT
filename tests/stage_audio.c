/* Application-level sound integration without a window or audio device.
 * Compile this translation unit with the normal game objects except main.o
 * and audio.o: the real stage code runs, and the audio boundary is recorded.
 * Keeping this outside test_*.c avoids the pure-logic test linker rule. */
#define SDL_MAIN_HANDLED
#define main unused_game_entry_for_stage_audio
#include "../src/main.c"
#undef main

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
    start_stage(&game, 0, &CHARACTERS[character], &profile.progress);
    if (weapon == WEAPON_SHOTGUN)
        swap_weapon(&game);
    CHECK(game.guns[game.weapon_slot] == weapon);
    /* Keep real stage/update code but isolate the requested interaction. */
    terrain_clear(&game.run.terrain);
    game.run.zombie_count = 0;
    memset(&game.crows, 0, sizeof(game.crows));
    weather_start(&game.weather, WEATHER_CLEAR, camera_left(game.player.x));
    tick_number = 0;
    clear_cues();
}

static void step(const InputState *input)
{
    tick_number++;
    CHECK(stage_step(&game, input, &profile));
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
        fire_weapon(&game, &profile.progress);
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
        if (cues[i].kind != CUE_PLAY || cues[i].name == NULL || strcmp(cues[i].name, "world/footstep") != 0)
            continue;
        steps++;
        lo = fminf(lo, cues[i].gain);
        hi = fmaxf(hi, cues[i].gain);
    }
    CHECK(steps >= 4 && hi <= FOOTSTEP_GAIN + 1e-4f && lo < hi);
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
    CHECK(game.player.shot.rounds == 12 && plays("weapons/switch") == 1);
    bullets_clear(&game.bullets);
    CHECK(bullets_from_one_click() == 1 && game.player.shot.rounds == 11);
    press(ACTION_FIRE_MODE);
    CHECK(!game.single_fire && game.player.shot.magazine == 5 && game.player.shot.rounds == 3);
    bullets_clear(&game.bullets);
    CHECK(bullets_from_one_click() == 3);

    setup_weapon(WEAPON_SHOTGUN);
    press(ACTION_FIRE_MODE);
    CHECK(!game.single_fire && game.player.shot.magazine == weapon_def(WEAPON_SHOTGUN)->magazine);
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
    volumes_init(&volumes);
    list_menu_init(&volume_menu, VOLUME_ROWS);
    volume_menu.selected = VOLUME_PLAYER;
    clear_cues();
    InputState input = {0};
    input.pressed[ACTION_LEFT] = true;
    CHECK(volume_step(&input));
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
    CHECK(game.flashlight);
    press(ACTION_LIGHT);
    CHECK(!game.flashlight && game.player.x == x && game.player.shot.rounds == 2);
    press(ACTION_LIGHT);
    CHECK(game.flashlight);
    game.paused = true;
    game.pause_view = PAUSE_VIEW_LIST;
    list_menu_init(&game.pause_menu, PAUSE_ITEMS);
    game.pause_menu.selected = PAUSE_ALMANAC;
    press(ACTION_CONFIRM);
    CHECK(game.request_almanac && game.paused);
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
    start_stage(&game, 0, &CHARACTERS[0], &profile.progress);
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
        draw_heat(renderer, 0.0f, .5);
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
    RUN(test_footsteps_are_quiet_and_uneven);
    RUN(test_rifle_fire_mode_toggles_on_k_keeping_its_rounds);
    RUN(test_bandage_starts_once_and_stops_only_when_cancelled);
    RUN(test_player_volume_preview_uses_player_group);
    RUN(test_field_guide_request_and_light_preserve_stage_state);
    RUN(test_discoveries_and_kills_survive_a_stage_restart);
    RUN(test_heat_haze_is_subtle_and_stays_on_the_road);
    RUN(test_canine_voices_do_not_replace_any_existing_zombie_voice);
    return TEST_EXIT();
}
