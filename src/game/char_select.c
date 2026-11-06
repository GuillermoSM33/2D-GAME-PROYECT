#include "game/char_select.h"

#include "config.h"
#include "game/characters.h"

void char_select_init(CharSelect *select, int selected)
{
    select->selected = selected >= 0 && selected < CHARACTER_COUNT ? selected : 0;
    select->notice_time = 0.0f;
    select->denied = false;
}

int char_select_update(CharSelect *select, const InputState *input)
{
    select->denied = false;
    if (input->pressed[ACTION_LEFT])
        select->selected = (select->selected + CHARACTER_COUNT - 1) % CHARACTER_COUNT;
    if (input->pressed[ACTION_RIGHT])
        select->selected = (select->selected + 1) % CHARACTER_COUNT;
    bool in_development = CHARACTERS[select->selected].in_development;
    /* The mouse also moves selected, before this update. */
    select->notice_time = in_development && select->notice_time > FIXED_DT
                              ? select->notice_time - FIXED_DT : 0.0f;
    if (!input->pressed[ACTION_CONFIRM])
        return -1;
    if (in_development) {
        select->denied = true;
        select->notice_time = CHAR_SELECT_NOTICE_TIME;
        return -1;
    }
    return select->selected;
}
