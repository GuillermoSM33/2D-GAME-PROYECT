#include "game/weapons.h"

#include "config.h"
#include "game/damage.h"

/* Balanced to about the revolver's damage per second against the riot zombie
 * (tests/test_characters.c), each its own way: the rifle by bursts, the shotgun by
 * burst up close, the plasma by ignoring half the armor. */
static const WeaponDef WEAPONS[WEAPON_COUNT] = {
    [WEAPON_REVOLVER] = {
        .name = "Cañón de mano", .damage_mult = 1.0f, .reload_time = PLAYER_SHOOT_RELOAD_TIME,
        .pellets = 1, .speed = BULLET_SPEED, .armor_share = 1.0f, .tint = 0xffffff,
        .shot_sound = "player/shot", .reload_sound = "player/reload",
        .smoke_puffs = SMOKE_PUFFS_PER_SHOT, .smoke_scale = 1.0f,
    },
    [WEAPON_RIFLE] = {
        .name = "Rifle", .damage_mult = 0.53f, .reload_time = 0.35f,
        .burst = 3, .burst_gap = 0.07f, .automatic = true, /* Light rounds, so many of them */
        .magazine = 5, .magazine_reload = 1.2f, /* 5 bursts, then a new magazine */
        .pellets = 1, .speed = 1300.0f, .armor_share = 1.0f, .tint = 0xd8e0ff,
        .shot_sound = "player/shot",
        .smoke_puffs = 3, .smoke_scale = 0.7f, /* A quick wisp: it fires often */
        .reload_sheet = "reload",
    },
    [WEAPON_SHOTGUN] = {
        .name = "Escopeta", .damage_mult = 0.60f, .reload_time = 0.62f,
        .pellets = 3, .pellet_gap = 10.0f, .pellet_spread = 0.18f, /* A fan */ .speed = 1000.0f, .range = 380.0f, .armor_share = 1.0f,
        .tint = 0xffd8a8, .shot_sound = "player/shot", .reload_sound = "player/reload",
        .smoke_puffs = 10, .smoke_scale = 1.5f, /* A thick cloud */
        .magazine = 8, .magazine_reload = 1.1f, /* 8 shells in the tube */
        .shoot_sheet = "shoot_shotgun", .reload_sheet = "reload_shotgun", .sit_sheet = "sit_shotgun",
    },
    [WEAPON_DUAL] = {
        /* Both fire at once, a bullet each a little apart: a bit more than the
         * single cannon, as a level's reward. */
        .name = "Pistolas duales", .damage_mult = 0.62f, .reload_time = PLAYER_SHOOT_RELOAD_TIME,
        .pellets = 2, .pellet_gap = 16.0f, .speed = BULLET_SPEED, .armor_share = 1.0f, .tint = 0xffffff,
        .shot_sound = "player/shot", .reload_sound = "player/reload",
        .smoke_puffs = SMOKE_PUFFS_PER_SHOT + 2, .smoke_scale = 1.2f,
        .shoot_sheet = "shoot_dual",
    },
    [WEAPON_PLASMA] = {
        .name = "Cañón de plasma", .damage_mult = 1.3f, .reload_time = 0.62f,
        .pellets = 1, .speed = 700.0f, .armor_share = 0.6f, .tint = 0x80ffd8,
        .shot_sound = "player/shot",
        .smoke_puffs = SMOKE_PUFFS_PER_SHOT, .smoke_scale = 1.0f,
    },
};

const WeaponDef *weapon_def(WeaponId id)
{
    return &WEAPONS[id];
}

float weapon_dps(WeaponId id, float base_damage, float armor)
{
    const WeaponDef *w = &WEAPONS[id];
    float per_bullet = damage_through_armor(base_damage * w->damage_mult, armor * w->armor_share);
    /* A follow-up shot fires one frame after the reload ends, which starts
     * after the burst's last bullet (shoot.c). */
    int burst = w->burst > 1 ? w->burst : 1;
    float cycle = (float)(burst - 1) * w->burst_gap + w->reload_time + 1.0f / PLAYER_SHOOT_FPS;
    if (w->magazine > 0) /* A whole magazine plus putting the next one in */
        cycle += w->magazine_reload / (float)w->magazine;
    return per_bullet * (float)(w->pellets * burst) / cycle;
}
