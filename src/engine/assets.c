#include "engine/assets.h"

#include <stdio.h>
#include <string.h>

typedef struct {
    const char *name;
    SDL_Texture *texture;
} LoadedTexture;

static LoadedTexture *textures;
static int texture_count;

const EmbeddedImage *assets_find_image(const char *name)
{
    if (!name)
        return NULL;
    for (int i = 0; i < embedded_image_count; i++) {
        if (strcmp(embedded_images[i].name, name) == 0)
            return &embedded_images[i];
    }
    return NULL;
}

const EmbeddedBlob *assets_find_blob(const char *name)
{
    if (!name)
        return NULL;
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
    assets_unload();
    if (!renderer || embedded_image_count < 0)
        return false;
    if (embedded_image_count == 0)
        return true;
    textures = SDL_calloc((size_t)embedded_image_count, sizeof(*textures));
    if (!textures) {
        fprintf(stderr, "No se pudo reservar la tabla de imágenes: %s\n", SDL_GetError());
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
    SDL_free(textures);
    textures = NULL;
    texture_count = 0;
}

SDL_Texture *assets_texture(const char *name)
{
    if (!name)
        return NULL;
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

/* A texture of these pixels (RGBA, freed here), set up like the embedded ones. */
static SDL_Texture *texture_from_pixels(SDL_Renderer *renderer, unsigned char *rgba, int width, int height)
{
    SDL_Surface *surface = SDL_CreateRGBSurfaceWithFormatFrom(rgba, width, height, 32, width * 4,
                                                              SDL_PIXELFORMAT_RGBA32);
    SDL_Texture *texture = surface ? SDL_CreateTextureFromSurface(renderer, surface) : NULL;
    SDL_FreeSurface(surface);
    SDL_free(rgba);
    if (texture) {
        SDL_SetTextureBlendMode(texture, SDL_BLENDMODE_BLEND);
        SDL_SetTextureScaleMode(texture, SDL_ScaleModeNearest);
    }
    return texture;
}

SDL_Texture *assets_texture_recolored(SDL_Renderer *renderer, const char *name,
                                      const unsigned (*pairs)[2], int count)
{
    const EmbeddedImage *image = assets_find_image(name);
    if (image == NULL)
        return NULL;
    size_t size = (size_t)image->width * (size_t)image->height * 4;
    unsigned char *rgba = SDL_malloc(size);
    if (rgba == NULL)
        return NULL;
    memcpy(rgba, image->rgba, size);
    for (size_t i = 0; i < size; i += 4) {
        unsigned rgb = ((unsigned)rgba[i] << 16) | ((unsigned)rgba[i + 1] << 8) | rgba[i + 2];
        for (int k = 0; k < count; k++) {
            if (pairs[k][0] == rgb) {
                rgba[i] = (pairs[k][1] >> 16) & 0xFF;
                rgba[i + 1] = (pairs[k][1] >> 8) & 0xFF;
                rgba[i + 2] = pairs[k][1] & 0xFF;
                break;
            }
        }
    }
    return texture_from_pixels(renderer, rgba, image->width, image->height);
}

SDL_Texture *assets_texture_graded(SDL_Renderer *renderer, const char *name, unsigned shadow, unsigned light)
{
    const EmbeddedImage *image = assets_find_image(name);
    if (image == NULL)
        return NULL;
    size_t size = (size_t)image->width * (size_t)image->height * 4;
    unsigned char *rgba = SDL_malloc(size);
    if (rgba == NULL)
        return NULL;
    memcpy(rgba, image->rgba, size);
    unsigned char map[3][256]; /* Per channel: where each value goes */
    for (int c = 0; c < 3; c++) {
        int lo = (int)((shadow >> (16 - 8 * c)) & 0xFF), hi = (int)((light >> (16 - 8 * c)) & 0xFF);
        for (int v = 0; v < 256; v++)
            map[c][v] = (unsigned char)(lo + ((hi - lo) * v + 127) / 255);
    }
    for (size_t i = 0; i < size; i += 4) {
        if (rgba[i + 3] == ASSETS_LIGHT_ALPHA) {
            rgba[i + 3] = 255;
            continue;
        }
        rgba[i] = map[0][rgba[i]];
        rgba[i + 1] = map[1][rgba[i + 1]];
        rgba[i + 2] = map[2][rgba[i + 2]];
    }
    return texture_from_pixels(renderer, rgba, image->width, image->height);
}
