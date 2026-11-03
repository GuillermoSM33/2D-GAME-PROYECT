#ifndef GAME_SCENE_H
#define GAME_SCENE_H

#include <SDL.h>

#include "game/world.h"

/* The landscape for a camera at camera_x: the world's theme's background
 * layers, each scrolled by its parallax, the loaded chunks' props in the
 * theme's colors, and its fog, which drifts with time (seconds). */
void scene_draw(SDL_Renderer *renderer, const World *world, float camera_x, double time);

/* Rivers on the road (world x of their middles, half widths): the houses in
 * the back are left out wherever one would stand over a river on screen. */
void scene_set_rivers(const float *xs, int count, float half);

/* Frees the theme's recolored props. */
void scene_shutdown(void);

/* The color of the sky's top row: the band above the view is filled with it. */
unsigned scene_sky_top(const ThemeDef *theme);

#endif
