#include "game/player.h"

#include <math.h>
#include <string.h>

#include "config.h"
#include "game/damage.h"
#include "game/movement.h"

#define PLAYER_WALK_SHEET "sprites/player/walk"
#define PLAYER_JUMP_SHEET "sprites/player/jump"
#define PLAYER_SHOOT_SHEET "sprites/player/shoot"

/* Pivots measured on the art: the body spans x 6..32 (walk), 12..38 (jump)
 * and 18..44 (shoot); the boots end on rows 59, 67 and 66, two rows above
 * where they meet the ground line. */
#define WALK_ANCHOR_X 19.5f
#define WALK_GROUND_Y 61
#define JUMP_ANCHOR_X 25.5f
#define JUMP_GROUND_Y 69
#define SHOOT_ANCHOR_X 31.5f
#define SHOOT_GROUND_Y 68

/* Standing still uses the neutral first walk frame; it does not animate. */
static const AnimationDef ANIM_IDLE = {
    .sheet = PLAYER_WALK_SHEET, .frame_w = PLAYER_WALK_FRAME_W, .frame_h = PLAYER_WALK_FRAME_H,
    .first_frame = 0, .frame_count = 1, .fps = 0.0f, .loop = true,
    .anchor_x = WALK_ANCHOR_X, .ground_y = WALK_GROUND_Y,
};
/* Walk and run share the same frames, so switching keeps the cycle going. */
static const AnimationDef ANIM_WALK = {
    .sheet = PLAYER_WALK_SHEET, .frame_w = PLAYER_WALK_FRAME_W, .frame_h = PLAYER_WALK_FRAME_H,
    .first_frame = 0, .frame_count = PLAYER_WALK_FRAMES, .fps = PLAYER_WALK_FPS, .loop = true,
    .anchor_x = WALK_ANCHOR_X, .ground_y = WALK_GROUND_Y,
};
/* Driven by jump progress rather than time, so it always matches the arc. */
static const AnimationDef ANIM_JUMP_AIR = {
    .sheet = PLAYER_JUMP_SHEET, .frame_w = PLAYER_JUMP_FRAME_W, .frame_h = PLAYER_JUMP_FRAME_H,
    .first_frame = 0, .frame_count = PLAYER_JUMP_AIR_FRAMES, .fps = 0.0f, .loop = false,
    .anchor_x = JUMP_ANCHOR_X, .ground_y = JUMP_GROUND_Y,
};
static const AnimationDef ANIM_LAND = {
    .sheet = PLAYER_JUMP_SHEET, .frame_w = PLAYER_JUMP_FRAME_W, .frame_h = PLAYER_JUMP_FRAME_H,
    .first_frame = PLAYER_JUMP_AIR_FRAMES,
    .frame_count = PLAYER_JUMP_FRAMES - PLAYER_JUMP_AIR_FRAMES,
    .fps = PLAYER_LAND_FPS, .loop = false,
    .anchor_x = JUMP_ANCHOR_X, .ground_y = JUMP_GROUND_Y,
};

/* Frames are picked by the shot sequence (shoot.c), not by time. */
static const AnimationDef ANIM_SHOOT = {
    .sheet = PLAYER_SHOOT_SHEET, .frame_w = PLAYER_SHOOT_FRAME_W, .frame_h = PLAYER_SHOOT_FRAME_H,
    .first_frame = 0, .frame_count = PLAYER_SHOOT_FRAMES, .fps = 0.0f, .loop = false,
    .anchor_x = SHOOT_ANCHOR_X, .ground_y = SHOOT_GROUND_Y,
};

static const AnimationDef *const ANIMATIONS[] = {
    &ANIM_IDLE, &ANIM_WALK, &ANIM_JUMP_AIR, &ANIM_LAND, &ANIM_SHOOT,
};

void player_init(Player *player)
{
    memset(player, 0, sizeof(*player));
    player->x = PLAYER_START_X;
    player->facing = FACING_RIGHT;
    player->state = PLAYER_IDLE;
    player->health = PLAYER_HEALTH;
    jump_reset(&player->jump);
    shot_reset(&player->shot);
    animation_play(&player->anim, &ANIM_IDLE);
}

