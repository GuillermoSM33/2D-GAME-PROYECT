#ifndef GAME_ALMANAC_H
#define GAME_ALMANAC_H

#include <stdbool.h>

#include "config.h"
#include "engine/input.h"
#include "game/zombie.h"

#define ALMANAC_ENTRIES (ZOMBIE_KIND_COUNT * 2)
#define ALMANAC_COLUMNS 4
#define ALMANAC_ROWS 2
#define ALMANAC_PAGE_SIZE (ALMANAC_COLUMNS * ALMANAC_ROWS)

/* Shared gallery geometry keeps pointer selection and drawing in agreement. */
#define ALMANAC_GRID_X 24
#define ALMANAC_GRID_Y 106
#define ALMANAC_CARD_W 128
#define ALMANAC_CARD_H 164
#define ALMANAC_CARD_GAP 10
#define ALMANAC_GRID_W (ALMANAC_COLUMNS * ALMANAC_CARD_W + (ALMANAC_COLUMNS - 1) * ALMANAC_CARD_GAP)
#define ALMANAC_PAGE_Y 452
#define ALMANAC_FOOTER_Y (WINDOW_HEIGHT - 52)

typedef struct {
    bool discovered;
    int seen;        /* Individual encounters, not frames spent on screen */
    int defeated;
    int max_level;
} AlmanacEntry;

/* Belongs to the character's session profile, alongside Progress. */
typedef struct {
    AlmanacEntry entries[ALMANAC_ENTRIES];
} Almanac;

/* Belongs to one stage play; reset on every start/retry, without resetting
 * the profile's book. Slots match the stable StageRun.zombies array. */
typedef struct {
    int entry[RUN_MAX_ZOMBIES];
    bool defeated[RUN_MAX_ZOMBIES];
} AlmanacEncounter;

typedef struct {
    int selected;
    int scroll; /* First entry of the current page */
    bool detail;
} AlmanacView;

typedef struct {
    int level, health;
    float damage, armor, speed; /* Speed in world pixels per second */
} AlmanacStats;

void almanac_init(Almanac *book);
void almanac_encounter_start(AlmanacEncounter *encounter);
int almanac_index(ZombieKind kind, bool runner); /* -1 for an invalid kind */
ZombieKind almanac_kind(int entry);              /* COUNT for an invalid entry */
bool almanac_runner(int entry);
const AlmanacEntry *almanac_entry(const Almanac *book, int entry);
int almanac_count(const Almanac *book);

/* Records one new individual encounter, returning true for a newly revealed
 * type/runner variant. Repeated frames should use almanac_observe instead. */
bool almanac_discover(Almanac *book, ZombieKind kind, bool runner, int level);

/* Unknown kinds stay unknown even if something dies outside the view. */
bool almanac_record_kill(Almanac *book, ZombieKind kind, bool runner);

/* Call each simulation step. Only living, awake, non-hidden zombies whose
 * body intersects the view can reveal an entry. Previously seen individuals'
 * deaths count once, including when they later move off screen. Returns the
 * number of newly revealed entries. Do not also count these kills manually. */
int almanac_observe(Almanac *book, AlmanacEncounter *encounter, const Zombie *zombies,
                    int count, float camera_x, float view_width);

/* Returns no stats for an unknown entry; uses the game's exact scaling for
 * level 1 or the highest level actually observed, including runner stats. */
bool almanac_stats_at(const Almanac *book, int entry, bool observed, AlmanacStats *stats);

void almanac_view_init(AlmanacView *view);
void almanac_view_select(AlmanacView *view, int entry);
int almanac_pages(void);
int almanac_hit(const AlmanacView *view, int x, int y); /* Visible card, or -1 */

/* WASD/arrows navigate, Enter/click opens details. Esc closes a detail first;
 * returns false when Esc/the clickable back hint exits the whole book. */
bool almanac_view_update(AlmanacView *view, const InputState *input);

#endif
