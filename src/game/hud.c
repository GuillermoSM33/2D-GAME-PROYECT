#include "game/hud.h"

#include <limits.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

#include "config.h"
#include "engine/assets.h"
#include "engine/pixfont.h"
#include "game/terrain.h"
#include "game/ui.h"
#include "game/weapons.h"

#define MARGIN 16

/* A point of the view (world x minus the camera, the view's y) in the window. */
static int view_x(float x)
{
    return (int)lroundf(x * VIEW_SCALE);
}

static int view_y(float y)
{
    return VIEW_TOP + (int)lroundf(y * VIEW_SCALE);
}
#define TAG_GAP 8 /* Window px between a head (or bar) and its level tag */

/* Compact leather readouts leave the landscape open. The wider life field
 * accommodates large health totals; secondary information stays underneath. */
#define HUD_MARGIN 12
#define TOP_H 52
#define LEFT_W 264
#define RIGHT_W 356
#define WEAPON_W 292
#define WEAPON_X (HUD_MARGIN + LEFT_W + 12)

enum { HUD_ROAD, HUD_WEAPON, HUD_LIFE };
static const SDL_Rect HUD_REGIONS[] = {
    {HUD_MARGIN, 12, LEFT_W, TOP_H},
    {WEAPON_X, 12, WEAPON_W, TOP_H},
    {WINDOW_WIDTH - HUD_MARGIN - RIGHT_W, 12, RIGHT_W, TOP_H},
};

#define POPUP_MAX 6
#define POPUP_TIME 1.4f
#define POPUP_RISE 40.0f /* px it climbs over its life */

#define CARD_W 292
#define CARD_GAP 18
#define CARD_PAD 16 /* Text keeps this far from the card's frame */
#define CARD_TOP 84
#define CARD_H 416
#define PORTRAIT_SCALE 3

typedef struct {
    bool active;
    char str[48];
    unsigned rgb;
    float world_x;
    int y;
    bool big;
    float age;
} Popup;

static Popup popups[POPUP_MAX];

/* Keep the existing leather artwork and warm brass/wood palette, with a
 * thinner edge than the large menu boards. Menus retain their usual frames. */
static void hud_plate(SDL_Renderer *renderer, int x, int y, int w, int h)
{
    SDL_Texture *leather = assets_texture("sprites/ui/panel");
    SDL_Rect rect = {x, y, w, h};
    SDL_SetRenderDrawColor(renderer, 35, 25, 22, 255);
    SDL_RenderFillRect(renderer, &rect);
    if (leather) {
        SDL_Rect src = {8, 8, 8, 8};
        SDL_RenderCopy(renderer, leather, &src, &rect);
    }
    SDL_SetRenderDrawColor(renderer, 99, 71, 46, 255);
    SDL_RenderDrawLine(renderer, x + 3, y, x + w - 4, y);
    SDL_SetRenderDrawColor(renderer, 24, 17, 16, 255);
    SDL_RenderDrawLine(renderer, x + 2, y + h - 1, x + w - 3, y + h - 1);
    SDL_SetRenderDrawColor(renderer, 171, 123, 69, 255);
    SDL_Rect rivets[] = {{x + 2, y + 2, 2, 2}, {x + w - 4, y + 2, 2, 2},
                         {x + 2, y + h - 4, 2, 2}, {x + w - 4, y + h - 4, 2, 2}};
    SDL_RenderFillRects(renderer, rivets, 4);
}

/* Critical numbers always remain complete. Current names fit at scale two;
 * exceptionally long labels use scale one before any text can meet a neighbour. */
static int hud_text_scale(const char *str, int width, int preferred_scale)
{
    int scale = preferred_scale;
    while (scale > 1 && ui_text_width(str, scale) > width)
        scale--;
    return scale;
}

static int hud_text_fit(SDL_Renderer *renderer, const char *str, int x, int y,
                        int width, int preferred_scale, unsigned ink, Anchor anchor)
{
    return ui_text(renderer, str, x, y, hud_text_scale(str, width, preferred_scale), ink, anchor);
}

static void hud_top_panel(SDL_Renderer *renderer, int index)
{
    const SDL_Rect *r = &HUD_REGIONS[index];
    hud_plate(renderer, r->x, r->y, r->w, r->h);
}

static void hud_meter(SDL_Renderer *renderer, int x, int y, int w, int h,
                       float share, unsigned fill, unsigned light)
{
    share = fmaxf(0.0f, fminf(1.0f, share));
    SDL_Rect back = {x, y, w, h};
    SDL_SetRenderDrawColor(renderer, 23, 18, 18, 255);
    SDL_RenderFillRect(renderer, &back);
    int filled = (int)lroundf((float)(w - 4) * share);
    if (filled > 0) {
        SDL_Rect front = {x + 2, y + 2, filled, h - 4};
        SDL_SetRenderDrawColor(renderer, (Uint8)(fill >> 16), (Uint8)(fill >> 8), (Uint8)fill, 255);
        SDL_RenderFillRect(renderer, &front);
        SDL_SetRenderDrawColor(renderer, (Uint8)(light >> 16), (Uint8)(light >> 8), (Uint8)light, 255);
        SDL_RenderDrawLine(renderer, x + 2, y + 2, x + 1 + filled, y + 2);
    }
    SDL_SetRenderDrawColor(renderer, 107, 80, 56, 255);
    SDL_RenderDrawRect(renderer, &back);
}

bool hud_init(SDL_Renderer *renderer)
{
    (void)renderer;
    return pixfont_init();
}

void hud_shutdown(void)
{
    hud_clear_popups();
}

/* Key hints along the bottom of a screen: pairs of key cap and what it does. */
#define ZONE_MAX 48

static struct {
    SDL_Rect rect;
    HudZoneKind kind;
    int index;
} zones[ZONE_MAX];
static int zone_count;

void hud_zones_clear(void)
{
    zone_count = 0;
}

static void add_zone(HudZoneKind kind, int index, int x, int y, int w, int h)
{
    if (zone_count >= ZONE_MAX)
        return;
    zones[zone_count].rect = (SDL_Rect){x, y, w, h};
    zones[zone_count].kind = kind;
    zones[zone_count].index = index;
    zone_count++;
}

bool hud_zone_at(int x, int y, HudZone *zone)
{
    SDL_Point point = {x, y};
    for (int i = zone_count - 1; i >= 0; i--) { /* Last drawn is on top */
        if (!SDL_PointInRect(&point, &zones[i].rect))
            continue;
        zone->kind = zones[i].kind;
        zone->index = zones[i].index;
        zone->share = (float)(x - zones[i].rect.x) / (float)(zones[i].rect.w > 1 ? zones[i].rect.w - 1 : 1);
        return true;
    }
    return false;
}

