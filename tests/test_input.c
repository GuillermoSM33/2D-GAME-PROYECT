#include <stdbool.h>
#include <string.h>

#include "engine/input.h"
#include "test.h"

static void feed(InputState *input, bool left, bool right)
{
    bool down[ACTION_COUNT];
    memset(down, 0, sizeof(down));
    down[ACTION_LEFT] = left;
    down[ACTION_RIGHT] = right;
    input_update(input, down);
}

static void test_edges(void)
{
    InputState input;
    input_init(&input);
    feed(&input, false, true);
    CHECK(input.pressed[ACTION_RIGHT]);
    CHECK(input.down[ACTION_RIGHT]);
    feed(&input, false, true);
    CHECK(!input.pressed[ACTION_RIGHT]); /* Held, not a new press */
    feed(&input, false, false);
    CHECK(input.released[ACTION_RIGHT]);
    CHECK(!input.down[ACTION_RIGHT]);
}

static void test_single_direction(void)
{
    InputState input;
    input_init(&input);
    CHECK(input_horizontal(&input) == 0);
    feed(&input, true, false);
    CHECK(input_horizontal(&input) == -1);
    feed(&input, false, true);
    CHECK(input_horizontal(&input) == 1);
}

static void test_last_pressed_wins(void)
{
    InputState input;
    input_init(&input);
    feed(&input, false, true);
    feed(&input, true, true); /* Left pressed while holding right */
    CHECK(input_horizontal(&input) == -1);
    feed(&input, false, true); /* Left released: back to right */
    CHECK(input_horizontal(&input) == 1);
    feed(&input, true, true);
    feed(&input, true, false); /* Right released: left keeps going */
    CHECK(input_horizontal(&input) == -1);
}

int main(void)
{
    printf("test_input\n");
    RUN(test_edges);
    RUN(test_single_direction);
    RUN(test_last_pressed_wins);
    return TEST_EXIT();
}
