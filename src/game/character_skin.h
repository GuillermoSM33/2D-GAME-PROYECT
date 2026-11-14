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
#define SKIN_SHEETS 4 /* walk, jump, shoot, sit */

typedef struct {
    const CharacterDef *character;
    SDL_Texture *sheets[SKIN_SHEETS];
    bool owned[SKIN_SHEETS]; /* Tinted copies we made and must destroy */
    bool placeholder;        /* At least one sheet is the tinted stand-in */
    /* Per gun it can carry (its power's included): its own shoot sheet
     * (WeaponDef.shoot_sheet), or NULL to use the character's shoot sheet. */
    SDL_Texture *weapon_shoot[WEAPON_COUNT];
    SDL_Texture *weapon_walk[WEAPON_COUNT];        /* Its own walk with this gun (WeaponDef.walk_sheet)... */
    SDL_Texture *weapon_jump[WEAPON_COUNT];        /* ...and jump */
    SDL_Texture *weapon_stand[WEAPON_COUNT];       /* ...and stood still (WeaponDef.stand_sheet) */
    SDL_Texture *weapon_carry[WEAPON_COUNT];       /* Armed locomotion on the wider action template */
    SDL_Texture *weapon_power[WEAPON_COUNT];       /* ...and its ricochet (WeaponDef.power_sheet), */
    SDL_Texture *weapon_power_lit[WEAPON_COUNT];   /* ...with the flashlight on */
    SDL_Texture *weapon_legs[WEAPON_COUNT];        /* ...and its walk with no arms (WeaponDef.legs_sheet) */
    SDL_Texture *swap_far_sheet;                   /* Her far arm and pistol alone, over walking legs: swap... */
    SDL_Texture *light_far_sheet;                  /* ...and the flashlight going on with both guns */
    SDL_Texture *legs_sheet;                       /* Its walk with no arms, if it has one */
    SDL_Texture *stand_sheet;                      /* Stood still, if it has its own: else the walk's first frame */
    SDL_Texture *weapon_shoot_other[WEAPON_COUNT]; /* Its other gun's turn (WeaponDef.shoot_other_sheet) */
    SDL_Texture *weapon_shoot_lit[WEAPON_COUNT];   /* Both, with the flashlight on (shoot_lit_sheet)... */
    SDL_Texture *weapon_shoot_other_lit[WEAPON_COUNT]; /* ...(shoot_other_lit_sheet) */
    /* Per gun: its reload sheet (WeaponDef.reload_sheet), or NULL. */
    SDL_Texture *weapon_reload[WEAPON_COUNT];
    SDL_Texture *weapon_reload_other[WEAPON_COUNT];
    SDL_Texture *weapon_reload_lower[WEAPON_COUNT];
    SDL_Texture *weapon_reload_other_lower[WEAPON_COUNT];
    /* Per gun: its sit sheet (WeaponDef.sit_sheet), or NULL to use the
     * character's sit sheet. */
    SDL_Texture *weapon_sit[WEAPON_COUNT];
    SDL_Texture *throw_sheet; /* Its grenade throw, if it has one */
    /* Its blow with the gun: per gun (WeaponDef.melee_sheet), else its own
     * "melee", else NULL (the shoot sheet stands in). */
    SDL_Texture *weapon_melee[WEAPON_COUNT];
    SDL_Texture *weapon_melee_lit[WEAPON_COUNT]; /* ...with the flashlight on (WeaponDef.melee_lit_sheet) */
    SDL_Texture *melee_sheet;
    /* Per gun: turning its flashlight on (WeaponDef.light_sheet), or NULL. */
    SDL_Texture *weapon_light[WEAPON_COUNT];
    SDL_Texture *weapon_light_walk[WEAPON_COUNT]; /* ...walking with it on */
    /* The flashlight alone over its shoot sheet, when it isn't part of the gun. */
    SDL_Texture *flashlight_sheet;
    SDL_Texture *faint_sheet; /* Out cold from the heat, if it has one */
    SDL_Texture *drink_sheet; /* A drink of water... */
    SDL_Texture *bandage_sheet; /* ...and binding a wound, if it has them */
    SDL_Texture *plant_sheet;   /* Setting a charge of dynamite */
    SDL_Texture *swap_sheet;    /* Taking a second pistol out, if it has one */
    SDL_Texture *swap_lit_sheet; /* ...with the flashlight on the first */
} CharacterSkin;

void skin_load(CharacterSkin *skin, SDL_Renderer *renderer, const CharacterDef *character);
void skin_free(CharacterSkin *skin);

/* This character's texture for one of the template's sheets
 * ("sprites/characters/cowgirl/walk" and so on, ".../reload" or ".../throw")
 * with gun (a WeaponId, or -1) in hand, or NULL. */
/* Its sheet for standing still with this gun, or NULL (then the walk's first frame). */
SDL_Texture *skin_stand(const CharacterSkin *skin, int gun);
/* What to draw its walking legs from under another pose: no arms if it has that, else walk. */
SDL_Texture *skin_legs(const CharacterSkin *skin, int gun, SDL_Texture *walk);
SDL_Texture *skin_sheet(const CharacterSkin *skin, const char *template_sheet, int gun);

/* The template's sheet file names, in skin order. */
extern const char *const SKIN_SHEET_NAMES[SKIN_SHEETS];

#endif
