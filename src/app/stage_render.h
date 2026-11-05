#ifndef APP_STAGE_RENDER_H
#define APP_STAGE_RENDER_H

#include "app/options.h"
#include "app/state.h"
#include "game/character_skin.h"

void stage_draw(Platform *platform, StagePlay *play, const CharacterSkin *skin,
                 const Progress *progress, float alpha, float prev_player_x,
                 float prev_jump, const AppOptions *options);
void stage_draw_backdrop(Platform *platform, World *world, float dim);
void stage_draw_heat(SDL_Renderer *renderer, float camera_x, double time);

#endif
