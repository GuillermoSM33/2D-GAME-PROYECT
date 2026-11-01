#ifndef GAME_CHARACTER_SKIN_H
#define GAME_CHARACTER_SKIN_H

#include <stdbool.h>

#include <SDL.h>

#include "game/characters.h"

/* The sheets a character is drawn with. Every character follows the
 * cowgirl's template (docs/CHARACTERS.md), so the animations name her sheets
 * and the skin answers with this character's: its own from
 * assets/sprites/characters/<id>/ when they exist, or else hers in its
 * placeholder tint. */
#define SKIN_SHEETS 3 /* walk, jump, shoot */

typedef struct {
    const CharacterDef *character;
    SDL_Texture *sheets[SKIN_SHEETS];
    bool owned[SKIN_SHEETS]; /* Tinted copies we made and must destroy */
    bool placeholder;        /* At least one sheet is the tinted stand-in */
} CharacterSkin;

void skin_load(CharacterSkin *skin, SDL_Renderer *renderer, const CharacterDef *character);
void skin_free(CharacterSkin *skin);

/* This character's texture for one of the template's sheets
 * ("sprites/characters/cowgirl/walk" and so on), or NULL. */
SDL_Texture *skin_sheet(const CharacterSkin *skin, const char *template_sheet);

/* The template's sheet file names, in skin order. */
extern const char *const SKIN_SHEET_NAMES[SKIN_SHEETS];

#endif
