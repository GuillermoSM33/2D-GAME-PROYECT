#include "engine/prefs.h"

#include <stdio.h>

#include <SDL.h>

#define PREFS_ORG "TheMiracle"
#define PREFS_APP "TheMiracle"

/* Full path of a preference's file, or false if there is no data folder. */
static bool pref_path(const char *name, char *path, size_t size)
{
    char *base = SDL_GetPrefPath(PREFS_ORG, PREFS_APP);
    if (base == NULL)
        return false;
    int n = snprintf(path, size, "%s%s.txt", base, name);
    SDL_free(base);
    return n > 0 && (size_t)n < size;
}

bool prefs_get_bool(const char *name, bool fallback)
{
    char path[1024];
    if (!pref_path(name, path, sizeof(path)))
        return fallback;
    FILE *file = fopen(path, "r");
    if (file == NULL)
        return fallback;
    int c = fgetc(file);
    fclose(file);
    return c == '1' ? true : c == '0' ? false : fallback;
}

void prefs_set_bool(const char *name, bool value)
{
    char path[1024];
    FILE *file = pref_path(name, path, sizeof(path)) ? fopen(path, "w") : NULL;
    if (file == NULL) {
        fprintf(stderr, "No se pudo guardar el ajuste '%s'\n", name);
        return;
    }
    fputs(value ? "1\n" : "0\n", file);
    fclose(file);
}
