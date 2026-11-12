#include <math.h>
#include <stdio.h>
#include <string.h>

#include "engine/assets.h"
#include "engine/pixfont.h"
#include "game/casefile_render.h"
#include "game/hud.h"
#include "game/stages.h"
#include "game/ui.h"

#define CORK 0x8a6a44
#define CORK_DARK 0x6e5232
#define CORK_LIGHT 0xa07c50
#define CARD_PAPER 0xefe6cc
#define CARD_SHADOW 0x3a2a1a
#define STRING_RED 0xb02a1a
#define PIN_RED 0xd8402a
#define PIN_SHINE 0xffb08a
#define BRASS 0xe0b050

static void fill(SDL_Renderer *r, int x, int y, int w, int h, unsigned rgb, Uint8 alpha)
{
    SDL_SetRenderDrawBlendMode(r, SDL_BLENDMODE_BLEND);
    SDL_SetRenderDrawColor(r, (Uint8)(rgb >> 16), (Uint8)(rgb >> 8), (Uint8)rgb, alpha);
    SDL_Rect rect = {x, y, w, h};
    SDL_RenderFillRect(r, &rect);
}

void clue_draw(SDL_Renderer *renderer, int clue, int x, int y, int scale, Uint8 alpha)
{
    SDL_Texture *sheet = assets_texture("sprites/clues/clues");
    if (sheet == NULL || clue < 0 || clue >= CLUE_COUNT)
        return;
    SDL_Rect src = {clue * CLUE_SPRITE, 0, CLUE_SPRITE, CLUE_SPRITE};
    SDL_Rect dst = {x, y, CLUE_SPRITE * scale, CLUE_SPRITE * scale};
    SDL_SetTextureAlphaMod(sheet, alpha);
    SDL_RenderCopy(renderer, sheet, &src, &dst);
    SDL_SetTextureAlphaMod(sheet, 255);
}

int casefile_wrap(const char *text, int scale, int max_w, char lines[][96], int max_lines)
{
    int count = 0;
    char line[96] = "";
    const char *p = text;
    while (*p && count < max_lines) {
        int n = 0;
        while (p[n] && p[n] != ' ' && n < 60)
            n++;
        char trial[96];
        int len = snprintf(trial, sizeof(trial), "%s%s%.*s", line, line[0] ? " " : "", n, p);
        if (line[0] && (len >= (int)sizeof(trial) || pixfont_width(trial, scale) > max_w)) {
            memcpy(lines[count++], line, sizeof(line));
            snprintf(line, sizeof(line), "%.*s", n, p);
        } else {
            memcpy(line, trial, sizeof(line));
        }
        p += n;
        while (*p == ' ')
            p++;
    }
    if (line[0] && count < max_lines)
        snprintf(lines[count++], 96, "%s", line);
    return count;
}

static unsigned grain(unsigned h)
{
    h ^= h >> 16;
    h *= 0x7feb352du;
    h ^= h >> 15;
    return h;
}

void casefile_draw_cork(SDL_Renderer *renderer, int x, int y, int w, int h)
{
    fill(renderer, x, y, w, h, CORK, 255);
    const int px = 3;
    for (int i = 0; i < w * h / 90; i++) { /* Its grain, in whole art px */
        unsigned g = grain((unsigned)i * 2654435761u + 7u);
        int gx = x + (int)(g % (unsigned)(w / px)) * px;
        int gy = y + (int)((g >> 12) % (unsigned)(h / px)) * px;
        fill(renderer, gx, gy, px * (1 + (int)((g >> 24) % 2)), px, (g >> 8) % 3 ? CORK_DARK : CORK_LIGHT, 255);
    }
}

static void pin(SDL_Renderer *r, int cx, int y)
{
    fill(r, cx - 4, y - 2, 9, 9, PIN_RED, 255);
    fill(r, cx - 2, y, 3, 3, PIN_SHINE, 255);
    fill(r, cx - 4, y + 7, 9, 2, 0x5a1410, 255);
}

