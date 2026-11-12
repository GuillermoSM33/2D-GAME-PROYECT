/* Real save codec and asynchronous file storage, isolated from user data.
 * The Python runner supplies a temporary directory and also starts fresh
 * writer/reader processes to test actual persistence between sessions. */
#define SDL_MAIN_HANDLED
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <SDL.h>

#include "app/autosave.h"
#include "app/stage.h"
#include "game/hud.h"
#include "game/ui.h"
#include "test.h"

#ifdef _WIN32
#include <wchar.h>
#include <windows.h>
#include <shellapi.h>
#endif

/* Storage takes UTF-8, as SDL_GetPrefPath returns it. On Windows argv uses the
 * ANSI code page, so a path with accents has to be read from the wide command
 * line. The copy lives as long as this short test process. */
static const char *directory_argument(const char *fallback)
{
#ifdef _WIN32
    int count = 0;
    LPWSTR *wide = CommandLineToArgvW(GetCommandLineW(), &count);
    char *utf8 = wide && count > 2
        ? SDL_iconv_string("UTF-8", "UTF-16LE", (const char *)wide[2],
                           (wcslen(wide[2]) + 1) * sizeof(wchar_t))
        : NULL;
    if (wide) LocalFree(wide);
    return utf8 ? utf8 : fallback;
#else
    return fallback;
#endif
}

static SaveGame source, decoded;
static StagePlay play, resumed;
static AppOptions options;
static unsigned char bytes[SAVE_GAME_CAPACITY];
static const char *directory;

/* The appended cylinder/handoff fields precede the three case-file masks. */
static void legacy_checkpoint(unsigned schema, size_t *size)
{
    size_t extra = schema == 7 ? 4 : 20;
    CHECK(*size >= extra + 12 && source.has_checkpoint);
    memmove(bytes + *size - extra - 12, bytes + *size - 12, 12);
    *size -= extra;
    bytes[4] = (unsigned char)schema;
}

static void fixture(int health, int gold)
{
    save_game_init(&source);
    for (int i = 0; i < CHARACTER_COUNT; i++) {
        for (int j = 0; j < i; j++)
            progress_add_xp(&source.profiles[i].progress, xp_to_next(source.profiles[i].progress.level));
        source.profiles[i].progress.xp = i + 2;
        almanac_discover(&source.profiles[i].almanac, ZOMBIE_KIND_DOG, true, i + 1);
    }
    stage_start(&play, 0, &CHARACTERS[1], &source.profiles[1].progress);
    InputState reload = {0};
    reload.pressed[ACTION_RELOAD] = true;
    play.player.shot.rounds = 1;
    CHECK(stage_step(&play, &reload, &source.profiles[1], &options));
    play.player.x += 190.0f;
    play.player.health = health;
    play.player.water = 4;
    play.player.thirst = 70.0f;
    play.player.wet = .4f;
    play.player.bleeding = true;
    play.player.bleed_tick = BLEED_TICK;
    play.player.bleed_damage = 2.0f;
    play.player.burned = true;
    play.run.mission.ticks = 123 * SIMULATION_HZ + 17;
    play.run.dynamite = 3;
    source.profiles[1].progress.gold = gold;
    source.profiles[1].record.cleared[1] = true;
    source.profiles[1].record.stars[1] = 2;
    source.profiles[1].record.best_ticks[1] = 220 * SIMULATION_HZ;
    zombie_hit_through(&play.run.zombies[0], 1e6f, 0.0f);
    play.run.beaten[0] = play.run.chest_done[0] = true;
    play.run.defeated = 1;
    play.encounter.entry[0] = almanac_index(ZOMBIE_KIND_RIOT, false);
    play.encounter.defeated[0] = true;
    chest_place(&play.run.chests[0], play.player.x + 400.0f, 3);
    Piece *charge = terrain_add(&play.run.terrain, TERRAIN_CHARGE, play.player.x + 800.0f);
    CHECK(charge != NULL);
    if (charge) charge->fuse = .75f;
    play.run.grenades[0] = (Grenade){true, play.player.x + 100.0f, 35.0f, 110.0f, -50.0f, .9f};
    CHECK(bullets_spawn(&play.bullets, play.player.x, play.player.x + 80.0f, BASELINE - 90.0f, 1));
    bullet_glance(&play.bullets, &play.bullets.items[0], &play.run.zombies[0], .7f);
    CHECK(bullets_spawn(&play.bullets, play.player.x, play.player.x + 100.0f, BASELINE - 90.0f, 1));
    bullet_glance(&play.bullets, &play.bullets.items[1], &play.run.terrain.items[0], .7f);
    save_game_snapshot(&source, source.profiles, 1, &source.volumes, &play);
}

