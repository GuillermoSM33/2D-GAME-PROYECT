#include "game/mission.h"

#include <limits.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>

#include "config.h"
#include "game/damage.h"
#include "game/progression.h"
#include "game/stage_run.h"
#include "game/weapons.h"

static unsigned round_quarter_minute(float seconds)
{
    return (unsigned)ceilf(seconds / 15.0f) * 15u;
}

MissionGoals mission_goals(int index)
{
    static MissionGoals known[16];
    if (index < 0 || index >= STAGE_COUNT) return (MissionGoals){0};
    if (index < 16 && known[index].seconds[2]) return known[index];
    const StageDef *stage = &STAGES[index];
    /* A walking route, actual profession/armor/health at the mission level,
     * revolver cadence, cylinder reloads, reaction time and the route's obstacles.
     * No sprint or particular character is required for three stars. */
    float budget = run_road_length(index) / PLAYER_WALK_SPEED;
    const WeaponDef *revolver = weapon_def(WEAPON_REVOLVER);
    float cadence = revolver->reload_time +
                    (PLAYER_SHOOT_FRAMES - PLAYER_SHOOT_FIRE_FRAME) / PLAYER_SHOOT_FPS +
                    revolver->magazine_reload / (float)revolver->magazine;
    for (int i = 0; i < stage->zombies; i++) {
        Zombie foe;
        zombie_spawn(&foe, stage_zombie_stats(stage, i), 0.0f);
        zombie_set_level(&foe, stage_zombie_level(stage, i));
        float damage = damage_through_armor(weapon_damage(stage->zombie_level), foe.armor);
        budget += ceilf((float)foe.max_health / fmaxf(1.0f, damage)) * cadence + 1.25f;
    }
    for (int i = 0; i < stage->spot_count; i++) {
        const StageSpot *spot = &stage->spots[i];
        switch (spot->kind) {
        case SPOT_WALL: case SPOT_TRAIN: budget += spot->count == 2 ? 3.0f : 5.0f; break;
        case SPOT_RIVER: budget += 7.0f; break;
        case SPOT_REST: budget += 10.0f; break;
        case SPOT_BARRICADE: budget += 2.0f; break;
        case SPOT_TRAPS: case SPOT_NET: case SPOT_SNARE: case SPOT_SPIKES: case SPOT_WIRE:
            budget += 2.0f * spot->count; break;
        default: break;
        }
    }
    unsigned par = round_quarter_minute(fmaxf(120.0f, budget * 1.15f));
    int tolerance = stage->complexity >= 1.5f ? 2 : stage->complexity >= 1.2f ? 1 : 0;
    MissionGoals goals = {
        .seconds = {round_quarter_minute(par * 1.75f), round_quarter_minute(par * 1.35f), par},
        .health_percent = {stage->complexity >= 1.35f ? 15 : 20, 60 - tolerance * 5, 90 - tolerance * 5},
    };
    if (index < 16) known[index] = goals;
    return goals;
}

void mission_advance(MissionReport *report, float seconds)
{
    if (!isfinite(seconds) || seconds <= 0.0f || report->claimed) return;
    double ticks = report->tick_fraction + (double)seconds * SIMULATION_HZ;
    if (ticks >= UINT_MAX - report->ticks) {
        report->ticks = UINT_MAX;
        report->tick_fraction = 0.0f;
        return;
    }
    unsigned whole = (unsigned)ticks;
    report->ticks += whole;
    report->tick_fraction = (float)(ticks - whole);
}

int mission_health_percent(int health, int max_health)
{
    if (health <= 0 || max_health <= 0) return 0;
    if (health >= max_health) return 100;
    return (int)((int64_t)health * 100 / max_health);
}

int mission_stars(int index, unsigned ticks, int health, int max_health)
{
    if (index < 0 || index >= STAGE_COUNT || health <= 0 || max_health <= 0) return 0;
    MissionGoals goals = mission_goals(index);
    int percent = mission_health_percent(health, max_health);
    for (int stars = 3; stars > 0; stars--)
        if ((uint64_t)ticks <= (uint64_t)goals.seconds[stars - 1] * SIMULATION_HZ &&
            percent >= goals.health_percent[stars - 1]) return stars;
    return 0;
}

int mission_base_xp(int index)
{
    if (index < 0 || index >= STAGE_COUNT) return 0;
    return (int)lroundf(xp_to_next(STAGES[index].zombie_level) * .25f * STAGES[index].complexity);
}

int mission_base_gold(int index)
{
    if (index < 0 || index >= STAGE_COUNT) return 0;
    return (int)lroundf(GOLD_MISSION * STAGES[index].complexity);
}

bool mission_finish(MissionReport *r, StageRecord *record, int index, int health, int max_health)
{
    if (r->claimed || index < 0 || index >= STAGE_COUNT || index >= 16) return false;
    r->claimed = true;
    r->stars = mission_stars(index, r->ticks, health, max_health);
    r->health_percent = mission_health_percent(health, max_health);
    r->new_record = record->best_ticks[index] == 0 || r->ticks < record->best_ticks[index];
    r->base_xp = mission_base_xp(index);
    r->base_gold = mission_base_gold(index);
    r->star_xp = (int)lroundf(r->base_xp * .25f * r->stars);
    r->star_gold = (int)lroundf(r->base_gold * .25f * r->stars);
    bool perfect = r->new_record && r->health_percent == 100;
    r->record_xp = perfect ? (int)lroundf(r->base_xp * .50f) : 0;
    r->record_gold = perfect ? (int)lroundf(r->base_gold * .50f) : 0;
    record->cleared[index] = true;
    if ((unsigned)r->stars > record->stars[index]) record->stars[index] = (unsigned)r->stars;
    if (r->new_record) record->best_ticks[index] = r->ticks;
    return true;
}

void mission_format_time(unsigned ticks, char *text, unsigned capacity)
{
    unsigned seconds = ticks / SIMULATION_HZ;
    if (seconds >= 3600)
        snprintf(text, capacity, "%u:%02u:%02u", seconds / 3600, seconds / 60 % 60, seconds % 60);
    else
        snprintf(text, capacity, "%02u:%02u", seconds / 60, seconds % 60);
}
