#include "game/almanac_render.h"

#include <math.h>
#include <stdio.h>
#include <string.h>

#include "engine/assets.h"
#include "game/ui.h"
#include "game/zombie_render.h"

#define DETAIL_X (ALMANAC_GRID_X + ALMANAC_GRID_W + 20)
#define DETAIL_W (WINDOW_WIDTH - DETAIL_X - 24)
#define GALLERY_H (ALMANAC_ROWS * ALMANAC_CARD_H + (ALMANAC_ROWS - 1) * ALMANAC_CARD_GAP)

static int fit_scale(const char *str, int width, int scale)
{
    while (scale > 1 && ui_text_width(str, scale) > width)
        scale--;
    return scale;
}

static void text_fit(SDL_Renderer *r, const char *str, int x, int y, int width,
                      int scale, unsigned ink, Anchor anchor)
{
    ui_text(r, str, x, y, fit_scale(str, width, scale), ink, anchor);
}

/* Catalog prose may wrap; numeric values use separate measured columns and
 * never share a line with a profession's potentially long display name. */
static int prose(SDL_Renderer *r, const char *str, int x, int y, int width,
                   int scale, int line_height, int max_lines, unsigned ink)
{
    char line[256] = "", word[96], trial[352];
    const char *p = str;
    int lines = 0;
    while (*p && lines < max_lines) {
        while (*p == ' ')
            p++;
        if (!*p)
            break;
        size_t n = 0;
        while (p[n] && p[n] != ' ' && n < sizeof(word) - 1)
            n++;
        memcpy(word, p, n);
        word[n] = '\0';
        p += n;
        snprintf(trial, sizeof(trial), "%s%s%s", line, line[0] ? " " : "", word);
        if (line[0] && (strlen(trial) >= sizeof(line) || ui_text_width(trial, scale) > width)) {
            ui_text(r, line, x, y, scale, ink, ANCHOR_NW);
            y += line_height;
            lines++;
            snprintf(line, sizeof(line), "%s", word);
        } else {
            size_t length = strlen(trial);
            if (length >= sizeof(line))
                length = sizeof(line) - 1;
            memcpy(line, trial, length);
            line[length] = '\0';
        }
    }
    if (line[0] && lines < max_lines) {
        text_fit(r, line, x, y, width, scale, ink, ANCHOR_NW);
        y += line_height;
    }
    return y;
}

static void preview(SDL_Renderer *r, int entry, int center_x, int baseline,
                      int scale, float time, bool small)
{
    ZombieKind kind = almanac_kind(entry);
    bool runner = almanac_runner(entry);
    ZombieAnimation action = runner ? ZOMBIE_ANIM_RUN : small ? ZOMBIE_ANIM_IDLE : ZOMBIE_ANIM_WALK;
    const AnimationDef *def = zombie_animation(kind, action);
    if (!def || def->frame_count <= 0)
        return;
    float pace = action == ZOMBIE_ANIM_IDLE ? 1.0f : zombie_stats(kind, runner)->speed;
    int frame = def->first_frame + (int)floorf(fmaxf(0.0f, time) * def->fps * pace) % def->frame_count;
    SDL_Texture *sheet = zombie_animation_texture(def, &frame);
    if (!sheet)
        return;
    SDL_Rect shadow = {center_x - 12 * scale, baseline, 26 * scale, 2 * scale};
    SDL_SetRenderDrawColor(r, 31, 23, 20, 255);
    SDL_RenderFillRect(r, &shadow);
    SDL_Rect src = {frame * def->frame_w, 0, def->frame_w, def->frame_h};
    SDL_Rect dst = {center_x - (int)lroundf(def->anchor_x * scale),
                    baseline - def->ground_y * scale,
                    def->frame_w * scale, def->frame_h * scale};
    unsigned tint = zombie_stats(kind, runner)->tint;
    SDL_SetTextureColorMod(sheet, (Uint8)(tint >> 16), (Uint8)(tint >> 8), (Uint8)tint);
    SDL_RenderCopy(r, sheet, &src, &dst);
    SDL_SetTextureColorMod(sheet, 255, 255, 255);
}

