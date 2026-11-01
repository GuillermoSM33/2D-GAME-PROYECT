#include "engine/text.h"

#include <stdio.h>
#include <string.h>

#include "engine/assets.h"

bool text_system_init(void)
{
    if (TTF_Init() != 0) {
        fprintf(stderr, "No se pudo iniciar SDL_ttf: %s\n", TTF_GetError());
        return false;
    }
    return true;
}

void text_system_shutdown(void)
{
    TTF_Quit();
}

TTF_Font *text_font_open(const char *asset_name, int size_px)
{
    const EmbeddedBlob *blob = assets_find_blob(asset_name);
    if (blob == NULL) {
        fprintf(stderr, "Fuente no incrustada: %s\n", asset_name);
        return NULL;
    }
    SDL_RWops *rw = SDL_RWFromConstMem(blob->data, (int)blob->size);
    TTF_Font *font = rw ? TTF_OpenFontRW(rw, 1, size_px) : NULL;
    if (font == NULL)
        fprintf(stderr, "No se pudo abrir la fuente %s: %s\n", asset_name, TTF_GetError());
    return font;
}

bool text_create(Text *text, SDL_Renderer *renderer, TTF_Font *font,
                 const char *utf8, unsigned rgb)
{
    memset(text, 0, sizeof(*text));
    SDL_Color color = {(rgb >> 16) & 0xFF, (rgb >> 8) & 0xFF, rgb & 0xFF, 0xFF};
    SDL_Surface *surface = TTF_RenderUTF8_Blended(font, utf8, color);
    if (surface == NULL) {
        fprintf(stderr, "No se pudo dibujar el texto '%s': %s\n", utf8, TTF_GetError());
        return false;
    }
    text->texture = SDL_CreateTextureFromSurface(renderer, surface);
    text->width = surface->w;
    text->height = surface->h;
    SDL_FreeSurface(surface);
    return text->texture != NULL;
}

void text_draw(SDL_Renderer *renderer, const Text *text, int x, int y, Anchor anchor)
{
    if (text->texture == NULL)
        return;
    SDL_Rect dst = {x, y, text->width, text->height};
    if (anchor == ANCHOR_S || anchor == ANCHOR_SW || anchor == ANCHOR_SE)
        dst.y -= text->height;
    if (anchor == ANCHOR_SE || anchor == ANCHOR_NE)
        dst.x -= text->width;
    if (anchor == ANCHOR_N || anchor == ANCHOR_S)
        dst.x -= text->width / 2;
    SDL_RenderCopy(renderer, text->texture, NULL, &dst);
}

void text_destroy(Text *text)
{
    if (text->texture)
        SDL_DestroyTexture(text->texture);
    memset(text, 0, sizeof(*text));
}

bool cached_text_set(CachedText *cached, SDL_Renderer *renderer, TTF_Font *font,
                     const char *utf8, unsigned rgb)
{
    if (cached->text.texture && cached->rgb == rgb && strcmp(cached->shown, utf8) == 0)
        return true;
    text_destroy(&cached->text);
    snprintf(cached->shown, sizeof(cached->shown), "%s", utf8);
    cached->rgb = rgb;
    return text_create(&cached->text, renderer, font, cached->shown, rgb);
}

void cached_text_destroy(CachedText *cached)
{
    text_destroy(&cached->text);
    memset(cached, 0, sizeof(*cached));
}
