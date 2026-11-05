#include "game/hud.h"

#include <limits.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

#include "config.h"
#include "engine/assets.h"
#include "engine/pixfont.h"
#include "game/hang_render.h"
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

/* Three columns inside the sky band, ordered by what a player looks for:
 * herself on the left, the mission in the middle, the gun on the right. Each
 * has one main plate; everything under it appears only when it applies. The
 * world starts at VIEW_TOP, so none of this ever covers the fight. */
#define HUD_MARGIN 12
#define HUD_GAP 12
#define HUD_TOP 8
#define TOP_H 60
#define VITALS_W 324
#define MISSION_W 264
#define WEAPON_W 324
#define VITALS_X HUD_MARGIN
#define MISSION_X (VITALS_X + VITALS_W + HUD_GAP)
#define WEAPON_X (MISSION_X + MISSION_W + HUD_GAP)
#define XP_BAR_W 68
#define EXIT_W 146 /* "SALIDA 9999 M" at scale two */
#define ROUTE_W (MISSION_W - 24 - EXIT_W)
#define DEFEATED_W 62 /* "22/22" at scale two */
#define CLOCK_ICON_W 16 /* The clock's icon and the gap before its time */

/* Second row: supplies, a critical alert, gun shortcuts. */
#define CHIP_Y (HUD_TOP + TOP_H + 4)
#define CHIP_H 28
#define HUD_KEY_SIZE 28 /* ui_key_compact with a one-letter label */
#define SWAP_W 84
#define POWER_W 232

/* Third row: her conditions from the left, the save status on the right. */
#define STATE_Y (CHIP_Y + CHIP_H + 4)
#define STATE_H 24
#define STATE_GAP 4
#define STATES_W (VITALS_W + HUD_GAP + MISSION_W)
#define STATE_TIP_W 600
#define STATE_TIP_H 62
#define STATE_MAX 19 /* Entries in draw_states' table */

enum { HUD_VITALS, HUD_MISSION, HUD_WEAPON };
static const SDL_Rect HUD_REGIONS[] = {
    {VITALS_X, HUD_TOP, VITALS_W, TOP_H},
    {MISSION_X, HUD_TOP, MISSION_W, TOP_H},
    {WEAPON_X, HUD_TOP, WEAPON_W, TOP_H},
};

#define RESULT_W 708
#define RESULT_H 444
#define RESULT_STAR_SCALE 6
#define RESULT_STAR_GAP 16
#define MISSION_GOALS_W 452
#define MISSION_GOALS_H 174

#define POPUP_MAX 6
#define POPUP_TIME 1.4f
#define POPUP_RISE 40.0f /* px it climbs over its life */
#define POPUP_LIFT 26 /* Window px up, so a line starts clear of the level badge */

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

/* The y that centers a line of text in a band: the glyphs' 7 rows start 2 rows
 * into their cell (room for accents). */
static int hud_centered_y(int y, int h, int scale)
{
    return y + (h - 7 * scale) / 2 - 2 * scale;
}

static void hud_top_panel(SDL_Renderer *renderer, int index)
{
    const SDL_Rect *r = &HUD_REGIONS[index];
    hud_plate(renderer, r->x, r->y, r->w, r->h);
}

/* A lighter recess behind a gun's picture: the guns are dark art and would
 * otherwise sink into the leather. */
static void hud_well(SDL_Renderer *renderer, int x, int y, int w, int h)
{
    SDL_Rect well = {x, y, w, h};
    SDL_SetRenderDrawColor(renderer, 124, 104, 84, 255);
    SDL_RenderFillRect(renderer, &well);
    SDL_SetRenderDrawColor(renderer, 24, 17, 16, 255);
    SDL_RenderDrawRect(renderer, &well);
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
    float head = BASELINE - (PLAYER_HEAD_HEIGHT - player_sunk_rows(player)) * SPRITE_SCALE - player->jump.height;
    if (player->state == PLAYER_CAUGHT && player->catch_kind != CATCH_NONE) /* Over what hangs */
        head = BASELINE - hang_top(player->catch_kind, player->catch_time);
    draw_badge(renderer, view_x(player->x - camera_x), view_y(head) - TAG_GAP, player->level,
               BADGE_PLAYER, false);
    for (int i = 0; i < zombie_count; i++) {
        const Zombie *zombie = &zombies[i];
        float screen_x = zombie->x - camera_x;
        if (zombie->stats == NULL || !zombie_alive(zombie) || zombie->hidden || screen_x < -80.0f ||
            screen_x > VIEW_WIDTH + 80.0f)
            continue;
        float top = BASELINE - zombie_body_height(zombie) - 14.0f + /* Its health bar */
                    lroundf(zombie->depth * RIVER_DEEP_ROWS) * SPRITE_SCALE; /* Sunk with it, wading */
        if (zombie->caught > 0.0f && zombie->catch_kind != CATCH_NONE)
            top = fminf(top, BASELINE - hang_top(zombie->catch_kind, zombie->catch_time));
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
        pixfont_draw(renderer, p->str, view_x(p->world_x - camera_x), view_y((float)p->y) - POPUP_LIFT -
                     (int)lroundf(POPUP_RISE * t), p->big ? 3 : 2, p->rgb, ANCHOR_N,
                     (Uint8)lroundf(alpha * 255.0f));
    }
}

/* Middle: the clock, centered on the window; which route and how far to its
 * exit; then the zombies beaten and how much of the fight that is. */
