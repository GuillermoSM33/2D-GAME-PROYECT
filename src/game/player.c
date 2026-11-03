#include "game/player.h"

#include <math.h>
#include <string.h>

#include "config.h"
#include "game/damage.h"
#include "game/movement.h"

/* The cowgirl's sheets define the template every character follows (frame
 * sizes, pivots, muzzle): the renderer swaps in each character's own sheets
 * by file name (character_skin.c). */
#define PLAYER_WALK_SHEET "sprites/characters/cowgirl/walk"
#define PLAYER_JUMP_SHEET "sprites/characters/cowgirl/jump"
#define PLAYER_SHOOT_SHEET "sprites/characters/cowgirl/shoot"
/* Only guns with a magazine have one (WeaponDef.reload_sheet), so the
 * template names it but the cowgirl has none: the renderer finds the gun's. */
#define PLAYER_RELOAD_SHEET "sprites/characters/cowgirl/reload"
#define PLAYER_SIT_SHEET "sprites/characters/cowgirl/sit"
/* Only characters with grenades have one: the renderer finds theirs. */
#define PLAYER_THROW_SHEET "sprites/characters/cowgirl/throw"
#define PLAYER_MELEE_SHEET "sprites/characters/cowgirl/melee"
#define PLAYER_FAINT_SHEET "sprites/characters/cowgirl/faint"
#define PLAYER_DRINK_SHEET "sprites/characters/cowgirl/drink"
#define PLAYER_BANDAGE_SHEET "sprites/characters/cowgirl/bandage"

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

/* Frames follow the magazine reload's progress (shoot.c). */
static const AnimationDef ANIM_RELOAD = {
    .sheet = PLAYER_RELOAD_SHEET, .frame_w = PLAYER_SHOOT_FRAME_W, .frame_h = PLAYER_SHOOT_FRAME_H,
    .first_frame = 0, .frame_count = PLAYER_RELOAD_FRAMES, .fps = 0.0f, .loop = false,
    .anchor_x = SHOOT_ANCHOR_X, .ground_y = SHOOT_GROUND_Y,
};

/* Frames picked by the time sat (player_update): the walk's pivot and ground. */
static const AnimationDef ANIM_SIT = {
    .sheet = PLAYER_SIT_SHEET, .frame_w = PLAYER_SIT_FRAME_W, .frame_h = PLAYER_WALK_FRAME_H,
    .first_frame = 0, .frame_count = PLAYER_SIT_FRAMES, .fps = 0.0f, .loop = false,
    .anchor_x = PLAYER_SIT_ANCHOR_X, .ground_y = WALK_GROUND_Y,
};

/* The grenade throw, on the shoot template. */
/* Out cold from the heat: the walk template's height, wide enough to lie in. */
static const AnimationDef ANIM_FAINT = {
    .sheet = PLAYER_FAINT_SHEET, .frame_w = PLAYER_FAINT_FRAME_W, .frame_h = PLAYER_WALK_FRAME_H,
    .first_frame = 0, .frame_count = PLAYER_FAINT_FRAMES, .fps = PLAYER_FAINT_FPS, .loop = false,
    .anchor_x = 40.0f, .ground_y = WALK_GROUND_Y,
};

/* Drinking and binding a wound: frames picked by how far along (player_care_animation). */
static const AnimationDef ANIM_DRINK = {
    .sheet = PLAYER_DRINK_SHEET, .frame_w = PLAYER_SHOOT_FRAME_W, .frame_h = PLAYER_SHOOT_FRAME_H,
    .first_frame = 0, .frame_count = PLAYER_CARE_FRAMES, .fps = 0.0f, .loop = false,
    .anchor_x = SHOOT_ANCHOR_X, .ground_y = SHOOT_GROUND_Y,
};
static const AnimationDef ANIM_BANDAGE = {
    .sheet = PLAYER_BANDAGE_SHEET, .frame_w = PLAYER_SHOOT_FRAME_W, .frame_h = PLAYER_SHOOT_FRAME_H,
    .first_frame = 0, .frame_count = PLAYER_CARE_FRAMES, .fps = 0.0f, .loop = false,
    .anchor_x = SHOOT_ANCHOR_X, .ground_y = SHOOT_GROUND_Y,
};