static void unknown(SDL_Renderer *r, int center_x, int y, bool big)
{
    ui_icon(r, ICON_LOCK, center_x - (big ? 24 : 12), y + (big ? 0 : 6), big ? 4 : 2);
    ui_text(r, "????", center_x, y + (big ? 72 : 54), big ? 3 : 2,
             COLOR_HUD_LOCKED, ANCHOR_N);
}

static void card(SDL_Renderer *r, const Almanac *book, const AlmanacView *view,
                   int index, int x, int y, float time)
{
    bool selected = index == view->selected;
    if (selected)
        ui_button(r, x - 3, y - 3, ALMANAC_CARD_W + 6, ALMANAC_CARD_H + 6, "", true, true);
    ui_panel(r, x, y, ALMANAC_CARD_W, ALMANAC_CARD_H);
    const AlmanacEntry *record = almanac_entry(book, index);
    char str[24];
    snprintf(str, sizeof(str), "%02d", index + 1);
    ui_text(r, str, x + 12, y + 8, 1, COLOR_HUD_SECONDARY, ANCHOR_NW);
    if (!record || !record->discovered) {
        unknown(r, x + ALMANAC_CARD_W / 2, y + 30, false);
        ui_text(r, "SIN REGISTRO", x + ALMANAC_CARD_W / 2, y + 138, 1,
                 COLOR_HUD_LOCKED, ANCHOR_N);
        return;
    }
    const ZombieKindDef *def = zombie_kind_def(almanac_kind(index));
    preview(r, index, x + ALMANAC_CARD_W / 2, y + 96, 1, time + index * 0.07f, true);
    prose(r, def->name, x + 10, y + 105, ALMANAC_CARD_W - 20, 1, 12, 2,
          selected ? COLOR_HUD_TITLE : COLOR_HUD_PRIMARY);
    ui_text(r, almanac_runner(index) ? "CORREDOR" : "ERRANTE", x + ALMANAC_CARD_W / 2,
             y + 140, 1, almanac_runner(index) ? COLOR_HUD_DANGER : COLOR_HUD_SECONDARY, ANCHOR_N);
}

static void stats_table(SDL_Renderer *r, const Almanac *book, int index,
                         int x, int y, int width, bool compact)
{
    AlmanacStats base, observed;
    if (!almanac_stats_at(book, index, false, &base) ||
        !almanac_stats_at(book, index, true, &observed))
        return;
    int first = compact ? x + 82 : x + width / 2;
    int second = x + width;
    int number_width = compact ? 50 : width / 3 - 16;
    char str[32];
    snprintf(str, sizeof(str), compact ? "NV. 1" : "NIVEL 1");
    ui_text(r, str, first, y, compact ? 1 : 2, COLOR_HUD_SECONDARY, ANCHOR_NE);
    snprintf(str, sizeof(str), compact ? "NV. %d" : "VISTO NV. %d", observed.level);
    text_fit(r, str, second, y, compact ? 70 : width / 2 - 12, compact ? 1 : 2,
             COLOR_HUD_TITLE, ANCHOR_NE);
    static const char *const labels[] = {"VIDA", "DAÑO", "ARM.", "PASO"};
    for (int row = 0; row < 4; row++) {
        int ry = y + (compact ? 21 : 28) + row * 26;
        ui_text(r, labels[row], x, ry + (compact ? 5 : 0), compact ? 1 : 2,
                 COLOR_HUD_SECONDARY, ANCHOR_NW);
        for (int column = 0; column < 2; column++) {
            const AlmanacStats *s = column == 0 ? &base : &observed;
            if (row == 0)
                snprintf(str, sizeof(str), "%d", s->health);
            else if (row == 1)
                snprintf(str, sizeof(str), "%.1f", s->damage);
            else if (row == 2)
                snprintf(str, sizeof(str), "%.0f", s->armor);
            else
                snprintf(str, sizeof(str), "%.1f", s->speed);
            text_fit(r, str, column == 0 ? first : second, ry, number_width, 2,
                     column == 0 ? COLOR_HUD_PRIMARY : COLOR_HUD_TITLE, ANCHOR_NE);
        }
    }
}

