#ifndef ENGINE_AUDIO_H
#define ENGINE_AUDIO_H

#include <stdbool.h>

/* Sound effects from the embedded "sounds/..." WAV files (SDL2_mixer).
 * Without an audio device the game keeps running silently: every call is
 * then a no-op, so callers never need to check. */
bool audio_init(void);
void audio_shutdown(void);

/* Plays an effect by its path under assets/sounds, without extension:
 * "player/shot" is assets/sounds/player/shot.wav. */
void audio_play(const char *name);

#endif
