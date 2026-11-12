#include <string.h>

#include "game/menu.h"
#include "game/settings.h"
#include "test.h"

static InputState press(Action action)
{
    InputState input;
    input_init(&input);
    input.pressed[action] = true;
    return input;
}

static void test_starts_on_furthest_open_stage(void)
{
    StageRecord record;
    stage_record_init(&record);
    Menu menu;
    menu_init(&menu, &record);
    CHECK(menu.selected == 0);
    record.cleared[0] = record.cleared[1] = true;
    menu_init(&menu, &record);
    CHECK(menu.selected == 2);
}

static void test_moves_and_starts_only_open_stages(void)
{
    StageRecord record;
    stage_record_init(&record);
    Menu menu;
    menu_init(&menu, &record);
    InputState up = press(ACTION_UP), down = press(ACTION_DOWN), ok = press(ACTION_CONFIRM);
    CHECK(menu_update(&menu, &up, &record) == -1 && menu.selected == 0); /* Stays at the top */
    CHECK(menu_update(&menu, &down, &record) == -1 && menu.selected == 1);
    CHECK(menu_update(&menu, &ok, &record) == -1); /* 1-2 is locked */
    CHECK(menu_update(&menu, &up, &record) == -1 && menu.selected == 0);
    CHECK(menu_update(&menu, &ok, &record) == 0);
    for (int i = 0; i < 10; i++)
        menu_update(&menu, &down, &record);
    CHECK(menu.selected == STAGE_COUNT - 1); /* Stays at the bottom */
}

/* A page per phase: the wheel walks the stages like W/S, A/D turn the page,
 * and the backdrop is any phase she has reached. */
static void test_phases_wheel_and_backdrop(void)
{
    StageRecord record;
    stage_record_init(&record);
    Menu menu;
    menu_init(&menu, &record);
    CHECK(PHASE_COUNT == 2 && menu_phase(4) == 0 && menu_phase(5) == 1 && menu.backdrop == 0);
    InputState wheel;
    input_init(&wheel);
    wheel.wheel = -1; /* Down a notch: the next stage */
    CHECK(menu_update(&menu, &wheel, &record) == -1 && menu.selected == 1);
    wheel.wheel = 1;
    CHECK(menu_update(&menu, &wheel, &record) == -1 && menu.selected == 0);
    InputState right = press(ACTION_RIGHT), left = press(ACTION_LEFT);
    menu.selected = 2;
    menu_update(&menu, &right, &record);
    CHECK(menu.selected == 7); /* The same row of the next phase */
    menu_update(&menu, &left, &record);
    CHECK(menu.selected == 2);
    CHECK(menu_reached_phase(&record) == 0);
    menu_next_backdrop(&menu, &record);
    CHECK(menu.backdrop == 0); /* Nothing else reached yet */
    for (int s = 0; s < 5; s++)
        record.cleared[s] = true;
    CHECK(menu_reached_phase(&record) == 1);
    menu_init(&menu, &record);
    CHECK(menu.selected == 5 && menu.backdrop == 1);
    menu_next_backdrop(&menu, &record);
    CHECK(menu.backdrop == 0);
    menu_next_backdrop(&menu, &record);
    CHECK(menu.backdrop == 1);
}

static void test_fullscreen_row_switches_display(void)
{
    Volumes volumes;
    volumes_init(&volumes);
    ListMenu options;
    list_menu_init(&options, VOLUME_ROWS);
    options.selected = VOLUME_FULLSCREEN;
    CHECK(!volumes.fullscreen); /* Starts in a window */
    InputState input = press(ACTION_RIGHT);
    CHECK(volume_menu_update(&options, &volumes, &input) == VOLUME_FULLSCREEN);
    CHECK(volumes.fullscreen);
    input = press(ACTION_CONFIRM);
    CHECK(volume_menu_update(&options, &volumes, &input) == VOLUME_FULLSCREEN);
    CHECK(!volumes.fullscreen);
    input = press(ACTION_LEFT);
    CHECK(volume_menu_update(&options, &volumes, &input) == VOLUME_FULLSCREEN);
    CHECK(volumes.fullscreen);
    CHECK(volumes.master == 8 && volumes.player == VOLUME_STEPS); /* Volumes untouched */
    CHECK(!volume_set(&volumes, VOLUME_FULLSCREEN, 1)); /* Not a volume */
    CHECK(volume_set(&volumes, VOLUME_MUSIC, 3) && volumes.music == 3);
}

static void test_options_still_reach_back(void)
{
    Volumes volumes;
    volumes_init(&volumes);
    ListMenu options;
    list_menu_init(&options, VOLUME_ROWS);
    options.selected = VOLUME_FULLSCREEN;
    InputState input = press(ACTION_DOWN);
    CHECK(volume_menu_update(&options, &volumes, &input) == -1);
    CHECK(options.selected == VOLUME_BACK);
    CHECK(!volumes.fullscreen);
    input = press(ACTION_CONFIRM);
    CHECK(volume_menu_update(&options, &volumes, &input) == VOLUME_BACK);
}

int main(void)
{
    printf("test_menu\n");
    RUN(test_starts_on_furthest_open_stage);
    RUN(test_moves_and_starts_only_open_stages);
    RUN(test_phases_wheel_and_backdrop);
    RUN(test_fullscreen_row_switches_display);
    RUN(test_options_still_reach_back);
    return TEST_EXIT();
}
