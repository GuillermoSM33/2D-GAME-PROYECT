#ifndef GAME_THEMES_H
#define GAME_THEMES_H

#include <stdbool.h>

#include "game/props.h"

/* The landscape behind a stage (docs/LANDSCAPE.md). Every theme has the same
 * background layers, each in assets/backgrounds/<theme>/<layer>.png, its own
 * mix of props, and its own colors for them. */

typedef struct {
    const char *file; /* "sky" is assets/backgrounds/<theme>/sky.png */
    int top_row;      /* Art row of its top edge */
    float parallax;   /* Share of the camera's movement: 0 still, 1 with the ground */
    bool repeat;      /* Tiles horizontally (its first and last columns match) */
    int width, height; /* Expected size in art px, checked by --verify */
} BackgroundLayer;

/* Back to front. The props go between the last two (the hills and the ground). */
extern const BackgroundLayer BACKGROUND_LAYERS[];
extern const int BACKGROUND_LAYER_COUNT;

/* Optional, in front of the props and the ground, behind the characters; it
 * also drifts on its own (FOG_DRIFT). */
extern const BackgroundLayer FOG_LAYER;

#define THEME_MAX_RECOLORS 8

typedef struct {
    const char *name; /* Its folder in assets/backgrounds */
    bool fog;         /* Has a fog.png */
    bool night;       /* After dark: more coffins, and the night ones (coffin.png 2-3) */
    /* How often each prop is picked for a big decoration (0 = never). Grass
     * tufts are scattered on their own and don't use this. */
    int prop_weights[PROP_KIND_COUNT];
    /* Palette swap for the props, drawn in the sunset's colors: each pair is
     * {original 0xRRGGBB, this theme's}. None for the sunset itself. */
    unsigned prop_recolor[THEME_MAX_RECOLORS][2];
    int prop_recolor_count;
    int house_chance; /* Percent of the house slots with a building in the background */
    /* The second route's town. A city theme strews litter instead of grass,
     * has sparrows instead of crows, iron benches and a burning drum to rest
     * by. Each list below, when given, replaces the first route's rotation. */
    bool city;
    int houses[8], house_count;            /* Which frames of props/houses, picked at random */
    int barricades[6], barricade_count;    /* Barricade looks, in turn */
    int walls[6], wall_count;              /* Wall looks (Piece.variant: fronts), in turn */
    int vehicles[6], vehicle_count;        /* Vehicles left on the road to walk past (terrain/vehicles), in turn */
} ThemeDef;

extern const ThemeDef THEME_ATARDECER;
extern const ThemeDef THEME_CEMENTERIO;
extern const ThemeDef THEME_NOCHE;
extern const ThemeDef THEME_PUEBLO_FANTASMA;
extern const ThemeDef THEME_AFUERAS;
extern const ThemeDef THEME_CENTRO;
extern const ThemeDef THEME_VIAS;
extern const ThemeDef THEME_CIUDAD_NOCHE;
extern const ThemeDef THEME_BASE_MILITAR;

#endif
