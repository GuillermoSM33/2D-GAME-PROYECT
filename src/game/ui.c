#include "game/ui.h"

#include "config.h"
#include "engine/assets.h"
#include "engine/pixfont.h"

#define PANEL_SHEET "sprites/ui/panel"
#define BUTTON_SHEET "sprites/ui/button"
#define KEY_SHEET "sprites/ui/key"
#define PIP_SHEET "sprites/ui/pip"
#define BAR_SHEET "sprites/ui/bar"
#define ICON_SHEET "sprites/ui/icons"
#define WEAPON_SHEET "sprites/ui/weapons"

#define PANEL_SIZE 24
#define PANEL_CORNER 8
#define BUTTON_SIZE 16
#define BUTTON_CORNER 5
#define KEY_SIZE 14
#define KEY_CORNER 4
#define BAR_W 12
#define BAR_H 8
#define BAR_CORNER 3
#define PIP_W 6
#define PIP_H 10

/* Draws a w x h box from a 9-slice region of a sheet (corner c art px, at
 * UI_SCALE): corners as drawn, edges and middle stretched. */
static void nine_slice(SDL_Renderer *renderer, SDL_Texture *sheet, int sx, int sy, int sw, int sh,
                       int c, int x, int y, int w, int h)
{
    if (sheet == NULL)
        return;
    int k = c * UI_SCALE;
    if (w < 2 * k)
        w = 2 * k;
    if (h < 2 * k)
        h = 2 * k;
    int src_x[3] = {sx, sx + c, sx + sw - c}, src_w[3] = {c, sw - 2 * c, c};
    int src_y[3] = {sy, sy + c, sy + sh - c}, src_h[3] = {c, sh - 2 * c, c};
    int dst_x[3] = {x, x + k, x + w - k}, dst_w[3] = {k, w - 2 * k, k};
    int dst_y[3] = {y, y + k, y + h - k}, dst_h[3] = {k, h - 2 * k, k};
    for (int row = 0; row < 3; row++) {
        for (int col = 0; col < 3; col++) {
            SDL_Rect src = {src_x[col], src_y[row], src_w[col], src_h[row]};
            SDL_Rect dst = {dst_x[col], dst_y[row], dst_w[col], dst_h[row]};
            SDL_RenderCopy(renderer, sheet, &src, &dst);
        }
    }
}

void ui_panel(SDL_Renderer *renderer, int x, int y, int w, int h)
{
    nine_slice(renderer, assets_texture(PANEL_SHEET), 0, 0, PANEL_SIZE, PANEL_SIZE, PANEL_CORNER, x,
               y, w, h);
}

int ui_text(SDL_Renderer *renderer, const char *utf8, int x, int y, int scale, unsigned rgb,
            Anchor anchor)
{
    return pixfont_draw(renderer, utf8, x, y, scale, rgb, anchor, 255);
}

int ui_text_width(const char *utf8, int scale)
{
    return pixfont_width(utf8, scale);
}

void ui_button(SDL_Renderer *renderer, int x, int y, int w, int h, const char *label, bool selected,
               bool enabled)
{
    int frame = selected ? 1 : 0;
    nine_slice(renderer, assets_texture(BUTTON_SHEET), frame * BUTTON_SIZE, 0, BUTTON_SIZE,
               BUTTON_SIZE, BUTTON_CORNER, x, y, w, h);
    unsigned ink = !enabled ? COLOR_HUD_LOCKED : selected ? COLOR_HUD_TITLE : COLOR_HUD_PRIMARY;
    int scale = h >= 48 ? 3 : 2;
    /* Centered on the letters' 7 rows (the cell has 2 rows of accents above). */
    ui_text(renderer, label, x + w / 2, y + (h - 7 * scale) / 2 - 2 * scale, scale, ink, ANCHOR_N);
}

int ui_key_width(const char *label)
{
    int w = pixfont_width(label, 2) + 2 * 4 * UI_SCALE;
    return w < KEY_SIZE * UI_SCALE ? KEY_SIZE * UI_SCALE : w;
}

