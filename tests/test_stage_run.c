#include <math.h>

#include "config.h"
#include "game/hallucination.h"
#include "game/camera.h"
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
    player->health = player->max_health; /* The route is under test, not her: traps don't end it */
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
        /* Its length, and a little more where the road made room */
        CHECK(run.goal_x >= player.x + STAGES[s].length && run.goal_x <= player.x + STAGES[s].length * 1.35f);
        CHECK_NEAR(run.goal_x - player.x, run_road_length(s), 1e-2f);
        CHECK(player.x + run_road_length(s) < WORLD_WIDTH - VIEW_WIDTH);
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
    CHECK(run.defeated == 1 &&
          run.xp_gained == (int)lroundf((float)kill_xp(1, 1) * stage_xp_share(run.stage)));
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
    /* Every zombie leaves one, the last too, plus the mission's at the gate. */
    CHECK(chests == STAGES[0].zombies + 1);
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
    for (int b = 0; b < run.blasts; b++)
        CHECK(run.blast_kind[b] == BLAST_BARREL);
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
    CHECK(run_take_sound_events(&run) & RUN_SOUND_TRAP_BEAR);
    CHECK(run_take_sound_events(&run) == 0);
    float x = z->x;
    for (int i = 0; i < 60; i++)
        zombie_update(z, player.x, true, FIXED_DT);
    CHECK(z->x == x); /* Held */
}

static void test_trap_makes_her_bleed_and_limp(void)
{
    /* Her foot in a trap: a bite, then bleeding every BLEED_TICK (through any
     * armor) until she bandages it, and a limp at SLOW_MULT for SLOW_TIME. */
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 1, true);
    for (int k = 0; k < run.zombie_count; k++)
        run.zombies[k].x = run.goal_x + 1e4f;
    const Piece *trap = NULL;
    for (int i = 0; i < run.terrain.count && !trap; i++) {
        if (run.terrain.items[i].kind == TERRAIN_TRAP)
            trap = &run.terrain.items[i];
    }
    CHECK(trap != NULL);
    player.x = trap->x;
    player.armor = 1e6f; /* Bleeding goes through it anyway */
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(player.bleeding && player.slow_time > 0.0f);
    int health = player.health;
    InputState input;
    input_init(&input);
    for (int i = 0; i < (int)((SLOW_TIME + 2.0f) / FIXED_DT); i++)
        player_update(&player, &input, FIXED_DT);
    CHECK(player.health < health && player.bleeding && player.slow_time == 0.0f); /* Still open */
    bool binding[ACTION_COUNT] = {0};
    binding[ACTION_BANDAGE] = true;
    for (int i = 0; i < (int)(BANDAGE_TIME / FIXED_DT) + 2; i++) {
        input_update(&input, binding);
        player_update(&player, &input, FIXED_DT);
    }
    CHECK(!player.bleeding && player.bandage_shown > 0.0f); /* Bound: it stops */
    /* Limping covers less ground. */
    Player a, b;
    player_init(&a);
    player_init(&b);
    b.slow_time = SLOW_TIME;
    bool down[ACTION_COUNT] = {0};
    down[ACTION_RIGHT] = true;
    input_update(&input, down);
    for (int i = 0; i < 30; i++) {
        player_update(&a, &input, FIXED_DT);
        player_update(&b, &input, FIXED_DT);
    }
    CHECK(b.x - PLAYER_START_X < (a.x - PLAYER_START_X) * 0.7f);
}

static void test_more_coffins_by_night(void)
{
    /* Coffin spots shut their zombies in more often after dark. */
    int day = 0, day_spots = 0, night = 0, night_spots = 0;
    for (int s = 0; s < STAGE_COUNT; s++) {
        StageRun run;
        run_start(&run, s, 0.0f, true);
        int coffins = 0, places = 0;
        for (int i = 0; i < run.terrain.count; i++)
            coffins += run.terrain.items[i].kind == TERRAIN_COFFIN;
        for (int i = 0; i < STAGES[s].spot_count; i++)
            places += STAGES[s].spots[i].kind == SPOT_COFFINS ? STAGES[s].spots[i].count : 0;
        if (STAGES[s].theme->night) {
            night += coffins;
            night_spots += places;
        } else {
            day += coffins;
            day_spots += places;
        }
        for (int i = 0; i < run.terrain.count; i++) {
            if (run.terrain.items[i].kind == TERRAIN_COFFIN)
                CHECK(run.terrain.items[i].variant == (int)STAGES[s].theme->night);
        }
    }
    CHECK(day_spots > 0 && night_spots > 0);
    CHECK((float)night / (float)night_spots > (float)day / (float)day_spots);
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
    /* 1-2: no heat there (in the heat a fire only wears her out). */
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 1, true);
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

static void test_ricochet_bounces_lightly(void)
{
    /* Glancing off, it rises a little and comes back to its line, once, and is spent further on. */
    Bullets bullets;
    bullets_clear(&bullets);
    BulletSpec spec = {30.0f, 1000.0f, 0.0f, 0.0f, 0xffffff, 0.0f, true};
    bullets_fire(&bullets, 100.0f, 100.0f, 300.0f, 1, &spec);
    Bullet *b = &bullets.items[0];
    int body = 0;
    bullet_glance(&bullets, b, &body, 1.0f);
    CHECK(bullets.glances == 1 && b->burst && !b->spec.ricochet);
    float highest = b->y;
    for (int i = 0; i < 30; i++) {
        bullets_update(&bullets, FIXED_DT, 0.0f);
        highest = fminf(highest, b->y);
    }
    CHECK(highest < 300.0f && highest >= 300.0f - RICOCHET_BOUNCE - 0.01f);
    CHECK(fabsf(b->y - 300.0f) < 0.01f);
    for (int i = 0; i < 60 && b->active; i++)
        bullets_update(&bullets, FIXED_DT, 0.0f);
    CHECK(!b->active);
}

static void test_ricochet_breaks_through_crates(void)
{
    /* The ricochet goes through the first crate on to the next: one hit each. */
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 0, true);
    terrain_clear(&run.terrain);
    Piece *a = terrain_add(&run.terrain, TERRAIN_CRATE, 2000.0f);
    Piece *b = terrain_add(&run.terrain, TERRAIN_CRATE, 2300.0f);
    Bullets bullets;
    bullets_clear(&bullets);
    Effects effects;
    effects_clear(&effects);
    float muzzle = BASELINE - PLAYER_MUZZLE_DY * SPRITE_SCALE;
    BulletSpec spec = {30.0f, 1000.0f, 0.0f, 0.0f, 0xffffff, 0.0f, true};
    bullets_fire(&bullets, 1800.0f, 1800.0f, muzzle, 1, &spec);
    for (int i = 0; i < 60; i++) {
        bullets_update(&bullets, FIXED_DT, 1500.0f);
        run_bullets(&run, &bullets, &effects);
    }
    CHECK(a->hits == 1 && b->hits == 1);
    CHECK(!bullets.items[0].active);
}

static void test_shut_in_stay_hidden(void)
{
    /* A group in the open wakes; its zombie still in a coffin does not (it
     * would walk about unseen): it waits for its lid. */
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 0, true);
    run.zombie_count = 2;
    for (int k = 0; k < 2; k++) {
        zombie_spawn(&run.zombies[k], &ZOMBIE_RIOT, player.x + 500.0f + (float)k * 100.0f);
        run.zombies[k].awake = false;
        run.group_of[k] = 0;
    }
    run.zombies[1].hidden = true;
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(run.zombies[0].awake);
    CHECK(!run.zombies[1].awake && run.zombies[1].hidden);
}

