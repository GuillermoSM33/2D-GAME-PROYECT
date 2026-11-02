#include "game/settings.h"

#include <stddef.h>

void volumes_init(Volumes *volumes)
{
    volumes->master = 8;
    volumes->player = VOLUME_STEPS;
    volumes->zombie = VOLUME_STEPS;
}

void list_menu_init(ListMenu *menu, int count)
{
    menu->selected = 0;
    menu->count = count > 0 ? count : 1;
}

int list_menu_update(ListMenu *menu, const InputState *input)
{
    if (input->pressed[ACTION_UP])
        menu->selected = (menu->selected + menu->count - 1) % menu->count;
    if (input->pressed[ACTION_DOWN])
        menu->selected = (menu->selected + 1) % menu->count;
    return input->pressed[ACTION_CONFIRM] ? menu->selected : -1;
}

static int *volume_of(Volumes *volumes, int row)
{
    switch (row) {
    case VOLUME_MASTER: return &volumes->master;
    case VOLUME_PLAYER: return &volumes->player;
    case VOLUME_ZOMBIE: return &volumes->zombie;
    default: return NULL;
    }
}

int volume_menu_update(ListMenu *menu, Volumes *volumes, const InputState *input)
{
    if (input->pressed[ACTION_QUIT])
        return VOLUME_BACK;
    int chosen = list_menu_update(menu, input);
    if (chosen == VOLUME_BACK)
        return VOLUME_BACK;
    int *volume = volume_of(volumes, menu->selected);
    if (volume == NULL)
        return -1;
    int step = (input->pressed[ACTION_RIGHT] ? 1 : 0) - (input->pressed[ACTION_LEFT] ? 1 : 0);
    int next = *volume + step;
    if (step == 0 || next < 0 || next > VOLUME_STEPS)
        return -1;
    *volume = next;
    return menu->selected;
}

bool volume_set(Volumes *volumes, int row, int value)
{
    int *volume = volume_of(volumes, row);
    value = value < 0 ? 0 : value > VOLUME_STEPS ? VOLUME_STEPS : value;
    if (volume == NULL || *volume == value)
        return false;
    *volume = value;
    return true;
}

float volume_share(int steps)
{
    return (float)steps / (float)VOLUME_STEPS;
}
