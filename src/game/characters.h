#ifndef GAME_CHARACTERS_H
#define GAME_CHARACTERS_H

#include <stdbool.h>

#include "game/weapons.h"

/* The playable characters (docs/CHARACTERS.md). They share the body template
 * (frame sizes, pivots, muzzle), the controls and the level rules; what sets
 * them apart is their art, their guns and their ability. */
typedef enum {
    ABILITY_CHEST_DROPS,          /* Every zombie she beats can leave a chest */
    ABILITY_WEAPON_SWAP,          /* Carries two guns and switches between them */
    ABILITY_EXPERIMENTAL_WEAPON   /* A gun that goes through part of the armor */
} Ability;

/* What a character gains at POWER_LEVEL. */
typedef enum {
    POWER_NONE,
    POWER_DUAL_PISTOLS, /* Its first gun becomes power_weapon; F: a ricochet shot */
    POWER_GRENADES      /* F throws a grenade (the "throw" sheet) */
} Power;

#define CHARACTER_MAX_WEAPONS 2
#define CHARACTER_ABILITY_LINES 3

typedef struct {
    const char *id;   /* Its folder: assets/sprites/characters/<id>/ */
    const char *name;
    Ability ability;
    const char *ability_name;
    const char *ability_lines[CHARACTER_ABILITY_LINES]; /* Short description, one line each */
    WeaponId weapons[CHARACTER_MAX_WEAPONS];
    int weapon_count;
    Power power;
    const char *power_name;  /* Shown on its card: what POWER_LEVEL brings */
    WeaponId power_weapon;   /* POWER_DUAL_PISTOLS: what weapons[0] becomes */
    /* Until its own sheets exist, the cowgirl's art in this one tint stands in. */
    unsigned placeholder_tint;
} CharacterDef;

extern const CharacterDef CHARACTERS[];
extern const int CHARACTER_COUNT;

/* Whether the zombies this character beats can leave chests (not only the
 * mission's last one). */
int character_drops_chests(const CharacterDef *character);

/* The gun in a slot at a level (its power may have changed it). */
WeaponId character_weapon(const CharacterDef *character, int slot, int level);

/* Whether it throws grenades at that level. */
bool character_throws(const CharacterDef *character, int level);

#endif
