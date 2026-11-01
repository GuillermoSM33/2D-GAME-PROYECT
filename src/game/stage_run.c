#include "game/stage_run.h"

#include <string.h>

#include "config.h"

static void spawn_next(StageRun *run, Zombie *zombie, float player_x)
{
    float x = zombie_spawn_x(player_x);
    zombie_spawn(zombie, &ZOMBIE_RIOT, x);
    zombie_set_level(zombie, stage_zombie_level(run->stage, run->defeated));
    zombie->facing = player_x < x ? -1 : 1;
    run->phase = RUN_FIGHTING;
}

void run_start(StageRun *run, int stage_index, Zombie *zombie, float player_x, bool drops_chests)
{
    memset(run, 0, sizeof(*run));
    run->stage_index = stage_index;
    run->drops_chests = drops_chests;
    run->stage = &STAGES[stage_index];
    chest_clear(&run->chest);
    spawn_next(run, zombie, player_x);
}

static void give_xp(StageRun *run, Progress *progress, int xp)
{
    run->xp_gained += xp;
    run->levels_gained += progress_add_xp(progress, xp);
}

/* After a zombie's body is gone: its chest or the next zombie. The mission's
 * last zombie always leaves one, and opening it clears the stage. */
static void after_zombie(StageRun *run, const Zombie *zombie, const Progress *progress)
{
    int index = run->defeated - 1;
    bool done = run->defeated >= run->stage->zombies;
    if (done || (run->drops_chests && stage_chest_after(run->stage, index))) {
        float progress_share = (float)run->defeated / (float)run->stage->zombies;
        int xp = chest_xp(progress->level, run->stage->zombie_level, run->stage->complexity,
                          progress_share, done);
        chest_place(&run->chest, zombie->x, xp);
        run->phase = RUN_CHEST;
    } else {
        run->phase = RUN_NEXT;
        run->timer = ZOMBIE_NEXT_DELAY;
    }
}

void run_update(StageRun *run, Zombie *zombie, const Player *player, Progress *progress, float dt)
{
    run->xp_gained = run->levels_gained = 0;
    run->chest_opened = run->cleared_now = false;
    if (run->phase == RUN_CLEARED || run->phase == RUN_FAILED)
        return;
    if (!player_alive(player)) {
        run->phase = RUN_FAILED;
        return;
    }

    switch (run->phase) {
    case RUN_FIGHTING:
        if (zombie->just_died) {
            run->defeated++;
            give_xp(run, progress, kill_xp(zombie->level, progress->level));
        }
        if (zombie_gone(zombie))
            after_zombie(run, zombie, progress);
        break;
    case RUN_CHEST:
        chest_update(&run->chest, player->x, true, dt);
        if (run->chest.just_opened) {
            run->chest_opened = true;
            give_xp(run, progress, run->chest.reward_xp);
        }
        if (!chest_present(&run->chest)) {
            if (run->defeated >= run->stage->zombies) {
                run->phase = RUN_CLEARED;
                run->cleared_now = true;
            } else {
                run->phase = RUN_NEXT;
                run->timer = ZOMBIE_NEXT_DELAY;
            }
        }
        break;
    case RUN_NEXT:
        run->timer -= dt;
        if (run->timer <= 0.0f)
            spawn_next(run, zombie, player->x);
        break;
    case RUN_CLEARED:
    case RUN_FAILED:
        break;
    }
}
