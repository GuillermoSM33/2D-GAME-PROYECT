#ifndef GAME_UI_H
#define GAME_UI_H

#include <stdbool.h>

#include <SDL.h>

#include "engine/text.h"

/* The interface's pixel-art pieces (sprites/ui, tools/make_ui.py), drawn at
 * UI_SCALE: boards, buttons, key caps, icons, bars and the pixel font. */

typedef enum {
    ICON_HEART,
    ICON_BULLET,
    ICON_SKULL,
    ICON_FLAG,
    ICON_DYNAMITE,
    ICON_SPEAKER,
    ICON_STAR,
    ICON_LOCK,
    ICON_CHECK,
    ICON_SHELL,
    ICON_BLOOD,  /* Bleeding */
    ICON_SLOW,   /* Limping */
    ICON_GOLD,   /* A gold coin */
    ICON_WIND,   /* Gusts */
    ICON_CURRENT, /* Waves */
    ICON_HEAT,   /* A blazing sun */
    ICON_OMEN,   /* A crow's eye */
    ICON_COLD,   /* A snowflake */
    ICON_WET,    /* Drops */
    ICON_COZY,   /* A campfire's flame */
    ICON_WATER,  /* A jug of water */
    ICON_FRESH,  /* Refreshed: a drop and a sparkle */
    ICON_COUNT
} UiIcon;

#define UI_ICON_SIZE 12   /* Art px */
#define UI_WEAPON_W 36
#define UI_WEAPON_H 14
#define UI_GRENADE WEAPON_COUNT /* ui_weapon: the grenade's picture, after the guns */

/* A board for a window or a group of readouts (wood frame, leather inside). */
void ui_panel(SDL_Renderer *renderer, int x, int y, int w, int h);

/* A button with its label centered; selected, it is brass-edged and lit;
 * disabled, its label is greyed. */
void ui_button(SDL_Renderer *renderer, int x, int y, int w, int h, const char *label, bool selected,
               bool enabled);

/* A key cap sized to its label ("E", "ESC", "←"), top-left at x, y.
 * Returns its width. */
int ui_key(SDL_Renderer *renderer, int x, int y, const char *label);
int ui_key_width(const char *label);
int ui_key_height(void);

/* An icon or a gun's picture at a whole-number scale, top-left at x, y. */
void ui_icon(SDL_Renderer *renderer, UiIcon icon, int x, int y, int scale);
void ui_weapon(SDL_Renderer *renderer, int weapon, int x, int y, int scale);

/* A volume bar: max notches, value of them full. Returns its width. */
int ui_pips(SDL_Renderer *renderer, int x, int y, int value, int max);

/* A framed bar filled share (0..1) of the way in fill, a lighter top row in light. */
void ui_bar(SDL_Renderer *renderer, int x, int y, int w, int h, float share, unsigned fill,
            unsigned light);

/* Pixel-font text (engine/pixfont): returns its width. */
int ui_text(SDL_Renderer *renderer, const char *utf8, int x, int y, int scale, unsigned rgb,
            Anchor anchor);
int ui_text_width(const char *utf8, int scale);

/* Darkens the whole window (behind a pause or a message). */
void ui_dim(SDL_Renderer *renderer, Uint8 alpha);

#endif