static void test_a_bullet_wakes_a_sleeping_group(void)
{
    /* Too far to wake by walking up, but in range of her gun: the bullet hits
     * one, and all its group gets up; the next group sleeps on. */
    StageRun run;
    Player player;
    Progress progress;
    Effects effects;
    effects_clear(&effects);
    setup(&run, &player, &progress, 0, true);
    terrain_clear(&run.terrain);
    int k = -1;
    for (int i = 0; i + 1 < run.zombie_count && k < 0; i++)
        k = run.group_of[i] == run.group_of[i + 1] && run.ambush_x[i] <= 0.0f ? i : -1;
    CHECK(k >= 0);
    if (k < 0)
        return;
    Zombie *z = &run.zombies[k];
    float health = z->health;
    CHECK(!z->awake && !run.zombies[k + 1].awake && z->x - player.x > ROUTE_WAKE_DISTANCE);
    Bullets bullets;
    bullets_clear(&bullets);
    float chest = (float)BASELINE - PLAYER_MUZZLE_DY * SPRITE_SCALE;
    bullets_spawn(&bullets, z->x - 40.0f, z->x - 20.0f, chest, 1);
    bullets_update(&bullets, FIXED_DT, z->x - 500.0f);
    CHECK(run_bullets(&run, &bullets, &effects) == 1);
    CHECK(z->health < health && bullets_active_count(&bullets) == 0);
    CHECK(z->awake && run.zombies[k + 1].awake);
    for (int i = 0; i < run.zombie_count; i++)
        if (run.group_of[i] != run.group_of[k])
            CHECK(!run.zombies[i].awake);
    /* And one killed by that first shot still counts. */
    int before = run.defeated;
    z->health = 1.0f;
    bullets_clear(&bullets);
    bullets_spawn(&bullets, z->x - 40.0f, z->x - 20.0f, chest, 1);
    bullets_update(&bullets, FIXED_DT, z->x - 500.0f);
    run_bullets(&run, &bullets, &effects);
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(!zombie_alive(z) && run.defeated == before + 1);
}

static void test_a_blast_wakes_a_sleeping_group(void)
{
    /* A barrel going up beside a sleeping group: it hurts them and they wake. */
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 0, true);
    terrain_clear(&run.terrain);
    int k = -1;
    for (int i = 0; i + 1 < run.zombie_count && k < 0; i++)
        k = run.group_of[i] == run.group_of[i + 1] && run.ambush_x[i] <= 0.0f ? i : -1;
    CHECK(k >= 0);
    if (k < 0)
        return;
    for (int i = 0; i < k; i++)
        run.zombies[i].health = 0, run.zombies[i].state = ZOMBIE_DEAD;
    Zombie *z = &run.zombies[k];
    float health = z->health;
    CHECK(z->x - player.x > ROUTE_WAKE_DISTANCE && !z->awake);
    Piece *barrel = terrain_add(&run.terrain, TERRAIN_BARREL, z->x);
    barrel->blowing = true;
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(z->awake && run.zombies[k + 1].awake && z->health < health);
}

static void test_scenery_looks_like_traps_but_is_harmless(void)
{
    /* Trees and shrubs on every stage, drawn from the traps' own sheets. */
    for (int stage = 0; stage < STAGE_COUNT; stage++) {
        StageRun run;
        Player player;
        Progress progress;
        setup(&run, &player, &progress, stage, true);
        int decoys = 0;
        for (int i = 0; i < run.terrain.count; i++) {
            const Piece *p = &run.terrain.items[i];
            if (p->kind != TERRAIN_DEAD_TREE && p->kind != TERRAIN_SHRUB)
                continue;
            decoys++;
            TerrainKind trap = p->kind == TERRAIN_DEAD_TREE ? TERRAIN_NET : TERRAIN_SNARE;
            CHECK(terrain_sheet(p->kind) == terrain_sheet(trap) && terrain_frame(p) == 0);
        }
        /* The town has no trees nor shrubs (and no nets or snares to hide). */
        CHECK((STAGES[stage].theme->city ? decoys == 0 : decoys >= 3) && run.terrain.count < TERRAIN_MAX);
    }
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 0, true);
    terrain_clear(&run.terrain);
    run.zombie_count = 0;
    terrain_add(&run.terrain, TERRAIN_DEAD_TREE, player.x);
    terrain_add(&run.terrain, TERRAIN_SHRUB, player.x + 30.0f);
    run_update(&run, &player, &progress, FIXED_DT);
    run_place_player(&run, &player);
    CHECK(player.state != PLAYER_CAUGHT && player.max_x > player.x + 500.0f);
}

static void test_traps_keep_clear_of_big_things(void)
{
    /* No wire up against the wagon, nor any trap against a wall or a bench. */
    for (int stage = 0; stage < STAGE_COUNT; stage++) {
        StageRun run;
        Player player;
        Progress progress;
        setup(&run, &player, &progress, stage, true);
        const Terrain *t = &run.terrain;
        for (int a = 0; a < t->count; a++) {
            TerrainKind ka = t->items[a].kind;
            if (ka != TERRAIN_WIRE && ka != TERRAIN_TRAP && ka != TERRAIN_SPIKES && ka != TERRAIN_NET && ka != TERRAIN_SNARE)
                continue;
            for (int b = 0; b < t->count; b++) {
                TerrainKind kb = t->items[b].kind;
                if (kb != TERRAIN_SUPPLY && kb != TERRAIN_BENCH && kb != TERRAIN_WALL && kb != TERRAIN_BARRICADE)
                    continue;
                CHECK(fabsf(t->items[a].x - t->items[b].x) >= terrain_half_width(ka) + terrain_half_width(kb) + HAZARD_ROOM - 1.0f);
            }
            CHECK(t->items[a].x < run.goal_x - terrain_half_width(ka));
        }
    }
}

static void test_no_zombie_starts_on_a_trap(void)
{
    /* Nor a sign on its trap. */
    for (int stage = 0; stage < STAGE_COUNT; stage++) {
        StageRun run;
        Player player;
        Progress progress;
        setup(&run, &player, &progress, stage, true);
        for (int a = 0; a < run.terrain.count; a++) {
            const Piece *sign = &run.terrain.items[a];
            if (sign->kind != TERRAIN_SIGN)
                continue;
            for (int b = 0; b < run.terrain.count; b++) {
                const Piece *trap = &run.terrain.items[b];
                if ((int)trap->kind == sign->variant)
                    CHECK(fabsf(trap->x - sign->x) >= terrain_half_width(trap->kind) + terrain_half_width(TERRAIN_SIGN));
            }
        }
        for (int a = 0; a < run.terrain.count; a++) {
            TerrainKind kind = run.terrain.items[a].kind;
            if (kind != TERRAIN_WIRE && kind != TERRAIN_TRAP && kind != TERRAIN_SPIKES && kind != TERRAIN_NET && kind != TERRAIN_SNARE)
                continue;
            for (int k = 0; k < run.zombie_count; k++)
                if (run.ambush_x[k] <= 0.0f)
                    CHECK(fabsf(run.zombies[k].x - run.terrain.items[a].x) >=
                          terrain_half_width(kind) + zombie_body_half_width(&run.zombies[k]));
        }
    }
}

static void test_wire_bites_zombies_too(void)
{
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 0, true);
    terrain_clear(&run.terrain);
    run.zombie_count = 2;
    Zombie *in = &run.zombies[0], *out = &run.zombies[1];
    float x = player.x + 700.0f;
    zombie_spawn(in, &ZOMBIE_RIOT, x);
    zombie_spawn(out, &ZOMBIE_RIOT, x + 900.0f);
    float a = in->health + in->armor, b = out->health + out->armor;
    terrain_add(&run.terrain, TERRAIN_WIRE, x);
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(in->health + in->armor < a && out->health + out->armor == b);
    float once = in->health + in->armor; /* Not every tick: every so often */
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(in->health + in->armor == once);
    in->x = x;
    for (float t = 0.0f; t < WIRE_BITE_EVERY + 0.1f; t += FIXED_DT) {
        in->x = x;
        run_update(&run, &player, &progress, FIXED_DT);
    }
    CHECK(in->health + in->armor < once);
}