static void draw_hints(SDL_Renderer *renderer, const char *const *pairs, int count, int y)
{
    int total = 0;
    for (int i = 0; i < count; i++)
        total += ui_key_width(pairs[2 * i]) + 8 + ui_text_width(pairs[2 * i + 1], 2) + 28;
    int x = (WINDOW_WIDTH - total + 28) / 2;
    for (int i = 0; i < count; i++) {
        const char *key = pairs[2 * i];
        int x0 = x;
        x += ui_key(renderer, x, y, key) + 8;
        x += ui_text(renderer, pairs[2 * i + 1], x, y + 8, 2, COLOR_HUD_PRIMARY, ANCHOR_NW);
        /* The key and its word click like the key itself. */
        if (strcmp(key, "ESC") == 0)
            add_zone(HUD_ZONE_BACK, 0, x0, y, x - x0, 14 * UI_SCALE);
        else if (strcmp(key, "ENTER") == 0)
            add_zone(HUD_ZONE_ACCEPT, 0, x0, y, x - x0, 14 * UI_SCALE);
        else if (strcmp(key, "R") == 0)
            add_zone(HUD_ZONE_RETRY, 0, x0, y, x - x0, 14 * UI_SCALE);
        x += 28;
    }
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
static int draw_badge(SDL_Renderer *renderer, int cx, int tip_y, int level, BadgeStyle style, bool dim)
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
    if (level > 999)
        snprintf(str, sizeof(str), "999+");
    else
        snprintf(str, sizeof(str), "%d", level);
    /* The glyphs' 7 rows start 2 rows into their cell (room for accents). */
    int band_top = dst.y + BADGE_BAND_TOP * BADGE_SCALE;
    int band_h = (BADGE_BAND_BOTTOM - BADGE_BAND_TOP + 1) * BADGE_SCALE;
    int scale = ui_text_width(str, 2) > w - 4 ? 1 : 2;
    pixfont_draw(renderer, str, cx, band_top + (band_h - 7 * scale) / 2 - 2 * scale, scale, BADGES[style].ink,
                 ANCHOR_N, alpha);
    return w;
}

static void draw_tags(SDL_Renderer *renderer, const Player *player, const Zombie *zombies,
                      int zombie_count, float camera_x)
{
    float head = BASELINE - PLAYER_HEAD_HEIGHT * SPRITE_SCALE - player->jump.height;
    draw_badge(renderer, view_x(player->x - camera_x), view_y(head) - TAG_GAP, player->level,
               BADGE_PLAYER, false);
    for (int i = 0; i < zombie_count; i++) {
        const Zombie *zombie = &zombies[i];
        float screen_x = zombie->x - camera_x;
        if (zombie->stats == NULL || !zombie_alive(zombie) || zombie->hidden || screen_x < -80.0f ||
            screen_x > VIEW_WIDTH + 80.0f)
            continue;
        float top = BASELINE - zombie_body_height(zombie) - 14.0f; /* Its health bar */
        draw_badge(renderer, view_x(screen_x), view_y(top) - TAG_GAP, zombie->level, BADGE_ZOMBIE, false);
    }
}

static void draw_popups(SDL_Renderer *renderer, float camera_x)
{
    for (int i = 0; i < POPUP_MAX; i++) {
        Popup *p = &popups[i];
        if (!p->active)
            continue;
        float t = p->age / POPUP_TIME;
        float alpha = t < 0.6f ? 1.0f : fmaxf(0.0f, 1.0f - (t - 0.6f) / 0.4f);
        pixfont_draw(renderer, p->str, view_x(p->world_x - camera_x), view_y((float)p->y) -
                     (int)lroundf(POPUP_RISE * t), p->big ? 3 : 2, p->rgb, ANCHOR_N,
                     (Uint8)lroundf(alpha * 255.0f));
    }
}

/* Top left: the stage, the zombies beaten and the meters to the gate (and
 * the dynamite she carries, once she has any). */
static void draw_road_panel(SDL_Renderer *renderer, const Player *player, const StageRun *run)
{
    char str[64];
    int x = HUD_MARGIN + 12, right = HUD_MARGIN + LEFT_W - 12;
    hud_top_panel(renderer, HUD_ROAD);
    snprintf(str, sizeof(str), "RUTA %s", run->stage->name);
    hud_text_fit(renderer, str, x, 20, LEFT_W / 2 - 16, 2, COLOR_HUD_TITLE, ANCHOR_NW);
    int meters = (int)fmaxf(0.0f, (run->goal_x - player->x) / ROUTE_PX_PER_METER);
    snprintf(str, sizeof(str), "SALIDA %d M", meters);
    ui_text(renderer, str, right, 25, 1, COLOR_HUD_PRIMARY, ANCHOR_NE);
    ui_icon(renderer, ICON_SKULL, x, 42, 1);
    snprintf(str, sizeof(str), "%d/%d ZOMBIS", run->defeated, run->stage->zombies);
    hud_text_fit(renderer, str, x + 18, 43, LEFT_W - 42, 1, COLOR_HUD_SECONDARY, ANCHOR_NW);
    float share = run->stage->zombies > 0 ? (float)run->defeated / (float)run->stage->zombies : 1.0f;
    hud_meter(renderer, x, 56, LEFT_W - 24, 6, share, 0x9c7044, 0xcd9b5b);
}

