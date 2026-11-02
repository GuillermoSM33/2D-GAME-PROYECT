#include "game/bullet.h"

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
        animation_play(&b->anim, &ANIM_BULLET);
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
        b->flown += b->spec.speed * dt;
        animation_update(&b->anim, dt);
        if (b->x < view_left - OFFSCREEN_MARGIN ||
            b->x > view_left + VIEW_WIDTH + OFFSCREEN_MARGIN ||
            (b->spec.range > 0.0f && b->flown >= b->spec.range))
            b->active = false;
    }
}

int bullets_active_count(const Bullets *bullets)
{
    int count = 0;
    for (int i = 0; i < BULLET_MAX; i++)
        count += bullets->items[i].active;
    return count;
}

const AnimationDef *bullet_animation(void)
{
    return &ANIM_BULLET;
}