void casefile_draw_card(SDL_Renderer *r, int clue, bool found, int x, int y, int scale, bool selected)
{
    int size = CLUE_SPRITE * scale + 10;
    if (selected)
        fill(r, x - 4, y - 4, size + 8, size + 8, BRASS, 255);
    if (found) {
        fill(r, x + 3, y + 3, size, size, CARD_SHADOW, 160);
        fill(r, x, y, size, size, CARD_PAPER, 255);
        clue_draw(r, clue, x + 5, y + 5, scale, 255);
        pin(r, x + size / 2, y - 2);
    } else {
        /* Where it will go: an empty, darker patch with a question mark */
        fill(r, x, y, size, size, CORK_DARK, 200);
        for (int k = 0; k < size; k += 8) { /* Dashed edge */
            fill(r, x + k, y, 4, 2, CORK_LIGHT, 255);
            fill(r, x + k, y + size - 2, 4, 2, CORK_LIGHT, 255);
            fill(r, x, y + k, 2, 4, CORK_LIGHT, 255);
            fill(r, x + size - 2, y + k, 2, 4, CORK_LIGHT, 255);
        }
        pixfont_draw(r, "?", x + size / 2, y + size / 2 - 14, 3, CORK_LIGHT, ANCHOR_N, 255);
    }
}

/* Red thread from pin to pin, sagging a little between them. */
static void thread(SDL_Renderer *r, int x0, int x1, int y)
{
    int mid = (x0 + x1) / 2;
    for (int x = x0; x < x1; x += 3) {
        float k = (float)(x - x0) / (float)(x1 - x0);
        int sag = (int)lroundf(sinf(k * 3.14159f) * 6.0f) / 3 * 3;
        fill(r, x, y + sag, 3, 3, STRING_RED, 255);
    }
    (void)mid;
}

static int card_top(int row)
{
    return board_row_y(row) + (BOARD_ROW_H - BOARD_CARD) / 2;
}

static void draw_row(SDL_Renderer *r, const CaseFile *file, const BoardView *view, int row)
{
    int ids[CASE_MAX_CLUES];
    int n = casefile_case_clues(row, ids);
    int top = card_top(row);
    char str[48];
    bool solved = casefile_solved(file, row);
    /* Its label, on a strip of paper pinned to the cork */
    fill(r, BOARD_X + 6, top + 6, BOARD_LABEL_W - 20, 46, CARD_PAPER, 255);
    pin(r, BOARD_X + 6 + (BOARD_LABEL_W - 20) / 2, top + 4);
    /* Its name, centered on the strip in one or two lines */
    char lines[2][96];
    int count = casefile_wrap(CASES[row].name, 2, BOARD_LABEL_W - 32, lines, 2);
    int line_h = pixfont_height(2);
    int ty = top + 6 + (46 - count * line_h) / 2 + 2;
    for (int k = 0; k < count; k++)
        pixfont_draw(r, lines[k], BOARD_X + 6 + (BOARD_LABEL_W - 20) / 2, ty + k * line_h, 2, 0x3a3430, ANCHOR_N,
                     255);
    for (int c = 0; c < n; c++)
        casefile_draw_card(r, ids[c], casefile_has(file, ids[c]), board_card_x(c), top, 2,
                           view->row == row && view->col == c);
    /* The red thread joins the clues found so far, pin to pin, over the cards */
    int last = -1;
    for (int c = 0; c < n; c++) {
        if (!casefile_has(file, ids[c]))
            continue;
        if (last >= 0)
            thread(r, board_card_x(last) + BOARD_CARD / 2 + 4, board_card_x(c) + BOARD_CARD / 2 - 4, top + 1);
        last = c;
    }
    /* The question's slot */
    bool on = view->row == row && view->col == n;
    int sx = board_slot_x(), sy = top + 8;
    if (solved) {
        if (on)
            fill(r, sx - 4, sy - 4, BOARD_SLOT_W + 8, 50, BRASS, 255);
        fill(r, sx, sy, BOARD_SLOT_W, 42, 0x2a1410, 255); /* A stamp: RESUELTO */
        fill(r, sx + 3, sy + 3, BOARD_SLOT_W - 6, 36, 0x902004, 255);
        pixfont_draw(r, "RESUELTO", sx + BOARD_SLOT_W / 2, sy + 12, 2, 0xffe0c0, ANCHOR_N, 255);
    } else if (casefile_ready(file, row)) {
        ui_button(r, sx, sy, BOARD_SLOT_W, 42, "DEDUCIR", on, true);
    } else {
        if (on)
            fill(r, sx - 4, sy - 4, BOARD_SLOT_W + 8, 50, BRASS, 255);
        fill(r, sx, sy, BOARD_SLOT_W, 42, CORK_DARK, 255);
        snprintf(str, sizeof(str), "FALTAN %d", n - casefile_case_found(file, row));
        pixfont_draw(r, str, sx + BOARD_SLOT_W / 2, sy + 12, 2, 0xd8c8a8, ANCHOR_N, 255);
    }
}

