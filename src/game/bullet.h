#ifndef GAME_BULLET_H
#define GAME_BULLET_H

#include <stdbool.h>

#include "config.h"
#include "engine/animation.h"

/* What a gun fires (weapons.c): every bullet carries its own. */
typedef struct {
    float damage;      /* Before armor */
    float speed;       /* Window px per second */
    float range;       /* Window px it flies before vanishing; 0 = until off screen */
    float armor_share; /* Share of the target's armor that counts */
    unsigned tint;     /* 0xRRGGBB over the sprite */
    float slope;       /* Px down per px flown: shotgun pellets fan out; 0 = straight */
    bool ricochet;     /* Glances off the first body it hits on to the next (combat.c) */
} BulletSpec;

typedef struct {
    bool active;
    float x, y;   /* Center of the ball, in world pixels */
    float prev_x; /* Where the last step started: it swept prev_x..x */
    int dir;    /* -1 left, +1 right */
    float flown;  /* Window px since it left the muzzle */
    const void *glanced; /* The body a ricochet glanced off (not hit twice), or NULL */
    float bounce_y;      /* Glancing off: the height it left, and comes back to... */
    float bounce_left;   /* ...and the seconds left of that arc */
    bool burst;          /* It just glanced: an impact to show, once */
    BulletSpec spec;
    Animation anim;
} Bullet;

/* Fixed pool: no allocation while playing. */
typedef struct {
    Bullet items[BULLET_MAX];
    int glances;  /* Ricochets since the last read (a sound for them) */
} Bullets;

void bullets_clear(Bullets *bullets);

/* from_x is where the shot starts (the gun hand), x where the ball appears (the
 * muzzle): anything in between is hit too, even at point-blank range.
 * Returns false when the pool is full (the shot still happens, without a ball). */
bool bullets_fire(Bullets *bullets, float from_x, float x, float y, int dir, const BulletSpec *spec);

/* A plain revolver ball at weapon level 1. */
bool bullets_spawn(Bullets *bullets, float from_x, float x, float y, int dir);

/* Moves the bullets and frees those out of the view starting at world x
 * view_left (see camera_left). */
void bullets_update(Bullets *bullets, float dt, float view_left);

/* A ricochet bullet leaves this body for the next, on a light arc, with its damage times mult. */
void bullet_glance(Bullets *bullets, Bullet *bullet, const void *body, float mult);

int bullets_active_count(const Bullets *bullets);

const AnimationDef *bullet_animation(void);

/* Where a ricochet bullet hits: pivot on the ball. */
const AnimationDef *bullet_impact_animation(void);
const AnimationDef *const *bullet_animations(int *count);

#endif
