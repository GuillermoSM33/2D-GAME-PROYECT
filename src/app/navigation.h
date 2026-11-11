#ifndef APP_NAVIGATION_H
#define APP_NAVIGATION_H

#include "game/almanac.h"
#include "game/casefile.h"

typedef enum {
    SCREEN_INTRO,     /* The opening cinematic (game/intro.h) */
    SCREEN_TITLE,     /* Jugar, Historia, Almanaque, Controles, Opciones, Salir */
    SCREEN_CONTROLS,
    SCREEN_VOLUME,
    SCREEN_CHARACTER, /* Elige tu personaje */
    SCREEN_MENU,      /* Its stages */
    SCREEN_ALMANAC,
    SCREEN_CASEFILE,  /* El expediente: the clues and the cases (game/casefile.h) */
    SCREEN_REPORT,    /* A solved case written up, over the case file */
    SCREEN_EXAMINE,   /* A clue up close, over the case file */
    SCREEN_TAPES,     /* HISTORIA: the story's animations as video tapes */
    SCREEN_STORY,     /* A story beat: a stage's ending */
    SCREEN_AUTOSAVE_NOTICE,
    SCREEN_STAGE
} Screen;

bool play_almanac_sounds(Screen before, Screen after,
                          const AlmanacView *previous, const AlmanacView *view);
/* Case file/examination/report gestures. Returns true when it owns the cue,
 * so the caller does not add a second generic menu click. */
bool play_casefile_sounds(Screen before, Screen after,
                           const BoardView *previous, const BoardView *view);
void play_tape_sounds(const TapeView *previous, const TapeView *view, const CaseFile *file,
                       const InputState *input, int result);

#endif
