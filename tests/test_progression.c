#include <math.h>

#include "config.h"
#include "game/damage.h"
#include "game/mission.h"
#include "game/progression.h"
#include "game/stages.h"
#include "game/stage_run.h"
#include "game/zombie.h"
#include "test.h"

static void test_xp_curve_grows(void)
{
    CHECK(xp_to_next(1) == (int)XP_CURVE_BASE);
    for (int level = 1; level < 20; level++)
        CHECK(xp_to_next(level + 1) > xp_to_next(level));
}

static void test_add_xp_levels_up_and_carries_over(void)
{
    Progress p;
    progress_init(&p);
    CHECK(progress_add_xp(&p, xp_to_next(1) - 1) == 0 && p.level == 1);
    CHECK(progress_add_xp(&p, 1 + 10) == 1 && p.level == 2 && p.xp == 10);
    /* Enough for two levels at once. */
    CHECK(progress_add_xp(&p, xp_to_next(2) + xp_to_next(3)) == 2 && p.level == 4);
    CHECK(p.weapon_level == 4 && p.armor_level == 4); /* For now they follow her level */
    CHECK(progress_max_health(&p) == level_health(PLAYER_HEALTH, 4));
}

static void test_gap_rewards_challenge(void)
{
    CHECK(kill_xp(3, 3) == (int)lroundf(XP_PER_ZOMBIE_LEVEL * 3));
    CHECK(kill_xp(4, 3) > kill_xp(3, 3) * 4 / 3); /* Above her: bonus */
    CHECK(kill_xp(2, 5) < kill_xp(2, 2));         /* Below her: less */
    CHECK(xp_gap_factor(1, 20) >= XP_GAP_MIN && xp_gap_factor(20, 1) <= XP_GAP_MAX);
    /* Chests grow with the mission and the last one doubles. */
    int first = chest_xp(2, 2, 1.0f, 0.25f, false), later = chest_xp(2, 2, 1.0f, 0.75f, false);
    CHECK(later > first);
    CHECK(chest_xp(2, 2, 1.0f, 1.0f, true) >= 2 * chest_xp(2, 2, 1.0f, 1.0f, false) - 1);
    CHECK(chest_xp(2, 2, 1.5f, 0.5f, false) > chest_xp(2, 2, 1.0f, 0.5f, false));
}

static void test_equal_levels_stay_balanced(void)
{
    /* Same level on both sides: the fight lasts about the same at any level,
     * about 7 shots to put down a riot zombie. */
    for (int level = 1; level <= 10; level++) {
        float to_kill = (float)level_health(ZOMBIE_RIOT.health, level) /
                        (float)damage_after_armor(weapon_damage(level),
                                                  level_armor(ZOMBIE_RIOT.armor, ZOMBIE_ARMOR_PER_LEVEL, level));
        float to_die = (float)level_health(PLAYER_HEALTH, level) /
                       (float)damage_after_armor(damage_at_level(ZOMBIE_ATTACK_BASE, level),
                                                 level_armor(PLAYER_ARMOR, PLAYER_ARMOR_PER_LEVEL, level));
        CHECK(ceilf(to_kill) >= 6 && ceilf(to_kill) <= 10);
        CHECK(ceilf(to_die) >= 8 && ceilf(to_die) <= 12);
    }
}

/* Plays the campaign once in order with the cowgirl, beating every zombie and
 * opening every chest (hers after each zombie, every elite's, the
 * mission's at the gate; kills and her chests at the stage's XP share), and checks each fight is achievable but not
 * trivial: bullets to kill and claws to die within a band (an elite takes
 * longer and hits harder), and she gains about one level a stage. */
static void simulate_campaign(bool best_result)
{
    Progress p;
    StageRecord record;
    stage_record_init(&record);
    progress_init(&p);
    for (int s = 0; s < STAGE_COUNT; s++) {
        const StageDef *stage = &STAGES[s];
        int start_level = p.level;
        CHECK(start_level >= stage->zombie_level - 1); /* Never more than one level behind */
        for (int k = 0; k < stage->zombies; k++) {
            const ZombieStats *stats = stage_zombie_stats(stage, k);
            bool elite = stats == &ZOMBIE_ELITE;
            int z = stage_zombie_level(stage, k);
            Zombie opponent;
            zombie_spawn(&opponent, stats, 0.0f);
            zombie_set_level(&opponent, z);
            int shots = (int)ceilf((float)opponent.max_health /
                                   damage_through_armor(progress_damage(&p), opponent.armor));
            int claws = (int)ceilf((float)progress_max_health(&p) /
                                   (float)damage_after_armor(damage_at_level(stats->attack_base, z),
                                                             progress_armor(&p)));
            if (s == 0) { /* The original tutorial's balance remains intact. */
                CHECK(stats == &ZOMBIE_RIOT);
                CHECK(shots >= 4 && shots <= 11);
                CHECK(claws >= 6 && claws <= 14);
            } else if (stats->runner) { /* Faster approach trades away health, not equipment. */
                CHECK(shots >= 1 && shots <= 11);
                CHECK(claws >= 5 && claws <= 22);
            } else {
                CHECK(shots >= (elite ? 5 : 2) && shots <= (elite ? 18 : 14));
                CHECK(claws >= (elite ? 4 : 5) && claws <= 22);
            }
            float share = stage_xp_share(stage);
            progress_add_xp(&p, (int)lroundf((float)kill_xp(z, p.level) * share));
            if (elite || stage_chest_after(stage, k)) {
                int xp = chest_xp(p.level, stage->zombie_level, stage->complexity,
                                  (float)(k + 1) / (float)stage->zombies, false);
                progress_add_xp(&p, elite ? xp : (int)lroundf((float)xp * share));
            }
        }
        MissionGoals goals = mission_goals(s);
        MissionReport report = {
            .ticks = best_result ? goals.seconds[2] * SIMULATION_HZ
                                 : goals.seconds[0] * SIMULATION_HZ + 1,
        };
        CHECK(mission_finish(&report, &record, s, best_result ? 100 : 20, 100));
        progress_add_xp(&p, report.base_xp + report.star_xp + report.record_xp);
        CHECK(p.level - start_level >= 1 && p.level - start_level <= 2);
    }
}

