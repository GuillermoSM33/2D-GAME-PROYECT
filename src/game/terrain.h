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
    TERRAIN_CHARGE,    /* A charge she planted on the road, its fuse burning: a barrel's blast */
    TERRAIN_WIRE,      /* Barbed wire: no wall, but it tears her up; shots or blows cut it */
    TERRAIN_NET,       /* A net under the leaves: the first to step on it hangs in it */
    TERRAIN_SNARE,     /* A snare: the first to step in it hangs by a foot from the sapling */
    TERRAIN_SPIKES,    /* A spike plate: stepped on, spikes come up (timer: its cycle) */
    TERRAIN_RIVER,     /* A river across the road: wading it is slow (timer: its current) */
    TERRAIN_PUDDLE,    /* A puddle: splashes and ripples under feet */
    TERRAIN_SIGN,      /* A warning sign before a trap (variant: the trap's kind) */
    TERRAIN_DEAD_TREE, /* Only scenery, drawn just as a net's tree: which is which? */
    TERRAIN_SHRUB,     /* Only scenery, drawn just as a snare's shrub */
    TERRAIN_BURNER,    /* A burning oil drum (city): light; shot or blown over, its oil burns the road */
    TERRAIN_SIREN,     /* A patrol car: walked past or hit, its siren wails (timer) and calls a horde;
                        * spent once it has gone off, damage 1 once its light bar is smashed */
    TERRAIN_VEHICLE,   /* A car, jeep or truck left on the road (variant: which): only to walk past */
    TERRAIN_OUTPOST,   /* An army outpost: E searches it once (spent), its floodlight on from then */
    TERRAIN_HYDRANT,   /* A fire hydrant: shot, it bursts (spent) and its water shoots up while timer runs */
    TERRAIN_KINDS
} TerrainKind;

/* What a broken crate gives (terrain_loot). */
typedef enum { LOOT_AMMO, LOOT_HEALTH, LOOT_DYNAMITE, LOOT_GOLD, LOOT_WATER } Loot;

/* Material impacts survive terrain_clear_events until the sound consumer
 * takes them. Repeated impacts of one kind within a tick share one cue. */
typedef enum {
    TERRAIN_SOUND_HIT_WOOD = 1u << 0,
    TERRAIN_SOUND_HIT_METAL = 1u << 1,
    TERRAIN_SOUND_HIT_STONE = 1u << 2,
    TERRAIN_SOUND_HIT_WIRE = 1u << 3,
    TERRAIN_SOUND_HIT_SAND = 1u << 4,
    /* Bits 5..9 are the stage's body impacts and traps (RunSound). */
    TERRAIN_SOUND_GLASS = 1u << 10
} TerrainSound;

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
    float ripple; /* Puddle: seconds left of its rings */
    int variant;  /* Campfire: 1 with a pot hung over it. Coffin: 1 the night's. Wall: 0 a palisade in ruins,
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
    int sirens[TERRAIN_EVENTS], siren_count;     /* Went off */
    int burners[TERRAIN_EVENTS], burner_count;   /* Burning drums knocked over: their fire flares */
    int hydrants[TERRAIN_EVENTS], hydrant_count; /* Hydrants burst */
} TerrainEvents;

typedef struct {
    Piece items[TERRAIN_MAX];
    int count;
    TerrainEvents events;
    unsigned sound_events;
} Terrain;

void terrain_clear(Terrain *terrain);

/* Returns the new piece, or NULL when full. */
Piece *terrain_add(Terrain *terrain, TerrainKind kind, float x);

/* A barricade or wall still standing (not wrecked). */
bool terrain_blocks(const Piece *piece);

/* Half its width, window px. */
float terrain_half_width(TerrainKind kind);

/* A barricade that is a car (its look 0..VEHICLE_LOOKS-1, else -1) or a
 * motorcycle. Both take bullets and, shot enough, clawed down or caught in a
 * blast, blow up like a barrel. */
int terrain_car_look(const Piece *piece);
int terrain_moto_look(const Piece *piece);
/* The barricade variant of a car or a motorcycle's look. */
int terrain_car_variant(int look);
int terrain_moto_variant(int look);

/* The same for a piece: a barricade that is a car is as wide as a car. */
float terrain_piece_half_width(const Piece *piece);

/* The width of the standing barricade right ahead of x (terrain_barricade_ahead), or 0. */
float terrain_vault_span(const Terrain *terrain, float x, int dir);

/* The unsearched outpost within reach of x, or -1; and searching it. */
int terrain_outpost_near(const Terrain *terrain, float x);

/* Whether a burst hydrant's water is still shooting up. */
bool terrain_hydrant_jetting(const Piece *piece);

/* Whether a knocked-over drum is still burning on its side. */
bool terrain_burner_burning(const Piece *piece);

/* Sheets drawn in place of a kind's own: the barricade that is a car, the
 * town's fronts and its supply truck. */
