#include <math.h>
#include <stdio.h>
#include <string.h>

#include "config.h"
#include "game/bats.h"
#include "test.h"

static int flying(const Bats *bats)
{
    int n = 0;
    for (int i = 0; i < BATS_MAX; i++)
        n += bats->items[i].alive;
    return n;
}

static void test_colonies_on_the_road_only_at_night(void)
{
    /* Set along the road like the crows, and few: none by day, and no more
     * ever come than those placed, however long she takes. */
    Bats bats;
    bats_start(&bats, 3, 0.0f, 26500.0f, false);
    CHECK(flying(&bats) == 0);
    bats_start(&bats, 3, 0.0f, 26500.0f, true);
    int placed = flying(&bats);
    CHECK(placed >= 3 && placed <= 12);
    for (int i = 0; i < BATS_MAX; i++)
        if (bats.items[i].alive)
            CHECK(bats.items[i].x > 0.0f && bats.items[i].x < 26500.0f);
    for (int i = 0; i < (int)(120.0f / FIXED_DT); i++)
        bats_update(&bats, -5000.0f, FIXED_DT);
    CHECK(flying(&bats) == placed);
}

static void test_they_flit_through_her_line_of_fire(void)
{
    /* Over its spot, and at times as low as her gun. */
    Bats bats;
    memset(&bats, 0, sizeof(bats));
    bats.items[0] = (Bat){.x = 2000.0f, .home = 2000.0f, .base = BAT_HIGH, .alive = true};
    Bat *b = &bats.items[0];
    float muzzle = PLAYER_MUZZLE_DY * SPRITE_SCALE;
    bool in_line = false;
    for (int i = 0; i < (int)(10.0f / FIXED_DT); i++) {
        bats_update(&bats, -5000.0f, FIXED_DT);
        CHECK(fabsf(b->x - b->home) <= BAT_ROAM + 1.0f);
        in_line = in_line || fabsf(b->height + BAT_FRAME_H * SPRITE_SCALE / 2.0f - muzzle) < 10.0f;
    }
    CHECK(in_line);
}

static void test_they_fly_off_when_she_comes(void)
{
    Bats bats;
    memset(&bats, 0, sizeof(bats));
    bats.items[0] = (Bat){.x = 1000.0f, .home = 1000.0f, .base = BAT_LOW, .alive = true};
    Bat *b = &bats.items[0];
    bats_update(&bats, 1000.0f - BAT_SCARE_RANGE, FIXED_DT);
    CHECK(b->fleeing && b->facing > 0);
    for (int i = 0; i < (int)(10.0f / FIXED_DT) && b->alive; i++)
        bats_update(&bats, 1000.0f - BAT_SCARE_RANGE, FIXED_DT);
    CHECK(!bat_present(b) && b->x > 1000.0f);
    CHECK(bats_take_flee_events(&bats) == 1); /* Survives all flight updates */
    CHECK(bats_take_flee_events(&bats) == 0);
}

static void test_a_bullet_brings_one_down(void)
{
    Bats bats;
    memset(&bats, 0, sizeof(bats));
    bats.items[1] = (Bat){.x = 800.0f, .home = 800.0f, .base = BAT_HIGH, .alive = true};
    Bat *b = &bats.items[0];
    b->alive = true;
    b->x = 600.0f;
    b->height = 140.0f;
    b->facing = 1;
    Bullets bullets;
    bullets_clear(&bullets);
    float y = (float)BASELINE - b->height - BAT_FRAME_H * SPRITE_SCALE / 2.0f;
    bullets_spawn(&bullets, 500.0f, 560.0f, y, 1);
    bullets_update(&bullets, FIXED_DT, 0.0f);
    CHECK(bats_shoot(&bats, &bullets) == 1 && b->dead && !b->alive);
    CHECK(bullets_active_count(&bullets) == 0);
    CHECK(bats.items[1].fleeing); /* The other one heard it */
    bats_update(&bats, -5000.0f, FIXED_DT);
    CHECK(bats_take_flee_events(&bats) == 1); /* Not cleared by update */
    CHECK(bats_take_flee_events(&bats) == 0);
    for (int i = 0; i < 120; i++)
        bats_update(&bats, -5000.0f, FIXED_DT);
    CHECK(b->height == 0.0f && bat_frame(b) == 5); /* Lying on the road */
    for (int i = 0; i < (int)((CROW_CORPSE_TIME + CROW_FADE_TIME) / FIXED_DT); i++)
        bats_update(&bats, -5000.0f, FIXED_DT);
    CHECK(!bat_present(b));
}

static void test_a_blast_kills_the_low_ones(void)
{
    Bats bats;
    memset(&bats, 0, sizeof(bats));
    bats.items[0] = (Bat){.x = 100.0f, .height = 120.0f, .alive = true};
    bats.items[1] = (Bat){.x = 100.0f, .height = 600.0f, .alive = true};
    CHECK(bats_blast(&bats, 120.0f, BARREL_RADIUS) == 1);
    CHECK(bats.items[0].dead && bats.items[1].alive);
    bats_update(&bats, -5000.0f, FIXED_DT);
    CHECK(bats_take_flee_events(&bats) == 1);
    bats_blast(&bats, 120.0f, BARREL_RADIUS);
    CHECK(bats_take_flee_events(&bats) == 0); /* Already fleeing */
    bats_start(&bats, 3, 0.0f, 26500.0f, false);
    CHECK(bats_take_flee_events(&bats) == 0); /* A new run is clean */
}

int main(void)
{
    printf("test_bats\n");
    RUN(test_colonies_on_the_road_only_at_night);
    RUN(test_they_flit_through_her_line_of_fire);
    RUN(test_they_fly_off_when_she_comes);
    RUN(test_a_bullet_brings_one_down);
    RUN(test_a_blast_kills_the_low_ones);
    return TEST_EXIT();
}
