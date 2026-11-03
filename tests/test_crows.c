#include <math.h>

#include "config.h"
#include "game/crows.h"
#include "test.h"

static void test_flocks_along_the_road(void)
{
    Crows crows;
    crows_start(&crows, 0, 1000.0f, 19000.0f);
    CHECK(crows.count >= 6 && crows.count <= CROWS_MAX);
    for (int i = 0; i < crows.count; i++)
        CHECK(!crows.items[i].flying && crows.items[i].x > 1000.0f && crows.items[i].x < 20000.0f);
}

static void test_they_fly_off_when_she_comes(void)
{
    Crows crows;
    crows_start(&crows, 0, 1000.0f, 19000.0f);
    Crow *c = &crows.items[0];
    crows_update(&crows, c->x - CROW_SCARE_RANGE - 50.0f, true, FIXED_DT);
    CHECK(!c->flying);
    crows_update(&crows, c->x - CROW_SCARE_RANGE + 10.0f, true, FIXED_DT);
    CHECK(c->flying && crows.took_off > 0 && c->facing == 1); /* Away from her */
    for (int i = 0; i < 600; i++)
        crows_update(&crows, 0.0f, false, FIXED_DT);
    CHECK(c->gone);
}

static void test_a_shot_scares_them(void)
{
    Crows crows;
    crows_start(&crows, 1, 1000.0f, 19000.0f);
    Crow *c = &crows.items[0];
    crows_noise(&crows, c->x + CROW_SHOT_RANGE + 50.0f, CROW_SHOT_RANGE);
    CHECK(!c->flying);
    crows_noise(&crows, c->x + 200.0f, CROW_SHOT_RANGE);
    CHECK(c->flying && c->facing == -1);
}

static void test_a_bullet_kills_one(void)
{
    /* A crow up in the line of fire takes the bullet: it drops, lies on the
     * road, fades and is gone. */
    Crows crows;
    crows_start(&crows, 0, 1000.0f, 19000.0f);
    Crow *c = &crows.items[0];
    c->flying = true;
    c->height = 100.0f;
    Bullets bullets;
    bullets_clear(&bullets);
    float y = (float)BASELINE - c->height - CROW_FRAME_H * SPRITE_SCALE / 2.0f;
    BulletSpec spec = {30.0f, 1000.0f, 0.0f, 1.0f, 0xffffff, 0.0f, false};
    bullets_fire(&bullets, c->x - 100.0f, c->x - 100.0f, y, 1, &spec);
    for (int i = 0; i < 20 && !c->dead; i++) {
        bullets_update(&bullets, FIXED_DT, c->x - 600.0f);
        crows_shoot(&crows, &bullets);
    }
    CHECK(c->dead && !bullets.items[0].active);
    for (int i = 0; i < (int)((CROW_CORPSE_TIME + CROW_FADE_TIME + 2.0f) / FIXED_DT); i++)
        crows_update(&crows, 0.0f, false, FIXED_DT);
    CHECK(c->height == 0.0f && c->gone);
}

int main(void)
{
    RUN(test_flocks_along_the_road);
    RUN(test_they_fly_off_when_she_comes);
    RUN(test_a_shot_scares_them);
    RUN(test_a_bullet_kills_one);
    return TEST_EXIT();
}