const char *terrain_car_wreck_sheet(void);
const char *terrain_city_front_sheet(void);
const char *terrain_supply_truck_sheet(void);

/* A drum's fire flaring up, its pivot at the bottom center. */
const AnimationDef *terrain_flare(void);

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

/* Where smoke rises from (burning oil, campfires). Returns how many. */
int terrain_smokes(const Terrain *terrain, float *xs, int max);

/* Sets off a patrol car's siren that has not gone off yet: it goes into events. */
void terrain_trip_siren(Terrain *terrain, int index);

/* Whether a siren is wailing now; and how loud for someone at x (0..1). */
bool terrain_siren_on(const Piece *piece);
float terrain_siren_loudness(const Terrain *terrain, float x);

/* The door's look in a wall's doorway (door.png has 3 frames per look):
 * 0 planks, 1 a steel shutter, 2 the train's jammed coupling. */
int terrain_door_look(const Piece *wall);

/* The derailed train drawn round its wall (TERRAIN_WALL, FACADE_TRAIN). */
const char *terrain_train_sheet(void);

/* Opens a closed coffin (she came near): it goes into events. */
void terrain_open_coffin(Terrain *terrain, int index);

/* What crate index of stage stage_index holds: the same every time. */
Loot terrain_loot(int stage_index, int index);

/* Lights a charge on a standing wall within reach of x (WALL_USE_RANGE from
 * its edge). Returns whether it did. */
bool terrain_light_charge(Terrain *terrain, float x);

/* A charge on the road at x, its fuse lit (TERRAIN_CHARGE). */
bool terrain_plant_charge(Terrain *terrain, float x);

/* A blow with a gun over x0..x1: crates, bottles, lamps, coffins and wire
 * take it (wire as WIRE_MELEE_HITS shots), barricades and walls like a
 * claw. Returns how many pieces it hit. */
int terrain_melee(Terrain *terrain, float x0, float x1);

/* The uncut wire she stands in (below WIRE_TOP), or -1. */
int terrain_wire_at(const Terrain *terrain, float x, float height);

/* A spike plate's cycle: seconds left (0 = armed) and whether its spikes
 * are out now. */
bool terrain_spikes_out(const Piece *piece);

/* A warning sign ahead within range, the way she faces: the kind of trap
 * it warns of, or -1. */
int terrain_sign_ahead(const Terrain *terrain, float x, int dir, float range);

/* In a river at x. */
bool terrain_river_at(const Terrain *terrain, float x);

/* How deep the river is at x: 0 on the banks and dry land, 1 in its deep
 * middle (to the waist), in between on the slopes. */
float terrain_river_depth(const Terrain *terrain, float x);

/* Feet in water at x: a river or a puddle. */
bool terrain_water_at(const Terrain *terrain, float x);

/* Feet in water at x (a river or a puddle): true, and a puddle there
 * ripples. */
bool terrain_splash(Terrain *terrain, float x);

/* Art rows a kind's sprite goes under the ground line (water lies in the
 * road, not on it). */
int terrain_sink(TerrainKind kind);

/* Uncut wire ahead of her within range, the way she faces. */
bool terrain_wire_ahead(const Terrain *terrain, float x, int dir, float range);

/* The center of the first wall past x, standing or blown; 0 if there is none. */
float terrain_next_wall(const Terrain *terrain, float x);

/* Whether there is a standing, unlit wall within reach of x. */
bool terrain_wall_near(const Terrain *terrain, float x);

/* Burns down the fuses (a charge that runs out blows) and the fires. */
void terrain_update(Terrain *terrain, float dt);

/* Forgets this step's events, once the stage has acted on them. */
void terrain_clear_events(Terrain *terrain);

/* Takes pending material impacts once, independently of loot events. */
unsigned terrain_take_sound_events(Terrain *terrain);

/* What blows up now: barrels hit and charges burnt down, each setting off
 * barrels within BARREL_CHAIN_RADIUS and wrecking barricades and walls,
 * breaking crates and bottles, felling lamps and bursting coffins within
 * BARREL_RADIUS. Their x into xs (up to max). Returns how many. */
int terrain_explosions(Terrain *terrain, float *xs, int max);

/* Also returns the original kind (barrel, wall charge, planted charge) for
 * each blast. kinds may be NULL, as in terrain_explosions. */
int terrain_explosions_typed(Terrain *terrain, float *xs, TerrainKind *kinds, int max);

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
 * and coffins within radius break, walls and barricades take
 * GRENADE_STRUCTURE_STRIKES claws' worth (two fell a wall). */
void terrain_grenade(Terrain *terrain, float x, float radius);

/* Whether something moving from x0 to x1 at height (window px over the
 * ground) runs into a wall, or a barricade below its top. */
bool terrain_stops(const Terrain *terrain, float x0, float x1, float height);
const AnimationDef *terrain_explosion(void);

#endif
