#include "game/characters.h"

#include "config.h"
#include "game/progression.h"

const CharacterDef CHARACTERS[] = {
    {
        .id = "cowgirl", .name = "La Sheriff", /* Dolores Vega (docs/LORE.md) */
        .ability = ABILITY_CHEST_DROPS, .ability_name = "Botín",
        .ability_lines = {"Los zombis que vence", "sueltan cofres con XP."},
        .weapons = {WEAPON_REVOLVER}, .weapon_count = 1,
        .armor = 22.0f, .armor_per_level = 3.5f, /* Light on her feet: her guns are her strength */
        .power = POWER_DUAL_PISTOLS, .power_name = "Nv 3: duales, rebote F",
        .power_weapon = WEAPON_DUAL,
    },
    {
        .id = "swat", .name = "El SWAT",
        .walk_waist_row = 44,
        .ability = ABILITY_WEAPON_SWAP, .ability_name = "Arsenal",
        .ability_lines = {"Lleva rifle y escopeta.", "Q: cambiar · K: modo rifle."},
        .weapons = {WEAPON_RIFLE, WEAPON_SHOTGUN}, .weapon_count = 2,
        .armor = 34.0f, .armor_per_level = 6.5f, /* Plates and a helmet */
        .power = POWER_GRENADES, .power_name = "Nv 3: granada F",
        .placeholder_tint = 0x8fa0c0,
    },
    {
        .id = "hero", .name = "El Héroe",
        .ability = ABILITY_EXPERIMENTAL_WEAPON, .ability_name = "Prototipo",
        .ability_lines = {"Cañón de plasma que", "atraviesa la armadura."},
        .weapons = {WEAPON_PLASMA}, .weapon_count = 1,
        .armor = PLAYER_ARMOR, .armor_per_level = PLAYER_ARMOR_PER_LEVEL,
        .placeholder_tint = 0x70c8b0,
        .in_development = true,
    },
};

const int CHARACTER_COUNT = (int)(sizeof(CHARACTERS) / sizeof(CHARACTERS[0]));

int character_playable(int index)
{
    if (index >= 0 && index < CHARACTER_COUNT && !CHARACTERS[index].in_development)
        return index;
    for (int c = 0; c < CHARACTER_COUNT; c++)
        if (!CHARACTERS[c].in_development)
            return c;
    return 0;
}

int character_drops_chests(const CharacterDef *character)
{
    return character->ability == ABILITY_CHEST_DROPS;
}

WeaponId character_weapon(const CharacterDef *character, int slot, int level)
{
    if (slot == 0 && character->power == POWER_DUAL_PISTOLS && level >= POWER_LEVEL)
        return character->power_weapon;
    return character->weapons[slot];
}

bool character_throws(const CharacterDef *character, int level)
{
    return character->power == POWER_GRENADES && level >= POWER_LEVEL;
}

float character_armor(const CharacterDef *character, int armor_level)
{
    return level_armor(character->armor, character->armor_per_level, armor_level);
}
