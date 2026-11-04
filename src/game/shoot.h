#ifndef GAME_SHOOT_H
#define GAME_SHOOT_H

#include <stdbool.h>

/* Standing shot: draw, aim, fire, recoil, holster (see config.h). After the
 * bullet she reloads: the recoil frame holds until the next ball is in. */
typedef struct {
    bool active;
    bool fired;      /* The bullet already left during this shot */
    int start_frame; /* 0 for a fresh shot, the aim frame for a follow-up */
    float time;      /* Seconds since start_frame */
    float reload;    /* Seconds left until the next shot can start */
    float reload_time; /* The gun's: what reload restarts at after each bullet */
    int burst;         /* The gun's bullets per shot */
    float burst_gap;   /* ...and seconds between them */
    bool automatic;    /* The gun keeps firing while the trigger is held */
    bool piston;       /* Two guns taking turns: each shot plays whole, the other's next */
    bool other_gun;    /* ...this shot is the other gun's */
    bool next_other;   /* ...and whose the next is: it changes once a bullet has left */
    bool held;         /* ...the trigger is down: the next turn follows without a stop */
    bool queued;       /* ...it was clicked during this turn: the next follows too */
    int burst_left;    /* Bullets of this shot still to come */
    float burst_timer; /* Seconds until the next of them */
    int magazine;          /* The gun's shots per magazine; 0 = it never runs dry */
    float mag_reload_time; /* ...and seconds to put a full one in */
    int rounds;            /* Shots left in the magazine */
    float mag_reload;      /* Seconds left of a magazine reload; > 0 while reloading */
} Shot;

/* Idle, with the revolver's reload time and single shot. */
void shot_reset(Shot *shot);

/* Ends the shot in progress (a jump, a death), keeping the gun and what is
 * left in its magazine; a magazine reload cut short starts over next time. */
void shot_cancel(Shot *shot);

/* The gun changed: this is its reload time from the next bullet on. */
void shot_set_reload(Shot *shot, float reload_time);

/* The gun changed: bullets per shot (1 = single), seconds between them and
 * whether holding the trigger keeps firing. */
void shot_set_burst(Shot *shot, int burst, float burst_gap, bool automatic);

/* The gun changed: two guns taking turns like a piston, or one gun. */
void shot_set_piston(Shot *shot, bool piston);

/* The trigger this step: a click, and whether it is held (only an automatic gun
 * fires on while held). With two guns they keep the turns coming. */
void shot_trigger(Shot *shot, bool pressed, bool held);

/* The gun changed: shots per magazine (0 = no magazine), seconds to reload
 * one, and the shots it still has (a gun put away keeps its count). */
void shot_set_magazine(Shot *shot, int magazine, float reload_time, int rounds);

/* Starts a shot. While one is active, a new shot is only accepted once the
 * previous bullet is out, its muzzle flash was shown and she reloaded; it then
 * skips the draw and restarts already aimed. With the magazine empty it starts
 * the magazine reload instead. Returns whether it started. */
bool shot_start(Shot *shot);

/* Advances the sequence. Returns true on each step a bullet fires: once per
 * shot, or once per bullet of a burst. Between those bullets the frame
 * flicks between fire and recoil, and the reload starts after the last. */
bool shot_update(Shot *shot, float dt);

/* Frames per second this shot's sheet plays at. */
float shot_fps(const Shot *shot);

/* Sheet frame to show, 0 .. PLAYER_SHOOT_FRAMES - 1. */
int shot_frame(const Shot *shot);

/* R: a new magazine now, if the gun has one and it isn't full (one round
 * left is enough). A shot in progress is dropped. Returns whether it started. */
bool shot_reload_now(Shot *shot);

/* A magazine is going in: the reload sheet plays instead of the shoot one.
 * The shot empties the magazine with its last bullet, shows the recoil and
 * then reloads; when done it stands aimed, so a held trigger fires on. */
bool shot_reloading(const Shot *shot);

/* How far the magazine reload is, 0 .. 1. */
float shot_reload_progress(const Shot *shot);

#endif
