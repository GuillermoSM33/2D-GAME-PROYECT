#ifndef APP_INTRO_RENDER_H
#define APP_INTRO_RENDER_H

#include "engine/platform.h"
#include "game/character_skin.h"
#include "game/intro.h"
#include "game/world.h"

/* Draws the opening cinematic at its clock (game/intro.h): the lab through
 * Valeria's camera (assets/cinematics/lab, sprites/mercenary, sprites/vial),
 * the road, the town and the graveyard with the stages' own landscapes, and
 * the sheriff before the title. title_world is the menus' landscape: the last
 * scene ends on it, as the title screen begins. */
void intro_render(Platform *platform, const Intro *intro, World *title_world,
                  const CharacterSkin *sheriff);

/* The dust the title rises out of: blowing across the sky band at time t
 * of the last scene, thick (0..1). */
void intro_draw_dust(SDL_Renderer *renderer, float t, float thick);
/* The same dust behind the title screen, carrying on from where the intro
 * left it: since is seconds since the title screen came up. */
void intro_draw_title_dust(SDL_Renderer *renderer, double since);

#endif
