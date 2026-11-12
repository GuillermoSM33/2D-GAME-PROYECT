#include <math.h>
#include <stdio.h>
#include <string.h>

#include "app/application.h"

#define PHASE_COUNT_MAX 4
#include "app/autosave.h"
#include "app/capture.h"
#include "app/intro_render.h"
#include "app/navigation.h"
#include "app/smoke.h"
#include "app/stage.h"
#include "app/stage_render.h"
#include "app/story_render.h"
#include "app/story_audio.h"
#include "engine/assets.h"
#include "engine/audio.h"
#include "engine/prefs.h"
#include "engine/text.h"
#include "game/almanac_render.h"
#include "game/casefile_render.h"
#include "game/char_select.h"
#include "game/controls.h"
#include "game/hud.h"
#include "game/menu.h"
#include "game/scene.h"
#include "game/terrain_render.h"

static void set_window_icon(SDL_Window *window)
{
    SDL_Surface *icon = assets_surface_region("sprites/characters/cowgirl/walk", 0, 0,
                                              PLAYER_WALK_FRAME_W, PLAYER_WALK_FRAME_H);
    if (icon) {
        SDL_SetWindowIcon(window, icon);
        SDL_FreeSurface(icon);
    }
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

/* The almanac and the case file (and a case's report on it) open over a
 * paused stage too (book_return). */
static bool over_stage(Screen screen, Screen book_return, Screen story_return)
{
    (void)story_return;
    return book_return == SCREEN_STAGE &&
           (screen == SCREEN_ALMANAC || screen == SCREEN_CASEFILE || screen == SCREEN_REPORT ||
            screen == SCREEN_EXAMINE);
}

static bool has_live_stage(Screen screen, Screen book_return, Screen story_return)
{
    return screen == SCREEN_STAGE || over_stage(screen, book_return, story_return);
}

/* Once the whole cinematic has been seen, the game opens on its short end. */
#define PREF_INTRO_SEEN "intro_vista"

/* Plays a cue of the cinematic's script (game/intro.c). */
static void play_intro_cue(const IntroCue *cue)
{
    switch (cue->kind) {
    case CUE_PLAY:
        audio_play_in_gain(cue->sound, cue->group, cue->gain);
        break;
    case CUE_LOOP:
        audio_loop_in(cue->sound, cue->group, cue->gain);
        break;
    case CUE_STOP_LOOP:
        audio_stop_loop(cue->sound);
        break;
    case CUE_MUSIC:
        audio_music_play(cue->sound);
        break;
    case CUE_STOP:
        audio_stop(cue->sound);
        break;
    }
}

static void enter_stage(StagePlay *play, Autosave *save, Profile *profiles,
                         AppOptions *options, int hero, int stage)
{
    if (!save_game_resume(&save->game, play, hero, stage)) {
        save_game_abandon(&save->game, profiles);
        stage_start_profile(play, stage, &CHARACTERS[hero], &profiles[hero]);
    }
    autosave_request(save, profiles, hero, &options->volumes, play);
}

/* A stage about to be played for the first time: what is told before it
 * (2-1: the town leads to the city), then the stage. */
#define STORY_BEFORE(stage_index) do { \
    const StoryBeat *before_beat = story_before_stage(stage_index); \
    if (before_beat && !(save.game.case_file.beats_seen & story_bit(stage_index, true))) { \
        save.game.case_file.beats_seen |= story_bit(stage_index, true); \
        story_start(&story, before_beat); \
        story_since = platform_time(); \
        story_return = SCREEN_STAGE; \
        screen = SCREEN_STORY; \
    } \
} while (0)

