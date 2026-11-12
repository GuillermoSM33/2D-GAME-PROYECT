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
    float depth;          /* ...and how deep: 0 ankles .. 1 to the waist (drawn sunk) */
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
    bool power_shot;      /* This shot is her ricochet: both hands together */
    float swap_time;      /* Seconds left of taking her second pistol out or away (player_swap) */
    bool swap_back;       /* ...away: the same frames backwards */
    float plant_time;     /* Seconds left of setting a charge (player_plant): she stands to it */
    bool burned;          /* Lightning burned her: slower, heals slower (player_burn) */
    float fear;           /* Seconds left afraid (a horde, the stage sets it): FEAR_PACE faster on her
                           * feet, FEAR_RELOAD_MULT slower to reload, FEAR_FIRE_MULT with endless rounds */
    bool burn_bandaged;   /* ...its bandage is on: a drink of water ends it */
    CatchKind catch_kind; /* While caught: what holds her */
    int catch_blows;      /* Blows still needed to cut free */
    float catch_time;     /* Seconds since it caught her */
    float catch_shake;    /* Seconds left of the shake from a blow at the ropes */
    float catch_anchor_x, catch_anchor_y; /* What the rope hangs from: bough or sapling tip (world x, view y) */
    int health;
    int level;      /* Shown above her head; stats below come from it (progression.c) */
    int max_health;
    float armor;
    float hurt_time;      /* While > 0, she blinks red */
    float heal_time;      /* While > 0, she glows green (a heal) */
    bool bleeding;        /* A wound (a trap): bleed_damage every BLEED_TICK until bandaged */
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
    float vault_speed;  /* ...at this many px a second (a car is a longer leap); 0 = PLAYER_VAULT_SPEED */
    /* Walking while a magazine goes in: the legs walk (legs) under the reload. */
    bool reload_walk;
    bool light_on;     /* Her flashlight (for drawing it: the switch is the stage's)... */
    float light_since; /* ...and seconds since it was flipped */
    float light_time;  /* ...and how long turning it on takes with this gun */
    float light_rows;  /* ...and its lens's height, if not PLAYER_LIGHT_DY */
    bool light_swings; /* ...and it stays on through a blow (art of its own for it) */
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

/* Burned (lightning): slower and slower to heal until bandaged (U held)
 * and given water (U). */
void player_burn(Player *player);

/* Bandaging is wanted: she bleeds, or a burn has no bandage yet. */
bool player_needs_bandage(const Player *player);

/* E lit a charge: she stands PLANT_TIME setting it, neither walking nor
 * shooting (a jump cuts it short). */
void player_plant(Player *player);

/* The blow's animation (its strike frame shows her hitting the ropes). */
const AnimationDef *player_melee_animation(void);

/* While she holds the gun up with its flashlight, or is turning it on or off:
 * its animation and frame, else NULL. */
const AnimationDef *player_light_animation(const Player *player, int *frame);

/* Art rows she is sunk wading the deep river (0 on land, or in the air). */
int player_sunk_rows(const Player *player);

/* How far through turning it on she is: 0 to 1 (and on, past it). */
float player_light_progress(const Player *player);

/* Q with the duals: her hands on the second pistol for a moment, no shooting,
 * out (back false) or away. */
void player_swap(Player *player, bool back);

/* Holding the flashlight up, stood still: which breath she is on. */
int player_light_breath(const Player *player);

/* Art rows its lens is off its mark right now, as she breathes and walks (+ down). */
int player_light_sway(const Player *player);

/* How far its lens has moved from the level gun right now (art px; +x forward, +y
 * down) and how far the beam tilts, on its gun's kick or in a blow. */
void player_light_kick(const Player *player, float *dx, float *dy, float *tilt);

/* The shoot frame shown with the flashlight up: its gun is up already, no drawing
 * it or putting it away. */
int player_lit_shoot_frame(int frame);

/* Whether her hands are on the gun, so its flashlight can shine. */
bool player_light_ready(const Player *player);

/* N at a low barricade: a jump that carries her over it, the way she faces.
 * Only from the ground and not mid-shot. Returns whether she leapt. */
bool player_vault(Player *player);

/* Takes a hit of raw damage through her armor, pushed toward push_dir
 * (-1 or +1). Returns true if it killed her. */
bool player_hit(Player *player, float damage, int push_dir);

/* A trap's bite: she bleeds damage every BLEED_TICK (armor doesn't stop it)
 * until she bandages it, and limps for SLOW_TIME. */
void player_bleed(Player *player, float damage);

bool player_alive(const Player *player);

const char *player_state_name(PlayerState state);

/* Window position where a bullet fired now appears (the muzzle tip). */
void player_muzzle(const Player *player, float *x, float *y);

/* Whether def is the magazine reload (drawn with the gun's reload sheet). */
bool player_reload_animation(const AnimationDef *def);

/* Shared physical sheets for resource validation; weapon-specific sheets
 * are validated through the weapon catalogue. */
const AnimationDef *const *player_animations(int *count);
/* All state definitions, including logical templates drawn with the gun's
 * own reload/throw sheet. Stable ordering for versioned checkpoints. */
const AnimationDef *const *player_state_animations(int *count);

#endif
