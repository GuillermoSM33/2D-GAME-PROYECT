#ifndef GAME_HANG_RENDER_H
#define GAME_HANG_RENDER_H

#include <SDL.h>

#include "game/catch.h"

/* Drawing a body hung up by a trap (player_render.c, zombie_render.c). */

/* The snare's yank, t seconds in: 0 still upright, 1 swung sideways (a
 * quarter turn), 2 hanging head down. Whole turns keep the pixel art true. */
int hang_turn(float t);

/* Window px its frame goes up, t seconds after the trap sprang. */
float hang_lift(CatchKind kind, float t);

/* The sway: art px left or right, t seconds in. */
int hang_sway(float t);

/* A rope in pixel art from (x0, y0) to (x1, y1), view coordinates. */
void hang_rope(SDL_Renderer *renderer, float x0, float y0, float x1, float y1);

/* The net closed round a body, its bottom at y (view), centered on x,
 * then its rope up off the top of the view. */
void hang_net(SDL_Renderer *renderer, float anchor_x, float anchor_y, float x, float bottom_y, float t);

/* Window px over the ground to the top of what hangs (the bag, or her feet). */
float hang_top(CatchKind kind, float t);

#endif
