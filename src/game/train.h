#ifndef GAME_TRAIN_H
#define GAME_TRAIN_H

#include <stdbool.h>
#include "game/player.h"

#define TRAIN_STAGE 7
#define EXPERIMENTAL_PARTS 8
#define TRAIN_PART_MASK 7u
#define TRAIN_PARTS_ABOARD 3      /* Parts 0..2 ride the train; the rest lie on later routes */

/* Where things stand in a room's own art pixels (tools/train_art.py draws
 * the door, cradles, terminal and hatch at these same columns). */
#define TRAIN_ENTRY_ART 40       /* Car 01's side door */
#define TRAIN_SUIT_ART 218       /* Car 01's hazmat suits: between their two hooks... */
#define TRAIN_SUIT_HOOK 13       /* ...this far to each side */
#define TRAIN_SUIT_BOTTOM 236    /* Art row under a hanging suit's boots */
#define TRAIN_TABLET_ART 311     /* Car 01's tablet in its open locker... */
#define TRAIN_TABLET_BOTTOM 201  /* ...lying on the shelf above this art row */
/* sprites/terrain/train_gear: frame 0 a suit on its hook, 1 the tablet;
 * each centred on its column and standing on its bottom row. */
#define TRAIN_GEAR_W 32
#define TRAIN_GEAR_H 80
#define TRAIN_CRADLE_ART 259     /* A part's cradle: cars 02, 07 and machinery */
#define TRAIN_CRADLE_TOP 211     /* Art row a part rests on */
#define TRAIN_TERMINAL_ART 234   /* The control room's terminal, its tablet dock below */
#define TRAIN_EXIT_ART 320       /* The control room's hatch */
#define TRAIN_EXIT_LAMP_ART 337  /* Its lock lamp (red, then green) */

/* Zero-based room and art-pixel centre of each clear supply bay. The art
 * generator reads this list too, so a usable crate never shares a furniture
 * footprint. Car 09 (room index 8) is reserved for the container-seal clue. */
#define TRAIN_SUPPLY_BAYS(X) \
    X(1, 180) \
    X(3, 230) \
    X(5, 231) \
    X(7, 188) \
    X(8, 250) \
    X(9, 176) \
    X(11, 178)

/* Extractor housings in room art pixels; their blades turn in the renderer. */
#define TRAIN_VENT_FANS(X) \
    X(0, 282, 92) \
    X(4, 302, 104) \
    X(8, 240, 94) \
    X(9, 305, 95) \
    X(10, 196, 102)

typedef struct {
    bool present, inside, complete, control_read;
    bool tablet; /* Car 01's tablet: the train's map and the terminal's key */
    bool suit;   /* She wears one of car 01's hazmat suits */
    float fumes; /* Seconds until a broken tank's fumes hurt her again */
    float left, right; /* Interior limits in world pixels. */
    int first_zombie, zombie_count;
} TrainJourney;

/* What the player should do next, in the order the mission reads. */
typedef enum {
    TRAIN_GOAL_NONE,
    TRAIN_GOAL_YARD,     /* Outside: clear the yard so the door can be opened */
    TRAIN_GOAL_BOARD,    /* Outside: car 01's door */
    TRAIN_GOAL_TABLET,   /* Car 01's tablet: the terminal needs it */
    TRAIN_GOAL_PART,     /* A part still on its cradle */
    TRAIN_GOAL_TERMINAL, /* Archivo 4: it unlocks the hatch */
    TRAIN_GOAL_CREW,     /* Infected still loose in some car */
    TRAIN_GOAL_EXIT,     /* Everything done: the hatch */
    TRAIN_GOAL_ROAD_PART /* Later routes: a part along the road */
} TrainGoal;

/* What pressing E does at a prompt. */
typedef enum {
    TRAIN_PROMPT_USE,     /* It acts: boards, takes, reads, leaves */
    TRAIN_PROMPT_BLOCKED, /* Not yet: the line says what is missing */
    TRAIN_PROMPT_DONE     /* Already done: the line only reminds */
} TrainPromptKind;

struct StageRun;
void train_install(struct StageRun *run);
int train_room(const struct StageRun *run, float x);
float train_room_left(const struct StageRun *run, int room);
bool train_zombies_clear(const struct StageRun *run);
int train_crew_left(const struct StageRun *run);
int train_crew_in_room(const struct StageRun *run, int room);
bool train_zombie_visible(const struct StageRun *run, int index);
bool train_part_position(const struct StageRun *run, int part, float *x);
int train_part_near(const struct StageRun *run, const Player *player);
int train_part_room(int part); /* Room of a part carried by the train, or -1 */
int train_parts_aboard(unsigned parts); /* Of the three on the train, how many she has */
float train_entry_x(const struct StageRun *run);
float train_suit_x(const struct StageRun *run);
float train_tablet_x(const struct StageRun *run);
int train_supply_art(int room); /* Clear supply bay, or -1 for no bay */
/* Cars whose broken tanks leak: without a suit their fumes hurt her. */
bool train_room_toxic(int room);
bool train_in_fumes(const struct StageRun *run, const Player *player);
/* Each step: the fumes, if she breathes them. */
void train_update(struct StageRun *run, Player *player, float dt);
float train_terminal_x(const struct StageRun *run);
float train_exit_x(const struct StageRun *run);
bool train_exit_open(const struct StageRun *run);
/* The next goal and where it is (world x), for the HUD and the markers. */
TrainGoal train_next_goal(const struct StageRun *run, const Player *player, float *x);
/* Inside, the view never shows past the cars' ends. */
float train_camera(const struct StageRun *run, float camera_left);
bool train_use(struct StageRun *run, Player *player);
/* The line under her feet and what E does there now. */
const char *train_prompt(const struct StageRun *run, const Player *player, TrainPromptKind *kind);
const char *train_room_name(int room);
const char *train_part_name(int part);
int train_part_count(unsigned parts);

#endif
