#include <math.h>

#include "config.h"
#include "game/stage_run.h"
#include "test.h"

static void setup(StageRun *run, Player *player, Progress *progress, int stage, bool drops)
{
    progress_init(progress);
    player_init(player);
    run_start(run, stage, player->x, drops);
}

/* One step of a player who walks right as far as she may, goes back for any
 * closed chest, kills on sight and hops over barricades. Returns chests that
 * appeared on this step. */
static int walk_and_kill(StageRun *run, Player *player, Progress *progress)
{
    int before = 0, after = 0;
    float chest_x = -1.0f;
    for (int c = 0; c < RUN_MAX_CHESTS; c++) {
        before += chest_present(&run->chests[c]);
        if (run->chests[c].state == CHEST_CLOSED && c != run->mission_chest)
            chest_x = run->chests[c].x; /* The gate's is on the way */
    }
    run_place_player(run, player);
    if (chest_x >= 0.0f) {
        player->x = chest_x;
    } else {
        float next = player->x + 6.0f;
        if (next > player->max_x && run_fight_left(run) == 0)
            next = player->max_x + 2.0f * terrain_half_width(TERRAIN_BARRICADE) + 2.0f * PLAYER_BODY_HALF_WIDTH;
        player->x = fminf(next, run->goal_x);
    }
    for (int k = 0; k < run->zombie_count; k++) {
        if (run->zombies[k].awake && zombie_alive(&run->zombies[k]))
            zombie_hit(&run->zombies[k], 1e6f);
    }
    run_update(run, player, progress, FIXED_DT);
    for (int c = 0; c < RUN_MAX_CHESTS; c++)
        after += chest_present(&run->chests[c]);
    return after > before ? after - before : 0;
}

static int play_through(StageRun *run, Player *player, Progress *progress, int *clears)
{
    int chests = 0;
    for (int guard = 0; guard < 60000 && run->phase == RUN_FIGHTING; guard++) {
        chests += walk_and_kill(run, player, progress);
        *clears += run->cleared_now;
    }
    return chests;
}

static void test_road_is_laid_out(void)
{
    for (int s = 0; s < STAGE_COUNT; s++) {
        StageRun run;
        Player player;
        Progress progress;
        setup(&run, &player, &progress, s, true);
        CHECK(run.zombie_count == STAGES[s].zombies);
        CHECK_NEAR(run.goal_x, player.x + STAGES[s].length, 1e-3f);
        CHECK_NEAR(terrain_goal_x(&run.terrain), run.goal_x, 1e-3f);
        for (int k = 0; k < run.zombie_count; k++) {
            const Zombie *z = &run.zombies[k];
            CHECK(!z->awake && zombie_alive(z));
            CHECK(z->level == stage_zombie_level(&STAGES[s], k));
            CHECK(z->stats == stage_zombie_stats(&STAGES[s], k));
            CHECK(z->x > player.x + ROUTE_WAKE_DISTANCE && z->x < run.goal_x);
            if (k > 0)
                CHECK(z->x > run.zombies[k - 1].x); /* In route order */
        }
    }
    /* The first elite comes in 1-3. */
    CHECK(stage_zombie_stats(&STAGES[0], STAGES[0].zombies - 1) == &ZOMBIE_RIOT);
    CHECK(stage_zombie_stats(&STAGES[2], STAGES[2].zombies - 1) == &ZOMBIE_ELITE);
}

static void test_group_wakes_and_holds_her(void)
{
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 0, true);
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(!run.zombies[0].awake && run.wall_x == 0.0f);

    player.x = run.zombies[0].x - ROUTE_WAKE_DISTANCE + 1.0f;
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(run.zombies[0].awake && run.zombies[0].just_spawned);
    CHECK(!run.zombies[1].awake); /* The next group sleeps on */
    CHECK(run_fight_left(&run) == 1);
    run_place_player(&run, &player);
    CHECK(run.wall_x > 0.0f && player.max_x <= run.wall_x);

    zombie_hit(&run.zombies[0], 1e6f);
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(run.defeated == 1 && run.xp_gained == kill_xp(1, 1));
    CHECK(run.group_beaten && run.wall_x == 0.0f && run_fight_left(&run) == 0);
}

