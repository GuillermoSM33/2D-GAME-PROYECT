#ifndef GAME_SMOKE_RENDER_H
#define GAME_SMOKE_RENDER_H

#include <SDL.h>

#include "game/smoke.h"

void smoke_render(SDL_Renderer *renderer, const Smoke *smoke, float camera_x);

#endif
