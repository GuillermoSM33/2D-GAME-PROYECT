#include "game/zombie.h"

#include <math.h>
#include <string.h>

#include "config.h"
#include "game/camera.h"
#include "game/damage.h"
#include "game/progression.h"

#define ZOMBIE_WALK_SHEET "sprites/zombie/walk"
#define ZOMBIE_HURT_SHEET "sprites/zombie/hurt"
#define ZOMBIE_DEATH_SHEET "sprites/zombie/death"
#define ZOMBIE_ATTACK_SHEET "sprites/zombie/attack"

/* Time from the killing hit until the body lies on the ground, starting
 * from frame 1 (see zombie_hit). */
#define DEATH_FALL_TIME ((ZOMBIE_DEATH_FRAMES - 1) / ZOMBIE_DEATH_FPS)
#define DEATH_FADE_START (DEATH_FALL_TIME + ZOMBIE_CORPSE_TIME)

/* Measured on the art: the helmet stays on x 23..48 and the torso on 8..51
 * (arm included), so 27.5 keeps the body steady between frames. */
static const AnimationDef ANIM_WALK = {
    .sheet = ZOMBIE_WALK_SHEET, .frame_w = ZOMBIE_FRAME_W, .frame_h = ZOMBIE_FRAME_H,
    .first_frame = 0, .frame_count = ZOMBIE_WALK_FRAMES, .fps = ZOMBIE_WALK_FPS, .loop = true,
    .anchor_x = 27.5f, .ground_y = 68,
};

/* Same template and pivot; frame 0 already leans back 2 px. */
static const AnimationDef ANIM_HURT = {
    .sheet = ZOMBIE_HURT_SHEET, .frame_w = ZOMBIE_FRAME_W, .frame_h = ZOMBIE_FRAME_H,
    .first_frame = 0, .frame_count = ZOMBIE_HURT_FRAMES, .fps = ZOMBIE_HURT_FPS, .loop = false,
    .anchor_x = 27.5f, .ground_y = 68,
};

/* Standing frames keep the pivot; lying on frame 7, it reaches x 71 in front. */
static const AnimationDef ANIM_DEATH = {
    .sheet = ZOMBIE_DEATH_SHEET, .frame_w = ZOMBIE_FRAME_W, .frame_h = ZOMBIE_FRAME_H,
    .first_frame = 0, .frame_count = ZOMBIE_DEATH_FRAMES, .fps = ZOMBIE_DEATH_FPS, .loop = false,
    .anchor_x = 27.5f, .ground_y = 68,
};

/* The legs never move, so the walk pivot fits; the claw trail reaches x 63. */
static const AnimationDef ANIM_ATTACK = {
    .sheet = ZOMBIE_ATTACK_SHEET, .frame_w = ZOMBIE_FRAME_W, .frame_h = ZOMBIE_FRAME_H,
    .first_frame = 0, .frame_count = ZOMBIE_ATTACK_FRAMES, .fps = ZOMBIE_ATTACK_FPS, .loop = false,
    .anchor_x = 27.5f, .ground_y = 68,
};

static const AnimationDef *const ANIMATIONS[] = {&ANIM_WALK, &ANIM_HURT, &ANIM_DEATH, &ANIM_ATTACK};

const ZombieStats ZOMBIE_COMMON = {
    .health = 100, .armor = 0.0f, .attack_base = ZOMBIE_ATTACK_BASE, .tint = 0xffffff,
};
const ZombieStats ZOMBIE_RIOT = {
    .health = 100, .armor = 85.0f, .attack_base = ZOMBIE_ATTACK_BASE, .tint = 0xffffff,
};
/* About twice as long to put down as a riot zombie, and its claw hurts a
 * third more: one per stage, guarding something. */
const ZombieStats ZOMBIE_ELITE = {
    .health = 150, .armor = 120.0f, .attack_base = ZOMBIE_ATTACK_BASE * 1.35f, .tint = 0xffa080,
};

void zombie_spawn(Zombie *zombie, const ZombieStats *stats, float x)
{
    memset(zombie, 0, sizeof(*zombie));
    zombie->stats = stats;
    zombie->x = x;
    zombie->facing = -1; /* zombie_update turns it toward the player */
    zombie->state = ZOMBIE_WALK;
    zombie->awake = true;
    zombie->just_spawned = true;
    zombie->growl_time = ZOMBIE_GROWL_INTERVAL; /* Its spawn growl counts as the first */
    animation_play(&zombie->anim, &ANIM_WALK);
    zombie_set_level(zombie, 1);
}

