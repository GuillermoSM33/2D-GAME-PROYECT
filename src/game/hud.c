#include "game/hud.h"

#include <math.h>
#include <stdio.h>

#include "config.h"
#include "engine/assets.h"
#include "engine/platform.h"
#include "engine/text.h"
#include "game/health_bar.h"

#define FONT_REGULAR "fonts/DejaVuSansMono"
#define FONT_BOLD "fonts/DejaVuSansMono-Bold"

#define BAR_W 200
#define HEALTH_BAR_H 12
#define XP_BAR_H 6
#define RIGHT (WINDOW_WIDTH - 32)
#define HEALTH_LABEL_Y 28
#define HEALTH_BAR_Y 52
#define XP_BAR_Y 70    /* Right under the health bar */
#define BADGE_GAP 8    /* Between her level badge and the bars, on their left */
/* The block ends at y 80: themes put their moon right under it (rows 24-44 of
 * the art, from y 96), so nothing here may reach lower. */
#define OVERLAY_Y 140
#define TAG_GAP 8 /* Window px between a head (or bar) and its level tag */

#define POPUP_MAX 6
#define POPUP_TIME 1.4f
#define POPUP_RISE 40.0f /* px it climbs over its life */

/* Character cards: name, ability, its lines, guns, placeholder note, badge. */
#define CARD_TEXTS (4 + CHARACTER_ABILITY_LINES)
#define CARD_W 270
#define CARD_GAP 30
#define CARD_TOP 96
#define CARD_H 400
#define PORTRAIT_SCALE 3

#define MENU_ROW_Y 190
#define MENU_ROW_H 52
#define MENU_LEFT 220
#define MENU_WIDTH (WINDOW_WIDTH - 2 * MENU_LEFT)

typedef enum {
    F_SMALL,     /* 12 */
    F_HELP,      /* 13 */
    F_BODY,      /* 15 */
    F_TAG,       /* 14 bold: XP popups */
    F_BADGE,     /* 14 bold: the number in a level badge */
    F_ROW,       /* 22 bold */
    F_TITLE,     /* 25 bold */
    F_BIG,       /* 34 bold */
    FONT_COUNT
} FontId;

static const struct {
    const char *file;
    int size;
} FONT_SPECS[FONT_COUNT] = {
    {FONT_REGULAR, 12}, {FONT_REGULAR, 13}, {FONT_REGULAR, 15}, {FONT_BOLD, 14},
    {FONT_BOLD, 14},    {FONT_BOLD, 22},    {FONT_BOLD, 25},    {FONT_BOLD, 34},
};

static TTF_Font *fonts[FONT_COUNT];
static SDL_Renderer *hud_renderer;

/* Every piece of text the HUD shows, re-rendered only when it changes. */
enum {
    T_STAGE, T_MISSION, T_HELP, T_FOOTER, T_HEALTH_LABEL, T_XP_LABEL, T_WEAPON,
    T_PLAYER_TAG, T_ZOMBIE_TAG, T_HUD_BADGE, T_OVERLAY_1, T_OVERLAY_2,
    T_MENU_TITLE, T_MENU_SUB, T_MENU_PLAYER, T_MENU_XP, T_MENU_BADGE, T_MENU_HELP,
    T_CHAR_TITLE, T_CHAR_HELP,
    T_CHAR_CARDS, /* CARD_TEXTS per character */
    T_MENU_ROWS = T_CHAR_CARDS + CARD_TEXTS * 8, /* 4 per stage: name, detail, status, badge */
    TEXT_COUNT = T_MENU_ROWS + 4 * 16
};

static CachedText texts[TEXT_COUNT];

typedef struct {
    bool active;
    CachedText text;
    char str[48];
    unsigned rgb;
    float world_x;
    int y;
    bool big;
    float age;
} Popup;

static Popup popups[POPUP_MAX];

bool hud_init(SDL_Renderer *renderer)
{
    hud_renderer = renderer;
    for (int i = 0; i < FONT_COUNT; i++) {
        fonts[i] = text_font_open(FONT_SPECS[i].file, FONT_SPECS[i].size);
        if (fonts[i] == NULL)
            return false;
    }
    return true;
}

void hud_shutdown(void)
{
    for (int i = 0; i < TEXT_COUNT; i++)
        cached_text_destroy(&texts[i]);
    hud_clear_popups();
    for (int i = 0; i < FONT_COUNT; i++) {
        if (fonts[i])
            TTF_CloseFont(fonts[i]);
        fonts[i] = NULL;
    }
}