static void draw_detail(SDL_Renderer *r, const CaseFile *file, const BoardView *view)
{
    int y = BOARD_DETAIL_Y, h = 120;
    ui_panel(r, BOARD_X, y, BOARD_W, h);
    int clue = board_selected_clue(view);
    char lines[4][96];
    int text_x = BOARD_X + 112;
    int text_w = BOARD_W - 136;
    if (clue >= 0 && casefile_has(file, clue)) {
        clue_draw(r, clue, BOARD_X + 22, y + 20, 3, 255);
        pixfont_draw(r, CLUES[clue].title, text_x, y + 16, 2, COLOR_HUD_TITLE, ANCHOR_NW, 255);
        int n = casefile_wrap(CLUES[clue].text, 2, text_w, lines, 4);
        /* Up to three lines, all inside the panel's frame; its key facts stand out */
        bool emphasis = false;
        for (int k = 0; k < n && k < 3; k++)
            pixfont_draw_rich(r, lines[k], text_x, y + 38 + k * (pixfont_height(2) + 1), 2, COLOR_STORY_TEXT,
                              COLOR_STORY_EMPHASIS, ANCHOR_NW, 255, true, &emphasis);
    } else if (clue >= 0) {
        pixfont_draw(r, "PISTA SIN ENCONTRAR", text_x, y + 16, 2, COLOR_HUD_SECONDARY, ANCHOR_NW, 255);
        static const char *const WHERE[] = {"ESTÁ EN EL COFRE DE SALIDA", "LA LLEVA UNO DE LOS ZOMBIS",
                                            "ALGO SE ESCONDE EN EL CAMINO"};
        char str[96];
        snprintf(str, sizeof(str), "NIVEL %s: %s", STAGES[CLUES[clue].stage].name, WHERE[CLUES[clue].source]);
        pixfont_draw(r, str, text_x, y + 44, 2, COLOR_HUD_PRIMARY, ANCHOR_NW, 255);
    } else {
        int row = view->row;
        int n = casefile_wrap(CASES[row].question, 2, text_w, lines, 2);
        for (int k = 0; k < n; k++)
            pixfont_draw(r, lines[k], text_x, y + 16 + k * (pixfont_height(2) + 3), 2, COLOR_HUD_TITLE, ANCHOR_NW, 255);
        const char *state = casefile_solved(file, row) ? "CASO RESUELTO. ENTER: LEER EL EXPEDIENTE"
                            : casefile_ready(file, row) ? "TIENES TODAS LAS PISTAS. ENTER: RESPONDER"
                                                        : "REÚNE TODAS SUS PISTAS PARA RESPONDER";
        pixfont_draw(r, state, text_x, y + 60, 2, COLOR_HUD_PRIMARY, ANCHOR_NW, 255);
        pixfont_draw(r, "?", BOARD_X + 56, y + 30, 6, COLOR_HUD_TITLE, ANCHOR_N, 255);
    }
}

