#ifndef GAME_ZOMBIE_RENDER_H
#define GAME_ZOMBIE_RENDER_H

#include <SDL.h>

#include "game/zombie.h"

/* The zombie, fading out once dead, and its health bar once damaged. */
void zombie_render(SDL_Renderer *renderer, const Zombie *zombie);

#endif