static const AnimationDef ANIM_MELEE = {
    .sheet = PLAYER_MELEE_SHEET, .frame_w = PLAYER_SHOOT_FRAME_W, .frame_h = PLAYER_SHOOT_FRAME_H,
    .first_frame = 0, .frame_count = PLAYER_MELEE_FRAMES, .fps = PLAYER_MELEE_FPS, .loop = false,
    .anchor_x = SHOOT_ANCHOR_X, .ground_y = SHOOT_GROUND_Y,
};

static const AnimationDef ANIM_THROW = {
    .sheet = PLAYER_THROW_SHEET, .frame_w = PLAYER_SHOOT_FRAME_W, .frame_h = PLAYER_SHOOT_FRAME_H,
    .first_frame = 0, .frame_count = PLAYER_THROW_FRAMES, .fps = PLAYER_THROW_FPS, .loop = false,
    .anchor_x = SHOOT_ANCHOR_X, .ground_y = SHOOT_GROUND_Y,
};

/* The sheets every character has (ANIM_RELOAD's belongs to some guns only). */
static const AnimationDef *const ANIMATIONS[] = {
    &ANIM_IDLE, &ANIM_WALK, &ANIM_JUMP_AIR, &ANIM_LAND, &ANIM_SHOOT, &ANIM_SIT,
};

static bool lose_blood(Player *player);

void player_init(Player *player)
{
    memset(player, 0, sizeof(*player));
    player->x = PLAYER_START_X;
    player->facing = FACING_RIGHT;
    player->state = PLAYER_IDLE;
    player->level = 1;
    player->max_health = player->health = PLAYER_HEALTH;
    player->armor = PLAYER_ARMOR;
    player->sit_gun = player->sit_reloaded_gun = -1;
    player->min_x = movement_min_x();
    player->max_x = movement_max_x();
    jump_reset(&player->jump);
    shot_reset(&player->shot);
    animation_play(&player->anim, &ANIM_IDLE);
}

void player_set_stats(Player *player, int level, int max_health, float armor, bool heal)
{
    player->level = level;
    player->max_health = max_health;
    player->armor = armor;
    if (heal || player->health > max_health)
        player->health = max_health;
}

void player_set_ground(Player *player, float floor, float min_x, float max_x)
{
    player->floor = floor;
    player->min_x = fmaxf(min_x, movement_min_x());
    player->max_x = fminf(max_x, movement_max_x());
}

static void keep_in_bounds(Player *player)
{
    player->x = fminf(player->max_x, fmaxf(player->min_x, player->x));
}

/* The lowest slot still to reload, or -1. */
static int next_sit_gun(unsigned guns)
{
    for (int slot = 0; slot < 32; slot++) {
        if (guns & (1u << slot))
            return slot;
    }
    return -1;
}

bool player_sit(Player *player, float bench_x, unsigned reload_guns)
{
    if (!player_alive(player) || player->shot.active || player->jump.airborne ||
        player->state == PLAYER_SIT)
        return false;
    player->x = bench_x;
    player->state = PLAYER_SIT;
    player->sit_time = 0.0f;
    player->sit_guns = reload_guns;
    player->sit_gun = next_sit_gun(reload_guns);
    player->sit_gun_time = 0.0f;
    animation_play(&player->anim, &ANIM_SIT);
    animation_set_frame(&player->anim, 0);
    return true;
}

/* Sat: getting down, a reload per gun that needs one, then breathing; after
 * a while, dozing. */
