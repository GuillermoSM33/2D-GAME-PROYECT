#ifndef GAME_DAMAGE_H
#define GAME_DAMAGE_H

/* Damage of an attack with the given base at the given level, before armor:
 * base * (1 + DAMAGE_LEVEL_GROWTH * (level - 1)). Level 1 is the base. */
float damage_at_level(float base, int level);

/* The player's weapon: damage_at_level with DAMAGE_BASE. */
float weapon_damage(int level);

/* Health points removed from a target with the given armor: rounded, never
 * below 1, so every hit counts. */
int damage_after_armor(float damage, float armor);

#endif
