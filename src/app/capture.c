#include <limits.h>
#include <stdio.h>

#include "app/capture.h"
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
    hud_draw_title(r, &list);
    save_capture(r, dir, "1_titulo");
    stage_draw_backdrop(platform, menu_world, 0.5f);
    hud_draw_controls(r);
    save_capture(r, dir, "2_controles");
    list_menu_init(&options->volume_menu, VOLUME_ROWS);
    stage_draw_backdrop(platform, menu_world, 0.5f);
    hud_draw_volume(r, &options->volume_menu, &options->volumes);
    save_capture(r, dir, "3_volumen");
    stage_draw_backdrop(platform, menu_world, 0.45f);
    hud_draw_characters(r, skins, progress, 1);
    save_capture(r, dir, "4_personajes");
    profiles[1].record.cleared[0] = true;
    stage_draw_backdrop(platform, menu_world, 0.45f);
    hud_draw_menu(r, CHARACTERS[1].name, &profiles[1].progress, &profiles[1].record, 1);
    save_capture(r, dir, "5_niveles");
    hud_draw_autosave_notice(r);
    save_capture(r, dir, "33_aviso_autoguardado");
    profiles[1].record.cleared[0] = false;

    /* The SWAT in 1-1, the first zombie woken and coming. */
    stage_start(&play, 0, &CHARACTERS[1], &profiles[1].progress);
    play.player.x = play.run.zombies[0].x - ROUTE_WAKE_DISTANCE + 20.0f;
    idle_steps(&play, &profiles[1], &input, 150, options);
    stage_draw(platform, &play, &skins[1], &profiles[1].progress, 1.0f, play.player.x,
               play.player.jump.height, options);
    save_capture(r, dir, "6_pelea");
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
}
