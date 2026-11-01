#ifndef GAME_CHAR_SELECT_H
#define GAME_CHAR_SELECT_H

#include "engine/input.h"

/* "Elige tu personaje": left and right move over the characters (it wraps
 * around), confirm picks one. */
typedef struct {
    int selected;
} CharSelect;

void char_select_init(CharSelect *select, int selected);

/* Returns the character picked on this update, or -1. */
int char_select_update(CharSelect *select, const InputState *input);

#endif