/* The arrows: only a sprung ambush still out of sight, on the side it comes from. */
static void test_ambush_arrows_point_to_it_until_it_is_in_sight(void)
{
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 0, true);
    int k = -1;
    for (int i = 0; i < run.zombie_count && k < 0; i++)
        k = run.ambush_x[i] > 0.0f ? i : -1;
    CHECK(k >= 0);
    for (int i = 0; i < k; i++) /* The groups before are beaten */
        run.zombies[i].health = 0, run.zombies[i].state = ZOMBIE_DEAD;
    bool left = true, right = true;
    run_incoming(&run, 0.0f, 1e6f, &left, &right);
    CHECK(!left && !right); /* Nothing sprung, nothing to point at */
    player.x = run.ambush_x[k] + 1.0f;
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(!run.zombies[k].hidden);
    float view = camera_left(player.x);
    run_incoming(&run, view, view + VIEW_WIDTH, &left, &right);
    CHECK(left); /* The first comes from behind, past the edge of the view */
    CHECK(run.zombies[k].x < view);
    for (int i = 0; i < run.zombie_count; i++)
        if (run.ambush_x[i] > 0.0f && i != k)
            run.zombies[i].hidden = true;
    run_incoming(&run, run.zombies[k].x - 1.0f, view + VIEW_WIDTH, &left, &right);
    CHECK(!left); /* In sight: the arrow goes */
    run.zombies[k].x = view - 100.0f;
    zombie_hit(&run.zombies[k], 1e6f);
    run_incoming(&run, view, view + VIEW_WIDTH, &left, &right);
    CHECK(!left); /* Dead: nothing coming */
}

static void test_ambush_walks_in(void)
{
    /* 1-1's ambush at its first wall: unseen until she gets there, then it
     * walks in from off screen, and she is held where it sprang. */
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 0, true);
    int k = -1;
    for (int i = 0; i < run.zombie_count && k < 0; i++)
        k = run.ambush_x[i] > 0.0f ? i : -1;
    CHECK(k >= 0);
    if (k < 0)
        return;
    CHECK(run.zombies[k].hidden && !run.zombies[k].awake);
    for (int i = 0; i < k; i++) /* The groups before are beaten */
        run.zombies[i].health = 0, run.zombies[i].state = ZOMBIE_DEAD;
    player.x = run.ambush_x[k] + 1.0f;
    run_update(&run, &player, &progress, FIXED_DT);
    const Zombie *z = &run.zombies[k];
    CHECK(run.ambushed && z->awake && !z->hidden);
    CHECK(fabsf(z->x - player.x) >= AMBUSH_BEHIND - 1.0f);
    CHECK(run.wall_x >= player.x);
}

static void test_ambush_lets_her_reach_the_wall_ahead(void)
{
    /* Every ambush before a wall, on every stage: while it holds her she can
     * walk up to the wall and light a charge on it, and blowing it neither
     * throws her back nor lets her past before the ambush is beaten. */
    for (int stage = 0; stage < STAGE_COUNT; stage++) {
        int checked = 0;
        for (int k = 0; k < RUN_MAX_ZOMBIES; k++) {
            StageRun run;
            Player player;
            Progress progress;
            setup(&run, &player, &progress, stage, true);
            if (k >= run.zombie_count)
                break;
            if (run.ambush_x[k] <= 0.0f || (k > 0 && run.group_of[k - 1] == run.group_of[k]))
                continue;
            if (run.siren_of[k] > 0) /* A horde comes with its siren, not at a spot */
                continue;
            Piece *wall = NULL;
            for (int i = 0; i < run.terrain.count; i++) {
                Piece *p = &run.terrain.items[i];
                if (p->kind == TERRAIN_WALL && p->x > run.ambush_x[k] && (wall == NULL || p->x < wall->x))
                    wall = p;
            }
            /* On the first route every ambush comes before a wall; on the
             * second, only those with a wall close ahead are this case. */
            CHECK(wall != NULL || stage >= 5);
            if (wall == NULL || (stage >= 5 && wall->x - run.ambush_x[k] > AMBUSH_WALL_SPAN))
                continue;
            for (int i = 0; i < k; i++) /* The groups before are beaten */
                run.zombies[i].health = 0, run.zombies[i].state = ZOMBIE_DEAD;
            player.x = run.ambush_x[k] + 1.0f;
            run_update(&run, &player, &progress, FIXED_DT);
            CHECK(run.ambushed && run.wall_x > 0.0f);
            run_place_player(&run, &player);
            player.x = player.max_x; /* As far as she may go */
            CHECK(terrain_wall_near(&run.terrain, player.x));
            float at_the_wall = player.x;
            wall->spent = true;
            run_update(&run, &player, &progress, FIXED_DT);
            run_place_player(&run, &player);
            CHECK(run.wall_x > 0.0f && player.max_x >= at_the_wall && player.max_x <= wall->x + 1.0f);
            checked++;
        }
        /* 1-1 to 1-5 all have an ambush */
        CHECK(checked > 0 || stage >= 5);
    }
}

static void test_charge_on_the_road(void)
{
    /* Away from walls and benches, E plants the charge at her feet: it goes
     * off like a barrel. */
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 0, true);
    run.dynamite = 1;
    CHECK(run_use(&run, &player) && run.dynamite == 0);
    run.zombie_count = 1;
    zombie_spawn(&run.zombies[0], &ZOMBIE_RIOT, player.x + 200.0f);
    run.zombies[0].awake = true;
    run.group_of[0] = 0;
    bool blew = false;
    for (int i = 0; i < (int)((CHARGE_FUSE + 0.2f) / FIXED_DT); i++) {
        run_update(&run, &player, &progress, FIXED_DT);
        blew |= run.blasts > 0;
        for (int b = 0; b < run.blasts; b++)
            CHECK(run.blast_kind[b] == BLAST_DYNAMITE);
    }
    CHECK(blew);
    CHECK(run.zombies[0].health < run.zombies[0].max_health);
}

static void test_blow_knocks_back_and_cuts_wire(void)
{
    /* Two blows cut the wire in front of her; a zombie in reach is hurt and
     * knocked back. */
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 0, true);
    terrain_clear(&run.terrain);
    Piece *wire = terrain_add(&run.terrain, TERRAIN_WIRE, player.x + 150.0f);
    run.zombie_count = 1;
    zombie_spawn(&run.zombies[0], &ZOMBIE_RIOT, player.x + 120.0f);
    float before = run.zombies[0].x;
    run_melee(&run, &player, &progress);
    CHECK(run.melee_hits == 2 && !wire->spent);
    CHECK(run.zombies[0].health < run.zombies[0].max_health && run.zombies[0].x > before);
    run_melee(&run, &player, &progress);
    CHECK(wire->spent);
}

static void test_blow_waits_and_hurts_less_than_a_shot(void)
{
    /* After a blow she waits MELEE_COOLDOWN before the next; and it hurts
     * less than a bullet would. */
    Player player;
    player_init(&player);
    InputState in = {0};
    CHECK(player_melee(&player));
    float t = 0.0f;
    while (player.state == PLAYER_MELEE && t < 5.0f) {
        player_update(&player, &in, FIXED_DT);
        t += FIXED_DT;
    }
    CHECK(fabsf(t - PLAYER_MELEE_FRAMES / PLAYER_MELEE_FPS) < 0.05f);
    CHECK(!player_melee(&player));
    for (float w = 0.0f; w < MELEE_COOLDOWN + FIXED_DT; w += FIXED_DT)
        player_update(&player, &in, FIXED_DT);
    CHECK(player_melee(&player));
    CHECK(MELEE_DAMAGE_MULT < 1.0f);
}

static void test_wire_tears_her(void)
{
    /* Walking into uncut wire: a bite, bleeding and a limp; over it in a
     * high jump, nothing. */
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 0, true);
    terrain_clear(&run.terrain);
    terrain_add(&run.terrain, TERRAIN_WIRE, player.x);
    player.jump.height = WIRE_TOP + 1.0f;
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(!run.wire_bit && player.health == player.max_health);
    player.jump.height = 0.0f;
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(run.wire_bit && player.health < player.max_health);
    CHECK(player.bleeding && player.slow_time > 0.0f);
}

static void test_barricade_kinds_hold_differently(void)
{
    /* Crates go in BARRICADE_STRIKES claws; the steel barrier takes twice. */
    Terrain t;
    terrain_clear(&t);
    Piece *crates = terrain_add(&t, TERRAIN_BARRICADE, 1000.0f);
    Piece *steel = terrain_add(&t, TERRAIN_BARRICADE, 3000.0f);
    steel->variant = 3;
    for (int i = 0; i < BARRICADE_STRIKES; i++) {
        terrain_claw(&t, 0);
        terrain_claw(&t, 1);
    }
    CHECK(crates->spent && !steel->spent);
    CHECK(terrain_frame(steel) == 3 * 3 + 1); /* Its kind's cracked frame */
    for (int i = 0; i < BARRICADE_STRIKES; i++)
        terrain_claw(&t, 1);
    CHECK(steel->spent);
}

