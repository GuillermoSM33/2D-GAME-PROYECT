#ifndef GAME_TERRAIN_RENDER_H
#define GAME_TERRAIN_RENDER_H

#include <SDL.h>

#include "game/terrain.h"

/* The road's pieces in view, standing on the ground line (a blown barrel is
 * gone; a wrecked barricade and an empty wagon stay). */
void terrain_render(SDL_Renderer *renderer, const Terrain *terrain, float camera_x);

/* Warm light round lamps, burning oil and campfires, added over everything
 * drawn so far and flickering with time. */
void terrain_render_lights(SDL_Renderer *renderer, const Terrain *terrain, float camera_x, double time);

#endif