void player_update(Player *player, const InputState *input, float dt)
{
    player->shot_fired = false;
    if (input->pressed[ACTION_RESET]) {
        player_init(player);
        return;
    }

    if (player->hurt_time > 0.0f)
        player->hurt_time = fmaxf(0.0f, player->hurt_time - dt);
    /* The push applies on top of whatever she is doing, shooting included. */
    if (player->knockback_time > 0.0f) {
        float push = fminf(dt, player->knockback_time);
        player->knockback_time -= push;
        player->x = fminf(movement_max_x(), fmaxf(movement_min_x(),
                          player->x + (float)player->knockback_dir * PLAYER_KNOCKBACK_SPEED * push));
    }

    /* No death sheet yet: she keeps the standing frame and only falls back
     * to the ground if she was in the air. */
    if (player->state == PLAYER_DEAD) {
        if (player->jump.airborne)
            jump_update(&player->jump, dt);
        return;
    }

    int dir = input_horizontal(input);
    bool run = input->down[ACTION_RUN];

    /* Shooting is done standing on the ground, toward the held direction if
     * any. Jumping cancels it; everything else waits until it ends. */
    if (input->pressed[ACTION_SHOOT] && !player->jump.airborne && shot_start(&player->shot)) {
        if (dir != 0)
            player->facing = dir > 0 ? FACING_RIGHT : FACING_LEFT;
        player->state = PLAYER_SHOOT;
        animation_play(&player->anim, &ANIM_SHOOT);
    }
    if (player->shot.active && input->pressed[ACTION_JUMP])
        shot_reset(&player->shot);
    if (player->shot.active) {
        player->shot_fired = shot_update(&player->shot, dt);
        if (player->shot.active) {
            animation_set_frame(&player->anim, shot_frame(&player->shot));
            return;
        }
    }

    /* Horizontal control is the same on the ground and in the air. */
    if (dir != 0) {
        player->facing = dir > 0 ? FACING_RIGHT : FACING_LEFT;
        player->x = movement_step(player->x, dir, run, dt);
    }

    /* Jumping is allowed from the ground, including during the landing. */
    if (input->pressed[ACTION_JUMP] && jump_start(&player->jump)) {
        player->state = PLAYER_JUMP;
        animation_play(&player->anim, &ANIM_JUMP_AIR);
    }

    if (player->jump.airborne) {
        if (!jump_update(&player->jump, dt)) {
            animation_set_progress(&player->anim, jump_progress(&player->jump));
            return;
        }
        player->state = PLAYER_LAND;
        animation_play(&player->anim, &ANIM_LAND);
        return;
    }

    if (player->state == PLAYER_LAND) {
        animation_update(&player->anim, dt);
        if (!player->anim.finished)
            return;
    }

    if (dir == 0) {
        player->state = PLAYER_IDLE;
        animation_play(&player->anim, &ANIM_IDLE);
        return;
    }
    /* Frame 0 is the standing pose, so a fresh start goes straight to the
     * first step; otherwise a short tap would slide her without moving a leg. */
    bool was_walking = player->state == PLAYER_WALK || player->state == PLAYER_RUN;
    player->state = run ? PLAYER_RUN : PLAYER_WALK;
    animation_play(&player->anim, &ANIM_WALK);
    if (!was_walking)
        animation_seek(&player->anim, 1);
    animation_update(&player->anim, dt * (run ? PLAYER_RUN_ANIM_MULT : 1.0f));
}

bool player_hit(Player *player, float damage, int push_dir)
{
    if (!player_alive(player))
        return false;
    player->health -= damage_after_armor(damage, PLAYER_ARMOR);
    player->hurt_time = PLAYER_HURT_TIME;
    player->knockback_time = PLAYER_KNOCKBACK_TIME;
    player->knockback_dir = push_dir < 0 ? -1 : 1;
    if (player->health > 0)
        return false;
    player->health = 0;
    player->state = PLAYER_DEAD;
    shot_reset(&player->shot);
    animation_play(&player->anim, &ANIM_IDLE);
    return true;
}

bool player_alive(const Player *player)
{
    return player->state != PLAYER_DEAD;
}

const char *player_state_name(PlayerState state)
{
    switch (state) {
    case PLAYER_IDLE: return "idle";
    case PLAYER_WALK: return "walk";
    case PLAYER_RUN: return "run";
    case PLAYER_JUMP: return "jump";
    case PLAYER_LAND: return "land";
    case PLAYER_SHOOT: return "shoot";
    case PLAYER_DEAD: return "dead";
    }
    return "?";
}

void player_muzzle(const Player *player, float *x, float *y)
{
    *x = player->x + (float)player->facing * PLAYER_MUZZLE_DX * SPRITE_SCALE;
    *y = BASELINE - PLAYER_MUZZLE_DY * SPRITE_SCALE - player->jump.height;
}

const AnimationDef *const *player_animations(int *count)
{
    *count = (int)(sizeof(ANIMATIONS) / sizeof(ANIMATIONS[0]));
    return ANIMATIONS;
}