static void test_chest_then_gate_clears(void)
{
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 0, true);
    int clears = 0;
    int chests = play_through(&run, &player, &progress, &clears);
    CHECK(run.phase == RUN_CLEARED && clears == 1);
    CHECK(run.defeated == STAGES[0].zombies);
    /* Every zombie but the last leaves one, plus the mission's at the gate. */
    CHECK(chests == STAGES[0].zombies);
    CHECK(run.mission_chest >= 0);
    CHECK(progress.level >= 2); /* 1-1 cleared takes her to level 2 */
}

static void test_without_the_ability_elites_and_mission_only(void)
{
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 2, false);
    int clears = 0;
    int chests = play_through(&run, &player, &progress, &clears);
    CHECK(run.phase == RUN_CLEARED && run.defeated == STAGES[2].zombies);
    CHECK(chests == 2); /* The elite's and the mission's */
}

static void test_boss_is_stronger(void)
{
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 4, true);
    int last = STAGES[4].zombies - 1;
    CHECK(run.zombies[0].level == STAGES[4].zombie_level);
    CHECK(run.zombies[last].level == STAGES[4].zombie_level + STAGES[4].boss_bonus);
}

static void test_zombies_queue_up(void)
{
    /* Two zombies from the same side: one stops a step behind the other. */
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 0, true);
    Zombie *a = &run.zombies[1], *b = &run.zombies[2]; /* 1-1's first pair */
    CHECK(run.group_of[1] == run.group_of[2]);
    player.x = b->x - ROUTE_WAKE_DISTANCE + 10.0f;
    for (int i = 0; i < 1200; i++) {
        player.health = player.max_health; /* Out of the way of their claws */
        run_update(&run, &player, &progress, FIXED_DT);
    }
    CHECK(a->awake && b->awake);
    CHECK(fabsf(fabsf(b->x - a->x) - ROUTE_QUEUE_STEP) < 8.0f);
}

static void test_death_fails_run(void)
{
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 0, true);
    player_hit(&player, 1e6f, 1);
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(run.phase == RUN_FAILED);
}

static void test_supply_heals_once(void)
{
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 0, true);
    float wagon = 0.0f;
    for (int i = 0; i < run.terrain.count; i++) {
        if (run.terrain.items[i].kind == TERRAIN_SUPPLY)
            wagon = run.terrain.items[i].x;
    }
    CHECK(wagon > 0.0f);
    for (int k = 0; k < run.zombie_count; k++)
        run.zombies[k].x = wagon + 1e5f; /* Out of the way */
    player.health = 10;
    player.x = wagon;
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(run.supply_taken);
    CHECK(player.health == 10 + (int)lroundf(player.max_health * SUPPLY_HEAL_SHARE));
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(!run.supply_taken);
}

static void test_barrel_blast(void)
{
    /* A shot barrel hurts the woken zombies next to it, and her if close. */
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 1, true); /* 1-2: two barrels inside a group */
    Piece *barrel = NULL;
    for (int i = 0; i < run.terrain.count && !barrel; i++) {
        if (run.terrain.items[i].kind == TERRAIN_BARREL)
            barrel = &run.terrain.items[i];
    }
    CHECK(barrel != NULL);
    Zombie *z = &run.zombies[1];
    z->x = barrel->x + 100.0f;
    zombie_wake(z);
    player.x = barrel->x - 600.0f;
    Bullets bullets;
    bullets_clear(&bullets);
    float muzzle = BASELINE - PLAYER_MUZZLE_DY * SPRITE_SCALE;
    bullets_spawn(&bullets, barrel->x - 100.0f, barrel->x - 100.0f, muzzle, 1);
    Effects effects;
    effects_clear(&effects);
    for (int i = 0; i < 20 && !barrel->spent; i++) {
        bullets_update(&bullets, FIXED_DT, barrel->x - 400.0f);
        run_bullets(&run, &bullets, &effects);
        run_update(&run, &player, &progress, FIXED_DT);
    }
    CHECK(barrel->spent && run.blasts >= 1);
    CHECK(z->health < z->max_health);
    CHECK(player.health == player.max_health); /* 600 px off: safe */
    int spent = 0;
    for (int i = 0; i < run.terrain.count; i++)
        spent += run.terrain.items[i].kind == TERRAIN_BARREL && run.terrain.items[i].spent;
    CHECK(spent == 2); /* Its neighbor went up with it */
}

