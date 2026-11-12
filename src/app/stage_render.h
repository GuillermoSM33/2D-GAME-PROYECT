#ifndef APP_STAGE_RENDER_H
#define APP_STAGE_RENDER_H

#include "app/options.h"
#include "app/state.h"
#include "game/character_skin.h"

void stage_draw(Platform *platform, StagePlay *play, const CharacterSkin *skin,
                 const Progress *progress, float alpha, float prev_player_x,
                 float prev_jump, const AppOptions *options);
void stage_draw_backdrop(Platform *platform, World *world, float dim);
/* The same landscape held at camera_x; and the drift starting over from
 * PLAYER_START_X, so the title screen picks up where the intro left it. */
void stage_draw_backdrop_at(Platform *platform, World *world, float camera_x, float dim);
void stage_backdrop_restart(void);
/* Seconds since then. */
double stage_backdrop_seconds(void);
/* The world's view, filling the window at VIEW_SCALE. Draw the world between
 * them, in view px (VIEW_WIDTH x VIEW_HEIGHT). */
void stage_begin_view(SDL_Renderer *renderer, const ThemeDef *theme);
void stage_end_view(SDL_Renderer *renderer);
/* Frees the view's texture (before its renderer goes). */
void stage_render_shutdown(void);
void stage_draw_heat(SDL_Renderer *renderer, float camera_x, double time);

#endif
