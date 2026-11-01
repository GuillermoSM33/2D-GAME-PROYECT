#ifndef GAME_BULLET_RENDER_H
#define GAME_BULLET_RENDER_H

#include <SDL.h>

#include "game/bullet.h"

void bullets_render(SDL_Renderer *renderer, const Bullets *bullets, float camera_x);

#endif