static void draw_question(SDL_Renderer *r, const BoardView *view)
{
    ui_dim(r, 170);
    int w = BOARD_OPTION_W + 80, x = (WINDOW_WIDTH - w) / 2, y = 110;
    ui_panel(r, x, y, w, 330);
    pixfont_draw(r, CASES[view->row].name, WINDOW_WIDTH / 2, y + 20, 2, COLOR_HUD_SECONDARY, ANCHOR_N, 255);
    char lines[3][96];
    int n = casefile_wrap(CASES[view->row].question, 3, w - 60, lines, 3);
    for (int k = 0; k < n; k++)
        pixfont_draw(r, lines[k], WINDOW_WIDTH / 2, y + 48 + k * 28, 3, COLOR_HUD_TITLE, ANCHOR_N, 255);
    for (int o = 0; o < CASE_OPTIONS; o++)
        ui_button(r, (WINDOW_WIDTH - BOARD_OPTION_W) / 2, BOARD_OPTION_Y + o * (BOARD_OPTION_H + 10), BOARD_OPTION_W,
                  BOARD_OPTION_H, CASES[view->row].options[o], view->option == o, true);
    if (view->wrong_time > 0.0f)
        pixfont_draw(r, "NO CUADRA. REVISA LAS PISTAS.", WINDOW_WIDTH / 2, y + 296, 2, COLOR_HUD_DANGER, ANCHOR_N,
                     (Uint8)fminf(255.0f, view->wrong_time * 400.0f));
}

void casefile_render(SDL_Renderer *r, const CaseFile *file, const BoardView *view, float time)
{
    (void)time;
    ui_dim(r, 120);
    ui_text(r, "EXPEDIENTE", BOARD_X, 18, 4, COLOR_HUD_TITLE, ANCHOR_NW);
    char str[48];
    snprintf(str, sizeof(str), "%d/%d PISTAS", casefile_found_count(file), CLUE_COUNT);
    ui_text(r, str, WINDOW_WIDTH - BOARD_X, 30, 2, COLOR_HUD_PRIMARY, ANCHOR_NE);
    /* A page of the board per route: W/S walk through every case, turning it. */
    int page = board_page(view->row), pages = (CASE_COUNT + BOARD_ROWS - 1) / BOARD_ROWS;
    snprintf(str, sizeof(str), "RUTA %d DE %d", page + 1, pages);
    ui_text(r, str, WINDOW_WIDTH / 2, 30, 2, COLOR_HUD_SECONDARY, ANCHOR_N);
    int board_h = BOARD_ROWS * BOARD_ROW_H;
    ui_panel(r, BOARD_X - 6, BOARD_Y - 10, BOARD_W + 12, board_h + 16);
    casefile_draw_cork(r, BOARD_X + 6, BOARD_Y - 2, BOARD_W - 12, board_h);
    for (int row = page * BOARD_ROWS; row < page * BOARD_ROWS + board_page_rows(page); row++)
        draw_row(r, file, view, row);
    draw_detail(r, file, view);
    if (view->asking) {
        draw_question(r, view);
        static const char *const hints[] = {"W/S", "ELEGIR", "ENTER", "RESPONDER", "ESC", "VOLVER"};
        hud_draw_hints(r, hints, 3, WINDOW_HEIGHT - 52);
    } else {
        static const char *const on_clue[] = {"WASD", "ELEGIR", "ENTER", "EXAMINAR", "ESC", "VOLVER"};
        static const char *const on_case[] = {"WASD", "ELEGIR", "ENTER", "DEDUCIR", "ESC", "VOLVER"};
        hud_draw_hints(r, board_selected_clue(view) >= 0 ? on_clue : on_case, 3, WINDOW_HEIGHT - 52);
    }
}

/* Up in the HUD's band, exactly under the mission's plate (its middle
 * column; the rows there only hold a passing alert), where the plate's clue
 * count has just gone up. Its card and its name, in one or two lines. */
