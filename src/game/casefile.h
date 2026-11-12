#ifndef GAME_CASEFILE_H
#define GAME_CASEFILE_H

#include <stdbool.h>

#include "engine/input.h"

/* "Encuentra la causa" (docs/LORE.md): the clues to the outbreak, found along
 * the stages, pinned on the case file's board and grouped into cases. Once
 * every clue of a case is in, the player answers its question; the right
 * answer opens its report: that part of the story, written out in full as a
 * case file. Getting it wrong costs nothing. The story's animations are kept
 * apart, as video tapes (HISTORIA): the intro and each stage's ending.
 *
 * Each stage holds three: one in the exit chest, one on a zombie of its
 * route (both sure to turn up) and one hidden in a crate on the road, for
 * whoever breaks it. What a stage changes in the landscape is told at its
 * end anyway (story beats); the clues tell why. No SDL. */

#define CLUE_COUNT 30 /* 15 on each route: the save keeps them as bits of one word */
#define CASE_COUNT 7  /* Four on the first route, three on the second */
#define CASE_MAX_CLUES 6
#define STAGE_CLUES 3
#define CASE_OPTIONS 3
#define STORY_MAX_LINES 4

typedef enum { CLUE_DOCUMENT, CLUE_TAPE, CLUE_PHOTO, CLUE_OBJECT } ClueKind;
typedef enum { CLUE_FROM_MISSION, CLUE_FROM_ZOMBIE, CLUE_FROM_CRATE } ClueSource;

typedef struct {
    const char *title;
    const char *text;    /* What it is, on the board */
    const char *examine; /* What a closer look shows (EXAMINAR) */
    ClueKind kind;     /* Its look in sprites/clues (one frame per clue, in this order) */
    int case_index;
    int stage;         /* Stage index it is found in */
    ClueSource source;
    float at;          /* CLUE_FROM_CRATE: the crate nearest this share of the road (0 start, 1 goal) */
    int zombie;        /* CLUE_FROM_ZOMBIE: that zombie of the route, in route order */
} ClueDef;

typedef struct {
    const char *name;
    const char *question;
    const char *options[CASE_OPTIONS];
    int answer;
    const char *report_title; /* The case written up, once solved: its heading... */
    const char *report;       /* ...and its text, paragraphs split by blank lines */
} CaseDef;

extern const ClueDef CLUES[CLUE_COUNT];
extern const CaseDef CASES[CASE_COUNT];

/* What the player has: kept in the save, the same for every character
 * (there is one story). */
typedef struct {
    unsigned found;      /* Bit per clue */
    unsigned solved;     /* Bit per case */
    unsigned beats_seen; /* Bit per stage: its end-of-stage beat was played */
} CaseFile;

void casefile_init(CaseFile *file);
bool casefile_has(const CaseFile *file, int clue);
/* Adds a clue; true if it is new. */
bool casefile_take(CaseFile *file, int clue);
int casefile_found_count(const CaseFile *file);

/* A case's clues in board order into out (up to CASE_MAX_CLUES); their count. */
int casefile_case_clues(int case_index, int *out);
int casefile_case_found(const CaseFile *file, int case_index);
bool casefile_solved(const CaseFile *file, int case_index);
/* Every clue in and not solved yet: its question can be answered. */
bool casefile_ready(const CaseFile *file, int case_index);
/* The player's answer: true (and the case solved) when it is the right one. */
bool casefile_answer(CaseFile *file, int case_index, int option);

/* Where clues turn up: the clue of that source in that stage, or -1.
 * share: where the broken crate stood along the road (0..1). */
int casefile_mission_clue(int stage);
int casefile_zombie_clue(int stage, int zombie_index, int zombie_count);
int casefile_crate_clue(int stage, float share);
int casefile_stage_found(const CaseFile *file, int stage);

/* ---- The board on screen -------------------------------------------------- */

/* Rows are the cases; in a row, its clues then its question's slot. */
#define BOARD_X 24
#define BOARD_Y 72
#define BOARD_W 912
#define BOARD_ROW_H 70
#define BOARD_LABEL_W 168
#define BOARD_CARD 58     /* A card: the clue's sprite at 2x on its paper */
#define BOARD_CARD_STEP 70
#define BOARD_SLOT_W 150  /* The question's slot at the end of a row */
#define BOARD_DETAIL_Y 360 /* The selected clue's text, under the board */
#define BOARD_OPTION_W 600
#define BOARD_OPTION_H 40
#define BOARD_OPTION_Y 250

#define BOARD_ROWS 4 /* Cases on a page of the board: the first route's, then the second's */

int board_card_x(int col);
int board_row_y(int row);
int board_page(int row);
int board_page_rows(int page);
int board_slot_x(void);

typedef enum { BOARD_STAY, BOARD_BACK, BOARD_REVEAL, BOARD_EXAMINE } BoardResult;

