#include <string.h>

#include "game/casefile.h"
#include "test.h"

static InputState press(Action action)
{
    InputState input;
    input_init(&input);
    input.pressed[action] = true;
    return input;
}

static void test_every_stage_has_one_clue_of_each_source(void)
{
    for (int stage = 0; stage < 5; stage++) {
        int mission = 0, zombie = 0, crate = 0;
        for (int c = 0; c < CLUE_COUNT; c++) {
            if (CLUES[c].stage != stage)
                continue;
            mission += CLUES[c].source == CLUE_FROM_MISSION;
            zombie += CLUES[c].source == CLUE_FROM_ZOMBIE;
            crate += CLUES[c].source == CLUE_FROM_CRATE;
        }
        CHECK(mission == 1 && zombie == 1 && crate == 1);
        CHECK(casefile_mission_clue(stage) >= 0);
    }
}

static void test_cases_are_whole_and_answerable(void)
{
    int total = 0;
    for (int k = 0; k < CASE_COUNT; k++) {
        int n = casefile_case_clues(k, NULL);
        CHECK(n >= 3 && n <= CASE_MAX_CLUES);
        total += n;
        CHECK(CASES[k].answer >= 0 && CASES[k].answer < CASE_OPTIONS);
        CHECK(CASES[k].report_title[0] && strstr(CASES[k].report, "\n\n") != NULL);
        for (int o = 0; o < CASE_OPTIONS; o++)
            CHECK(CASES[k].options[o] && CASES[k].options[o][0]);
    }
    CHECK(total == CLUE_COUNT);
    for (int c = 0; c < CLUE_COUNT; c++)
        CHECK(CLUES[c].title[0] && strlen(CLUES[c].text) > 20);
}

static void test_sources_find_the_right_clue(void)
{
    /* 1-1: the press card in the crate at 0.46 of the road, tape 1 on its fourth zombie. */
    CHECK(casefile_crate_clue(0, 0.46f) == 1);
    CHECK(casefile_crate_clue(0, 0.47f) == 1);
    CHECK(casefile_crate_clue(0, 0.09f) == -1); /* Other crates hold their usual loot */
    CHECK(casefile_zombie_clue(0, 3, 8) == 2);
    CHECK(casefile_zombie_clue(0, 2, 8) == -1);
    /* A route shorter than the script: its last zombie carries it. */
    CHECK(casefile_zombie_clue(4, 2, 3) == casefile_zombie_clue(4, 2, 3));
    CHECK(casefile_zombie_clue(4, 2, 3) >= 0);
}

static void test_answers_only_once_everything_is_in(void)
{
    CaseFile file;
    casefile_init(&file);
    int ids[CASE_MAX_CLUES];
    int n = casefile_case_clues(2, ids);
    CHECK(!casefile_ready(&file, 2));
    CHECK(!casefile_answer(&file, 2, CASES[2].answer)); /* Not with clues missing */
    for (int k = 0; k < n; k++) {
        CHECK(casefile_take(&file, ids[k]));
        CHECK(!casefile_take(&file, ids[k])); /* Only new once */
    }
    CHECK(casefile_ready(&file, 2));
    CHECK(!casefile_answer(&file, 2, (CASES[2].answer + 1) % CASE_OPTIONS)); /* Wrong: still open */
    CHECK(casefile_ready(&file, 2));
    CHECK(casefile_answer(&file, 2, CASES[2].answer));
    CHECK(casefile_solved(&file, 2) && !casefile_ready(&file, 2));
    CHECK(casefile_stage_found(&file, 3) == 3);
}

static void test_board_asks_and_reveals(void)
{
    CaseFile file;
    casefile_init(&file);
    int ids[CASE_MAX_CLUES];
    int n = casefile_case_clues(1, ids);
    for (int k = 0; k < n; k++)
        casefile_take(&file, ids[k]);
    BoardView view;
    board_view_init(&view);
    InputState down = press(ACTION_DOWN);
    board_view_update(&view, &file, &down, 0.016f);
    CHECK(view.row == 1 && board_selected_clue(&view) == ids[0]);
    InputState left = press(ACTION_LEFT); /* Wraps onto the question's slot */
    board_view_update(&view, &file, &left, 0.016f);
    CHECK(board_selected_clue(&view) == -1);
    InputState enter = press(ACTION_CONFIRM);
    board_view_update(&view, &file, &enter, 0.016f);
    CHECK(view.asking);
    view.option = (CASES[1].answer + 1) % CASE_OPTIONS;
    CHECK(board_view_update(&view, &file, &enter, 0.016f) == BOARD_STAY && view.wrong_time > 0.0f);
    view.option = CASES[1].answer;
    CHECK(board_view_update(&view, &file, &enter, 0.016f) == BOARD_REVEAL && view.revealed == 1);
    InputState esc = press(ACTION_QUIT);
    CHECK(board_view_update(&view, &file, &esc, 0.016f) == BOARD_BACK);
}