#define TOAST_X 348 /* The mission plate's column (hud.c MISSION_X, MISSION_W) */
#define TOAST_W 264
#define TOAST_H 60
#define TOAST_Y 72

void casefile_draw_toast(SDL_Renderer *r, int clue, int stage_found, float left)
{
    (void)stage_found;
    if (clue < 0 || clue >= CLUE_COUNT || left <= 0.0f)
        return;
    const float total = CLUE_TOAST_SECONDS;
    float shown = total - left;
    float a = fminf(1.0f, fminf(shown / 0.2f, left / 0.5f));
    int drop = (int)lroundf((1.0f - fminf(1.0f, shown / 0.2f)) * -16.0f);
    int x = TOAST_X, y = TOAST_Y + drop;
    Uint8 alpha = (Uint8)lroundf(a * 255.0f);
    fill(r, x, y, TOAST_W, TOAST_H, 0x1a1210, (Uint8)lroundf(a * 235.0f));
    fill(r, x, y, TOAST_W, 2, BRASS, alpha);
    fill(r, x, y + TOAST_H - 2, TOAST_W, 2, BRASS, alpha);
    fill(r, x + 5, y + 5, 50, 50, CARD_PAPER, alpha);
    clue_draw(r, clue, x + 6, y + 6, 2, alpha);
    int text_x = x + 64, text_w = TOAST_W - 72;
    char lines[2][96];
    int n = casefile_wrap(CLUES[clue].title, 2, text_w, lines, 2);
    if (n == 1) {
        pixfont_draw(r, "NUEVA PISTA", text_x, y + 9, 2, COLOR_HUD_SECONDARY, ANCHOR_NW, alpha);
        pixfont_draw(r, lines[0], text_x, y + 32, 2, COLOR_HUD_TITLE, ANCHOR_NW, alpha);
    } else {
        for (int k = 0; k < n; k++)
            pixfont_draw(r, lines[k], text_x, y + 9 + k * 23, 2, COLOR_HUD_TITLE, ANCHOR_NW, alpha);
    }
}

/* ---- A solved case's report ------------------------------------------------ */

static float smooth01(float edge0, float edge1, float t)
{
    float k = (t - edge0) / (edge1 - edge0);
    k = k < 0.0f ? 0.0f : k > 1.0f ? 1.0f : k;
    return k * k * (3.0f - 2.0f * k);
}

#define REPORT_INK 0x2e2824
#define REPORT_PAPER 0xf2ead6

