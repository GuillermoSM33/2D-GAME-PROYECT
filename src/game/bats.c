#include "game/bats.h"

#include <math.h>
#include <string.h>

static unsigned next(Bats *bats)
{
    unsigned h = bats->seed = bats->seed * 1103515245u + 12345u;
    h ^= h >> 13;
    h *= 0x5bd1e995u;
    return h ^ (h >> 15);
}

static float roll(Bats *bats, float lo, float hi)
{
    return lo + (hi - lo) * (float)(next(bats) % 1000u) / 999.0f;
}

void bats_start(Bats *bats, int stage_index)
{
    memset(bats, 0, sizeof(*bats));
    bats->seed = (unsigned)stage_index * 2654435761u + 7u;
    bats->wait = BAT_FIRST;
}

static void spawn(Bats *bats, float view_left)
{
    int dir = next(bats) & 1u ? 1 : -1;
    int count = 1 + (int)(next(bats) % (unsigned)BAT_GROUP_MAX);
    float base = roll(bats, BAT_LOW, BAT_HIGH);
    for (int i = 0, made = 0; i < BATS_MAX && made < count; i++) {
        Bat *b = &bats->items[i];
        if (bat_present(b))
            continue;
        memset(b, 0, sizeof(*b));
        b->alive = true;
        b->facing = dir;
        b->vx = (float)dir * roll(bats, BAT_SPEED * 0.8f, BAT_SPEED * 1.2f);
        b->x = dir > 0 ? view_left - 60.0f - (float)made * 70.0f
                       : view_left + VIEW_WIDTH + 60.0f + (float)made * 70.0f;
        b->base = base + roll(bats, -30.0f, 30.0f);
        b->time = roll(bats, 0.0f, 3.0f); /* Each on its own beat */
        b->height = b->base;
        made++;
    }
}

void bats_update(Bats *bats, bool night, float view_left, float dt)
{
    bats->killed = 0;
    if (night) {
        bats->wait -= dt;
        if (bats->wait <= 0.0f) {
            spawn(bats, view_left);
            bats->wait = roll(bats, BAT_EVERY_MIN, BAT_EVERY_MAX);
        }
    }
    for (int i = 0; i < BATS_MAX; i++) {
        Bat *b = &bats->items[i];
        if (!bat_present(b))
            continue;
        b->time += dt;
        if (b->dead) {
            if (b->height > 0.0f) {
                b->vy -= CROW_FALL_GRAVITY * dt;
                b->x += b->vx * dt;
                b->height = fmaxf(0.0f, b->height + b->vy * dt);
            } else {
                b->dead_time += dt;
            }
            continue;
        }
        /* Flitting: a swoop up and down with a quick jitter on top. */
        b->x += b->vx * dt;
        b->height = b->base + BAT_DIP * sinf(b->time * 2.6f) + 10.0f * sinf(b->time * 11.0f);
        bool past = b->facing > 0 ? b->x > view_left + VIEW_WIDTH + 200.0f : b->x < view_left - 200.0f;
        if (past)
            b->alive = false;
    }
}

static void kill(Bats *bats, Bat *b)
{
    b->alive = false;
    b->dead = true;
    b->vx *= 0.25f;
    b->vy = 0.0f;
    bats->killed++;
}

int bats_shoot(Bats *bats, Bullets *bullets)
{
    int hits = 0;
    float half_w = BAT_FRAME_W * SPRITE_SCALE / 2.0f, half_h = BAT_FRAME_H * SPRITE_SCALE / 2.0f + 6.0f;
    for (int i = 0; i < BATS_MAX; i++) {
        Bat *b = &bats->items[i];
        if (!b->alive)
            continue;
        float cy = (float)BASELINE - b->height - half_h;
        for (int k = 0; k < BULLET_MAX; k++) {
            Bullet *bullet = &bullets->items[k];
            if (!bullet->active || fabsf(bullet->y - cy) > half_h)
                continue;
            float lo = fminf(bullet->prev_x, bullet->x), hi = fmaxf(bullet->prev_x, bullet->x);
            if (hi < b->x - half_w || lo > b->x + half_w)
                continue;
            bullet->active = false;
            kill(bats, b);
            hits++;
            break;
        }
    }
    return hits;
}

int bats_blast(Bats *bats, float x, float radius)
{
    int killed = 0;
    for (int i = 0; i < BATS_MAX; i++) {
        Bat *b = &bats->items[i];
        if (b->alive && fabsf(b->x - x) <= radius && b->height <= radius) {
            kill(bats, b);
            killed++;
        }
    }
    return killed;
}

bool bat_present(const Bat *bat)
{
    return bat->alive || (bat->dead && bat->dead_time < CROW_CORPSE_TIME + CROW_FADE_TIME);
}

int bat_frame(const Bat *bat)
{
    if (bat->dead)
        return bat->height > 0.0f ? 4 : 5;
    return (int)(bat->time * BAT_FLAP_FPS) % 4;
}

float bat_opacity(const Bat *bat)
{
    if (!bat->dead || bat->dead_time <= CROW_CORPSE_TIME)
        return 1.0f;
    return fmaxf(0.0f, 1.0f - (bat->dead_time - CROW_CORPSE_TIME) / CROW_FADE_TIME);
}
