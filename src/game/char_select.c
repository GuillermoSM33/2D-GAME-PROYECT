#include "game/char_select.h"

#include "game/characters.h"

void char_select_init(CharSelect *select, int selected)
{
    select->selected = selected >= 0 && selected < CHARACTER_COUNT ? selected : 0;
}

int char_select_update(CharSelect *select, const InputState *input)
{
    if (input->pressed[ACTION_LEFT])
        select->selected = (select->selected + CHARACTER_COUNT - 1) % CHARACTER_COUNT;
    if (input->pressed[ACTION_RIGHT])
        select->selected = (select->selected + 1) % CHARACTER_COUNT;
    if (input->pressed[ACTION_CONFIRM])
        return select->selected;
    return -1;
}
