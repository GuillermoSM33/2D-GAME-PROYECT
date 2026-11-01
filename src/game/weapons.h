#ifndef GAME_WEAPONS_H
#define GAME_WEAPONS_H

/* The guns the characters carry (docs/CHARACTERS.md). Damage is a multiple of
 * the character's weapon level damage (progression.c), so every gun scales
 * with her or his level the same way. */
typedef enum {
    WEAPON_REVOLVER,  /* The cowgirl's hand cannon */
    WEAPON_RIFLE,     /* SWAT: fast, light */
    WEAPON_SHOTGUN,   /* SWAT: slow, three pellets, short reach */
    WEAPON_PLASMA,    /* Hero: experimental, goes through part of the armor */
    WEAPON_COUNT
} WeaponId;

typedef struct {
    const char *name;     /* Shown in the HUD */
    float damage_mult;    /* Per bullet, times the weapon level's damage */
    float reload_time;    /* Seconds from one shot to when the next can start */
    int pellets;          /* Bullets per shot, stacked vertically */
    float pellet_gap;     /* Window px between pellets */
    float speed;          /* Window px per second */
    float range;          /* Window px a bullet flies before vanishing; 0 = until off screen */
    float armor_share;    /* Share of the target's armor that counts: 1 all, 0.5 half */
    unsigned tint;        /* 0xRRGGBB multiplied over the bullet sprite */
    const char *shot_sound;   /* Path under assets/sounds, or NULL */
    const char *reload_sound;
} WeaponDef;

const WeaponDef *weapon_def(WeaponId id);

/* Damage per second of one target with this armor, at weapon level damage
 * base_damage, firing as fast as the reload allows: for balancing. */
float weapon_dps(WeaponId id, float base_damage, float armor);

#endif
