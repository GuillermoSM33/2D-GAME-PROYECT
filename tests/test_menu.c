#include <string.h>

#include "game/menu.h"
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

int main(void)
{
    printf("test_menu\n");
    RUN(test_starts_on_furthest_open_stage);
    RUN(test_moves_and_starts_only_open_stages);
    return TEST_EXIT();
}
