/* Vaquera 2D - walking demo in C + SDL2.
 *
 * The animation comes exclusively from the eight approved frames, embedded
 * in the executable at build time (see tools/embed_assets.py).
 */
#include <stdio.h>
#include <string.h>

#include "config.h"
#include "engine/assets.h"
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

/* Scripted input for --smoke-test: walk right, jump while walking right,
 * walk left, stop, then shoot once standing and let the bullet leave.
 * Meanwhile the zombie limps in from the right. */
#define SMOKE_RIGHT_START 0.15f
#define SMOKE_JUMP_AT 1.30f
#define SMOKE_LEFT_START 2.25f
#define SMOKE_STOP 2.60f
#define SMOKE_SHOOT_AT 2.70f
#define SMOKE_END 3.70f

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

    int failures = 0;
    for (int i = 0; i < anim_count; i++)
        failures += !verify_sheet(anims[i]);
    const char *fonts[] = {"fonts/DejaVuSansMono", "fonts/DejaVuSansMono-Bold"};
    for (size_t i = 0; i < sizeof(fonts) / sizeof(fonts[0]); i++) {
        if (assets_find_blob(fonts[i]) == NULL) {
            fprintf(stderr, "FALTA: %s\n", fonts[i]);
            failures++;
        }
    }
    if (failures)
        return 1;
    printf("OK: %d imagen(es) y %d fuente(s) incrustadas.\n",
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
                     zombie->health == zombie->stats->health;
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

static void set_window_icon(SDL_Window *window)
{
    SDL_Surface *icon = assets_surface_region("sprites/player/walk", 0, 0,
                                              PLAYER_WALK_FRAME_W, PLAYER_WALK_FRAME_H);
    if (icon) {
        SDL_SetWindowIcon(window, icon);
        SDL_FreeSurface(icon);
    }
}

static int run_game(bool smoke_mode)
{
    Platform platform;
    if (!platform_init(&platform, WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT))
        return 1;

    int status = 1;
    bool text_ready = false;
    if (!assets_load(platform.renderer))
        goto cleanup;
    if (!(text_ready = text_system_init()) || !hud_init(platform.renderer))
        goto cleanup;
    set_window_icon(platform.window);
    platform_set_bindings(&platform, CONTROLS, CONTROLS_COUNT);

    InputState input;
    Player player;
    Bullets bullets;
    Zombie zombie;
    Effects effects;
    SmokeTest smoke = {.enabled = smoke_mode};
    input_init(&input);
    player_init(&player);
    bullets_clear(&bullets);
    effects_clear(&effects);
    zombie_spawn(&zombie, &ZOMBIE_RIOT, WINDOW_WIDTH - ZOMBIE_SPAWN_MARGIN);
    const float damage = weapon_damage(WEAPON_LEVEL);

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
        accumulator += frame_time;

        while (accumulator >= FIXED_DT && running) {
            bool down[ACTION_COUNT];
            if (smoke.enabled)
                smoke_override(&smoke, down);
            else
                platform_read_actions(&platform, down);
            input_update(&input, down);
            if (input.pressed[ACTION_QUIT])
                running = false;

            if (input.pressed[ACTION_RESET]) {
                bullets_clear(&bullets);
                effects_clear(&effects);
                zombie_spawn(&zombie, &ZOMBIE_RIOT, WINDOW_WIDTH - ZOMBIE_SPAWN_MARGIN);
            }
            player_update(&player, &input, FIXED_DT);
            bullets_update(&bullets, FIXED_DT);
            if (player.shot_fired) {
                float mx, my;
                player_muzzle(&player, &mx, &my);
                bullets_spawn(&bullets, player.x, mx, my, player.facing);
            }
            zombie_update(&zombie, player.x, player_alive(&player), FIXED_DT);
            effects_update(&effects, FIXED_DT);
            combat_bullets_vs_zombie(&bullets, &zombie, damage, &effects);
            combat_zombie_vs_player(&zombie, &player);
            if (smoke.enabled) {
                smoke_observe(&smoke, &player, &bullets, &zombie);
                if (smoke.done)
                    running = false;
            }
            accumulator -= FIXED_DT;
        }

        scene_draw(platform.renderer);
        /* The claw trail reaches past her, so a swiping zombie goes in front. */
        bool zombie_in_front = zombie.state == ZOMBIE_ATTACK;
        if (!zombie_in_front)
            zombie_render(platform.renderer, &zombie);
        player_render(platform.renderer, &player);
        if (zombie_in_front)
            zombie_render(platform.renderer, &zombie);
        bullets_render(platform.renderer, &bullets);
        effects_render(platform.renderer, &effects);
        hud_draw(platform.renderer, &player);
        SDL_RenderPresent(platform.renderer);
        if (!platform.vsync)
            SDL_Delay(1);
    }
    status = (smoke.enabled && !smoke.passed) ? 1 : 0;

cleanup:
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
