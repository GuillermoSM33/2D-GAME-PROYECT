#ifndef GAME_CROWS_H
#define GAME_CROWS_H

#include <stdbool.h>

#include "config.h"
#include "game/bullet.h"

/* Crows on the road, pecking at the dirt in small flocks. They fly off
 * when she walks up to them or at a noise near enough (a shot, a blast),
 * each away from her and up out of the view. A bullet or a blast kills
 * one: it drops, lies on the road and fades. No SDL. */
typedef struct {
    float x;      /* World px */
    float height; /* Window px over the ground */
    float vx, vy; /* Px per second; vy up */
    int facing;   /* -1 left, +1 right */
    bool flying;
    bool gone;    /* Flown out of the view, or its body faded */
    bool dead;    /* Shot or blown: falling, then lying on the road */
    float dead_time; /* Seconds lying there */
    float time;   /* Seconds into its pecking or its flight */
} Crow;

typedef struct {
    Crow items[CROWS_MAX];
    int count;
    int took_off; /* Crows that took off on the last update (for a caw) */
    int killed;   /* Crows killed during the current simulation step */
} Crows;

/* Flocks along the road from start_x to start_x + length, the same for a
 * stage every time. */
void crows_start(Crows *crows, int stage_index, float start_x, float length);

/* She is at player_x (moving or not): close enough and moving, they go. */
void crows_update(Crows *crows, float player_x, bool moving, float dt);

/* A noise at x heard range px away: every crow within it takes off. */
void crows_noise(Crows *crows, float x, float range);

/* Bullets against the crows (frame-sized boxes): a hit kills it and the
 * bullet is spent; the rest of its flock hears it. Returns the hits. */
int crows_shoot(Crows *crows, Bullets *bullets);

/* A blast at x: crows within radius die, the rest take off. */
/* Returns the number of crows killed by the blast. */
int crows_blast(Crows *crows, float x, float radius);

/* Its frame in sprites/crow/crow: 0-1 pecking, 2-5 the wingbeat, 6
 * falling dead, 7 lying dead. */
int crow_frame(const Crow *crow);

/* 1 while alive or fresh dead, fading to 0 before it is gone. */
float crow_opacity(const Crow *crow);

#endif
