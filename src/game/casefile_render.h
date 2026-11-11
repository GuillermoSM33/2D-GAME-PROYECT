#ifndef GAME_CASEFILE_RENDER_H
#define GAME_CASEFILE_RENDER_H

#include <SDL.h>

#include "game/casefile.h"

#define CLUE_SPRITE 24 /* Art px of each clue's picture (sprites/clues/clues) */
#define CLUE_TOAST_SECONDS 4.0f /* How long the popup of a found clue stays */

/* A clue's picture at a whole scale, top-left at x, y. */
void clue_draw(SDL_Renderer *renderer, int clue, int x, int y, int scale, Uint8 alpha);

/* Breaks text into lines no wider than max_w at scale (at spaces), up to
 * max_lines of up to 95 bytes each; returns how many. */
int casefile_wrap(const char *text, int scale, int max_w, char lines[][96], int max_lines);

/* The case file: its board of cases and clues, the selected clue's text,
 * and a case's question when it is being answered. */
void casefile_render(SDL_Renderer *renderer, const CaseFile *file, const BoardView *view, float time);

/* The popup at the top of a stage when a clue turns up: its picture, its
 * name and how many of the stage's are in. left: seconds left of it. */
void casefile_draw_toast(SDL_Renderer *renderer, int clue, int stage_found, float left);

/* Cork with its grain, over a rectangle (the board, the story's case). */
void casefile_draw_cork(SDL_Renderer *renderer, int x, int y, int w, int h);

/* A clue pinned on the board as a card (or the empty spot of a missing one). */
void casefile_draw_card(SDL_Renderer *renderer, int clue, bool found, int x, int y, int scale, bool selected);

/* A solved case written up: its report on a sheet of paper over the board,
 * its clues pinned beside it, the RESUELTO stamp coming down. */
void report_render(SDL_Renderer *renderer, const Report *report, const CaseFile *file);

/* A clue up close: its picture large on its card, and the examination
 * notes (what it is, where it turned up, the details) on a sheet. */
void exam_render(SDL_Renderer *renderer, const ClueExam *exam, const CaseFile *file);

/* HISTORIA: the story's animations as video tapes on a shelf, the locked ones
 * blank, with the stage that unlocks them. */
void tapes_render(SDL_Renderer *renderer, const TapeView *view, const CaseFile *file);

#endif