void report_render(SDL_Renderer *r, const Report *report, const CaseFile *file)
{
    int index = report->case_index;
    if (index < 0 || index >= CASE_COUNT)
        return;
    float t = report->time;
    ui_dim(r, (Uint8)lroundf(150.0f * smooth01(0.0f, 0.25f, t)));
    /* Its clues down the left, pinned to a strip of cork */
    int ids[CASE_MAX_CLUES];
    int n = casefile_case_clues(index, ids);
    int slide = (int)lroundf((1.0f - smooth01(0.0f, 0.35f, t)) * 560.0f);
    casefile_draw_cork(r, 24, 24 + slide, 176, 470);
    int step = n > 4 ? 76 : 100;
    for (int k = 0; k < n; k++)
        casefile_draw_card(r, ids[k], casefile_has(file, ids[k]), 83, 44 + k * step + slide, 2, false);
    /* The sheet itself */
    int x = 222, y = 24 + slide, w = 714, h = 470;
    fill(r, x + 6, y + 6, w, h, 0x1a120c, 140);
    fill(r, x, y, w, h, REPORT_PAPER, 255);
    fill(r, x, y, w, 3, 0xffffff, 255);
    /* Ink on paper: no shadow under the letters, or they smear together */
    char str[64];
    snprintf(str, sizeof(str), "EXPEDIENTE N.º %d · %s", index + 1, CASES[index].name);
    pixfont_draw_flat(r, str, x + 28, y + 22, 2, 0x8a8070, ANCHOR_NW, 255);
    char lines[24][96];
    int count = casefile_wrap(CASES[index].report_title, 3, w - 300, lines, 2); /* Clear of the stamp */
    for (int k = 0; k < count; k++)
        pixfont_draw_flat(r, lines[k], x + 28, y + 48 + k * (pixfont_height(3) + 2), 3, REPORT_INK, ANCHOR_NW, 255);
    int ty = y + 52 + count * (pixfont_height(3) + 2);
    fill(r, x + 28, ty, w - 56, 3, REPORT_INK, 255);
    ty += 16;
    /* Its paragraphs, split at the blank lines */
    const char *p = CASES[index].report;
    while (*p) {
        const char *end = strstr(p, "\n\n");
        int len = end ? (int)(end - p) : (int)strlen(p);
        char para[700];
        snprintf(para, sizeof(para), "%.*s", len, p);
        int m = casefile_wrap(para, 2, w - 56, lines, 24);
        bool emphasis = false; /* Its key facts underlined in red ink, as a detective would */
        for (int k = 0; k < m; k++) {
            pixfont_draw_rich(r, lines[k], x + 28, ty, 2, COLOR_PAPER_INK, COLOR_PAPER_EMPHASIS, ANCHOR_NW, 255, false,
                              &emphasis);
            ty += pixfont_height(2) + 4;
        }
        ty += 10;
        p += len;
        while (*p == '\n')
            p++;
    }
    /* RESUELTO, stamped askew across the top corner: it comes down big, then lands */
    SDL_Texture *stamp = assets_texture("sprites/clues/stamp");
    if (stamp && t >= REPORT_STAMP_AT) {
        float k = smooth01(REPORT_STAMP_AT, REPORT_STAMP_AT + 0.12f, t);
        int sw, sh;
        SDL_QueryTexture(stamp, NULL, NULL, &sw, &sh);
        int scale = k < 0.5f ? 4 : 3;
        SDL_Rect dst = {x + w - 24 - sw * 3 - (scale - 3) * sw / 2, y + 12 - (scale - 3) * sh / 2, sw * scale, sh * scale};
        SDL_SetTextureAlphaMod(stamp, (Uint8)lroundf(255.0f * (0.5f + 0.5f * k)));
        SDL_RenderCopy(r, stamp, NULL, &dst);
        SDL_SetTextureAlphaMod(stamp, 255);
    }
    fill(r, 0, WINDOW_HEIGHT - 44, WINDOW_WIDTH, 44, 0x0a0806, 255); /* Over the board's own hints */
    static const char *const hints[] = {"ENTER", "CERRAR"};
    hud_draw_hints(r, hints, 1, WINDOW_HEIGHT - 40);
}

/* ---- The tapes ------------------------------------------------------------------ */

static void draw_tape(SDL_Renderer *r, int x, int y, bool unlocked, bool selected, float time)
{
    const int px = 4;
    if (selected)
        fill(r, x - 6, y - 6, TAPE_W + 12, TAPE_H + 12, BRASS, 255);
    fill(r, x + 6, y + 6, TAPE_W, TAPE_H, 0x0a0806, 150);
    fill(r, x, y, TAPE_W, TAPE_H, 0x1c1c22, 255);                   /* The cassette */
    fill(r, x, y, TAPE_W, px, 0x3a3a44, 255);
    fill(r, x, y, px, TAPE_H, 0x2c2c34, 255);
    fill(r, x + 12, y + 10, TAPE_W - 24, 34, unlocked ? 0xefe6cc : 0x6a6670, 255); /* Its label */
    if (unlocked) {
        fill(r, x + 12, y + 10, TAPE_W - 24, 6, 0x902004, 255);
        for (int k = 0; k < 3; k++)
            fill(r, x + 20, y + 22 + k * 6, TAPE_W - 60 - k * 18, 2, 0x8a8070, 255);
    } else {
        pixfont_draw(r, "?", x + TAPE_W / 2, y + 14, 3, 0x3a3640, ANCHOR_N, 255);
    }
    fill(r, x + 30, y + 54, TAPE_W - 60, 34, 0x0c0c10, 255);        /* The window, two reels */
    float spin = selected && unlocked ? time * 6.0f : 0.0f;
    for (int side = 0; side < 2; side++) {
        int cx = x + (side ? TAPE_W - 54 : 54), cy = y + 71;
        fill(r, cx - 12, cy - 12, 24, 24, 0xd8d2c4, 255);
        fill(r, cx - 6, cy - 6, 12, 12, 0x1c1c22, 255);
        int spoke = (int)spin % 2;
        fill(r, cx - 2, cy - (spoke ? 10 : 2), 4, spoke ? 20 : 4, 0xd8d2c4, 255);
        fill(r, cx - (spoke ? 2 : 10), cy - 2, spoke ? 4 : 20, 4, 0xd8d2c4, 255);
    }
    fill(r, x + 66, y + 66, TAPE_W - 132, 10, 0x3a2a1c, 255);       /* The tape between them */
    fill(r, x + 20, y + TAPE_H - 14, TAPE_W - 40, 6, 0x2c2c34, 255);
}

