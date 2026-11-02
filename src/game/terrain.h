#ifndef GAME_TERRAIN_H
#define GAME_TERRAIN_H

#include <stdbool.h>

#include "config.h"
#include "engine/animation.h"
#include "game/bullet.h"

/* The things a stage's route puts on the road (stages.c), in front of the
 * scenery: unlike props, she and the zombies deal with them. */
typedef enum {
    TERRAIN_BARRICADE, /* Low crates: block below their top; she can jump on; claws break them */
    TERRAIN_WALL,      /* A palisade her height: blocks her and bullets; only a blast (or
                        * a long clawing) brings it down */
    TERRAIN_BARREL,    /* A shot (or a blast next to it) blows it up */
    TERRAIN_DYNAMITE,  /* A box of dynamite to pick up: one charge for a wall */
    TERRAIN_SUPPLY,    /* Walk up to it once: full magazines and some health */
    TERRAIN_GOAL,      /* The way out, at the end of the road */
    TERRAIN_CRATE,     /* A loose crate: shot apart (or blown) it gives loot */
    TERRAIN_BOTTLES,   /* Three bottles on a fence: shoot them all for XP */
    TERRAIN_TRAP,      /* A bear trap in the dirt: snaps on the first to step on it */
    TERRAIN_COFFIN,    /* An upright coffin with a zombie inside: opens when she comes near or shoots it */
    TERRAIN_LAMP,      /* An oil lamp on a post: shot down, it sets the ground on fire */
    TERRAIN_FIRE,      /* Burning oil where a lamp fell: hurts whoever walks through */
    TERRAIN_BENCH,     /* A bench: E sits her down to reload; the first sit heals a little */
    TERRAIN_CAMPFIRE,  /* A campfire: standing by it heals slowly */
    TERRAIN_KINDS
} TerrainKind;

/* What a broken crate gives (terrain_loot). */
typedef enum { LOOT_AMMO, LOOT_HEALTH, LOOT_DYNAMITE, LOOT_GOLD } Loot;

#define TERRAIN_EVENTS 8

typedef struct {
    TerrainKind kind;
    float x;      /* World px, center */
    int damage;   /* Barricade or wall: claw strikes taken */
    bool spent;   /* Wrecked, blown, picked up or emptied */
    bool blowing; /* Goes up on the next terrain_explosions */
    float fuse;   /* Wall: seconds left on a lit charge; 0 = none */
    int hits;     /* Crate, bottles, coffin: shots taken */
    float timer;  /* Fire: seconds it still burns; its flicker */
    int zombie;   /* Coffin: the index of the zombie inside (stage_run), or -1 */
    int variant;  /* Campfire: 1 with a pot hung over it. Wall: 0 a palisade in ruins,
                   * 1..FACADE_KINDS a building's front (church, sheriff, smithy, stable)
                   * with its door barred */
} Piece;

/* What happened to the pieces on this step, for the stage to act on:
 * indices into items. Cleared by terrain_update. */
typedef struct {
    int crates[TERRAIN_EVENTS], crate_count;     /* Broken open... */
    bool crate_blasted[TERRAIN_EVENTS];          /* ...by a blast (its health is lost) */
    int bottles[TERRAIN_EVENTS], bottle_count;   /* The last bottle shot */
    int coffins[TERRAIN_EVENTS], coffin_count;   /* Burst open */
} TerrainEvents;

typedef struct {
    Piece items[TERRAIN_MAX];
    int count;
    TerrainEvents events;
} Terrain;

void terrain_clear(Terrain *terrain);

/* Returns the new piece, or NULL when full. */
Piece *terrain_add(Terrain *terrain, TerrainKind kind, float x);

/* A barricade or wall still standing (not wrecked). */
bool terrain_blocks(const Piece *piece);

/* Half its width, window px. */
float terrain_half_width(TerrainKind kind);

/* Height of what she stands on at x: a standing barricade's top, or 0. */
float terrain_floor(const Terrain *terrain, float x);

/* Narrows [*min_x, *max_x] by what she can't walk through from x: walls
 * always, low barricades while her feet are below their top. */
void terrain_bounds(const Terrain *terrain, float x, float height, float *min_x, float *max_x);

/* Bounds while vaulting: only walls stop her. */
void terrain_wall_bounds(const Terrain *terrain, float x, float *min_x, float *max_x);

/* Whether a standing low barricade is right ahead of x, facing dir (-1, +1),
 * within VAULT_REACH of where it stops her. */
