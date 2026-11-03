#ifndef GAME_PLAYER_H
#define GAME_PLAYER_H

#include "engine/animation.h"
#include "game/catch.h"
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
    PLAYER_SIT,   /* On a bench: reloading if a gun needs it, then resting, then dozing */
    PLAYER_THROW, /* Throwing a grenade (player_throw): planted until it ends */
    PLAYER_MELEE, /* A blow with the gun (player_melee): planted until it ends */
    PLAYER_CAUGHT, /* Hanging in a net or a snare (player_catch) until she cuts free */
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
    bool threw;      /* A grenade left her hand on this update */
    bool thrown;     /* This throw's grenade is gone */
    bool struck;     /* A blow landed on this update (the stage sees what it hit) */
    bool landed;     /* This blow has landed */
    float melee_wait; /* Seconds until she can strike again (MELEE_COOLDOWN after a blow) */
    bool wading;          /* In a river: slowed (the stage sets it, run_place_player) */
    int wind;             /* The wind: +1 blowing right, -1 left, 0 none (the stage sets it) */
    bool hot;             /* In the heat: her blows come slower (the stage sets it) */
    bool cold;            /* In the cold: slower blows and steps (the stage sets it) */
    bool cozy;            /* By a campfire: warm, drying fast (the stage sets it) */
    float wet;            /* 1 just out of a river, down to 0 dry */
    float fatigue;        /* Seconds by a fire in the heat (heatstroke at FATIGUE_STROKE) */
    bool fainted;         /* She fainted from the heat (dead to the stage) */
    int water;            /* Jugs of water she carries */
    float drink_time;     /* Seconds left of drinking one (U) */
    float refreshed;      /* Seconds left with the heat off her, after a drink */
    bool drank;           /* A jug was drunk on this update */
    float thirst;         /* Up with time, 0 after a drink (THIRSTY, DEHYDRATED, HALLUCINATING) */
    bool ghost;           /* Drawn as a hallucination of herself (pale, see-through) */
    int wind_feel;        /* On the last step: +1 the wind pushed her, -1 she fought it, 0 */
    int current_feel;     /* On the last step in a river: +1 with the current, -1 against, 0 */
    float bandage;        /* Seconds of holding U toward stopping the bleeding */
    bool bandaged;        /* The bleeding stopped on this update */
    float bandage_shown;  /* Seconds left of the done bandage on her leg */
    CatchKind catch_kind; /* While caught: what holds her */
    int catch_blows;      /* Blows still needed to cut free */
    float catch_time;     /* Seconds since it caught her */
    float catch_shake;    /* Seconds left of the shake from a blow at the ropes */
    float catch_anchor_x, catch_anchor_y; /* A snare: the sapling's tip (world x, view y) */
    int health;
    int level;      /* Shown above her head; stats below come from it (progression.c) */
    int max_health;
    float armor;
    float hurt_time;      /* While > 0, she blinks red */
    float heal_time;      /* While > 0, she glows green (a heal) */
    float bleed_time;     /* While > 0, she bleeds (a trap): bleed_damage every BLEED_TICK */
    float bleed_tick;
    float bleed_damage;
    float slow_time;      /* While > 0, she limps at SLOW_MULT of her pace */
    float knockback_time; /* While > 0, she slides away from the hit */
    int knockback_dir;    /* -1 or +1 */
    /* What the stage puts around her (player_set_ground): the height she
     * stands on here and how far she can walk. */
    float floor;
    float min_x, max_x;
    bool vaulting;      /* Leaping over a low barricade (player_vault): carried across */
    /* Walking while a magazine goes in: the legs walk (legs) under the reload. */
    bool reload_walk;
    Animation legs;
    float sit_time;    /* Seconds on the bench */
    unsigned sit_guns; /* Weapon slots (bits) still to reload sat, one after another */
    int sit_gun;       /* The slot on her lap being reloaded, or -1 */
    float sit_gun_time; /* Seconds into that gun's reload */
    bool sit_reloaded; /* A gun's sitting reload finished on this update... */
    int sit_reloaded_gun; /* ...this slot's: fill it */
    Animation anim;
} Player;

/* Level 1, standing at the start, full health. */
void player_init(Player *player);

/* Her level's stats; with heal, back to full health (a level up does). */
void player_set_stats(Player *player, int level, int max_health, float armor, bool heal);
void player_update(Player *player, const InputState *input, float dt);

/* For the next update: the top of what is under her (0 = the ground; a
 * barricade's top) and the walls either side (a fight in progress, a
 * barricade she is below the top of). She falls off when floor drops. */
void player_set_ground(Player *player, float floor, float min_x, float max_x);

/* Sits her on the bench at bench_x, if she is free to. Each weapon slot set
 * in reload_guns (bit per slot) gets a reload on her lap, one after the other
 * (sit_reloaded and sit_reloaded_gun tell when each is full). Moving,
 * jumping, shooting or a hit gets her up. */
bool player_sit(Player *player, float bench_x, unsigned reload_guns);

/* F: the grenade throw (the "throw" sheet), from the ground and not mid-shot.
 * threw tells the update the grenade leaves. Returns whether she started. */
bool player_throw(Player *player);

/* V: a blow with the gun in hand, on the ground and not mid-shot; struck
 * tells the update when it lands. Returns whether she started. */
bool player_melee(Player *player);

/* A trap hangs her up (CATCH_NET or CATCH_SNARE) where she stands: no
 * moving or shooting until her blows (player_struggle) cut her free. */
bool player_catch(Player *player, CatchKind kind, float anchor_x, float anchor_y);

/* V while caught: a blow at the ropes. Returns true on the one that frees
 * her: she drops to the ground. */
bool player_struggle(Player *player);

/* 0 fine, 1 thirsty, 2 dehydrated, 3 hallucinating. */
int player_thirst_level(const Player *player);

/* Seconds she takes to dry from wet as things are (heat, cold, a fire). */
float player_dry_time(const Player *player);

/* While she drinks or binds a wound: its animation and frame, else NULL. */
const AnimationDef *player_care_animation(const Player *player, int *frame);

/* The blow's animation (its strike frame shows her hitting the ropes). */
const AnimationDef *player_melee_animation(void);

/* N at a low barricade: a jump that carries her over it, the way she faces.
 * Only from the ground and not mid-shot. Returns whether she leapt. */
bool player_vault(Player *player);

/* Takes a hit of raw damage through her armor, pushed toward push_dir
 * (-1 or +1). Returns true if it killed her. */
bool player_hit(Player *player, float damage, int push_dir);

/* A trap's bite: she bleeds damage every BLEED_TICK for BLEED_TIME (armor
 * doesn't stop it) and limps for SLOW_TIME. */
void player_bleed(Player *player, float damage);

bool player_alive(const Player *player);

const char *player_state_name(PlayerState state);

/* Window position where a bullet fired now appears (the muzzle tip). */
void player_muzzle(const Player *player, float *x, float *y);

/* Whether def is the magazine reload (drawn with the gun's reload sheet). */
bool player_reload_animation(const AnimationDef *def);

/* Every animation the player uses, so their sheets can be validated. */
const AnimationDef *const *player_animations(int *count);

#endif