static void record_counts(SDL_Renderer *r, const AlmanacEntry *record, int x, int y, int width)
{
    char str[80];
    snprintf(str, sizeof(str), "VISTOS %d · ABATIDOS %d", record->seen, record->defeated);
    text_fit(r, str, x, y, width, 1, COLOR_HUD_SECONDARY, ANCHOR_NW);
}

static void sidebar(SDL_Renderer *r, const Almanac *book, int index, float time)
{
    int x = DETAIL_X, y = ALMANAC_GRID_Y;
    ui_panel(r, x, y, DETAIL_W, GALLERY_H);
    const AlmanacEntry *record = almanac_entry(book, index);
    if (!record || !record->discovered) {
        ui_text(r, "POR DESCUBRIR", x + DETAIL_W / 2, y + 24, 2, COLOR_HUD_TITLE, ANCHOR_N);
        unknown(r, x + DETAIL_W / 2, y + 95, true);
        prose(r, "ENCUENTRA A ESTE ZOMBI EN EL CAMINO PARA AÑADIR SU FICHA.",
              x + 24, y + 241, DETAIL_W - 48, 1, 14, 4, COLOR_HUD_SECONDARY);
        return;
    }
    const ZombieKindDef *def = zombie_kind_def(almanac_kind(index));
    prose(r, def->name, x + 18, y + 16, DETAIL_W - 36, 2, 22, 2, COLOR_HUD_TITLE);
    ui_text(r, almanac_runner(index) ? "VARIANTE CORREDORA" : "VARIANTE ERRANTE", x + 18,
             y + 62, 1, almanac_runner(index) ? COLOR_HUD_DANGER : COLOR_HUD_SECONDARY, ANCHOR_NW);
    preview(r, index, x + 93, y + 220, 2, time, false);
    stats_table(r, book, index, x + 184, y + 84, DETAIL_W - 200, true);
    ui_text(r, "DAÑO BRUTO · PX/S", x + 184, y + 217, 1, COLOR_HUD_SECONDARY, ANCHOR_NW);
    record_counts(r, record, x + 18, y + 239, DETAIL_W - 36);
    prose(r, def->description, x + 18, y + 260, DETAIL_W - 36, 1, 12, 2, COLOR_HUD_PRIMARY);
    ui_text(r, "PROTECCIÓN", x + 18, y + 289, 1, COLOR_HUD_SECONDARY, ANCHOR_NW);
    prose(r, def->armor_profession, x + 18, y + 304, DETAIL_W - 36, 1, 12, 2, COLOR_HUD_TITLE);
}

static void detail(SDL_Renderer *r, const Almanac *book, int index, float time)
{
    const AlmanacEntry *record = almanac_entry(book, index);
    int x = 24, y = ALMANAC_GRID_Y, width = WINDOW_WIDTH - 48;
    ui_panel(r, x, y, width, ALMANAC_FOOTER_Y - y - 8);
    if (!record || !record->discovered) {
        unknown(r, WINDOW_WIDTH / 2, y + 78, true);
        ui_text(r, "TODAVÍA NO TE HAS CRUZADO CON ÉL", WINDOW_WIDTH / 2, y + 222, 2,
                 COLOR_HUD_SECONDARY, ANCHOR_N);
        ui_text(r, "LOS DESCONOCIDOS NO REVELAN SUS ESTADÍSTICAS", WINDOW_WIDTH / 2, y + 260, 1,
                 COLOR_HUD_LOCKED, ANCHOR_N);
        return;
    }
    const ZombieKindDef *def = zombie_kind_def(almanac_kind(index));
    int info_x = 300, info_w = WINDOW_WIDTH - info_x - 50;
    prose(r, def->name, info_x, y + 18, info_w, 3, 30, 1, COLOR_HUD_TITLE);
    ui_text(r, almanac_runner(index) ? "VARIANTE CORREDORA" : "VARIANTE ERRANTE", info_x,
             y + 61, 2, almanac_runner(index) ? COLOR_HUD_DANGER : COLOR_HUD_SECONDARY, ANCHOR_NW);
    preview(r, index, 150, y + 296, 3, time, false);
    prose(r, def->description, info_x, y + 100, info_w, 2, 22, 2, COLOR_HUD_PRIMARY);
    stats_table(r, book, index, info_x, y + 162, info_w, false);
    ui_text(r, "PROTECCIÓN", info_x, y + 300, 1, COLOR_HUD_SECONDARY, ANCHOR_NW);
    prose(r, def->armor_profession, info_x, y + 315, info_w, 1, 12, 2, COLOR_HUD_TITLE);
    record_counts(r, record, info_x, y + 344, info_w);
    ui_text(r, "PASO: PX/S · DAÑO: ANTES DE ARMADURA", x + 20, y + 344, 1,
             COLOR_HUD_SECONDARY, ANCHOR_NW);
}

