#ifndef APP_OPTIONS_H
#define APP_OPTIONS_H

#include "engine/platform.h"
#include "game/settings.h"

/* One application's options. No shared process-wide menu/window state. */
typedef struct {
    Volumes volumes;
    ListMenu volume_menu;
    Platform *display;
    bool remember_display;
} AppOptions;

void options_init(AppOptions *options, Platform *display, bool remember_display);
void options_set_fullscreen(AppOptions *options, bool on);
bool options_step(AppOptions *options, const InputState *input);
void options_apply_pointer(AppOptions *options, InputState *input, int *selected);
/* Restores saved audio levels without changing the separately persisted window preference. */
void options_restore_volumes(AppOptions *options, const Volumes *volumes);

#endif