static void test_roundtrip_preserves_live_mission_and_rebinds_references(void)
{
    fixture(37, 111);
    size_t size = 0;
    CHECK(save_game_encode(&source, bytes, sizeof(bytes), &size));
    CHECK(size > 1000 && size < sizeof(bytes));
    save_game_init(&decoded);
    CHECK(save_game_decode(bytes, size, &decoded));
    CHECK(decoded.has_checkpoint && decoded.hero == 1);
    CHECK(decoded.profiles[1].progress.gold == 111);
    CHECK(decoded.profiles[2].progress.level == 3);
    CHECK(almanac_count(&decoded.profiles[1].almanac) == almanac_count(&source.profiles[1].almanac));
    CHECK(save_game_resume(&decoded, &resumed, 1, 0));
    CHECK_NEAR(resumed.player.x, play.player.x, .001f);
    CHECK(resumed.player.health == 37 && resumed.player.water == 4);
    CHECK(resumed.run.mission.ticks == 123 * SIMULATION_HZ + 17);
    CHECK(decoded.profiles[1].inventory.water == 4 && decoded.profiles[1].inventory.dynamite == 3);
    CHECK(decoded.profiles[1].record.stars[1] == 2 && decoded.profiles[1].record.best_ticks[1] == 220 * SIMULATION_HZ);
    CHECK(resumed.player.bleeding && resumed.player.burned);
    CHECK(resumed.player.shot.mag_reload == play.player.shot.mag_reload);
    CHECK(resumed.player.anim.def == play.player.anim.def);
    CHECK(resumed.run.stage == &STAGES[0] && resumed.character == &CHARACTERS[1]);
    CHECK(resumed.run.defeated == 1 && resumed.run.beaten[0] && resumed.run.chest_done[0]);
    CHECK(resumed.run.zombies[0].stats == play.run.zombies[0].stats);
    CHECK(resumed.run.chests[0].state == CHEST_CLOSED);
    CHECK_NEAR(resumed.run.grenades[0].fuse, .9f, .0001f);
    CHECK(resumed.run.terrain.count == play.run.terrain.count);
    CHECK(resumed.bullets.items[0].glanced == &resumed.run.zombies[0]);
    CHECK(resumed.bullets.items[1].glanced == &resumed.run.terrain.items[0]);
    CHECK(resumed.progress_at_start.gold == play.progress_at_start.gold);
    CHECK(resumed.encounter.defeated[0]);
    CHECK(!save_game_resume(&decoded, &resumed, 0, 0));
    const InputState idle = {0};
    CHECK(stage_step(&resumed, &idle, &decoded.profiles[1], &options));
}

static void test_revolver_checkpoint_keeps_ammo_and_migrates_hand_cannon(void)
{
    save_game_init(&source);
    stage_start(&play, 0, &CHARACTERS[0], &source.profiles[0].progress);
    play.player.shot.rounds = 3;
    CHECK(shot_reload_now(&play.player.shot));
    CHECK(!shot_update(&play.player.shot, .4f));
    save_game_snapshot(&source, source.profiles, 0, &source.volumes, &play);
    size_t size = 0;
    CHECK(save_game_encode(&source, bytes, sizeof(bytes), &size));
    CHECK(save_game_decode(bytes, size, &decoded));
    CHECK(save_game_resume(&decoded, &resumed, 0, 0));
    CHECK(resumed.player.shot.rounds == 3 && resumed.player.shot.magazine == 8);
    CHECK_NEAR(resumed.player.shot.mag_reload, .8f, .0001f);

    /* Schema 5 had unlimited hand-cannon ammunition. */
    shot_cancel(&play.player.shot);
    shot_set_magazine(&play.player.shot, 0, 0.0f, 0);
    shot_set_reload(&play.player.shot, PLAYER_SHOOT_RELOAD_TIME);
    save_game_snapshot(&source, source.profiles, 0, &source.volumes, &play);
    CHECK(save_game_encode(&source, bytes, sizeof(bytes), &size));
    legacy_checkpoint(5, &size);
    CHECK(save_game_decode(bytes, size, &decoded));
    CHECK(save_game_resume(&decoded, &resumed, 0, 0));
    CHECK(resumed.player.shot.magazine == 8 && resumed.player.shot.rounds == 8);
    CHECK_NEAR(resumed.player.shot.mag_reload_time, 1.2f, .0001f);
    CHECK_NEAR(resumed.player.shot.reload_time, weapon_def(WEAPON_REVOLVER)->reload_time, .0001f);
    CHECK_NEAR(resumed.player.x, play.player.x, .0001f);
}