static void footer(SDL_Renderer *r, bool in_detail)
{
    int y = ALMANAC_FOOTER_Y, x = 24;
    x += ui_key(r, x, y, "WASD") + 8;
    x += ui_text(r, "EXPLORAR", x, y + 9, 2, COLOR_HUD_PRIMARY, ANCHOR_NW) + 28;
    x += ui_key(r, x, y, "ENTER") + 8;
    ui_text(r, in_detail ? "GALERÍA" : "FICHA", x, y + 9, 2, COLOR_HUD_PRIMARY, ANCHOR_NW);
    x = WINDOW_WIDTH - 194;
    x += ui_key(r, x, y, "ESC") + 8;
    ui_text(r, "VOLVER", x, y + 9, 2, COLOR_HUD_PRIMARY, ANCHOR_NW);
}

void almanac_render(SDL_Renderer *renderer, const Almanac *book,
                     const AlmanacView *view, float time)
{
    int selected = view->selected >= 0 && view->selected < ALMANAC_ENTRIES ? view->selected : 0;
    char str[48];
    ui_dim(renderer, 100);
    ui_text(renderer, "ALMANAQUE", 24, 24, 4, COLOR_HUD_TITLE, ANCHOR_NW);
    snprintf(str, sizeof(str), "%d/%d DESCUBIERTOS", almanac_count(book), ALMANAC_ENTRIES);
    ui_text(renderer, str, WINDOW_WIDTH - 24, 45, 2, COLOR_HUD_PRIMARY, ANCHOR_NE);
    ui_text(renderer, "LOS QUE HAN CRUZADO TU CAMINO", 26, 78, 1, COLOR_HUD_SECONDARY, ANCHOR_NW);
    if (view->detail) {
        detail(renderer, book, selected, time);
    } else {
        for (int n = 0; n < ALMANAC_PAGE_SIZE && view->scroll + n < ALMANAC_ENTRIES; n++) {
            int x = ALMANAC_GRID_X + (n % ALMANAC_COLUMNS) * (ALMANAC_CARD_W + ALMANAC_CARD_GAP);
            int y = ALMANAC_GRID_Y + (n / ALMANAC_COLUMNS) * (ALMANAC_CARD_H + ALMANAC_CARD_GAP);
            card(renderer, book, view, view->scroll + n, x, y, time);
        }
        sidebar(renderer, book, selected, time);
        ui_button(renderer, ALMANAC_GRID_X, ALMANAC_PAGE_Y, 44, 30, "←", false, true);
        ui_button(renderer, ALMANAC_GRID_X + ALMANAC_GRID_W - 44, ALMANAC_PAGE_Y, 44, 30, "→", false, true);
        snprintf(str, sizeof(str), "PÁGINA %d/%d", selected / ALMANAC_PAGE_SIZE + 1, almanac_pages());
        ui_text(renderer, str, ALMANAC_GRID_X + ALMANAC_GRID_W / 2, ALMANAC_PAGE_Y + 5, 2,
                 COLOR_HUD_SECONDARY, ANCHOR_N);
    }
    footer(renderer, view->detail);
}
