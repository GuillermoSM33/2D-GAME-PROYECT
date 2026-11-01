#ifndef GAME_CHEST_H
#define GAME_CHEST_H

#include <stdbool.h>

#include "engine/animation.h"

/* A reward chest left where a zombie fell. It opens when she walks up to it,
 * stays open a moment, then fades away. */
typedef enum {
    CHEST_NONE,    /* Not in the world */
    CHEST_CLOSED,  /* Waiting for her */
    CHEST_OPENING, /* Lid lifting (sheet frames 0-5) */
    CHEST_OPEN,
    CHEST_FADING
} ChestState;

typedef struct {
    ChestState state;
    float x;        /* World px, center */
    float time;     /* Seconds in the current state */
    int reward_xp;
    bool just_opened; /* On the update it starts opening: grant the reward */
    Animation anim;
} Chest;

void chest_clear(Chest *chest);
void chest_place(Chest *chest, float x, int reward_xp);
void chest_update(Chest *chest, float player_x, bool player_alive, float dt);

bool chest_present(const Chest *chest);
float chest_opacity(const Chest *chest);

const AnimationDef *chest_animation(void);

/* Sparks bursting out as it opens: a one-shot effect at (x, BASELINE). */
const AnimationDef *chest_sparks(void);

#endif
