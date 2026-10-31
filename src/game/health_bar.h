#ifndef GAME_HEALTH_BAR_H
#define GAME_HEALTH_BAR_H

#include <stdbool.h>

#include <SDL.h>

/* A health bar with its top-left corner at (x, y), filled to health / max.
 * Armored bodies get a steel frame around it. */
void health_bar_draw(SDL_Renderer *renderer, int x, int y, int w, int h,
                     int health, int max, bool armored);

#endif