int app_run(bool smoke_mode, const char *capture_dir)
{
    if (CHARACTER_COUNT > APP_PROFILE_CAPACITY) {
        fprintf(stderr, "El catálogo supera la capacidad de perfiles.\n");
        return 1;
    }
    Platform platform;
    if (!platform_init(&platform, WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT))
        return 1;

    int status = 1;
    bool text_ready = false;
    bool save_ready = false;
    static Autosave save;
    static CharacterSkin skins[APP_PROFILE_CAPACITY];
    if (!assets_load(platform.renderer))
        goto cleanup;
    if (!(text_ready = text_system_init()) || !hud_init(platform.renderer))
        goto cleanup;
    set_window_icon(platform.window);
    audio_init();
    AppOptions options;
    options_init(&options, &platform, !smoke_mode && capture_dir == NULL);
    autosave_init(&save, !smoke_mode && capture_dir == NULL, NULL);
    save_ready = true;
    options_restore_volumes(&options, &save.game.volumes);
    platform_set_bindings(&platform, CONTROLS, CONTROLS_COUNT);
    for (int c = 0; c < CHARACTER_COUNT; c++)
        skin_load(&skins[c], platform.renderer, &CHARACTERS[c]);

    static Profile profiles[APP_PROFILE_CAPACITY];
    Progress progress_view[APP_PROFILE_CAPACITY];
    for (int c = 0; c < CHARACTER_COUNT; c++) {
        profiles[c] = save.game.profiles[c];
    }
    int hero = character_playable(save.game.hero);
    CharSelect char_select;
    Menu menu;
    char_select_init(&char_select, hero);
    menu_init(&menu, &profiles[hero].record);
    if (prefs_get_bool("menu_backdrop_first", false)) /* Her choice: an earlier phase's landscape */
        menu.backdrop = 0;

    InputState input;
    static StagePlay play; /* Large; static keeps it off the stack */
    /* The landscape drifting behind the menus: the first phase's, or (her
     * choice in the stage select, once reached) a later one's. */
    static World menu_worlds[PHASE_COUNT_MAX];
    for (int p = 0; p < PHASE_COUNT && p < PHASE_COUNT_MAX; p++)
        world_init(&menu_worlds[p], STAGES[p * PHASE_STAGES].theme);
#define menu_world menu_worlds[0]
    ListMenu title;
    list_menu_init(&title, TITLE_ITEMS);
    SmokeTest smoke = {.enabled = smoke_mode};
    input_init(&input);
    Screen screen = SCREEN_TITLE;
    Screen book_return = SCREEN_TITLE;   /* Where the almanac or the case file goes back to */
    Screen story_return = SCREEN_MENU;   /* ...and a story beat */
    BoardView board;
    board_view_init(&board);
    Report report = {0, 0.0f};
    ClueExam exam = {0, 0.0f};
    TapeView tapes = {0};
    Screen intro_return = SCREEN_TITLE; /* The intro from HISTORIA's tapes goes back to them */
    Story story;
    memset(&story, 0, sizeof(story));
    story.done = true;
    double story_since = 0.0;
    /* The whole cinematic the first time the game opens; afterwards only the
     * title rising out of the dust. Never in the scripted or capture runs. */
    Intro intro;
    bool remember_intro = !smoke_mode && capture_dir == NULL;
    if (remember_intro) {
        intro_start(&intro, prefs_get_bool(PREF_INTRO_SEEN, false) ? INTRO_SHORT : INTRO_FULL);
        screen = SCREEN_INTRO;
        audio_music_stop(0);
    }
    bool notice_seen = false;
    int pending_stage = -1;
    AlmanacView almanac_view;
    almanac_view_init(&almanac_view);
    if (capture_dir) {
        app_capture_screens(&platform, capture_dir, skins, profiles, &menu_world, &options);
        status = 0;
        goto cleanup;
    }
    if (smoke.enabled) {
        /* Straight into 1-1 with the cowgirl. Leave enough space for the
         * scripted walk and the shot's longer journey across the wider view,
         * without the zombie reaching her before the observations finish. */
        stage_start(&play, 0, &CHARACTERS[0], &profiles[0].progress);
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
            options_set_fullscreen(&options, platform.fullscreen);
        }

        double now = platform_time();
        float frame_time = (float)(now - previous);
        previous = now;
        bool playing = screen == SCREEN_STAGE && !play.paused &&
                       play.run.phase == RUN_FIGHTING && player_alive(&play.player) && !platform.focus_lost;
        bool save_due = autosave_tick(&save, frame_time, playing);
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
                selected = &options.volume_menu.selected;
            else if (screen == SCREEN_CHARACTER)
                selected = &char_select.selected;
            else if (screen == SCREEN_MENU)
                selected = &menu.selected;
            else if (screen == SCREEN_STAGE && play.paused)
                selected = play.pause_view == PAUSE_VIEW_LIST     ? &play.pause_menu.selected
                           : play.pause_view == PAUSE_VIEW_VOLUME ? &options.volume_menu.selected
                                                                  : NULL;
            Screen previous_screen = screen;
            RunPhase previous_phase = play.run.phase;
            int previous_level = profiles[hero].progress.level;
            AlmanacView previous_almanac = almanac_view;
            BoardView previous_board = board;
            bool was_paused = (screen == SCREEN_STAGE && play.paused) || over_stage(screen, book_return, story_return);
            int previous_selection = selected ? *selected : -1;
            options_apply_pointer(&options, &input, selected);

            /* Esc goes back one screen: the stage's pause, its menu, character
             * select, the title. */
            if (screen == SCREEN_INTRO) {
                bool skip = input.pressed[ACTION_CONFIRM] || input.pressed[ACTION_QUIT] || input.pointer_clicked;
                const IntroCue *fired[8];
                int count = intro_update(&intro, FIXED_DT, skip, fired, 8);
                for (int k = 0; k < count; k++)
                    play_intro_cue(fired[k]);
                if (intro.done) {
                    if (intro.mode == INTRO_FULL && remember_intro)
                        prefs_set_bool(PREF_INTRO_SEEN, true);
                    audio_stop_all(); /* Its noises and the wind; the title's music plays on */
                    stage_backdrop_restart();
                    if (intro_return == SCREEN_TITLE)
                        list_menu_init(&title, TITLE_ITEMS);
                    screen = intro_return;
                    intro_return = SCREEN_TITLE;
                }
            } else if (screen == SCREEN_TITLE) {
                switch (list_menu_update(&title, &input)) {
                case TITLE_PLAY:
                    char_select_init(&char_select, hero);
                    screen = SCREEN_CHARACTER;
                    break;
                case TITLE_STORY:
                    /* Only the intro yet: straight to it; more, the shelf of tapes */
                    if (tapes_unlocked(&save.game.case_file) > 1) {
                        screen = SCREEN_TAPES;
                    } else {
                        intro_start(&intro, INTRO_FULL);
                        intro_return = SCREEN_TITLE;
                        audio_music_stop(400);
                        screen = SCREEN_INTRO;
                    }
                    break;
                case TITLE_CASEFILE:
                    book_return = SCREEN_TITLE;
                    board_view_init(&board);
                    screen = SCREEN_CASEFILE;
                    break;
                case TITLE_ALMANAC:
                    book_return = SCREEN_TITLE;
                    almanac_view_init(&almanac_view);
                    screen = SCREEN_ALMANAC;
                    break;
                case TITLE_CONTROLS:
                    screen = SCREEN_CONTROLS;
                    break;
                case TITLE_VOLUME:
                    list_menu_init(&options.volume_menu, VOLUME_ROWS);
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
                if (!options_step(&options, &input))
                    screen = SCREEN_TITLE;
            } else if (screen == SCREEN_CHARACTER) {
                if (input.pressed[ACTION_QUIT])
                    screen = SCREEN_TITLE;
                int chosen = char_select_update(&char_select, &input);
                if (chosen >= 0) {
                    hero = chosen;
                    menu_init(&menu, &profiles[hero].record);
    if (prefs_get_bool("menu_backdrop_first", false)) /* Her choice: an earlier phase's landscape */
        menu.backdrop = 0;
                    if (save.game.has_checkpoint && save.game.checkpoint_hero == hero)
                        menu.selected = save.game.checkpoint.run.stage_index;
                    screen = SCREEN_MENU;
                }
            } else if (screen == SCREEN_MENU) {
                if (input.pressed[ACTION_QUIT]) {
                    char_select_init(&char_select, hero);
                    screen = SCREEN_CHARACTER;
                }
                /* The mouse on the page: a phase's tab, a stage's tape, the backdrop. */
                HudZone zone;
                int replay = -1;
                bool on_zone = input.pointer_clicked && hud_zone_at(input.pointer_x, input.pointer_y, &zone);
                if (on_zone && zone.kind == HUD_ZONE_PHASE) {
                    menu_show_phase(&menu, zone.index);
                    audio_play("ui/move");
                } else if (on_zone && zone.kind == HUD_ZONE_TAPE) {
                    replay = zone.index;
                    input.pressed[ACTION_CONFIRM] = false; /* Its row was under the click too */
                } else if ((on_zone && zone.kind == HUD_ZONE_BACKDROP) || input.pressed[ACTION_SWAP]) {
                    menu_next_backdrop(&menu, &profiles[hero].record);
                    prefs_set_bool("menu_backdrop_first", menu.backdrop == 0);
                    audio_play("ui/move");
                    input.pressed[ACTION_CONFIRM] = false;
                }
                if (input.pressed[ACTION_USE]) { /* E: the selected stage's tape */
                    int tape = stage_tape(menu.selected, false);
                    if (tape < 0 || !tape_unlocked(&save.game.case_file, tape))
                        tape = stage_tape(menu.selected, true);
                    if (tape >= 0 && tape_unlocked(&save.game.case_file, tape))
                        replay = tape;
                }
                if (replay > 0) {
                    audio_play("ui/confirm");
                    story_start(&story, tape_beat(replay));
                    story_since = platform_time();
                    story_return = SCREEN_MENU;
                    screen = SCREEN_STORY;
                }
                int chosen = screen == SCREEN_MENU ? menu_update(&menu, &input, &profiles[hero].record) : -1;
                if (chosen >= 0) {
                    if (!notice_seen) {
                        pending_stage = chosen;
                        screen = SCREEN_AUTOSAVE_NOTICE;
                    } else {
                        enter_stage(&play, &save, profiles, &options, hero, chosen);
                        prev_player_x = play.player.x;
                        prev_jump = play.player.jump.height;
                        screen = SCREEN_STAGE;
                        STORY_BEFORE(chosen);
                    }
                }
            } else if (screen == SCREEN_AUTOSAVE_NOTICE) {
                if (input.pressed[ACTION_QUIT]) {
                    pending_stage = -1;
                    screen = SCREEN_MENU;
                } else if (input.pressed[ACTION_CONFIRM] && pending_stage >= 0) {
                    notice_seen = true;
                    enter_stage(&play, &save, profiles, &options, hero, pending_stage);
                    prev_player_x = play.player.x;
                    prev_jump = play.player.jump.height;
                    screen = SCREEN_STAGE;
                    STORY_BEFORE(pending_stage);
                    pending_stage = -1;
                }
            } else if (screen == SCREEN_ALMANAC) {
                if (!almanac_view_update(&almanac_view, &input))
                    screen = book_return;
            } else if (screen == SCREEN_CASEFILE) {
                BoardResult result = board_view_update(&board, &save.game.case_file, &input, FIXED_DT);
                if (result == BOARD_BACK) {
                    screen = book_return;
                } else if (result == BOARD_EXAMINE) {
                    exam_open(&exam, board.examined);
                    screen = SCREEN_EXAMINE;
                } else if (result == BOARD_REVEAL) {
                    report_open(&report, board.revealed);
                    screen = SCREEN_REPORT;
                    autosave_request(&save, profiles, hero, &options.volumes,
                                     book_return == SCREEN_STAGE ? &play : NULL);
                }
            } else if (screen == SCREEN_EXAMINE) {
                if (!exam_update(&exam, &input, FIXED_DT)) {
                    screen = SCREEN_CASEFILE;
                }
            } else if (screen == SCREEN_REPORT) {
                bool stamped = false;
                if (!report_update(&report, &input, FIXED_DT, &stamped)) {
                    screen = SCREEN_CASEFILE;
                }
                if (stamped && screen == SCREEN_REPORT)
                    audio_play_in_gain("ui/stamp", SOUND_MASTER, 0.8f);
            } else if (screen == SCREEN_TAPES) {
                TapeView previous_tapes = tapes;
                int tape = tape_view_update(&tapes, &save.game.case_file, &input);
                play_tape_sounds(&previous_tapes, &tapes, &save.game.case_file, &input, tape);
                if (tape == TAPE_BACK) {
                    screen = SCREEN_TITLE;
                } else if (tape == TAPE_INTRO) {
                    intro_start(&intro, INTRO_FULL);
                    intro_return = SCREEN_TAPES;
                    audio_music_stop(400);
                    screen = SCREEN_INTRO;
                } else if (tape > 0) {
                    story_start(&story, tape_beat(tape));
                    story_since = platform_time();
                    story_return = SCREEN_TAPES;
                    screen = SCREEN_STORY;
                }
            } else if (screen == SCREEN_STORY) {
                Story previous_story = story;
                story_update(&story, input.pressed[ACTION_CONFIRM] || input.pointer_clicked,
                             input.pressed[ACTION_QUIT], FIXED_DT);
                story_audio_update(&previous_story, &story, FIXED_DT);
                if (story.done)
                    screen = story_return;
            } else if (!stage_step(&play, &input, &profiles[hero], &options)) {
                save.game.has_checkpoint = false;
                menu_init(&menu, &profiles[hero].record);
    if (prefs_get_bool("menu_backdrop_first", false)) /* Her choice: an earlier phase's landscape */
        menu.backdrop = 0;
                screen = SCREEN_MENU;
                /* A stage cleared for the first time: what its end means, before the menu */
                int cleared = play.run.stage_index;
                const StoryBeat *beat = play.run.phase == RUN_CLEARED ? story_after_stage(cleared) : NULL;
                if (beat && !(save.game.case_file.beats_seen & story_bit(cleared, false))) {
                    save.game.case_file.beats_seen |= story_bit(cleared, false);
                    story_start(&story, beat);
                    story_since = platform_time();
                    story_return = SCREEN_MENU;
                    screen = SCREEN_STORY;
                }
                autosave_request(&save, profiles, hero, &options.volumes, NULL);
            }
            if (screen == SCREEN_STAGE) { /* The clues it turned up, kept for good */
                bool found_clue = false;
                for (int k = 0; k < play.clue_count; k++) {
                    if (casefile_take(&save.game.case_file, play.clues_now[k])) {
                        play.clue_toast = play.clues_now[k];
                        play.clue_toast_time = CLUE_TOAST_SECONDS;
                        found_clue = true;
                    }
                }
                if (found_clue) { /* A batch has one rustle, not stacked copies. */
                    audio_play("ui/book_page");
                    autosave_request(&save, profiles, hero, &options.volumes, &play);
                }
                play.clue_count = 0;
                if (!play.paused && play.clue_toast_time > 0.0f)
                    play.clue_toast_time -= FIXED_DT;
            }
            if (previous_screen == SCREEN_STAGE && screen == SCREEN_STAGE &&
                (play.run.phase != previous_phase || profiles[hero].progress.level != previous_level))
                autosave_request(&save, profiles, hero, &options.volumes, &play);
            /* Clicking outside the window (or switching away) pauses a stage
             * in play, like Esc; a cleared stage has nothing left to pause.
             * The scripted run has no real window to keep focused. */
            if (platform.focus_lost) {
                platform.focus_lost = false;
                if (!smoke.enabled && screen == SCREEN_STAGE && !play.paused &&
                    play.run.phase != RUN_CLEARED)
                    stage_pause(&play);
            }
            if (screen == SCREEN_STAGE && play.request_casefile) {
                play.request_casefile = false;
                book_return = SCREEN_STAGE;
                board_view_init(&board);
                screen = SCREEN_CASEFILE;
            }
            if (screen == SCREEN_STAGE && play.request_almanac) {
                play.request_almanac = false;
                book_return = SCREEN_STAGE;
                almanac_view_init(&almanac_view);
                screen = SCREEN_ALMANAC;
            }
            bool now_paused = (screen == SCREEN_STAGE && play.paused) || over_stage(screen, book_return, story_return);
            if (previous_screen == SCREEN_STAGE && !has_live_stage(screen, book_return, story_return)) {
                audio_stop_all();
                audio_music_stop(0);
            } else if (was_paused != now_paused)
                audio_pause(now_paused);
            bool menu_input = previous_screen != SCREEN_STAGE || was_paused || now_paused;
            /* The click that started or resumed the stage is not a shot. */
            if (screen == SCREEN_STAGE && !now_paused && menu_input)
                platform_block_mouse(&platform);
            if (previous_screen != SCREEN_STORY && screen == SCREEN_STORY)
                story_audio_start(&story);
            bool book_input = play_almanac_sounds(previous_screen, screen, &previous_almanac, &almanac_view) ||
                              play_casefile_sounds(previous_screen, screen, &previous_board, &board);
            if (menu_input && !book_input && previous_screen != SCREEN_INTRO && previous_screen != SCREEN_STORY &&
                previous_screen != SCREEN_TAPES) {
                if (input.pressed[ACTION_QUIT] ||
                    (previous_screen == SCREEN_CHARACTER && char_select.denied))
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

        if (save_due && save.elapsed >= AUTOSAVE_SECONDS)
            autosave_request(&save, profiles, hero, &options.volumes,
                               has_live_stage(screen, book_return, story_return) ? &play : NULL);

        hud_zones_clear();
        World *backdrop_world = &menu_worlds[menu.backdrop >= 0 && menu.backdrop < PHASE_COUNT ? menu.backdrop : 0];
        if (screen == SCREEN_INTRO) {
            intro_render(&platform, &intro, &menu_world, &skins[0]);
        } else if (screen == SCREEN_TITLE) {
            stage_draw_backdrop(&platform, backdrop_world, 0.15f);
            intro_draw_title_dust(platform.renderer, stage_backdrop_seconds());
            hud_draw_title(platform.renderer, &title);
        } else if (screen == SCREEN_CONTROLS) {
            stage_draw_backdrop(&platform, backdrop_world, 0.5f);
            hud_draw_controls(platform.renderer);
        } else if (screen == SCREEN_VOLUME) {
            stage_draw_backdrop(&platform, backdrop_world, 0.5f);
            hud_draw_volume(platform.renderer, &options.volume_menu, &options.volumes);
        } else if (screen == SCREEN_CHARACTER) {
            for (int c = 0; c < CHARACTER_COUNT; c++)
                progress_view[c] = profiles[c].progress;
            stage_draw_backdrop(&platform, backdrop_world, 0.45f);
            hud_draw_characters(platform.renderer, skins, progress_view, char_select.selected,
                                char_select.notice_time > 0.0f);
        } else if (screen == SCREEN_MENU || screen == SCREEN_AUTOSAVE_NOTICE) {
            stage_draw_backdrop(&platform, backdrop_world, 0.45f);
            unsigned seen_tapes = 0;
            for (int t = 1; t < TAPE_COUNT; t++)
                seen_tapes |= tape_unlocked(&save.game.case_file, t) ? 1u << t : 0u;
            hud_draw_menu(platform.renderer, CHARACTERS[hero].name, &profiles[hero].progress,
                          &profiles[hero].record, menu.selected, seen_tapes, menu.backdrop,
                          menu_reached_phase(&profiles[hero].record));
            if (screen == SCREEN_AUTOSAVE_NOTICE)
                hud_draw_autosave_notice(platform.renderer);
            else if (save.game.has_checkpoint && save.game.checkpoint_hero == hero &&
                     menu.selected == save.game.checkpoint.run.stage_index)
                hud_draw_resume_hint(platform.renderer, STAGES[menu.selected].name);
        } else if (screen == SCREEN_ALMANAC) {
            stage_draw_backdrop(&platform, backdrop_world, 0.70f);
            almanac_render(platform.renderer, &profiles[hero].almanac, &almanac_view, (float)platform_time());
        } else if (screen == SCREEN_CASEFILE) {
            stage_draw_backdrop(&platform, backdrop_world, 0.70f);
            casefile_render(platform.renderer, &save.game.case_file, &board, (float)platform_time());
        } else if (screen == SCREEN_EXAMINE) {
            stage_draw_backdrop(&platform, backdrop_world, 0.70f);
            casefile_render(platform.renderer, &save.game.case_file, &board, (float)platform_time());
            exam_render(platform.renderer, &exam, &save.game.case_file);
        } else if (screen == SCREEN_REPORT) {
            stage_draw_backdrop(&platform, backdrop_world, 0.70f);
            casefile_render(platform.renderer, &save.game.case_file, &board, (float)platform_time());
            report_render(platform.renderer, &report, &save.game.case_file);
        } else if (screen == SCREEN_TAPES) {
            stage_draw_backdrop(&platform, backdrop_world, 0.15f);
            intro_draw_title_dust(platform.renderer, stage_backdrop_seconds());
            tapes_render(platform.renderer, &tapes, &save.game.case_file);
        } else if (screen == SCREEN_STORY) {
            story_render(&platform, &story, &save.game.case_file, (float)(platform_time() - story_since), &skins[0]);
        } else {
            hud_set_stage_clues(casefile_stage_found(&save.game.case_file, play.run.stage_index), STAGE_CLUES);
            stage_draw(&platform, &play, &skins[hero], &profiles[hero].progress,
                       accumulator / FIXED_DT, prev_player_x, prev_jump, &options);
        }
        if (!has_live_stage(screen, book_return, story_return) && screen != SCREEN_INTRO)
            audio_music_play(menu.backdrop >= 1 ? MENU_MUSIC_CITY : MENU_MUSIC); /* Keeps playing from one menu to the next */
        if (screen == SCREEN_STAGE && !play.paused)
            casefile_draw_toast(platform.renderer, play.clue_toast,
                                casefile_stage_found(&save.game.case_file, play.run.stage_index),
                                play.clue_toast_time);
        if (screen == SCREEN_STAGE && (save.saving || save.feedback_time > 0.0f))
            hud_draw_autosave_status(platform.renderer, save.saving, save.failed, save.feedback_age);
        platform_present(&platform);
        if (!platform.vsync)
            SDL_Delay(1);
    }
    autosave_request(&save, profiles, hero, &options.volumes,
                       has_live_stage(screen, book_return, story_return) ? &play : NULL);
    status = (smoke.enabled && !smoke.passed) ? 1 : 0;

cleanup:
    if (save_ready)
        autosave_shutdown(&save);
    for (int c = 0; c < CHARACTER_COUNT; c++)
        skin_free(&skins[c]);
    scene_shutdown();
    terrain_render_shutdown();
    stage_render_shutdown();
    story_audio_stop();
    audio_shutdown();
    hud_shutdown();
    if (text_ready)
        text_system_shutdown();
    assets_unload();
    platform_shutdown(&platform);
    return status;
}