int ui_key_height(void)
{
    return KEY_SIZE * UI_SCALE;
}

int ui_key(SDL_Renderer *renderer, int x, int y, const char *label)
{
    int w = ui_key_width(label), h = ui_key_height();
    nine_slice(renderer, assets_texture(KEY_SHEET), 0, 0, KEY_SIZE, KEY_SIZE, KEY_CORNER, x, y, w, h);
    /* On the cap's face (its lit top 11 rows), letters' 7 rows centered. */
    pixfont_draw(renderer, label, x + w / 2, y + (11 * UI_SCALE - 7 * 2) / 2 - 2 * 2 + UI_SCALE, 2,
                 0x2a1f1a, ANCHOR_N, 255);
    return w;
}

void ui_icon(SDL_Renderer *renderer, UiIcon icon, int x, int y, int scale)
{
    SDL_Texture *sheet = assets_texture(ICON_SHEET);
    if (sheet == NULL)
        return;
    SDL_Rect src = {(int)icon * UI_ICON_SIZE, 0, UI_ICON_SIZE, UI_ICON_SIZE};
    SDL_Rect dst = {x, y, UI_ICON_SIZE * scale, UI_ICON_SIZE * scale};
    SDL_RenderCopy(renderer, sheet, &src, &dst);
}

void ui_weapon(SDL_Renderer *renderer, int weapon, int x, int y, int scale)
{
    SDL_Texture *sheet = assets_texture(WEAPON_SHEET);
    if (sheet == NULL)
        return;
    SDL_Rect src = {weapon * UI_WEAPON_W, 0, UI_WEAPON_W, UI_WEAPON_H};
    SDL_Rect dst = {x, y, UI_WEAPON_W * scale, UI_WEAPON_H * scale};
    SDL_RenderCopy(renderer, sheet, &src, &dst);
}

int ui_pips(SDL_Renderer *renderer, int x, int y, int value, int max)
{
    SDL_Texture *sheet = assets_texture(PIP_SHEET);
    int step = (PIP_W - 1) * UI_SCALE + UI_SCALE;
    for (int i = 0; i < max && sheet; i++) {
        SDL_Rect src = {(i < value ? 1 : 0) * PIP_W, 0, PIP_W, PIP_H};
        SDL_Rect dst = {x + i * step, y, PIP_W * UI_SCALE, PIP_H * UI_SCALE};
        SDL_RenderCopy(renderer, sheet, &src, &dst);
    }
    return max * step;
}

static void fill_rect(SDL_Renderer *renderer, int x, int y, int w, int h, unsigned rgb)
{
    SDL_Rect rect = {x, y, w, h};
    SDL_SetRenderDrawColor(renderer, (Uint8)(rgb >> 16), (Uint8)(rgb >> 8), (Uint8)rgb, 255);
    SDL_RenderFillRect(renderer, &rect);
}

void ui_bar(SDL_Renderer *renderer, int x, int y, int w, int h, float share, unsigned fill,
            unsigned light)
{
    nine_slice(renderer, assets_texture(BAR_SHEET), 0, 0, BAR_W, BAR_H, BAR_CORNER, x, y, w, h);
    int inset = 2 * UI_SCALE;
    int inner_w = w - 2 * inset, inner_h = h - 2 * inset;
    share = share < 0.0f ? 0.0f : share > 1.0f ? 1.0f : share;
    /* Whole art pixels, so the fill steps like the rest of the art. */
    int filled = (int)((float)(inner_w / UI_SCALE) * share + 0.5f) * UI_SCALE;
    if (filled <= 0 || inner_h <= 0)
        return;
    fill_rect(renderer, x + inset, y + inset, filled, inner_h, fill);
    fill_rect(renderer, x + inset, y + inset, filled, UI_SCALE, light);
}

void ui_dim(SDL_Renderer *renderer, Uint8 alpha)
{
    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
    SDL_SetRenderDrawColor(renderer, 10, 8, 8, alpha);
    SDL_RenderFillRect(renderer, NULL);
    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);
}
