#ifndef GAME_INTRO_H
#define GAME_INTRO_H

#include <stdbool.h>

/* The opening cinematic, "La filtración" (docs/LORE.md): ten scenes told in
 * pictures, noises and captions, never voices. This is its clock and script:
 * which scene is on, how far into it, the caption typed so far, the fades to
 * black and the sounds due. No SDL: app/intro_render.c draws it.
 *
 * The first time the game opens it plays whole; after that only its last
 * scene's end, the title rising out of the dust (INTRO_SHORT). Enter, Esc or
 * a click skips it. */

typedef enum {
    INTRO_REC,       /* 1 Black, then the camera comes on in the lab's corridor */
    INTRO_MONITORS,  /* 2 The AI designing The Miracle */
    INTRO_ALARM,     /* 3 MRC-1 dividing, out of control */
    INTRO_MERCS,     /* 4 Flashlights at the end of the corridor */
    INTRO_SAMPLE,    /* 5 Valeria raises the sample */
    INTRO_SHOT,      /* 6 The shot: cut to black, the camera falls */
    INTRO_ROAD,      /* 7 The ambulance to Ojo de Cuervo */
    INTRO_TOWN,      /* 8 The town going quiet */
    INTRO_GRAVE,     /* 9 The dead don't stay down */
    INTRO_TITLE,     /* 10 The sheriff; THE MIRACLE out of the dust */
    INTRO_SCENES
} IntroScene;

typedef enum { INTRO_FULL, INTRO_SHORT } IntroMode;

typedef enum {
    CUE_PLAY,       /* audio_play_in(sound, group, gain) */
    CUE_LOOP,       /* audio_loop_in */
    CUE_STOP_LOOP,  /* audio_stop_loop */
    CUE_MUSIC,      /* audio_music_play(sound) */
    CUE_STOP        /* audio_stop: cut a one-shot at a picture/silence boundary */
} IntroCueKind;

typedef struct {
    IntroScene scene;
    float at;           /* Seconds into the scene */
    IntroCueKind kind;
    const char *sound;  /* Asset name, as audio.h takes it */
    int group;          /* SoundGroup */
    float gain;
} IntroCue;

typedef struct {
    IntroMode mode;
    float time;    /* Seconds since the cinematic's start (INTRO_SHORT starts late) */
    float end;     /* Its last second */
    int next_cue;  /* First cue not played yet */
    bool done;
    bool skipped;
} Intro;

/* Seconds each scene lasts; their sum is the full cinematic. */
float intro_scene_length(IntroScene scene);
float intro_total_length(void);
/* Where INTRO_SHORT starts: into INTRO_TITLE, after the sheriff is gone. */
float intro_short_start(void);

void intro_start(Intro *intro, IntroMode mode);

/* Moves the clock dt seconds on (or to the end when skip). Writes up to max of
 * the cues that came due into fired and returns how many; a skip fires none.
 * After the end, done is set and nothing more happens. */
int intro_update(Intro *intro, float dt, bool skip, const IntroCue **fired, int max);

/* The scene at the intro's time, and seconds into it. */
IntroScene intro_scene(const Intro *intro, float *local);

/* How black the screen is (0..1): fading in and out of scenes. */
float intro_black(const Intro *intro);

/* The scene's caption typed up to now into buf (lines split by '\n', whole
 * UTF-8 letters), and its opacity (0..1). Returns false when there is none
 * on screen. dialog tells a line someone says from the narrator's. */
bool intro_caption(const Intro *intro, char *buf, int size, float *alpha, bool *dialog);

/* The whole caption of a scene, or NULL. */
const char *intro_caption_text(IntroScene scene);

/* For the tests: the script's cues, in order. */
const IntroCue *intro_cues(int *count);

#endif