/* Supplies form one small line rather than a second large board. */
static void draw_gold(SDL_Renderer *renderer, const Player *player, const Progress *progress,
                      const StageRun *run)
{
    char values[3][24];
    const UiIcon icons[] = {ICON_GOLD, ICON_WATER, ICON_DYNAMITE};
    snprintf(values[0], sizeof(values[0]), "%d", progress->gold);
    snprintf(values[1], sizeof(values[1]), "%d", player->water);
    snprintf(values[2], sizeof(values[2]), "%d", run->dynamite);
    int scale = 2, count = run->dynamite > 0 ? 3 : 2, width;
    do {
        width = 0;
        for (int i = 0; i < count; i++)
            width += 18 + ui_text_width(values[i], scale) + (i ? 10 : 0);
        if (width <= LEFT_W - 16 || scale == 1)
            break;
        scale--;
    } while (true);
    int x = HUD_MARGIN + 8, y = 78;
    for (int i = 0; i < count; i++) {
        ui_icon(renderer, icons[i], x, y + 4, 1);
        x += 18;
        x += ui_text(renderer, values[i], x, y + (scale == 1 ? 6 : 1), scale,
                     i == 0 ? COLOR_HUD_TITLE : COLOR_HUD_PRIMARY, ANCHOR_NW) + 10;
    }
    /* A critical condition has a readable name even without hovering its icon. */
    char title[48] = "", note[64] = "";
    unsigned ink = COLOR_HUD_DANGER;
    if (player->bandage > 0.0f)
        snprintf(title, sizeof(title), "VENDANDO %d%%", (int)(100.0f * player->bandage / BANDAGE_TIME));
    else if (player->bleed_time > 0.0f) {
        snprintf(title, sizeof(title), "SANGRADO");
        snprintf(note, sizeof(note), "MANTÉN U PARA VENDARTE");
    } else if (player->fatigue >= FATIGUE_STROKE) {
        snprintf(title, sizeof(title), "GOLPE DE CALOR");
        snprintf(note, sizeof(note), "ALÉJATE DEL FUEGO");
    } else if (player_thirst_level(player) >= 2) {
        snprintf(title, sizeof(title), "DESHIDRATACIÓN");
        snprintf(note, sizeof(note), "U PARA BEBER");
    } else if (player->drink_time > 0.0f) {
        snprintf(title, sizeof(title), "BEBIENDO");
        ink = COLOR_HUD_PRIMARY;
    }
    if (player_alive(player) && title[0]) {
        hud_text_fit(renderer, title, HUD_MARGIN + 8, 103, LEFT_W - 16, 2, ink, ANCHOR_NW);
        if (note[0])
            ui_text(renderer, note, HUD_MARGIN + 8, 122, 1, COLOR_HUD_PRIMARY, ANCHOR_NW);
    }
}

/* Top right: health with its numbers, XP under it, her level badge left of both. */
static void draw_life_panel(SDL_Renderer *renderer, const Player *player, const Progress *progress)
{
    char str[48];
    int x0 = WINDOW_WIDTH - HUD_MARGIN - RIGHT_W;
    hud_top_panel(renderer, HUD_LIFE);
    draw_badge(renderer, x0 + 22, 57, progress->level, BADGE_PLAYER, false);
    int x = x0 + 46, right = WINDOW_WIDTH - HUD_MARGIN - 12;
    ui_icon(renderer, ICON_HEART, x, 19, 2);
    float life = player->max_health > 0 ? (float)player->health / (float)player->max_health : 0.0f;
    hud_meter(renderer, x + 30, 23, 114, 16, life, COLOR_HEALTH_FILL, 0xe07a50);
    snprintf(str, sizeof(str), "%d/%d", player->health, player->max_health);
    hud_text_fit(renderer, str, right, 21, right - (x + 152), 2,
                 life > 0.25f ? COLOR_HUD_PRIMARY : COLOR_HUD_DANGER, ANCHOR_NE);
    ui_icon(renderer, ICON_STAR, x + 7, 44, 1);
    int need = xp_to_next(progress->level);
    hud_meter(renderer, x + 30, 47, 114, 7, need > 0 ? (float)progress->xp / (float)need : 1.0f,
              COLOR_HUD_XP, 0xb0e090);
    snprintf(str, sizeof(str), "XP %d/%d", progress->xp, need);
    hud_text_fit(renderer, str, right, 45, right - (x + 152), 1, COLOR_HUD_XP, ANCHOR_NE);
}

/* Where the mouse is (hud_set_pointer). */
static int pointer_x = -1, pointer_y = -1;

/* Under the life panel: what helps or ails her now, each a small icon (and
 * the seconds left, if it wears off); the mouse over one opens it: a name
 * and what it means. */
