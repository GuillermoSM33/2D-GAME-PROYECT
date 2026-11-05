#include <limits.h>
#include <math.h>
#include <string.h>
#include "config.h"
#include "game/mission.h"
#include "game/stage_run.h"
#include "test.h"

static void test_goals_use_each_routes_length_combat_and_difficulty(void)
{
    unsigned first = 0, last = 0;
    int previous_xp = 0, previous_gold = 0;
    for (int i = 0; i < STAGE_COUNT; i++) {
        MissionGoals g = mission_goals(i);
        CHECK(g.seconds[0] > g.seconds[1] && g.seconds[1] > g.seconds[2]);
        CHECK(g.seconds[2] > run_road_length(i) / PLAYER_WALK_SPEED);
        CHECK(g.health_percent[0] < g.health_percent[1] && g.health_percent[1] < g.health_percent[2]);
        CHECK(g.health_percent[0] > 0 && g.health_percent[2] <= 100);
        CHECK(mission_base_xp(i) > previous_xp && mission_base_gold(i) > previous_gold);
        previous_xp = mission_base_xp(i); previous_gold = mission_base_gold(i);
        if (!i) first = g.seconds[2];
        last = g.seconds[2];
        printf("    %s: 3=%u s/%d%%, 2=%u s/%d%%, 1=%u s/%d%%; base=%d XP/%d oro\n",
               STAGES[i].name, g.seconds[2], g.health_percent[2], g.seconds[1], g.health_percent[1],
               g.seconds[0], g.health_percent[0], previous_xp, previous_gold);
    }
    CHECK(last > first);
    CHECK(mission_goals(STAGE_COUNT - 1).health_percent[2] < mission_goals(0).health_percent[2]);
}

static void test_thresholds_are_inclusive_and_never_exceed_three_stars(void)
{
    for (int i = 0; i < STAGE_COUNT; i++) {
        MissionGoals g = mission_goals(i);
        for (int stars = 1; stars <= 3; stars++) {
            unsigned time = g.seconds[stars - 1] * SIMULATION_HZ;
            int health = g.health_percent[stars - 1] * 10;
            CHECK(mission_stars(i, time, health, 1000) == stars);
            CHECK(mission_stars(i, time, health - 1, 1000) < stars);
            CHECK(mission_stars(i, time + 1, health, 1000) < stars);
        }
        CHECK(mission_stars(i, 1, 1000, 1000) == 3);
        CHECK(mission_stars(i, 1, 0, 1000) == 0);
        CHECK(mission_stars(i, 1, 100, 0) == 0);
    }
}

static void test_records_and_star_rewards_are_paid_once_and_best_scores_do_not_fall(void)
{
    StageRecord record;
    stage_record_init(&record);
    MissionGoals goals = mission_goals(0);
    MissionReport result = {.ticks = goals.seconds[2] * SIMULATION_HZ};
    CHECK(mission_finish(&result, &record, 0, 100, 100));
    CHECK(result.stars == 3 && result.new_record && result.health_percent == 100);
    CHECK(result.star_xp == (int)lroundf(result.base_xp * .75f));
    CHECK(result.star_gold == (int)lroundf(result.base_gold * .75f));
    CHECK(result.record_xp == (int)lroundf(result.base_xp * .5f));
    CHECK(!mission_finish(&result, &record, 0, 100, 100));
    MissionReport equal = {.ticks = result.ticks};
    mission_finish(&equal, &record, 0, 100, 100);
    CHECK(!equal.new_record && equal.record_xp == 0 && equal.record_gold == 0);
    MissionReport slower = {.ticks = result.ticks + SIMULATION_HZ};
    mission_finish(&slower, &record, 0, 40, 100);
    CHECK(slower.stars < 3 && !slower.new_record && record.stars[0] == 3);
    CHECK(record.best_ticks[0] == result.ticks);
    MissionReport faster_injured = {.ticks = result.ticks - 1};
    mission_finish(&faster_injured, &record, 0, 99, 100);
    CHECK(faster_injured.new_record && faster_injured.record_xp == 0 && faster_injured.record_gold == 0);
    CHECK(record.best_ticks[0] == faster_injured.ticks);
    MissionReport faster_perfect = {.ticks = result.ticks - 2};
    mission_finish(&faster_perfect, &record, 0, 100, 100);
    CHECK(faster_perfect.new_record && faster_perfect.record_xp > 0 && faster_perfect.record_gold > 0);
}

static void test_clock_handles_fixed_and_variable_steps_and_saturates(void)
{
    MissionReport clock = {0};
    for (int i = 0; i < 120 * (int)SIMULATION_HZ; i++) mission_advance(&clock, FIXED_DT);
    CHECK(clock.ticks == 120 * SIMULATION_HZ);
    char text[24];
    mission_format_time(clock.ticks, text, sizeof(text));
    CHECK(strcmp(text, "02:00") == 0);
    mission_advance(&clock, 3600.0f);
    mission_format_time(clock.ticks, text, sizeof(text));
    CHECK(strcmp(text, "1:02:00") == 0);
    clock.claimed = true;
    unsigned stopped = clock.ticks;
    mission_advance(&clock, 10.0f);
    CHECK(clock.ticks == stopped);
    clock.claimed = false;
    clock.ticks = UINT_MAX - 1;
    mission_advance(&clock, 1.0f);
    CHECK(clock.ticks == UINT_MAX);
}

int main(void)
{
    RUN(test_goals_use_each_routes_length_combat_and_difficulty);
    RUN(test_thresholds_are_inclusive_and_never_exceed_three_stars);
    RUN(test_records_and_star_rewards_are_paid_once_and_best_scores_do_not_fall);
    RUN(test_clock_handles_fixed_and_variable_steps_and_saturates);
    return TEST_EXIT();
}
