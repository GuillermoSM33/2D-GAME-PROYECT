#ifndef APP_STORY_RENDER_H
#define APP_STORY_RENDER_H

#include "engine/platform.h"
#include "game/casefile.h"
#include "game/character_skin.h"

/* A story beat (game/casefile.h) on screen: its tape's own shot for the line
 * being typed (the town, the graveyard, the lab, the sheriff in it). */
void story_render(Platform *platform, const Story *story, const CaseFile *file, float time,
                  const CharacterSkin *sheriff);

#endif
