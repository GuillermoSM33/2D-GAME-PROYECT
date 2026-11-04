#include <math.h>
#include <stdio.h>

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

static void test_only_at_night(void)
{
    Bats bats;
    bats_start(&bats, 3);
    for (int i = 0; i < (int)(60.0f / FIXED_DT); i++)
        bats_update(&bats, false, 0.0f, FIXED_DT);
    CHECK(flying(&bats) == 0);
    int seen = 0;
    for (int i = 0; i < (int)(60.0f / FIXED_DT); i++) {
        bats_update(&bats, true, 0.0f, FIXED_DT);
        seen = flying(&bats) > seen ? flying(&bats) : seen;
    }
    CHECK(seen >= 1 && seen <= BAT_GROUP_MAX * 2);
}

static void test_they_cross_and_go(void)
{
    /* Each comes from off one side, crosses flitting up and down, and is
     * gone past the other side. */
    Bats bats;
    bats_start(&bats, 0);
    bats.wait = 0.0f;
    bats_update(&bats, true, 0.0f, FIXED_DT);
    Bat *b = NULL;
    for (int i = 0; i < BATS_MAX && b == NULL; i++)
        b = bats.items[i].alive ? &bats.items[i] : NULL;
    CHECK(b != NULL);
    if (b == NULL)
        return;
    CHECK(b->x < 0.0f || b->x > VIEW_WIDTH);
    float low = 1e9f, high = 0.0f;
    bats.wait = 1e9f; /* No more */
    for (int i = 0; i < 600 && b->alive; i++) {
        bats_update(&bats, true, 0.0f, FIXED_DT);
        low = fminf(low, b->height);
        high = fmaxf(high, b->height);
    }
    CHECK(!b->alive && !bat_present(b));
    CHECK(high - low > BAT_DIP && low > 40.0f);
    CHECK(bat_frame(b) >= 0 && bat_frame(b) < 4);
}

static void test_a_bullet_brings_one_down(void)
{
    Bats bats;
    bats_start(&bats, 0);
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
    for (int i = 0; i < 120; i++)
        bats_update(&bats, false, 0.0f, FIXED_DT);
    CHECK(b->height == 0.0f && bat_frame(b) == 5); /* Lying on the road */
    for (int i = 0; i < (int)((CROW_CORPSE_TIME + CROW_FADE_TIME) / FIXED_DT); i++)
        bats_update(&bats, false, 0.0f, FIXED_DT);
    CHECK(!bat_present(b));
}

static void test_a_blast_kills_the_low_ones(void)
{
    Bats bats;
    bats_start(&bats, 0);
    bats.items[0] = (Bat){.x = 100.0f, .height = 120.0f, .alive = true};
    bats.items[1] = (Bat){.x = 100.0f, .height = 600.0f, .alive = true};
    CHECK(bats_blast(&bats, 120.0f, BARREL_RADIUS) == 1);
    CHECK(bats.items[0].dead && bats.items[1].alive);
}

int main(void)
{
    printf("test_bats\n");
    RUN(test_only_at_night);
    RUN(test_they_cross_and_go);
    RUN(test_a_bullet_brings_one_down);
    RUN(test_a_blast_kills_the_low_ones);
    return TEST_EXIT();
}
