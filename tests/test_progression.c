#include <math.h>

#include "config.h"
#include "game/damage.h"
#include "game/progression.h"
#include "game/stages.h"
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
    /* Same level on both sides: the fight lasts about the same at any level. */
    for (int level = 1; level <= 10; level++) {
        float to_kill = (float)level_health(ZOMBIE_RIOT.health, level) /
                        (float)damage_after_armor(weapon_damage(level),
                                                  level_armor(ZOMBIE_RIOT.armor, ZOMBIE_ARMOR_PER_LEVEL, level));
        float to_die = (float)level_health(PLAYER_HEALTH, level) /
                       (float)damage_after_armor(damage_at_level(ZOMBIE_ATTACK_BASE, level),
                                                 level_armor(PLAYER_ARMOR, PLAYER_ARMOR_PER_LEVEL, level));
        CHECK(ceilf(to_kill) >= 9 && ceilf(to_kill) <= 14);
        CHECK(ceilf(to_die) >= 8 && ceilf(to_die) <= 12);
    }
}

/* Plays the campaign once in order, beating every zombie and opening every
 * chest, and checks each fight is achievable but not trivial: bullets to
 * kill and claws to die within a band, and she gains about one level a stage. */
static void test_campaign_is_winnable_not_trivial(void)
{
    Progress p;
    progress_init(&p);
    for (int s = 0; s < STAGE_COUNT; s++) {
        const StageDef *stage = &STAGES[s];
        int start_level = p.level;
        CHECK(start_level >= stage->zombie_level - 1); /* Never more than one level behind */
        for (int k = 0; k < stage->zombies; k++) {
            int z = stage_zombie_level(stage, k);
            int shots = (int)ceilf((float)level_health(ZOMBIE_RIOT.health, z) /
                                   (float)damage_after_armor(progress_damage(&p),
                                                             level_armor(ZOMBIE_RIOT.armor, ZOMBIE_ARMOR_PER_LEVEL, z)));
            int claws = (int)ceilf((float)progress_max_health(&p) /
                                   (float)damage_after_armor(damage_at_level(ZOMBIE_ATTACK_BASE, z),
                                                             progress_armor(&p)));
            CHECK(shots >= 6 && shots <= 16);
            CHECK(claws >= 6 && claws <= 14);
            progress_add_xp(&p, kill_xp(z, p.level));
            if (stage_chest_after(stage, k)) {
                bool done = k == stage->zombies - 1;
                progress_add_xp(&p, chest_xp(p.level, stage->zombie_level, stage->complexity,
                                             (float)(k + 1) / (float)stage->zombies, done));
            }
        }
        CHECK(p.level - start_level >= 1 && p.level - start_level <= 2);
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
    CHECK(STAGE_COUNT == 5);
    /* Not linear: a breather and a jump. */
    CHECK(STAGES[2].zombie_level < 3 && STAGES[3].zombie_level > 3);
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
    RUN(test_stages_unlock_in_order);
    return TEST_EXIT();
}
