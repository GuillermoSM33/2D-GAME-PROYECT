#ifndef GAME_PROGRESSION_H
#define GAME_PROGRESSION_H

#include <stdbool.h>

/* Levels, XP and the stats that grow with them, shared by the player and the
 * zombies so both sides scale by the same rules (constants in config.h). */

/* Health of something with base health at level 1, at this level. */
int level_health(int base, int level);

/* Armor of something with base armor at level 1, gaining per_level each level. */
float level_armor(float base, float per_level, int level);

/* The player's long-term progress, kept between stages. */
typedef struct {
    int level;
    int xp;           /* Toward the next level */
    int weapon_level; /* Sets her damage (damage.c) */
    int armor_level;  /* Sets her armor */
} Progress;

void progress_init(Progress *progress);

/* XP needed to go from this level to the next. */
int xp_to_next(int level);

/* Adds XP and levels up as many times as it reaches. For now the weapon and
 * the armor follow her level; rewards can raise them on their own later.
 * Returns the levels gained. */
int progress_add_xp(Progress *progress, int xp);

int progress_max_health(const Progress *progress);
float progress_armor(const Progress *progress);
float progress_damage(const Progress *progress);

/* XP multiplier for beating something of enemy_level at player_level. */
float xp_gap_factor(int enemy_level, int player_level);

int kill_xp(int zombie_level, int player_level);

/* A chest's XP. mission_progress is 0..1 (zombies beaten / zombies in the
 * mission); the mission's last chest (mission_done) gets the bonus. */
int chest_xp(int player_level, int stage_zombie_level, float complexity,
             float mission_progress, bool mission_done);

#endif