static void draw_states(SDL_Renderer *renderer, const Player *player, const StageRun *run)
{
    if (!player_alive(player))
        return;
    char bleed_note[48];
    if (player->bandage > 0.0f)
        snprintf(bleed_note, sizeof(bleed_note), "VENDANDO... %d%%",
                 (int)(100.0f * player->bandage / BANDAGE_TIME));
    else
        snprintf(bleed_note, sizeof(bleed_note), "MANTÉN U PARA VENDARTE");
    const struct {
        bool on;
        int icon;
        const char *name, *note;
        float time; /* 0: lasts while it lasts */
        bool good;
    } states[] = {
        {player->bleed_time > 0.0f, ICON_BLOOD, "SANGRADO", bleed_note, player->bleed_time, false},
        {player->slow_time > 0.0f, ICON_SLOW, "LENTITUD", "TE LASTIMASTE LA PIERNA", player->slow_time, false},
        {player->wind_feel > 0, ICON_WIND, "RAPIDEZ", "EL VIENTO TE EMPUJA", 0.0f, true},
        {player->wind_feel < 0, ICON_WIND, "LENTITUD", "VAS CONTRA EL VIENTO", 0.0f, false},
        {player->current_feel < 0, ICON_CURRENT, "LENTITUD", "ESTÁS CONTRA CORRIENTE", 0.0f, false},
        {player->wading && player->current_feel >= 0, ICON_CURRENT, "LENTITUD", "VADEANDO EL RÍO", 0.0f, false},
        {player->hot && player->refreshed <= 0.0f, ICON_HEAT, "CALOR",
         "TARDAS MÁS EN GOLPEAR. BEBE AGUA CON U", 0.0f, false},
        {player->refreshed > 0.0f, ICON_FRESH, "HIDRATADO", "PARECE QUE PUEDES MOVERTE UN POCO MÁS RÁPIDO",
         player->refreshed, true},
        {player_thirst_level(player) == 1, ICON_WATER, "SEDIENTO", "SIENTES LA BOCA SECA", 0.0f, false},
        {player_thirst_level(player) == 2, ICON_WATER, "DESHIDRATADO", "EMPIEZAS A ALUCINAR", 0.0f, false},
        {player_thirst_level(player) == 3, ICON_OMEN, "ALUCINACIÓN", "PUEDES VER COSAS DONDE NO LAS HAY", 0.0f,
         false},
        {player->cold, ICON_COLD, "FRÍO", "GOLPEAS Y CAMINAS UN POCO MÁS LENTO", 0.0f, false},
        {player->wet > 0.0f, ICON_WET, "HÚMEDO", "ESTÁS UN POCO MOJADO", player->wet * player_dry_time(player),
         false},
        {player->cozy && !player->hot && player_alive(player), ICON_COZY, "CALOR AGRADABLE",
         "RECUPERAS VIDA POCO A POCO", 0.0f, true},
        {player->fatigue > 0.0f && player->fatigue < FATIGUE_SLOW, ICON_HEAT, "FATIGA",
         "PARECE QUE TE DARÁ UN GOLPE DE CALOR", FATIGUE_FAINT - player->fatigue, false},
        {player->fatigue >= FATIGUE_SLOW && player->fatigue < FATIGUE_STROKE, ICON_HEAT, "FATIGA",
         "TE MUEVES, GOLPEAS Y DISPARAS MÁS LENTO", FATIGUE_FAINT - player->fatigue, false},
        {player->fatigue >= FATIGUE_STROKE, ICON_HEAT, "GOLPE DE CALOR", "¡ALÉJATE DEL FUEGO O TE DESMAYARÁS!",
         FATIGUE_FAINT - player->fatigue, false},
        {run->omen, ICON_OMEN, "MAL PRESAGIO", "UNA EMBOSCADA PUEDE ESTAR CERCA", 0.0f, false},
    };
    /* Two bounded rows keep simultaneous weather/health states within the
     * life column instead of growing leftward into the gun and supplies. */
    int size = 24, gap = 4, columns = (RIGHT_W - 8) / (size + gap), shown = 0;
    int open = -1, open_x = 0, open_y = 0;
    for (int i = 0; i < (int)(sizeof(states) / sizeof(states[0])); i++) {
        if (!states[i].on)
            continue;
        int x = WINDOW_WIDTH - HUD_MARGIN - size - (shown % columns) * (size + gap);
        int y = 76 + (shown / columns) * (size + gap);
        shown++;
        bool hover = pointer_x >= x && pointer_x < x + size && pointer_y >= y && pointer_y < y + size;
        hud_plate(renderer, x, y, size, size);
        ui_icon(renderer, states[i].icon, x + 6, y + 2, 1);
        if (states[i].time > 0.0f) { /* Seconds left, small under the icon */
            char str[16];
            if (states[i].time > 99.0f)
                snprintf(str, sizeof(str), "99+");
            else
                snprintf(str, sizeof(str), "%d", (int)ceilf(states[i].time));
            ui_text(renderer, str, x + size - 3, y + 12, 1, COLOR_HUD_PRIMARY, ANCHOR_NE);
        }
        unsigned rgb = states[i].good ? COLOR_HUD_XP : COLOR_HUD_DANGER;
        SDL_SetRenderDrawColor(renderer, (Uint8)(rgb >> 16), (Uint8)(rgb >> 8), (Uint8)rgb, 255);
        SDL_RenderDrawLine(renderer, x + 5, y + size - 2, x + size - 6, y + size - 2);
        if (hover) {
            open = i;
            open_x = x;
            open_y = y;
        }
    }
    if (open < 0)
        return;
    int w = RIGHT_W, px = open_x + size - w, py = open_y + size + 6;
    if (px < HUD_MARGIN)
        px = HUD_MARGIN;
    hud_plate(renderer, px, py, w, 50);
    ui_icon(renderer, states[open].icon, px + 12, py + 12, 2);
    int timer_width = states[open].time > 0.0f ? 70 : 0;
    hud_text_fit(renderer, states[open].name, px + 44, py + 7, w - 56 - timer_width, 2,
                 states[open].good ? COLOR_HUD_XP : COLOR_HUD_DANGER, ANCHOR_NW);
    hud_text_fit(renderer, states[open].note, px + 44, py + 31, w - 56, 1, COLOR_HUD_PRIMARY, ANCHOR_NW);
    if (states[open].time > 0.0f) {
        char str[16];
        snprintf(str, sizeof(str), "%.1f S", states[open].time);
        hud_text_fit(renderer, str, px + w - 12, py + 10, 68, 1, COLOR_HUD_PRIMARY, ANCHOR_NE);
    }
}

void hud_set_pointer(int x, int y)
{
    pointer_x = x;
    pointer_y = y;
}

static bool weapon_readout(const HudWeapon *weapon, char *str, size_t size)
{
    if (weapon->magazine > 0)
        snprintf(str, size, "%d/%d", weapon->rounds, weapon->magazine);
    else if (weapon->reloading)
        snprintf(str, size, "RECARGANDO");
    else if (weapon->magazine == 0)
        snprintf(str, size, "∞");
    else
        snprintf(str, size, "%d/%d", weapon->rounds, weapon->magazine);
    return weapon->reloading && weapon->magazine > 0;
}

/* Top middle: the gun's picture and name, its rounds (or "recargando"), and
 * the other gun with its key if she can switch. */
static void draw_weapon_panel(SDL_Renderer *renderer, const HudWeapon *weapon)
{
    char str[64];
    int x0 = WEAPON_X, y0 = 12;
    hud_top_panel(renderer, HUD_WEAPON);
    ui_weapon(renderer, weapon->id, x0 + 12, y0 + 16, 2);
    hud_text_fit(renderer, weapon->name, x0 + 92, y0 + 7, WEAPON_W - 104, 2,
                 COLOR_HUD_TITLE, ANCHOR_NW);
    ui_icon(renderer, weapon->id == WEAPON_SHOTGUN ? ICON_SHELL : ICON_BULLET, x0 + 92, y0 + 32, 1);
    bool reload_label = weapon_readout(weapon, str, sizeof(str));
    hud_text_fit(renderer, str, x0 + 110, y0 + 30, WEAPON_W - 122,
                 2,
                 weapon->reloading || (weapon->magazine > 0 && weapon->rounds == 0)
                     ? COLOR_HUD_DANGER : COLOR_HUD_PRIMARY, ANCHOR_NW);
    if (reload_label) {
        int after = 110 + ui_text_width(str, hud_text_scale(str, WEAPON_W - 122, 2)) + 10;
        if (after + ui_text_width("RECARGANDO", 1) <= WEAPON_W - 12)
            ui_text(renderer, "RECARGANDO", x0 + after, y0 + 35, 1, COLOR_HUD_DANGER, ANCHOR_NW);
        else
            ui_text(renderer, "RECARGANDO", x0 + 12, y0 + 1, 1, COLOR_HUD_DANGER, ANCHOR_NW);
    }
    if (weapon->can_swap) {
        int x = x0;
        ui_key(renderer, x, 72, "Q");
        ui_weapon(renderer, weapon->other_id, x + 48, 85, 1);
    }
}