static void draw_mission(SDL_Renderer *renderer, const Player *player, const StageRun *run)
{
    char str[64];
    int x = MISSION_X + 12, right = MISSION_X + MISSION_W - 12, y0 = HUD_TOP;
    hud_top_panel(renderer, HUD_MISSION);
    char time[24];
    mission_format_time(run->mission.ticks, time, sizeof(time));
    int time_w = ui_text_width(time, 2), clock_w = CLOCK_ICON_W + time_w;
    int clock_x = WINDOW_WIDTH / 2 - clock_w / 2;
    ui_icon(renderer, ICON_CLOCK, clock_x, y0 + 5, 1);
    ui_text(renderer, time, clock_x + CLOCK_ICON_W, y0, 2, COLOR_HUD_TITLE, ANCHOR_NW);
    snprintf(str, sizeof(str), "RUTA %s", run->stage->name);
    hud_text_fit(renderer, str, x, y0 + 19, ROUTE_W, 2, COLOR_HUD_TITLE, ANCHOR_NW);
    int meters = (int)fmaxf(0.0f, (run->goal_x - player->x) / ROUTE_PX_PER_METER);
    snprintf(str, sizeof(str), "SALIDA %d M", meters);
    hud_text_fit(renderer, str, right, y0 + 19, EXIT_W, 2, COLOR_HUD_PRIMARY, ANCHOR_NE);
    ui_icon(renderer, ICON_SKULL, x, y0 + 43, 1);
    snprintf(str, sizeof(str), "%d/%d", run->defeated, run->stage->zombies);
    hud_text_fit(renderer, str, x + 16, y0 + 38, DEFEATED_W, 2, COLOR_HUD_PRIMARY, ANCHOR_NW);
    float share = run->stage->zombies > 0 ? (float)run->defeated / (float)run->stage->zombies : 1.0f;
    int bar_x = x + 16 + DEFEATED_W + 6;
    hud_meter(renderer, bar_x, y0 + 44, right - bar_x, 9, share, 0x9c7044, 0xcd9b5b);
}

/* Under her health: what she carries. Dynamite shows once she has some. */
static void draw_supplies(SDL_Renderer *renderer, const Player *player, const Progress *progress,
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
            width += 16 + ui_text_width(values[i], scale) + (i ? 14 : 0);
        if (width <= VITALS_W - 20 || scale == 1)
            break;
        scale--;
    } while (true);
    hud_plate(renderer, VITALS_X, CHIP_Y, width + 20, CHIP_H);
    int x = VITALS_X + 10;
    for (int i = 0; i < count; i++) {
        ui_icon(renderer, icons[i], x, CHIP_Y + (CHIP_H - UI_ICON_SIZE) / 2, 1);
        x += 16;
        x += ui_text(renderer, values[i], x, hud_centered_y(CHIP_Y, CHIP_H, scale), scale,
                     i == 0 ? COLOR_HUD_TITLE : COLOR_HUD_PRIMARY, ANCHOR_NW) + 14;
    }
}

/* What needs doing right now, by name and with its key, even without hovering
 * an icon. It appears only then, so it stands out when it does. */
static void draw_alert(SDL_Renderer *renderer, const Player *player)
{
    char label[32] = "";
    const char *action = NULL, *key = NULL;
    unsigned ink = COLOR_HUD_DANGER;
    if (player->bandage > 0.0f) {
        snprintf(label, sizeof(label), "VENDANDO %d%%", (int)(100.0f * player->bandage / BANDAGE_TIME));
        ink = COLOR_HUD_TITLE;
    } else if (player->bleeding) {
        snprintf(label, sizeof(label), "SANGRADO");
        action = "MANTÉN";
        key = "U";
    } else if (player->fatigue >= FATIGUE_STROKE) {
        snprintf(label, sizeof(label), "¡ALÉJATE DEL FUEGO!");
    } else if (player_thirst_level(player) >= 2) {
        snprintf(label, sizeof(label), "SED GRAVE");
        action = "BEBE";
        key = "U";
    } else if (player->drink_time > 0.0f) {
        snprintf(label, sizeof(label), "BEBIENDO");
        ink = COLOR_HUD_TITLE;
    }
    if (!player_alive(player) || !label[0])
        return;
    int width = ui_text_width(label, 2);
    if (key)
        width += 10 + ui_text_width(action, 2) + 6 + HUD_KEY_SIZE;
    hud_plate(renderer, MISSION_X, CHIP_Y, MISSION_W, CHIP_H);
    SDL_Rect accent = {MISSION_X, CHIP_Y, 3, CHIP_H};
    SDL_SetRenderDrawColor(renderer, (Uint8)(ink >> 16), (Uint8)(ink >> 8), (Uint8)ink, 255);
    SDL_RenderFillRect(renderer, &accent);
    int x = MISSION_X + (MISSION_W - width) / 2, y = hud_centered_y(CHIP_Y, CHIP_H, 2);
    x += ui_text(renderer, label, x, y, 2, ink, ANCHOR_NW);
    if (key) {
        x += 10;
        x += ui_text(renderer, action, x, y, 2, COLOR_HUD_PRIMARY, ANCHOR_NW) + 6;
        ui_key_compact(renderer, x, CHIP_Y, key);
    }
}

