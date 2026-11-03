#ifndef GAME_ALMANAC_RENDER_H
#define GAME_ALMANAC_RENDER_H

#include <SDL.h>

#include "game/almanac.h"

/* Draw over the landscape, like the character and stage selection screens.
 * time advances while the book is open, independently of a paused stage. */
void almanac_render(SDL_Renderer *renderer, const Almanac *book,
                     const AlmanacView *view, float time);

#endif
