#ifndef GAME_PLAYER_RENDER_H
#define GAME_PLAYER_RENDER_H

#include <SDL.h>

#include "game/character_skin.h"
#include "game/player.h"

/* Kept apart from player.c so the player logic builds and tests without SDL.
 * The skin gives the character's own sheets for the template's animations. */
void player_render(SDL_Renderer *renderer, const Player *player, const CharacterSkin *skin,
                   float camera_x);

#endif
