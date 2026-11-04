#include "game/shoot.h"

#include <math.h>
#include <string.h>

#include "config.h"

void shot_reset(Shot *shot)
{
    memset(shot, 0, sizeof(*shot));
    shot->reload_time = PLAYER_SHOOT_RELOAD_TIME;
    shot->burst = 1;
}

void shot_cancel(Shot *shot)
{
    Shot gun = *shot;
    if (gun.fired && gun.burst_left > 0)
        gun.rounds--; /* A burst cut short still spent its shot */
    memset(shot, 0, sizeof(*shot));
    shot->reload_time = gun.reload_time;
    shot->burst = gun.burst;
    shot->burst_gap = gun.burst_gap;
    shot->automatic = gun.automatic;
    shot->piston = gun.piston;
    shot->other_gun = gun.other_gun;
    shot->next_other = gun.next_other;
    shot->magazine = gun.magazine;
    shot->mag_reload_time = gun.mag_reload_time;
    shot->rounds = gun.rounds;
}

void shot_set_reload(Shot *shot, float reload_time)
{
    shot->reload_time = reload_time;
}

void shot_set_burst(Shot *shot, int burst, float burst_gap, bool automatic)
{
    shot->burst = burst > 1 ? burst : 1;
    shot->burst_gap = burst_gap;
    shot->automatic = automatic;
}

void shot_set_piston(Shot *shot, bool piston)
{
    shot->piston = piston;
}

void shot_trigger(Shot *shot, bool pressed, bool held)
{
    shot->held = held && shot->automatic;
    if (pressed && shot->active && shot->piston)
        shot->queued = true;
}

float shot_fps(const Shot *shot)
{
    return shot->piston ? PLAYER_PISTON_FPS : PLAYER_SHOOT_FPS;
}

void shot_set_magazine(Shot *shot, int magazine, float reload_time, int rounds)
{
    shot->magazine = magazine > 0 ? magazine : 0;
    shot->mag_reload_time = reload_time;
    shot->rounds = rounds < 0 || rounds > shot->magazine ? shot->magazine : rounds;
}

static bool empty(const Shot *shot)
{
    return shot->magazine > 0 && shot->rounds <= 0;
}

static void start_magazine_reload(Shot *shot)
{
    shot->active = true;
    shot->fired = true;
    shot->burst_left = 0;
    shot->mag_reload = shot->mag_reload_time > 0.0f ? shot->mag_reload_time : 1e-3f;
}

bool shot_reload_now(Shot *shot)
{
    if (shot->magazine == 0 || shot->mag_reload > 0.0f)
        return false;
    if (shot->active)
        shot_cancel(shot);
    if (shot->rounds >= shot->magazine)
        return false;
    shot->time = 0.0f;
    shot->start_frame = 0;
    start_magazine_reload(shot);
    return true;
}

/* Holds the sequence mid-frame on this sheet frame. */
static void hold_frame(Shot *shot, int frame)
{
    shot->time = ((float)(frame - shot->start_frame) + 0.5f) / shot_fps(shot);
}

static int raw_frame(const Shot *shot)
{
    return shot->start_frame + (int)(shot->time * shot_fps(shot));
}

bool shot_start(Shot *shot)
{
    if (shot->mag_reload > 0.0f)
        return false;
    if (empty(shot)) {
        if (shot->active) /* The recoil still showing: the reload follows it */
            return false;
        start_magazine_reload(shot);
        return true;
    }
    if (shot->piston) { /* A turn under way plays whole: shot_update starts the next */
        if (shot->active)
            return false;
        shot->active = true;
        shot->fired = false;
        shot->start_frame = 0;
        shot->time = 0.0f;
        shot->other_gun = shot->next_other;
        return true;
    }
    bool follow_up = shot->active;
    if (follow_up && (raw_frame(shot) <= PLAYER_SHOOT_FIRE_FRAME || shot->reload > 0.0f ||
                      shot->burst_left > 0))
        return false;
    shot->active = true;
    shot->fired = false;
    shot->start_frame = follow_up ? PLAYER_SHOOT_AIM_FRAME : 0;
    shot->time = 0.0f;
    return true;
}

bool shot_update(Shot *shot, float dt)
{
    if (!shot->active)
        return false;
    if (shot->mag_reload > 0.0f) {
        shot->mag_reload -= dt;
        if (shot->mag_reload > 0.0f)
            return false;
        /* Full again, standing aimed after the recoil: the trigger fires on. */
        shot->mag_reload = 0.0f;
        shot->rounds = shot->magazine;
        shot->reload = 0.0f;
        shot->time = 0.0f;
        hold_frame(shot, PLAYER_SHOOT_FIRE_FRAME + 1);
        return false;
    }
    shot->time += dt;
    shot->reload = fmaxf(0.0f, shot->reload - dt);
    if (shot->burst_left > 0) {
        /* Mid-burst: the flash for the first half of the gap, then the kick. */
        shot->burst_timer -= dt;
        bool flash = shot->burst_timer > shot->burst_gap * 0.5f;
        hold_frame(shot, flash ? PLAYER_SHOOT_FIRE_FRAME : PLAYER_SHOOT_FIRE_FRAME + 1);
        if (shot->burst_timer > 0.0f)
            return false;
        shot->burst_left--;
        shot->burst_timer += shot->burst_gap;
        hold_frame(shot, PLAYER_SHOOT_FIRE_FRAME);
        if (shot->burst_left == 0) {
            shot->reload = shot->reload_time;
            shot->rounds--;
        }
        return true;
    }
    int frame = raw_frame(shot);
    if (shot->fired && empty(shot) && frame >= PLAYER_SHOOT_RELOAD_FRAME) {
        /* The magazine ran dry: once the recoil has shown, put a new one in. */
        start_magazine_reload(shot);
        return false;
    }
    if (!shot->piston && shot->fired && shot->reload > 0.0f && frame > PLAYER_SHOOT_RELOAD_FRAME) {
        /* Reloading: stay mid-frame on the recoil until the ball is in. */
        hold_frame(shot, PLAYER_SHOOT_RELOAD_FRAME);
        frame = PLAYER_SHOOT_RELOAD_FRAME;
    }
    if (frame >= PLAYER_SHOOT_FRAMES) {
        if (shot->piston && (shot->held || shot->queued)) {
            /* The other gun is on its way up already: its turn, no stop between. */
            shot->time -= (float)PLAYER_SHOOT_FRAMES / shot_fps(shot);
            shot->fired = false;
            shot->queued = false;
            shot->other_gun = shot->next_other;
            return false;
        }
        shot_cancel(shot);
        return false;
    }
    if (!shot->fired && frame >= PLAYER_SHOOT_FIRE_FRAME) {
        shot->fired = true;
        shot->next_other = !shot->other_gun;
        shot->burst_left = shot->burst - 1;
        shot->burst_timer = shot->burst_gap;
        shot->reload = shot->burst_left > 0 ? 0.0f : shot->reload_time;
        if (shot->burst_left == 0)
            shot->rounds--;
        return true;
    }
    return false;
}

bool shot_reloading(const Shot *shot)
{
    return shot->active && shot->mag_reload > 0.0f;
}

float shot_reload_progress(const Shot *shot)
{
    if (!shot_reloading(shot) || shot->mag_reload_time <= 0.0f)
        return 0.0f;
    return fminf(1.0f, fmaxf(0.0f, 1.0f - shot->mag_reload / shot->mag_reload_time));
}

int shot_frame(const Shot *shot)
{
    int frame = raw_frame(shot);
    return frame < PLAYER_SHOOT_FRAMES ? frame : PLAYER_SHOOT_FRAMES - 1;
}