static void test_board_examines_found_clues_only(void)
{
    CaseFile file;
    casefile_init(&file);
    BoardView view;
    board_view_init(&view);
    InputState enter = press(ACTION_CONFIRM);
    CHECK(board_view_update(&view, &file, &enter, 0.016f) == BOARD_STAY); /* Not found yet */
    casefile_take(&file, 0);
    CHECK(board_view_update(&view, &file, &enter, 0.016f) == BOARD_EXAMINE && view.examined == 0);
    ClueExam exam;
    exam_open(&exam, 0);
    CHECK(exam_update(&exam, &enter, 0.1f)); /* The click that opened it */
    CHECK(!exam_update(&exam, &enter, 0.2f));
    for (int c = 0; c < CLUE_COUNT; c++)
        CHECK(CLUES[c].examine && strlen(CLUES[c].examine) > 60);
}

static void test_board_will_not_ask_an_open_case(void)
{
    CaseFile file;
    casefile_init(&file);
    BoardView view;
    board_view_init(&view);
    view.col = casefile_case_clues(0, NULL);
    InputState enter = press(ACTION_CONFIRM);
    board_view_update(&view, &file, &enter, 0.016f);
    CHECK(!view.asking);
}

static void test_story_types_lines_and_ends(void)
{
    const StoryBeat *beat = story_after_stage(1);
    CHECK(beat != NULL && beat->count > 0);
    CHECK(story_after_stage(0) == NULL);
    Story story;
    story_start(&story, beat);
    char buf[128];
    float alpha;
    CHECK(!story_caption(&story, buf, sizeof(buf), &alpha)); /* A breath before it types */
    story_update(&story, false, false, 1.0f);
    CHECK(story_caption(&story, buf, sizeof(buf), &alpha) && strlen(buf) > 0 &&
          strlen(buf) < strlen(beat->lines[0]));
    story_update(&story, true, false, 0.0f); /* Enter: the whole line */
    CHECK(story_caption(&story, buf, sizeof(buf), &alpha) && strcmp(buf, beat->lines[0]) == 0);
    story_update(&story, true, false, 0.0f); /* Enter again: the next */
    CHECK(story.line == 1);
    for (int i = 0; i < 2000 && !story.done; i++)
        story_update(&story, false, false, 0.05f);
    CHECK(story.done);
    story_start(&story, beat);
    story_update(&story, false, true, 0.0f); /* Esc ends it */
    CHECK(story.done);
}

static void test_report_stamps_once_and_closes(void)
{
    Report report;
    report_open(&report, 2);
    InputState none, enter = press(ACTION_CONFIRM);
    input_init(&none);
    bool stamped, stamps = 0;
    CHECK(report_update(&report, &enter, 0.1f, &stamped)); /* Too soon: the answering click */
    for (int i = 0; i < 60; i++) {
        report_update(&report, &none, 0.02f, &stamped);
        stamps += stamped;
    }
    CHECK(stamps == 1);
    CHECK(!report_update(&report, &enter, 0.02f, &stamped));
}

static void test_tapes_unlock_with_stage_endings(void)
{
    CaseFile file;
    casefile_init(&file);
    CHECK(tape_unlocked(&file, TAPE_INTRO) && tapes_unlocked(&file) == 1);
    for (int t = 1; t < TAPE_COUNT; t++)
        CHECK(story_after_stage(TAPES[t].stage) != NULL); /* Every tape has its beat */
    file.beats_seen |= 1u << TAPES[2].stage;
    CHECK(tape_unlocked(&file, 2) && !tape_unlocked(&file, 1) && tapes_unlocked(&file) == 2);
    TapeView view = {1};
    InputState enter = press(ACTION_CONFIRM);
    CHECK(tape_view_update(&view, &file, &enter) == -1); /* Locked: nothing */
    view.selected = 2;
    CHECK(tape_view_update(&view, &file, &enter) == 2);
    InputState esc = press(ACTION_QUIT);
    CHECK(tape_view_update(&view, &file, &esc) == TAPE_BACK);
}

int main(void)
{
    printf("casefile:\n");
    RUN(test_every_stage_has_one_clue_of_each_source);
    RUN(test_cases_are_whole_and_answerable);
    RUN(test_sources_find_the_right_clue);
    RUN(test_answers_only_once_everything_is_in);
    RUN(test_board_asks_and_reveals);
    RUN(test_board_examines_found_clues_only);
    RUN(test_board_will_not_ask_an_open_case);
    RUN(test_story_types_lines_and_ends);
    RUN(test_report_stamps_once_and_closes);
    RUN(test_tapes_unlock_with_stage_endings);
    return TEST_EXIT();
}