static void test_campaign_is_winnable_not_trivial(void)
{
    simulate_campaign(false); /* Base reward, without earning any stars. */
    simulate_campaign(true);  /* Maximum rewards: 3 stars and a perfect record. */
}

static void test_routes_add_up(void)
{
    /* Each stage's zombie count is its spots', and they fit the pools. */
    for (int s = 0; s < STAGE_COUNT; s++) {
        const StageDef *stage = &STAGES[s];
        int zombies = 0, terrain = 1; /* The gate */
        bool supply = false;
        for (int i = 0; i < stage->spot_count; i++) {
            const StageSpot *spot = &stage->spots[i];
            bool fighter = spot_has_zombies(spot->kind);
            zombies += fighter ? spot->count : 0;
            terrain += spot->kind == SPOT_SIREN ? 1 /* The car */
                       : fighter && spot->kind != SPOT_COFFINS ? 0 : spot->count;
            supply |= spot->kind == SPOT_SUPPLY;
            CHECK(spot->at > 0.0f && spot->at < 1.0f);
            if (i > 0)
                CHECK(spot->at >= stage->spots[i - 1].at); /* In route order */
        }
        CHECK(zombies == stage->zombies && zombies <= RUN_MAX_ZOMBIES);
        int charges = 0;
        for (int i = 0; i < stage->spot_count; i++) {
            const StageSpot *spot = &stage->spots[i];
            if (spot->kind == SPOT_DYNAMITE)
                charges += spot->count * DYNAMITE_PER_BOX;
            if (spot->kind == SPOT_SUPPLY)
                charges += stage_supply_dynamite(stage);
            if (spot_is_wall(spot->kind) && spot->count < 2) {
                CHECK(charges > 0); /* A box before it that no other wall used */
                charges--;
            }
        }
        CHECK(terrain <= TERRAIN_MAX && supply);
        CHECK(stage->length >= 4.0f * VIEW_WIDTH);
        CHECK(PLAYER_START_X + stage->length < WORLD_WIDTH - VIEW_WIDTH);
    }
}

static void test_stages_unlock_in_order(void)
{
    StageRecord record;
    stage_record_init(&record);
    CHECK(stage_unlocked(&record, 0));
    CHECK(!stage_unlocked(&record, 1));
    record.cleared[0] = true;
    CHECK(stage_unlocked(&record, 1) && !stage_unlocked(&record, 2));
    CHECK(STAGE_COUNT == 10); /* Two routes of five */
    /* The wagon's dynamite grows with the road: 1, 2 or 3. */
    CHECK(stage_supply_dynamite(&STAGES[0]) == 1 && stage_supply_dynamite(&STAGES[4]) == 3);
    CHECK(stage_supply_dynamite(&STAGES[5]) == 3);
    /* The second route: longer than the first's longest, each longer than the last. */
    for (int i = 5; i < STAGE_COUNT; i++)
        CHECK(STAGES[i].length > STAGES[4].length && STAGES[i].length > STAGES[i - 1].length &&
              STAGES[i].zombies > STAGES[4].zombies);
    /* Never easier than the stage before, and a jump at 1-4. */
    for (int i = 1; i < STAGE_COUNT; i++)
        CHECK(STAGES[i].zombie_level >= STAGES[i - 1].zombie_level);
    CHECK(STAGES[3].zombie_level > STAGES[2].zombie_level);
    CHECK(stage_zombie_level(&STAGES[4], STAGES[4].zombies - 1) == STAGES[4].zombie_level + 1);
}

int main(void)
{
    printf("test_progression\n");
    RUN(test_xp_curve_grows);
    RUN(test_add_xp_levels_up_and_carries_over);
    RUN(test_gap_rewards_challenge);
    RUN(test_equal_levels_stay_balanced);
    RUN(test_campaign_is_winnable_not_trivial);
    RUN(test_routes_add_up);
    RUN(test_stages_unlock_in_order);
    return TEST_EXIT();
}
