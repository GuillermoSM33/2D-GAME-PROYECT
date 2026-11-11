#ifndef APP_NAVIGATION_H
#define APP_NAVIGATION_H

#include "game/almanac.h"

typedef enum {
    SCREEN_INTRO,     /* The opening cinematic (game/intro.h) */
    SCREEN_TITLE,     /* Jugar, Historia, Almanaque, Controles, Opciones, Salir */
    SCREEN_CONTROLS,
    SCREEN_VOLUME,
    SCREEN_CHARACTER, /* Elige tu personaje */
    SCREEN_MENU,      /* Its stages */
    SCREEN_ALMANAC,
    SCREEN_AUTOSAVE_NOTICE,
    SCREEN_STAGE
} Screen;

bool play_almanac_sounds(Screen before, Screen after,
                          const AlmanacView *previous, const AlmanacView *view);

#endif