static void test_net_hangs_her_till_she_cuts_free(void)
{
    /* Stepping on the net: hung up, no walking off; NET_BLOWS blows at the
     * ropes and she drops. */
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 0, true);
    terrain_clear(&run.terrain);
    terrain_add(&run.terrain, TERRAIN_NET, player.x + 20.0f);
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(player.state == PLAYER_CAUGHT && player.catch_kind == CATCH_NET);
    CHECK(run_take_sound_events(&run) & RUN_SOUND_TRAP_ROPE);
    InputState in = {0};
    in.down[ACTION_RIGHT] = true;
    float x = player.x;
    player_update(&player, &in, FIXED_DT);
    CHECK(player.x == x);
    for (int b = 1; b < NET_BLOWS; b++)
        CHECK(!player_struggle(&player));
    CHECK(player_struggle(&player));
    CHECK(player.state == PLAYER_CAUGHT && player.catch_kind != CATCH_NONE); /* Its swing plays first */
    CHECK(!player_struggle(&player)); /* Another blow meanwhile counts for nothing */
    const InputState none = {0};
    for (float t = 0.0f; t < CATCH_SHAKE_TIME - 2 * FIXED_DT; t += FIXED_DT) {
        player_update(&player, &none, FIXED_DT);
        CHECK(player.state == PLAYER_CAUGHT);
    }
    for (int i = 0; i < 4; i++)
        player_update(&player, &none, FIXED_DT);
    CHECK(player.state != PLAYER_CAUGHT && player.catch_kind == CATCH_NONE && player.jump.airborne);
}

static void test_snare_hangs_a_zombie(void)
{
    /* A zombie steps in the snare: it hangs a while, then drops and comes on. */
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 0, true);
    terrain_clear(&run.terrain);
    Piece *snare = terrain_add(&run.terrain, TERRAIN_SNARE, player.x + 400.0f);
    run.zombie_count = 1;
    zombie_spawn(&run.zombies[0], &ZOMBIE_RIOT, player.x + 410.0f);
    run.group_of[0] = 0;
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(snare->spent && run.zombies[0].catch_kind == CATCH_SNARE);
    for (int i = 0; i < (int)((SNARE_HOLD + 0.1f) / FIXED_DT); i++)
        run_update(&run, &player, &progress, FIXED_DT);
    CHECK(run.zombies[0].catch_kind == CATCH_NONE && run.zombies[0].caught <= 0.0f);
}

static void test_spikes_come_up(void)
{
    /* She steps on the plate: a moment later the spikes run her through
     * (bleeding); a jump over the plate clears them. */
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 0, true);
    terrain_clear(&run.terrain);
    terrain_add(&run.terrain, TERRAIN_SPIKES, player.x);
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(player.health == player.max_health);
    for (int i = 0; i < (int)((SPIKES_DELAY + 0.1f) / FIXED_DT); i++)
        run_update(&run, &player, &progress, FIXED_DT);
    CHECK(player.health < player.max_health && player.bleeding);
    CHECK(run_take_sound_events(&run) & RUN_SOUND_TRAP_SPIKES);
}

static void test_wet_dries_by_the_weather(void)
{
    /* Out of the river she is wet: dry in DRY_HOT in the heat, DRY_COLD in
     * the cold, DRY_FIRE by a campfire. */
    const struct { bool hot, cold, cozy; float time; } cases[] = {
        {true, false, false, DRY_HOT}, {false, false, false, DRY_MILD},
        {false, true, false, DRY_COLD}, {false, true, true, DRY_FIRE},
    };
    for (int c = 0; c < 4; c++) {
        Player player;
        player_init(&player);
        InputState in = {0};
        player.wading = true;
        player_update(&player, &in, FIXED_DT);
        CHECK(player.wet == 1.0f);
        player.wading = false;
        player.hot = cases[c].hot;
        player.cold = cases[c].cold;
        player.cozy = cases[c].cozy;
        CHECK(fabsf(player_dry_time(&player) - cases[c].time) < 1e-4f);
        for (float t = 0.0f; t < cases[c].time - 0.2f; t += FIXED_DT)
            player_update(&player, &in, FIXED_DT);
        CHECK(player.wet > 0.0f);
        for (float t = 0.0f; t < 0.4f; t += FIXED_DT)
            player_update(&player, &in, FIXED_DT);
        CHECK(player.wet == 0.0f);
    }
}

static void test_sits_though_still_walking(void)
{
    /* Walking up to the bench and pressing E with the way still held: she
     * sits (only a fresh press gets her up). */
    Player player;
    player_init(&player);
    InputState in = {0};
    in.down[ACTION_RIGHT] = true;
    CHECK(player_sit(&player, player.x, 0u));
    player_update(&player, &in, FIXED_DT);
    CHECK(player.state == PLAYER_SIT);
    in.pressed[ACTION_RIGHT] = true;
    player_update(&player, &in, FIXED_DT);
    CHECK(player.state != PLAYER_SIT);
}

static void test_heat_by_the_fire_wears_her_out(void)
{
    /* By a fire in the heat: slower after FATIGUE_SLOW, out cold at
     * FATIGUE_FAINT; away from it, it wears off. */
    Player player;
    player_init(&player);
    player.hot = player.cozy = true;
    InputState in = {0};
    for (float t = 0.0f; t < FATIGUE_SLOW + 0.1f; t += FIXED_DT)
        player_update(&player, &in, FIXED_DT);
    CHECK(player_alive(&player) && player.fatigue >= FATIGUE_SLOW);
    in.down[ACTION_RIGHT] = true;
    float x0 = player.x;
    player_update(&player, &in, FIXED_DT);
    float tired = player.x - x0;
    player.cozy = false;
    for (int i = 0; i < 400; i++)
        player_update(&player, &in, FIXED_DT);
    CHECK(player.fatigue == 0.0f);
    x0 = player.x;
    player_update(&player, &in, FIXED_DT);
    CHECK(fabsf(tired - (player.x - x0) * FATIGUE_PACE) < 0.01f);
    player.cozy = true;
    in.down[ACTION_RIGHT] = false;
    for (float t = 0.0f; t < FATIGUE_FAINT + 0.1f; t += FIXED_DT)
        player_update(&player, &in, FIXED_DT);
    CHECK(player.fainted && !player_alive(&player));
}

static void test_water_thirst_and_visions(void)
{
    /* U drinks a jug (not while bleeding: then it binds the wound), slowly
     * walking; thirst grows to hallucinations, a drink clears it. */
    Player player;
    player_init(&player);
    player.hot = true;
    player.water = 1;
    InputState in = {0};
    for (float t = 0.0f; t < HALLUCINATING / THIRST_HOT + 0.1f; t += FIXED_DT)
        player_update(&player, &in, FIXED_DT);
    CHECK(player_thirst_level(&player) == 3);
    player_bleed(&player, 0.5f);
    in.pressed[ACTION_BANDAGE] = in.down[ACTION_BANDAGE] = true;
    player_update(&player, &in, FIXED_DT);
    CHECK(player.drink_time == 0.0f && player.bandage > 0.0f); /* The wound first */
    player.bleeding = false;
    player_update(&player, &in, FIXED_DT);
    CHECK(player.drink_time > 0.0f);
    in.pressed[ACTION_BANDAGE] = in.down[ACTION_BANDAGE] = false;
    bool drank = false;
    for (float t = 0.0f; t < DRINK_TIME + 0.1f; t += FIXED_DT) {
        player_update(&player, &in, FIXED_DT);
        drank |= player.drank;
    }
    CHECK(drank && player.water == 0 && player.thirst < 1.0f && player.refreshed > 0.0f);

    /* A vision walks in and goes at a shot. */
    Hallucination h;
    hallucination_clear(&h);
    for (float t = 0.0f; t < PHANTOM_EVERY; t += FIXED_DT)
        hallucination_update(&h, true, 2000.0f, 1, 1500.0f, FIXED_DT);
    int k = -1;
    for (int i = 0; i < PHANTOMS_MAX; i++)
        k = h.phantoms[i].active ? i : k;
    CHECK(k >= 0);
    Bullets bullets;
    bullets_clear(&bullets);
    BulletSpec spec = {30.0f, 1000.0f, 0.0f, 1.0f, 0xffffff, 0.0f, false};
    float muzzle = BASELINE - PLAYER_MUZZLE_DY * SPRITE_SCALE;
    bullets_fire(&bullets, h.phantoms[k].x - 50.0f, h.phantoms[k].x - 50.0f, muzzle, 1, &spec);
    bullets_update(&bullets, 0.1f, h.phantoms[k].x - 300.0f);
    CHECK(hallucination_shoot(&h, &bullets) == 1 && h.phantoms[k].fading);
}

