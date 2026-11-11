#ifndef APP_STORY_AUDIO_H
#define APP_STORY_AUDIO_H

#include "game/casefile.h"

/* Sound follows the story clock, never the render rate. Call start once
 * after story_start, then update with the states before/after story_update
 * and its real simulation dt. Enter's time jumps do not play skipped actions.
 * stop releases this cinematic's effects and loops, preserving the music. */
void story_audio_start(const Story *story);
void story_audio_update(const Story *before, const Story *after, float dt);
void story_audio_stop(void);

#endif