static void test_dual_cylinders_and_reload_target_survive_a_save(void)
{
    save_game_init(&source);
    source.profiles[0].progress.level = POWER_LEVEL;
    stage_start(&play, 0, &CHARACTERS[0], &source.profiles[0].progress);
    play.player.shot.rounds = 3;
    play.player.shot.other_rounds = 5;
    play.player.shot.next_other = true;
    CHECK(shot_reload_now(&play.player.shot));
    CHECK(!shot_update(&play.player.shot, .4f));
    save_game_snapshot(&source, source.profiles, 0, &source.volumes, &play);
    size_t size = 0;
    CHECK(save_game_encode(&source, bytes, sizeof(bytes), &size));
    CHECK(save_game_decode(bytes, size, &decoded));
    CHECK(save_game_resume(&decoded, &resumed, 0, 0));
    CHECK(resumed.player.shot.rounds == 3 && resumed.player.shot.other_rounds == 5);
    CHECK(resumed.player.shot.reload_other && resumed.player.shot.reload_all);
    CHECK(resumed.player.shot.reload_pair);
    CHECK_NEAR(resumed.player.shot.mag_reload, .8f, .0001f);
    CHECK(!shot_update(&resumed.player.shot, resumed.player.shot.mag_reload));
    CHECK(resumed.player.shot.rounds == 3 && resumed.player.shot.other_rounds == 8);
    CHECK(shot_reloading(&resumed.player.shot) && !resumed.player.shot.reload_other);
    CHECK(resumed.player.shot.reload_pair);
    save_game_snapshot(&source, source.profiles, 0, &source.volumes, &resumed);
    CHECK(save_game_encode(&source, bytes, sizeof(bytes), &size));
    CHECK(save_game_decode(bytes, size, &decoded));
    CHECK(decoded.checkpoint.player.shot.reload_pair && !decoded.checkpoint.player.shot.reload_all);
    CHECK(!decoded.checkpoint.player.shot.reload_other);

    /* Last version's in-progress paired reload keeps its counters and target. */
    save_game_snapshot(&source, source.profiles, 0, &source.volumes, &play);
    CHECK(save_game_encode(&source, bytes, sizeof(bytes), &size));
    legacy_checkpoint(7, &size);
    CHECK(save_game_decode(bytes, size, &decoded));
    CHECK(decoded.checkpoint.player.shot.reload_pair && decoded.checkpoint.player.shot.reload_other);
    CHECK(decoded.checkpoint.player.shot.rounds == 3 && decoded.checkpoint.player.shot.other_rounds == 5);

    /* Holstered ammunition is serialized separately from the primary gun. */
    shot_cancel(&play.player.shot);
    play.dual_rounds = 2;
    play.duals_out = false;
    play.rounds[0] = 3;
    stage_refresh_weapons(&play, POWER_LEVEL);
    save_game_snapshot(&source, source.profiles, 0, &source.volumes, &play);
    CHECK(save_game_encode(&source, bytes, sizeof(bytes), &size));
    CHECK(save_game_decode(bytes, size, &decoded));
    CHECK(save_game_resume(&decoded, &resumed, 0, 0));
    CHECK(!resumed.duals_out && resumed.dual_rounds == 2 && resumed.player.shot.rounds == 3);
}

