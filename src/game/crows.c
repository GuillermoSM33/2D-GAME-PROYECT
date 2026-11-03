#include "game/crows.h"

#include <math.h>
#include <string.h>

static unsigned hash(unsigned h)
{
    h ^= h >> 13;
    h *= 0x5bd1e995u;
    h ^= h >> 15;
    return h;
}

void crows_start(Crows *crows, int stage_index, float start_x, float length)
{
    memset(crows, 0, sizeof(*crows));
    unsigned seed = (unsigned)stage_index * 7919u + 3u;
    /* A flock every CROW_FLOCK_EVERY or so, from a little way in. */
    for (float x = start_x + CROW_FLOCK_EVERY * 0.5f; x < start_x + length - 600.0f;) {
        seed = hash(seed + 101u);
        int size = 2 + (int)(seed % 3u);
        for (int i = 0; i < size && crows->count < CROWS_MAX; i++) {
            Crow *c = &crows->items[crows->count++];
            unsigned h = hash(seed + (unsigned)i * 31u);
            c->x = x + (float)(i * 70) + (float)(h % 40u);
            c->facing = h & 1u ? 1 : -1;
            c->time = (float)(h % 100u) / 37.0f; /* Each pecks on its own beat */
        }
        x += CROW_FLOCK_EVERY * (0.7f + (float)(seed % 60u) / 100.0f);
    }
}

static void take_off(Crows *crows, Crow *c, float from_x)
{
    if (c->flying || c->gone || c->dead)
        return;
    unsigned h = hash((unsigned)(c->x * 3.0f));
    c->flying = true;
    c->time = 0.0f;
    c->facing = c->x < from_x ? -1 : 1; /* Away from her (or the noise) */
    c->vx = (float)c->facing * (CROW_FLY_SPEED + (float)(h % 80u));
    c->vy = CROW_CLIMB + (float)(h % 60u);
    crows->took_off++;
}

void crows_update(Crows *crows, float player_x, bool moving, float dt)
{
    crows->took_off = crows->killed = 0;
    for (int i = 0; i < crows->count; i++) {
        Crow *c = &crows->items[i];
        if (c->gone)
            continue;
        c->time += dt;
        if (c->dead) { /* Dropping like a stone, then lying there */
            if (c->height > 0.0f) {
                c->vy -= CROW_FALL_GRAVITY * dt;
                c->x += c->vx * dt;
                c->height = fmaxf(0.0f, c->height + c->vy * dt);
            } else {
                c->dead_time += dt;
                c->gone = c->dead_time >= CROW_CORPSE_TIME + CROW_FADE_TIME;
            }
            continue;
        }
        if (!c->flying) {
            if (fabsf(c->x - player_x) <= (moving ? CROW_SCARE_RANGE : CROW_SCARE_RANGE * 0.4f))
                take_off(crows, c, player_x);
            continue;
        }
        c->x += c->vx * dt;
        c->height += c->vy * dt;
        c->vy += CROW_CLIMB * 0.5f * dt; /* Climbing harder as it gets going */
        c->gone = c->height > CROW_GONE_HEIGHT;
    }
}

void crows_noise(Crows *crows, float x, float range)
{
    for (int i = 0; i < crows->count; i++) {
        if (fabsf(crows->items[i].x - x) <= range)
            take_off(crows, &crows->items[i], x);
    }
}

static void kill(Crows *crows, Crow *c)
{
    c->dead = true;
    c->flying = false;
    c->vx *= 0.3f;
    c->vy = 0.0f;
    crows->killed++;
}

int crows_shoot(Crows *crows, Bullets *bullets)
{
    int hits = 0;
    float half_w = CROW_FRAME_W * SPRITE_SCALE / 2.0f, half_h = CROW_FRAME_H * SPRITE_SCALE / 2.0f;
    for (int i = 0; i < crows->count; i++) {
        Crow *c = &crows->items[i];
        if (c->gone || c->dead)
            continue;
        float cy = (float)BASELINE - c->height - half_h;
        for (int b = 0; b < BULLET_MAX; b++) {
            Bullet *bullet = &bullets->items[b];
            if (!bullet->active || fabsf(bullet->y - cy) > half_h)
                continue;
            float lo = fminf(bullet->prev_x, bullet->x), hi = fmaxf(bullet->prev_x, bullet->x);
            if (hi < c->x - half_w || lo > c->x + half_w)
                continue;
            bullet->active = false;
            kill(crows, c);
            hits++;
            crows_noise(crows, c->x, CROW_SCARE_RANGE * 2.0f); /* Its flock goes */
            break;
        }
    }
    return hits;
}

int crows_blast(Crows *crows, float x, float radius)
{
    int killed = 0;
    for (int i = 0; i < crows->count; i++) {
        Crow *c = &crows->items[i];
        if (!c->gone && !c->dead && fabsf(c->x - x) <= radius) {
            kill(crows, c);
            killed++;
        }
    }
    crows_noise(crows, x, CROW_BLAST_RANGE);
    return killed;
}

float crow_opacity(const Crow *crow)
{
    if (!crow->dead || crow->dead_time <= CROW_CORPSE_TIME)
        return 1.0f;
    return fmaxf(0.0f, 1.0f - (crow->dead_time - CROW_CORPSE_TIME) / CROW_FADE_TIME);
}

int crow_frame(const Crow *crow)
{
    if (crow->dead)
        return crow->height > 0.0f ? 6 : 7;
    if (crow->flying)
        return 2 + (int)(crow->time * CROW_FLAP_FPS) % 4;
    /* Pecking now and then, standing in between. */
    return fmodf(crow->time, 2.2f) > 1.8f ? (int)(crow->time * 8.0f) % 2 : 0;
}