/* Left: her level, her health with its numbers on the bar, XP under it. */
static void draw_vitals(SDL_Renderer *renderer, const Player *player, const Progress *progress)
{
    char str[48];
    int x0 = VITALS_X, y0 = HUD_TOP, x = x0 + 74, w = VITALS_W - 84, bar_y = y0 + 7, bar_h = 22;
    hud_top_panel(renderer, HUD_VITALS);
    draw_badge(renderer, x0 + 24, y0 + (TOP_H + BADGE_H * BADGE_SCALE) / 2, progress->level, BADGE_PLAYER, false);
    ui_icon(renderer, ICON_HEART, x0 + 46, y0 + 6, 2);
    float life = player->max_health > 0 ? (float)player->health / (float)player->max_health : 0.0f;
    hud_meter(renderer, x, bar_y, w, bar_h, life, COLOR_HEALTH_FILL, 0xe07a50);
    if (life <= 0.25f) {
        SDL_Rect frame = {x, bar_y, w, bar_h};
        unsigned rgb = COLOR_HUD_DANGER;
        SDL_SetRenderDrawColor(renderer, (Uint8)(rgb >> 16), (Uint8)(rgb >> 8), (Uint8)rgb, 255);
        SDL_RenderDrawRect(renderer, &frame);
    }
    snprintf(str, sizeof(str), "%d/%d", player->health, player->max_health);
    int scale = hud_text_scale(str, w - 8, 2), text_y = hud_centered_y(bar_y, bar_h, scale);
    ui_text(renderer, str, x + w / 2 + 1, text_y + 1, scale, 0x140e0c, ANCHOR_N); /* Legible on any fill */
    ui_text(renderer, str, x + w / 2, text_y, scale, COLOR_HUD_TITLE, ANCHOR_N);
    ui_icon(renderer, ICON_STAR, x0 + 52, y0 + 38, 1);
    int need = xp_to_next(progress->level);
    hud_meter(renderer, x, y0 + 39, XP_BAR_W, 10, need > 0 ? (float)progress->xp / (float)need : 1.0f,
              COLOR_HUD_XP, 0xb0e090);
    snprintf(str, sizeof(str), "XP %d/%d", progress->xp, need);
    scale = hud_text_scale(str, w - XP_BAR_W - 8, 2);
    ui_text(renderer, str, x + w, hud_centered_y(y0 + 34, 20, scale), scale, COLOR_HUD_XP, ANCHOR_NE);
}

/* Where the mouse is (hud_set_pointer). */
static int pointer_x = -1, pointer_y = -1;