void zombie_set_level(Zombie *zombie, int level)
{
    zombie->level = level < 1 ? 1 : level;
    zombie->max_health = level_health(zombie->stats->health, zombie->level);
    zombie->armor = level_armor(zombie->stats->armor, ZOMBIE_ARMOR_PER_LEVEL, zombie->level);
    zombie->health = zombie->max_health;
    zombie->wound = 0.0f;
}

float zombie_spawn_x(float player_x)
{
    float left = camera_left(player_x);
    return player_x - left <= VIEW_WIDTH / 2.0f ? left + VIEW_WIDTH - ZOMBIE_SPAWN_MARGIN
                                                  : left + ZOMBIE_SPAWN_MARGIN;
}

void zombie_wake(Zombie *zombie)
{
    if (zombie->awake)
        return;
    zombie->awake = true;
    zombie->just_spawned = true;
    zombie->rouse = ZOMBIE_ROUSE_TIME;
}

int zombie_breath(const Zombie *zombie)
{
    if (zombie->state == ZOMBIE_DEAD)
        return 0;
    if (zombie->awake) /* Woken: it jerks upright, then settles */
        return zombie->rouse > ZOMBIE_ROUSE_TIME - 0.15f ? 2 : 0;
    return fmodf(zombie->idle_time, ZOMBIE_BREATH_TIME) < ZOMBIE_BREATH_TIME / 2.0f ? 1 : 0;
}

void zombie_update(Zombie *zombie, float player_x, bool player_alive, float dt)
{
    zombie->struck = false;
    if (!zombie->awake && zombie->state != ZOMBIE_DEAD) {
        /* Standing on the first walk frame, breathing, watching her come.
         * Each one breathes on its own beat (its spot sets the phase). */
        if (zombie->idle_time == 0.0f)
            zombie->idle_time = fmodf(zombie->x * 0.013f, ZOMBIE_BREATH_TIME) + 0.001f;
        zombie->idle_time += dt;
        zombie->facing = player_x < zombie->x ? -1 : 1;
        animation_restart(&zombie->anim);
        return;
    }
    if (zombie->caught > 0.0f && zombie->state != ZOMBIE_DEAD) {
        /* In a trap: it writhes on the spot (the recoil's first frames). */
        zombie->caught -= dt;
        zombie->facing = player_x < zombie->x ? -1 : 1;
        animation_play(&zombie->anim, &ANIM_HURT);
        animation_set_frame(&zombie->anim, (int)(zombie->caught * 6.0f) % 2);
        if (zombie->caught > 0.0f)
            return;
        zombie->caught = 0.0f;
        animation_play(&zombie->anim, &ANIM_WALK);
    }
    if (zombie->rouse > 0.0f && zombie->state != ZOMBIE_DEAD && zombie->state != ZOMBIE_HURT) {
        /* Woken: it jerks upright and shudders, turned on her, then lurches
         * into its first step and sets off. */
        zombie->rouse -= dt;
        zombie->facing = player_x < zombie->x ? -1 : 1;
        animation_play(&zombie->anim, &ANIM_WALK);
        animation_set_frame(&zombie->anim, zombie->rouse > ZOMBIE_ROUSE_TIME / 2.0f ? 0 : 1);
        if (zombie->rouse > 0.0f)
            return;
        zombie->rouse = 0.0f;
        animation_play(&zombie->anim, &ANIM_WALK);
    }
    if (zombie->stagger_time > 0.0f)
        zombie->stagger_time = fmaxf(0.0f, zombie->stagger_time - dt);
    if (zombie->attack_cooldown > 0.0f)
        zombie->attack_cooldown = fmaxf(0.0f, zombie->attack_cooldown - dt);
    if (zombie->state != ZOMBIE_DEAD) {
        zombie->growl_time -= dt;
        if (zombie->growl_time <= 0.0f) {
            zombie->growl_due = true;
            zombie->growl_time += ZOMBIE_GROWL_INTERVAL;
        }
    }

    if (zombie->state == ZOMBIE_DEAD) {
        zombie->dead_time += dt;
        animation_update(&zombie->anim, dt); /* Holds the last frame once down */
        return;
    }

    if (zombie->state == ZOMBIE_HURT) {
        animation_update(&zombie->anim, dt);
        if (!zombie->anim.finished)
            return;
        animation_play(&zombie->anim, &ANIM_WALK);
    }

    /* The swipe plays out facing where it started; a recoil cuts it short. */
    if (zombie->state == ZOMBIE_ATTACK) {
        int before = zombie->anim.frame;
        animation_update(&zombie->anim, dt);
        zombie->struck = before < ZOMBIE_ATTACK_STRIKE_FRAME &&
                         zombie->anim.frame >= ZOMBIE_ATTACK_STRIKE_FRAME;
        if (!zombie->anim.finished)
            return;
        zombie->attack_cooldown = ZOMBIE_ATTACK_COOLDOWN;
        animation_play(&zombie->anim, &ANIM_WALK);
    }

    float gap = player_x - zombie->x;
    zombie->facing = gap < 0.0f ? -1 : 1;
    if (fabsf(gap) <= ZOMBIE_REACH) {
        if (player_alive && zombie->attack_cooldown <= 0.0f) {
            zombie->state = ZOMBIE_ATTACK;
            animation_play(&zombie->anim, &ANIM_ATTACK);
            animation_restart(&zombie->anim);
            return;
        }
        /* Waiting shows the first walk frame, like the player's idle. */
        zombie->state = ZOMBIE_WAIT;
        animation_restart(&zombie->anim);
        return;
    }
    zombie->state = ZOMBIE_WALK;
    float step = fminf(ZOMBIE_SPEED * dt, fabsf(gap) - ZOMBIE_REACH);
    zombie->x += (float)zombie->facing * step;
    animation_update(&zombie->anim, dt);
}