/* Sets text slot id to str and draws it. */
static void put(int id, FontId font, const char *str, unsigned rgb, int x, int y, Anchor anchor)
{
    if (cached_text_set(&texts[id], hud_renderer, fonts[font], str, rgb))
        text_draw(hud_renderer, &texts[id].text, x, y, anchor);
}

static void fill(SDL_Renderer *renderer, int x, int y, int w, int h, unsigned rgb)
{
    SDL_Rect rect = {x, y, w, h};
    platform_set_color(renderer, rgb);
    SDL_RenderFillRect(renderer, &rect);
}

static void draw_xp_bar(SDL_Renderer *renderer, const Progress *progress, int x, int y, int w)
{
    int need = xp_to_next(progress->level);
    int filled = need > 0 ? (int)((long)w * progress->xp / need) : w;
    fill(renderer, x, y, w, XP_BAR_H, COLOR_HEALTH_BACK);
    fill(renderer, x, y, filled, XP_BAR_H, COLOR_HUD_XP);
}

/* Level badge: the sprite (an inverted pyramid that points at its owner)
 * with the level written in its top band. */
typedef enum {
    BADGE_PLAYER, /* Brass, with a star */
    BADGE_ZOMBIE  /* Rusted iron, with a skull */
} BadgeStyle;

static const struct {
    const char *sheet;
    unsigned ink;
} BADGES[] = {
    [BADGE_PLAYER] = {"sprites/ui/badge_player", COLOR_BADGE_PLAYER_INK},
    [BADGE_ZOMBIE] = {"sprites/ui/badge_zombie", COLOR_BADGE_ZOMBIE_INK},
};

/* Draws it centered on cx with its point at tip_y; dim fades it into the
 * background. Returns its width in px. */
static int draw_badge(SDL_Renderer *renderer, int slot, int cx, int tip_y, int level,
                      BadgeStyle style, bool dim)
{
    const int w = BADGE_W * BADGE_SCALE, h = BADGE_H * BADGE_SCALE;
    SDL_Rect dst = {cx - w / 2, tip_y - h, w, h};
    SDL_Texture *sheet = assets_texture(BADGES[style].sheet);
    Uint8 alpha = dim ? 90 : 255;
    if (sheet) {
        SDL_SetTextureAlphaMod(sheet, alpha);
        SDL_RenderCopy(renderer, sheet, NULL, &dst);
        SDL_SetTextureAlphaMod(sheet, 255);
    }
    char str[16];
    snprintf(str, sizeof(str), "%d", level);
    if (cached_text_set(&texts[slot], renderer, fonts[F_BADGE], str, BADGES[style].ink)) {
        const Text *number = &texts[slot].text;
        int band_top = dst.y + BADGE_BAND_TOP * BADGE_SCALE;
        int band_h = (BADGE_BAND_BOTTOM - BADGE_BAND_TOP + 1) * BADGE_SCALE;
        SDL_SetTextureAlphaMod(number->texture, alpha);
        /* The font's digits sit a little right of their box: nudge them back so
         * they line up with the icon below. */
        text_draw(renderer, number, cx - (number->width + 1) / 2 - 1,
                  band_top + (band_h - number->height) / 2, ANCHOR_NW);
        SDL_SetTextureAlphaMod(number->texture, 255);
    }
    return w;
}

static void draw_tags(SDL_Renderer *renderer, const Player *player, const Zombie *zombie,
                      float camera_x)
{
    int head = BASELINE - PLAYER_HEAD_HEIGHT * SPRITE_SCALE - (int)lroundf(player->jump.height);
    draw_badge(renderer, T_PLAYER_TAG, (int)lroundf(player->x - camera_x), head - TAG_GAP,
               player->level, BADGE_PLAYER, false);
    if (zombie->stats != NULL && zombie_alive(zombie)) {
        int top = BASELINE - (int)(ZOMBIE_HEIGHT * SPRITE_SCALE) - 14; /* Its health bar */
        draw_badge(renderer, T_ZOMBIE_TAG, (int)lroundf(zombie->x - camera_x), top - TAG_GAP,
                   zombie->level, BADGE_ZOMBIE, false);
    }
}

