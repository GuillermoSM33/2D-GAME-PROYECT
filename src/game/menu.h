#ifndef GAME_MENU_H
#define GAME_MENU_H

#include "engine/input.h"
#include "game/stages.h"

/* Stage select. Up and down move over every stage (locked ones show why
 * they can't be played); confirm starts the selected one if it is open. */
typedef struct {
    int selected;
} Menu;

/* Selects the furthest stage she can play. */
void menu_init(Menu *menu, const StageRecord *record);

/* Returns the stage to start, or -1. */
int menu_update(Menu *menu, const InputState *input, const StageRecord *record);

#endif
