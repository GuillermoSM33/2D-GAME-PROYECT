#include "config.h"
#include "game/stage_run.h"
#include "test.h"

/* Runs the stage until the zombie's body is gone (it is killed right away). */
static void kill_and_wait(StageRun *run, Zombie *zombie, Player *player, Progress *progress)
{
    zombie_hit(zombie, 1e6f);
    for (int i = 0; i < 600 && run->phase == RUN_FIGHTING; i++) {
        zombie_update(zombie, player->x, true, FIXED_DT);
        run_update(run, zombie, player, progress, FIXED_DT);
        zombie->just_died = false;
    }
}

static void step(StageRun *run, Zombie *zombie, Player *player, Progress *progress, int steps)
{
    for (int i = 0; i < steps; i++) {
        zombie_update(zombie, player->x, true, FIXED_DT);
        run_update(run, zombie, player, progress, FIXED_DT);
    }
}

static void test_first_zombie_has_stage_level(void)
{
    StageRun run;
    Zombie zombie;
    run_start(&run, 3, &zombie, 1000.0f, true);
    CHECK(run.phase == RUN_FIGHTING);
    CHECK(zombie.level == STAGES[3].zombie_level);
    CHECK(zombie_alive(&zombie) && zombie.health == zombie.max_health);
}

static void test_kill_gives_xp_then_chest_then_next(void)
{
    StageRun run;
    Zombie zombie;
    Player player;
    Progress progress;
    progress_init(&progress);
    player_init(&player);
    run_start(&run, 0, &zombie, player.x, true);

    zombie_hit(&zombie, 1e6f);
    zombie_update(&zombie, player.x, true, FIXED_DT);
    run_update(&run, &zombie, &player, &progress, FIXED_DT);
    CHECK(run.defeated == 1 && run.xp_gained == kill_xp(1, 1));
    zombie.just_died = false;
    kill_and_wait(&run, &zombie, &player, &progress);
    CHECK(run.phase == RUN_CHEST);
    CHECK(run.chest.state == CHEST_CLOSED);

    /* Far away it stays closed; walking up opens it and pays once. */
    player.x = run.chest.x + 3.0f * CHEST_OPEN_RANGE;
    step(&run, &zombie, &player, &progress, 30);
    CHECK(run.chest.state == CHEST_CLOSED);
    int xp_before = progress.xp, reward = run.chest.reward_xp, paid = 0;
    player.x = run.chest.x + CHEST_OPEN_RANGE * 0.5f;
    for (int i = 0; i < 600 && run.phase == RUN_CHEST; i++) {
        zombie_update(&zombie, player.x, true, FIXED_DT);
        run_update(&run, &zombie, &player, &progress, FIXED_DT);
        paid += run.chest_opened;
    }
    CHECK(paid == 1 && reward > 0);
    CHECK(progress.xp == xp_before + reward || progress.level > 1);

    CHECK(run.phase == RUN_NEXT);
    step(&run, &zombie, &player, &progress, (int)(ZOMBIE_NEXT_DELAY / FIXED_DT) + 2);
    CHECK(run.phase == RUN_FIGHTING && zombie_alive(&zombie));
    CHECK(zombie.just_spawned);
}

static void test_last_chest_clears_stage(void)
{
    StageRun run;
    Zombie zombie;
    Player player;
    Progress progress;
    progress_init(&progress);
    player_init(&player);
    run_start(&run, 0, &zombie, player.x, true);
    int clears = 0;
    for (int guard = 0; guard < 20000 && run.phase != RUN_CLEARED; guard++) {
        if (run.phase == RUN_FIGHTING && zombie_alive(&zombie))
            zombie_hit(&zombie, 1e6f);
        if (run.phase == RUN_CHEST)
            player.x = run.chest.x;
        zombie_update(&zombie, player.x, true, FIXED_DT);
        run_update(&run, &zombie, &player, &progress, FIXED_DT);
        clears += run.cleared_now;
        zombie.just_died = false;
    }
    CHECK(run.phase == RUN_CLEARED && clears == 1);
    CHECK(run.defeated == STAGES[0].zombies);
    CHECK(progress.level >= 2); /* 1-1 cleared takes her to level 2 */
}

static void test_boss_is_stronger(void)
{
    StageRun run;
    Zombie zombie;
    Player player;
    Progress progress;
    progress_init(&progress);
    player_init(&player);
    run_start(&run, 4, &zombie, player.x, true);
    int levels[16] = {0}, seen = 0;
    for (int guard = 0; guard < 40000 && run.phase != RUN_CLEARED; guard++) {
        if (run.phase == RUN_FIGHTING && zombie_alive(&zombie)) {
            if (seen < 16 && zombie.just_spawned)
                levels[seen++] = zombie.level;
            zombie.just_spawned = false;
            zombie_hit(&zombie, 1e6f);
        }
        if (run.phase == RUN_CHEST)
            player.x = run.chest.x;
        zombie_update(&zombie, player.x, true, FIXED_DT);
        run_update(&run, &zombie, &player, &progress, FIXED_DT);
        zombie.just_died = false;
    }
    CHECK(seen == STAGES[4].zombies);
    CHECK(levels[0] == STAGES[4].zombie_level);
    CHECK(levels[seen - 1] == STAGES[4].zombie_level + STAGES[4].boss_bonus);
}

static void test_death_fails_run(void)
{
    StageRun run;
    Zombie zombie;
    Player player;
    Progress progress;
    progress_init(&progress);
    player_init(&player);
    run_start(&run, 0, &zombie, player.x, true);
    player_hit(&player, 1e6f, 1);
    run_update(&run, &zombie, &player, &progress, FIXED_DT);
    CHECK(run.phase == RUN_FAILED);
}

static void test_without_the_ability_only_the_last_chest(void)
{
    StageRun run;
    Zombie zombie;
    Player player;
    Progress progress;
    progress_init(&progress);
    player_init(&player);
    run_start(&run, 1, &zombie, player.x, false);
    int chests = 0;
    for (int guard = 0; guard < 40000 && run.phase != RUN_CLEARED; guard++) {
        if (run.phase == RUN_FIGHTING && zombie_alive(&zombie))
            zombie_hit(&zombie, 1e6f);
        if (run.phase == RUN_CHEST) {
            chests += run.chest.state == CHEST_CLOSED && run.chest.time == 0.0f;
            player.x = run.chest.x;
        }
        zombie_update(&zombie, player.x, true, FIXED_DT);
        run_update(&run, &zombie, &player, &progress, FIXED_DT);
        zombie.just_died = false;
    }
    CHECK(run.phase == RUN_CLEARED && run.defeated == STAGES[1].zombies);
    CHECK(chests == 1); /* Just the mission's */
}

int main(void)
{
    printf("test_stage_run\n");
    RUN(test_first_zombie_has_stage_level);
    RUN(test_kill_gives_xp_then_chest_then_next);
    RUN(test_last_chest_clears_stage);
    RUN(test_boss_is_stronger);
    RUN(test_death_fails_run);
    RUN(test_without_the_ability_only_the_last_chest);
    return TEST_EXIT();
}
