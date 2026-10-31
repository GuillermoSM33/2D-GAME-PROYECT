#include "engine/input.h"

#include <string.h>

void input_init(InputState *input)
{
    memset(input, 0, sizeof(*input));
    input->last_horizontal = 1;
}

void input_update(InputState *input, const bool down[ACTION_COUNT])
{
    for (int i = 0; i < ACTION_COUNT; i++) {
        input->pressed[i] = down[i] && !input->down[i];
        input->released[i] = !down[i] && input->down[i];
        input->down[i] = down[i];
    }
    /* If both arrive in the same update, right wins (arbitrary but stable). */
    if (input->pressed[ACTION_LEFT])
        input->last_horizontal = -1;
    if (input->pressed[ACTION_RIGHT])
        input->last_horizontal = 1;
}

int input_horizontal(const InputState *input)
{
    bool left = input->down[ACTION_LEFT];
    bool right = input->down[ACTION_RIGHT];
    if (left && right)
        return input->last_horizontal;
    return (int)right - (int)left;
}
