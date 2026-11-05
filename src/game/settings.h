#ifndef GAME_SETTINGS_H
#define GAME_SETTINGS_H

#include <stdbool.h>

#include "engine/input.h"

/* Volume groups the game plays its sounds in (audio_play_in). */
typedef enum {
    SOUND_MASTER = 0, /* Ambient weather and UI follow the general volume */
    SOUND_PLAYER = 1, /* Everything the character does or sets off: guns, reloads, blasts, pickups */
    SOUND_ZOMBIE = 2  /* The zombies' voices */
} SoundGroup;

#define VOLUME_STEPS 10

/* The options menu's volumes, 0 to VOLUME_STEPS each: everything, then the
 * music's, the character's and the zombies' sounds on top of it. Kept for the session.
 * The same screen also switches the window to full screen and back. */
typedef struct {
    int master, music, player, zombie;
    bool fullscreen;
} Volumes;

typedef enum {
    VOLUME_MASTER,
    VOLUME_MUSIC,
    VOLUME_PLAYER,
    VOLUME_ZOMBIE,
    VOLUME_FULLSCREEN, /* Window or full screen; not a volume */
    VOLUME_BACK,
    VOLUME_ROWS
} VolumeRow;

void volumes_init(Volumes *volumes);

/* A vertical list of choices (main menu, pause, options): up and down move
 * over them, wrapping. */
typedef struct {
    int selected;
    int count;
} ListMenu;

void list_menu_init(ListMenu *menu, int count);

/* Returns the choice confirmed on this update, or -1. */
int list_menu_update(ListMenu *menu, const InputState *input);

/* The options screen: a ListMenu over VolumeRow; left and right turn the
 * selected volume down and up. Returns the row whose volume changed (to play
 * a sample of it), VOLUME_FULLSCREEN when left, right or confirm switched
 * the display, VOLUME_BACK when it is left (Esc, or Volver), or -1. */
int volume_menu_update(ListMenu *menu, Volumes *volumes, const InputState *input);

/* Sets a row's volume to value (clamped); false if the row has none or it
 * didn't change. */
bool volume_set(Volumes *volumes, int row, int value);

/* 0..1 of a volume. */
float volume_share(int steps);

#endif
