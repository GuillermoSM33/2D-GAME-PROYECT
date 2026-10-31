#ifndef GAME_PLAYER_RENDER_H
#define GAME_PLAYER_RENDER_H

#include <SDL.h>

#include "game/player.h"

/* Kept apart from player.c so the player logic builds and tests without SDL. */
void player_render(SDL_Renderer *renderer, const Player *player);

#endif
