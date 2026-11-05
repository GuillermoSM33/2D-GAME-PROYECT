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
    bool piston;          /* Two guns taking turns, each shot played whole */
    int magazine;         /* Shots (bursts count as one) before a magazine reload; 0 = never */
    float magazine_reload; /* Seconds that reload takes */
    /* K: a second fire mode, one bullet per click, with the magazine's bullets
     * counted one by one (magazine x burst); 0 = the gun has none. */
    int single_magazine;
    float single_reload;  /* Seconds between those single shots */
    int pellets;          /* Bullets per shot, stacked vertically */
    float pellet_gap;     /* Window px between pellets */
    float pellet_spread;  /* How fast neighboring pellets part: px apart per px flown */
    float speed;          /* Window px per second */
    float range;          /* Window px a bullet flies before vanishing; 0 = until off screen */
    float armor_share;    /* Share of the target's armor that counts: 1 all, 0.5 half */
    unsigned tint;        /* 0xRRGGBB multiplied over the bullet sprite */
    const char *shot_sound;   /* Path under assets/sounds, or NULL */
    const char *cycle_sound;  /* Between shots: ramrod, pump, plasma recharge */
    const char *reload_sound; /* Replacing the magazine (including on a bench) */
    const char *empty_sound;  /* Trigger pulled with an empty magazine */
    const char *melee_sound;  /* Swing of this gun */
    int smoke_puffs;          /* Puffs of gun smoke per shot */
    float smoke_scale;        /* Size of that cloud: 1 is the revolver's */
    /* The character's sheet drawn while shooting this gun, instead of "shoot"
     * (assets/sprites/characters/<id>/<shoot_sheet>.png), or NULL. Same size
     * and template as shoot.png. */
    const char *shoot_sheet;
    /* With two guns taking turns: the sheet where the other one fires, or NULL. */
    const char *shoot_other_sheet;
    const char *walk_sheet;            /* Her own walk and jump with this gun, if any: its holsters */
    const char *jump_sheet;
    const char *melee_lit_sheet;       /* Its blow with the flashlight on: the beam swings with it */
    const char *legs_sheet;            /* Its walk with no arms, for the legs under another pose */
    const char *power_sheet;           /* Her ricochet with this gun, 8 frames of the shoot template... */
    const char *power_lit_sheet;       /* ...and with the flashlight on */
    const char *stand_sheet;           /* Stood still with this gun, one frame of the walk's size */
    const char *shoot_lit_sheet;       /* Both turns with the flashlight on: it stays up, lit */
    const char *shoot_other_lit_sheet;
    /* The character's sheet while putting a magazine in (needed with a
     * magazine), same size and template as shoot.png. */
    const char *reload_sheet;
    /* The character's sheet sat on a bench with this gun on the lap (its
     * reload there), instead of "sit", or NULL. Same size as sit.png. */
    const char *sit_sheet;
    /* The character's sheet for a blow with this gun, instead of "melee", or
     * NULL (tools/make_melee.py). Same frame size as shoot.png. */
    const char *melee_sheet;
    /* The character's sheet turning on the flashlight with this gun, its last
     * frame held while it stays on (tools/make_flashlight.py, make_swat.py), or
     * NULL. Same frame size as shoot.png. */
    const char *light_sheet;
    /* ...and walking with it on, the same frames as the walk (light_walk.png). */
    const char *light_walk_sheet;
    float light_time; /* Seconds turning it on: fetching and clipping it, or just the switch */
    float light_rows; /* Art rows over the ground to its lens, if not PLAYER_LIGHT_DY: clipped under the barrel */
} WeaponDef;

const WeaponDef *weapon_def(WeaponId id);

/* Damage per second of one target with this armor, at weapon level damage
 * base_damage, firing as fast as the reloads allow (the magazine's too):
 * for balancing. */
float weapon_dps(WeaponId id, float base_damage, float armor);

#endif
