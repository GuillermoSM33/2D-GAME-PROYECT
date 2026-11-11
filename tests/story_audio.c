/* The real story audio scheduler, with a recording audio boundary.
 * No renderer, device, files, SDL setup or generated assets are needed. */
#include <math.h>
#include <string.h>

#include "app/story_audio.h"
#include "engine/audio.h"
#include "game/settings.h"
#include "test.h"

typedef enum { PLAY, LOOP, STOP, STOP_LOOP } Kind;
typedef struct { Kind kind; const char *name; int group; float gain; } Event;
static Event events[256];
static int count;

static void record(Kind kind, const char *name, int group, float gain)
{
    CHECK(count < (int)(sizeof(events) / sizeof(events[0])));
    if (count < (int)(sizeof(events) / sizeof(events[0])))
        events[count++] = (Event){kind, name, group, gain};
}

void audio_play_in_gain(const char *name, int group, float gain) { record(PLAY, name, group, gain); }
void audio_loop_in(const char *name, int group, float gain) { record(LOOP, name, group, gain); }
void audio_stop(const char *name) { record(STOP, name, 0, 0); }
void audio_stop_loop(const char *name) { record(STOP_LOOP, name, 0, 0); }

static int matches(Kind kind, const char *name)
{
    int n = 0;
    for (int i = 0; i < count; i++)
        n += events[i].kind == kind && strcmp(events[i].name, name) == 0;
    return n;
}

static Story shot(int scene, int line, float time)
{
    return (Story){.beat = {.scene = scene, .count = 3}, .line = line, .time = time};
}

static void advance(Story *story, float seconds)
{
    Story before = *story;
    story->time += seconds;
    story_audio_update(&before, story, seconds);
}

static void test_actions_follow_visible_animation_boundaries(void)
{
    Story story = shot(1, 0, 0.0f);
    story_audio_start(&story);
    count = 0;
    advance(&story, 0.59f);
    CHECK(matches(PLAY, "world/hit_wood") == 0);
    advance(&story, 0.02f);
    CHECK(matches(PLAY, "world/hit_wood") == 1);
    advance(&story, 2.0f);
    CHECK(matches(PLAY, "world/hit_wood") == 5);

    story = shot(1, 2, 0.0f);
    story_audio_start(&story);
    count = 0;
    advance(&story, 0.61f);
    CHECK(matches(PLAY, "weather/thunder") == 1);
    CHECK(matches(PLAY, "world/hit_sand") == 0);
    advance(&story, 0.99f);
    CHECK(matches(PLAY, "world/hit_sand") == 2);
    CHECK(matches(PLAY, "zombie/spawn") == 1);
}

static void test_lamps_and_departing_crows_have_their_own_cues(void)
{
    Story story = shot(2, 2, 0.0f);
    count = 0;
    advance(&story, 0.99f);
    CHECK(matches(PLAY, "player/flashlight_off") == 0);
    advance(&story, 0.02f);
    CHECK(matches(PLAY, "player/flashlight_off") == 1);
    advance(&story, 1.8f);
    CHECK(matches(PLAY, "player/flashlight_off") == 3);

    story = shot(3, 0, 0.0f);
    count = 0;
    advance(&story, 1.59f);
    CHECK(matches(PLAY, "crow/caw") == 0);
    advance(&story, 0.02f);
    CHECK(matches(PLAY, "crow/caw") == 1);
}

static void test_enter_skips_future_actions_and_next_shot_cleans_up(void)
{
    Story before = shot(1, 2, 0.0f), after = before;
    after.time = 5.0f; /* The caption was completed by Enter. */
    count = 0;
    story_audio_update(&before, &after, 1.0f / 60.0f);
    CHECK(matches(PLAY, "weather/thunder") == 0);
    CHECK(matches(PLAY, "zombie/spawn") == 0);
    before = after;
    after = shot(2, 0, 0.0f);
    story_audio_update(&before, &after, 1.0f / 60.0f);
    CHECK(matches(STOP, "zombie/spawn") == 1);
    CHECK(matches(LOOP, "weather/wind") == 1);
    CHECK(matches(PLAY, "world/footstep") == 0);
    before = after;
    after.done = true;
    count = 0;
    story_audio_update(&before, &after, 1.0f / 60.0f);
    CHECK(matches(STOP_LOOP, "weather/wind") == 1);
    CHECK(matches(STOP, "world/footstep") == 1);
    CHECK(matches(LOOP, "weather/wind") == 0);
}

static void test_lab_ambience_and_invalid_or_paused_time_do_not_leak(void)
{
    Story before = shot(4, 1, 0.0f);
    count = 0;
    story_audio_start(&before);
    CHECK(matches(LOOP, "cinematic/lab_hum") == 1);
    CHECK(matches(LOOP, "cinematic/lab_alarm") == 1);
    CHECK(matches(LOOP, "weather/wind") == 0);
    Story after = shot(4, 2, 0.0f);
    count = 0;
    story_audio_update(&before, &after, 1.0f / 60.0f);
    CHECK(matches(STOP_LOOP, "cinematic/lab_alarm") == 1);
    CHECK(matches(LOOP, "cinematic/lab_hum") == 1);
    CHECK(matches(LOOP, "cinematic/lab_alarm") == 0);
    count = 0;
    story_audio_update(&after, &after, 10.0f);
    CHECK(count == 0);
    before = shot(2, 0, 0.0f);
    after = shot(2, 0, 3.0f);
    story_audio_update(&before, &after, NAN);
    CHECK(count == 0);
    story_audio_stop();
    CHECK(matches(STOP_LOOP, "cinematic/lab_hum") == 1);
}

int main(void)
{
    RUN(test_actions_follow_visible_animation_boundaries);
    RUN(test_lamps_and_departing_crows_have_their_own_cues);
    RUN(test_enter_skips_future_actions_and_next_shot_cleans_up);
    RUN(test_lab_ambience_and_invalid_or_paused_time_do_not_leak);
    return TEST_EXIT();
}