bool terrain_barricade_ahead(const Terrain *terrain, float x, int dir);

/* Where a zombie at zombie_x heading for her at player_x walks to: her, or
 * the near side of a barricade or wall between them (or under her feet).
 * *blocker is set to its index, or -1. */
float terrain_zombie_target(const Terrain *terrain, float zombie_x, float player_x, int *blocker);

/* A claw strike on piece index. Returns true when it wrecks it. */
bool terrain_claw(Terrain *terrain, int index);

/* Bullets that cross a wall stop on it; those that cross a barrel set it to
 * blow; crates, bottles, coffins and lamps take the hit (and break, fall or
 * burst open: see events). The bullets are spent. Returns how many hit. */
int terrain_shoot(Terrain *terrain, Bullets *bullets);

/* The bench within reach of x, or -1. */
int terrain_bench_near(const Terrain *terrain, float x);

/* Health a bench's first sit gives: BENCH_HEAL_MIN..MAX, the same every time. */
int terrain_bench_heal(int stage_index, int index);

/* Whether x is warm by a campfire. */
bool terrain_by_campfire(const Terrain *terrain, float x);

/* What gives light (a lit lamp, burning oil, a campfire), for the renderer:
 * its x and the width of its light. Returns how many, up to max. */
int terrain_lights(const Terrain *terrain, float *xs, float *sizes, int max);

/* Where smoke rises from (burning oil, campfires). Returns how many. */
int terrain_smokes(const Terrain *terrain, float *xs, int max);

/* Opens a closed coffin (she came near): it goes into events. */
void terrain_open_coffin(Terrain *terrain, int index);

/* What crate index of stage stage_index holds: the same every time. */
Loot terrain_loot(int stage_index, int index);

/* Lights a charge on a standing wall within reach of x (WALL_USE_RANGE from
 * its edge). Returns whether it did. */
bool terrain_light_charge(Terrain *terrain, float x);

/* Whether there is a standing, unlit wall within reach of x. */
bool terrain_wall_near(const Terrain *terrain, float x);

/* Burns down the fuses (a charge that runs out blows) and the fires. */
void terrain_update(Terrain *terrain, float dt);

/* Forgets this step's events, once the stage has acted on them. */
void terrain_clear_events(Terrain *terrain);

/* What blows up now: barrels hit and charges burnt down, each setting off
 * barrels within BARREL_CHAIN_RADIUS and wrecking barricades and walls,
 * breaking crates and bottles, felling lamps and bursting coffins within
 * BARREL_RADIUS. Their x into xs (up to max). Returns how many. */
int terrain_explosions(Terrain *terrain, float *xs, int max);

/* Picks up the dynamite boxes next to x. Returns how many charges. */
int terrain_take_dynamite(Terrain *terrain, float x);

/* Empties the wagon if she is next to it and it is full. Returns whether. */
bool terrain_take_supply(Terrain *terrain, float player_x);

/* The goal's x, or 0 if the route has none. */
float terrain_goal_x(const Terrain *terrain);

/* Sheet frame of a piece (barricade, wall: whole, cracked, wrecked; wagon:
 * full, empty). */
int terrain_frame(const Piece *piece);

/* Sheet, frame size and frame count of each kind (tools/make_terrain.py). */
const char *terrain_sheet(TerrainKind kind);
void terrain_frame_size(TerrainKind kind, int *w, int *h, int *frames);

/* The green aura and + of a heal, its pivot at the bottom center. */
const AnimationDef *terrain_heal_effect(void);

/* A lit charge (2 frames, its fuse sparking) and the blast. */
const char *terrain_charge_sheet(void);

/* The ruined house a palisade closes, drawn behind it (it stays when the wall goes). */
const char *terrain_ruins_sheet(void);

/* A wall that is a building: its fronts (FACADE_KINDS frames), drawn behind,
 * and its door, the part that blocks (3 frames like the palisade's). */
const char *terrain_facade_sheet(void);
const char *terrain_door_sheet(void);

/* A grenade going off at x: barrels close by catch, crates, bottles, lamps
 * and coffins within radius break. Walls and barricades hold. */
void terrain_grenade(Terrain *terrain, float x, float radius);

/* Whether something moving from x0 to x1 at height (window px over the
 * ground) runs into a wall, or a barricade below its top. */
bool terrain_stops(const Terrain *terrain, float x0, float x1, float height);
const AnimationDef *terrain_explosion(void);

#endif
