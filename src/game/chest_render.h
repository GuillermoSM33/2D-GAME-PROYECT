#ifndef GAME_CHEST_RENDER_H
#define GAME_CHEST_RENDER_H

#include <SDL.h>

#include "game/chest.h"

void chest_render(SDL_Renderer *renderer, const Chest *chest, float camera_x);

#endif
