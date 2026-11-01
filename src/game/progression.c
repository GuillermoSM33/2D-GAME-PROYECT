#include "game/progression.h"

#include <math.h>

#include "config.h"
#include "game/damage.h"

static int clamp_level(int level)
{
    return level < 1 ? 1 : (level > MAX_LEVEL ? MAX_LEVEL : level);
}

int level_health(int base, int level)
{
    level = clamp_level(level);
    return (int)lroundf((float)base * (1.0f + DAMAGE_LEVEL_GROWTH * (float)(level - 1)));
}

float level_armor(float base, float per_level, int level)
{
    return base + per_level * (float)(clamp_level(level) - 1);
}

void progress_init(Progress *progress)
{
    progress->level = 1;
    progress->xp = 0;
    progress->weapon_level = 1;
    progress->armor_level = 1;
}

int xp_to_next(int level)
{
    return (int)lroundf(XP_CURVE_BASE * powf((float)clamp_level(level), XP_CURVE_EXP));
}

int progress_add_xp(Progress *progress, int xp)
{
    int gained = 0;
    progress->xp += xp > 0 ? xp : 0;
    while (progress->level < MAX_LEVEL && progress->xp >= xp_to_next(progress->level)) {
        progress->xp -= xp_to_next(progress->level);
        progress->level++;
        gained++;
    }
    if (progress->level >= MAX_LEVEL)
        progress->xp = 0;
    if (progress->weapon_level < progress->level)
        progress->weapon_level = progress->level;
    if (progress->armor_level < progress->level)
        progress->armor_level = progress->level;
    return gained;
}

int progress_max_health(const Progress *progress)
{
    return level_health(PLAYER_HEALTH, progress->level);
}

float progress_armor(const Progress *progress)
{
    return level_armor(PLAYER_ARMOR, PLAYER_ARMOR_PER_LEVEL, progress->armor_level);
}

float progress_damage(const Progress *progress)
{
    return weapon_damage(progress->weapon_level);
}

float xp_gap_factor(int enemy_level, int player_level)
{
    float f = 1.0f + XP_GAP_STEP * (float)(enemy_level - player_level);
    return fminf(XP_GAP_MAX, fmaxf(XP_GAP_MIN, f));
}

int kill_xp(int zombie_level, int player_level)
{
    return (int)lroundf(XP_PER_ZOMBIE_LEVEL * (float)zombie_level *
                        xp_gap_factor(zombie_level, player_level));
}

int chest_xp(int player_level, int stage_zombie_level, float complexity,
             float mission_progress, bool mission_done)
{
    float progress = fminf(1.0f, fmaxf(0.0f, mission_progress));
    float xp = (float)xp_to_next(player_level) * CHEST_XP_SHARE * complexity *
               (0.75f + 0.5f * progress) * xp_gap_factor(stage_zombie_level, player_level);
    if (mission_done)
        xp *= CHEST_MISSION_BONUS;
    int points = (int)lroundf(xp);
    return points < 1 ? 1 : points;
}
