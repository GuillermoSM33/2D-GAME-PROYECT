#include "game/characters.h"

const CharacterDef CHARACTERS[] = {
    {
        .id = "cowgirl", .name = "La Vaquera",
        .ability = ABILITY_CHEST_DROPS, .ability_name = "Botín",
        .ability_lines = {"Los zombis que vence", "sueltan cofres con XP."},
        .weapons = {WEAPON_REVOLVER}, .weapon_count = 1,
    },
    {
        .id = "swat", .name = "El SWAT",
        .ability = ABILITY_WEAPON_SWAP, .ability_name = "Arsenal",
        .ability_lines = {"Lleva rifle y escopeta.", "Q o clic derecho: cambiar."},
        .weapons = {WEAPON_RIFLE, WEAPON_SHOTGUN}, .weapon_count = 2,
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
