#ifndef GAME_ZOMBIE_RENDER_H
#define GAME_ZOMBIE_RENDER_H

#include <SDL.h>

#include "game/zombie.h"

/* The zombie, fading out once dead, and its health bar once damaged. */
void zombie_render(SDL_Renderer *renderer, const Zombie *zombie, float camera_x);

/* Resolve the requested sheet, retaining the original enemy art if a new
 * authoring sheet is absent. Also clamps the source frame to the real strip.
 * Shared with the field guide so an incomplete skin cannot become invisible. */
SDL_Texture *zombie_animation_texture(const AnimationDef *animation, int *frame);

#endif