/* Under the gun: the level-3 power on F, ready or how long until it is. */
static void draw_power_panel(SDL_Renderer *renderer, const HudWeapon *weapon)
{
    if (weapon->power == POWER_NONE)
        return;
    int w = weapon->can_swap ? 194 : 208, h = 42;
    int x0 = WEAPON_X + WEAPON_W - w, y0 = 72;
    hud_plate(renderer, x0, y0, w, h);
    int x = x0;
    x += ui_key(renderer, x, y0, "F") + 6;
    int picture = weapon->power == POWER_GRENADES ? UI_GRENADE : WEAPON_DUAL;
    ui_weapon(renderer, picture, x, y0 + 14, 1);
    x += UI_WEAPON_W + 6;
    char str[24];
    if (weapon->power_wait <= 0.0f) {
        hud_text_fit(renderer, weapon->power == POWER_GRENADES ? "GRANADA" : "REBOTE", x, y0 + 13,
                     x0 + w - x - 8, 2, COLOR_HUD_XP, ANCHOR_NW);
    } else {
        snprintf(str, sizeof(str), "%d S", (int)ceilf(weapon->power_wait));
        hud_text_fit(renderer, str, x, y0 + 13, x0 + w - x - 8, 2, COLOR_HUD_SECONDARY, ANCHOR_NW);
    }
}

static void draw_context(SDL_Renderer *renderer, const char *key, const char *label, unsigned ink)
{
    int scale = 2, key_w = key ? ui_key_width(key) + 10 : 0;
    if (key_w + ui_text_width(label, scale) > WINDOW_WIDTH - 48)
        scale = 1;
    int w = key_w + ui_text_width(label, scale);
    int x = (WINDOW_WIDTH - w) / 2, y = WINDOW_HEIGHT - 44;
    hud_plate(renderer, x - 12, y + 6, w + 24, 30);
    if (key)
        x += ui_key(renderer, x, y, key) + 10;
    ui_text(renderer, label, x, y + (scale == 2 ? 10 : 15), scale, ink, ANCHOR_NW);
}

/* A nearby hazard takes priority over the general fight instruction. The
 * route's kill count stays visible above while this contextual line changes. */
static void draw_prompt(SDL_Renderer *renderer, const Player *player, const StageRun *run)
{
    char str[80];
    if (run->phase != RUN_FIGHTING)
        return;
    if (player->state == PLAYER_CAUGHT) { /* First things first */
        snprintf(str, sizeof(str), "GOLPEA LA CUERDA · %d RESTANTES", player->catch_blows);
        draw_context(renderer, "V", str, COLOR_HUD_DANGER);
        return;
    }
    int kind = terrain_sign_ahead(&run->terrain, player->x, player->facing, SIGN_WARN_RANGE);
    if (kind >= 0) {
        bool bleeds = kind == TERRAIN_TRAP || kind == TERRAIN_SPIKES || kind == TERRAIN_WIRE;
        draw_context(renderer, NULL, bleeds ? "TRAMPA ADELANTE · U PARA VENDARTE"
                                            : "CUIDADO · HAY UNA TRAMPA ADELANTE", COLOR_HUD_TITLE);
    } else if (terrain_wire_ahead(&run->terrain, player->x, player->facing, WIRE_WARN_RANGE)) {
        draw_context(renderer, "V", "ALAMBRE · CULATAZO O DISPARO", COLOR_HUD_DANGER);
    } else if (terrain_wall_near(&run->terrain, player->x)) {
        draw_context(renderer, run->dynamite > 0 ? "E" : NULL,
                     run->dynamite > 0 ? "COLOCAR DINAMITA" : "ESTE MURO NECESITA DINAMITA O UN BARRIL",
                     run->dynamite > 0 ? COLOR_HUD_TITLE : COLOR_HUD_DANGER);
    } else if (player->state == PLAYER_SIT) {
        draw_context(renderer, "A/D", "LEVANTARSE", COLOR_HUD_PRIMARY);
    } else if (terrain_bench_near(&run->terrain, player->x) >= 0 && player->jump.height <= 0.0f) {
        draw_context(renderer, "E", "DESCANSAR", COLOR_HUD_TITLE);
    } else if (terrain_barricade_ahead(&run->terrain, player->x, player->facing) &&
               player->jump.height <= 0.0f) {
        draw_context(renderer, "N", "CRUZAR BARRICADA", COLOR_HUD_TITLE);
    } else if (run_fight_left(run) > 0) {
        int left = run_fight_left(run);
        snprintf(str, sizeof(str), "DESPEJA EL CAMINO · %s %d", left == 1 ? "FALTA" : "FALTAN", left);
        draw_context(renderer, NULL, str, COLOR_HUD_DANGER);
    } else if (run->defeated >= run->stage->zombies) {
        draw_context(renderer, NULL, "EL COFRE TE ESPERA EN LA SALIDA →", COLOR_HUD_TITLE);
    }
}

/* A message board in the middle: title, then key hints. */
static void draw_message(SDL_Renderer *renderer, const char *title, unsigned rgb,
                         const char *const *hints, int hint_count)
{
    int w = 560, h = 150, x = (WINDOW_WIDTH - w) / 2, y = 150;
    ui_dim(renderer, 110);
    ui_panel(renderer, x, y, w, h);
    ui_text(renderer, title, WINDOW_WIDTH / 2, y + 32, 3, rgb, ANCHOR_N);
    draw_hints(renderer, hints, hint_count, y + 92);
}

void hud_draw_stage(SDL_Renderer *renderer, const Player *player, const Zombie *zombies,
                    int zombie_count, const Progress *progress, const StageRun *run,
                    float camera_x, const HudWeapon *weapon)
{
    draw_tags(renderer, player, zombies, zombie_count, camera_x);
    draw_popups(renderer, camera_x);
    draw_road_panel(renderer, player, run);
    draw_gold(renderer, player, progress, run);
    draw_life_panel(renderer, player, progress);
    draw_weapon_panel(renderer, weapon);
    draw_power_panel(renderer, weapon);
    draw_states(renderer, player, run);
    draw_prompt(renderer, player, run);

    if (run->phase == RUN_FAILED) {
        static const char *const hints[] = {"R", "REINTENTAR", "ESC", "PAUSA"};
        draw_message(renderer, player->fainted ? "TE DESMAYASTE POR EL CALOR" : "TE ALCANZÓ EL ZOMBI",
                     COLOR_HUD_DANGER, hints, 2);
    } else if (run->phase == RUN_CLEARED) {
        static const char *const hints[] = {"ENTER", "CONTINUAR"};
        char str[48];
        snprintf(str, sizeof(str), "¡NIVEL %s COMPLETADO!", run->stage->name);
        draw_message(renderer, str, COLOR_HUD_XP, hints, 1);
    }
}

static bool layout_text_fits(const char *str, int width, int preferred_scale)
{
    int measured = ui_text_width(str, hud_text_scale(str, width, preferred_scale));
    if (measured <= width)
        return true;
    fprintf(stderr, "HUD: '%s' necesita %d px, dispone de %d.\n", str, measured, width);
    return false;
}

