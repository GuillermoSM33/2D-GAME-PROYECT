#include "game/weapons.h"

#include "config.h"
#include "game/damage.h"

/* Balanced to about the revolver's damage per second against the riot zombie
 * (tests/test_weapons.c), each its own way: the rifle by rate, the shotgun by
 * burst up close, the plasma by ignoring half the armor. */
static const WeaponDef WEAPONS[WEAPON_COUNT] = {
    [WEAPON_REVOLVER] = {
        .name = "Cañón de mano", .damage_mult = 1.0f, .reload_time = PLAYER_SHOOT_RELOAD_TIME,
        .pellets = 1, .speed = BULLET_SPEED, .armor_share = 1.0f, .tint = 0xffffff,
        .shot_sound = "player/shot", .reload_sound = "player/reload",
    },
    [WEAPON_RIFLE] = {
        .name = "Rifle", .damage_mult = 0.45f, .reload_time = 0.14f,
        .pellets = 1, .speed = 1300.0f, .armor_share = 1.0f, .tint = 0xd8e0ff,
        .shot_sound = "player/shot",
    },
    [WEAPON_SHOTGUN] = {
        .name = "Escopeta", .damage_mult = 0.55f, .reload_time = 0.62f,
        .pellets = 3, .pellet_gap = 14.0f, .speed = 1000.0f, .range = 380.0f, .armor_share = 1.0f,
        .tint = 0xffd8a8, .shot_sound = "player/shot", .reload_sound = "player/reload",
    },
    [WEAPON_PLASMA] = {
        .name = "Cañón de plasma", .damage_mult = 1.1f, .reload_time = 0.62f,
        .pellets = 1, .speed = 700.0f, .armor_share = 0.4f, .tint = 0x80ffd8,
        .shot_sound = "player/shot",
    },
};

const WeaponDef *weapon_def(WeaponId id)
{
    return &WEAPONS[id];
}

float weapon_dps(WeaponId id, float base_damage, float armor)
{
    const WeaponDef *w = &WEAPONS[id];
    float per_bullet = (float)damage_after_armor(base_damage * w->damage_mult, armor * w->armor_share);
    /* A follow-up shot fires one frame after the reload ends (shoot.c). */
    float cycle = w->reload_time + 1.0f / PLAYER_SHOOT_FPS;
    return per_bullet * (float)w->pellets / cycle;
}
