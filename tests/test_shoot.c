#include "config.h"
#include "game/shoot.h"
#include "test.h"

static float frame_time(void)
{
    return 1.0f / PLAYER_SHOOT_FPS;
}

static void test_full_sequence(void)
{
    Shot shot;
    shot_reset(&shot);
    CHECK(shot_start(&shot));
    CHECK(shot_frame(&shot) == 0);

    int fired_at = -1, steps = 0;
    unsigned seen = 1u;
    while (shot.active && steps < 1000) {
        if (shot_update(&shot, FIXED_DT))
            fired_at = shot_frame(&shot);
        if (shot.active)
            seen |= 1u << shot_frame(&shot);
        steps++;
    }
    CHECK(fired_at == PLAYER_SHOOT_FIRE_FRAME);
    CHECK(seen == (1u << PLAYER_SHOOT_FRAMES) - 1);
    CHECK_NEAR(steps * FIXED_DT, PLAYER_SHOOT_FRAMES * frame_time(), FIXED_DT * 1.01f);
}

static void test_fires_exactly_once(void)
{
    Shot shot;
    shot_reset(&shot);
    shot_start(&shot);
    int fires = 0;
    for (int i = 0; i < 120; i++)
        fires += shot_update(&shot, FIXED_DT);
    CHECK(fires == 1);
    CHECK(!shot.active);
}

static void test_no_follow_up_before_fire(void)
{
    Shot shot;
    shot_reset(&shot);
    shot_start(&shot);
    shot_update(&shot, frame_time() * 2.5f); /* Still drawing */
    CHECK(!shot_start(&shot));
    shot_update(&shot, frame_time() * 2.0f); /* On the fire frame */
    CHECK(shot_frame(&shot) == PLAYER_SHOOT_FIRE_FRAME);
    CHECK(!shot_start(&shot)); /* Flash must be shown first */
}

static void test_follow_up_restarts_aimed(void)
{
    Shot shot;
    shot_reset(&shot);
    shot_start(&shot);
    while (shot_frame(&shot) <= PLAYER_SHOOT_FIRE_FRAME)
        shot_update(&shot, FIXED_DT);
    CHECK(shot_start(&shot));
    CHECK(shot_frame(&shot) == PLAYER_SHOOT_AIM_FRAME);
    CHECK(!shot.fired);
    int fires = 0;
    for (int i = 0; i < 120; i++)
        fires += shot_update(&shot, FIXED_DT);
    CHECK(fires == 1); /* The follow-up fires its own bullet */
}

int main(void)
{
    printf("test_shoot\n");
    RUN(test_full_sequence);
    RUN(test_fires_exactly_once);
    RUN(test_no_follow_up_before_fire);
    RUN(test_follow_up_restarts_aimed);
    return TEST_EXIT();
}
