#ifndef GAME_HUD_H
#define GAME_HUD_H

#include <stdbool.h>

#include <SDL.h>

#include "game/character_skin.h"
#include "game/player.h"
#include "game/progression.h"
#include "game/stage_run.h"
#include "game/stages.h"
#include "game/zombie.h"

bool hud_init(SDL_Renderer *renderer);
void hud_shutdown(void);

/* During a stage: stage and mission, health and XP, the gun in hand (and how
 * to switch, if can_swap), the level above each head, popups, and the cleared /
 * defeated messages. Positions are in the world; camera_x is the view's left
 * edge. */
void hud_draw_stage(SDL_Renderer *renderer, const Player *player, const Zombie *zombie,
                    const Progress *progress, const StageRun *run, float camera_x,
                    const char *weapon_name, bool can_swap);

/* Stage select for one character: every stage with its zombies' level and
 * whether it is open. */
void hud_draw_menu(SDL_Renderer *renderer, const char *character_name, const Progress *progress,
                   const StageRecord *record, int selected);

/* "Elige tu personaje": a card per character with its look, level, ability
 * and guns. progress holds each character's, in CHARACTERS order. */
void hud_draw_characters(SDL_Renderer *renderer, const CharacterSkin *skins,
                         const Progress *progress, int selected);

/* A short message that rises and fades above a point of the world. */
void hud_popup(const char *utf8, unsigned rgb, float world_x, int y, bool big);
void hud_update(float dt);
void hud_clear_popups(void);

#endif