bool hud_verify_layout(void)
{
    if (!pixfont_init())
        return false;
    bool ok = true;
    SDL_Rect sky = {0, 0, WINDOW_WIDTH, VIEW_TOP};
    for (int i = 0; i < 3; i++) {
        const SDL_Rect *r = &HUD_REGIONS[i];
        SDL_Rect intersection;
        if (!SDL_IntersectRect(r, &sky, &intersection) || !SDL_RectEquals(r, &intersection)) {
            fprintf(stderr, "HUD: panel %d fuera de la franja superior.\n", i);
            ok = false;
        }
        for (int j = i + 1; j < 3; j++)
            if (SDL_HasIntersection(r, &HUD_REGIONS[j])) {
                fprintf(stderr, "HUD: paneles %d y %d superpuestos.\n", i, j);
                ok = false;
            }
    }
    /* Use the actual formatter and font metrics with full integer totals;
     * the compact fallback must preserve the complete health/ammo numbers. */
    char str[80];
    snprintf(str, sizeof(str), "%d/%d", INT_MAX, INT_MAX);
    ok = layout_text_fits(str, RIGHT_W - 210, 2) && ok;
    snprintf(str, sizeof(str), "XP %d/%d", INT_MAX, INT_MAX);
    ok = layout_text_fits(str, RIGHT_W - 210, 1) && ok;
    snprintf(str, sizeof(str), "SALIDA %d M", INT_MAX);
    ok = layout_text_fits(str, LEFT_W / 2 - 8, 1) && ok;
    snprintf(str, sizeof(str), "%d/%d ZOMBIS", INT_MAX, INT_MAX);
    ok = layout_text_fits(str, LEFT_W - 42, 1) && ok;
    snprintf(str, sizeof(str), "%d", INT_MAX);
    if (3 * (18 + ui_text_width(str, 1)) + 20 > LEFT_W - 16) {
        fprintf(stderr, "HUD: suministros máximos exceden su columna.\n");
        ok = false;
    }
    for (int id = 0; id < WEAPON_COUNT; id++) {
        const WeaponDef *def = weapon_def((WeaponId)id);
        ok = layout_text_fits(def->name, WEAPON_W - 104, 2) && ok;
        HudWeapon weapon = {.id = id, .name = def->name, .rounds = INT_MAX,
                            .magazine = INT_MAX, .reloading = true};
        weapon_readout(&weapon, str, sizeof(str));
        ok = layout_text_fits(str, WEAPON_W - 122, 1) && ok;
    }
    static const char *const critical[] = {
        "SANGRADO", "GOLPE DE CALOR", "DESHIDRATACIÓN", "VENDANDO 100%",
    };
    for (int i = 0; i < (int)(sizeof(critical) / sizeof(critical[0])); i++)
        ok = layout_text_fits(critical[i], LEFT_W - 16, 2) && ok;
    ok = layout_text_fits("GRANADA", 194 - 42 - 6 - UI_WEAPON_W - 6 - 8, 2) && ok;
    ok = layout_text_fits("999+", BADGE_W * BADGE_SCALE - 4, 1) && ok;
    /* The last of eighteen possible state cells stays above the world and
     * inside the life column, including when effects need a second row. */
    int columns = (RIGHT_W - 8) / 28;
    int state_left = WINDOW_WIDTH - HUD_MARGIN - 24 - (columns - 1) * 28;
    int state_bottom = 76 + (17 / columns) * 28 + 24;
    if (state_left < HUD_REGIONS[HUD_LIFE].x || state_bottom > VIEW_TOP) {
        fprintf(stderr, "HUD: estados fuera de su columna.\n");
        ok = false;
    }
    return ok;
}

/* A column of buttons centered at cx, from y. */
static void draw_buttons(SDL_Renderer *renderer, const char *const *labels, int count, int selected,
                         int cx, int y, int w, int h, int gap)
{
    for (int i = 0; i < count; i++) {
        ui_button(renderer, cx - w / 2, y + i * (h + gap), w, h, labels[i], i == selected, true);
        add_zone(HUD_ZONE_ITEM, i, cx - w / 2, y + i * (h + gap), w, h);
    }
}

void hud_draw_title(SDL_Renderer *renderer, const ListMenu *menu)
{
    static const char *const labels[TITLE_ITEMS] = {"JUGAR", "ALMANAQUE", "CONTROLES", "VOLUMEN", "SALIR"};
    ui_text(renderer, "VAQUERA 2D", WINDOW_WIDTH / 2, 46, 8, COLOR_HUD_TITLE, ANCHOR_N);
    ui_text(renderer, "ZOMBIS EN EL VIEJO OESTE", WINDOW_WIDTH / 2, 142, 2, COLOR_HUD_PRIMARY, ANCHOR_N);
    ui_panel(renderer, WINDOW_WIDTH / 2 - 190, 186, 380, 282);
    draw_buttons(renderer, labels, TITLE_ITEMS, menu->selected, WINDOW_WIDTH / 2, 202, 320, 42, 10);
    static const char *const hints[] = {"W/S", "ELEGIR", "ENTER", "ACEPTAR"};
    draw_hints(renderer, hints, 2, WINDOW_HEIGHT - 58);
}

void hud_draw_controls(SDL_Renderer *renderer)
{
    static const struct {
        const char *keys[3];
        const char *action;
    } rows[] = {
        {{"A", "D", NULL}, "CAMINAR  (TAMBIÉN ← / →)"},
        {{"SHIFT", NULL, NULL}, "CORRER"},
        {{"ESPACIO", "W", NULL}, "SALTAR  (Y SUBIR A UNA BARRICADA)"},
        {{"N", NULL, NULL}, "ATRAVESAR UNA BARRICADA BAJA"},
        {{"CLIC IZQ", NULL, NULL}, "DISPARAR  (MANTENER: RÁFAGAS)"},
        {{"R", NULL, NULL}, "RECARGAR"},
        {{"Q", "CLIC DER", NULL}, "CAMBIAR DE ARMA  (SWAT)"},
        {{"E", NULL, NULL}, "DINAMITA (MURO O SUELO) / SENTARSE"},
        {{"F", "CLIC CENTRAL", NULL}, "PODER (NIVEL 3): GRANADA / DISPARO DE REBOTE"},
        {{"V", NULL, NULL}, "CULATAZO  (CORTA ALAMBRE, ROMPE CAJAS)"},
        {{"U", NULL, NULL}, "MANTÉN: VENDARSE · PULSA: BEBER"},
        {{"ESC", NULL, NULL}, "PAUSA"},
    };
    int count = (int)(sizeof(rows) / sizeof(rows[0]));
    int w = 860, h = 56 + count * 34 + 8, x = (WINDOW_WIDTH - w) / 2, y = 6;
    ui_panel(renderer, x, y, w, h);
    ui_text(renderer, "CONTROLES", WINDOW_WIDTH / 2, y + 16, 3, COLOR_HUD_TITLE, ANCHOR_N);
    ui_key(renderer, x + 32, y + 10, "B");
    ui_text(renderer, "ALMANAQUE", x + 78, y + 25, 1, COLOR_HUD_PRIMARY, ANCHOR_NW);
    ui_key(renderer, x + w - 182, y + 10, "L");
    ui_text(renderer, "LINTERNA", x + w - 136, y + 25, 1, COLOR_HUD_PRIMARY, ANCHOR_NW);
    for (int i = 0; i < count; i++) {
        int ry = y + 54 + i * 34, kx = x + 36;
        for (int k = 0; k < 3 && rows[i].keys[k]; k++) {
            if (k > 0)
                kx += ui_text(renderer, "/", kx + 6, ry + 12, 2, COLOR_HUD_SECONDARY, ANCHOR_NW) + 12;
            kx += ui_key(renderer, kx, ry, rows[i].keys[k]);
        }
        hud_text_fit(renderer, rows[i].action, x + 330, ry + 12, w - 350, 2,
                     COLOR_HUD_PRIMARY, ANCHOR_NW);
    }
    static const char *const hints[] = {"ESC", "VOLVER"};
    draw_hints(renderer, hints, 1, y + h + 8);
}