static void draw_popups(float camera_x)
{
    for (int i = 0; i < POPUP_MAX; i++) {
        Popup *p = &popups[i];
        if (!p->active)
            continue;
        if (!cached_text_set(&p->text, hud_renderer, fonts[p->big ? F_ROW : F_TAG], p->str, p->rgb))
            continue;
        float t = p->age / POPUP_TIME;
        float alpha = t < 0.6f ? 1.0f : fmaxf(0.0f, 1.0f - (t - 0.6f) / 0.4f);
        SDL_SetTextureAlphaMod(p->text.text.texture, (Uint8)lroundf(alpha * 255.0f));
        text_draw(hud_renderer, &p->text.text, (int)lroundf(p->world_x - camera_x),
                  p->y - (int)lroundf(POPUP_RISE * t), ANCHOR_N);
    }
}

void hud_draw_stage(SDL_Renderer *renderer, const Player *player, const Zombie *zombie,
                    const Progress *progress, const StageRun *run, float camera_x,
                    const char *weapon_name, bool can_swap)
{
    char str[96];
    snprintf(str, sizeof(str), "NIVEL %s", run->stage->name);
    put(T_STAGE, F_TITLE, str, COLOR_HUD_TITLE, 32, 28, ANCHOR_NW);
    snprintf(str, sizeof(str), "Zombis %d/%d   ·   enemigos Nv %d", run->defeated,
             run->stage->zombies, run->stage->zombie_level);
    put(T_MISSION, F_BODY, str, COLOR_HUD_PRIMARY, 32, 65, ANCHOR_NW);
    put(T_HELP, F_HELP,
        "A/D Caminar  SHIFT Correr  ESPACIO/W Saltar  CLIC Disparar  R Reiniciar  ESC Menú",
        COLOR_HUD_SECONDARY, 32, 88, ANCHOR_NW);
    snprintf(str, sizeof(str), "C + SDL2  •  %s", SDL_GetPlatform());
    put(T_FOOTER, F_SMALL, str, COLOR_HUD_FOOTER, 25, WINDOW_HEIGHT - 18, ANCHOR_SW);
    snprintf(str, sizeof(str), can_swap ? "%s   ·   Q / CLIC DER  Cambiar" : "%s", weapon_name);
    put(T_WEAPON, F_HELP, str, COLOR_HUD_PRIMARY, WINDOW_WIDTH - 25, WINDOW_HEIGHT - 18, ANCHOR_SE);

    put(T_HEALTH_LABEL, F_HELP, "VIDA", COLOR_HUD_SECONDARY, RIGHT, HEALTH_LABEL_Y, ANCHOR_NE);
    health_bar_draw(renderer, RIGHT - BAR_W, HEALTH_BAR_Y, BAR_W, HEALTH_BAR_H, player->health,
                    player->max_health, player->armor > 0.0f);
    /* XP numbers left of the "VIDA" label, the XP bar under the health bar, and
     * her level badge to the left of both. */
    snprintf(str, sizeof(str), "XP %d/%d", progress->xp, xp_to_next(progress->level));
    put(T_XP_LABEL, F_HELP, str, COLOR_HUD_XP, RIGHT - BAR_W, HEALTH_LABEL_Y, ANCHOR_NW);
    draw_xp_bar(renderer, progress, RIGHT - BAR_W, XP_BAR_Y, BAR_W);
    int badge_cx = RIGHT - BAR_W - BADGE_GAP - BADGE_W * BADGE_SCALE / 2;
    draw_badge(renderer, T_HUD_BADGE, badge_cx, XP_BAR_Y + XP_BAR_H + 4, progress->level,
               BADGE_PLAYER, false);

    draw_tags(renderer, player, zombie, camera_x);
    draw_popups(camera_x);

    if (run->phase == RUN_FAILED) {
        put(T_OVERLAY_1, F_TITLE, "TE ALCANZÓ EL ZOMBI", COLOR_HUD_DANGER, WINDOW_WIDTH / 2,
            OVERLAY_Y, ANCHOR_N);
        put(T_OVERLAY_2, F_BODY, "R  Reintentar      ESC  Menú", COLOR_HUD_PRIMARY,
            WINDOW_WIDTH / 2, OVERLAY_Y + 40, ANCHOR_N);
    } else if (run->phase == RUN_CLEARED) {
        snprintf(str, sizeof(str), "¡NIVEL %s COMPLETADO!", run->stage->name);
        put(T_OVERLAY_1, F_TITLE, str, COLOR_HUD_XP, WINDOW_WIDTH / 2, OVERLAY_Y, ANCHOR_N);
        put(T_OVERLAY_2, F_BODY, "ENTER  Continuar", COLOR_HUD_PRIMARY, WINDOW_WIDTH / 2,
            OVERLAY_Y + 40, ANCHOR_N);
    }
}

