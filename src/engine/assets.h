#ifndef ENGINE_ASSETS_H
#define ENGINE_ASSETS_H

#include <stdbool.h>
#include <stddef.h>

#include <SDL.h>

#include "assets_data.h"

/* Lookup of embedded data; usable without a window. */
const EmbeddedImage *assets_find_image(const char *name);
const EmbeddedBlob *assets_find_blob(const char *name);

/* Uploads every embedded image as a texture. */
bool assets_load(SDL_Renderer *renderer);
void assets_unload(void);

SDL_Texture *assets_texture(const char *name);

/* New surface with a region of an embedded image (caller frees it). */
SDL_Surface *assets_surface_region(const char *name, int x, int y, int w, int h);

#endif