static void test_legacy_duals_gain_two_finite_cylinders(void)
{
    for (unsigned schema = 5; schema <= 6; schema++) {
        save_game_init(&source);
        source.profiles[0].progress.level = POWER_LEVEL;
        stage_start(&play, 0, &CHARACTERS[0], &source.profiles[0].progress);
        shot_set_magazine(&play.player.shot, 0, 0.0f, 0);
        play.rounds[0] = 3;
        save_game_snapshot(&source, source.profiles, 0, &source.volumes, &play);
        size_t size = 0;
        CHECK(save_game_encode(&source, bytes, sizeof(bytes), &size));
        legacy_checkpoint(schema, &size);
        CHECK(save_game_decode(bytes, size, &decoded));
        CHECK(save_game_resume(&decoded, &resumed, 0, 0));
        CHECK(resumed.player.shot.magazine == 8 && resumed.player.shot.other_rounds == 8);
        CHECK(resumed.player.shot.rounds == (schema == 6 ? 3 : 8));
        CHECK_NEAR(resumed.player.shot.mag_reload_time, 1.2f, .0001f);
    }
}

static void test_invalid_or_truncated_data_never_mutates_profiles(void)
{
    fixture(37, 111);
    size_t size = 0;
    CHECK(save_game_encode(&source, bytes, sizeof(bytes), &size));
    save_game_init(&decoded);
    decoded.profiles[0].progress.gold = 777;
    for (size_t length = 0; length < size; length += 173) {
        CHECK(!save_game_decode(bytes, length, &decoded));
        CHECK(decoded.profiles[0].progress.gold == 777);
    }
    bytes[4] = 255; /* Unknown schema version, even with a valid storage CRC. */
    CHECK(!save_game_decode(bytes, size, &decoded));
    CHECK(decoded.profiles[0].progress.gold == 777);
    bytes[4] = 2;
    source.checkpoint.player.x = NAN;
    CHECK(!save_game_encode(&source, bytes, sizeof(bytes), &size));
    CHECK(size == 0);
}

static void prepare_shots_and_level_up(int hero)
{
    const InputState idle = {0};
    save_game_init(&source);
    source.profiles[hero].progress.xp = xp_to_next(1) - 1;
    stage_start_profile(&play, 0, &CHARACTERS[hero], &source.profiles[hero]);
    InputState trigger = {0};
    trigger.pressed[ACTION_SHOOT] = true;
    for (int shot = 0; shot < 3; shot++) {
        CHECK(stage_step(&play, &trigger, &source.profiles[hero], &options));
        for (int frame = 0; frame < 75; frame++)
            CHECK(stage_step(&play, &idle, &source.profiles[hero], &options));
    }
    play.player.health = 9;
    chest_place(&play.run.chests[0], play.player.x, 2);
    CHECK(stage_step(&play, &idle, &source.profiles[hero], &options));
    CHECK(source.profiles[hero].progress.level == 2);
    CHECK(play.player.health == play.player.max_health);
    if (play.player.shot.magazine == 0)
        CHECK(play.player.shot.rounds == 0);
}

static void test_level_up_checkpoint_roundtrip_for_every_character(void)
{
    for (int hero = 0; hero < CHARACTER_COUNT; hero++) {
        prepare_shots_and_level_up(hero);
        save_game_snapshot(&source, source.profiles, hero, &source.volumes, &play);
        size_t size = 0;
        CHECK(save_game_encode(&source, bytes, sizeof(bytes), &size));
        CHECK(save_game_decode(bytes, size, &decoded));
        CHECK(save_game_resume(&decoded, &resumed, hero, 0));
        CHECK(resumed.player.level == 2 && resumed.player.health == play.player.health);
        if (play.player.shot.magazine == 0) {
            /* A live attempt produced by the previous version can already
             * contain negative counters; they are unused for infinite ammo. */
            source.checkpoint.player.shot.rounds = -3;
            source.checkpoint.rounds[source.checkpoint.weapon_slot] = -3;
            CHECK(save_game_encode(&source, bytes, sizeof(bytes), &size));
            CHECK(save_game_decode(bytes, size, &decoded));
            CHECK(decoded.checkpoint.player.shot.rounds == -3);
        } else {
            source.checkpoint.player.shot.rounds = -1;
            CHECK(!save_game_encode(&source, bytes, sizeof(bytes), &size));
            source.checkpoint.player.shot.rounds = 1;
            source.checkpoint.rounds[source.checkpoint.weapon_slot] = -2;
            CHECK(!save_game_encode(&source, bytes, sizeof(bytes), &size));
        }
    }
}

