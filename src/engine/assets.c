#include "engine/assets.h"

#include <stdio.h>
#include <string.h>

#define MAX_TEXTURES 64

typedef struct {
    const char *name;
    SDL_Texture *texture;
} LoadedTexture;

static LoadedTexture textures[MAX_TEXTURES];
static int texture_count;

const EmbeddedImage *assets_find_image(const char *name)
{
    for (int i = 0; i < embedded_image_count; i++) {
        if (strcmp(embedded_images[i].name, name) == 0)
            return &embedded_images[i];
    }
    return NULL;
}

const EmbeddedBlob *assets_find_blob(const char *name)
{
    for (int i = 0; i < embedded_blob_count; i++) {
        if (strcmp(embedded_blobs[i].name, name) == 0)
            return &embedded_blobs[i];
    }
    return NULL;
}

static SDL_Surface *surface_from_image(const EmbeddedImage *image)
{
    /* SDL does not write to it; the cast only satisfies the API. */
    return SDL_CreateRGBSurfaceWithFormatFrom((void *)image->rgba, image->width, image->height,
                                              32, image->width * 4, SDL_PIXELFORMAT_RGBA32);
}

bool assets_load(SDL_Renderer *renderer)
{
    if (embedded_image_count > MAX_TEXTURES) {
        fprintf(stderr, "Demasiadas imágenes incrustadas (%d > %d)\n",
                embedded_image_count, MAX_TEXTURES);
        return false;
    }
    for (int i = 0; i < embedded_image_count; i++) {
        const EmbeddedImage *image = &embedded_images[i];
        SDL_Surface *surface = surface_from_image(image);
        SDL_Texture *texture = surface ? SDL_CreateTextureFromSurface(renderer, surface) : NULL;
        SDL_FreeSurface(surface);
        if (texture == NULL) {
            fprintf(stderr, "No se pudo cargar '%s': %s\n", image->name, SDL_GetError());
            assets_unload();
            return false;
        }
        SDL_SetTextureBlendMode(texture, SDL_BLENDMODE_BLEND);
        SDL_SetTextureScaleMode(texture, SDL_ScaleModeNearest);
        textures[texture_count].name = image->name;
        textures[texture_count].texture = texture;
        texture_count++;
    }
    return true;
}

void assets_unload(void)
{
    for (int i = 0; i < texture_count; i++)
        SDL_DestroyTexture(textures[i].texture);
    texture_count = 0;
}

SDL_Texture *assets_texture(const char *name)
{
    for (int i = 0; i < texture_count; i++) {
        if (strcmp(textures[i].name, name) == 0)
            return textures[i].texture;
    }
    return NULL;
}

SDL_Surface *assets_surface_region(const char *name, int x, int y, int w, int h)
{
    const EmbeddedImage *image = assets_find_image(name);
    if (image == NULL)
        return NULL;
    SDL_Surface *source = surface_from_image(image);
    SDL_Surface *region = SDL_CreateRGBSurfaceWithFormat(0, w, h, 32, SDL_PIXELFORMAT_RGBA32);
    if (source && region) {
        SDL_Rect src = {x, y, w, h};
        SDL_SetSurfaceBlendMode(source, SDL_BLENDMODE_NONE); /* Copy alpha as-is */
        SDL_BlitSurface(source, &src, region, NULL);
    }
    SDL_FreeSurface(source);
    return region;
}