static void test_rivers_clear_of_buildings(void)
{
    /* No river runs under a building: 25 m from a wall's ruins or front. */
    for (int s = 0; s < STAGE_COUNT; s++) {
        StageRun run;
        Player player;
        Progress progress;
        setup(&run, &player, &progress, s, true);
        for (int i = 0; i < run.terrain.count; i++) {
            const Piece *river = &run.terrain.items[i];
            if (river->kind != TERRAIN_RIVER)
                continue;
            for (int j = 0; j < run.terrain.count; j++) {
                const Piece *wall = &run.terrain.items[j];
                if (wall->kind != TERRAIN_WALL)
                    continue;
                float half = (float)(FACADE_W > WALL_RUINS_W ? FACADE_W : WALL_RUINS_W) * SPRITE_SCALE / 2.0f;
                float gap = fabsf(river->x - wall->x) - half - terrain_half_width(TERRAIN_RIVER);
                CHECK(gap >= RIVER_CLEARANCE);
            }
        }
    }
}

static void test_river_slows_everyone(void)
{
    /* Wading a river with its current: she and the zombies go at RIVER_SLOW
     * times RIVER_WITH of their pace (the wind counts the same in and out of
     * it); a puddle only ripples. */
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 0, true);
    terrain_clear(&run.terrain);
    terrain_add(&run.terrain, TERRAIN_RIVER, player.x);
    Piece *puddle = terrain_add(&run.terrain, TERRAIN_PUDDLE, player.x + 2000.0f);
    InputState in = {0};
    in.down[ACTION_RIGHT] = true;
    run_place_player(&run, &player);
    CHECK(player.wading);
    float x0 = player.x;
    player_update(&player, &in, FIXED_DT);
    float wading = player.x - x0;
    player.x = puddle->x;
    run_place_player(&run, &player);
    CHECK(!player.wading);
    x0 = player.x;
    player_update(&player, &in, FIXED_DT);
    CHECK(fabsf(wading - (player.x - x0) * RIVER_SLOW * RIVER_WITH) < 0.01f);
    CHECK(player.current_feel == 0 && player.wind_feel == 1); /* 1-1 is windy, blowing her way */
    CHECK(terrain_splash(&run.terrain, puddle->x) && puddle->ripple > 0.0f);

    run.zombie_count = 1;
    zombie_spawn(&run.zombies[0], &ZOMBIE_RIOT, player.x - 2000.0f + 100.0f); /* In the river */
    run.zombies[0].just_spawned = false;
    run.zombies[0].rouse = 0.0f;
    run.group_of[0] = 0;
    float z0 = run.zombies[0].x;
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(run.zombies[0].wading);
    float pace = RIVER_SLOW * RIVER_WITH * WIND_WITH; /* Walking right to her */
    CHECK(fabsf(fabsf(run.zombies[0].x - z0) - ZOMBIE_SPEED * pace * FIXED_DT) < 0.01f);
}

static void test_wind_and_bandage(void)
{
    /* Into the wind she is slower than with it; holding U still stops the
     * bleeding after BANDAGE_TIME. */
    Player player;
    player_init(&player);
    player.wind = 1;
    InputState in = {0};
    in.down[ACTION_RIGHT] = true;
    float x0 = player.x;
    player_update(&player, &in, FIXED_DT);
    float with = player.x - x0;
    in.down[ACTION_RIGHT] = false;
    in.down[ACTION_LEFT] = true;
    for (int i = 0; i < 30; i++) /* Turned round and walking */
        player_update(&player, &in, FIXED_DT);
    x0 = player.x;
    player_update(&player, &in, FIXED_DT);
    CHECK(player.wind_feel == -1 && fabsf((x0 - player.x) * WIND_WITH - with * WIND_AGAINST) < 0.01f);

    player_bleed(&player, 1.0f);
    InputState still = {0};
    still.down[ACTION_BANDAGE] = true;
    bool stopped = false;
    for (float t = 0.0f; t < BANDAGE_TIME + 0.1f; t += FIXED_DT) {
        player_update(&player, &still, FIXED_DT);
        stopped |= player.bandaged;
    }
    CHECK(stopped && !player.bleeding);

    /* Walking while binding it: at BANDAGE_WALK of her pace. */
    player_bleed(&player, 1.0f);
    InputState walk = {0};
    walk.down[ACTION_LEFT] = true;
    float x0b = player.x;
    player_update(&player, &walk, FIXED_DT);
    float free_step = x0b - player.x;
    walk.down[ACTION_BANDAGE] = true;
    x0b = player.x;
    player_update(&player, &walk, FIXED_DT);
    CHECK(player.bandage > 0.0f && fabsf((x0b - player.x) - free_step * BANDAGE_WALK) < 0.01f);
}

static void test_grenade_and_glass_sounds_are_events(void)
{
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 0, true);
    terrain_clear(&run.terrain);
    for (int k = 0; k < run.zombie_count; k++)
        run.zombies[k].x = run.goal_x + 1e4f;
    float x = player.x + 1000.0f;
    run.grenades[0] = (Grenade){.active = true, .x = x, .height = 1.0f,
                               .vx = 80.0f, .vy = -300.0f, .fuse = 10.0f};
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(run_take_sound_events(&run) == RUN_SOUND_GRENADE_BOUNCE);
    CHECK(run_take_sound_events(&run) == 0);

    run.grenades[0].height = run.grenades[0].vy = run.grenades[0].vx = 0.0f;
    for (int i = 0; i < 30; i++) {
        run_update(&run, &player, &progress, FIXED_DT);
        CHECK(run_take_sound_events(&run) == 0); /* Settled, no endless rattle */
    }

    terrain_add(&run.terrain, TERRAIN_WALL, x + 100.0f);
    run.grenades[0].x = x + 100.0f - terrain_half_width(TERRAIN_WALL) - 2.0f;
    run.grenades[0].height = 30.0f;
    run.grenades[0].vx = 300.0f;
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(run.grenades[0].vx < 0.0f);
    CHECK(run_take_sound_events(&run) == RUN_SOUND_GRENADE_BOUNCE);
    run.grenades[0].active = false;

    terrain_clear(&run.terrain);
    terrain_add(&run.terrain, TERRAIN_BOTTLES, x);
    CHECK(terrain_melee(&run.terrain, x - 2.0f, x + 2.0f) == 1);
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(run.bottles_hit == 0); /* Reward only after the last bottle */
    CHECK(run_take_sound_events(&run) == RUN_SOUND_GLASS); /* First glass still sounds */
    CHECK(run_take_sound_events(&run) == 0);
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
        for (int b = 0; b < run.blasts; b++)
            CHECK(run.blast_kind[b] == BLAST_GRENADE);
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
    int buildings = 0, palisades = 0, trains = 0;
    for (int s = 0; s < STAGE_COUNT; s++) {
        StageRun run;
        run_start(&run, s, 0.0f, true);
        for (int i = 0; i < run.terrain.count; i++) {
            const Piece *p = &run.terrain.items[i];
            if (p->kind == TERRAIN_WALL) {
                buildings += p->variant > 0;
                palisades += p->variant == 0;
                if (s < 5) /* The first route: palisades and western fronts */
                    CHECK(p->variant >= 0 && p->variant <= FACADE_KINDS);
                else /* The town: only its fronts and the derailed trains */
                    CHECK(p->variant > FACADE_KINDS && p->variant <= FACADE_TRAIN);
                trains += p->variant == FACADE_TRAIN;
            }
        }
    }
    CHECK(buildings > 0 && palisades > 0);
    CHECK(trains == 3); /* All in the rail yard, 2-3 */
}

