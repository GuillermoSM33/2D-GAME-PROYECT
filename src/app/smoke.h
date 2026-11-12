#ifndef APP_SMOKE_H
#define APP_SMOKE_H

#include "engine/input.h"
#include "config.h"
#include "game/player.h"
#include "game/bullet.h"
#include "game/zombie.h"

#define SMOKE_ZOMBIE_GAP (VIEW_WIDTH * .5f + 240.0f)

typedef struct {
    bool enabled;
    float time;
    float x_after_right;
    unsigned walk_frames_seen; /* Bit per frame shown, per sheet */
    unsigned jump_frames_seen;
    unsigned shoot_frames_seen;
    int shots_fired;
    int bullets_seen; /* Most bullets alive at once */
    float bullet_start_x;
    float bullet_last_x;
    float x_before_shot;
    float x_after_shot;
    float max_height;
    unsigned zombie_frames_seen;
    float zombie_start_x;
    float zombie_min_x;
    bool faced_left;
    bool done;
    bool passed;
} SmokeTest;

void smoke_override(const SmokeTest *smoke, bool down[ACTION_COUNT]);
void smoke_observe(SmokeTest *smoke, const Player *player, const Bullets *bullets,
                   const Zombie *zombie);

#endif
