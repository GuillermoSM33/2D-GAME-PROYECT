#ifndef APP_CAPTURE_H
#define APP_CAPTURE_H

#include "app/stage_render.h"

void app_capture_screens(Platform *platform, const char *dir, CharacterSkin *skins,
                         Profile *profiles, World *menu_world, AppOptions *options);

#endif