static void test_dynamite_opens_the_wall(void)
{
    /* 1-1: the box before the wall, then E at the wall lights it; stepping
     * back, the blast opens the way. */
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 0, true);
    Piece *box = NULL, *wall = NULL;
    for (int i = 0; i < run.terrain.count; i++) {
        Piece *p = &run.terrain.items[i];
        if (p->kind == TERRAIN_DYNAMITE)
            box = p;
        if (p->kind == TERRAIN_WALL && wall == NULL)
            wall = p;
    }
    CHECK(box != NULL && wall != NULL && box->x < wall->x);
    for (int k = 0; k < run.zombie_count; k++)
        run.zombies[k].x = run.goal_x + 1e4f; /* Out of the way */
    CHECK(!run_use(&run, &player)); /* Nothing to light it with */
    player.x = box->x;
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(run.dynamite == 1 && run.dynamite_taken);
    player.x = wall->x - terrain_half_width(TERRAIN_WALL) - PLAYER_BODY_HALF_WIDTH;
    run_place_player(&run, &player);
    CHECK(player.max_x <= player.x + 0.01f); /* Blocked */
    CHECK(run_use(&run, &player) && run.dynamite == 0);
    player.x -= 2.0f * BARREL_RADIUS; /* Steps back */
    for (int i = 0; i < (int)(CHARGE_FUSE / FIXED_DT) + 5; i++)
        run_update(&run, &player, &progress, FIXED_DT);
    CHECK(!terrain_blocks(wall));
    CHECK(player.health == player.max_health); /* Far enough */
}

static void test_coffin_ambush(void)
{
    /* 1-3: the coffin's zombie stays shut in and out of reach until she
     * comes near; then it bursts out hunting. */
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 2, true);
    int k = -1;
    for (int i = 0; i < run.terrain.count && k < 0; i++) {
        if (run.terrain.items[i].kind == TERRAIN_COFFIN)
            k = run.terrain.items[i].zombie;
    }
    CHECK(k >= 0 && run.zombies[k].hidden);
    player.x = run.zombies[k].x - ROUTE_WAKE_DISTANCE; /* In view, not near */
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(run.zombies[k].hidden && !run.zombies[k].awake);
    player.x = run.zombies[k].x - COFFIN_RANGE + 1.0f;
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(!run.zombies[k].hidden && run.zombies[k].awake && run.coffins_burst == 1);
}

static void test_trap_holds_a_zombie(void)
{
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 1, true); /* 1-2: a trap in a group's path */
    Piece *trap = NULL;
    for (int i = 0; i < run.terrain.count && !trap; i++) {
        if (run.terrain.items[i].kind == TERRAIN_TRAP)
            trap = &run.terrain.items[i];
    }
    CHECK(trap != NULL);
    Zombie *z = &run.zombies[0];
    z->x = trap->x;
    zombie_wake(z);
    player.x = trap->x - 600.0f;
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(trap->spent && z->caught > 0.0f && z->health < z->max_health && run.traps_sprung == 1);
    float x = z->x;
    for (int i = 0; i < 60; i++)
        zombie_update(z, player.x, true, FIXED_DT);
    CHECK(z->x == x); /* Held */
}

static const Piece *find(const StageRun *run, TerrainKind kind)
{
    for (int i = 0; i < run->terrain.count; i++) {
        if (run->terrain.items[i].kind == kind)
            return &run->terrain.items[i];
    }
    return NULL;
}