/* 2-1: walking past a patrol car sets its siren off. Its horde walks in from
 * both sides at once, a sleeping group near it wakes, and she is afraid
 * until the horde is down (and a little after). Shots then smash it quiet. */
static void test_siren_calls_a_horde(void)
{
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 5, true);
    int car = -1;
    for (int i = 0; i < run.terrain.count && car < 0; i++)
        if (run.terrain.items[i].kind == TERRAIN_SIREN)
            car = i;
    CHECK(car >= 0);
    if (car < 0)
        return;
    int horde = 0;
    for (int k = 0; k < run.zombie_count; k++) {
        if (run.siren_of[k] == car + 1) {
            horde++;
            CHECK(run.zombies[k].hidden);
        } else if (run.zombies[k].x < run.terrain.items[car].x) { /* The groups before are beaten */
            run.zombies[k].health = 0;
            run.zombies[k].state = ZOMBIE_DEAD;
        }
    }
    CHECK(horde == 4);
    player.x = run.terrain.items[car].x - SIREN_TRIP_RANGE - 50.0f;
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(!run.terrain.items[car].spent && !run.horde_came && player.fear == 0.0f);
    player.x = run.terrain.items[car].x - SIREN_TRIP_RANGE + 10.0f;
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(run.terrain.items[car].spent && terrain_siren_on(&run.terrain.items[car]));
    CHECK(run.siren_tripped && run.horde_came && !run.ambushed);
    CHECK(run.horde_left == horde && player.fear >= FEAR_TIME - 0.01f);
    int left = 0, right = 0;
    for (int k = 0; k < run.zombie_count; k++) {
        if (run.siren_of[k] != car + 1)
            continue;
        CHECK(!run.zombies[k].hidden && run.zombies[k].awake);
        left += run.zombies[k].x < player.x;
        right += run.zombies[k].x > player.x;
    }
    CHECK(left > 0 && right > 0); /* From both sides */
    CHECK(terrain_siren_loudness(&run.terrain, player.x) > 0.85f);
    CHECK(terrain_siren_loudness(&run.terrain, player.x + SIREN_HEAR_RANGE * 2.0f) == 0.0f);
    /* Blows on its light bar: quiet after SIREN_SILENCE_HITS. */
    float x = run.terrain.items[car].x;
    for (int i = 0; i < SIREN_SILENCE_HITS; i++)
        terrain_melee(&run.terrain, x - 10.0f, x + 10.0f);
    CHECK(run.terrain.items[car].damage == 1 && !terrain_siren_on(&run.terrain.items[car]));
    CHECK(terrain_frame(&run.terrain.items[car]) == 3);
    /* Fear holds while the horde stands, then wears off. */
    player.fear = 0.0f;
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(player.fear >= FEAR_LINGER - 0.01f);
    for (int k = 0; k < run.zombie_count; k++)
        run.zombies[k].health = 0, run.zombies[k].state = ZOMBIE_DEAD;
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(run.horde_left == 0);
}

/* A shot (or a blow) at a patrol car from afar sets it off too. */
static void test_a_shot_sets_a_siren_off(void)
{
    Terrain t;
    terrain_clear(&t);
    terrain_add(&t, TERRAIN_SIREN, 1000.0f);
    Bullets bullets;
    bullets_clear(&bullets);
    Bullet *b = &bullets.items[0];
    b->active = true;
    b->prev_x = 900.0f;
    b->x = 1010.0f;
    b->y = BASELINE - 60.0f;
    b->dir = 1;
    CHECK(terrain_shoot(&t, &bullets) == 1 && !b->active);
    CHECK(t.items[0].spent && t.events.siren_count == 1 && terrain_siren_on(&t.items[0]));
    terrain_update(&t, SIREN_TIME + 0.1f); /* Left alone, it winds down */
    CHECK(!terrain_siren_on(&t.items[0]) && t.items[0].damage == 0);
}

/* A burning drum lights the road; knocked over, its oil burns there. */
static void test_burning_drum_tips_into_fire(void)
{
    Terrain t;
    terrain_clear(&t);
    terrain_add(&t, TERRAIN_BURNER, 1000.0f);
    float xs[4];
    CHECK(terrain_smokes(&t, xs, 4) == 1);
    CHECK(terrain_melee(&t, 990.0f, 1010.0f) == 1);
    /* Over it goes: its fire flares (an event), its oil burns down the road. */
    CHECK(t.items[0].spent && terrain_frame(&t.items[0]) == 6 && t.events.burner_count == 1);
    CHECK(t.count == 3 && t.items[1].kind == TERRAIN_FIRE && !t.items[1].spent);
    terrain_update(&t, BURNER_TIP_TIME + 0.05f); /* On its side, still burning: light and smoke */
    CHECK(terrain_burner_burning(&t.items[0]) && terrain_frame(&t.items[0]) >= 8 && terrain_frame(&t.items[0]) <= 11);
    for (int i = 0; i < 40; i++)
        terrain_update(&t, 0.2f);
    CHECK(!terrain_burner_burning(&t.items[0]) && terrain_frame(&t.items[0]) == 12);
    /* A car across the road is as wide as a car; an outpost is searched once. */
    terrain_clear(&t);
    Piece *car = terrain_add(&t, TERRAIN_BARRICADE, 2000.0f);
    car->variant = BARRICADE_CAR;
    CHECK(terrain_piece_half_width(car) == CAR_WRECK_W * SPRITE_SCALE / 2.0f);
    float at = 2000.0f - terrain_piece_half_width(car) - PLAYER_BODY_HALF_WIDTH;
    CHECK(terrain_barricade_ahead(&t, at, 1) && terrain_vault_span(&t, at, 1) == CAR_WRECK_W * SPRITE_SCALE);
    terrain_add(&t, TERRAIN_OUTPOST, 4000.0f);
    CHECK(terrain_outpost_near(&t, 4000.0f + OUTPOST_RANGE - 1.0f) == 1 && terrain_outpost_near(&t, 3000.0f) < 0);
}

/* A car across the road: one long leap (N) lands her past it. An army
 * outpost: E searches it once. The town's supply point is a truck. */
static void test_car_vault_outpost_and_truck(void)
{
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 5, true);
    terrain_clear(&run.terrain);
    run.zombie_count = 0;
    Piece *car = terrain_add(&run.terrain, TERRAIN_BARRICADE, player.x + 600.0f);
    car->variant = BARRICADE_CAR;
    float half = terrain_piece_half_width(car);
    player.x = car->x - half - PLAYER_BODY_HALF_WIDTH;
    run_place_player(&run, &player);
    CHECK(player.max_x <= car->x - half - PLAYER_BODY_HALF_WIDTH + 1.0f); /* It stops her */
    CHECK(run_vault(&run, &player) && player.vaulting);
    InputState idle = {0};
    for (int i = 0; i < 90 && (player.vaulting || player.jump.airborne); i++) {
        run_place_player(&run, &player);
        player_update(&player, &idle, FIXED_DT);
    }
    CHECK(player.x > car->x + half + PLAYER_BODY_HALF_WIDTH - 1.0f && player.jump.height == 0.0f);

    terrain_add(&run.terrain, TERRAIN_OUTPOST, player.x + 100.0f);
    int dynamite = run.dynamite, water = player.water;
    player.health = player.max_health / 2;
    CHECK(run_search(&run, &player) && run.searched);
    CHECK(run.dynamite == dynamite + 1 && player.water == water + 1 && player.health > player.max_health / 2);
    CHECK(!run_search(&run, &player)); /* Once */

    setup(&run, &player, &progress, 5, true);
    int trucks = 0, cars = 0, outposts = 0;
    for (int i = 0; i < run.terrain.count; i++) {
        const Piece *p = &run.terrain.items[i];
        trucks += p->kind == TERRAIN_SUPPLY && p->variant == 1;
        cars += p->kind == TERRAIN_VEHICLE;
        outposts += p->kind == TERRAIN_OUTPOST;
    }
    CHECK(trucks == 1 && cars >= 5 && outposts == 1);
    setup(&run, &player, &progress, 0, true); /* The first route keeps its wagon and has no cars */
    for (int i = 0; i < run.terrain.count; i++) {
        const Piece *p = &run.terrain.items[i];
        CHECK(p->kind != TERRAIN_VEHICLE && (p->kind != TERRAIN_SUPPLY || p->variant == 0));
    }
}

