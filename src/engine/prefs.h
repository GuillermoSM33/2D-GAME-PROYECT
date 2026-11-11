#ifndef ENGINE_PREFS_H
#define ENGINE_PREFS_H

#include <stdbool.h>

/* Small on/off preferences kept between runs, one file each in the user's
 * data folder (SDL_GetPrefPath: ~/.local/share/TheMiracle on Linux,
 * %APPDATA%\TheMiracle on Windows). Missing or unreadable means fallback. */
bool prefs_get_bool(const char *name, bool fallback);

/* Best effort: a failure to save is reported, never fatal. */
void prefs_set_bool(const char *name, bool value);

#endif
