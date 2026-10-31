#ifndef ENGINE_INPUT_H
#define ENGINE_INPUT_H

#include <stdbool.h>

/* Game actions, independent of the physical keys bound to them. */
typedef enum {
    ACTION_LEFT,
    ACTION_RIGHT,
    ACTION_RUN,
    ACTION_JUMP,
    ACTION_SHOOT,
    ACTION_RESET,
    ACTION_QUIT,
    ACTION_COUNT
} Action;

typedef struct {
    bool down[ACTION_COUNT];
    bool pressed[ACTION_COUNT];  /* Went down this update */
    bool released[ACTION_COUNT]; /* Went up this update */
    int last_horizontal;         /* -1 left, +1 right: the most recently pressed */
} InputState;

void input_init(InputState *input);

/* Feed the current down/up state of every action once per update.
 * Edges (pressed/released) are derived from the previous call. */
void input_update(InputState *input, const bool down[ACTION_COUNT]);

/* -1, 0 or +1. When left and right are both held, the last pressed wins. */
int input_horizontal(const InputState *input);

#endif
