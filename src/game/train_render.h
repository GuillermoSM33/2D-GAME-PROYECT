#ifndef GAME_TRAIN_RENDER_H
#define GAME_TRAIN_RENDER_H
#include <SDL.h>
#include "game/stage_run.h"

/* Inside the train: its rooms (the view never shows past their ends). */
void train_render_background(SDL_Renderer *r, const StageRun *run, float camera, float time);
/* In the world: car 01's suits and tablet, the parts on their cradles or the
 * road, with their light, the hatch's lock lamp and a marker over the next
 * goal. View px. */
void train_render_world(SDL_Renderer *r, const StageRun *run, const Player *player, float camera, float time);
/* Brief feedback for a recovered part, in window px. Objectives live in M. */
void train_render_status(SDL_Renderer *r, const StageRun *run, const Player *player, int part, float toast);
/* M: the tablet's map of the whole train over the frozen stage: each car, her
 * place, the parts, the terminal, the infected left and the fouled air. Window px. */
void train_render_map(SDL_Renderer *r, const StageRun *run, const Player *player, float time);

/* Window px of transient pickup feedback, clear of the main HUD. */
#define TRAIN_TOAST_Y (HUD_BAND + 6)
#define TRAIN_TOAST_X 624
#define TRAIN_TOAST_W 324
#define TRAIN_TOAST_H 76
bool train_render_verify_layout(void);

#endif
