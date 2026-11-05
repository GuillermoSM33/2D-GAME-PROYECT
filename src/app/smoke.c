#include <stdio.h>
#include <string.h>

#include "app/smoke.h"
#include "config.h"

/* Scripted input for --smoke-test: walk right, jump while walking right,
 * walk left, stop, then shoot once standing and let the bullet leave.
 * Meanwhile the zombie limps in from the right. */
#define SMOKE_RIGHT_START 0.15f
#define SMOKE_JUMP_AT 1.30f
#define SMOKE_LEFT_START 2.25f
#define SMOKE_STOP 2.60f
#define SMOKE_SHOOT_AT 2.70f
#define SMOKE_END 3.70f

void smoke_override(const SmokeTest *smoke, bool down[ACTION_COUNT])
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

void smoke_observe(SmokeTest *smoke, const Player *player, const Bullets *bullets,
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