HitResult zombie_hit(Zombie *zombie, float damage)
{
    return zombie_hit_through(zombie, damage, 1.0f);
}

HitResult zombie_hit_through(Zombie *zombie, float damage, float armor_share)
{
    if (!zombie_alive(zombie))
        return HIT_NONE;
    zombie->wound += damage_through_armor(damage, zombie->armor * armor_share);
    int points = (int)zombie->wound;
    zombie->wound -= (float)points;
    zombie->health -= points;
    if (zombie->health > 0) {
        if (zombie->stagger_time > 0.0f)
            return HIT_ARMOR;
        zombie->state = ZOMBIE_HURT;
        zombie->stagger_time = ZOMBIE_HURT_FRAMES / ZOMBIE_HURT_FPS + ZOMBIE_STAGGER_COOLDOWN;
        animation_play(&zombie->anim, &ANIM_HURT);
        animation_restart(&zombie->anim);
        return HIT_STAGGER;
    }
    zombie->health = 0;
    zombie->state = ZOMBIE_DEAD;
    zombie->dead_time = 0.0f;
    zombie->just_died = true;
    zombie->growl_due = false; /* The death groan replaces a growl due now */
    /* Frame 0 is the standing pose: start on the jolt, which has the sparks. */
    animation_play(&zombie->anim, &ANIM_DEATH);
    animation_seek(&zombie->anim, 1);
    return HIT_KILL;
}

float zombie_attack_damage(const Zombie *zombie)
{
    return damage_at_level(zombie->stats->attack_base, zombie->level);
}

int zombie_shudder(const Zombie *zombie)
{
    if (!zombie->awake || zombie->rouse <= ZOMBIE_ROUSE_TIME / 2.0f || zombie->state == ZOMBIE_DEAD)
        return 0;
    return (int)(zombie->rouse * 25.0f) % 2 ? 1 : -1;
}

bool zombie_alive(const Zombie *zombie)
{
    return zombie->state != ZOMBIE_DEAD;
}

bool zombie_overlaps(const Zombie *zombie, float x0, float x1, float y)
{
    float half = ZOMBIE_HALF_WIDTH * SPRITE_SCALE;
    return fmaxf(x0, x1) >= zombie->x - half && fminf(x0, x1) <= zombie->x + half &&
           y <= BASELINE && y >= BASELINE - ZOMBIE_HEIGHT * SPRITE_SCALE;
}

bool zombie_gone(const Zombie *zombie)
{
    return !zombie_alive(zombie) && zombie->dead_time >= DEATH_FADE_START + ZOMBIE_FADE_TIME;
}

float zombie_opacity(const Zombie *zombie)
{
    if (zombie_alive(zombie))
        return 1.0f;
    float fading = zombie->dead_time - DEATH_FADE_START;
    return fminf(1.0f, fmaxf(0.0f, 1.0f - fading / ZOMBIE_FADE_TIME));
}

const AnimationDef *const *zombie_animations(int *count)
{
    *count = (int)(sizeof(ANIMATIONS) / sizeof(ANIMATIONS[0]));
    return ANIMATIONS;
}
