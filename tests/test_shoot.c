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
    /* Up to the bullet, then the reload, then what is left of the holster. */
    float reload_end = PLAYER_SHOOT_FIRE_FRAME * frame_time() + PLAYER_SHOOT_RELOAD_TIME;
    float expected = reload_end + (PLAYER_SHOOT_FRAMES - PLAYER_SHOOT_RELOAD_FRAME - 0.5f) * frame_time();
    CHECK_NEAR(steps * FIXED_DT, expected, FIXED_DT * 2.01f);
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
    while (shot.reload > 0.0f || shot_frame(&shot) <= PLAYER_SHOOT_FIRE_FRAME)
        shot_update(&shot, FIXED_DT);
    CHECK(shot_start(&shot));
    CHECK(shot_frame(&shot) == PLAYER_SHOOT_AIM_FRAME);
    CHECK(!shot.fired);
    int fires = 0;
    for (int i = 0; i < 120; i++)
        fires += shot_update(&shot, FIXED_DT);
    CHECK(fires == 1); /* The follow-up fires its own bullet */
}

static void test_reload_holds_recoil_and_blocks(void)
{
    Shot shot;
    shot_reset(&shot);
    shot_start(&shot);
    while (!shot_update(&shot, FIXED_DT))
        ;
    CHECK_NEAR(shot.reload, PLAYER_SHOOT_RELOAD_TIME, 1e-6f);
    /* Most of the reload later she still holds the recoil frame and can't shoot. */
    float waited = 0.0f;
    while (waited + FIXED_DT < PLAYER_SHOOT_RELOAD_TIME - FIXED_DT) {
        shot_update(&shot, FIXED_DT);
        waited += FIXED_DT;
        CHECK(shot.active && shot_frame(&shot) <= PLAYER_SHOOT_RELOAD_FRAME);
        CHECK(!shot_start(&shot));
    }
    while (shot.reload > 0.0f)
        shot_update(&shot, FIXED_DT);
    CHECK(shot.active);
    CHECK(shot_start(&shot)); /* Reloaded: the follow-up is accepted */
}

static void test_bullets_are_spaced_by_reload(void)
{
    /* Clicking every step, bullets come out one per reload plus the aim frame. */
    Shot shot;
    shot_reset(&shot);
    int fires = 0;
    float first = -1.0f, second = -1.0f, t = 0.0f;
    for (int i = 0; i < 120 && fires < 2; i++) {
        shot_start(&shot);
        if (shot_update(&shot, FIXED_DT)) {
            fires++;
            if (fires == 1)
                first = t;
            else
                second = t;
        }
        t += FIXED_DT;
    }
    CHECK(fires == 2);
    CHECK_NEAR(second - first, PLAYER_SHOOT_RELOAD_TIME + frame_time(), FIXED_DT * 1.01f);
}

static void test_reload_follows_the_gun(void)
{
    Shot shot;
    shot_reset(&shot);
    shot_set_reload(&shot, 0.2f);
    shot_start(&shot);
    while (!shot_update(&shot, FIXED_DT))
        ;
    CHECK_NEAR(shot.reload, 0.2f, 1e-6f);
    /* Cancelling (a jump) keeps the gun; a reset goes back to the revolver. */
    shot_cancel(&shot);
    CHECK_NEAR(shot.reload_time, 0.2f, 1e-6f);
    shot_reset(&shot);
    CHECK_NEAR(shot.reload_time, PLAYER_SHOOT_RELOAD_TIME, 1e-6f);
}

static void test_burst_fires_three_spaced(void)
{
    /* One click: three bullets burst_gap apart, then the reload. */
    Shot shot;
    shot_reset(&shot);
    shot_set_reload(&shot, 0.3f);
    shot_set_burst(&shot, 3, 0.07f, false);
    shot_start(&shot);
    float times[4];
    int fires = 0;
    bool flicked = false;
    for (int i = 0; i < 120 && shot.active; i++) {
        if (shot_update(&shot, FIXED_DT) && fires < 4)
            times[fires++] = (float)i * FIXED_DT;
        if (fires >= 1 && shot.burst_left > 0)
            flicked |= shot_frame(&shot) == PLAYER_SHOOT_FIRE_FRAME + 1;
        CHECK(fires < 3 || shot.burst_left == 0);
    }
    CHECK(fires == 3);
    CHECK_NEAR(times[1] - times[0], 0.07f, FIXED_DT * 1.01f);
    CHECK_NEAR(times[2] - times[1], 0.07f, FIXED_DT * 1.01f);
    CHECK(flicked); /* The gun kicks between bullets */
}

