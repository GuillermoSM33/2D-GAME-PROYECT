#ifndef GAME_WEAPONS_H
#define GAME_WEAPONS_H

#include <stdbool.h>

/* The guns the characters carry (docs/CHARACTERS.md). Damage is a multiple of
 * the character's weapon level damage (progression.c), so every gun scales
 * with her or his level the same way. */
typedef enum {
    WEAPON_REVOLVER,  /* The cowgirl's hand cannon */
    WEAPON_RIFLE,     /* SWAT: fast, light */
    WEAPON_SHOTGUN,   /* SWAT: slow, three pellets, short reach */
    WEAPON_PLASMA,    /* Hero: experimental, goes through part of the armor */
    WEAPON_DUAL,      /* The cowgirl from level 3: a hand cannon in each hand */
    WEAPON_COUNT
} WeaponId;

typedef struct {
    const char *name;     /* Shown in the HUD */
    float damage_mult;    /* Per bullet, times the weapon level's damage */
    float reload_time;    /* Seconds from one shot to when the next can start */
    int burst;            /* Bullets per shot, one after another; 0 or 1 = a single one */
    float burst_gap;      /* Seconds between the bullets of a burst */
    bool automatic;       /* Holding the trigger keeps firing */
    int magazine;         /* Shots (bursts count as one) before a magazine reload; 0 = never */
    float magazine_reload; /* Seconds that reload takes */
    int pellets;          /* Bullets per shot, stacked vertically */
    float pellet_gap;     /* Window px between pellets */
    float pellet_spread;  /* How fast neighboring pellets part: px apart per px flown */
    float speed;          /* Window px per second */
    float range;          /* Window px a bullet flies before vanishing; 0 = until off screen */
    float armor_share;    /* Share of the target's armor that counts: 1 all, 0.5 half */
    unsigned tint;        /* 0xRRGGBB multiplied over the bullet sprite */
    const char *shot_sound;   /* Path under assets/sounds, or NULL */
    const char *reload_sound;
    int smoke_puffs;          /* Puffs of gun smoke per shot */
    float smoke_scale;        /* Size of that cloud: 1 is the revolver's */
    /* The character's sheet drawn while shooting this gun, instead of "shoot"
     * (assets/sprites/characters/<id>/<shoot_sheet>.png), or NULL. Same size
     * and template as shoot.png. */
    const char *shoot_sheet;
    /* The character's sheet while putting a magazine in (needed with a
     * magazine), same size and template as shoot.png. */
    const char *reload_sheet;
    /* The character's sheet sat on a bench with this gun on the lap (its
     * reload there), instead of "sit", or NULL. Same size as sit.png. */
    const char *sit_sheet;
    /* The character's sheet for a blow with this gun, instead of "melee", or
     * NULL (tools/make_melee.py). Same frame size as shoot.png. */
    const char *melee_sheet;
} WeaponDef;

const WeaponDef *weapon_def(WeaponId id);

/* Damage per second of one target with this armor, at weapon level damage
 * base_damage, firing as fast as the reloads allow (the magazine's too):
 * for balancing. */
float weapon_dps(WeaponId id, float base_damage, float armor);

#endif
