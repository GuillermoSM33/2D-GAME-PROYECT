#ifndef ENGINE_ASSETS_H
#define ENGINE_ASSETS_H

#include <stdbool.h>
#include <stddef.h>

#include <SDL.h>

#include "assets_data.h"

/* Lookup of embedded data; usable without a window. */
const EmbeddedImage *assets_find_image(const char *name);
const EmbeddedBlob *assets_find_blob(const char *name);

/* Uploads every embedded image as a texture, sizing the table to the actual
 * catalogue. Reloading first releases the previous textures; unload is safe
 * before loading, after failure, or more than once. */
bool assets_load(SDL_Renderer *renderer);
void assets_unload(void);

SDL_Texture *assets_texture(const char *name);

/* New surface with a region of an embedded image (caller frees it). */
SDL_Surface *assets_surface_region(const char *name, int x, int y, int w, int h);

/* New texture of an embedded image with a palette swap (caller destroys it):
 * every pixel whose color is pairs[i][0] (0xRRGGBB) becomes pairs[i][1],
 * keeping its alpha. Pixel art that shares art between themes uses it. */
SDL_Texture *assets_texture_recolored(SDL_Renderer *renderer, const char *name,
                                      const unsigned (*pairs)[2], int count);

#endif