void tapes_render(SDL_Renderer *r, const TapeView *view, const CaseFile *file)
{
    ui_dim(r, 140);
    ui_text(r, "HISTORIA", WINDOW_WIDTH / 2, 30, 5, COLOR_HUD_TITLE, ANCHOR_N);
    char str[48];
    snprintf(str, sizeof(str), "%d/%d CINTAS", tapes_unlocked(file), TAPE_COUNT);
    ui_text(r, str, WINDOW_WIDTH / 2, 88, 2, COLOR_HUD_PRIMARY, ANCHOR_N);
    float time = (float)SDL_GetTicks() / 1000.0f;
    for (int t = 0; t < TAPE_COUNT; t++) {
        int x = tape_x(t), TAPE_ROW_Y = tape_y(t, view->selected);
        if (TAPE_ROW_Y < 0) /* On a row scrolled out of view */
            continue;
        bool unlocked = tape_unlocked(file, t), selected = view->selected == t;
        int lift = selected ? -6 : 0;
        draw_tape(r, x, TAPE_ROW_Y + lift, unlocked, selected, time);
        char lines[2][96];
        int n = casefile_wrap(unlocked ? TAPES[t].title : "???", 2, TAPE_W, lines, 2);
        for (int k = 0; k < n; k++)
            pixfont_draw(r, lines[k], x + TAPE_W / 2, TAPE_ROW_Y + TAPE_H + 8 + k * (pixfont_height(1) + 2), 1,
                         selected ? COLOR_HUD_TITLE : COLOR_HUD_PRIMARY, ANCHOR_N, 255);
        if (!unlocked) {
            snprintf(str, sizeof(str), "%s %s", TAPES[t].before ? "LLEGA A" : "TERMINA", STAGES[TAPES[t].stage].name);
            pixfont_draw(r, str, x + TAPE_W / 2, TAPE_ROW_Y + TAPE_H + 24, 1, COLOR_HUD_SECONDARY, ANCHOR_N, 255);
        }
    }
    static const char *const hints[] = {"A/D", "ELEGIR", "ENTER", "VER", "ESC", "VOLVER"};
    hud_draw_hints(r, hints, 3, WINDOW_HEIGHT - 52);
}

/* ---- A clue up close ----------------------------------------------------------- */