/* A car or a motorcycle across the road takes bullets and, shot enough,
 * blows up like a barrel (so do those next to it); a hydrant shot bursts,
 * and its water hits and throws back whoever is near for HYDRANT_TIME. */
static void test_vehicles_blow_up_and_hydrants_burst(void)
{
    Terrain t;
    terrain_clear(&t);
    Piece *moto = terrain_add(&t, TERRAIN_BARRICADE, 1000.0f);
    moto->variant = terrain_moto_variant(1);
    Piece *car = terrain_add(&t, TERRAIN_BARRICADE, 1000.0f + BARREL_RADIUS);
    car->variant = terrain_car_variant(2);
    CHECK(terrain_moto_look(moto) == 1 && terrain_car_look(car) == 2 && terrain_car_look(moto) < 0);
    Bullets bullets;
    float xs[4];
    for (int shot = 0; shot < MOTO_BLOW_HITS; shot++) {
        CHECK(terrain_explosions(&t, xs, 4) == 0);
        bullets_clear(&bullets);
        Bullet *b = &bullets.items[0];
        b->active = true;
        b->prev_x = 700.0f;
        b->x = 900.0f;
        b->y = BASELINE - 60.0f;
        b->dir = 1;
        CHECK(terrain_shoot(&t, &bullets) == 1 && !b->active);
    }
    CHECK(terrain_explosions(&t, xs, 4) == 2); /* Its tank goes up, and the car's with it */
    CHECK(t.items[0].spent && t.items[1].spent && terrain_frame(&t.items[0]) % 3 == 2);

    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 5, true);
    terrain_clear(&run.terrain);
    run.zombie_count = 1;
    Piece *hydrant = terrain_add(&run.terrain, TERRAIN_HYDRANT, player.x + 400.0f);
    zombie_spawn(&run.zombies[0], &ZOMBIE_RIOT, hydrant->x + 60.0f);
    run.zombies[0].awake = true;
    float zombie_from = run.zombies[0].x;
    int health = run.zombies[0].health;
    terrain_melee(&run.terrain, hydrant->x - 5.0f, hydrant->x + 5.0f);
    CHECK(terrain_hydrant_jetting(hydrant));
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(run.hydrants_burst == 1 && run.zombies[0].health < health && run.zombies[0].x > zombie_from + HYDRANT_PUSH - 20.0f);
    CHECK(!run.soaked); /* She stood clear of it */
    player.x = hydrant->x - 60.0f;
    for (int i = 0; i < (int)(HYDRANT_TICK / FIXED_DT) + 2; i++)
        run_update(&run, &player, &progress, FIXED_DT);
    CHECK(player.health < player.max_health && player.wet == 1.0f);
    for (int i = 0; i < (int)(HYDRANT_TIME / FIXED_DT) + 5; i++)
        run_update(&run, &player, &progress, FIXED_DT);
    int puddles = 0;
    for (int i = 0; i < run.terrain.count; i++)
        puddles += run.terrain.items[i].kind == TERRAIN_PUDDLE;
    CHECK(!terrain_hydrant_jetting(&run.terrain.items[0]) && puddles == 1);
}

/* Afraid, she walks faster but a magazine goes in slower. */
static void test_fear_hurries_her_feet_and_slows_her_hands(void)
{
    Player calm, afraid;
    player_init(&calm);
    player_init(&afraid);
    afraid.fear = 5.0f;
    InputState input = {0};
    input.down[ACTION_RIGHT] = true;
    float from = calm.x;
    for (int i = 0; i < 30; i++) {
        player_update(&calm, &input, FIXED_DT);
        player_update(&afraid, &input, FIXED_DT);
    }
    CHECK(afraid.x - from > (calm.x - from) * 1.1f);
    CHECK(afraid.fear < 5.0f);
    Player a, b;
    player_init(&a);
    player_init(&b);
    b.fear = 30.0f;
    shot_set_magazine(&a.shot, 6, 1.0f, 0);
    shot_set_magazine(&b.shot, 6, 1.0f, 0);
    CHECK(shot_reload_now(&a.shot) && shot_reload_now(&b.shot));
    InputState idle = {0};
    a.state = b.state = PLAYER_SHOOT;
    for (int i = 0; i < (int)(1.1f / FIXED_DT); i++) {
        player_update(&a, &idle, FIXED_DT);
        player_update(&b, &idle, FIXED_DT);
    }
    CHECK(!shot_reloading(&a.shot) && shot_reloading(&b.shot));
}

static void test_impacts_accumulate_until_played(void)
{
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 0, true);
    terrain_clear(&run.terrain);
    run.zombie_count = 1;
    zombie_spawn(&run.zombies[0], &ZOMBIE_RIOT, player.x + 100.0f);
    run.zombies[0].awake = true;
    run_melee(&run, &player, &progress);
    CHECK(run.sound_events & RUN_SOUND_HIT_ARMOR);
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(run_take_sound_events(&run) == RUN_SOUND_HIT_ARMOR);
    CHECK(run_take_sound_events(&run) == 0);

    zombie_spawn(&run.zombies[0], &ZOMBIE_COMMON, player.x + 300.0f);
    run.zombies[0].awake = true;
    Bullets bullets;
    Effects effects;
    bullets_clear(&bullets);
    effects_clear(&effects);
    float y = BASELINE - PLAYER_MUZZLE_DY * SPRITE_SCALE;
    bullets_spawn(&bullets, player.x + 200.0f, player.x + 320.0f, y, 1);
    CHECK(run_bullets(&run, &bullets, &effects) == 1);
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(run_take_sound_events(&run) == RUN_SOUND_HIT_FLESH);
    CHECK(run_take_sound_events(&run) == 0);

    run.zombie_count = 0;
    terrain_add(&run.terrain, TERRAIN_BARRICADE, player.x + 100.0f)->variant = 3;
    run_melee(&run, &player, &progress);
    run_update(&run, &player, &progress, FIXED_DT);
    CHECK(run_take_sound_events(&run) == RUN_SOUND_HIT_METAL);
    CHECK(run_take_sound_events(&run) == 0);
}

static void test_dog_body_edge_receives_melee_and_blasts(void)
{
    for (int action = 0; action < 3; action++) {
        StageRun run;
        Player player;
        Progress progress;
        setup(&run, &player, &progress, 0, false);
        terrain_clear(&run.terrain);
        run.zombie_count = 1;
        Zombie *dog = &run.zombies[0];
        float blast_x = player.x + 1500.0f;
        float edge = action == 0 ? player.x + PLAYER_BODY_HALF_WIDTH + MELEE_REACH :
                     blast_x + (action == 1 ? BARREL_RADIUS : GRENADE_RADIUS);
        zombie_spawn(dog, zombie_stats(ZOMBIE_KIND_DOG, false),
                     edge + 22.0f * SPRITE_SCALE - 1.0f);
        if (action == 0) {
            run_melee(&run, &player, &progress);
        } else {
            if (action == 1)
                terrain_add(&run.terrain, TERRAIN_BARREL, blast_x)->blowing = true;
            else {
                run.grenades[0] = (Grenade){.active = true, .x = blast_x, .fuse = FIXED_DT / 2};
            }
            run_update(&run, &player, &progress, FIXED_DT);
            CHECK(run.blasts == 1);
        }
        CHECK(dog->health < dog->max_health);
        CHECK(run.sound_events & RUN_SOUND_HIT_FLESH);
    }
}

/* A blast hurts her only where its fireball is drawn: past that she is
 * untouched, even though zombies there would still be caught. */
static void test_blast_hurts_her_only_inside_the_fireball(void)
{
    for (int grenade = 0; grenade < 2; grenade++) {
        for (int inside = 0; inside < 2; inside++) {
            StageRun run;
            Player player;
            Progress progress;
            setup(&run, &player, &progress, 0, false);
            terrain_clear(&run.terrain);
            run.zombie_count = 0;
            float gap = PLAYER_BODY_HALF_WIDTH + BLAST_SELF_RADIUS + (inside ? -5.0f : 40.0f);
            float blast_x = player.x + gap;
            if (grenade)
                run.grenades[0] = (Grenade){.active = true, .x = blast_x, .fuse = FIXED_DT / 2};
            else
                terrain_add(&run.terrain, TERRAIN_BARREL, blast_x)->blowing = true;
            run_update(&run, &player, &progress, FIXED_DT);
            CHECK(run.blasts == 1);
            CHECK((player.health < player.max_health) == (inside == 1));
        }
    }
}

