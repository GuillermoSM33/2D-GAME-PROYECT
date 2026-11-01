#include "game/menu.h"

void menu_init(Menu *menu, const StageRecord *record)
{
    menu->selected = 0;
    while (menu->selected + 1 < STAGE_COUNT && stage_unlocked(record, menu->selected + 1))
        menu->selected++;
}

int menu_update(Menu *menu, const InputState *input, const StageRecord *record)
{
    if (input->pressed[ACTION_UP] && menu->selected > 0)
        menu->selected--;
    if (input->pressed[ACTION_DOWN] && menu->selected + 1 < STAGE_COUNT)
        menu->selected++;
    if (input->pressed[ACTION_CONFIRM] && stage_unlocked(record, menu->selected))
        return menu->selected;
    return -1;
}