static void test_combat_checkpoints_through_first_level_up(void)
{
    const InputState idle = {0};
    save_game_init(&source);
    stage_start_profile(&play, 0, &CHARACTERS[0], &source.profiles[0]);
    for (int enemy = 0; enemy < play.run.zombie_count && source.profiles[0].progress.level == 1; enemy++) {
        play.player.x = play.run.zombies[enemy].x;
        zombie_hit_through(&play.run.zombies[enemy], 10000.0f, 0.0f);
        for (int frame = 0; frame < 160; frame++) {
            CHECK(stage_step(&play, &idle, &source.profiles[0], &options));
            save_game_snapshot(&source, source.profiles, 0, &source.volumes, &play);
            size_t size = 0;
            if (!save_game_encode(&source, bytes, sizeof(bytes), &size)) {
                fprintf(stderr, "combat snapshot failed: enemy=%d frame=%d level=%d\n", enemy, frame,
                        source.profiles[0].progress.level);
                CHECK(false);
                return;
            }
        }
    }
    CHECK(source.profiles[0].progress.level == 2);
}

static void test_next_mission_saves_after_clearing_the_first(void)
{
    save_game_init(&source);
    Profile *profile = &source.profiles[0];
    stage_start_profile(&play, 0, &CHARACTERS[0], profile);
    CHECK(!stage_unlocked(&profile->record, 1));
    play.run.phase = RUN_CLEARED;
    mission_finish(&play.run.mission, &profile->record, 0, play.player.health, play.player.max_health);
    size_t size = 0;
    save_game_snapshot(&source, source.profiles, 0, &source.volumes, &play);
    CHECK(!source.has_checkpoint && save_game_encode(&source, bytes, sizeof(bytes), &size));
    save_game_snapshot(&source, source.profiles, 0, &source.volumes, NULL);
    CHECK(save_game_encode(&source, bytes, sizeof(bytes), &size));
    CHECK(stage_unlocked(&profile->record, 1));
    stage_start_profile(&play, 1, &CHARACTERS[0], profile);
    save_game_snapshot(&source, source.profiles, 0, &source.volumes, &play);
    CHECK(source.has_checkpoint && save_game_encode(&source, bytes, sizeof(bytes), &size));
    CHECK(save_game_decode(bytes, size, &decoded));
    CHECK(save_game_resume(&decoded, &resumed, 0, 1));
}

static void test_music_volume_is_kept(void)
{
    save_game_init(&source);
    CHECK(source.volumes.music > 0); /* On by default, also for older saves */
    source.volumes.music = 2;
    size_t size = 0;
    CHECK(save_game_encode(&source, bytes, sizeof(bytes), &size));
    CHECK(save_game_decode(bytes, size, &decoded));
    CHECK(decoded.volumes.music == 2);
    source.volumes.music = VOLUME_STEPS + 1;
    CHECK(!save_game_encode(&source, bytes, sizeof(bytes), &size));
}

static void test_retry_cannot_bank_unearned_progress_or_duplicate_rewards(void)
{
    fixture(37, 111);
    play.player.state = PLAYER_DEAD;
    play.player.health = 0;
    play.run.phase = RUN_FAILED;
    save_game_snapshot(&source, source.profiles, 1, &source.volumes, &play);
    CHECK(!source.has_checkpoint);
    CHECK(source.profiles[1].progress.gold == play.progress_at_start.gold);
    CHECK(almanac_count(&source.profiles[1].almanac) > 0);
    fixture(37, 111);
    play.run.phase = RUN_CLEARED;
    source.profiles[1].record.cleared[0] = true;
    save_game_snapshot(&source, source.profiles, 1, &source.volumes, &play);
    CHECK(!source.has_checkpoint && source.profiles[1].progress.gold == 111);
    CHECK(source.profiles[1].record.cleared[0]);
}

