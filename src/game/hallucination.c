#include "game/hallucination.h"

#include <math.h>
#include <string.h>

void hallucination_clear(Hallucination *h)
{
    memset(h, 0, sizeof(*h));
    h->spawn_wait = PHANTOM_EVERY * 0.5f;
    h->double_time = DOUBLE_EVERY;
}

static void vanish(Hallucination *h, Phantom *p)
{
    if (p->fading)
        return;
    p->fading = true;
    if (h->vanished < PHANTOMS_MAX)
        h->vanished_x[h->vanished++] = p->x;
}

void hallucination_update(Hallucination *h, bool on, float player_x, int player_facing, float camera_x,
                          float dt)
{
    h->spawned = h->vanished = 0;
    if (on) {
        h->spawn_wait -= dt;
        if (h->spawn_wait <= 0.0f) { /* One walks in from an edge, the sides in turn */
            h->spawn_wait = PHANTOM_EVERY;
            for (int i = 0; i < PHANTOMS_MAX; i++) {
                Phantom *p = &h->phantoms[i];
                if (p->active)
                    continue;
                h->side = h->side > 0 ? -1 : 1;
                int side = h->side;
                memset(p, 0, sizeof(*p));
                p->active = true;
                p->fade = 1.0f;
                p->x = side > 0 ? camera_x + (float)VIEW_WIDTH + 60.0f : camera_x - 60.0f;
                p->facing = side > 0 ? -1 : 1;
                h->spawned++;
                break;
            }
        }
    }
    for (int i = 0; i < PHANTOMS_MAX; i++) {
        Phantom *p = &h->phantoms[i];
        if (!p->active)
            continue;
        if (!on)
            vanish(h, p);
        if (p->fading) {
            p->fade -= dt / PHANTOM_FADE;
            p->active = p->fade > 0.0f;
            continue;
        }
        p->time += dt;
        p->facing = player_x < p->x ? -1 : 1;
        p->x += (float)p->facing * PHANTOM_SPEED * dt;
        if (fabsf(p->x - player_x) < PHANTOM_REACH) /* Right up to her: nothing there */
            vanish(h, p);
    }
    /* Herself, a few steps ahead, looking back; then gone a while. */
    h->double_time -= dt;
    if (h->double_on && (h->double_time <= 0.0f || !on)) {
        h->double_on = false;
        h->double_time = DOUBLE_EVERY;
    } else if (!h->double_on && on && h->double_time <= 0.0f) {
        h->double_on = true;
        h->double_time = DOUBLE_TIME;
        h->double_facing = -player_facing;
        h->double_x = player_x + (float)player_facing * DOUBLE_GAP;
    }
}

int hallucination_shoot(Hallucination *h, Bullets *bullets)
{
    int hits = 0;
    float half = ZOMBIE_HALF_WIDTH * SPRITE_SCALE;
    for (int i = 0; i < PHANTOMS_MAX; i++) {
        Phantom *p = &h->phantoms[i];
        if (!p->active || p->fading)
            continue;
        for (int b = 0; b < BULLET_MAX; b++) {
            Bullet *bullet = &bullets->items[b];
            if (!bullet->active || bullet->y < (float)BASELINE - ZOMBIE_HEIGHT * SPRITE_SCALE)
                continue;
            float lo = fminf(bullet->prev_x, bullet->x), hi = fmaxf(bullet->prev_x, bullet->x);
            if (hi < p->x - half || lo > p->x + half)
                continue;
            bullet->active = false;
            vanish(h, p);
            hits++;
            break;
        }
    }
    return hits;
}