void exam_render(SDL_Renderer *r, const ClueExam *exam, const CaseFile *file)
{
    int clue = exam->clue;
    if (clue < 0 || clue >= CLUE_COUNT)
        return;
    (void)file;
    float t = exam->time;
    ui_dim(r, (Uint8)lroundf(160.0f * smooth01(0.0f, 0.2f, t)));
    /* The clue on its card, on cork, coming up close */
    casefile_draw_cork(r, 24, 24, 400, 470);
    int scale = t < 0.08f ? 6 : t < 0.16f ? 7 : 8;
    int size = CLUE_SPRITE * scale + 24;
    int cx = 24 + 200, cy = 24 + 220;
    fill(r, cx - size / 2 + 8, cy - size / 2 + 8, size, size, 0x1a120c, 150);
    fill(r, cx - size / 2, cy - size / 2, size, size, CARD_PAPER, 255);
    clue_draw(r, clue, cx - size / 2 + 12, cy - size / 2 + 12, scale, 255);
    pin(r, cx, cy - size / 2 - 4);
    /* The examination notes, typed on a sheet */
    static const char *const KIND[] = {"DOCUMENTO", "CINTA DE AUDIO", "FOTOGRAFÍA", "OBJETO"};
    static const char *const WHERE[] = {"EL COFRE DE SALIDA", "UNO DE LOS ZOMBIS", "UNA CAJA DEL CAMINO"};
    int x = 444, y = 24, w = 492, h = 470;
    fill(r, x + 6, y + 6, w, h, 0x1a120c, 140);
    fill(r, x, y, w, h, REPORT_PAPER, 255);
    char str[96];
    snprintf(str, sizeof(str), "EXAMEN · %s", KIND[CLUES[clue].kind]);
    pixfont_draw_flat(r, str, x + 24, y + 20, 2, 0x8a8070, ANCHOR_NW, 255);
    char lines[12][96];
    int n = casefile_wrap(CLUES[clue].title, 3, w - 48, lines, 2);
    int ty = y + 44;
    for (int k = 0; k < n; k++, ty += pixfont_height(3) + 2)
        pixfont_draw_flat(r, lines[k], x + 24, ty, 3, COLOR_PAPER_INK, ANCHOR_NW, 255);
    fill(r, x + 24, ty + 4, w - 48, 3, COLOR_PAPER_INK, 255);
    ty += 18;
    snprintf(str, sizeof(str), "CASO: %s", CASES[CLUES[clue].case_index].name);
    pixfont_draw_flat(r, str, x + 24, ty, 2, 0x5a5048, ANCHOR_NW, 255);
    ty += pixfont_height(2) + 4;
    snprintf(str, sizeof(str), "HALLADA EN %s, EN %s", STAGES[CLUES[clue].stage].name, WHERE[CLUES[clue].source]);
    n = casefile_wrap(str, 2, w - 48, lines, 2);
    for (int k = 0; k < n; k++, ty += pixfont_height(2) + 4)
        pixfont_draw_flat(r, lines[k], x + 24, ty, 2, 0x5a5048, ANCHOR_NW, 255);
    ty += 12;
    bool emphasis = false;
    n = casefile_wrap(CLUES[clue].text, 2, w - 48, lines, 6);
    for (int k = 0; k < n; k++, ty += pixfont_height(2) + 4)
        pixfont_draw_rich(r, lines[k], x + 24, ty, 2, COLOR_PAPER_INK, COLOR_PAPER_EMPHASIS, ANCHOR_NW, 255, false,
                          &emphasis);
    ty += 14;
    pixfont_draw_flat(r, "DETALLES", x + 24, ty, 2, COLOR_PAPER_EMPHASIS, ANCHOR_NW, 255);
    fill(r, x + 24, ty + pixfont_height(2) + 1, pixfont_width("DETALLES", 2), 2, COLOR_PAPER_EMPHASIS, 255);
    ty += pixfont_height(2) + 10;
    emphasis = false;
    n = casefile_wrap(CLUES[clue].examine, 2, w - 48, lines, 12);
    for (int k = 0; k < n; k++, ty += pixfont_height(2) + 4)
        pixfont_draw_rich(r, lines[k], x + 24, ty, 2, COLOR_PAPER_INK, COLOR_PAPER_EMPHASIS, ANCHOR_NW, 255, false,
                          &emphasis);
    fill(r, 0, WINDOW_HEIGHT - 44, WINDOW_WIDTH, 44, 0x0a0806, 255);
    static const char *const hints[] = {"ENTER", "VOLVER AL TABLERO"};
    hud_draw_hints(r, hints, 1, WINDOW_HEIGHT - 40);
}
