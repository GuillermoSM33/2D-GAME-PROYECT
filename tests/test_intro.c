#include <string.h>

#include "game/intro.h"
#include "test.h"

#define STEP (1.0f / 60.0f)

static int run_to_end(Intro *intro, IntroScene *seen_order, int *scenes_seen)
{
    const IntroCue *fired[8];
    int cues = 0;
    *scenes_seen = 0;
    IntroScene last = (IntroScene)-1;
    for (int i = 0; i < 60 * 200 && !intro->done; i++) {
        IntroScene s = intro_scene(intro, NULL);
        if (s != last) {
            seen_order[(*scenes_seen)++] = s;
            last = s;
        }
        cues += intro_update(intro, STEP, false, fired, 8);
    }
    return cues;
}

static void test_full_plays_every_scene_in_order(void)
{
    Intro intro;
    intro_start(&intro, INTRO_FULL);
    IntroScene order[INTRO_SCENES * 2];
    int seen = 0;
    int cues = run_to_end(&intro, order, &seen);
    CHECK(intro.done && !intro.skipped);
    CHECK(seen == INTRO_SCENES);
    for (int s = 0; s < seen; s++)
        CHECK(order[s] == (IntroScene)s);
    int all;
    intro_cues(&all);
    CHECK(cues == all); /* Every noise once */
}

static void test_length_fits_the_script(void)
{
    /* docs/LORE.md: about 75 seconds. */
    float total = intro_total_length();
    CHECK(total >= 70.0f && total <= 80.0f);
    float sum = 0.0f;
    for (int s = 0; s < INTRO_SCENES; s++) {
        CHECK(intro_scene_length((IntroScene)s) >= 4.0f);
        sum += intro_scene_length((IntroScene)s);
    }
    CHECK_NEAR(sum, total, 0.001f);
}

static void test_cues_are_in_order_and_inside_their_scene(void)
{
    int count;
    const IntroCue *cues = intro_cues(&count);
    CHECK(count > 0);
    for (int i = 0; i < count; i++) {
        CHECK(cues[i].sound != NULL && cues[i].sound[0] != '\0');
        CHECK(cues[i].at >= 0.0f && cues[i].at < intro_scene_length(cues[i].scene));
        if (i > 0)
            CHECK(cues[i].scene > cues[i - 1].scene ||
                  (cues[i].scene == cues[i - 1].scene && cues[i].at >= cues[i - 1].at));
    }
}

static void test_skip_ends_at_once_without_noises(void)
{
    Intro intro;
    intro_start(&intro, INTRO_FULL);
    const IntroCue *fired[8];
    intro_update(&intro, 3.0f, false, fired, 8);
    CHECK(intro_update(&intro, STEP, true, fired, 8) == 0);
    CHECK(intro.done && intro.skipped);
    CHECK(intro_update(&intro, STEP, false, fired, 8) == 0); /* Nothing after the end */
}

static void test_short_is_only_the_title_with_its_music(void)
{
    Intro intro;
    intro_start(&intro, INTRO_SHORT);
    CHECK(intro_scene(&intro, NULL) == INTRO_TITLE);
    CHECK(intro_black(&intro) == 0.0f); /* Opens already lit, no fade from black */
    float length = intro.end - intro.time;
    CHECK(length >= 3.0f && length <= 6.0f);
    const IntroCue *fired[8];
    bool music = false;
    while (!intro.done) {
        int n = intro_update(&intro, STEP, false, fired, 8);
        for (int k = 0; k < n; k++) {
            CHECK(fired[k]->scene == INTRO_TITLE);
            music = music || fired[k]->kind == CUE_MUSIC;
        }
    }
    CHECK(music);
}

static void test_captions_type_then_fade(void)
{
    Intro intro;
    intro_start(&intro, INTRO_FULL);
    char buf[160];
    float alpha;
    bool dialog;
    CHECK(!intro_caption(&intro, buf, sizeof(buf), &alpha, &dialog)); /* Scene 1 has none */
    const IntroCue *fired[8];
    intro_update(&intro, intro_scene_length(INTRO_REC) + 1.05f, false, fired, 8);
    CHECK(intro_scene(&intro, NULL) == INTRO_MONITORS);
    CHECK(intro_caption(&intro, buf, sizeof(buf), &alpha, &dialog));
    size_t early = strlen(buf);
    CHECK(early > 0 && early < strlen(intro_caption_text(INTRO_MONITORS)));
    intro_update(&intro, 5.0f, false, fired, 8);
    CHECK(intro_caption(&intro, buf, sizeof(buf), &alpha, &dialog));
    CHECK(strcmp(buf, intro_caption_text(INTRO_MONITORS)) == 0); /* Whole by now */
    CHECK(alpha == 1.0f && !dialog);
    /* Cut in the middle of a letter? Never: "días" types whole. */
    for (float t = 0.0f; t < 6.0f; t += 0.01f) {
        Intro town = intro;
        town.time = 0.0f;
        for (int s = 0; s < INTRO_TOWN; s++)
            town.time += intro_scene_length((IntroScene)s);
        town.time += t;
        if (intro_caption(&town, buf, sizeof(buf), &alpha, &dialog)) {
            size_t n = strlen(buf);
            CHECK(n == 0 || ((unsigned char)buf[n - 1] & 0xC0) != 0xC0);
        }
    }
}

static void test_dialog_is_marked(void)
{
    Intro intro;
    intro_start(&intro, INTRO_FULL);
    for (int s = 0; s < INTRO_SAMPLE; s++)
        intro.time += intro_scene_length((IntroScene)s);
    intro.time += 3.0f;
    char buf[64];
    float alpha;
    bool dialog = false;
    CHECK(intro_caption(&intro, buf, sizeof(buf), &alpha, &dialog));
    CHECK(dialog);
}

static void test_fades_reach_black_between_scenes(void)
{
    Intro intro;
    intro_start(&intro, INTRO_FULL);
    float start_town = 0.0f;
    for (int s = 0; s < INTRO_TOWN; s++)
        start_town += intro_scene_length((IntroScene)s);
    intro.time = start_town - 0.001f;
    CHECK(intro_black(&intro) > 0.95f);
    intro.time = start_town + 0.001f;
    CHECK(intro_black(&intro) > 0.95f);
    intro.time = start_town + 3.0f;
    CHECK(intro_black(&intro) == 0.0f);
    /* The last scene doesn't fade out: it becomes the title screen. */
    intro.time = intro_total_length() - 0.01f;
    CHECK(intro_black(&intro) == 0.0f);
}

int main(void)
{
    printf("intro:\n");
    RUN(test_full_plays_every_scene_in_order);
    RUN(test_length_fits_the_script);
    RUN(test_cues_are_in_order_and_inside_their_scene);
    RUN(test_skip_ends_at_once_without_noises);
    RUN(test_short_is_only_the_title_with_its_music);
    RUN(test_captions_type_then_fade);
    RUN(test_dialog_is_marked);
    RUN(test_fades_reach_black_between_scenes);
    return TEST_EXIT();
}