static void test_replacing_pending_mission_restores_its_entry_balance(void)
{
    fixture(37, 111);
    CHECK(source.has_checkpoint && source.profiles[1].inventory.water == 4);
    int discoveries = almanac_count(&source.profiles[1].almanac);
    int other_gold = source.profiles[2].progress.gold;
    save_game_abandon(&source, source.profiles);
    CHECK(!source.has_checkpoint);
    CHECK(source.profiles[1].progress.gold == play.progress_at_start.gold);
    CHECK(source.profiles[1].inventory.water == play.inventory_at_start.water);
    CHECK(source.profiles[1].inventory.dynamite == play.inventory_at_start.dynamite);
    CHECK(almanac_count(&source.profiles[1].almanac) == discoveries);
    CHECK(source.profiles[2].progress.gold == other_gold);
    stage_start_profile(&resumed, 0, &CHARACTERS[1], &source.profiles[1]);
    CHECK(resumed.player.water == play.inventory_at_start.water);
    source.profiles[1].progress.gold = 777;
    save_game_abandon(&source, source.profiles); /* No attempt: no rollback. */
    CHECK(source.profiles[1].progress.gold == 777);
}

static void test_timer_counts_fifteen_minutes_of_active_play_only(void)
{
    static Autosave a;
    CHECK(autosave_init(&a, true, directory) == STORAGE_EMPTY);
    CHECK(!autosave_tick(&a, 899.0, true));
    CHECK(!autosave_tick(&a, 10000.0, false)); /* Paused/book/menu time. */
    CHECK_NEAR(a.elapsed, 899.0, .0001);
    CHECK(autosave_tick(&a, 1.0, true));
    CHECK(!autosave_tick(&a, NAN, true));
    CHECK(!autosave_tick(&a, -1.0, true));
    autosave_shutdown(&a);
    autosave_init(&a, false, directory);
    CHECK(!autosave_tick(&a, 100000.0, true));
    CHECK(a.store == NULL && a.elapsed == 0.0);
    autosave_shutdown(&a);
}

static void test_notice_and_indicator_do_not_leave_clicks_on_the_world(void)
{
    SDL_setenv("SDL_VIDEODRIVER", "dummy", 1);
    CHECK(SDL_InitSubSystem(SDL_INIT_VIDEO) == 0);
    SDL_Surface *surface = SDL_CreateRGBSurfaceWithFormat(0, WINDOW_WIDTH, WINDOW_HEIGHT, 32, SDL_PIXELFORMAT_ARGB8888);
    SDL_Renderer *r = surface ? SDL_CreateSoftwareRenderer(surface) : NULL;
    CHECK(r != NULL);
    if (r) {
        hud_zones_clear();
        hud_draw_menu(r, "SWAT", &source.profiles[1].progress, &source.profiles[1].record, 0, 0u, 0, 0);
        hud_draw_autosave_notice(r);
        HudZone zone;
        CHECK(!hud_zone_at(190, 124, &zone)); /* Underlying level row. */
        CHECK(hud_zone_at(WINDOW_WIDTH / 2, 385, &zone) && zone.kind == HUD_ZONE_ACCEPT);
        hud_zones_clear();
        hud_draw_autosave_status(r, true, false, .4f);
        CHECK(!hud_zone_at(420, 122, &zone)); /* Status never intercepts play. */
        SDL_DestroyRenderer(r);
    }
    SDL_FreeSurface(surface);
    SDL_QuitSubSystem(SDL_INIT_VIDEO);
}

static int write_sessions(void)
{
    static Autosave a;
    fixture(37, 111);
    autosave_init(&a, true, directory);
    CHECK(autosave_request(&a, source.profiles, 1, &source.volumes, &play));
    autosave_shutdown(&a); /* Exit waits for the newest queued snapshot. */
    CHECK(!a.failed);
    CHECK(autosave_init(&a, true, directory) == STORAGE_LOADED);
    CHECK(save_game_resume(&a.game, &resumed, 1, 0));
    CHECK(resumed.player.health == 37);
    resumed.player.health = 24;
    a.game.profiles[1].progress.gold = 222;
    CHECK(autosave_request(&a, a.game.profiles, 1, &a.game.volumes, &resumed));
    autosave_shutdown(&a);
    CHECK(!a.failed);
    return TEST_EXIT();
}

