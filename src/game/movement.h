#ifndef GAME_MOVEMENT_H
#define GAME_MOVEMENT_H

#include <stdbool.h>

/* Horizontal walk/run step. dir is -1, 0 or +1. The result keeps the whole
 * sprite inside the world. */
float movement_step(float x, int dir, bool run, float dt);

float movement_min_x(void);
float movement_max_x(void);

#endif
