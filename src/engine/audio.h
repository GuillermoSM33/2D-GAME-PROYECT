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

/* The same, in one of AUDIO_GROUPS volume groups (0 is audio_play's), so
 * the game can turn kinds of sounds up or down on their own. */
void audio_play_in(const char *name, int group);

/* Volumes, 0 (silent) to 1 (as recorded): one for everything, and one per
 * group on top of it. They apply to sounds started from then on. */
void audio_set_master(float volume);
void audio_set_group(int group, float volume);

#endif