void hud_draw_menu(SDL_Renderer *renderer, const char *character_name, const Progress *progress,
                   const StageRecord *record, int selected)
{
    char str[96];
    platform_set_color(renderer, COLOR_BACKGROUND);
    SDL_RenderClear(renderer);
    put(T_MENU_TITLE, F_BIG, "VAQUERA 2D", COLOR_HUD_TITLE, WINDOW_WIDTH / 2, 48, ANCHOR_N);
    put(T_MENU_SUB, F_BODY, "Elige un nivel", COLOR_HUD_SECONDARY, WINDOW_WIDTH / 2, 100, ANCHOR_N);
    put(T_MENU_PLAYER, F_BODY, character_name, COLOR_HUD_PRIMARY, WINDOW_WIDTH / 2 - 34, 132,
        ANCHOR_NE);
    draw_badge(renderer, T_MENU_BADGE, WINDOW_WIDTH / 2, 164, progress->level, BADGE_PLAYER,
               false);
    snprintf(str, sizeof(str), "XP %d/%d", progress->xp, xp_to_next(progress->level));
    put(T_MENU_XP, F_BODY, str, COLOR_HUD_XP, WINDOW_WIDTH / 2 + 34, 132, ANCHOR_NW);

    for (int i = 0; i < STAGE_COUNT && i < 16; i++) {
        const StageDef *stage = &STAGES[i];
        bool open = stage_unlocked(record, i);
        int y = MENU_ROW_Y + i * MENU_ROW_H;
        if (i == selected)
            fill(renderer, MENU_LEFT, y - 8, MENU_WIDTH, MENU_ROW_H - 8, COLOR_MENU_SELECTED);
        unsigned name_rgb = open ? (i == selected ? COLOR_HUD_TITLE : COLOR_HUD_PRIMARY)
                                 : COLOR_HUD_LOCKED;
        put(T_MENU_ROWS + 4 * i, F_ROW, stage->name, name_rgb, MENU_LEFT + 24, y, ANCHOR_NW);
        int badge_w = draw_badge(renderer, T_MENU_ROWS + 4 * i + 3, MENU_LEFT + 150, y + 36,
                                 stage->zombie_level, BADGE_ZOMBIE, !open);
        snprintf(str, sizeof(str), "%d zombis%s", stage->zombies, stage->boss_bonus ? " + jefe" : "");
        put(T_MENU_ROWS + 4 * i + 1, F_BODY, str, open ? COLOR_HUD_SECONDARY : COLOR_HUD_LOCKED,
            MENU_LEFT + 150 + badge_w / 2 + 16, y + 5, ANCHOR_NW);
        const char *status = record->cleared[i] ? "✓ Completado" : (open ? "" : "Bloqueado");
        unsigned status_rgb = record->cleared[i] ? COLOR_HUD_XP : COLOR_HUD_LOCKED;
        if (status[0])
            put(T_MENU_ROWS + 4 * i + 2, F_BODY, status, status_rgb, MENU_LEFT + MENU_WIDTH - 24,
                y + 5, ANCHOR_NE);
    }
    put(T_MENU_HELP, F_HELP, "↑/↓  Elegir      ENTER  Jugar      ESC  Personajes", COLOR_HUD_FOOTER,
        WINDOW_WIDTH / 2, WINDOW_HEIGHT - 40, ANCHOR_N);
}

