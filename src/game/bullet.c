#include "game/bullet.h"

#include <string.h>

#include "config.h"

#define BULLET_SHEET "sprites/player/bullet"

/* The ball spans x 1..6 and every row, so its center is (4, 3). For bullets
 * ground_y is just the vertical pivot row. */
static const AnimationDef ANIM_BULLET = {
    .sheet = BULLET_SHEET, .frame_w = BULLET_FRAME_W, .frame_h = BULLET_FRAME_H,
    .first_frame = 0, .frame_count = BULLET_FRAMES, .fps = BULLET_FPS, .loop = true,
    .anchor_x = 4.0f, .ground_y = 3,
};

/* Fully off-screen once the whole frame is past the edge. */
#define OFFSCREEN_MARGIN (BULLET_FRAME_W * SPRITE_SCALE)

void bullets_clear(Bullets *bullets)
{
    memset(bullets, 0, sizeof(*bullets));
}

bool bullets_spawn(Bullets *bullets, float from_x, float x, float y, int dir)
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
        animation_play(&b->anim, &ANIM_BULLET);
        return true;
    }
    return false;
}

void bullets_update(Bullets *bullets, float dt)
{
    for (int i = 0; i < BULLET_MAX; i++) {
        Bullet *b = &bullets->items[i];
        if (!b->active)
            continue;
        b->prev_x = b->x;
        b->x += (float)b->dir * BULLET_SPEED * dt;
        animation_update(&b->anim, dt);
        if (b->x < -OFFSCREEN_MARGIN || b->x > WINDOW_WIDTH + OFFSCREEN_MARGIN)
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
