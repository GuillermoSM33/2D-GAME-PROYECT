#ifndef ENGINE_TEXT_H
#define ENGINE_TEXT_H

#include <stdbool.h>

#include <SDL.h>
#include <SDL_ttf.h>

typedef enum {
    ANCHOR_NW,
    ANCHOR_N, /* Top edge, centered horizontally */
    ANCHOR_NE,
    ANCHOR_SW,
    ANCHOR_SE
} Anchor;

/* Pre-rendered text: build once, draw every frame. */
typedef struct {
    SDL_Texture *texture;
    int width;
    int height;
} Text;

bool text_system_init(void);
void text_system_shutdown(void);

/* Opens an embedded font (e.g. "fonts/DejaVuSansMono") at a pixel size. */
TTF_Font *text_font_open(const char *asset_name, int size_px);

bool text_create(Text *text, SDL_Renderer *renderer, TTF_Font *font,
                 const char *utf8, unsigned rgb);
void text_draw(SDL_Renderer *renderer, const Text *text, int x, int y, Anchor anchor);
void text_destroy(Text *text);

#endif
