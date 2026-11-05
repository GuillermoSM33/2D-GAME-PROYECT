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

/* Per-instance gain, on top of the master and group volumes. */
void audio_play_in_gain(const char *name, int group, float gain);

/* Starts or updates an ambience loop without restarting it. Four dedicated
 * channels let wind, rain, river and fire overlap under the effects. */
void audio_loop_in(const char *name, int group, float gain);
void audio_stop_loop(const char *name);

/* Stops every instance of one effect, including a cancelled reload. */
void audio_stop(const char *name);

/* Clears a stage's lingering sounds and ambience when leaving or restarting. */
void audio_stop_all(void);

/* Freezes/resumes current sounds. New effects (such as pause menu clicks)
 * may still play while the current stage's channels are paused. */
void audio_pause(bool paused);

/* One looping background track at a time, from the embedded "music/..." files:
 * "music/ruta_1_1" is assets/music/ruta_1_1.ogg. Pass a string that lasts, such
 * as a literal. Asking for the track already playing leaves it undisturbed. It carries on under a pause, so its volume can
 * be set there by ear. audio_stop_all leaves it alone: only this stops it. */
void audio_music_play(const char *name);
void audio_music_stop(int fade_ms);
void audio_set_music(float volume);

/* Volumes, 0 (silent) to 1 (as recorded): one for everything, and one per
 * group on top of it. They also update effects and loops already playing. */
void audio_set_master(float volume);
void audio_set_group(int group, float volume);

#endif