static void test_bench_heals_once_reloads_always(void)
{
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 0, true);
    const Piece *bench = find(&run, TERRAIN_BENCH);
    CHECK(bench != NULL);
    for (int k = 0; k < run.zombie_count; k++)
        run.zombies[k].x = run.goal_x + 1e4f;
    player.x = bench->x + 40.0f;
    player.health = 50;
    CHECK(run_sit(&run, &player, 1u));
    CHECK(player.state == PLAYER_SIT && player.x == bench->x);
    CHECK(run.healed >= BENCH_HEAL_MIN && run.healed <= BENCH_HEAL_MAX && player.health == 50 + run.healed);
    /* The reload sat: done after the sitting down and the reload. */
    InputState input;
    input_init(&input);
    bool reloaded = false;
    for (int i = 0; i < (int)((SIT_DOWN_TIME + SIT_RELOAD_TIME) / FIXED_DT) + 5; i++) {
        player_update(&player, &input, FIXED_DT);
        reloaded |= player.sit_reloaded && player.sit_reloaded_gun == 0;
    }
    CHECK(reloaded && player.state == PLAYER_SIT);
    /* Moving gets her up; sitting again reloads but doesn't heal. */
    bool down[ACTION_COUNT] = {0};
    down[ACTION_RIGHT] = true;
    input_update(&input, down);
    player_update(&player, &input, FIXED_DT);
    CHECK(player.state != PLAYER_SIT);
    run.healed = 0;
    int health = player.health;
    player.x = bench->x;
    CHECK(run_sit(&run, &player, 1u) && run.healed == 0 && player.health == health);
}

static void test_sit_reloads_each_gun(void)
{
    /* Two guns short: one reload on her lap after the other, each told apart. */
    Player player;
    player_init(&player);
    CHECK(player_sit(&player, player.x, 0x3u) && player.sit_gun == 0);
    InputState input;
    input_init(&input);
    int done[2] = {0, 0};
    for (int i = 0; i < (int)((SIT_DOWN_TIME + 2.0f * SIT_RELOAD_TIME) / FIXED_DT) + 10; i++) {
        player_update(&player, &input, FIXED_DT);
        if (player.sit_reloaded)
            done[player.sit_reloaded_gun]++;
        if (player.sit_gun == 1)
            CHECK(done[0] == 1);
    }
    CHECK(done[0] == 1 && done[1] == 1 && player.sit_gun == -1 && player.state == PLAYER_SIT);
}

static void test_campfire_warms(void)
{
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 0, true);
    const Piece *fire = find(&run, TERRAIN_CAMPFIRE);
    CHECK(fire != NULL);
    for (int k = 0; k < run.zombie_count; k++)
        run.zombies[k].x = run.goal_x + 1e4f;
    player.x = fire->x;
    player.health = 50;
    int healed = 0;
    for (int i = 0; i < (int)(2.0f * CAMPFIRE_HEAL_TIME / FIXED_DT) + 2; i++) {
        run_update(&run, &player, &progress, FIXED_DT);
        healed += run.healed;
        run.healed = 0;
    }
    CHECK(healed == 3 && player.health == 53); /* 1.5 every 3 s: 3 in 6 s */
}

static void test_dozing_off(void)
{
    Player player;
    player_init(&player);
    CHECK(player_sit(&player, player.x, false));
    InputState input;
    input_init(&input);
    for (int i = 0; i < (int)((SIT_DOWN_TIME + SIT_DOZE_TIME) / FIXED_DT) + 30; i++)
        player_update(&player, &input, FIXED_DT);
    CHECK(player.anim.frame >= 8); /* Nodding */
}

