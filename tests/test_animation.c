#include "engine/animation.h"
#include "test.h"

static const AnimationDef WALK = {.sheet = "walk", .frame_count = 8, .fps = 9.0f, .loop = true};
static const AnimationDef ONCE = {.sheet = "jump", .first_frame = 2, .frame_count = 3,
                                  .fps = 10.0f, .loop = false};

static void test_loops_through_all_frames(void)
{
    Animation anim = {0};
    animation_play(&anim, &WALK);
    CHECK(anim.frame == 0);
    unsigned seen = 0;
    for (int i = 0; i < 60; i++) { /* 1 s at 60 Hz = 9 frames */
        animation_update(&anim, 1.0f / 60.0f);
        seen |= 1u << anim.frame;
    }
    CHECK(seen == 0xFFu);
    CHECK(anim.frame >= 0 && anim.frame < 8);
}

static void test_play_same_def_keeps_progress(void)
{
    Animation anim = {0};
    animation_play(&anim, &WALK);
    animation_update(&anim, 0.35f);
    int frame = anim.frame;
    CHECK(frame == 3);
    animation_play(&anim, &WALK);
    CHECK(anim.frame == frame);
}

static void test_play_other_def_restarts(void)
{
    Animation anim = {0};
    animation_play(&anim, &WALK);
    animation_update(&anim, 0.35f);
    animation_play(&anim, &ONCE);
    CHECK(anim.frame == 2);
    CHECK_NEAR(anim.time, 0.0f, 1e-6f);
}

static void test_non_looping_stops_at_last(void)
{
    Animation anim = {0};
    animation_play(&anim, &ONCE);
    animation_update(&anim, 1.0f);
    CHECK(anim.frame == 4);
    CHECK(anim.finished);
}

static void test_progress_picks_frame(void)
{
    Animation anim = {0};
    animation_play(&anim, &WALK);
    animation_set_progress(&anim, 0.0f);
    CHECK(anim.frame == 0);
    animation_set_progress(&anim, 0.5f);
    CHECK(anim.frame == 4);
    animation_set_progress(&anim, 0.999f);
    CHECK(anim.frame == 7);
    animation_set_progress(&anim, 1.5f);
    CHECK(anim.frame == 7); /* Clamped */
    animation_play(&anim, &ONCE);
    animation_set_progress(&anim, 0.0f);
    CHECK(anim.frame == 2); /* Offset by first_frame */
}

int main(void)
{
    printf("test_animation\n");
    RUN(test_loops_through_all_frames);
    RUN(test_play_same_def_keeps_progress);
    RUN(test_play_other_def_restarts);
    RUN(test_non_looping_stops_at_last);
    RUN(test_progress_picks_frame);
    return TEST_EXIT();
}
