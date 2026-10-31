#ifndef GAME_EFFECTS_H
#define GAME_EFFECTS_H

#include <stdbool.h>

#include "engine/animation.h"

#define EFFECT_MAX 16

/* A one-shot animation drawn at a point, gone when it finishes. */
typedef struct {
    bool active;
    float x, y; /* Window position of the animation's pivot */
    int facing; /* -1 mirrors the art */
    Animation anim;
} Effect;

typedef struct {
    Effect items[EFFECT_MAX];
} Effects;

void effects_clear(Effects *effects);

/* Returns false when the pool is full (the effect is skipped). */
bool effects_spawn(Effects *effects, const AnimationDef *def, float x, float y, int facing);

void effects_update(Effects *effects, float dt);

int effects_active_count(const Effects *effects);

/* Sparks of a bullet hitting armor. */
const AnimationDef *effect_sparks(void);

#endif
