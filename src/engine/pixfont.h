#ifndef ENGINE_PIXFONT_H
#define ENGINE_PIXFONT_H

#include <stdbool.h>

#include <SDL.h>

#include "engine/text.h"

/* The game's pixel font (sprites/ui/font, tools/make_ui.py): uppercase
 * glyphs of 5 x 7 px with room for accents above and a descender below,
 * drawn at a whole-number scale so they stay crisp. Lowercase is shown in
 * uppercase; letters it doesn't have show as a space. Glyph widths are read
 * from the art, so narrow letters (I, 1, !) take less room. */

/* Measures the glyphs. Needs the embedded font image (not a window). */
bool pixfont_init(void);

/* Width in window px of a string at this scale. */
int pixfont_width(const char *utf8, int scale);

/* Height of a line at this scale: accents, letters and descender. */
int pixfont_height(int scale);

/* Draws a string with its top-left (or the anchor's point) at x, y, in rgb,
 * with a one-pixel dark shadow under it so it reads over anything. alpha
 * fades it (popups). Returns its width. */
int pixfont_draw(SDL_Renderer *renderer, const char *utf8, int x, int y, int scale, unsigned rgb,
                 Anchor anchor, Uint8 alpha);

#endif