static void test_ricochet_glances_on(void)
{
    /* A ricochet bullet hits the first zombie, then the one behind it for
     * RICOCHET_LOSS of the damage (the first one still stands). */
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 0, true);
    run.zombie_count = 2;
    for (int k = 0; k < 2; k++) {
        zombie_spawn(&run.zombies[k], &ZOMBIE_RIOT, 2000.0f + (float)k * 200.0f);
        run.zombies[k].awake = true;
    }
    Bullets bullets;
    bullets_clear(&bullets);
    Effects effects;
    effects_clear(&effects);
    float muzzle = BASELINE - PLAYER_MUZZLE_DY * SPRITE_SCALE;
    BulletSpec spec = {30.0f, 1000.0f, 0.0f, 0.0f, 0xffffff, 0.0f, true};
    bullets_fire(&bullets, 1800.0f, 1800.0f, muzzle, 1, &spec);
    for (int i = 0; i < 40; i++) {
        bullets_update(&bullets, FIXED_DT, 1500.0f);
        run_bullets(&run, &bullets, &effects);
    }
    float first = run.zombies[0].max_health - run.zombies[0].health;
    float second = run.zombies[1].max_health - run.zombies[1].health;
    CHECK(first > 0.0f && second > 0.0f);
    CHECK(fabsf(second - first * RICOCHET_LOSS) < 0.6f); /* No armor counted: damage as is */
    CHECK(!bullets.items[0].active);
}

static void test_grenade_arcs_and_blows(void)
{
    /* Thrown ahead, it goes off after its fuse: the zombie where it lands is
     * hurt, she (far behind) isn't, and no wall opens. */
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 0, true);
    for (int k = 0; k < run.zombie_count; k++)
        run.zombies[k].x = run.goal_x + 1e4f;
    run.zombie_count = 1;
    zombie_spawn(&run.zombies[0], &ZOMBIE_RIOT, player.x + 380.0f);
    run.zombies[0].awake = true;
    run_throw(&run, &player);
    CHECK(run.grenades[0].active);
    int blasts = 0, steps = 0;
    while (run.grenades[0].active && steps++ < 600) {
        run_update(&run, &player, &progress, FIXED_DT);
        blasts += run.blasts;
    }
    CHECK(blasts == 1 && steps >= (int)(GRENADE_FUSE / FIXED_DT) - 2);
    CHECK(run.zombies[0].health < run.zombies[0].max_health);
    CHECK(player.health == player.max_health);
    for (int i = 0; i < run.terrain.count; i++)
        CHECK(run.terrain.items[i].kind != TERRAIN_WALL || !run.terrain.items[i].spent);
}

static void test_some_walls_are_buildings(void)
{
    /* Along the campaign, some walls are a building's barred door. */
    int buildings = 0, palisades = 0;
    for (int s = 0; s < STAGE_COUNT; s++) {
        StageRun run;
        run_start(&run, s, 0.0f, true);
        for (int i = 0; i < run.terrain.count; i++) {
            const Piece *p = &run.terrain.items[i];
            if (p->kind == TERRAIN_WALL) {
                buildings += p->variant > 0;
                palisades += p->variant == 0;
                CHECK(p->variant >= 0 && p->variant <= FACADE_KINDS);
            }
        }
    }
    CHECK(buildings > 0 && palisades > 0);
}

int main(void)
{
    printf("test_stage_run\n");
    RUN(test_road_is_laid_out);
    RUN(test_group_wakes_and_holds_her);
    RUN(test_chest_then_gate_clears);
    RUN(test_without_the_ability_elites_and_mission_only);
    RUN(test_boss_is_stronger);
    RUN(test_zombies_queue_up);
    RUN(test_death_fails_run);
    RUN(test_supply_heals_once);
    RUN(test_barrel_blast);
    RUN(test_ricochet_glances_on);
    RUN(test_grenade_arcs_and_blows);
    RUN(test_some_walls_are_buildings);
    RUN(test_dynamite_opens_the_wall);
    RUN(test_coffin_ambush);
    RUN(test_trap_holds_a_zombie);
    RUN(test_bench_heals_once_reloads_always);
    RUN(test_sit_reloads_each_gun);
    RUN(test_campfire_warms);
    RUN(test_dozing_off);
    return TEST_EXIT();
}