/* The bottom row: what helps or ails her now, each an icon (and the seconds
 * left, if it wears off) underlined green or red; the mouse over one opens it:
 * a name and what it means. */
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
        float time; /* 0: lasts while it lasts (bleeding: till bandaged) */
        bool good;
    } states[] = {
        {player->bleeding, ICON_BLOOD, "SANGRADO", bleed_note, 0.0f, false},
        {player->burned, ICON_COZY, "QUEMADURA",
         player->burn_bandaged ? "BEBE AGUA CON U PARA CURARLA" : "TE CURAS Y CAMINAS MÁS LENTO. MANTÉN U: VÉNDATE",
         0.0f, false},
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
    /* One row: if the seconds would not fit beside every icon, the row drops
     * them. They stay available in each icon's description. */
    int count = (int)(sizeof(states) / sizeof(states[0]));
    char times[sizeof(states) / sizeof(states[0])][16];
    int total = 0;
    for (int i = 0; i < count; i++) {
        times[i][0] = '\0';
        if (!states[i].on)
            continue;
        if (states[i].time > 99.0f)
            snprintf(times[i], sizeof(times[i]), "99+");
        else if (states[i].time > 0.0f)
            snprintf(times[i], sizeof(times[i]), "%d", (int)ceilf(states[i].time));
        total += STATE_H + STATE_GAP + (times[i][0] ? ui_text_width(times[i], 2) + 2 : 0);
    }
    bool compact = total > STATES_W;
    int x = VITALS_X, open = -1, open_x = 0;
    for (int i = 0; i < count; i++) {
        if (!states[i].on)
            continue;
        int w = STATE_H + (!compact && times[i][0] ? ui_text_width(times[i], 2) + 2 : 0);
        bool hover = pointer_x >= x && pointer_x < x + w && pointer_y >= STATE_Y && pointer_y < STATE_Y + STATE_H;
        hud_plate(renderer, x, STATE_Y, w, STATE_H);
        ui_icon(renderer, states[i].icon, x + 6, STATE_Y + 5, 1);
        if (!compact && times[i][0])
            ui_text(renderer, times[i], x + 22, hud_centered_y(STATE_Y, STATE_H - 2, 2), 2,
                    COLOR_HUD_PRIMARY, ANCHOR_NW);
        unsigned rgb = states[i].good ? COLOR_HUD_XP : COLOR_HUD_DANGER;
        SDL_Rect mark = {x + 4, STATE_Y + STATE_H - 4, w - 8, 2};
        SDL_SetRenderDrawColor(renderer, (Uint8)(rgb >> 16), (Uint8)(rgb >> 8), (Uint8)rgb, 255);
        SDL_RenderFillRect(renderer, &mark);
        if (hover) {
            open = i;
            open_x = x;
        }
        x += w + STATE_GAP;
    }
    if (open < 0)
        return;
    int w = STATE_TIP_W, px = open_x, py = VIEW_TOP + 6;
    if (px + w > WINDOW_WIDTH - HUD_MARGIN)
        px = WINDOW_WIDTH - HUD_MARGIN - w;
    hud_plate(renderer, px, py, w, STATE_TIP_H);
    ui_icon(renderer, states[open].icon, px + 12, py + 19, 2);
    int timer_width = states[open].time > 0.0f ? 96 : 0;
    hud_text_fit(renderer, states[open].name, px + 44, py + 6, w - 56 - timer_width, 2,
                 states[open].good ? COLOR_HUD_XP : COLOR_HUD_DANGER, ANCHOR_NW);
    hud_text_fit(renderer, states[open].note, px + 44, py + 32, w - 56, 2, COLOR_HUD_PRIMARY, ANCHOR_NW);
    if (states[open].time > 0.0f) {
        char str[16];
        snprintf(str, sizeof(str), "%.1f S", states[open].time);
        hud_text_fit(renderer, str, px + w - 12, py + 6, timer_width - 8, 2, COLOR_HUD_PRIMARY, ANCHOR_NE);
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
        snprintf(str, size, "INFINITA");
    else
        snprintf(str, size, "%d/%d", weapon->rounds, weapon->magazine);
    return weapon->reloading && weapon->magazine > 0;
}

/* Right: the gun's picture and name, its rounds (or "recargando"), and under
 * it the other gun with its key if she can switch. */
static void draw_weapon_panel(SDL_Renderer *renderer, const HudWeapon *weapon)
{
    char str[64];
    int x0 = WEAPON_X, y0 = HUD_TOP, x = x0 + 96, w = WEAPON_W - 108;
    hud_top_panel(renderer, HUD_WEAPON);
    hud_well(renderer, x0 + 8, y0 + 10, UI_WEAPON_W * 2 + 8, UI_WEAPON_H * 2 + 12);
    ui_weapon(renderer, weapon->id, x0 + 12, y0 + 16, 2);
    hud_text_fit(renderer, weapon->name, x, y0 + 5, w, 2, COLOR_HUD_TITLE, ANCHOR_NW);
    ui_icon(renderer, weapon->id == WEAPON_SHOTGUN ? ICON_SHELL : ICON_BULLET, x, y0 + 35, 1);
    bool reload_label = weapon_readout(weapon, str, sizeof(str));
    int scale = hud_text_scale(str, w - 18, 2);
    int used = ui_text(renderer, str, x + 18, y0 + 30, scale,
                       weapon->reloading || (weapon->magazine > 0 && weapon->rounds == 0)
                           ? COLOR_HUD_DANGER : COLOR_HUD_PRIMARY, ANCHOR_NW);
    if (reload_label && 18 + used + 10 + ui_text_width("RECARGANDO", 2) <= w)
        ui_text(renderer, "RECARGANDO", x + 18 + used + 10, y0 + 30, 2, COLOR_HUD_DANGER, ANCHOR_NW);
    if (weapon->can_swap) {
        hud_plate(renderer, x0, CHIP_Y, SWAP_W, CHIP_H);
        ui_key_compact(renderer, x0, CHIP_Y, "Q");
        hud_well(renderer, x0 + HUD_KEY_SIZE + 4, CHIP_Y + 4, UI_WEAPON_W + 8, CHIP_H - 8);
        ui_weapon(renderer, weapon->other_id, x0 + HUD_KEY_SIZE + 8, CHIP_Y + (CHIP_H - UI_WEAPON_H) / 2, 1);
    }
}

/* Beside the other gun: the level-3 power on F, ready or how long until it is. */
static void draw_power_panel(SDL_Renderer *renderer, const HudWeapon *weapon)
{
    if (weapon->power == POWER_NONE)
        return;
    int x0 = WEAPON_X + WEAPON_W - POWER_W, y = hud_centered_y(CHIP_Y, CHIP_H, 2);
    hud_plate(renderer, x0, CHIP_Y, POWER_W, CHIP_H);
    int x = x0;
    x += ui_key_compact(renderer, x, CHIP_Y, "F") + 6;
    int picture = weapon->power == POWER_GRENADES ? UI_GRENADE : WEAPON_DUAL;
    hud_well(renderer, x - 2, CHIP_Y + 4, UI_WEAPON_W + 4, CHIP_H - 8);
    ui_weapon(renderer, picture, x, CHIP_Y + (CHIP_H - UI_WEAPON_H) / 2, 1);
    x += UI_WEAPON_W + 6;
    char str[24];
    const char *name = weapon->power == POWER_GRENADES ? "GRANADA" : "REBOTE";
    if (weapon->power_wait <= 0.0f) {
        hud_text_fit(renderer, name, x, y, x0 + POWER_W - x - 8, 2, COLOR_HUD_XP, ANCHOR_NW);
    } else {
        snprintf(str, sizeof(str), "%s %d S", name, (int)ceilf(weapon->power_wait));
        hud_text_fit(renderer, str, x, y, x0 + POWER_W - x - 8, 2, COLOR_HUD_SECONDARY, ANCHOR_NW);
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

static void draw_stars(SDL_Renderer *renderer, int earned, int x, int y, int scale, int gap)
{
    for (int i = 0; i < 3; i++)
        ui_icon(renderer, i < earned ? ICON_MISSION_STAR : ICON_MISSION_STAR_EMPTY,
                  x + i * (UI_ICON_SIZE * scale + gap), y, scale);
}

/* Center the whole icon/value group, including when the clock grows to hours. */
static void draw_metric(SDL_Renderer *renderer, UiIcon icon, const char *text, int center,
                          int y, int width, unsigned ink)
{
    int size = UI_ICON_SIZE * 2, gap = 8;
    int scale = hud_text_scale(text, width - size - gap, 2);
    int text_width = ui_text_width(text, scale);
    int x = center - (size + gap + text_width) / 2;
    ui_icon(renderer, icon, x, y, 2);
    ui_text(renderer, text, x + size + gap, y + (size - pixfont_height(scale)) / 2,
              scale, ink, ANCHOR_NW);
}

/* The mouse over the mission plate opens the goals for its three stars. */
static void draw_mission_goals(SDL_Renderer *renderer, const StageRun *run)
{
    SDL_Point pointer = {pointer_x, pointer_y};
    if (!SDL_PointInRect(&pointer, &HUD_REGIONS[HUD_MISSION]) || run->phase != RUN_FIGHTING)
        return;
    MissionGoals goals = mission_goals(run->stage_index);
    int left = (WINDOW_WIDTH - MISSION_GOALS_W) / 2, top = VIEW_TOP + 6;
    ui_panel(renderer, left, top, MISSION_GOALS_W, MISSION_GOALS_H);
    ui_text(renderer, "METAS DE ESTA MISIÓN", WINDOW_WIDTH / 2, top + 12, 2, COLOR_HUD_TITLE, ANCHOR_N);
    ui_text(renderer, "TIEMPO MÁX.", left + 124, top + 36, 2, COLOR_HUD_SECONDARY, ANCHOR_NW);
    ui_text(renderer, "VIDA MÍN.", left + 314, top + 36, 2, COLOR_HUD_SECONDARY, ANCHOR_NW);
    for (int stars = 3; stars > 0; stars--) {
        int row = top + 62 + (3 - stars) * 34;
        draw_stars(renderer, stars, left + 20, row, 2, 4);
        char limit[24], text[24];
        mission_format_time(goals.seconds[stars - 1] * SIMULATION_HZ, limit, sizeof(limit));
        ui_icon(renderer, ICON_CLOCK, left + 124, row + 6, 1);
        ui_text(renderer, limit, left + 144, row + 2, 2, COLOR_HUD_PRIMARY, ANCHOR_NW);
        ui_icon(renderer, ICON_HEART, left + 314, row + 6, 1);
        snprintf(text, sizeof(text), "%d%%", goals.health_percent[stars - 1]);
        ui_text(renderer, text, left + 334, row + 2, 2, COLOR_HUD_PRIMARY, ANCHOR_NW);
    }
}

static void draw_reward_row(SDL_Renderer *renderer, int x, int y, const char *label,
                               int xp, int gold, unsigned ink)
{
    char text[40];
    hud_text_fit(renderer, label, x + 30, y, 286, 2, ink, ANCHOR_NW);
    snprintf(text, sizeof(text), "+%d XP", xp);
    hud_text_fit(renderer, text, x + 492, y, 160, 2, COLOR_HUD_PRIMARY, ANCHOR_NE);
    snprintf(text, sizeof(text), "+%d ORO", gold);
    hud_text_fit(renderer, text, x + RESULT_W - 30, y, 160, 2, COLOR_HUD_PRIMARY, ANCHOR_NE);
}

static void draw_mission_results(SDL_Renderer *renderer, const StageRun *run)
{
    const MissionReport *m = &run->mission;
    int w = RESULT_W, h = RESULT_H, x = (WINDOW_WIDTH - w) / 2, y = (WINDOW_HEIGHT - h) / 2;
    char text[128], time[24];
    ui_dim(renderer, 130);
    ui_panel(renderer, x, y, w, h);
    snprintf(text, sizeof(text), "¡NIVEL %s COMPLETADO!", run->stage->name);
    hud_text_fit(renderer, text, WINDOW_WIDTH / 2, y + 18, w - 48, 3, COLOR_HUD_TITLE, ANCHOR_N);
    int stars_width = 3 * UI_ICON_SIZE * RESULT_STAR_SCALE + 2 * RESULT_STAR_GAP;
    draw_stars(renderer, m->stars, (WINDOW_WIDTH - stars_width) / 2, y + 60,
                  RESULT_STAR_SCALE, RESULT_STAR_GAP);
    snprintf(text, sizeof(text), "%d DE 3 ESTRELLAS", m->stars);
    ui_text(renderer, text, WINDOW_WIDTH / 2, y + 138, 2, COLOR_HUD_TITLE, ANCHOR_N);
    mission_format_time(m->ticks, time, sizeof(time));
    draw_metric(renderer, ICON_CLOCK, time, x + w / 4, y + 170, w / 2 - 60, COLOR_HUD_PRIMARY);
    snprintf(text, sizeof(text), "%d%% VIDA", m->health_percent);
    draw_metric(renderer, ICON_HEART, text, x + w * 3 / 4, y + 170, w / 2 - 60, COLOR_HUD_PRIMARY);
    if (m->new_record)
        ui_text(renderer, "NUEVO RÉCORD PERSONAL", x + w / 4, y + 198, 2, COLOR_HUD_TITLE, ANCHOR_N);
    int total_xp = m->base_xp + m->star_xp + m->record_xp;
    int total_gold = m->base_gold + m->star_gold + m->record_gold;
    int card_w = (w - 72) / 2;
    hud_plate(renderer, x + 30, y + 224, card_w, 54);
    hud_plate(renderer, x + w / 2 + 6, y + 224, card_w, 54);
    snprintf(text, sizeof(text), "+%d XP", total_xp);
    hud_text_fit(renderer, text, x + 30 + card_w / 2, y + 235, card_w - 24, 3, COLOR_HUD_XP, ANCHOR_N);
    snprintf(text, sizeof(text), "+%d ORO", total_gold);
    hud_text_fit(renderer, text, x + w / 2 + 6 + card_w / 2, y + 235, card_w - 24, 3, COLOR_HUD_TITLE, ANCHOR_N);
    draw_reward_row(renderer, x, y + 290, "BASE DE MISIÓN", m->base_xp, m->base_gold, COLOR_HUD_SECONDARY);
    snprintf(text, sizeof(text), "%d %s", m->stars, m->stars == 1 ? "ESTRELLA" : "ESTRELLAS");
    draw_reward_row(renderer, x, y + 316, text, m->star_xp, m->star_gold, COLOR_HUD_SECONDARY);
    if (m->record_xp || m->record_gold) {
        draw_reward_row(renderer, x, y + 342, "RÉCORD + VIDA 100%", m->record_xp, m->record_gold, COLOR_HUD_TITLE);
    }
    static const char *const hints[] = {"ENTER", "CONTINUAR"};
    draw_hints(renderer, hints, 1, y + 388);
}

void hud_draw_stage(SDL_Renderer *renderer, const Player *player, const Zombie *zombies,
                    int zombie_count, const Progress *progress, const StageRun *run,
                    float camera_x, const HudWeapon *weapon)
{
    draw_tags(renderer, player, zombies, zombie_count, camera_x);
    draw_popups(renderer, camera_x);
    draw_vitals(renderer, player, progress);
    draw_mission(renderer, player, run);
    draw_weapon_panel(renderer, weapon);
    draw_supplies(renderer, player, progress, run);
    draw_alert(renderer, player);
    draw_power_panel(renderer, weapon);
    draw_states(renderer, player, run);
    draw_prompt(renderer, player, run);
    draw_mission_goals(renderer, run);

    if (run->phase == RUN_FAILED) {
        static const char *const hints[] = {"R", "REINTENTAR", "ESC", "PAUSA"};
        draw_message(renderer, player->fainted ? "TE DESMAYASTE POR EL CALOR" : "TE ALCANZÓ EL ZOMBI",
                     COLOR_HUD_DANGER, hints, 2);
    } else if (run->phase == RUN_CLEARED) {
        draw_mission_results(renderer, run);
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

/* For what must not shrink to the small font in ordinary play. */
static bool layout_text_stays_large(const char *str, int width)
{
    int measured = ui_text_width(str, 2);
    if (measured <= width)
        return true;
    fprintf(stderr, "HUD: '%s' necesita %d px en tamaño 2, dispone de %d.\n", str, measured, width);
    return false;
}

void hud_draw_autosave_notice(SDL_Renderer *renderer)
{
    /* Discard click targets belonging to the stage menu beneath the modal. */
    hud_zones_clear();
    ui_dim(renderer, 170);
    int w = 660, h = 316, x = (WINDOW_WIDTH - w) / 2, y = (WINDOW_HEIGHT - h) / 2;
    ui_panel(renderer, x, y, w, h);
    ui_text(renderer, "GUARDADO AUTOMÁTICO", WINDOW_WIDTH / 2, y + 28, 3, COLOR_HUD_TITLE, ANCHOR_N);
    ui_icon(renderer, ICON_SAVE, x + 52, y + 82, 3);
    ui_text(renderer, "CUIDAMOS TU AVANCE", x + 106, y + 91, 2, COLOR_HUD_XP, ANCHOR_NW);
    ui_text(renderer, "GUARDAMOS CADA 15 MINUTOS DE JUEGO", WINDOW_WIDTH / 2, y + 142, 2,
            COLOR_HUD_PRIMARY, ANCHOR_N);
    ui_text(renderer, "TAMBIÉN AL COMPLETAR UN NIVEL Y AL SALIR", WINDOW_WIDTH / 2, y + 172, 2,
            COLOR_HUD_PRIMARY, ANCHOR_N);
    ui_text(renderer, "EL ICONO APARECE SIN DETENER LA PARTIDA", WINDOW_WIDTH / 2, y + 208, 2,
            COLOR_HUD_SECONDARY, ANCHOR_N);
    int bw = 354, bx = (WINDOW_WIDTH - bw) / 2, by = y + h - 66;
    ui_button(renderer, bx, by, bw, 44, "ENTENDIDO, CONTINUAR", true, true);
    add_zone(HUD_ZONE_ACCEPT, 0, bx, by, bw, 44);
    ui_text(renderer, "ENTER: CONTINUAR   ESC: VOLVER", WINDOW_WIDTH / 2, y + h + 14, 1,
            COLOR_HUD_SECONDARY, ANCHOR_N);
}

/* Bottom right, clear of everything else: brief, and it never takes a click. */
void hud_draw_autosave_status(SDL_Renderer *renderer, bool saving, bool failed, float age)
{
    const char *text = saving ? "GUARDANDO..." : failed ? "NO SE PUDO GUARDAR" : "PARTIDA GUARDADA";
    int w = 30 + ui_text_width(text, 2) + 10, h = STATE_H;
    int x = WINDOW_WIDTH - HUD_MARGIN - w, y = STATE_Y;
    hud_plate(renderer, x, y, w, h);
    ui_icon(renderer, ICON_SAVE, x + 8, y + (h - UI_ICON_SIZE) / 2, 1);
    ui_text(renderer, text, x + 30, hud_centered_y(y, h, 2), 2,
            failed && !saving ? COLOR_HUD_DANGER : COLOR_HUD_SECONDARY, ANCHOR_NW);
    if (saving) {
        int phase = (int)fmodf(fmaxf(0.0f, age) * 5.0f, 4.0f);
        SDL_Rect dot = {x + 4, y + 7 + phase * 2, 2, 2};
        SDL_SetRenderDrawColor(renderer, 205, 155, 91, 255);
        SDL_RenderFillRect(renderer, &dot);
    }
}

void hud_draw_resume_hint(SDL_Renderer *renderer, const char *stage_name)
{
    char text[80];
    snprintf(text, sizeof(text), "PARTIDA GUARDADA EN %s · ENTER PARA REANUDAR", stage_name);
    hud_plate(renderer, 180, 450, 600, 28);
    ui_icon(renderer, ICON_SAVE, 190, 458, 1);
    hud_text_fit(renderer, text, WINDOW_WIDTH / 2 + 8, 458, 548, 1,
                  COLOR_HUD_XP, ANCHOR_N);
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
    int health_w = VITALS_W - 84, xp_w = health_w - XP_BAR_W - 8, gun_w = WEAPON_W - 108;
    snprintf(str, sizeof(str), "%d/%d", INT_MAX, INT_MAX);
    ok = layout_text_fits(str, health_w - 8, 2) && ok;
    /* The clock stays centered and whole, past an hour too. */
    ok = layout_text_stays_large("99:59:59", MISSION_W - 24 - CLOCK_ICON_W) && ok;
    snprintf(str, sizeof(str), "XP %d/%d", INT_MAX, INT_MAX);
    ok = layout_text_fits(str, xp_w, 2) && ok;
    snprintf(str, sizeof(str), "SALIDA %d M", INT_MAX);
    ok = layout_text_fits(str, EXIT_W, 2) && ok;
    for (int s = 0; s < STAGE_COUNT; s++) {
        snprintf(str, sizeof(str), "%d/%d", STAGES[s].zombies, STAGES[s].zombies);
        ok = layout_text_stays_large(str, DEFEATED_W) && ok;
        snprintf(str, sizeof(str), "RUTA %s", STAGES[s].name);
        ok = layout_text_stays_large(str, ROUTE_W) && ok;
    }
    for (int level = 1; level < MAX_LEVEL; level++) {
        int need = xp_to_next(level);
        snprintf(str, sizeof(str), "XP %d/%d", need - 1, need);
        ok = layout_text_stays_large(str, xp_w) && ok;
    }
    snprintf(str, sizeof(str), "%d", INT_MAX);
    if (3 * (16 + ui_text_width(str, 1)) + 28 > VITALS_W - 20) {
        fprintf(stderr, "HUD: suministros máximos exceden su columna.\n");
        ok = false;
    }
    for (int id = 0; id < WEAPON_COUNT; id++) {
        const WeaponDef *def = weapon_def((WeaponId)id);
        ok = layout_text_stays_large(def->name, gun_w) && ok;
        HudWeapon weapon = {.id = id, .name = def->name, .rounds = INT_MAX,
                            .magazine = INT_MAX, .reloading = true};
        weapon_readout(&weapon, str, sizeof(str));
        ok = layout_text_fits(str, gun_w - 18, 2) && ok;
    }
    /* What a player reads in play stays at scale two with ordinary values. */
    ok = layout_text_stays_large("SALIDA 9999 M", EXIT_W) && ok;
    ok = layout_text_stays_large("0/99 RECARGANDO", gun_w - 18) && ok;
    ok = layout_text_stays_large("¡ALÉJATE DEL FUEGO!", MISSION_W - 12) && ok;
    ok = layout_text_stays_large("VENDANDO 100%", MISSION_W - 12) && ok;
    if (ui_text_width("SED GRAVE", 2) + 10 + ui_text_width("BEBE", 2) + 6 + HUD_KEY_SIZE > MISSION_W - 12 ||
        ui_text_width("SANGRADO", 2) + 10 + ui_text_width("MANTÉN", 2) + 6 + HUD_KEY_SIZE > MISSION_W - 12) {
        fprintf(stderr, "HUD: alerta fuera de su espacio.\n");
        ok = false;
    }
    int power_w = POWER_W - HUD_KEY_SIZE - 6 - UI_WEAPON_W - 6 - 8;
    ok = layout_text_stays_large("GRANADA 99 S", power_w) && ok;
    ok = layout_text_stays_large("REBOTE 99 S", power_w) && ok;
    if (HUD_KEY_SIZE + 8 + UI_WEAPON_W > SWAP_W || SWAP_W + POWER_W + 8 > WEAPON_W) {
        fprintf(stderr, "HUD: atajos del arma fuera de su columna.\n");
        ok = false;
    }
    ok = layout_text_fits("999+", BADGE_W * BADGE_SCALE - 4, 1) && ok;
    ok = layout_text_fits("GUARDADO AUTOMÁTICO", 612, 3) && ok;
    ok = layout_text_fits("TAMBIÉN AL COMPLETAR UN NIVEL Y AL SALIR", 612, 2) && ok;
    ok = layout_text_fits("VIDA AL LLEGAR: 100%", 612, 2) && ok;
    ok = layout_text_fits("06:45 · NUEVO RÉCORD", 460, 2) && ok;
    ok = layout_text_stays_large("TE CURAS Y CAMINAS MÁS LENTO. MANTÉN U: VÉNDATE", STATE_TIP_W - 56) && ok;
    /* The longest save message stays right of the conditions and inside the
     * sky band, and every condition at once still fits as bare icons. */
    int save_x = WINDOW_WIDTH - HUD_MARGIN - (30 + ui_text_width("NO SE PUDO GUARDAR", 2) + 10);
    if (save_x < VITALS_X + STATES_W || STATE_Y + STATE_H > VIEW_TOP) {
        fprintf(stderr, "HUD: autoguardado fuera de su espacio.\n");
        ok = false;
    }
    if (STATE_MAX * (STATE_H + STATE_GAP) > STATES_W) {
        fprintf(stderr, "HUD: estados fuera de su fila.\n");
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
    static const char *const labels[TITLE_ITEMS] = {"JUGAR", "ALMANAQUE", "CONTROLES", "OPCIONES", "SALIR"};
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
        const char *keys[2];
        const char *action;
        const char *note;
    } rows[] = {
        {{"A", "D"}, "CAMINAR", "TAMBIÉN ← / →"},
        {{"SHIFT", NULL}, "CORRER", NULL},
        {{"ESPACIO", "W"}, "SALTAR", NULL},
        {{"N", NULL}, "CRUZAR BARRICADA", "O RÓMPELA"},
        {{"CLIC IZQ", NULL}, "DISPARAR", "MANTENER: RÁFAGAS"},
        {{"R", NULL}, "RECARGAR", NULL},
        {{"Q", "CLIC DER"}, "CAMBIAR DE ARMA", "SWAT · VAQUERA: DUALES"},
        {{"K", NULL}, "MODO DEL RIFLE", "RÁFAGAS O TIRO A TIRO (SWAT)"},
        {{"E", NULL}, "DINAMITA / SENTAR", "EN UN MURO O EN EL SUELO"},
        {{"F", "RUEDA"}, "PODER", "NIVEL 3: GRANADA O REBOTE"},
        {{"V", NULL}, "CULATAZO", "CORTA ALAMBRE, ROMPE CAJAS"},
        {{"U", NULL}, "VENDAR / BEBER", "MANTÉN: VENDAR · PULSA: BEBER"},
        {{"L", NULL}, "LINTERNA", NULL},
        {{"B", NULL}, "ALMANAQUE", NULL},
        {{"ESC", NULL}, "PAUSA", NULL},
    };
    enum { LEFT_ROWS = 8, PITCH = 48, KEYS_W = 186 };
    int count = (int)(sizeof(rows) / sizeof(rows[0]));
    int w = 900, h = 52 + LEFT_ROWS * PITCH + 8, x = (WINDOW_WIDTH - w) / 2, y = 12;
    ui_panel(renderer, x, y, w, h);
    ui_text(renderer, "CONTROLES", WINDOW_WIDTH / 2, y + 12, 3, COLOR_HUD_TITLE, ANCHOR_N);
    for (int i = 0; i < count; i++) {
        bool left = i < LEFT_ROWS;
        int ry = y + 52 + (left ? i : i - LEFT_ROWS) * PITCH;
        int column = left ? x + 28 : x + w / 2 + 12;
        int kx = column;
        for (int k = 0; k < 2 && rows[i].keys[k]; k++) {
            if (k > 0)
                kx += ui_text(renderer, "/", kx + 6, ry + 12, 2, COLOR_HUD_SECONDARY, ANCHOR_NW) + 12;
            kx += ui_key(renderer, kx, ry, rows[i].keys[k]);
        }
        int tx = column + KEYS_W, room = w / 2 - 28 - KEYS_W - 8;
        hud_text_fit(renderer, rows[i].action, tx, rows[i].note ? ry + 1 : ry + 10, room, 2,
                     COLOR_HUD_PRIMARY, ANCHOR_NW);
        if (rows[i].note)
            hud_text_fit(renderer, rows[i].note, tx, ry + 25, room, 1, COLOR_HUD_SECONDARY, ANCHOR_NW);
    }
    static const char *const hints[] = {"ESC", "VOLVER"};
    draw_hints(renderer, hints, 1, y + h + 8);
}

void hud_draw_volume(SDL_Renderer *renderer, const ListMenu *menu, const Volumes *volumes)
{
    static const char *const names[] = {"GENERAL", "PERSONAJE", "ZOMBIS"};
    const int values[] = {volumes->master, volumes->player, volumes->zombie};
    int w = 620, h = 386, x = (WINDOW_WIDTH - w) / 2, y = 70;
    ui_panel(renderer, x, y, w, h);
    ui_text(renderer, "OPCIONES", WINDOW_WIDTH / 2, y + 22, 3, COLOR_HUD_TITLE, ANCHOR_N);
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
    /* Not a volume: window or full screen, switched with A/D, Enter, a click or F11. */
    int ry = y + 82 + VOLUME_FULLSCREEN * 56;
    bool selected = menu->selected == VOLUME_FULLSCREEN;
    add_zone(HUD_ZONE_ITEM, VOLUME_FULLSCREEN, x + 24, ry - 10, w - 48, 50);
    if (selected)
        ui_button(renderer, x + 24, ry - 10, w - 48, 50, "", true, true);
    ui_text(renderer, "PANTALLA", x + 80, ry + 4, 2, selected ? COLOR_HUD_TITLE : COLOR_HUD_PRIMARY,
            ANCHOR_NW);
    ui_text(renderer, volumes->fullscreen ? "COMPLETA" : "VENTANA", x + 270, ry + 4, 2,
            selected ? COLOR_HUD_TITLE : COLOR_HUD_PRIMARY, ANCHOR_NW);
    ui_key(renderer, x + w - 92, ry - 3, "F11");
    ui_button(renderer, WINDOW_WIDTH / 2 - 110, y + h - 70, 220, 44, "VOLVER",
              menu->selected == VOLUME_BACK, true);
    add_zone(HUD_ZONE_ITEM, VOLUME_BACK, WINDOW_WIDTH / 2 - 110, y + h - 70, 220, 44);
    static const char *const hints[] = {"W/S", "ELEGIR", "A/D", "BAJAR/SUBIR", "ESC", "VOLVER"};
    draw_hints(renderer, hints, 3, WINDOW_HEIGHT - 52);
}

void hud_draw_pause(SDL_Renderer *renderer, const ListMenu *menu)
{
    static const char *const labels[PAUSE_ITEMS] = {"CONTINUAR", "REINICIAR NIVEL", "ALMANAQUE", "OPCIONES",
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
        snprintf(str, sizeof(str), "%d M", (int)(run_road_length(i) / ROUTE_PX_PER_METER));
        ui_icon(renderer, ICON_FLAG, x + 396, y + 14, 2);
        ui_text(renderer, str, x + 426, y + 18, 2, open ? COLOR_HUD_SECONDARY : COLOR_HUD_LOCKED, ANCHOR_NW);
        if (record->cleared[i]) {
            for (int star = 0; star < 3; star++)
                ui_icon(renderer, (unsigned)star < record->stars[i] ? ICON_MISSION_STAR : ICON_MISSION_STAR_EMPTY,
                          x + w - 88 + star * (UI_ICON_SIZE * 2 + 2), y + 14, 2);
        } else if (!open)
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
        char trial[sizeof(line) + sizeof(word)]; /* Both, and the space between them */
        snprintf(trial, sizeof(trial), "%s%s%s", line, line[0] ? " " : "", word);
        if (line[0] && ui_text_width(trial, 2) > max_w) {
            ui_text(renderer, line, cx, y, 2, rgb, ANCHOR_N);
            y += line_h;
            snprintf(line, sizeof(line), "%s", word);
        } else {
            SDL_strlcpy(line, trial, sizeof(line));
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

    /* Stood still, in its own pose if it has one, else its walk's first frame; a little
     * smaller than in play. */
    SDL_Texture *walk = skin->stand_sheet ? skin->stand_sheet : skin->sheets[0];
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