int main(int argc, char **argv)
{
    SDL_SetMainReady();
    if (argc < 3) return 2;
    directory = directory_argument(argv[2]);
    if (strcmp(argv[1], "levelup-write") == 0 || strcmp(argv[1], "levelup-read") == 0) {
        if (argc != 4) return 2;
        int hero = atoi(argv[3]);
        if (hero < 0 || hero >= CHARACTER_COUNT) return 2;
        static Autosave a;
        if (strcmp(argv[1], "levelup-write") == 0) {
            prepare_shots_and_level_up(hero);
            CHECK(autosave_init(&a, true, directory) == STORAGE_EMPTY);
            CHECK(autosave_request(&a, source.profiles, hero, &source.volumes, &play));
            autosave_shutdown(&a);
            CHECK(!a.failed);
        } else {
            CHECK(autosave_init(&a, true, directory) == STORAGE_LOADED);
            CHECK(a.game.hero == hero && a.game.profiles[hero].progress.level == 2);
            CHECK(a.game.profiles[hero].progress.xp == 1);
            CHECK(save_game_resume(&a.game, &resumed, hero, 0));
            CHECK(resumed.player.level == 2 && resumed.player.health == resumed.player.max_health);
            CHECK(resumed.player.shot.rounds >= 0);
            CHECK(resumed.progress_at_start.level == 1);
            const InputState idle = {0};
            CHECK(stage_step(&resumed, &idle, &a.game.profiles[hero], &options));
            autosave_shutdown(&a);
        }
    } else if (strcmp(argv[1], "checks") == 0) {
        RUN(test_roundtrip_preserves_live_mission_and_rebinds_references);
        RUN(test_revolver_checkpoint_keeps_ammo_and_migrates_hand_cannon);
        RUN(test_dual_cylinders_and_reload_target_survive_a_save);
        RUN(test_legacy_duals_gain_two_finite_cylinders);
        RUN(test_invalid_or_truncated_data_never_mutates_profiles);
        RUN(test_level_up_checkpoint_roundtrip_for_every_character);
        RUN(test_combat_checkpoints_through_first_level_up);
        RUN(test_next_mission_saves_after_clearing_the_first);
        RUN(test_music_volume_is_kept);
        RUN(test_retry_cannot_bank_unearned_progress_or_duplicate_rewards);
        RUN(test_replacing_pending_mission_restores_its_entry_balance);
        RUN(test_timer_counts_fifteen_minutes_of_active_play_only);
        RUN(test_notice_and_indicator_do_not_leave_clicks_on_the_world);
    } else if (strcmp(argv[1], "write") == 0) {
        write_sessions();
    } else if (strcmp(argv[1], "legacy") == 0) {
        static Autosave a;
        CHECK(autosave_init(&a, true, directory) == STORAGE_LOADED);
        CHECK(!a.game.has_checkpoint && a.game.profiles[0].progress.level == 2);
        CHECK(a.game.profiles[0].progress.gold == 77 && a.game.profiles[0].record.cleared[0]);
        CHECK(a.game.profiles[0].inventory.water == 0 && a.game.profiles[0].record.stars[0] == 0);
        autosave_shutdown(&a);
    } else {
        static Autosave a;
        StorageLoad result = autosave_init(&a, true, directory);
        CHECK(result == (strcmp(argv[1], "recover") == 0 ? STORAGE_RECOVERED : STORAGE_LOADED));
        CHECK(a.game.has_checkpoint && a.game.hero == 1);
        CHECK(save_game_resume(&a.game, &resumed, 1, 0));
        int health = strcmp(argv[1], "recover") == 0 ? 37 : 24;
        int gold = strcmp(argv[1], "recover") == 0 ? 111 : 222;
        CHECK(resumed.player.health == health && a.game.profiles[1].progress.gold == gold);
        CHECK(resumed.player.water == 4 && resumed.player.bleeding && resumed.player.burned);
        CHECK(resumed.run.defeated == 1 && resumed.encounter.defeated[0]);
        CHECK(resumed.run.mission.ticks == 123 * SIMULATION_HZ + 17);
        CHECK(a.game.profiles[1].record.stars[1] == 2);
        if (strcmp(argv[1], "recover") == 0 || strcmp(argv[1], "fail") == 0) {
            CHECK(autosave_request(&a, a.game.profiles, 1, &a.game.volumes, &resumed));
            bool expected_failure = strcmp(argv[1], "fail") == 0;
            autosave_shutdown(&a);
            CHECK(a.failed == expected_failure);
        } else autosave_shutdown(&a);
    }
    SDL_Quit();
    return TEST_EXIT();
}
