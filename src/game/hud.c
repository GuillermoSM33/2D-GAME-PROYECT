#include "game/hud.h"

#include "config.h"
#include "engine/text.h"
#include "game/health_bar.h"

#define FONT_REGULAR "fonts/DejaVuSansMono"
#define FONT_BOLD "fonts/DejaVuSansMono-Bold"

#define HEALTH_BAR_W 200
#define HEALTH_BAR_H 12
#define HEALTH_RIGHT (WINDOW_WIDTH - 32)
#define HEALTH_LABEL_Y 28
#define HEALTH_BAR_Y 52
#define GAME_OVER_Y 140

typedef struct {
    const char *font;
    int size_px;
    const char *text;
    unsigned color;
    int x, y;
    Anchor anchor;
} HudLine;

static const HudLine LINES[] = {
    {FONT_BOLD, 25, "VAQUERA 2D", COLOR_HUD_TITLE, 32, 28, ANCHOR_NW},
    {FONT_REGULAR, 15, "D / →  Caminar a la derecha    A / ←  Izquierda",
     COLOR_HUD_PRIMARY, 32, 65, ANCHOR_NW},
    {FONT_REGULAR, 13, "SHIFT  Correr    ESPACIO / W / ↑  Saltar    CLIC IZQ  Disparar    R  Reiniciar    ESC  Salir",
     COLOR_HUD_SECONDARY, 32, 88, ANCHOR_NW},
    {FONT_REGULAR, 12, "8 FRAMES  •  SPRITE ORIGINAL  •  PIXEL ART",
     COLOR_HUD_FOOTER, WINDOW_WIDTH - 20, WINDOW_HEIGHT - 18, ANCHOR_SE},
    {FONT_REGULAR, 12, "Linux • C + SDL2", COLOR_HUD_FOOTER, 25, WINDOW_HEIGHT - 18, ANCHOR_SW},
};

/* Shown only while the player is down. */
static const HudLine GAME_OVER_LINES[] = {
    {FONT_BOLD, 25, "TE ALCANZÓ EL ZOMBI", COLOR_HUD_DANGER, WINDOW_WIDTH / 2, GAME_OVER_Y, ANCHOR_N},
    {FONT_REGULAR, 15, "R  Reiniciar", COLOR_HUD_PRIMARY, WINDOW_WIDTH / 2, GAME_OVER_Y + 40, ANCHOR_N},
};

static const HudLine HEALTH_LABEL = {
    FONT_BOLD, 13, "VIDA", COLOR_HUD_SECONDARY, HEALTH_RIGHT, HEALTH_LABEL_Y, ANCHOR_NE,
};

#define LINE_COUNT ((int)(sizeof(LINES) / sizeof(LINES[0])))
#define GAME_OVER_COUNT ((int)(sizeof(GAME_OVER_LINES) / sizeof(GAME_OVER_LINES[0])))

static Text texts[LINE_COUNT];
static Text game_over_texts[GAME_OVER_COUNT];
static Text health_label;

static bool create_line(Text *text, SDL_Renderer *renderer, const HudLine *line)
{
    TTF_Font *font = text_font_open(line->font, line->size_px);
    if (font == NULL)
        return false;
    bool ok = text_create(text, renderer, font, line->text, line->color);
    TTF_CloseFont(font);
    return ok;
}

bool hud_init(SDL_Renderer *renderer)
{
    for (int i = 0; i < LINE_COUNT; i++)
        if (!create_line(&texts[i], renderer, &LINES[i]))
            return false;
    for (int i = 0; i < GAME_OVER_COUNT; i++)
        if (!create_line(&game_over_texts[i], renderer, &GAME_OVER_LINES[i]))
            return false;
    return create_line(&health_label, renderer, &HEALTH_LABEL);
}

static void draw_line(SDL_Renderer *renderer, const Text *text, const HudLine *line)
{
    text_draw(renderer, text, line->x, line->y, line->anchor);
}

void hud_draw(SDL_Renderer *renderer, const Player *player)
{
    for (int i = 0; i < LINE_COUNT; i++)
        draw_line(renderer, &texts[i], &LINES[i]);
    draw_line(renderer, &health_label, &HEALTH_LABEL);
    health_bar_draw(renderer, HEALTH_RIGHT - HEALTH_BAR_W, HEALTH_BAR_Y, HEALTH_BAR_W,
                    HEALTH_BAR_H, player->health, PLAYER_HEALTH, PLAYER_ARMOR > 0.0f);
    if (player_alive(player))
        return;
    for (int i = 0; i < GAME_OVER_COUNT; i++)
        draw_line(renderer, &game_over_texts[i], &GAME_OVER_LINES[i]);
}

void hud_shutdown(void)
{
    for (int i = 0; i < LINE_COUNT; i++)
        text_destroy(&texts[i]);
    for (int i = 0; i < GAME_OVER_COUNT; i++)
        text_destroy(&game_over_texts[i]);
    text_destroy(&health_label);
}
