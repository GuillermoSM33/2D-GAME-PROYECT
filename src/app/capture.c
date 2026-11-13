#include <limits.h>
#include <stdio.h>

#include "app/capture.h"
#include "app/intro_render.h"
#include "app/story_render.h"
#include "game/casefile_render.h"
#include "app/stage.h"
#include "engine/assets.h"
#include "game/almanac_render.h"
#include "game/camera.h"
#include "game/hud.h"
#include "game/scene.h"

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
static void idle_steps(StagePlay *play, Profile *profile, InputState *input, int n, AppOptions *options)
{
    bool down[ACTION_COUNT] = {0};
    for (int i = 0; i < n; i++) {
        input_update(input, down);
        stage_step(play, input, profile, options);
    }
}

/* --capturas: every screen drawn once into dir, to check the interface's
 * art without playing (the menus, a fight, a wall, the pause, a defeat). */
void app_capture_screens(Platform *platform, const char *dir, CharacterSkin *skins,
                            Profile *profiles, World *menu_world, AppOptions *options)
{
    SDL_Renderer *r = platform->renderer;
    static StagePlay play;
    InputState input;
    input_init(&input);
    ListMenu list;
    list_menu_init(&list, TITLE_ITEMS);
    Progress progress[APP_PROFILE_CAPACITY];
    for (int c = 0; c < CHARACTER_COUNT; c++)
        progress[c] = profiles[c].progress;

    stage_draw_backdrop(platform, menu_world, 0.15f);
    intro_draw_title_dust(r, 0.0);
    hud_draw_title(r, &list);
    save_capture(r, dir, "1_titulo");

    /* The case file: some clues in, one case ready, one solved; a question
     * answered wrong; the popup of a clue found; two story beats. */
    {
        CaseFile file;
        casefile_init(&file);
        for (int c = 0; c < 8; c++)
            casefile_take(&file, c);
        for (int c = 9; c < 12; c++)
            casefile_take(&file, c);
        file.solved = 1u << 1;
        BoardView board;
        board_view_init(&board);
        board.row = 0;
        board.col = 0; /* The longest text: three lines */
        stage_draw_backdrop(platform, menu_world, 0.70f);
        casefile_render(r, &file, &board, 0.0f);
        save_capture(r, dir, "0n_expediente");
        board.row = 3;
        board.col = 0;
        stage_draw_backdrop(platform, menu_world, 0.70f);
        casefile_render(r, &file, &board, 0.0f);
        save_capture(r, dir, "0o_expediente_sin_pista");
        board.row = 2;
        board.col = 3;
        board.asking = true;
        board.option = 0;
        board.wrong_time = 1.2f;
        stage_draw_backdrop(platform, menu_world, 0.70f);
        casefile_render(r, &file, &board, 0.0f);
        save_capture(r, dir, "0p_expediente_pregunta");
        stage_draw_backdrop(platform, menu_world, 0.0f);
        casefile_draw_toast(r, 1, 2, 3.0f);
        save_capture(r, dir, "0q_pista_encontrada");
        Report report;
        report_open(&report, 0); /* The longest report: it must fit the sheet */
        report.time = 2.0f;
        stage_draw_backdrop(platform, menu_world, 0.70f);
        casefile_render(r, &file, &board, 0.0f);
        report_render(r, &report, &file);
        save_capture(r, dir, "0r_expediente_resuelto");
        for (int clue = 0; clue < CLUE_COUNT; clue++) { /* Every clue up close */
            ClueExam exam;
            exam_open(&exam, clue);
            exam.time = 1.0f;
            stage_draw_backdrop(platform, menu_world, 0.70f);
            casefile_render(r, &file, &board, 0.0f);
            exam_render(r, &exam, &file);
            char name[40];
            snprintf(name, sizeof(name), "0u_examen_%02d", clue);
            save_capture(r, dir, name);
        }
        file.beats_seen = (1u << 1) | (1u << 2);
        TapeView tapes = {1};
        stage_draw_backdrop(platform, menu_world, 0.15f);
        tapes_render(r, &tapes, &file);
        save_capture(r, dir, "0t_historia_cintas");
        /* Every line of every tape, in the middle of its shot */
        TapeView city_tapes = {7}; /* Its second row, scrolled to: the second route's */
        file.beats_seen |= story_bit(5, true) | story_bit(5, false) | story_bit(6, false);
        stage_draw_backdrop(platform, menu_world, 0.15f);
        tapes_render(r, &city_tapes, &file);
        save_capture(r, dir, "0t_historia_cintas_ruta2");
        for (int stage = 1; stage < TAPE_COUNT; stage++) { /* The tape's number: 1-4 are also their stage */
            const StoryBeat *beat = tape_beat(stage);
            for (int line = 0; line < beat->count; line++) {
                Story story;
                story_start(&story, beat);
                story.line = line;
                story.time = 3.2f;
                story_render(platform, &story, &file, 0.0f, &skins[0]);
                char name[48];
                snprintf(name, sizeof(name), "0s_cinta_%d_%d", stage, line + 1);
                save_capture(r, dir, name);
                if (stage == 4 && line == 0) { /* Keep its valley depth through the whole pan. */
                    const float moments[] = {0.8f, story_line_length(beat->lines[0]) - 0.7f};
                    for (int k = 0; k < 2; k++) {
                        story.time = moments[k];
                        story_render(platform, &story, &file, 0.0f, &skins[0]);
                        snprintf(name, sizeof(name), "0s_laboratorio_valle_%d", k);
                        save_capture(r, dir, name);
                    }
                }
            }
        }
    }

    /* The opening cinematic, a moment of each scene (and three of the last). */
    static const struct {
        float time;
        const char *name;
    } intro_shots[] = {
        {4.0f, "0a_intro_pasillo"}, {13.0f, "0b_intro_monitores"}, {21.5f, "0c_intro_alarma"}, {37.40f, "0f1_intro_disparo"}, {37.62f, "0f2_intro_sacudida"}, {40.0f, "0f3_intro_sin_senal"},
        {29.0f, "0d_intro_mercenarios"}, {30.7f, "0d1_intro_mercenarios_cerca"},
        {35.0f, "0e_intro_muestra"}, {38.8f, "0f_intro_camara_caida"},
        {46.0f, "0g_intro_ambulancia"}, {54.0f, "0h_intro_pueblo"}, {57.0f, "0i_intro_cuervos"},
        {63.0f, "0j_intro_tumba"}, {68.0f, "0k_intro_sheriff"}, {69.5f, "0l_intro_sheriff_camina"},
        {71.5f, "0l1_intro_sheriff_sigue"}, {72.8f, "0l2_intro_sheriff_fuera"},
        {75.9f, "0m_intro_titulo"},
    };
    for (size_t i = 0; i < sizeof(intro_shots) / sizeof(intro_shots[0]); i++) {
        Intro intro;
        intro_start(&intro, INTRO_FULL);
        intro.time = intro_shots[i].time;
        intro_render(platform, &intro, menu_world, &skins[0]);
        save_capture(r, dir, intro_shots[i].name);
    }
    stage_draw_backdrop(platform, menu_world, 0.5f);
    hud_draw_controls(r);
    save_capture(r, dir, "2_controles");
    list_menu_init(&options->volume_menu, VOLUME_ROWS);
    stage_draw_backdrop(platform, menu_world, 0.5f);
    hud_draw_volume(r, &options->volume_menu, &options->volumes);
    save_capture(r, dir, "3_volumen");
    stage_draw_backdrop(platform, menu_world, 0.45f);
    hud_draw_characters(r, skins, progress, 1, false);
    save_capture(r, dir, "4_personajes");
    stage_draw_backdrop(platform, menu_world, 0.45f);
    hud_draw_characters(r, skins, progress, 2, true);
    save_capture(r, dir, "4_personajes_en_desarrollo");
    profiles[1].record.cleared[0] = true;
    stage_draw_backdrop(platform, menu_world, 0.45f);
    hud_draw_menu(r, CHARACTERS[1].name, &profiles[1].progress, &profiles[1].record, 1, 1u << 1, 0, 0);
    save_capture(r, dir, "5_niveles");
    stage_draw_backdrop(platform, menu_world, 0.45f); /* Scrolled down to the second route */
    {   /* The second phase's page: reached, its tapes seen, its own landscape behind */
        static World city_world;
        world_init(&city_world, &THEME_AFUERAS);
        StageRecord reached = profiles[1].record;
        for (int s = 0; s < 7; s++)
            reached.cleared[s] = true, reached.stars[s] = 1 + (unsigned)s % 3;
        stage_draw_backdrop(platform, &city_world, 0.45f);
        hud_draw_menu(r, CHARACTERS[1].name, &profiles[1].progress, &reached, 7, 0x7ffu, 1, 1);
        save_capture(r, dir, "5_niveles_ruta2");
    }
    hud_draw_autosave_notice(r);
    save_capture(r, dir, "33_aviso_autoguardado");
    profiles[1].record.cleared[0] = false;

    hud_set_stage_clues(1, STAGE_CLUES); /* The plate's clue count on the stage captures */
    /* The SWAT in 1-1, the first zombie woken and coming. */
    stage_start(&play, 0, &CHARACTERS[1], &profiles[1].progress);
    play.player.x = play.run.zombies[0].x - ROUTE_WAKE_DISTANCE + 20.0f;
    idle_steps(&play, &profiles[1], &input, 150, options);
    stage_draw(platform, &play, &skins[1], &profiles[1].progress, 1.0f, play.player.x,
               play.player.jump.height, options);
    save_capture(r, dir, "6_pelea");
    casefile_draw_toast(r, 1, 2, 3.0f);
    save_capture(r, dir, "6_pelea_pista");
    stage_draw(platform, &play, &skins[1], &profiles[1].progress, 1.0f, play.player.x, play.player.jump.height, options);
    casefile_draw_toast(r, 6, 1, 3.0f); /* A name in two lines */
    save_capture(r, dir, "6_pelea_pista_larga");
    hud_draw_autosave_status(r, true, false, 0.4f);
    save_capture(r, dir, "34_autoguardado_en_curso");
    stage_draw(platform, &play, &skins[1], &profiles[1].progress, 1.0f, play.player.x,
               play.player.jump.height, options);
    hud_draw_autosave_status(r, false, false, 0.0f);
    save_capture(r, dir, "35_autoguardado_completo");

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
    idle_steps(&play, &profiles[1], &input, 2, options);
    stage_draw(platform, &play, &skins[1], &profiles[1].progress, 1.0f, play.player.x,
               play.player.jump.height, options);
    save_capture(r, dir, "7_muro");

    stage_pause(&play);
    stage_draw(platform, &play, &skins[1], &profiles[1].progress, 1.0f, play.player.x,
               play.player.jump.height, options);
    save_capture(r, dir, "8_pausa");
    play.paused = false;
    player_hit(&play.player, 1e6f, 1);
    idle_steps(&play, &profiles[1], &input, 2, options);
    stage_draw(platform, &play, &skins[1], &profiles[1].progress, 1.0f, play.player.x,
               play.player.jump.height, options);
    save_capture(r, dir, "9_derrota");

    /* 1-4 at night: sat on the bench by the campfire, dozing off. */
    stage_start(&play, 3, &CHARACTERS[1], &profiles[1].progress);
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
        idle_steps(&play, &profiles[1], &input, (int)((SIT_DOWN_TIME + SIT_DOZE_TIME) / FIXED_DT) + 40, options);
        stage_draw(platform, &play, &skins[1], &profiles[1].progress, 1.0f, play.player.x,
                   play.player.jump.height, options);
        save_capture(r, dir, "10_descanso");
    }
    /* The second route, each stage: its first patrol car going off with the
     * horde walking in, its first wall (a front or the derailed train), its
     * rest stop with the burning drum, and its burning drums on the road. */
    for (int stage = 5; stage < STAGE_COUNT; stage++) {
        const char *shots[] = {"horda", "muro", "descanso", "barriles"};
        const TerrainKind kinds[] = {TERRAIN_SIREN, TERRAIN_WALL, TERRAIN_CAMPFIRE, TERRAIN_BURNER};
        for (int shot = 0; shot < 4; shot++) {
            stage_start(&play, stage, &CHARACTERS[0], &profiles[0].progress);
            int at = -1;
            for (int i = 0; i < play.run.terrain.count && at < 0; i++)
                if (play.run.terrain.items[i].kind == kinds[shot])
                    at = i;
            if (at < 0)
                continue;
            float x = play.run.terrain.items[at].x;
            for (int k = 0; k < play.run.zombie_count; k++) { /* Only the horde in this picture */
                if (shot == 0 && play.run.siren_of[k] == at + 1)
                    continue;
                play.run.zombies[k].x = play.run.goal_x + 1e4f;
                play.run.zombies[k].awake = false;
            }
            play.player.x = shot == 0   ? x - SIREN_TRIP_RANGE + 5.0f
                            : shot == 1 ? x - terrain_half_width(TERRAIN_WALL) - PLAYER_BODY_HALF_WIDTH
                            : shot == 2 ? x - 120.0f : x - 260.0f;
            play.run.dynamite = 1;
            idle_steps(&play, &profiles[0], &input, shot == 0 ? 45 : 20, options);
            stage_draw(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x,
                       play.player.jump.height, options);
            char name[48];
            snprintf(name, sizeof(name), "4%d_ruta2_%s_%s", shot, STAGES[stage].name, shots[shot]);
            save_capture(r, dir, name);
        }
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
        stage_start(&play, stage, &CHARACTERS[0], &profiles[0].progress);
        weather_start(&play.weather, (Weather)kind, camera_left(play.player.x));
        for (int step = 0; step < 150; step++)
            weather_update(&play.weather, camera_left(play.player.x), FIXED_DT);
        if (kind == WEATHER_STORM)
            play.weather.flash = 0.0f; /* Inspect the rain rather than a white flash */
        stage_draw(platform, &play, &skins[0], &profiles[0].progress, 1.0f,
                   play.player.x, play.player.jump.height, options);
        save_capture(r, dir, weather_names[kind]);
    }
    Progress veteran = profiles[1].progress;
    veteran.level = POWER_LEVEL;
    veteran.gold = 123456;
    stage_start(&play, 2, &CHARACTERS[1], &veteran);
    stage_swap_weapon(&play);
    play.player.health = 27;
    play.player.water = 12;
    play.player.bleeding = true;
    play.player.slow_time = 3.0f;
    play.player.thirst = DEHYDRATED;
    play.player.wet = 1.0f;
    play.run.dynamite = 12;
    play.player.shot.rounds = 0;
    shot_reload_now(&play.player.shot);
    stage_draw(platform, &play, &skins[1], &veteran, 1.0f,
               play.player.x, play.player.jump.height, options);
    save_capture(r, dir, "14_hud_estados_recarga");
    hud_set_pointer(24, 114); /* The first condition opens its description */
    stage_draw(platform, &play, &skins[1], &veteran, 1.0f,
               play.player.x, play.player.jump.height, options);
    save_capture(r, dir, "14_hud_estado_detalle");
    hud_set_pointer(-1, -1);
    veteran.gold = veteran.xp = INT_MAX;
    play.player.health = 123456789;
    play.player.max_health = INT_MAX;
    play.player.water = INT_MAX;
    play.player.cold = true;
    play.player.fatigue = FATIGUE_STROKE;
    play.run.omen = true;
    play.run.dynamite = INT_MAX;
    play.power_cooldown = 9.0f;
    stage_draw(platform, &play, &skins[1], &veteran, 1.0f,
               play.player.x, play.player.jump.height, options);
    save_capture(r, dir, "15_hud_contadores_largos");

    Progress sheriff = profiles[0].progress;
    sheriff.level = POWER_LEVEL;
    stage_start(&play, 0, &CHARACTERS[0], &sheriff);
    play.player.shot.rounds = 3;
    play.player.shot.other_rounds = 6;
    stage_draw(platform, &play, &skins[0], &sheriff, 1.0f, play.player.x, 0.0f, options);
    save_capture(r, dir, "15_duales_cargadores_independientes");
    input = (InputState){0};
    input.pressed[ACTION_RELOAD] = true;
    player_update(&play.player, &input, FIXED_DT);
    stage_draw(platform, &play, &skins[0], &sheriff, 1.0f, play.player.x, 0.0f, options);
    save_capture(r, dir, "15_duales_recarga");
    for (int fire = 0; fire < 2; fire++) {
        stage_start(&play, 0, &CHARACTERS[0], &sheriff);
        terrain_clear(&play.run.terrain);
        play.run.zombie_count = 0;
        if (fire) {
            terrain_add(&play.run.terrain, TERRAIN_BARREL, play.player.x)->blowing = true;
            input = (InputState){0};
            player_update(&play.player, &input, FIXED_DT);
            run_update(&play.run, &play.player, &sheriff, FIXED_DT);
            terrain_add(&play.run.terrain, TERRAIN_FIRE, play.player.x);
        }
        play.player.shot.rounds = 2;
        play.player.shot.other_rounds = 5;
        input = (InputState){0};
        input.pressed[ACTION_RELOAD] = true;
        for (int tick = 0; tick <= 150; tick++) {
            player_update(&play.player, &input, FIXED_DT);
            input.pressed[ACTION_RELOAD] = false;
            run_update(&play.run, &play.player, &sheriff, FIXED_DT);
            if (tick % 3 != 0) continue;
            stage_draw(platform, &play, &skins[0], &sheriff, 1.0f, play.player.x, 0.0f, options);
            char name[64];
            snprintf(name, sizeof(name), "15_duales_recarga_%s_%03d", fire ? "fuego" : "quieta", tick);
            save_capture(r, dir, name);
        }
    }

    /* Resume ordinary fire after only the first cylinder finished reloading. */
    stage_start(&play, 0, &CHARACTERS[0], &sheriff);
    terrain_clear(&play.run.terrain);
    play.run.zombie_count = 0;
    play.player.shot.rounds = play.player.shot.other_rounds = 0;
    input = (InputState){0};
    for (int tick = 0; tick <= 180; tick++) {
        input.pressed[ACTION_RELOAD] = tick == 0;
        input.pressed[ACTION_SHOOT] = input.down[ACTION_SHOOT] = tick == 85;
        player_update(&play.player, &input, FIXED_DT);
        run_update(&play.run, &play.player, &sheriff, FIXED_DT);
        if (tick % 3 != 0) continue;
        stage_draw(platform, &play, &skins[0], &sheriff, 1.0f, play.player.x, 0.0f, options);
        char name[64];
        snprintf(name, sizeof(name), "15_duales_recarga_cortada_%03d", tick);
        save_capture(r, dir, name);
    }

    stage_start(&play, 0, &CHARACTERS[0], &sheriff);
    terrain_clear(&play.run.terrain);
    play.run.zombie_count = 0;
    play.player.shot.rounds = 2;
    play.player.shot.other_rounds = 5;
    input = (InputState){0};
    input.down[ACTION_RIGHT] = true;
    for (int tick = 0; tick <= 150; tick++) {
        input.pressed[ACTION_RELOAD] = tick == 0;
        player_update(&play.player, &input, FIXED_DT);
        run_update(&play.run, &play.player, &sheriff, FIXED_DT);
        if (tick != 18 && tick != 54 && tick != 114 && tick != 150) continue;
        stage_draw(platform, &play, &skins[0], &sheriff, 1.0f, play.player.x, 0.0f, options);
        char name[64];
        snprintf(name, sizeof(name), "15_duales_recarga_caminando_%03d", tick);
        save_capture(r, dir, name);
    }

    Almanac review_book;
    AlmanacView review_view;
    almanac_init(&review_book);
    almanac_view_init(&review_view);
    almanac_discover(&review_book, ZOMBIE_KIND_RIOT, false, 3);
    almanac_discover(&review_book, ZOMBIE_KIND_SOLDIER, true, 5);
    almanac_discover(&review_book, ZOMBIE_KIND_RIOT_SHIELD, false, 7);
    almanac_discover(&review_book, ZOMBIE_KIND_CIVIL_FEMALE_1, false, 2);
    almanac_view_select(&review_view, almanac_index(ZOMBIE_KIND_RIOT_SHIELD, false));
    stage_draw_backdrop(platform, menu_world, .70f);
    almanac_render(r, &review_book, &review_view, .25f);
    save_capture(r, dir, "16_almanaque");
    review_view.detail = true;
    stage_draw_backdrop(platform, menu_world, .70f);
    almanac_render(r, &review_book, &review_view, .25f);
    save_capture(r, dir, "17_almanaque_ficha");

    /* One fixed night scene isolates light height, occlusion and the
     * difference between a high lantern, a hand-held beam and a blast. */
    stage_start(&play, 3, &CHARACTERS[1], &profiles[1].progress);
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
    stage_draw(platform, &play, &skins[1], &profiles[1].progress, 1.0f, play.player.x, 0.0f, options);
    save_capture(r, dir, "18_luz_farol");
    play.flashlight = true;
    stage_draw(platform, &play, &skins[1], &profiles[1].progress, 1.0f, play.player.x, 0.0f, options);
    save_capture(r, dir, "19_luz_linterna");
    play.flashlight = false;
    effects_spawn(&play.effects, terrain_explosion(), play.player.x + 300.0f, BASELINE, 1);
    stage_draw(platform, &play, &skins[1], &profiles[1].progress, 1.0f, play.player.x, 0.0f, options);
    save_capture(r, dir, "20_luz_explosion");
    effects_update(&play.effects, .4f);
    stage_draw(platform, &play, &skins[1], &profiles[1].progress, 1.0f, play.player.x, 0.0f, options);
    save_capture(r, dir, "21_luz_explosion_cola");
    effects_clear(&play.effects);
    play.run.terrain.items[0].spent = true;
    terrain_add(&play.run.terrain, TERRAIN_FIRE, play.run.terrain.items[0].x);
    stage_draw(platform, &play, &skins[1], &profiles[1].progress, 1.0f, play.player.x, 0.0f, options);
    save_capture(r, dir, "22_farol_roto");

    /* The road's obstacles side by side (a barricade over her head, the
     * hidden snare and net), then caught by the snare, hanging. */
    stage_start(&play, 0, &CHARACTERS[0], &profiles[0].progress);
    terrain_clear(&play.run.terrain);
    play.run.zombie_count = 0;
    terrain_add(&play.run.terrain, TERRAIN_BARRICADE, play.player.x + 260.0f);
    terrain_add(&play.run.terrain, TERRAIN_SNARE, play.player.x + 560.0f);
    terrain_add(&play.run.terrain, TERRAIN_NET, play.player.x + 800.0f);
    terrain_add(&play.run.terrain, TERRAIN_SPIKES, play.player.x - 240.0f);
    weather_start(&play.weather, WEATHER_CLEAR, camera_left(play.player.x));
    stage_draw(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f, options);
    save_capture(r, dir, "24_obstaculos");
    Piece *wire = terrain_add(&play.run.terrain, TERRAIN_WIRE, play.player.x + 130.0f);
    stage_draw(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f, options);
    save_capture(r, dir, "24_alambre");
    wire->spent = true;
    play.player.x = play.run.terrain.items[1].x;
    idle_steps(&play, &profiles[0], &input, 90, options);
    stage_draw(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x,
               play.player.jump.height, options);
    save_capture(r, dir, "25_lazo");
    play.player.x = play.run.terrain.items[2].x;
    play.player.state = PLAYER_IDLE;
    play.player.jump.height = 0.0f;
    idle_steps(&play, &profiles[0], &input, 90, options);
    stage_draw(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x,
               play.player.jump.height, options);
    save_capture(r, dir, "26_red");
    play.player.catch_shake = CATCH_SHAKE_TIME * 0.5f; /* Mid-swing at the ropes */
    stage_draw(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x,
               play.player.jump.height, options);
    save_capture(r, dir, "26_red_golpe");
    play.player.catch_shake = 0.0f;

    /* The road's props at their size beside her: the bottles' table, a
     * crate, both benches with a campfire, a lamp and a coffin. */
    stage_start(&play, 0, &CHARACTERS[0], &profiles[0].progress);
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
    stage_draw(platform, &play, &skins[0], &profiles[0].progress, 1.0f, px + 300.0f, 0.0f, options);
    save_capture(r, dir, "27_props");

    /* The reworked chest in context: identical ground contact through the lid
     * poses, with its body and lock clear beside the sheriff. */
    chest_place(&play.run.chests[0], px + 180.0f, 1);
    const int chest_frames[] = {0, 3, 5};
    for (int k = 0; k < 3; k++) {
        play.run.chests[0].state = k ? CHEST_OPENING : CHEST_CLOSED;
        play.run.chests[0].anim.frame = chest_frames[k];
        stage_draw(platform, &play, &skins[0], &profiles[0].progress, 1.0f, px, 0.0f, options);
        char name[40];
        snprintf(name, sizeof(name), "27_cofre_%d", chest_frames[k]);
        save_capture(r, dir, name);
    }
    chest_clear(&play.run.chests[0]);

    /* Wading the river's deep middle, to the waist; a puddle on the bank. */
    terrain_clear(&play.run.terrain);
    Piece *river = terrain_add(&play.run.terrain, TERRAIN_RIVER, px + 200.0f);
    terrain_add(&play.run.terrain, TERRAIN_PUDDLE, px - 380.0f);
    scene_set_rivers(&river->x, 1, terrain_half_width(TERRAIN_RIVER));
    play.player.x = river->x + 40.0f;
    play.run.zombie_count = 1;
    zombie_spawn(&play.run.zombies[0], &ZOMBIE_RIOT, river->x + 300.0f);
    play.prev_zombie_x[0] = play.run.zombies[0].x;
    idle_steps(&play, &profiles[0], &input, 4, options);
    stage_draw(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f, options);
    save_capture(r, dir, "28_rio");
    play.flashlight = true; /* Her gun and its light sunk with her */
    play.flashlight_since = 10.0f;
    stage_draw(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f, options);
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
        stage_draw_backdrop(platform, menu_world, .70f);
        almanac_render(r, &review_book, &review_view, .45f);
        snprintf(name, sizeof(name), "23_catalogo_%02d", page + 1);
        save_capture(r, dir, name);
    }

    /* By day, on the things in its way. */
    stage_start(&play, 1, &CHARACTERS[0], &profiles[0].progress);
    terrain_clear(&play.run.terrain);
    play.run.zombie_count = 1;
    zombie_spawn(&play.run.zombies[0], &ZOMBIE_RIOT, play.player.x + 420.0f);
    play.prev_zombie_x[0] = play.run.zombies[0].x;
    terrain_add(&play.run.terrain, TERRAIN_CRATE, play.player.x + 220.0f);
    weather_start(&play.weather, WEATHER_CLEAR, camera_left(play.player.x));
    play.flashlight = true;
    play.flashlight_since = 10.0f;
    stage_draw(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f, options);
    save_capture(r, dir, "29_linterna_de_dia");

    /* The flashlight: each one turning it on, then lit and walking. */
    for (int c = 0; c < 2; c++) {
        static const float MOMENTS[] = {.5f, 1.1f, 1.5f, 1.9f};
        stage_start(&play, 3, &CHARACTERS[c], &profiles[c].progress);
        terrain_clear(&play.run.terrain);
        play.run.zombie_count = 0;
        weather_start(&play.weather, WEATHER_CLEAR, camera_left(play.player.x));
        char name[64];
        for (int m = 0; m < 4; m++) {
            play.flashlight_since = MOMENTS[m];
            stage_draw(platform, &play, &skins[c], &profiles[c].progress, 1.0f, play.player.x, 0.0f, options);
            snprintf(name, sizeof(name), "29_linterna_%d_%d", c, m);
            save_capture(r, dir, name);
        }
        bool down[ACTION_COUNT] = {0};
        down[ACTION_RIGHT] = true;
        for (int i = 0; i < 40; i++) {
            input_update(&input, down);
            stage_step(&play, &input, &profiles[c], options);
        }
        stage_draw(platform, &play, &skins[c], &profiles[c].progress, 1.0f, play.player.x, 0.0f, options);
        snprintf(name, sizeof(name), "29_linterna_%d_caminando", c);
        save_capture(r, dir, name);
    }

    /* The cowgirl with both guns holstered, walking. */
    stage_start(&play, 0, &CHARACTERS[0], &profiles[0].progress);
    terrain_clear(&play.run.terrain);
    play.run.zombie_count = 0;
    weather_start(&play.weather, WEATHER_CLEAR, camera_left(play.player.x));
    play.duals_out = true;
    stage_refresh_weapons(&play, profiles[0].progress.level);
    play.flashlight = false;
    play.flashlight_since = 10.0f;
    bool walking[ACTION_COUNT] = {0};
    walking[ACTION_RIGHT] = true;
    for (int i = 0; i < 24; i++) {
        input_update(&input, walking);
        stage_step(&play, &input, &profiles[0], options);
    }
    stage_draw(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f, options);
    save_capture(r, dir, "31_duales_caminando");
    /* Her ricochet, in the engine, on two zombies: with both guns, then one. */
    for (int guns_out = 1; guns_out >= 0; guns_out--) {
        Progress kept = profiles[0].progress;
        stage_start(&play, 0, &CHARACTERS[0], &profiles[0].progress);
        terrain_clear(&play.run.terrain);
        weather_start(&play.weather, WEATHER_CLEAR, camera_left(play.player.x));
        profiles[0].progress.level = POWER_LEVEL;
        play.duals_out = guns_out;
        stage_refresh_weapons(&play, POWER_LEVEL);
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
            stage_step(&play, &input, &profiles[0], options);
            if (i % 4 == 3) {
                char shot_name[64];
                stage_draw(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f, options);
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
        stage_draw(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f, options);
        snprintf(swap_name, sizeof(swap_name), "32_cambio_caminando_%d", f);
        save_capture(r, dir, swap_name);
    }
    play.player.swap_time = 0.0f;

    /* The cowgirl with it on, one gun and two: her blow, and the duals' turns. */
    stage_start(&play, 3, &CHARACTERS[0], &profiles[0].progress);
    terrain_clear(&play.run.terrain);
    play.run.zombie_count = 0;
    weather_start(&play.weather, WEATHER_CLEAR, camera_left(play.player.x));
    play.flashlight = true;
    play.flashlight_since = 10.0f;
    for (int duals = 0; duals < 2; duals++) {
        char name[64];
        play.duals_out = duals == 1;
        stage_refresh_weapons(&play, profiles[0].progress.level);
        play.player.melee_wait = 0.0f;
        player_melee(&play.player);
        for (int f = 1; f < 5; f++) {
            animation_set_frame(&play.player.anim, f);
            stage_draw(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f, options);
            snprintf(name, sizeof(name), "30_golpe_linterna_%d_%d", duals, f);
            save_capture(r, dir, name);
        }
        play.player.state = PLAYER_IDLE;
    }
    bool trigger[ACTION_COUNT] = {0};
    trigger[ACTION_SHOOT] = true;
    input_update(&input, trigger);
    stage_step(&play, &input, &profiles[0], options);
    for (int turn = 0; turn < 2; turn++) {
        char name[64];
        play.player.shot.other_gun = turn == 1;
        for (int f = 4; f < 6; f++) {
            animation_set_frame(&play.player.anim, f);
            stage_draw(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f, options);
            snprintf(name, sizeof(name), "30_disparo_linterna_%d_%d", turn, f);
            save_capture(r, dir, name);
        }
    }
    /* The sheriff's rework and cylinder reload, through the real stage/render path. */
    {
        Progress kept = profiles[0].progress;
        profiles[0].progress.level = 1;
        stage_start(&play, 0, &CHARACTERS[0], &profiles[0].progress);
        play.run.zombie_count = 0;
        play.flashlight = false;
        weather_start(&play.weather, WEATHER_CLEAR, camera_left(play.player.x));
        stage_draw(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f, options);
        save_capture(r, dir, "52_sheriff_rework");
        InputState click = {0};
        click.pressed[ACTION_SHOOT] = true;
        stage_step(&play, &click, &profiles[0], options);
        for (int i = 0; i < 60 && !play.player.shot.fired; i++)
            idle_steps(&play, &profiles[0], &input, 1, options);
        stage_draw(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f, options);
        save_capture(r, dir, "52_sheriff_disparo");
        click = (InputState){0};
        click.pressed[ACTION_RELOAD] = true;
        stage_step(&play, &click, &profiles[0], options);
        for (int f = 0; f < PLAYER_RELOAD_FRAMES; f++) {
            char name[64];
            stage_draw(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f, options);
            snprintf(name, sizeof(name), "52_sheriff_recarga_%d", f);
            save_capture(r, dir, name);
            idle_steps(&play, &profiles[0], &input, 9, options);
        }
        profiles[0].progress = kept;
    }
    /* The new mission HUD and results use the same rules as real play. */
    stage_start(&play, 2, &CHARACTERS[0], &profiles[0].progress);
    play.run.mission.ticks = 187 * SIMULATION_HZ;
    hud_set_pointer(WINDOW_WIDTH / 2, 30); /* Over the mission plate */
    stage_draw(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f, options);
    save_capture(r, dir, "36_reloj_y_metas");
    hud_set_pointer(-1, -1);
    play.run.phase = RUN_CLEARED;
    stage_record_init(&profiles[0].record);
    mission_finish(&play.run.mission, &profiles[0].record, play.run.stage_index,
                      play.player.health, play.player.max_health);
    stage_draw(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f, options);
    save_capture(r, dir, "37_estrellas_y_recompensas");

    /* An ambush just sprung: its arrows, at the edge the zombies come from. */
    stage_start(&play, 0, &CHARACTERS[0], &profiles[0].progress);
    for (int k = 0; k < play.run.zombie_count; k++) {
        if (play.run.ambush_x[k] > 0.0f) {
            play.player.x = play.run.ambush_x[k] + 1.0f;
            break;
        }
    }
    idle_steps(&play, &profiles[0], &input, 2, options);
    stage_draw(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f, options);
    save_capture(r, dir, "38_emboscada_flechas");

    /* The last blow at a trap: her strike still plays, on the ropes. */
    stage_start(&play, 1, &CHARACTERS[0], &profiles[0].progress);
    player_catch(&play.player, CATCH_NET, play.player.x, BASELINE - 200.0f);
    while (!player_struggle(&play.player)) {
    }
    for (int i = 0; i < 12; i++)
        player_update(&play.player, &input, FIXED_DT);
    stage_draw(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f, options);
    save_capture(r, dir, "39_ultimo_golpe_trampa");

    /* All ten stages at the same human scale, with objects on either side.
     * Keep this fixture independent of progression and the random encounters. */
    for (int stage = 0; stage < STAGE_COUNT; stage++) {
        stage_start(&play, stage, &CHARACTERS[0], &profiles[0].progress);
        terrain_clear(&play.run.terrain);
        play.run.zombie_count = 0;
        play.player.x += 6000.0f;
        play.flashlight = false;
        const ThemeDef *theme = STAGES[stage].theme;
        Piece *bench = terrain_add(&play.run.terrain, TERRAIN_BENCH, play.player.x - 440.0f);
        if (bench)
            bench->variant = theme->city ? 1 : 0;
        Piece *fire = terrain_add(&play.run.terrain, TERRAIN_CAMPFIRE, play.player.x - 240.0f);
        if (fire)
            fire->variant = theme->city ? 1 : 0;
        terrain_add(&play.run.terrain, TERRAIN_BARREL, play.player.x + 300.0f);
        Piece *barrier = terrain_add(&play.run.terrain, TERRAIN_BARRICADE, play.player.x + 660.0f);
        if (barrier)
            barrier->variant = theme->barricade_count > 0
                                   ? theme->barricades[stage % theme->barricade_count]
                                   : stage % BARRICADE_KINDS_WEST;
        weather_start(&play.weather, WEATHER_CLEAR, camera_left(play.player.x));
        stage_draw(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f, options);
        char name[64];
        snprintf(name, sizeof(name), "50_escenario_%s", STAGES[stage].name);
        save_capture(r, dir, name);
    }

    /* The post's lens, its real cone on the road, and the handheld beam
     * together: no painted rays in the sprite and no shared-mask mix-up. */
    stage_start(&play, STAGE_COUNT - 1, &CHARACTERS[0], &profiles[0].progress);
    terrain_clear(&play.run.terrain);
    play.run.zombie_count = 0;
    play.player.x += 6000.0f;
    terrain_add(&play.run.terrain, TERRAIN_CRATE, play.player.x - 350.0f);
    Piece *post = terrain_add(&play.run.terrain, TERRAIN_OUTPOST, play.player.x + 250.0f);
    weather_start(&play.weather, WEATHER_CLEAR, camera_left(play.player.x));
    if (post) {
        play.flashlight = false;
        stage_draw(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f, options);
        save_capture(r, dir, "51_outpost_apagado");
        post->spent = true;
        stage_draw(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f, options);
        save_capture(r, dir, "51_outpost_encendido");
        play.flashlight = true;
        play.flashlight_since = 10.0f;
        stage_draw(platform, &play, &skins[0], &profiles[0].progress, 1.0f, play.player.x, 0.0f, options);
        save_capture(r, dir, "51_outpost_y_linterna");
    }
}
