#ifndef GAME_HUD_H
#define GAME_HUD_H

#include <stdbool.h>

#include <SDL.h>

#include "game/character_skin.h"
#include "game/player.h"
#include "game/progression.h"
#include "game/settings.h"
#include "game/stage_run.h"
#include "game/stages.h"
#include "game/zombie.h"

/* Everything on screen that isn't the world, in pixel art (game/ui.c): the
 * menus, the pause, the controls and volume screens, and the readouts during
 * a stage. */

/* The title, as the title screen and the end of the intro draw it (the same
 * place, so one becomes the other without a jump). */
#define TITLE_TEXT "THE MIRACLE"
#define TITLE_TAGLINE "LA CURA ERA LA PLAGA"
#define TITLE_Y 32          /* Window px: the title's top, scale TITLE_SCALE */
#define TITLE_SCALE 8
#define TITLE_TAGLINE_Y 120 /* ...and its tagline's, scale 2 */

typedef enum { TITLE_PLAY, TITLE_STORY, TITLE_ALMANAC, TITLE_CONTROLS, TITLE_VOLUME, TITLE_QUIT, TITLE_ITEMS } TitleItem;
typedef enum {
    PAUSE_CONTINUE,
    PAUSE_RETRY,
    PAUSE_ALMANAC,
    PAUSE_VOLUME,
    PAUSE_CONTROLS,
    PAUSE_LEAVE,
    PAUSE_ITEMS
} PauseItem;

/* The gun in hand, for the stage readouts. */
typedef struct {
    int id;            /* WeaponId: its picture */
    const char *name;
    int rounds, magazine; /* magazine 0: it never runs dry */
    bool reloading;
    bool can_swap;
    int other_id;      /* The other gun, if can_swap */
    int power;         /* Power (characters.h) once it has come, else POWER_NONE */
    float power_wait;  /* Seconds until F works again */
} HudWeapon;

/* What can be clicked on the screen last drawn: menu items (buttons, stage
 * rows, character cards, volume rows), the keys of the hints (Esc goes back,
 * Enter accepts, R retries) and the volume bars. */
typedef enum { HUD_ZONE_ITEM, HUD_ZONE_BACK, HUD_ZONE_ACCEPT, HUD_ZONE_RETRY, HUD_ZONE_VOLUME } HudZoneKind;

typedef struct {
    HudZoneKind kind;
    int index;   /* The item, or the volume's row */
    float share; /* 0..1 across the zone where it was hit (a volume bar) */
} HudZone;

/* Forgets the zones; call before drawing a frame. */
void hud_zones_clear(void);

/* The topmost zone under window point (x, y), if any. */
bool hud_zone_at(int x, int y, HudZone *zone);

bool hud_init(SDL_Renderer *renderer);
void hud_shutdown(void);

/* Checks gameplay panel bounds and real pixel-font measurements, including
 * large counters. No renderer/window needed; used by resource verification. */
bool hud_verify_layout(void);

/* During a stage: her health and XP, the gun and its rounds, the dynamite,
 * the zombies beaten and the meters to the gate, the fight holding her, a
 * prompt at a wall, the level above each head, popups, and the cleared /
 * defeated messages. Positions are in the world; camera_x is the view's left
 * edge. */
void hud_draw_stage(SDL_Renderer *renderer, const Player *player, const Zombie *zombies,
                    int zombie_count, const Progress *progress, const StageRun *run,
                    float camera_x, const HudWeapon *weapon);

/* Where the mouse is (window px): the stage's state icons open under it. */
void hud_set_pointer(int x, int y);

/* Screens drawn over the moving landscape the caller draws first. */
void hud_draw_title(SDL_Renderer *renderer, const ListMenu *menu);
void hud_draw_controls(SDL_Renderer *renderer);
void hud_draw_volume(SDL_Renderer *renderer, const ListMenu *menu, const Volumes *volumes);

/* The pause menu over the frozen stage. */
void hud_draw_pause(SDL_Renderer *renderer, const ListMenu *menu);

/* Stage select for one character: every stage with its zombies, their level
 * and whether it is open or cleared. */
void hud_draw_menu(SDL_Renderer *renderer, const char *character_name, const Progress *progress,
                   const StageRecord *record, int selected);

/* "Elige tu personaje": a card per character with its look, level, ability
 * and guns. progress holds each character's, in CHARACTERS order. dev_notice
 * shows the sign saying the selected one is still in development. */
void hud_draw_characters(SDL_Renderer *renderer, const CharacterSkin *skins,
                         const Progress *progress, int selected, bool dev_notice);

/* A short message that rises and fades above a point of the world. */
void hud_popup(const char *utf8, unsigned rgb, float world_x, int y, bool big);
void hud_update(float dt);
void hud_clear_popups(void);

/* First level entry of the session: the caller has not started simulation yet. */
void hud_draw_autosave_notice(SDL_Renderer *renderer);
/* Small status below the weapon panel; no modal, sound or input interception. */
void hud_draw_autosave_status(SDL_Renderer *renderer, bool saving, bool failed, float age);
void hud_draw_resume_hint(SDL_Renderer *renderer, const char *stage_name);

#endif
