#include "config.h"
#include "game/jump.h"
#include "test.h"

static void test_arc(void)
{
    Jump jump;
    jump_reset(&jump);
    CHECK(jump_start(&jump));
    CHECK(!jump_start(&jump)); /* Already airborne */

    float peak = 0.0f;
    int steps = 0;
    bool landed = false;
    while (!landed && steps < 1000) {
        landed = jump_update(&jump, FIXED_DT);
        if (jump.height > peak)
            peak = jump.height;
        CHECK(jump.height >= 0.0f);
        steps++;
    }
    CHECK(landed);
    CHECK_NEAR(peak, PLAYER_JUMP_HEIGHT, 0.5f);
    CHECK_NEAR(steps * FIXED_DT, PLAYER_JUMP_TIME, FIXED_DT * 1.01f);
    CHECK(!jump.airborne);
    CHECK_NEAR(jump.height, 0.0f, 1e-6f);
}

static void test_progress(void)
{
    Jump jump;
    jump_reset(&jump);
    CHECK_NEAR(jump_progress(&jump), 0.0f, 1e-6f);
    jump_start(&jump);
    jump_update(&jump, PLAYER_JUMP_TIME / 2.0f);
    CHECK_NEAR(jump_progress(&jump), 0.5f, 1e-4f);
    CHECK_NEAR(jump.height, PLAYER_JUMP_HEIGHT, 0.01f); /* Peak at half time */
}

static void test_ground_update_is_noop(void)
{
    Jump jump;
    jump_reset(&jump);
    CHECK(!jump_update(&jump, 1.0f));
    CHECK(!jump.airborne);
}

int main(void)
{
    printf("test_jump\n");
    RUN(test_arc);
    RUN(test_progress);
    RUN(test_ground_update_is_noop);
    return TEST_EXIT();
}