static void test_no_follow_up_mid_burst(void)
{
    Shot shot;
    shot_reset(&shot);
    shot_set_burst(&shot, 3, 0.07f, true);
    shot_start(&shot);
    while (!shot_update(&shot, FIXED_DT))
        ;
    CHECK(shot.burst_left == 2);
    CHECK(!shot_start(&shot));
    /* A jump cancels the burst but keeps the gun. */
    shot_cancel(&shot);
    CHECK(shot.burst == 3 && shot.automatic && shot.burst_left == 0);
}

static void test_magazine_runs_dry_and_reloads(void)
{
    /* Two shots per magazine, held trigger: two bullets, the reload sheet for
     * its time, then two more, the first right after (already aimed). */
    Shot shot;
    shot_reset(&shot);
    shot_set_reload(&shot, 0.1f);
    shot_set_magazine(&shot, 2, 1.0f, -1);
    CHECK(shot.rounds == 2);
    float times[4];
    int fires = 0;
    float reloading = 0.0f, t = 0.0f;
    for (int i = 0; i < 600 && fires < 4; i++) {
        shot_start(&shot);
        if (shot_update(&shot, FIXED_DT))
            times[fires++] = t;
        if (shot_reloading(&shot))
            reloading += FIXED_DT;
        t += FIXED_DT;
    }
    CHECK(fires == 4);
    CHECK_NEAR(reloading, 1.0f, FIXED_DT * 1.5f);
    CHECK(times[2] - times[1] > 1.0f);
    CHECK(times[2] - times[1] < 1.0f + 6.0f * frame_time());
    CHECK(shot.rounds == 0);
}

static void test_burst_counts_as_one_shot(void)
{
    Shot shot;
    shot_reset(&shot);
    shot_set_burst(&shot, 3, 0.07f, true);
    shot_set_magazine(&shot, 5, 1.2f, -1);
    shot_start(&shot);
    int fires = 0;
    for (int i = 0; i < 60; i++)
        fires += shot_update(&shot, FIXED_DT);
    CHECK(fires == 3 && shot.rounds == 4);
}

static void test_cut_reload_resumes_and_keeps_rounds(void)
{
    /* A jump cuts the reload: the magazine stays empty and the next pull
     * reloads instead of firing. A gun put away keeps its count. */
    Shot shot;
    shot_reset(&shot);
    shot_set_magazine(&shot, 1, 1.0f, -1);
    shot_start(&shot);
    while (!shot_reloading(&shot))
        shot_update(&shot, FIXED_DT);
    shot_cancel(&shot);
    CHECK(!shot_reloading(&shot) && shot.rounds == 0 && shot.magazine == 1);
    CHECK(shot_start(&shot) && shot_reloading(&shot));
    CHECK(!shot_start(&shot)); /* No shooting mid-reload */
    shot_set_magazine(&shot, 8, 1.1f, 3);
    CHECK(shot.rounds == 3);
    shot_set_magazine(&shot, 0, 0.0f, -1);
    CHECK(shot.magazine == 0); /* The revolver never runs dry */
}

int main(void)
{
    printf("test_shoot\n");
    RUN(test_full_sequence);
    RUN(test_fires_exactly_once);
    RUN(test_no_follow_up_before_fire);
    RUN(test_follow_up_restarts_aimed);
    RUN(test_reload_holds_recoil_and_blocks);
    RUN(test_bullets_are_spaced_by_reload);
    RUN(test_reload_follows_the_gun);
    RUN(test_burst_fires_three_spaced);
    RUN(test_no_follow_up_mid_burst);
    RUN(test_magazine_runs_dry_and_reloads);
    RUN(test_burst_counts_as_one_shot);
    RUN(test_cut_reload_resumes_and_keeps_rounds);
    return TEST_EXIT();
}
