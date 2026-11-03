#ifndef GAME_WEATHER_RENDER_H
#define GAME_WEATHER_RENDER_H

#include <SDL.h>

#include "game/weather.h"

/* Draw in unscaled WINDOW coordinates, after end_view() resets viewport and
 * scale, and before the HUD. Rain/gloom/lightning also cover the upper sky;
 * world-space particles keep their alignment with the road and camera. */
void weather_render(SDL_Renderer *renderer, const WeatherState *weather, float camera_x);

#endif
