#include "game/smoke.h"

#include <math.h>
#include <string.h>

/* Cheap deterministic variation in [0, 1): no global random state, so tests
 * and the smoke test always see the same clouds. */
static float vary(unsigned cloud, int puff, int salt)
{
    unsigned h = cloud * 747796405u + (unsigned)puff * 2891336453u + (unsigned)salt * 277803737u;
    h ^= h >> 16;
    h *= 0x7feb352du;
    h ^= h >> 15;
    return (float)(h >> 8) / 16777216.0f;
}

void smoke_clear(Smoke *smoke)
{
    memset(smoke, 0, sizeof(*smoke));
}

static Puff *free_puff(Smoke *smoke)
{
    Puff *oldest = &smoke->puffs[0];
    for (int i = 0; i < SMOKE_MAX_PUFFS; i++) {
        Puff *p = &smoke->puffs[i];
        if (!p->active)
            return p;
        if (p->age - p->delay > oldest->age - oldest->delay)
            oldest = p;
    }
    return oldest;
}

void smoke_emit(Smoke *smoke, float x, float y, int dir, int puffs, float scale)
{
    unsigned cloud = ++smoke->emitted;
    float side = dir < 0 ? -1.0f : 1.0f;
    for (int i = 0; i < puffs; i++) {
        Puff *p = free_puff(smoke);
        memset(p, 0, sizeof(*p));
        p->active = true;
        p->delay = (float)i * SMOKE_PUFF_INTERVAL;
        p->life = SMOKE_PUFF_LIFE * scale * (0.8f + 0.4f * vary(cloud, i, 0));
        p->scale = scale;
        p->x = x;
        p->y = y;
        /* The first puffs are pushed out by the shot, the later ones just leak. */
        float push = 1.0f - (float)i / (float)puffs;
        p->vx = side * (SMOKE_DRIFT_SPEED * (0.5f + push) + 15.0f * vary(cloud, i, 1));
        p->vy = -SMOKE_RISE_SPEED * (0.7f + 0.6f * vary(cloud, i, 2));
        p->phase = 6.2831853f * vary(cloud, i, 3);
    }
}

void smoke_rise(Smoke *smoke, float x, float y, int puffs, float scale)
{
    unsigned cloud = ++smoke->emitted;
    for (int i = 0; i < puffs; i++) {
        Puff *p = free_puff(smoke);
        memset(p, 0, sizeof(*p));
        p->active = true;
        p->delay = (float)i * SMOKE_PUFF_INTERVAL;
        p->life = SMOKE_PUFF_LIFE * 1.8f * scale * (0.8f + 0.4f * vary(cloud, i, 0));
        p->scale = scale;
        p->x = x + 24.0f * (vary(cloud, i, 1) - 0.5f);
        p->y = y;
        /* Straight up, wavering a little: no shot behind it. */
        p->vx = 14.0f * (vary(cloud, i, 2) - 0.5f);
        p->vy = -SMOKE_RISE_SPEED * (1.4f + 0.6f * vary(cloud, i, 3));
        p->phase = 6.2831853f * vary(cloud, i, 4);
    }
}

void smoke_update(Smoke *smoke, float dt)
{
    for (int i = 0; i < SMOKE_MAX_PUFFS; i++) {
        Puff *p = &smoke->puffs[i];
        if (!p->active)
            continue;
        p->age += dt;
        if (!puff_visible(p))
            continue;
        float t = p->age - p->delay;
        if (t >= p->life) {
            p->active = false;
            continue;
        }
        /* Air slows the push; the rise keeps going, with a slight wobble. */
        float drag = expf(-SMOKE_DRAG * dt);
        p->vx *= drag;
        p->x += (p->vx + SMOKE_WOBBLE * sinf(t * 9.0f + p->phase)) * dt;
        p->y += p->vy * dt;
    }
}

bool puff_visible(const Puff *puff)
{
    return puff->active && puff->age >= puff->delay;
}

float puff_progress(const Puff *puff)
{
    float t = (puff->age - puff->delay) / puff->life;
    return t < 0.0f ? 0.0f : (t > 1.0f ? 1.0f : t);
}

int puff_size(const Puff *puff)
{
    float t = puff_progress(puff);
    float size = SMOKE_PUFF_START_SIZE + (SMOKE_PUFF_END_SIZE - SMOKE_PUFF_START_SIZE) * t;
    return (int)lroundf(size * puff->scale);
}

float puff_opacity(const Puff *puff)
{
    /* Thick at first, then thinning out: (1 - t)^1.5. */
    float t = puff_progress(puff);
    return powf(1.0f - t, 1.5f);
}

int smoke_active_count(const Smoke *smoke)
{
    int count = 0;
    for (int i = 0; i < SMOKE_MAX_PUFFS; i++)
        count += smoke->puffs[i].active;
    return count;
}
