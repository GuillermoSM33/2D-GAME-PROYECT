#ifndef GAME_HALLUCINATION_H
#define GAME_HALLUCINATION_H

#include <stdbool.h>

#include "config.h"
#include "game/bullet.h"

/* What she sees when thirst makes her hallucinate: zombies that aren't
 * there, walking in from the edges of the view toward her and gone when
 * they reach her or when shot (the bullet is wasted), and now and then
 * herself, standing ahead and looking back at her. No SDL. */
typedef struct {
    bool active;
    bool fading; /* Shot, or it reached her: going */
    float x;     /* World px */
    int facing;  /* -1 left, +1 right */
    float time;  /* Seconds walking (its walk frame) */
    float fade;  /* 1 seen, down to 0 gone */
} Phantom;

typedef struct {
    Phantom phantoms[PHANTOMS_MAX];
    float spawn_wait;  /* Seconds until the next phantom */
    int side;          /* The edge the last one came from: they take turns */
    bool double_on;    /* Herself, standing ahead */
    float double_x;
    int double_facing;
    float double_time; /* Seconds left of it, or until the next */
    int spawned;       /* Phantoms that walked in on the last update... */
    int vanished;      /* ...and that went (shot or reached her), for a puff */
    float vanished_x[PHANTOMS_MAX];
} Hallucination;

void hallucination_clear(Hallucination *h);

/* on: she is hallucinating now (else what she sees fades away). */
void hallucination_update(Hallucination *h, bool on, float player_x, int player_facing, float camera_x,
                          float dt);

/* Bullets through a phantom: it goes, the bullet is spent. Returns the hits. */
int hallucination_shoot(Hallucination *h, Bullets *bullets);

#endif
