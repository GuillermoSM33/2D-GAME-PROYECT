#include <math.h>

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

static void test_infinite_ammo_never_spends_a_magazine_counter(void)
{
    for (int burst = 1; burst <= 3; burst += 2) {
        Shot shot;
        shot_reset(&shot);
        shot_set_burst(&shot, burst, 0.07f, true);
        shot_set_magazine(&shot, 0, 0.0f, -1);
        int fires = 0;
        for (int frame = 0; frame < 600; frame++) {
            shot_start(&shot);
            fires += shot_update(&shot, FIXED_DT);
            CHECK(shot.rounds == 0 && !shot_reloading(&shot));
        }
        CHECK(fires >= 10);
        shot_cancel(&shot);
        CHECK(shot.rounds == 0);
        if (burst > 1) {
            shot_start(&shot);
            while (!shot_update(&shot, FIXED_DT)) {}
            CHECK(shot.burst_left > 0);
            shot_cancel(&shot); /* A partially fired burst spends no finite ammo. */
            CHECK(shot.rounds == 0);
        }
    }
}

static void piston_guns(Shot *shot)
{
    shot_reset(shot);
    shot_set_reload(shot, 0.19f);
    shot_set_burst(shot, 1, 0.0f, true);
    shot_set_piston(shot, true);
}

/* Steps until the next bullet; the trigger held or not. */
static bool next_bullet(Shot *shot, bool held, float seconds)
{
    for (float t = 0.0f; t < seconds && shot->active; t += FIXED_DT) {
        shot_trigger(shot, false, held);
        if (shot_update(shot, FIXED_DT))
            return true;
    }
    return false;
}

static void test_held_trigger_alternates_the_guns(void)
{
    Shot shot;
    piston_guns(&shot);
    CHECK(shot_start(&shot) && !shot.other_gun);
    for (int n = 0; n < 6; n++) {
        CHECK(next_bullet(&shot, true, 1.0f));
        CHECK(shot.active);
        CHECK(shot.other_gun == (n % 2 == 1)); /* Never the same gun twice */
        CHECK(shot_frame(&shot) == PLAYER_SHOOT_FIRE_FRAME);
    }
}

static void test_turn_plays_whole_between_shots(void)
{
    /* Each gun has come down before the other fires: all 8 frames between bullets. */
    Shot shot;
    piston_guns(&shot);
    shot_start(&shot);
    CHECK(next_bullet(&shot, true, 1.0f));
    bool seen[PLAYER_SHOOT_FRAMES] = {false};
    float took = 0.0f;
    for (; took < 1.0f; took += FIXED_DT) {
        shot_trigger(&shot, false, true);
        if (shot_update(&shot, FIXED_DT))
            break;
        seen[shot_frame(&shot)] = true;
    }
    CHECK(seen[PLAYER_SHOOT_FRAMES - 1] && seen[0]);
    CHECK(fabsf(took - PLAYER_SHOOT_FRAMES / PLAYER_PISTON_FPS) < 2.0f * FIXED_DT);
}

static void test_clicks_during_a_turn_are_kept_and_alternate(void)
{
    Shot shot;
    piston_guns(&shot);
    shot_start(&shot);
    CHECK(next_bullet(&shot, false, 1.0f) && !shot.other_gun);
    CHECK(!shot_start(&shot));
    shot_trigger(&shot, true, false); /* Clicked during the recoil */
    CHECK(next_bullet(&shot, false, 1.0f) && shot.other_gun);
    /* No more clicks: the last turn ends and they rest; the next is the other gun. */
    while (shot.active)
        shot_update(&shot, FIXED_DT);
    CHECK(shot_start(&shot) && !shot.other_gun);
}

static void test_released_trigger_stops_after_its_turn(void)
{
    Shot shot;
    piston_guns(&shot);
    shot_start(&shot);
    CHECK(next_bullet(&shot, true, 1.0f));
    CHECK(!next_bullet(&shot, false, 2.0f) && !shot.active);
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
    RUN(test_infinite_ammo_never_spends_a_magazine_counter);
    RUN(test_held_trigger_alternates_the_guns);
    RUN(test_turn_plays_whole_between_shots);
    RUN(test_clicks_during_a_turn_are_kept_and_alternate);
    RUN(test_released_trigger_stops_after_its_turn);
    return TEST_EXIT();
}
