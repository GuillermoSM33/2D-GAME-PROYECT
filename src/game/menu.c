#include "game/menu.h"

int menu_phase(int stage)
{
    return stage / PHASE_STAGES;
}

int menu_reached_phase(const StageRecord *record)
{
    int phase = 0;
    while (phase + 1 < PHASE_COUNT && stage_unlocked(record, (phase + 1) * PHASE_STAGES))
        phase++;
    return phase;
}

void menu_init(Menu *menu, const StageRecord *record)
{
    menu->selected = 0;
    while (menu->selected + 1 < STAGE_COUNT && stage_unlocked(record, menu->selected + 1))
        menu->selected++;
    menu->backdrop = menu_phase(menu->selected);
}

void menu_show_phase(Menu *menu, int phase)
{
    if (phase < 0 || phase >= PHASE_COUNT || phase == menu_phase(menu->selected))
        return;
    int stage = phase * PHASE_STAGES + menu->selected % PHASE_STAGES;
    menu->selected = stage < STAGE_COUNT ? stage : STAGE_COUNT - 1;
}

void menu_next_backdrop(Menu *menu, const StageRecord *record)
{
    menu->backdrop = (menu->backdrop + 1) % (menu_reached_phase(record) + 1);
}

int menu_update(Menu *menu, const InputState *input, const StageRecord *record)
{
    int step = (input->pressed[ACTION_DOWN] ? 1 : 0) - (input->pressed[ACTION_UP] ? 1 : 0);
    step -= input->wheel > 0 ? 1 : input->wheel < 0 ? -1 : 0; /* Wheel up: the stage above */
    if (step < 0 && menu->selected > 0)
        menu->selected--;
    if (step > 0 && menu->selected + 1 < STAGE_COUNT)
        menu->selected++;
    if (input->pressed[ACTION_LEFT])
        menu_show_phase(menu, menu_phase(menu->selected) - 1);
    if (input->pressed[ACTION_RIGHT])
        menu_show_phase(menu, menu_phase(menu->selected) + 1);
    if (menu->backdrop > menu_reached_phase(record))
        menu->backdrop = menu_reached_phase(record);
    if (input->pressed[ACTION_CONFIRM] && stage_unlocked(record, menu->selected))
        return menu->selected;
    return -1;
}
