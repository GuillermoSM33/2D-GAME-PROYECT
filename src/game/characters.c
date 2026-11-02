#include "game/characters.h"

#include "config.h"

const CharacterDef CHARACTERS[] = {
    {
        .id = "cowgirl", .name = "La Vaquera",
        .ability = ABILITY_CHEST_DROPS, .ability_name = "Botín",
        .ability_lines = {"Los zombis que vence", "sueltan cofres con XP."},
        .weapons = {WEAPON_REVOLVER}, .weapon_count = 1,
        .power = POWER_DUAL_PISTOLS, .power_name = "Nv 3: duales, rebote F",
        .power_weapon = WEAPON_DUAL,
    },
    {
        .id = "swat", .name = "El SWAT",
        .ability = ABILITY_WEAPON_SWAP, .ability_name = "Arsenal",
        .ability_lines = {"Lleva rifle y escopeta.", "Q o clic derecho: cambiar."},
        .weapons = {WEAPON_RIFLE, WEAPON_SHOTGUN}, .weapon_count = 2,
        .power = POWER_GRENADES, .power_name = "Nv 3: granada F",
        .placeholder_tint = 0x8fa0c0,
    },
    {
        .id = "hero", .name = "El Héroe",
        .ability = ABILITY_EXPERIMENTAL_WEAPON, .ability_name = "Prototipo",
        .ability_lines = {"Cañón de plasma que", "atraviesa la armadura."},
        .weapons = {WEAPON_PLASMA}, .weapon_count = 1,
        .placeholder_tint = 0x70c8b0,
    },
};

const int CHARACTER_COUNT = (int)(sizeof(CHARACTERS) / sizeof(CHARACTERS[0]));

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
