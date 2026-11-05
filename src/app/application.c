#include <math.h>
#include <stdio.h>

#include "app/application.h"
#include "app/autosave.h"
#include "app/capture.h"
#include "app/navigation.h"
#include "app/smoke.h"
#include "app/stage.h"
#include "app/stage_render.h"
#include "engine/assets.h"
#include "engine/audio.h"
#include "engine/text.h"
#include "game/almanac_render.h"
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

static bool has_live_stage(Screen screen, Screen book_return)
{
    return screen == SCREEN_STAGE || (screen == SCREEN_ALMANAC && book_return == SCREEN_STAGE);
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
    int hero = save.game.hero;
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
        /* Straight into 1-1 with the cowgirl. The scripted walk needs the zombie
         * 800 px away; at the view's edge (400 px, she starts centered) it would
         * reach and hit her mid-script. */
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
            bool was_paused = (screen == SCREEN_STAGE && play.paused) ||
                              (screen == SCREEN_ALMANAC && almanac_return == SCREEN_STAGE);
            int previous_selection = selected ? *selected : -1;
            options_apply_pointer(&options, &input, selected);

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
                    if (save.game.has_checkpoint && save.game.checkpoint_hero == hero)
                        menu.selected = save.game.checkpoint.run.stage_index;
                    screen = SCREEN_MENU;
                }
            } else if (screen == SCREEN_MENU) {
                if (input.pressed[ACTION_QUIT]) {
                    char_select_init(&char_select, hero);
                    screen = SCREEN_CHARACTER;
                }
                int chosen = menu_update(&menu, &input, &profiles[hero].record);
                if (chosen >= 0) {
                    if (!notice_seen) {
                        pending_stage = chosen;
                        screen = SCREEN_AUTOSAVE_NOTICE;
                    } else {
                        enter_stage(&play, &save, profiles, &options, hero, chosen);
                        prev_player_x = play.player.x;
                        prev_jump = play.player.jump.height;
                        screen = SCREEN_STAGE;
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
                    pending_stage = -1;
                }
            } else if (screen == SCREEN_ALMANAC) {
                if (!almanac_view_update(&almanac_view, &input))
                    screen = almanac_return;
            } else if (!stage_step(&play, &input, &profiles[hero], &options)) {
                save.game.has_checkpoint = false;
                autosave_request(&save, profiles, hero, &options.volumes, NULL);
                menu_init(&menu, &profiles[hero].record);
                screen = SCREEN_MENU;
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
            if (screen == SCREEN_STAGE && play.request_almanac) {
                play.request_almanac = false;
                almanac_return = SCREEN_STAGE;
                almanac_view_init(&almanac_view);
                screen = SCREEN_ALMANAC;
            }
            bool now_paused = (screen == SCREEN_STAGE && play.paused) ||
                              (screen == SCREEN_ALMANAC && almanac_return == SCREEN_STAGE);
            if (previous_screen == SCREEN_STAGE && screen != SCREEN_STAGE && screen != SCREEN_ALMANAC) {
                audio_stop_all();
                audio_music_stop(0);
            } else if (was_paused != now_paused)
                audio_pause(now_paused);
            bool menu_input = previous_screen != SCREEN_STAGE || was_paused || now_paused;
            /* The click that started or resumed the stage is not a shot. */
            if (screen == SCREEN_STAGE && !now_paused && menu_input)
                platform_block_mouse(&platform);
            bool book_input = play_almanac_sounds(previous_screen, screen, &previous_almanac, &almanac_view);
            if (menu_input && !book_input) {
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

        if (save_due && save.elapsed >= AUTOSAVE_SECONDS)
            autosave_request(&save, profiles, hero, &options.volumes,
                               has_live_stage(screen, almanac_return) ? &play : NULL);

        hud_zones_clear();
        if (screen == SCREEN_TITLE) {
            stage_draw_backdrop(&platform, &menu_world, 0.15f);
            hud_draw_title(platform.renderer, &title);
        } else if (screen == SCREEN_CONTROLS) {
            stage_draw_backdrop(&platform, &menu_world, 0.5f);
            hud_draw_controls(platform.renderer);
        } else if (screen == SCREEN_VOLUME) {
            stage_draw_backdrop(&platform, &menu_world, 0.5f);
            hud_draw_volume(platform.renderer, &options.volume_menu, &options.volumes);
        } else if (screen == SCREEN_CHARACTER) {
            for (int c = 0; c < CHARACTER_COUNT; c++)
                progress_view[c] = profiles[c].progress;
            stage_draw_backdrop(&platform, &menu_world, 0.45f);
            hud_draw_characters(platform.renderer, skins, progress_view, char_select.selected);
        } else if (screen == SCREEN_MENU || screen == SCREEN_AUTOSAVE_NOTICE) {
            stage_draw_backdrop(&platform, &menu_world, 0.45f);
            hud_draw_menu(platform.renderer, CHARACTERS[hero].name, &profiles[hero].progress,
                          &profiles[hero].record, menu.selected);
            if (screen == SCREEN_AUTOSAVE_NOTICE)
                hud_draw_autosave_notice(platform.renderer);
            else if (save.game.has_checkpoint && save.game.checkpoint_hero == hero &&
                     menu.selected == save.game.checkpoint.run.stage_index)
                hud_draw_resume_hint(platform.renderer, STAGES[menu.selected].name);
        } else if (screen == SCREEN_ALMANAC) {
            stage_draw_backdrop(&platform, &menu_world, 0.70f);
            almanac_render(platform.renderer, &profiles[hero].almanac, &almanac_view, (float)platform_time());
        } else {
            stage_draw(&platform, &play, &skins[hero], &profiles[hero].progress,
                       accumulator / FIXED_DT, prev_player_x, prev_jump, &options);
        }
        if (!has_live_stage(screen, almanac_return))
            audio_music_play(MENU_MUSIC); /* Keeps playing from one menu to the next */
        if (screen == SCREEN_STAGE && (save.saving || save.feedback_time > 0.0f))
            hud_draw_autosave_status(platform.renderer, save.saving, save.failed, save.feedback_age);
        platform_present(&platform);
        if (!platform.vsync)
            SDL_Delay(1);
    }
    autosave_request(&save, profiles, hero, &options.volumes,
                       has_live_stage(screen, almanac_return) ? &play : NULL);
    status = (smoke.enabled && !smoke.passed) ? 1 : 0;

cleanup:
    if (save_ready)
        autosave_shutdown(&save);
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
