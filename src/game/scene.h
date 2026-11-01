#ifndef GAME_SCENE_H
#define GAME_SCENE_H

#include <SDL.h>

#include "game/world.h"

/* The landscape for a camera at camera_x: the world's theme's background
 * layers, each scrolled by its parallax, the loaded chunks' props in the
 * theme's colors, and its fog, which drifts with time (seconds). */
void scene_draw(SDL_Renderer *renderer, const World *world, float camera_x, double time);

/* Frees the theme's recolored props. */
void scene_shutdown(void);

#endif
