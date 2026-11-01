#ifndef GAME_PLAYER_H
#define GAME_PLAYER_H

#include "engine/animation.h"
#include "engine/input.h"
#include "game/jump.h"
#include "game/shoot.h"

typedef enum {
    PLAYER_IDLE,
    PLAYER_WALK,
    PLAYER_RUN,
    PLAYER_JUMP, /* In the air */
    PLAYER_LAND, /* Short landing after a jump */
    PLAYER_SHOOT, /* Standing shot; feet stay planted */
    PLAYER_DEAD   /* Out of health; only a reset brings her back */
} PlayerState;

typedef enum {
    FACING_LEFT = -1,
    FACING_RIGHT = 1
} Facing;

typedef struct {
    float x; /* Horizontal center of the body, in world pixels */
    Facing facing;
    PlayerState state;
    Jump jump;
    Shot shot;
    bool shot_fired; /* A bullet left on this update (hook for bullets, sound...) */
    int health;
    int level;      /* Shown above her head; stats below come from it (progression.c) */
    int max_health;
    float armor;
    float hurt_time;      /* While > 0, she blinks red */
    float knockback_time; /* While > 0, she slides away from the hit */
    int knockback_dir;    /* -1 or +1 */
    Animation anim;
} Player;

/* Level 1, standing at the start, full health. */
void player_init(Player *player);

/* Her level's stats; with heal, back to full health (a level up does). */
void player_set_stats(Player *player, int level, int max_health, float armor, bool heal);
void player_update(Player *player, const InputState *input, float dt);

/* Takes a hit of raw damage through her armor, pushed toward push_dir
 * (-1 or +1). Returns true if it killed her. */
bool player_hit(Player *player, float damage, int push_dir);

bool player_alive(const Player *player);

const char *player_state_name(PlayerState state);

/* Window position where a bullet fired now appears (the muzzle tip). */
void player_muzzle(const Player *player, float *x, float *y);

/* Every animation the player uses, so their sheets can be validated. */
const AnimationDef *const *player_animations(int *count);

#endif