void hud_draw_volume(SDL_Renderer *renderer, const ListMenu *menu, const Volumes *volumes)
{
    static const char *const names[] = {"GENERAL", "PERSONAJE", "ZOMBIS"};
    const int values[] = {volumes->master, volumes->player, volumes->zombie};
    int w = 620, h = 330, x = (WINDOW_WIDTH - w) / 2, y = 90;
    ui_panel(renderer, x, y, w, h);
    ui_text(renderer, "VOLUMEN", WINDOW_WIDTH / 2, y + 22, 3, COLOR_HUD_TITLE, ANCHOR_N);
    for (int i = 0; i < 3; i++) {
        int ry = y + 82 + i * 56;
        bool selected = menu->selected == i;
        add_zone(HUD_ZONE_ITEM, i, x + 24, ry - 10, w - 48, 50);
        if (selected)
            ui_button(renderer, x + 24, ry - 10, w - 48, 50, "", true, true);
        ui_icon(renderer, ICON_SPEAKER, x + 44, ry, 2);
        ui_text(renderer, names[i], x + 80, ry + 4, 2, selected ? COLOR_HUD_TITLE : COLOR_HUD_PRIMARY,
                ANCHOR_NW);
        int bar_w = ui_pips(renderer, x + 270, ry - 1, values[i], VOLUME_STEPS);
        add_zone(HUD_ZONE_VOLUME, i, x + 270, ry - 10, bar_w, 50);
    }
    ui_button(renderer, WINDOW_WIDTH / 2 - 110, y + h - 70, 220, 44, "VOLVER",
              menu->selected == VOLUME_BACK, true);
    add_zone(HUD_ZONE_ITEM, VOLUME_BACK, WINDOW_WIDTH / 2 - 110, y + h - 70, 220, 44);
    static const char *const hints[] = {"W/S", "ELEGIR", "A/D", "BAJAR/SUBIR", "ESC", "VOLVER"};
    draw_hints(renderer, hints, 3, WINDOW_HEIGHT - 52);
}

void hud_draw_pause(SDL_Renderer *renderer, const ListMenu *menu)
{
    static const char *const labels[PAUSE_ITEMS] = {"CONTINUAR", "REINICIAR NIVEL", "ALMANAQUE", "VOLUMEN",
                                                    "CONTROLES", "SALIR AL MENÚ"};
    ui_dim(renderer, 150);
    int w = 400, h = 408, x = (WINDOW_WIDTH - w) / 2, y = 28;
    ui_panel(renderer, x, y, w, h);
    ui_text(renderer, "PAUSA", WINDOW_WIDTH / 2, y + 20, 3, COLOR_HUD_TITLE, ANCHOR_N);
    draw_buttons(renderer, labels, PAUSE_ITEMS, menu->selected, WINDOW_WIDTH / 2, y + 64, 330, 46, 10);
    /* Right under the board, clear of the gun's panel. */
    static const char *const hints[] = {"W/S", "ELEGIR", "ENTER", "ACEPTAR", "ESC", "SEGUIR"};
    draw_hints(renderer, hints, 3, y + h + 10);
}

void hud_draw_menu(SDL_Renderer *renderer, const char *character_name, const Progress *progress,
                   const StageRecord *record, int selected)
{
    char str[96];
    ui_text(renderer, "ELIGE UN NIVEL", WINDOW_WIDTH / 2, 18, 4, COLOR_HUD_TITLE, ANCHOR_N);
    int name_w = ui_text_width(character_name, 2);
    ui_text(renderer, character_name, WINDOW_WIDTH / 2 - 30 - name_w, 74, 2, COLOR_HUD_PRIMARY, ANCHOR_NW);
    draw_badge(renderer, WINDOW_WIDTH / 2, 104, progress->level, BADGE_PLAYER, false);
    snprintf(str, sizeof(str), "XP %d/%d", progress->xp, xp_to_next(progress->level));
    ui_text(renderer, str, WINDOW_WIDTH / 2 + 30, 74, 2, COLOR_HUD_XP, ANCHOR_NW);

    int w = 600, row_h = 54, x = (WINDOW_WIDTH - w) / 2, top = 118;
    ui_panel(renderer, x - 20, top - 14, w + 40, STAGE_COUNT * (row_h + 8) + 22);
    for (int i = 0; i < STAGE_COUNT && i < 16; i++) {
        const StageDef *stage = &STAGES[i];
        bool open = stage_unlocked(record, i);
        int y = top + i * (row_h + 8);
        ui_button(renderer, x, y, w, row_h, "", i == selected, open);
        add_zone(HUD_ZONE_ITEM, i, x, y, w, row_h);
        unsigned ink = open ? (i == selected ? COLOR_HUD_TITLE : COLOR_HUD_PRIMARY) : COLOR_HUD_LOCKED;
        ui_text(renderer, stage->name, x + 24, y + 14, 3, ink, ANCHOR_NW);
        draw_badge(renderer, x + 150, y + row_h - 6, stage->zombie_level, BADGE_ZOMBIE, !open);
        snprintf(str, sizeof(str), "%d ZOMBIS%s", stage->zombies, stage->boss_bonus ? " + JEFE" : "");
        ui_icon(renderer, ICON_SKULL, x + 184, y + 14, 2);
        ui_text(renderer, str, x + 214, y + 18, 2, open ? COLOR_HUD_SECONDARY : COLOR_HUD_LOCKED, ANCHOR_NW);
        snprintf(str, sizeof(str), "%d M", (int)(stage->length / ROUTE_PX_PER_METER));
        ui_icon(renderer, ICON_FLAG, x + 384, y + 14, 2);
        ui_text(renderer, str, x + 414, y + 18, 2, open ? COLOR_HUD_SECONDARY : COLOR_HUD_LOCKED, ANCHOR_NW);
        if (record->cleared[i])
            ui_icon(renderer, ICON_CHECK, x + w - 52, y + 14, 2);
        else if (!open)
            ui_icon(renderer, ICON_LOCK, x + w - 52, y + 14, 2);
    }
    static const char *const hints[] = {"W/S", "ELEGIR", "ENTER", "JUGAR", "ESC", "PERSONAJES"};
    draw_hints(renderer, hints, 3, WINDOW_HEIGHT - 52);
}

