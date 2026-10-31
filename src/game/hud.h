#ifndef GAME_HUD_H
#define GAME_HUD_H

#include <stdbool.h>

#include <SDL.h>

#include "game/player.h"

bool hud_init(SDL_Renderer *renderer);
/* Help text, the player's health and, once she is down, how to restart. */
void hud_draw(SDL_Renderer *renderer, const Player *player);
void hud_shutdown(void);

#endif
