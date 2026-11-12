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
    ACTION_RELOAD,  /* A new magazine now; after a defeat, retry the stage */
    ACTION_QUIT,    /* Back one screen; in a stage, the pause menu */
    ACTION_UP,      /* Menus */
    ACTION_DOWN,
    ACTION_CONFIRM,
    ACTION_SWAP,    /* Switch guns (the SWAT) */
    ACTION_USE,     /* Light a charge on a wall */
    ACTION_VAULT,   /* Leap over a low barricade */
    ACTION_POWER,   /* The level-3 power: a grenade, a ricochet shot */
    ACTION_MELEE,   /* A blow with the gun */
    ACTION_BANDAGE, /* Held: stop the bleeding */
    ACTION_ALMANAC, /* Field guide of encountered zombie types */
    ACTION_LIGHT,   /* Toggle the hand-held night light */
    ACTION_FIRE_MODE, /* Bursts or single shots (the SWAT's rifle) */
    ACTION_COUNT
} Action;

typedef struct {
    bool down[ACTION_COUNT];
    bool pressed[ACTION_COUNT];  /* Went down this update */
    bool released[ACTION_COUNT]; /* Went up this update */
    int last_horizontal;         /* -1 left, +1 right: the most recently pressed */
    /* The mouse, in window coordinates (platform_read_pointer): where it is,
     * whether it moved and whether the left button was clicked since the
     * previous read. */
    int pointer_x, pointer_y;
    bool pointer_moved, pointer_clicked;
    int wheel; /* Notches the mouse wheel turned since the last read: + up (away), - down */
} InputState;

void input_init(InputState *input);

/* Feed the current down/up state of every action once per update.
 * Edges (pressed/released) are derived from the previous call. */
void input_update(InputState *input, const bool down[ACTION_COUNT]);

/* -1, 0 or +1. When left and right are both held, the last pressed wins. */
int input_horizontal(const InputState *input);

#endif
