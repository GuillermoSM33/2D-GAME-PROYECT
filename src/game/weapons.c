#include "game/weapons.h"

#include "config.h"
#include "game/damage.h"

/* Balanced to about the revolver's damage per second against the riot zombie
 * (tests/test_characters.c), each its own way: the rifle by bursts, the shotgun by
 * burst up close, the plasma by ignoring half the armor. */
static const WeaponDef WEAPONS[WEAPON_COUNT] = {
    [WEAPON_REVOLVER] = {
        .name = "Revólver", .damage_mult = 1.0f, .reload_time = REVOLVER_SHOT_DELAY,
        .magazine = REVOLVER_CAPACITY, .magazine_reload = RIFLE_MAGAZINE_RELOAD_TIME,
        .pellets = 1, .speed = BULLET_SPEED, .armor_share = 1.0f, .tint = 0xffffff,
        .shot_sound = "player/shot", .cycle_sound = "weapons/revolver_cycle", .reload_sound = "weapons/revolver_reload",
        .empty_sound = "player/empty", .melee_sound = "player/melee",
        .smoke_puffs = SMOKE_PUFFS_PER_SHOT, .smoke_scale = 1.0f,
        .reload_sheet = "reload",
        .melee_lit_sheet = "melee_lit", .power_sheet = "ricochet", .power_lit_sheet = "ricochet_lit",
        .light_sheet = "light", .light_walk_sheet = "light_walk", .light_time = 2.0f, .light_rows = 27.0f,
    },
    [WEAPON_RIFLE] = {
        .name = "Rifle", .damage_mult = 0.53f, .reload_time = 0.35f,
        .burst = 3, .burst_gap = 0.07f, .automatic = true, /* Light rounds, so many of them */
        .magazine = 5, .magazine_reload = RIFLE_MAGAZINE_RELOAD_TIME, /* 5 bursts, then a new magazine */
        .single_magazine = 15, .single_reload = 0.2f, /* K: the same 15 rounds one at a time */
        .pellets = 1, .speed = 1300.0f, .armor_share = 1.0f, .tint = 0xd8e0ff,
        .shot_sound = "weapons/rifle_shot", .reload_sound = "weapons/rifle_reload",
        .empty_sound = "weapons/rifle_empty", .melee_sound = "weapons/rifle_melee",
        .smoke_puffs = 3, .smoke_scale = 0.7f, /* A quick wisp: it fires often */
        .reload_sheet = "reload",
        .light_sheet = "light", .light_walk_sheet = "light_walk", .light_time = 1.0f,
    },
    [WEAPON_SHOTGUN] = {
        .name = "Escopeta", .damage_mult = 0.60f, .reload_time = 0.62f,
        .pellets = 3, .pellet_gap = 10.0f, .pellet_spread = 0.18f, /* A fan */ .speed = 1000.0f, .range = 380.0f, .armor_share = 1.0f,
        .tint = 0xffd8a8, .shot_sound = "weapons/shotgun_shot", .cycle_sound = "weapons/shotgun_cycle",
        .reload_sound = "weapons/shotgun_reload",
        .empty_sound = "weapons/shotgun_empty", .melee_sound = "weapons/shotgun_melee",
        .smoke_puffs = 10, .smoke_scale = 1.5f, /* A thick cloud */
        .magazine = 8, .magazine_reload = 1.1f, /* 8 shells in the tube */
        .shoot_sheet = "shoot_shotgun", .reload_sheet = "reload_shotgun", .sit_sheet = "sit_shotgun",
        .melee_sheet = "melee_shotgun",
        .light_sheet = "light_shotgun", .light_walk_sheet = "light_walk_shotgun", .light_time = 1.0f,
    },
    [WEAPON_DUAL] = {
        /* One after the other, each shot a whole turn (shoot.c): a bit more than
         * the single revolver, as a level's reward. Each cylinder is independent. */
        .name = "Revólveres duales", .damage_mult = 1.09f,
        .magazine = REVOLVER_CAPACITY, .magazine_reload = RIFLE_MAGAZINE_RELOAD_TIME,
        .reload_time = PLAYER_SHOOT_FRAMES / PLAYER_PISTON_FPS - 1.0f / PLAYER_SHOOT_FPS,
        .automatic = true, .piston = true, /* Hold it and they keep taking turns */
        .pellets = 1, .speed = BULLET_SPEED, .armor_share = 1.0f, .tint = 0xffffff,
        .shot_sound = "weapons/dual_shot", .cycle_sound = "weapons/revolver_cycle",
        .reload_sound = "weapons/revolver_reload", .reload_sheet = "reload_dual", .reload_other_sheet = "reload_dual_b",
        .reload_lower_sheet = "reload_dual_lower", .reload_other_lower_sheet = "reload_dual_b_lower",
        .empty_sound = "weapons/dual_empty", .melee_sound = "weapons/dual_melee",
        .smoke_puffs = SMOKE_PUFFS_PER_SHOT, .smoke_scale = 1.0f,
        .shoot_sheet = "shoot_dual", .shoot_other_sheet = "shoot_dual_b",
        .walk_sheet = "walk_dual", .jump_sheet = "jump_dual", .stand_sheet = "stand_dual", .legs_sheet = "legs_dual",
        .power_sheet = "ricochet_dual", .power_lit_sheet = "ricochet_dual_lit",
        .shoot_lit_sheet = "shoot_dual_lit", .shoot_other_lit_sheet = "shoot_dual_b_lit", .melee_sheet = "melee_dual",
        .melee_lit_sheet = "melee_dual_lit",
        .light_sheet = "light_dual", .light_walk_sheet = "light_walk_dual", .light_time = 2.6f, .light_rows = 27.0f,
    },
    [WEAPON_PLASMA] = {
        .name = "Cañón de plasma", .damage_mult = 1.3f, .reload_time = 0.62f,
        .pellets = 1, .speed = 700.0f, .armor_share = 0.6f, .tint = 0x80ffd8,
        .shot_sound = "weapons/plasma_shot", .cycle_sound = "weapons/plasma_reload",
        .reload_sound = "weapons/plasma_reload",
        .empty_sound = "weapons/plasma_empty", .melee_sound = "weapons/plasma_melee",
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
    if (w->magazine > 0) {
        /* On the final round the magazine reload starts after recoil; it
         * replaces that shot's normal action delay rather than adding to it. */
        float recoil = (PLAYER_SHOOT_RELOAD_FRAME - PLAYER_SHOOT_FIRE_FRAME) / PLAYER_SHOOT_FPS;
        cycle += (w->magazine_reload + recoil - w->reload_time) / (float)w->magazine;
    }
    return per_bullet * (float)(w->pellets * burst) / cycle;
}
