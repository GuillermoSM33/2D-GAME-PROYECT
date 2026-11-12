#ifndef GAME_MENU_H
#define GAME_MENU_H

#include "engine/input.h"
#include "game/stages.h"

/* Stage select, a page per phase (route): FASE 1 the desert town, FASE 2
 * the city. Up, down and the mouse wheel move over every stage (locked ones
 * show why they can't be played), turning the page at a phase's end; left
 * and right turn it too. Confirm starts the selected one if it is open. */
#define PHASE_STAGES 5
#define PHASE_COUNT ((STAGE_COUNT + PHASE_STAGES - 1) / PHASE_STAGES)

typedef struct {
    int selected;
    int backdrop; /* The phase whose landscape drifts behind the menus (one she has reached) */
} Menu;

/* Selects the furthest stage she can play; the backdrop, that stage's phase. */
void menu_init(Menu *menu, const StageRecord *record);

/* Returns the stage to start, or -1. */
int menu_update(Menu *menu, const InputState *input, const StageRecord *record);

int menu_phase(int stage);
/* The furthest phase she has reached: its first stage is open. */
int menu_reached_phase(const StageRecord *record);
/* Shows a phase's page: its first stage, or the same row as now. */
void menu_show_phase(Menu *menu, int phase);
/* The backdrop to the next phase she has reached (round to the first). */
void menu_next_backdrop(Menu *menu, const StageRecord *record);

#endif