static void test_traps_leave_room_between_them(void)
{
    /* Every stage: no two traps closer than HAZARD_GAP, so she can land
     * between them and jump the next. */
    for (int s = 0; s < STAGE_COUNT; s++) {
        StageRun run;
        run_start(&run, s, 0.0f, true);
        for (int i = 0; i < run.terrain.count; i++)
            for (int j = 0; j < run.terrain.count; j++) {
                TerrainKind a = run.terrain.items[i].kind, b = run.terrain.items[j].kind;
                bool ha = a == TERRAIN_TRAP || a == TERRAIN_SPIKES || a == TERRAIN_NET ||
                          a == TERRAIN_SNARE || a == TERRAIN_WIRE;
                bool hb = b == TERRAIN_TRAP || b == TERRAIN_SPIKES || b == TERRAIN_NET ||
                          b == TERRAIN_SNARE || b == TERRAIN_WIRE;
                if (i != j && ha && hb)
                    CHECK(fabsf(run.terrain.items[i].x - run.terrain.items[j].x) >= HAZARD_GAP - 0.5f);
            }
    }
}

static void test_lightning_warns_then_strikes_and_burns(void)
{
    /* In the storm (1-5) the ground crackles near her, then the bolt comes
     * down there: standing on it, she is hurt and burned. Clear stages: never. */
    StageRun run;
    Player player;
    Progress progress;
    setup(&run, &player, &progress, 0, true);
    for (int i = 0; i < (int)(40.0f / FIXED_DT); i++) {
        run_update(&run, &player, &progress, FIXED_DT);
        CHECK(run.bolt_warn == 0.0f && !run.bolt_struck);
    }
    setup(&run, &player, &progress, 4, true);
    terrain_clear(&run.terrain);
    run.zombie_count = 0;
    int guard = 0;
    while (run.bolt_warn <= 0.0f && guard++ < (int)(30.0f / FIXED_DT))
        run_update(&run, &player, &progress, FIXED_DT);
    CHECK(run.bolt_warn > 0.0f && fabsf(run.bolt_x - player.x) <= LIGHTNING_NEAR &&
          fabsf(run.bolt_x - player.x) >= LIGHTNING_FAR);
    CHECK(LIGHTNING_FAR - LIGHTNING_RADIUS - PLAYER_BODY_HALF_WIDTH > 0.0f); /* Standing still, it misses her */
    player.x = run.bolt_x;
    int health = player.health;
    float warned = 0.0f;
    while (!run.bolt_struck && warned < 3.0f) {
        run_update(&run, &player, &progress, FIXED_DT);
        warned += FIXED_DT;
    }
    CHECK(run.bolt_struck && run.bolt_hit_her && warned >= LIGHTNING_WARN - 2.0f * FIXED_DT);
    CHECK(player.health < health && player.burned && !player.burn_bandaged);
    CHECK(player_needs_bandage(&player));
}

static void test_a_burn_needs_a_bandage_then_water(void)
{
    Player player;
    player_init(&player);
    player_burn(&player);
    player.water = 1;
    InputState in;
    input_init(&in);
    bool down[ACTION_COUNT] = {0};
    /* Burned she walks slower. */
    float x = player.x;
    down[ACTION_RIGHT] = true;
    for (int i = 0; i < 60; i++) {
        input_update(&in, down);
        player_update(&player, &in, FIXED_DT);
    }
    float burned_walk = player.x - x;
    CHECK(burned_walk < PLAYER_WALK_SPEED * 1.0f * 0.9f);
    down[ACTION_RIGHT] = false;
    /* A tap of U first: no drink while the burn wants its bandage. */
    down[ACTION_BANDAGE] = true;
    input_update(&in, down);
    player_update(&player, &in, FIXED_DT);
    CHECK(player.drink_time <= 0.0f && player.bandage > 0.0f);
    for (int i = 0; i < (int)(BANDAGE_TIME / FIXED_DT) + 2; i++) {
        input_update(&in, down);
        player_update(&player, &in, FIXED_DT);
    }
    CHECK(player.burned && player.burn_bandaged && !player_needs_bandage(&player));
    down[ACTION_BANDAGE] = false;
    input_update(&in, down);
    player_update(&player, &in, FIXED_DT);
    down[ACTION_BANDAGE] = true; /* Now U drinks */
    input_update(&in, down);
    player_update(&player, &in, FIXED_DT);
    down[ACTION_BANDAGE] = false;
    for (int i = 0; i < (int)(DRINK_TIME / FIXED_DT) + 2; i++) {
        input_update(&in, down);
        player_update(&player, &in, FIXED_DT);
    }
    CHECK(!player.burned && !player.burn_bandaged && player.water == 0);
}

int main(void)
{
    printf("test_stage_run\n");
    RUN(test_road_is_laid_out);
    RUN(test_traps_leave_room_between_them);
    RUN(test_lightning_warns_then_strikes_and_burns);
    RUN(test_a_burn_needs_a_bandage_then_water);
    RUN(test_group_wakes_and_holds_her);
    RUN(test_chest_then_gate_clears);
    RUN(test_without_the_ability_elites_and_mission_only);
    RUN(test_boss_is_stronger);
    RUN(test_zombies_queue_up);
    RUN(test_death_fails_run);
    RUN(test_supply_heals_once);
    RUN(test_barrel_blast);
    RUN(test_ricochet_glances_on);
    RUN(test_ricochet_bounces_lightly);
    RUN(test_ricochet_breaks_through_crates);
    RUN(test_shut_in_stay_hidden);
    RUN(test_a_bullet_wakes_a_sleeping_group);
    RUN(test_a_blast_wakes_a_sleeping_group);
    RUN(test_scenery_looks_like_traps_but_is_harmless);
    RUN(test_traps_keep_clear_of_big_things);
    RUN(test_wire_bites_zombies_too);
    RUN(test_no_zombie_starts_on_a_trap);
    RUN(test_ambush_walks_in);
    RUN(test_ambush_lets_her_reach_the_wall_ahead);
    RUN(test_charge_on_the_road);
    RUN(test_blow_knocks_back_and_cuts_wire);
    RUN(test_blow_waits_and_hurts_less_than_a_shot);
    RUN(test_wire_tears_her);
    RUN(test_barricade_kinds_hold_differently);
    RUN(test_net_hangs_her_till_she_cuts_free);
    RUN(test_snare_hangs_a_zombie);
    RUN(test_ambush_arrows_point_to_it_until_it_is_in_sight);
    RUN(test_spikes_come_up);
    RUN(test_wet_dries_by_the_weather);
    RUN(test_sits_though_still_walking);
    RUN(test_heat_by_the_fire_wears_her_out);
    RUN(test_water_thirst_and_visions);
    RUN(test_rivers_clear_of_buildings);
    RUN(test_river_slows_everyone);
    RUN(test_wind_and_bandage);
    RUN(test_grenade_arcs_and_blows);
    RUN(test_grenade_and_glass_sounds_are_events);
    RUN(test_some_walls_are_buildings);
    RUN(test_dynamite_opens_the_wall);
    RUN(test_coffin_ambush);
    RUN(test_trap_holds_a_zombie);
    RUN(test_trap_makes_her_bleed_and_limp);
    RUN(test_more_coffins_by_night);
    RUN(test_bench_heals_once_reloads_always);
    RUN(test_sit_reloads_each_gun);
    RUN(test_campfire_warms);
    RUN(test_dozing_off);
    RUN(test_impacts_accumulate_until_played);
    RUN(test_dog_body_edge_receives_melee_and_blasts);
    RUN(test_blast_hurts_her_only_inside_the_fireball);
    RUN(test_siren_calls_a_horde);
    RUN(test_a_shot_sets_a_siren_off);
    RUN(test_burning_drum_tips_into_fire);
    RUN(test_car_vault_outpost_and_truck);
    RUN(test_vehicles_blow_up_and_hydrants_burst);
    RUN(test_fear_hurries_her_feet_and_slows_her_hands);
    return TEST_EXIT();
}
