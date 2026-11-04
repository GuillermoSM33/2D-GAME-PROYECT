#include "game/bats.h"

#include <math.h>
#include <string.h>

static unsigned hash(unsigned h)
{
    h ^= h >> 13;
    h *= 0x5bd1e995u;
    return h ^ (h >> 15);
}

void bats_start(Bats *bats, int stage_index, float start_x, float length, bool night)
{
    memset(bats, 0, sizeof(*bats));
    if (!night)
        return;
    unsigned seed = (unsigned)stage_index * 2654435761u + 7u;
    int count = 0;
    for (float x = start_x + BAT_COLONY_EVERY * 0.5f; x < start_x + length - 600.0f;) {
        seed = hash(seed + 101u);
        int size = 1 + (int)(seed % (unsigned)BAT_GROUP_MAX);
        for (int i = 0; i < size && count < BATS_MAX; i++) {
            Bat *b = &bats->items[count++];
            unsigned h = hash(seed + (unsigned)i * 31u);
            b->alive = true;
            b->home = x + (float)(i * 90);
            b->x = b->home;
            b->facing = h & 1u ? 1 : -1;
            b->base = BAT_LOW + (BAT_HIGH - BAT_LOW) * (float)(h % 100u) / 99.0f;
            b->time = (float)(h % 300u) / 100.0f; /* Each on its own beat */
            b->height = b->base;
        }
        x += BAT_COLONY_EVERY * (0.7f + (float)(seed % 60u) / 100.0f);
    }
}

static void take_off(Bat *b, float from_x)
{
    if (!b->alive || b->fleeing)
        return;
    b->fleeing = true;
    b->facing = b->x >= from_x ? 1 : -1;
    b->vx = (float)b->facing * BAT_FLEE_SPEED;
}

void bats_update(Bats *bats, float player_x, float dt)
{
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
        if (b->fleeing) {
            b->x += b->vx * dt;
            b->height += BAT_CLIMB * dt;
            b->alive = b->height < CROW_GONE_HEIGHT;
            continue;
        }
        if (fabsf(b->x - player_x) <= BAT_SCARE_RANGE) {
            take_off(b, player_x);
            continue;
        }
        /* Flitting over its spot: to and fro, a swoop up and down, a quick jitter. */
        float x = b->home + BAT_ROAM * sinf(b->time * 1.3f);
        if (x != b->x)
            b->facing = x > b->x ? 1 : -1;
        b->vx = (x - b->x) / dt;
        b->x = x;
        b->height = b->base + BAT_DIP * sinf(b->time * 2.6f) + 10.0f * sinf(b->time * 11.0f);
    }
}

static void kill(Bats *bats, Bat *b)
{
    b->alive = false;
    b->fleeing = false;
    b->dead = true;
    b->vx *= 0.25f;
    b->vy = 0.0f;
    for (int i = 0; i < BATS_MAX; i++) /* The rest of them scatter */
        if (fabsf(bats->items[i].x - b->x) <= BAT_FLOCK_RANGE)
            take_off(&bats->items[i], b->x);
}

int bats_shoot(Bats *bats, Bullets *bullets)
{
    int hits = 0;
    float half_w = BAT_FRAME_W * SPRITE_SCALE / 2.0f, half_h = BAT_FRAME_H * SPRITE_SCALE / 2.0f + 12.0f;
    for (int i = 0; i < BATS_MAX; i++) {
        Bat *b = &bats->items[i];
        if (!b->alive)
            continue;
        float cy = (float)BASELINE - b->height - BAT_FRAME_H * SPRITE_SCALE / 2.0f;
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
        if (!b->alive)
            continue;
        if (fabsf(b->x - x) <= radius && b->height <= radius) {
            kill(bats, b);
            killed++;
        } else if (fabsf(b->x - x) <= CROW_BLAST_RANGE) {
            take_off(b, x);
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
