#include "game/damage.h"

#include <math.h>

#include "config.h"

float damage_at_level(float base, int level)
{
    if (level < 1)
        level = 1;
    return base * (1.0f + DAMAGE_LEVEL_GROWTH * (float)(level - 1));
}

float weapon_damage(int level)
{
    return damage_at_level(DAMAGE_BASE, level);
}

int damage_after_armor(float damage, float armor)
{
    int points = (int)lroundf(damage_through_armor(damage, armor));
    return points < 1 ? 1 : points;
}

float damage_through_armor(float damage, float armor)
{
    if (armor < 0.0f)
        armor = 0.0f;
    return damage * ARMOR_SCALE / (ARMOR_SCALE + armor);
}