/* One character's card: its standing frame, level, ability and guns. */
static void draw_card(SDL_Renderer *renderer, const CharacterSkin *skin, const Progress *progress,
                      int index, bool selected)
{
    const CharacterDef *c = skin->character;
    int left = (WINDOW_WIDTH - (3 * CARD_W + 2 * CARD_GAP)) / 2 + index * (CARD_W + CARD_GAP);
    int cx = left + CARD_W / 2;
    int slot = T_CHAR_CARDS + index * CARD_TEXTS;
    fill(renderer, left, CARD_TOP, CARD_W, CARD_H, selected ? COLOR_HUD_LOCKED : COLOR_MENU_SELECTED);
    fill(renderer, left + 3, CARD_TOP + 3, CARD_W - 6, CARD_H - 6,
         selected ? COLOR_MENU_SELECTED : COLOR_BACKGROUND);

    /* Standing frame of its walk sheet, a little smaller than in play. */
    SDL_Texture *walk = skin->sheets[0];
    if (walk) {
        SDL_Rect src = {0, 0, PLAYER_WALK_FRAME_W, PLAYER_WALK_FRAME_H};
        SDL_Rect dst = {cx - PLAYER_WALK_FRAME_W * PORTRAIT_SCALE / 2, CARD_TOP + 22,
                        PLAYER_WALK_FRAME_W * PORTRAIT_SCALE, PLAYER_WALK_FRAME_H * PORTRAIT_SCALE};
        Uint8 shade = selected ? 255 : 150;
        SDL_SetTextureColorMod(walk, shade, shade, shade);
        SDL_RenderCopy(renderer, walk, &src, &dst);
        SDL_SetTextureColorMod(walk, 255, 255, 255);
    }
    draw_badge(renderer, slot + CARD_TEXTS - 1, left + 34, CARD_TOP + 56, progress->level,
               BADGE_PLAYER, !selected);

    int y = CARD_TOP + 22 + PLAYER_WALK_FRAME_H * PORTRAIT_SCALE + 12;
    put(slot, F_ROW, c->name, selected ? COLOR_HUD_TITLE : COLOR_HUD_PRIMARY, cx, y, ANCHOR_N);
    char str[96];
    snprintf(str, sizeof(str), "Habilidad: %s", c->ability_name);
    put(slot + 1, F_BODY, str, COLOR_HUD_XP, cx, y + 34, ANCHOR_N);
    for (int l = 0; l < CHARACTER_ABILITY_LINES && c->ability_lines[l]; l++)
        put(slot + 2 + l, F_HELP, c->ability_lines[l], COLOR_HUD_SECONDARY, cx, y + 58 + 17 * l,
            ANCHOR_N);
    if (c->weapon_count > 1)
        snprintf(str, sizeof(str), "%s / %s", weapon_def(c->weapons[0])->name,
                 weapon_def(c->weapons[1])->name);
    else
        snprintf(str, sizeof(str), "%s", weapon_def(c->weapons[0])->name);
    put(slot + 2 + CHARACTER_ABILITY_LINES, F_HELP, str, COLOR_HUD_LEVEL, cx, y + 120, ANCHOR_N);
    if (skin->placeholder)
        put(slot + 3 + CHARACTER_ABILITY_LINES, F_SMALL, "arte provisional", COLOR_HUD_LOCKED, cx,
            CARD_TOP + 22 + PLAYER_WALK_FRAME_H * PORTRAIT_SCALE - 14, ANCHOR_N);
}

void hud_draw_characters(SDL_Renderer *renderer, const CharacterSkin *skins,
                         const Progress *progress, int selected)
{
    platform_set_color(renderer, COLOR_BACKGROUND);
    SDL_RenderClear(renderer);
    put(T_CHAR_TITLE, F_BIG, "ELIGE TU PERSONAJE", COLOR_HUD_TITLE, WINDOW_WIDTH / 2, 30, ANCHOR_N);
    for (int i = 0; i < CHARACTER_COUNT && i < 8; i++)
        draw_card(renderer, &skins[i], &progress[i], i, i == selected);
    put(T_CHAR_HELP, F_HELP, "←/→  Elegir      ENTER  Continuar      ESC  Salir", COLOR_HUD_FOOTER,
        WINDOW_WIDTH / 2, WINDOW_HEIGHT - 30, ANCHOR_N);
}

void hud_popup(const char *utf8, unsigned rgb, float world_x, int y, bool big)
{
    Popup *slot = &popups[0];
    for (int i = 0; i < POPUP_MAX; i++) {
        if (!popups[i].active) {
            slot = &popups[i];
            break;
        }
        if (popups[i].age > slot->age)
            slot = &popups[i]; /* Reuse the oldest */
    }
    slot->active = true;
    snprintf(slot->str, sizeof(slot->str), "%s", utf8);
    slot->rgb = rgb;
    slot->world_x = world_x;
    slot->y = y;
    slot->big = big;
    slot->age = 0.0f;
}

void hud_update(float dt)
{
    for (int i = 0; i < POPUP_MAX; i++) {
        if (popups[i].active && (popups[i].age += dt) >= POPUP_TIME)
            popups[i].active = false;
    }
}

void hud_clear_popups(void)
{
    for (int i = 0; i < POPUP_MAX; i++) {
        cached_text_destroy(&popups[i].text);
        popups[i].active = false;
    }
}
