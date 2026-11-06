#ifndef GAME_CHAR_SELECT_H
#define GAME_CHAR_SELECT_H

#include <stdbool.h>

#include "engine/input.h"

/* How long the "in development" notice stays up, in seconds. */
#define CHAR_SELECT_NOTICE_TIME 3.0f

/* "Elige tu personaje": left and right move over the characters (it wraps
 * around), confirm picks one. Confirming one still in development picks
 * nothing and raises a notice instead. */
typedef struct {
    int selected;
    float notice_time; /* Seconds left of the notice; it goes away on leaving that card */
    bool denied;       /* This update's confirm was refused */
} CharSelect;

void char_select_init(CharSelect *select, int selected);

/* Returns the character picked on this update, or -1. Call once per fixed step. */
int char_select_update(CharSelect *select, const InputState *input);

#endif
