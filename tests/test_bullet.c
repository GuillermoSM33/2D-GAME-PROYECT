#include "config.h"
#include "game/bullet.h"
#include "test.h"

static void test_flies_at_speed(void)
{
    Bullets bullets;
    bullets_clear(&bullets);
    CHECK(bullets_spawn(&bullets, 100.0f, 100.0f, 300.0f, 1));
    bullets_update(&bullets, 0.25f, 0.0f);
    const Bullet *b = &bullets.items[0];
    CHECK(b->active);
    CHECK_NEAR(b->x, 100.0f + BULLET_SPEED * 0.25f, 0.01f);
    CHECK_NEAR(b->y, 300.0f, 1e-6f); /* Straight line */
}

static void test_flies_left(void)
{
    Bullets bullets;
    bullets_clear(&bullets);
    bullets_spawn(&bullets, 500.0f, 500.0f, 300.0f, -1);
    bullets_update(&bullets, 0.1f, 0.0f);
    CHECK(bullets.items[0].x < 500.0f);
    CHECK(bullets.items[0].dir == -1);
}

static void test_removed_off_screen(void)
{
    Bullets bullets;
    bullets_clear(&bullets);
    bullets_spawn(&bullets, VIEW_WIDTH - 10.0f, VIEW_WIDTH - 10.0f, 300.0f, 1);
    bullets_spawn(&bullets, 10.0f, 10.0f, 300.0f, -1);
    CHECK(bullets_active_count(&bullets) == 2);
    for (int i = 0; i < 30; i++)
        bullets_update(&bullets, FIXED_DT, 0.0f);
    CHECK(bullets_active_count(&bullets) == 0);
}

static void test_pool_limit_and_reuse(void)
{
    Bullets bullets;
    bullets_clear(&bullets);
    for (int i = 0; i < BULLET_MAX; i++)
        CHECK(bullets_spawn(&bullets, 400.0f, 400.0f, 300.0f, 1));
    CHECK(!bullets_spawn(&bullets, 400.0f, 400.0f, 300.0f, 1));
    for (int i = 0; i < 120; i++) /* Out of the view: 1920 px at 900 px/s */
        bullets_update(&bullets, FIXED_DT, 0.0f);
    CHECK(bullets_active_count(&bullets) == 0);
    CHECK(bullets_spawn(&bullets, 400.0f, 400.0f, 300.0f, 1)); /* Slots are reused */
}

static void test_spins(void)
{
    Bullets bullets;
    bullets_clear(&bullets);
    bullets_spawn(&bullets, 0.0f, 0.0f, 300.0f, 1);
    unsigned seen = 0;
    for (int i = 0; i < 30; i++) {
        bullets_update(&bullets, FIXED_DT, 0.0f);
        seen |= 1u << bullets.items[0].anim.frame;
    }
    CHECK(seen == (1u << BULLET_FRAMES) - 1);
}

static void test_pellets_fan_out(void)
{
    /* A sloped pellet drifts away from the line as it flies; a straight one doesn't. */
    Bullets bullets;
    bullets_clear(&bullets);
    BulletSpec up = {1.0f, 1000.0f, 0.0f, 1.0f, 0xffffff, -0.2f, false};
    BulletSpec level = {1.0f, 1000.0f, 0.0f, 1.0f, 0xffffff, 0.0f, false};
    bullets_fire(&bullets, 100.0f, 100.0f, 300.0f, 1, &up);
    bullets_fire(&bullets, 100.0f, 100.0f, 300.0f, 1, &level);
    bullets_update(&bullets, 0.1f, 0.0f);
    CHECK_NEAR(bullets.items[0].y, 300.0f - 0.2f * 100.0f, 1e-3f);
    CHECK_NEAR(bullets.items[1].y, 300.0f, 1e-6f);
}

int main(void)
{
    printf("test_bullet\n");
    RUN(test_flies_at_speed);
    RUN(test_flies_left);
    RUN(test_removed_off_screen);
    RUN(test_pool_limit_and_reuse);
    RUN(test_spins);
    RUN(test_pellets_fan_out);
    return TEST_EXIT();
}