typedef struct {
    int row, col;       /* col == the case's clue count: its question's slot */
    bool asking;        /* The question is up */
    int option;
    float wrong_time;   /* Seconds left of "no cuadra" after a wrong answer */
    int revealed;       /* BOARD_REVEAL: the case just solved */
    int examined;       /* BOARD_EXAMINE: the clue to look at closely */
} BoardView;

void board_view_init(BoardView *view);
/* Arrows/WASD move; Enter on a found clue examines it, on a ready case's
 * slot asks its question (and answers it); Esc closes the question or the
 * board. The mouse picks cards (a click examines), the slot and the answers. */
BoardResult board_view_update(BoardView *view, CaseFile *file, const InputState *input, float dt);
/* The clue under the selection, or -1 (the question's slot). */
int board_selected_clue(const BoardView *view);

/* ---- Story beats ------------------------------------------------------------ */

typedef enum {
    STORY_ATARDECER, STORY_CEMENTERIO, STORY_NOCHE, STORY_PUEBLO, /* A stage's landscape */
    STORY_LAB,         /* Laboratorio 4's corridor */
    STORY_AFUERAS, STORY_CENTRO, STORY_VIAS, STORY_CIUDAD_NOCHE, STORY_BASE, /* The second route's */
    STORY_VISUALS
} StoryVisual;

typedef struct {
    StoryVisual visual;  /* Where it happens, before its own shots dress it */
    const char *lines[STORY_MAX_LINES];
    int count;
    int scene;           /* Which tape's shots play under its lines (app/story_render.c) */
} StoryBeat;

/* What the landscape's change after a stage means, played when it is first
 * cleared; NULL for stages with none. */
const StoryBeat *story_after_stage(int stage);

/* What is told before a stage is first played (2-1: the town leads to the
 * city); NULL for the rest. */
const StoryBeat *story_before_stage(int stage);

/* The bit of CaseFile.beats_seen for a stage's beat: after it, or before it. */
#define STORY_BEFORE_BIT 16
unsigned story_bit(int stage, bool before);

/* ---- A solved case's report ----------------------------------------------- */

/* The case file written up: it slides in, its stamp comes down, and it stays
 * until Enter or Esc closes it. */
typedef struct {
    int case_index;
    float time;
} Report;

#define REPORT_STAMP_AT 0.55f /* Seconds in when the RESUELTO stamp lands */

void report_open(Report *report, int case_index);
/* False once closed. stamped: the stamp landed on this update (a thud). */
bool report_update(Report *report, const InputState *input, float dt, bool *stamped);

/* ---- Examining a clue ----------------------------------------------------- */

/* A found clue up close, filling the screen: its picture large, where it
 * turned up and the details a closer look shows. Enter or Esc closes it. */
typedef struct {
    int clue;
    float time;
} ClueExam;

void exam_open(ClueExam *exam, int clue);
bool exam_update(ClueExam *exam, const InputState *input, float dt);

/* ---- The video tapes (HISTORIA) --------------------------------------------- */

/* The intro and each stage's ending, kept to watch again. */
#define TAPE_COUNT 11
#define TAPE_INTRO 0

typedef struct {
    const char *title;
    int stage;   /* The stage whose ending it is; -1 for the intro */
    bool before; /* ...or played before that stage instead */
} TapeDef;

extern const TapeDef TAPES[TAPE_COUNT];

bool tape_unlocked(const CaseFile *file, int tape);
/* A tape's beat (NULL for the intro), and the tape of a stage's beat or -1. */
const StoryBeat *tape_beat(int tape);
int stage_tape(int stage, bool before);
int tapes_unlocked(const CaseFile *file);

#define TAPE_X 30
#define TAPE_Y 122
#define TAPE_STEP 182
#define TAPE_W 168
#define TAPE_H 112
#define TAPE_COLUMNS 5  /* In rows: the intro and the first route, then the second */
#define TAPE_ROW_STEP 176
#define TAPE_ROWS_SHOWN 2
int tape_x(int tape);
int tape_y(int tape, int selected); /* Scrolled so the selected one's row shows */

typedef struct {
    int selected;
} TapeView;

#define TAPE_BACK (-2)
/* The tape to play (an unlocked one), TAPE_BACK on Esc, or -1. */
int tape_view_update(TapeView *view, const CaseFile *file, const InputState *input);

/* A beat playing: each line typed, held, then the next; Enter hurries the
 * line along (or goes to the next), Esc ends it. */
typedef struct {
    StoryBeat beat;
    int line;
    float time;  /* Seconds into the line */
    bool done;
} Story;

void story_start(Story *story, const StoryBeat *beat);
void story_update(Story *story, bool advance, bool skip, float dt);
/* The line typed so far into buf; its opacity. */
bool story_caption(const Story *story, char *buf, int size, float *alpha);
float story_line_length(const char *line);

#endif