/* Text centered at cx from y, broken at spaces into lines no wider than
 * max_w, line_h apart. Returns the y under its last line. */
static int draw_wrapped(SDL_Renderer *renderer, const char *text, int cx, int y, int max_w, int line_h,
                        unsigned rgb)
{
    char line[272] = "", word[64];
    const char *p = text;
    while (*p) {
        int n = 0;
        while (p[n] && p[n] != ' ' && n < (int)sizeof(word) - 1)
            n++;
        memcpy(word, p, (size_t)n);
        word[n] = '\0';
        p += n;
        while (*p == ' ')
            p++;
        char trial[272];
        snprintf(trial, sizeof(trial), "%s%s%s", line, line[0] ? " " : "", word);
        if (line[0] && ui_text_width(trial, 2) > max_w) {
            ui_text(renderer, line, cx, y, 2, rgb, ANCHOR_N);
            y += line_h;
            snprintf(line, sizeof(line), "%s", word);
        } else {
            snprintf(line, sizeof(line), "%s", trial);
        }
    }
    if (line[0]) {
        ui_text(renderer, line, cx, y, 2, rgb, ANCHOR_N);
        y += line_h;
    }
    return y;
}

/* One character's card: its standing frame, level, ability and guns. */
static void draw_card(SDL_Renderer *renderer, const CharacterSkin *skin, const Progress *progress,
                      int index, bool selected)
{
    const CharacterDef *c = skin->character;
    int left = (WINDOW_WIDTH - (3 * CARD_W + 2 * CARD_GAP)) / 2 + index * (CARD_W + CARD_GAP);
    int cx = left + CARD_W / 2;
    if (selected)
        ui_button(renderer, left - 6, CARD_TOP - 6, CARD_W + 12, CARD_H + 12, "", true, true);
    add_zone(HUD_ZONE_ITEM, index, left, CARD_TOP, CARD_W, CARD_H);
    ui_panel(renderer, left, CARD_TOP, CARD_W, CARD_H);

    /* Standing frame of its walk sheet, a little smaller than in play. */
    SDL_Texture *walk = skin->sheets[0];
    int portrait_top = CARD_TOP + 2;
    if (walk) {
        SDL_Rect src = {0, 0, PLAYER_WALK_FRAME_W, PLAYER_WALK_FRAME_H};
        SDL_Rect dst = {cx - PLAYER_WALK_FRAME_W * PORTRAIT_SCALE / 2, portrait_top,
                        PLAYER_WALK_FRAME_W * PORTRAIT_SCALE, PLAYER_WALK_FRAME_H * PORTRAIT_SCALE};
        Uint8 shade = selected ? 255 : 140;
        SDL_SetTextureColorMod(walk, shade, shade, shade);
        SDL_RenderCopy(renderer, walk, &src, &dst);
        SDL_SetTextureColorMod(walk, 255, 255, 255);
    }
    draw_badge(renderer, left + 40, CARD_TOP + 64, progress->level, BADGE_PLAYER, !selected);
    if (skin->placeholder)
        ui_text(renderer, "ARTE PROVISIONAL", cx, portrait_top + PLAYER_WALK_FRAME_H * PORTRAIT_SCALE - 22,
                2, COLOR_HUD_LOCKED, ANCHOR_N);

    /* Name, its guns as they look in play, then its ability. */
    int y = portrait_top + PLAYER_WALK_FRAME_H * PORTRAIT_SCALE + 4;
    ui_text(renderer, c->name, cx, y, 3, selected ? COLOR_HUD_TITLE : COLOR_HUD_PRIMARY, ANCHOR_N);
    int guns_w = c->weapon_count * (UI_WEAPON_W * 2 + 12) - 12;
    for (int g = 0; g < c->weapon_count; g++)
        ui_weapon(renderer, c->weapons[g], cx - guns_w / 2 + g * (UI_WEAPON_W * 2 + 12), y + 34, 2);
    y += 34;
    ui_text(renderer, c->ability_name, cx, y + 36, 2, COLOR_HUD_XP, ANCHOR_N);
    char ability[160] = "";
    for (int l = 0; l < CHARACTER_ABILITY_LINES && c->ability_lines[l]; l++)
        snprintf(ability + strlen(ability), sizeof(ability) - strlen(ability), "%s%s", l ? " " : "",
                 c->ability_lines[l]);
    int under = draw_wrapped(renderer, ability, cx, y + 58, CARD_W - 2 * CARD_PAD - 2 * 8 * UI_SCALE, 20,
                             COLOR_HUD_SECONDARY);
    if (c->power_name) /* Its level-3 power: lit once it has it */
        ui_text(renderer, c->power_name, cx, under + 6, 2,
                progress->level >= POWER_LEVEL ? COLOR_HUD_LEVEL : COLOR_HUD_LOCKED, ANCHOR_N);
}

void hud_draw_characters(SDL_Renderer *renderer, const CharacterSkin *skins,
                         const Progress *progress, int selected)
{
    ui_text(renderer, "ELIGE TU PERSONAJE", WINDOW_WIDTH / 2, 26, 4, COLOR_HUD_TITLE, ANCHOR_N);
    for (int i = 0; i < CHARACTER_COUNT && i < 8; i++)
        draw_card(renderer, &skins[i], &progress[i], i, i == selected);
    static const char *const hints[] = {"A/D", "ELEGIR", "ENTER", "CONTINUAR", "ESC", "VOLVER"};
    draw_hints(renderer, hints, 3, WINDOW_HEIGHT - 50);
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
    for (int i = 0; i < POPUP_MAX; i++)
        popups[i].active = false;
}
