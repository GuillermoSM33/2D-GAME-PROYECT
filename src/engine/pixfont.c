#include "engine/pixfont.h"

#include <string.h>

#include "engine/assets.h"

#define FONT_SHEET "sprites/ui/font"
#define CELL_W 6
#define CELL_H 10
#define SPACE_W 3 /* Art px */
#define GAP 1     /* Art px between glyphs */
#define SHADOW 0x1a1210

/* Same order as GLYPHS in tools/make_ui.py. */
static const char PIXFONT_GLYPHS[] = " !¡?¿.,:;'\"-+/()%×·→←↑↓=✓∞"
                                     "0123456789ABCDEFGHIJKLMNÑOPQRSTUVWXYZÁÉÍÓÚÜ";
#define MAX_GLYPHS 96

static unsigned codepoints[MAX_GLYPHS];
static int widths[MAX_GLYPHS]; /* Art px */
static int glyph_count;

/* Next codepoint of a UTF-8 string; advances *s. 0 at the end. */
static unsigned next_codepoint(const char **s)
{
    const unsigned char *p = (const unsigned char *)*s;
    unsigned c = p[0];
    int extra = 0;
    if (c == 0)
        return 0;
    if (c >= 0xF0) {
        c &= 0x07;
        extra = 3;
    } else if (c >= 0xE0) {
        c &= 0x0F;
        extra = 2;
    } else if (c >= 0xC0) {
        c &= 0x1F;
        extra = 1;
    }
    p++;
    for (int i = 0; i < extra && *p; i++, p++)
        c = (c << 6) | (*p & 0x3F);
    *s = (const char *)p;
    return c;
}

/* Lowercase to the uppercase glyph (ASCII and Spanish letters). */
static unsigned to_upper(unsigned c)
{
    if (c >= 'a' && c <= 'z')
        return c - 'a' + 'A';
    switch (c) {
    case 0xE1: return 0xC1; /* á */
    case 0xE9: return 0xC9; /* é */
    case 0xED: return 0xCD; /* í */
    case 0xF3: return 0xD3; /* ó */
    case 0xFA: return 0xDA; /* ú */
    case 0xFC: return 0xDC; /* ü */
    case 0xF1: return 0xD1; /* ñ */
    case 0x2022: return 0xB7; /* • as · */
    default: return c;
    }
}

static int glyph_index(unsigned c)
{
    c = to_upper(c);
    for (int i = 0; i < glyph_count; i++) {
        if (codepoints[i] == c)
            return i;
    }
    return 0; /* Space */
}

bool pixfont_init(void)
{
    glyph_count = 0;
    const char *s = PIXFONT_GLYPHS;
    unsigned c;
    while ((c = next_codepoint(&s)) != 0 && glyph_count < MAX_GLYPHS)
        codepoints[glyph_count++] = c;
    const EmbeddedImage *image = assets_find_image(FONT_SHEET);
    if (image == NULL || image->width < glyph_count * CELL_W || image->height < CELL_H)
        return false;
    for (int g = 0; g < glyph_count; g++) {
        int right = -1;
        for (int x = 0; x < CELL_W; x++) {
            for (int y = 0; y < CELL_H; y++) {
                size_t i = ((size_t)y * (size_t)image->width + (size_t)(g * CELL_W + x)) * 4;
                if (image->rgba[i + 3])
                    right = x;
            }
        }
        widths[g] = right < 0 ? SPACE_W : right + 1;
    }
    return true;
}

int pixfont_width(const char *utf8, int scale)
{
    int w = 0;
    unsigned c;
    while ((c = next_codepoint(&utf8)) != 0)
        w += (widths[glyph_index(c)] + GAP) * scale;
    return w > 0 ? w - GAP * scale : 0;
}

int pixfont_height(int scale)
{
    return CELL_H * scale;
}

static void draw_run(SDL_Renderer *renderer, SDL_Texture *sheet, const char *utf8, int x, int y,
                     int scale)
{
    unsigned c;
    while ((c = next_codepoint(&utf8)) != 0) {
        int g = glyph_index(c);
        if (g > 0) {
            SDL_Rect src = {g * CELL_W, 0, widths[g], CELL_H};
            SDL_Rect dst = {x, y, widths[g] * scale, CELL_H * scale};
            SDL_RenderCopy(renderer, sheet, &src, &dst);
        }
        x += (widths[g] + GAP) * scale;
    }
}

int pixfont_draw(SDL_Renderer *renderer, const char *utf8, int x, int y, int scale, unsigned rgb,
                 Anchor anchor, Uint8 alpha)
{
    SDL_Texture *sheet = assets_texture(FONT_SHEET);
    int w = pixfont_width(utf8, scale), h = pixfont_height(scale);
    if (sheet == NULL || w == 0)
        return w;
    switch (anchor) {
    case ANCHOR_N: x -= w / 2; break;
    case ANCHOR_NE: x -= w; break;
    case ANCHOR_S: x -= w / 2; y -= h; break;
    case ANCHOR_SW: y -= h; break;
    case ANCHOR_SE: x -= w; y -= h; break;
    case ANCHOR_NW: break;
    }
    SDL_SetTextureAlphaMod(sheet, alpha);
    SDL_SetTextureColorMod(sheet, (Uint8)(SHADOW >> 16), (Uint8)(SHADOW >> 8), (Uint8)SHADOW);
    draw_run(renderer, sheet, utf8, x + scale, y + scale, scale);
    SDL_SetTextureColorMod(sheet, (Uint8)(rgb >> 16), (Uint8)(rgb >> 8), (Uint8)rgb);
    draw_run(renderer, sheet, utf8, x, y, scale);
    SDL_SetTextureColorMod(sheet, 255, 255, 255);
    SDL_SetTextureAlphaMod(sheet, 255);
    return w;
}