static void update_sit(Player *player, float dt)
{
    player->sit_time += dt;
    int frame;
    if (player->sit_time < SIT_DOWN_TIME) {
        frame = 0;
    } else if (player->sit_gun >= 0) {
        player->sit_gun_time += dt;
        if (player->sit_gun_time >= SIT_RELOAD_TIME) { /* Full: the next one, if any */
            player->sit_reloaded = true;
            player->sit_reloaded_gun = player->sit_gun;
            player->sit_guns &= ~(1u << player->sit_gun);
            player->sit_gun = next_sit_gun(player->sit_guns);
            player->sit_gun_time = 0.0f;
            player->sit_time = SIT_DOWN_TIME; /* Her rest starts after the last one */
        }
        frame = 4 + (int)(player->sit_gun_time / SIT_RELOAD_TIME * 6.0f);
        if (player->sit_gun < 0)
            frame = 1;
    } else {
        float rest = player->sit_time - SIT_DOWN_TIME;
        static const int BREATH[] = {1, 2, 1, 3};
        static const int DOZE[] = {10, 11, 12, 13, 13, 12, 11};
        if (rest < SIT_DOZE_TIME)
            frame = BREATH[(int)(rest * SIT_BREATH_FPS) % 4];
        else
            frame = DOZE[(int)((rest - SIT_DOZE_TIME) * SIT_DOZE_FPS) % 7];
    }
    animation_set_frame(&player->anim, frame < PLAYER_SIT_FRAMES ? frame : PLAYER_SIT_FRAMES - 1);
}

bool player_throw(Player *player)
{
    if (!player_alive(player) || player->shot.active || player->jump.airborne ||
        player->state == PLAYER_THROW || player->state == PLAYER_SIT)
        return false;
    player->state = PLAYER_THROW;
    player->thrown = false;
    animation_play(&player->anim, &ANIM_THROW);
    return true;
}

bool player_melee(Player *player)
{
    if (!player_alive(player) || player->shot.active || player->jump.airborne || player->melee_wait > 0.0f ||
        player->state == PLAYER_THROW || player->state == PLAYER_MELEE || player->state == PLAYER_SIT ||
        player->state == PLAYER_CAUGHT)
        return false;
    player->state = PLAYER_MELEE;
    player->landed = false;
    animation_play(&player->anim, &ANIM_MELEE);
    return true;
}

bool player_catch(Player *player, CatchKind kind, float anchor_x, float anchor_y)
{
    if (!player_alive(player) || player->state == PLAYER_CAUGHT || kind == CATCH_NONE)
        return false;
    shot_cancel(&player->shot);
    jump_reset(&player->jump);
    player->state = PLAYER_CAUGHT;
    player->sit_guns = 0;
    player->sit_gun = -1;
    player->catch_kind = kind;
    player->catch_blows = kind == CATCH_NET ? NET_BLOWS : SNARE_BLOWS;
    player->catch_time = player->catch_shake = 0.0f;
    player->catch_anchor_x = anchor_x;
    player->catch_anchor_y = anchor_y;
    animation_play(&player->anim, &ANIM_WALK); /* Kicking her legs while she hangs */
    return true;
}

bool player_struggle(Player *player)
{
    if (player->state != PLAYER_CAUGHT || !player_alive(player))
        return false;
    player->catch_shake = CATCH_SHAKE_TIME;
    if (--player->catch_blows > 0)
        return false;
    /* Cut free: down she drops from where she hung. */
    player->state = PLAYER_JUMP;
    player->jump.height = player->catch_kind == CATCH_NET ? NET_LIFT : SNARE_LIFT;
    jump_fall(&player->jump);
    player->catch_kind = CATCH_NONE;
    animation_play(&player->anim, &ANIM_IDLE);
    return true;
}

int player_thirst_level(const Player *player)
{
    return player->thirst >= HALLUCINATING ? 3 : player->thirst >= DEHYDRATED ? 2 : player->thirst >= THIRSTY ? 1 : 0;
}

float player_dry_time(const Player *player)
{
    if (player->cozy)
        return DRY_FIRE;
    return player->hot ? DRY_HOT : player->cold ? DRY_COLD : DRY_MILD;
}

