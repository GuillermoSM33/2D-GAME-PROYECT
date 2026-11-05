#include "game/bullet.h"

#include <math.h>
#include <string.h>

#include "config.h"
#include "game/damage.h"

#define BULLET_SHEET "sprites/weapons/bullet"

/* The ball spans x 1..6 and every row, so its center is (4, 3). For bullets
 * ground_y is just the vertical pivot row. */
static const AnimationDef ANIM_BULLET = {
    .sheet = BULLET_SHEET, .frame_w = BULLET_FRAME_W, .frame_h = BULLET_FRAME_H,
    .first_frame = 0, .frame_count = BULLET_FRAMES, .fps = BULLET_FPS, .loop = true,
    .anchor_x = 4.0f, .ground_y = 3,
};

/* The cowgirl's ricochet, her own sprite: flying, glanced off, and the impact. */
#define RICOCHET_SHEET "sprites/characters/cowgirl/weapons/bullet"
static const AnimationDef ANIM_RICOCHET_FLY = {
    .sheet = RICOCHET_SHEET, .frame_w = RICOCHET_FRAME_W, .frame_h = RICOCHET_FRAME_H,
    .first_frame = 0, .frame_count = RICOCHET_FLY_FRAMES, .fps = RICOCHET_FPS, .loop = true,
    .anchor_x = 11.0f, .ground_y = 8,
};
static const AnimationDef ANIM_RICOCHET_SPIN = {
    .sheet = RICOCHET_SHEET, .frame_w = RICOCHET_FRAME_W, .frame_h = RICOCHET_FRAME_H,
    .first_frame = RICOCHET_FLY_FRAMES, .frame_count = RICOCHET_SPIN_FRAMES, .fps = RICOCHET_FPS, .loop = true,
    .anchor_x = 10.0f, .ground_y = 8,
};
static const AnimationDef ANIM_RICOCHET_BURST = {
    .sheet = RICOCHET_SHEET, .frame_w = RICOCHET_FRAME_W, .frame_h = RICOCHET_FRAME_H,
    .first_frame = RICOCHET_FLY_FRAMES + RICOCHET_SPIN_FRAMES, .frame_count = RICOCHET_BURST_FRAMES,
    .fps = RICOCHET_FPS, .loop = false,
    .anchor_x = 10.0f, .ground_y = 8,
};

/* Fully out of view once the whole frame is past the edge. */
#define OFFSCREEN_MARGIN (BULLET_FRAME_W * SPRITE_SCALE)

void bullets_clear(Bullets *bullets)
{
    memset(bullets, 0, sizeof(*bullets));
}

bool bullets_fire(Bullets *bullets, float from_x, float x, float y, int dir, const BulletSpec *spec)
{
    for (int i = 0; i < BULLET_MAX; i++) {
        Bullet *b = &bullets->items[i];
        if (b->active)
            continue;
        memset(b, 0, sizeof(*b));
        b->active = true;
        b->x = x;
        b->prev_x = from_x;
        b->y = y;
        b->dir = dir < 0 ? -1 : 1;
        b->spec = *spec;
        animation_play(&b->anim, spec->ricochet ? &ANIM_RICOCHET_FLY : &ANIM_BULLET);
        return true;
    }
    return false;
}

bool bullets_spawn(Bullets *bullets, float from_x, float x, float y, int dir)
{
    const BulletSpec plain = {weapon_damage(1), BULLET_SPEED, 0.0f, 1.0f, 0xffffff, 0.0f, false};
    return bullets_fire(bullets, from_x, x, y, dir, &plain);
}

void bullets_update(Bullets *bullets, float dt, float view_left)
{
    for (int i = 0; i < BULLET_MAX; i++) {
        Bullet *b = &bullets->items[i];
        if (!b->active)
            continue;
        b->prev_x = b->x;
        b->x += (float)b->dir * b->spec.speed * dt;
        b->y += b->spec.slope * b->spec.speed * dt;
        if (b->bounce_left > 0.0f) { /* Glancing off: up a little and back down to its line */
            b->bounce_left -= dt;
            float done = 1.0f - fmaxf(b->bounce_left, 0.0f) / RICOCHET_BOUNCE_TIME;
            b->y = b->bounce_y - RICOCHET_BOUNCE * sinf(done * 3.14159265f);
        }
        b->flown += b->spec.speed * dt;
        animation_update(&b->anim, dt);
        if (b->x < view_left - OFFSCREEN_MARGIN ||
            b->x > view_left + VIEW_WIDTH + OFFSCREEN_MARGIN ||
            (b->spec.range > 0.0f && b->flown >= b->spec.range))
            b->active = false;
    }
}

void bullet_glance(Bullets *bullets, Bullet *bullet, const void *body, float mult)
{
    bullet->spec.ricochet = false;
    bullet->spec.damage *= mult;
    bullet->glanced = body;
    bullet->bounce_y = bullet->y;
    bullet->bounce_left = RICOCHET_BOUNCE_TIME;
    bullet->burst = true;
    bullet->spec.range = bullet->flown + RICOCHET_REACH; /* It doesn't fly on for ever */
    animation_play(&bullet->anim, &ANIM_RICOCHET_SPIN);
    bullets->glances++;
}

int bullets_active_count(const Bullets *bullets)
{
    int count = 0;
    for (int i = 0; i < BULLET_MAX; i++)
        count += bullets->items[i].active;
    return count;
}

const AnimationDef *bullet_impact_animation(void)
{
    return &ANIM_RICOCHET_BURST;
}

const AnimationDef *bullet_animation(void)
{
    return &ANIM_BULLET;
}