const AnimationDef *player_care_animation(const Player *player, int *frame)
{
    int last = PLAYER_CARE_FRAMES - 1;
    if (player->drink_time > 0.0f) {
        int f = (int)((1.0f - player->drink_time / DRINK_TIME) * (float)PLAYER_CARE_FRAMES);
        *frame = f < 0 ? 0 : f > last ? last : f;
        return &ANIM_DRINK;
    }
    if (player->bandage > 0.0f) { /* Round and round, a turn more each time */
        *frame = (int)(player->bandage / BANDAGE_TIME * (float)last) % last;
        return &ANIM_BANDAGE;
    }
    if (player->bandage_shown > BANDAGE_SHOW - 0.4f) { /* Done: tucking the end in */
        *frame = last;
        return &ANIM_BANDAGE;
    }
    return NULL;
}

const AnimationDef *player_melee_animation(void)
{
    return &ANIM_MELEE;
}

bool player_vault(Player *player)
{
    if (!player_alive(player) || player->shot.active || !jump_start(&player->jump))
        return false;
    player->vaulting = true;
    player->state = PLAYER_JUMP;
    animation_play(&player->anim, &ANIM_JUMP_AIR);
    return true;
}

void player_update(Player *player, const InputState *input, float dt)
{
    player->shot_fired = false;
    player->threw = false;
    player->struck = false;
    player->reload_walk = false;
    player->sit_reloaded = false;
    player->sit_reloaded_gun = -1;
    if (player->hurt_time > 0.0f)
        player->hurt_time = fmaxf(0.0f, player->hurt_time - dt);
    player->melee_wait = fmaxf(0.0f, player->melee_wait - dt);
    player->refreshed = fmaxf(0.0f, player->refreshed - dt);
    player->drank = false;
    if (player->heal_time > 0.0f)
        player->heal_time = fmaxf(0.0f, player->heal_time - dt);
    if (player->slow_time > 0.0f)
        player->slow_time = fmaxf(0.0f, player->slow_time - dt);
    if (player->bleed_time > 0.0f && player->state != PLAYER_DEAD) {
        player->bleed_time = fmaxf(0.0f, player->bleed_time - dt);
        player->bleed_tick -= dt;
        if (player->bleed_tick <= 0.0f) {
            player->bleed_tick += BLEED_TICK;
            lose_blood(player);
        }
    }
    /* The push applies on top of whatever she is doing, shooting included. */
    if (player->knockback_time > 0.0f) {
        float push = fminf(dt, player->knockback_time);
        player->knockback_time -= push;
        player->x += (float)player->knockback_dir * PLAYER_KNOCKBACK_SPEED * push;
        keep_in_bounds(player);
    }
    /* Off an edge, or what she stood on is gone: down she goes. */
    if (!player->jump.airborne && player->jump.height > player->floor + 0.5f) {
        jump_fall(&player->jump);
        shot_cancel(&player->shot);
        if (player->state != PLAYER_DEAD) {
            player->state = PLAYER_JUMP;
            animation_play(&player->anim, &ANIM_JUMP_AIR);
        }
    }

    /* No death sheet yet: she keeps the standing frame and only falls back
     * to the ground if she was in the air. */
    if (player->state == PLAYER_DEAD) {
        if (player->jump.airborne)
            jump_update_over(&player->jump, dt, player->floor);
        if (player->fainted)
            animation_update(&player->anim, dt);
        return;
    }

    int dir = input_horizontal(input);
    bool run = input->down[ACTION_RUN];
    float pace = player->slow_time > 0.0f ? SLOW_MULT : 1.0f; /* Limping after a trap */
    player->wind_feel = player->current_feel = 0;
    if (player->cold)
        pace *= COLD_PACE;
    /* Thirst: none while hydrated (a little quicker then), faster in the heat. */
    if (player->refreshed > 0.0f)
        pace *= HYDRATED_PACE;
    else if (player_alive(player))
        player->thirst += dt * (player->hot ? THIRST_HOT : player->cold ? THIRST_COLD : THIRST_MILD);
    if (player_thirst_level(player) >= 2)
        pace *= DEHYDRATED_PACE;
    /* By a fire in the heat: wearing out, then slower, then out cold. */
    if (player->hot && player->refreshed <= 0.0f && player->cozy && player_alive(player))
        player->fatigue += dt;
    else
        player->fatigue = fmaxf(0.0f, player->fatigue - dt * FATIGUE_EASE);
    bool weary = player->fatigue >= FATIGUE_SLOW;
    if (weary)
        pace *= FATIGUE_PACE;
    if (player->fatigue >= FATIGUE_FAINT && player_alive(player)) {
        player->fainted = true;
        player->health = 0;
        player->state = PLAYER_DEAD;
        shot_cancel(&player->shot);
        animation_play(&player->anim, &ANIM_FAINT); /* She sways, buckles and goes down */
        return;
    }
    if (player->wading) /* Out of the river she dries, slower in the cold, fast by a fire */
        player->wet = 1.0f;
    else
        player->wet = fmaxf(0.0f, player->wet - dt / player_dry_time(player));
    if (dir != 0 && player->wind != 0) { /* At her back or in her face */
        player->wind_feel = dir == player->wind ? 1 : -1;
        pace *= player->wind_feel > 0 ? WIND_WITH : WIND_AGAINST;
    }
    if (player->wading && !player->jump.airborne) { /* Wading a river, which flows right */
        pace *= RIVER_SLOW;
        if (dir != 0) {
            player->current_feel = dir > 0 ? 1 : -1;
            pace *= dir > 0 ? RIVER_WITH : RIVER_AGAINST;
        }
    }
    /* U held on the ground: binding the wound, walking slower meanwhile. */
    player->bandaged = false;
    player->bandage_shown = fmaxf(0.0f, player->bandage_shown - dt);
    bool binding = player->bleed_time > 0.0f && input->down[ACTION_BANDAGE] && !player->jump.airborne &&
                   player->state != PLAYER_CAUGHT && player_alive(player);
    player->bandage = binding ? player->bandage + dt : 0.0f;
    if (binding)
        pace *= BANDAGE_WALK;
    /* U not bleeding: a drink of water, if she has a jug (slow walking meanwhile). */
    if (player->bleed_time <= 0.0f && input->pressed[ACTION_BANDAGE] && player->water > 0 &&
        player->drink_time <= 0.0f && !player->jump.airborne && player->state != PLAYER_CAUGHT &&
        player->state != PLAYER_SIT && player_alive(player))
        player->drink_time = DRINK_TIME;
    if (player->drink_time > 0.0f) {
        pace *= DRINK_PACE;
        player->drink_time -= dt;
        if (player->drink_time <= 0.0f) {
            player->drink_time = 0.0f;
            player->water--;
            player->refreshed = REFRESH_TIME;
            player->fatigue = 0.0f;
            player->thirst = 0.0f;
            player->drank = true;
        }
    }
    if (player->bandage >= BANDAGE_TIME) {
        player->bleed_time = 0.0f;
        player->bandage = 0.0f;
        player->bandaged = true;
        player->bandage_shown = BANDAGE_SHOW;
    }

    /* Hanging in a trap: nothing but blows at the ropes (player_struggle). */
    if (player->state == PLAYER_CAUGHT) {
        player->catch_time += dt;
        player->catch_shake = fmaxf(0.0f, player->catch_shake - dt);
        animation_update(&player->anim, dt * 0.7f);
        return;
    }

    /* A blow: planted until the gun comes back; it lands once. */
    if (player->state == PLAYER_MELEE) {
        animation_update(&player->anim, player->fatigue >= FATIGUE_SLOW ? dt * FATIGUE_PACE : dt);
        if (!player->landed && player->anim.frame >= PLAYER_MELEE_HIT_FRAME) {
            player->landed = true;
            player->struck = true;
        }
        if (!player->anim.finished)
            return;
        player->state = PLAYER_IDLE;
        player->melee_wait = MELEE_COOLDOWN * (player->hot && player->refreshed <= 0.0f ? HEAT_MELEE_MULT : 1.0f) *
                             (player->cold ? COLD_MELEE_MULT : 1.0f) /
                             (player->fatigue >= FATIGUE_SLOW ? FATIGUE_PACE : 1.0f);
        animation_play(&player->anim, &ANIM_IDLE);
    }

    /* Throwing: planted until the arm comes back; the grenade leaves once. */
    if (player->state == PLAYER_THROW) {
        animation_update(&player->anim, dt);
        if (!player->thrown && player->anim.frame >= PLAYER_THROW_RELEASE_FRAME) {
            player->thrown = true;
            player->threw = true;
        }
        if (!player->anim.finished)
            return;
        player->state = PLAYER_IDLE;
        animation_play(&player->anim, &ANIM_IDLE);
    }

    /* On a bench until she moves, jumps or shoots (that same input then
     * plays out as usual). */
    if (player->state == PLAYER_SIT) {
        /* A way pressed now: one still held from walking up doesn't count. */
        bool up = input->pressed[ACTION_LEFT] || input->pressed[ACTION_RIGHT] ||
                  input->pressed[ACTION_JUMP] || input->pressed[ACTION_SHOOT] || input->pressed[ACTION_VAULT];
        if (!up) {
            update_sit(player, dt);
            return;
        }
        player->state = PLAYER_IDLE;
        player->sit_guns = 0;
        player->sit_gun = -1;
        animation_play(&player->anim, &ANIM_IDLE);
    }

    /* Shooting is done standing on the ground, toward the held direction if
     * any. Jumping cancels it; everything else waits until it ends. An
     * automatic gun keeps firing while the trigger is held. */
    if (input->pressed[ACTION_RELOAD] && !player->jump.airborne && shot_reload_now(&player->shot)) {
        player->state = PLAYER_SHOOT;
        animation_play(&player->anim, &ANIM_RELOAD);
    }
    bool trigger = input->pressed[ACTION_SHOOT] || (player->shot.automatic && input->down[ACTION_SHOOT]);
    if (trigger && !player->jump.airborne && shot_start(&player->shot)) {
        if (dir != 0)
            player->facing = dir > 0 ? FACING_RIGHT : FACING_LEFT;
        player->state = PLAYER_SHOOT;
        animation_play(&player->anim, &ANIM_SHOOT);
    }
    if (player->shot.active && input->pressed[ACTION_JUMP])
        shot_cancel(&player->shot);
    if (player->shot.active) {
        player->shot_fired = shot_update(&player->shot, weary ? dt * FATIGUE_PACE : dt);
        if (shot_reloading(&player->shot)) {
            /* A magazine going in: she can walk while it does, slowly (no
             * running). Standing still shows the reload itself. */
            int frame = (int)(shot_reload_progress(&player->shot) * PLAYER_RELOAD_FRAMES);
            animation_play(&player->anim, &ANIM_RELOAD);
            animation_set_frame(&player->anim, frame < PLAYER_RELOAD_FRAMES ? frame : PLAYER_RELOAD_FRAMES - 1);
            if (dir != 0) { /* Her legs walk under the reload (player_render puts them together) */
                player->facing = dir > 0 ? FACING_RIGHT : FACING_LEFT;
                player->x = movement_step(player->x, dir, false, dt * PLAYER_RELOAD_WALK_MULT * pace);
                keep_in_bounds(player);
                player->state = PLAYER_WALK;
                player->reload_walk = true;
                animation_play(&player->legs, &ANIM_WALK);
                animation_update(&player->legs, dt * PLAYER_RELOAD_WALK_MULT);
                return;
            }
            player->state = PLAYER_SHOOT;
            animation_play(&player->anim, &ANIM_RELOAD);
            animation_set_frame(&player->anim, frame < PLAYER_RELOAD_FRAMES ? frame : PLAYER_RELOAD_FRAMES - 1);
            return;
        }
        if (player->shot.active) {
            animation_play(&player->anim, &ANIM_SHOOT);
            animation_set_frame(&player->anim, shot_frame(&player->shot));
            return;
        }
    }

    /* Horizontal control is the same on the ground and in the air, except
     * over a barricade: the leap carries her across. */
    if (player->vaulting && player->jump.airborne) {
        player->x += (float)player->facing * PLAYER_VAULT_SPEED * dt;
        keep_in_bounds(player);
    } else if (dir != 0) {
        player->facing = dir > 0 ? FACING_RIGHT : FACING_LEFT;
        player->x = movement_step(player->x, dir, run, dt * pace);
        keep_in_bounds(player);
    }

    /* Jumping is allowed from the ground, including during the landing. */
    if (input->pressed[ACTION_JUMP] && jump_start(&player->jump)) {
        player->state = PLAYER_JUMP;
        animation_play(&player->anim, &ANIM_JUMP_AIR);
    }

    if (player->jump.airborne) {
        if (!jump_update_over(&player->jump, dt, player->vaulting ? 0.0f : player->floor)) {
            animation_set_progress(&player->anim, jump_progress(&player->jump));
            return;
        }
        player->vaulting = false;
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
    animation_update(&player->anim, dt * pace * (run ? PLAYER_RUN_ANIM_MULT : 1.0f));
}

void player_bleed(Player *player, float damage)
{
    if (!player_alive(player))
        return;
    player->bleed_time = BLEED_TIME;
    player->bleed_tick = BLEED_TICK;
    player->bleed_damage = damage;
    player->slow_time = SLOW_TIME;
}

/* Loses health to bleeding (no armor, no push); true if it killed her. */
static bool lose_blood(Player *player)
{
    int loss = (int)ceilf(player->bleed_damage);
    player->health -= loss > 0 ? loss : 1;
    player->hurt_time = PLAYER_HURT_TIME;
    if (player->health > 0)
        return false;
    player->health = 0;
    player->state = PLAYER_DEAD;
    shot_cancel(&player->shot);
    animation_play(&player->anim, &ANIM_IDLE);
    return true;
}

bool player_hit(Player *player, float damage, int push_dir)
{
    if (!player_alive(player))
        return false;
    player->health -= damage_after_armor(damage, player->armor);
    player->hurt_time = PLAYER_HURT_TIME;
    player->knockback_time = PLAYER_KNOCKBACK_TIME;
    player->knockback_dir = push_dir < 0 ? -1 : 1;
    if (player->state == PLAYER_SIT) { /* A hit gets her up */
        player->state = PLAYER_IDLE;
        player->sit_guns = 0;
        player->sit_gun = -1;
        animation_play(&player->anim, &ANIM_IDLE);
    }
    if (player->health > 0)
        return false;
    player->health = 0;
    player->state = PLAYER_DEAD;
    shot_cancel(&player->shot);
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
    case PLAYER_SIT: return "sit";
    case PLAYER_THROW: return "throw";
    case PLAYER_MELEE: return "melee";
    case PLAYER_CAUGHT: return "caught";
    case PLAYER_DEAD: return "dead";
    }
    return "?";
}

void player_muzzle(const Player *player, float *x, float *y)
{
    *x = player->x + (float)player->facing * PLAYER_MUZZLE_DX * SPRITE_SCALE;
    *y = BASELINE - PLAYER_MUZZLE_DY * SPRITE_SCALE - player->jump.height;
}

bool player_reload_animation(const AnimationDef *def)
{
    return def == &ANIM_RELOAD;
}

const AnimationDef *const *player_animations(int *count)
{
    *count = (int)(sizeof(ANIMATIONS) / sizeof(ANIMATIONS[0]));
    return ANIMATIONS;
}
