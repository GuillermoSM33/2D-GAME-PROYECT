#include "config.h"
#include "game/player.h"
#include "game/terrain.h"
#include "game/zombie.h"
#include "test.h"

static void test_barricade_blocks_below_its_top(void)
{
    Terrain t;
    terrain_clear(&t);
    terrain_add(&t, TERRAIN_BARRICADE, 1000.0f);
    float reach = terrain_half_width(TERRAIN_BARRICADE) + PLAYER_BODY_HALF_WIDTH;
    float min_x = -1e9f, max_x = 1e9f;
    terrain_bounds(&t, 700.0f, 0.0f, &min_x, &max_x);
    CHECK_NEAR(max_x, 1000.0f - reach, 1e-3f);
    min_x = -1e9f, max_x = 1e9f;
    terrain_bounds(&t, 1300.0f, 0.0f, &min_x, &max_x);
    CHECK_NEAR(min_x, 1000.0f + reach, 1e-3f);
    /* Above it (a jump), nothing stops her. */
    min_x = -1e9f, max_x = 1e9f;
    terrain_bounds(&t, 700.0f, BARRICADE_TOP + 1.0f, &min_x, &max_x);
    CHECK(max_x == 1e9f);
    CHECK_NEAR(terrain_floor(&t, 1000.0f), BARRICADE_TOP, 1e-6f);
    CHECK(terrain_floor(&t, 700.0f) == 0.0f);
}

static void test_zombies_claw_through(void)
{
    Terrain t;
    terrain_clear(&t);
    terrain_add(&t, TERRAIN_BARRICADE, 1000.0f);
    int index;
    float target = terrain_zombie_target(&t, 1500.0f, 600.0f, &index);
    CHECK(index == 0);
    /* It stands against the crates: target + reach is just past their edge. */
    CHECK_NEAR(target + ZOMBIE_REACH,
               1000.0f + terrain_half_width(TERRAIN_BARRICADE) + BARRICADE_CLAW_GAP, 1e-3f);
    /* Her on top counts as behind it too. */
    terrain_zombie_target(&t, 1500.0f, 1000.0f, &index);
    CHECK(index == 0);
    /* Same side: straight for her. */
    CHECK(terrain_zombie_target(&t, 1500.0f, 1300.0f, &index) == 1300.0f && index == -1);
    for (int i = 0; i < BARRICADE_STRIKES - 1; i++)
        CHECK(!terrain_claw(&t, 0));
    CHECK(terrain_frame(&t.items[0]) == 1); /* Cracked */
    CHECK(terrain_claw(&t, 0));
    CHECK(!terrain_blocks(&t.items[0]) && terrain_frame(&t.items[0]) == 2);
    CHECK(terrain_floor(&t, 1000.0f) == 0.0f);
    terrain_zombie_target(&t, 1500.0f, 600.0f, &index);
    CHECK(index == -1);
}

static void test_she_stands_on_it_and_falls_when_it_breaks(void)
{
    Player p;
    player_init(&p);
    InputState input;
    input_init(&input);
    p.jump.height = BARRICADE_TOP; /* Standing on top */
    player_set_ground(&p, BARRICADE_TOP, -1e9f, 1e9f);
    player_update(&p, &input, FIXED_DT);
    CHECK(!p.jump.airborne && p.jump.height == BARRICADE_TOP);
    /* Over the claw while up there. */
    CHECK(p.jump.height > ZOMBIE_CLAW_HEIGHT);
    player_set_ground(&p, 0.0f, -1e9f, 1e9f); /* Wrecked under her */
    bool landed = false;
    for (int i = 0; i < 120 && !landed; i++) {
        player_update(&p, &input, FIXED_DT);
        landed = !p.jump.airborne;
    }
    CHECK(landed && p.jump.height == 0.0f);
}

static void test_jump_lands_on_top(void)
{
    Jump j;
    jump_reset(&j);
    jump_start(&j);
    bool landed = false;
    for (int i = 0; i < 120 && !landed; i++)
        landed = jump_update_over(&j, FIXED_DT, BARRICADE_TOP);
    CHECK(landed && j.height == BARRICADE_TOP && !j.airborne);
    /* And off it again, down to the ground. */
    jump_start(&j);
    landed = false;
    float peak = 0.0f;
    for (int i = 0; i < 120 && !landed; i++) {
        landed = jump_update_over(&j, FIXED_DT, 0.0f);
        peak = j.height > peak ? j.height : peak;
    }
    CHECK(landed && j.height == 0.0f);
    CHECK_NEAR(peak, BARRICADE_TOP + PLAYER_JUMP_HEIGHT, 2.0f);
}

static void test_barrels_chain(void)
{
    Terrain t;
    terrain_clear(&t);
    terrain_add(&t, TERRAIN_BARREL, 1000.0f);
    terrain_add(&t, TERRAIN_BARREL, 1000.0f + BARREL_CHAIN_RADIUS - 1.0f);
    terrain_add(&t, TERRAIN_BARREL, 1000.0f + 3.0f * BARREL_CHAIN_RADIUS);
    Bullets bullets;
    bullets_clear(&bullets);
    bullets_spawn(&bullets, 980.0f, 990.0f, 330.0f, 1); /* Her muzzle's height */
    bullets_update(&bullets, FIXED_DT, 500.0f);
    CHECK(terrain_shoot(&t, &bullets) == 1);
    CHECK(bullets_active_count(&bullets) == 0); /* The bullet is spent */
    float xs[4];
    CHECK(terrain_explosions(&t, xs, 4) == 2); /* It and its neighbor; the far one stays */
    CHECK(t.items[0].spent && t.items[1].spent && !t.items[2].spent);
    CHECK(terrain_explosions(&t, xs, 4) == 0);
}

static void test_supply_once(void)
{
    Terrain t;
    terrain_clear(&t);
    terrain_add(&t, TERRAIN_SUPPLY, 1000.0f);
    CHECK(!terrain_take_supply(&t, 1000.0f + SUPPLY_RANGE + 1.0f));
    CHECK(terrain_take_supply(&t, 1000.0f));
    CHECK(!terrain_take_supply(&t, 1000.0f));
    CHECK(terrain_frame(&t.items[0]) == 1);
}

static void test_wall_blocks_even_jumping(void)
{
    Terrain t;
    terrain_clear(&t);
    terrain_add(&t, TERRAIN_WALL, 1000.0f);
    float reach = terrain_half_width(TERRAIN_WALL) + PLAYER_BODY_HALF_WIDTH;
    float min_x = -1e9f, max_x = 1e9f;
    terrain_bounds(&t, 700.0f, PLAYER_JUMP_HEIGHT, &min_x, &max_x);
    CHECK_NEAR(max_x, 1000.0f - reach, 1e-3f);
    CHECK(terrain_floor(&t, 1000.0f) == 0.0f); /* No standing on it */
    /* It stops bullets: nothing behind it gets hit. */
    Bullets bullets;
    bullets_clear(&bullets);
    bullets_spawn(&bullets, 900.0f, 930.0f, 330.0f, 1); /* Her muzzle's height */
    bullets_update(&bullets, FIXED_DT, 500.0f);
    CHECK(terrain_shoot(&t, &bullets) == 1 && bullets_active_count(&bullets) == 0);
    CHECK(terrain_blocks(&t.items[0])); /* Bullets don't hurt it */
    /* Claws do, slowly. */
    for (int i = 0; i < WALL_STRIKES - 1; i++)
        CHECK(!terrain_claw(&t, 0));
    CHECK(terrain_claw(&t, 0));
}

static void test_charge_blows_the_wall(void)
{
    Terrain t;
    terrain_clear(&t);
    terrain_add(&t, TERRAIN_WALL, 1000.0f);
    float edge = 1000.0f - terrain_half_width(TERRAIN_WALL) - PLAYER_BODY_HALF_WIDTH;
    CHECK(!terrain_light_charge(&t, edge - WALL_USE_RANGE - 50.0f)); /* Too far */
    CHECK(terrain_wall_near(&t, edge));
    CHECK(terrain_light_charge(&t, edge));
    CHECK(!terrain_wall_near(&t, edge)); /* Already lit */
    float xs[4];
    int steps = 0;
    while (terrain_explosions(&t, xs, 4) == 0 && steps < 1000) {
        terrain_update(&t, FIXED_DT);
        steps++;
    }
    CHECK_NEAR((float)steps * FIXED_DT, CHARGE_FUSE, 2.0f * FIXED_DT);
    CHECK(!terrain_blocks(&t.items[0]) && terrain_frame(&t.items[0]) == 2);
    float min_x = -1e9f, max_x = 1e9f;
    terrain_bounds(&t, 700.0f, 0.0f, &min_x, &max_x);
    CHECK(max_x == 1e9f); /* The way is open */
}

static void test_barrel_by_a_wall_opens_it(void)
{
    Terrain t;
    terrain_clear(&t);
    terrain_add(&t, TERRAIN_BARREL, 1000.0f - WALL_BARREL_GAP);
    terrain_add(&t, TERRAIN_WALL, 1000.0f);
    terrain_add(&t, TERRAIN_BARRICADE, 1000.0f + 2.0f * BARREL_RADIUS + 300.0f); /* Out of reach */
    t.items[0].blowing = true;
    float xs[4];
    CHECK(terrain_explosions(&t, xs, 4) == 1);
    CHECK(!terrain_blocks(&t.items[1]) && terrain_blocks(&t.items[2]));
}

static void test_dynamite_pickup(void)
{
    Terrain t;
    terrain_clear(&t);
    terrain_add(&t, TERRAIN_DYNAMITE, 1000.0f);
    CHECK(terrain_take_dynamite(&t, 1000.0f + PICKUP_RANGE + 1.0f) == 0);
    CHECK(terrain_take_dynamite(&t, 1000.0f) == DYNAMITE_PER_BOX);
    CHECK(terrain_take_dynamite(&t, 1000.0f) == 0);
}

/* One bullet flying right through x. */
static void shoot_at(Terrain *t, float x)
{
    Bullets bullets;
    bullets_clear(&bullets);
    bullets_spawn(&bullets, x - 20.0f, x - 10.0f, 330.0f, 1); /* Her muzzle's height */
    bullets_update(&bullets, FIXED_DT, x - 500.0f);
    terrain_shoot(t, &bullets);
}

static void test_crate_breaks_into_loot(void)
{
    Terrain t;
    terrain_clear(&t);
    terrain_add(&t, TERRAIN_CRATE, 1000.0f);
    for (int i = 0; i < CRATE_HITS - 1; i++)
        shoot_at(&t, 1000.0f);
    CHECK(!t.items[0].spent && terrain_frame(&t.items[0]) == 1 && t.events.crate_count == 0);
    shoot_at(&t, 1000.0f);
    CHECK(t.items[0].spent && t.events.crate_count == 1 && t.events.crates[0] == 0 &&
          !t.events.crate_blasted[0]);
    /* The same crate always holds the same; every kind turns up somewhere. */
    CHECK(terrain_loot(2, 5) == terrain_loot(2, 5));
    int seen[4] = {0};
    for (int i = 0; i < 64; i++)
        seen[terrain_loot(i % 5, i)]++;
    CHECK(seen[LOOT_AMMO] && seen[LOOT_HEALTH] && seen[LOOT_DYNAMITE] && seen[LOOT_GOLD]);
}

static void test_bottles_one_per_shot(void)
{
    Terrain t;
    terrain_clear(&t);
    terrain_add(&t, TERRAIN_BOTTLES, 1000.0f);
    for (int i = 0; i < BOTTLE_COUNT; i++) {
        CHECK(terrain_frame(&t.items[0]) == i);
        shoot_at(&t, 1000.0f);
    }
    CHECK(t.items[0].spent && t.events.bottle_count == 1);
}

static void test_lamp_falls_into_fire(void)
{
    Terrain t;
    terrain_clear(&t);
    terrain_add(&t, TERRAIN_LAMP, 1000.0f);
    shoot_at(&t, 1000.0f);
    CHECK(t.items[0].spent && t.count == 2 && t.items[1].kind == TERRAIN_FIRE);
    for (int i = 0; i < (int)(FIRE_TIME / FIXED_DT) + 2; i++)
        terrain_update(&t, FIXED_DT);
    CHECK(t.items[1].spent); /* Burnt out */
}

static void test_blast_opens_coffins_and_crates(void)
{
    Terrain t;
    terrain_clear(&t);
    terrain_add(&t, TERRAIN_BARREL, 1000.0f);
    terrain_add(&t, TERRAIN_CRATE, 1100.0f);
    terrain_add(&t, TERRAIN_COFFIN, 900.0f);
    t.items[0].blowing = true;
    float xs[4];
    terrain_explosions(&t, xs, 4);
    CHECK(t.items[1].spent && t.events.crate_count == 1 && t.events.crate_blasted[0]);
    CHECK(t.items[2].spent && t.events.coffin_count == 1);
    /* It leaves fire on the ground, round where it stood. */
    int fires = 0;
    for (int i = 0; i < t.count; i++)
        fires += t.items[i].kind == TERRAIN_FIRE && t.items[i].timer >= 1.5f;
    CHECK(fires == 3);
}

static void test_material_impacts_survive_event_clear(void)
{
    Terrain t;
    static const unsigned material[] = {
        TERRAIN_SOUND_HIT_WOOD, TERRAIN_SOUND_HIT_SAND,
        TERRAIN_SOUND_HIT_WOOD, TERRAIN_SOUND_HIT_METAL
    };
    for (int variant = 0; variant < BARRICADE_KINDS; variant++) {
        terrain_clear(&t);
        Piece *p = terrain_add(&t, TERRAIN_BARRICADE, 1000.0f);
        p->variant = variant;
        CHECK(!terrain_claw(&t, 0)); /* An impact, even when the piece survives */
        terrain_update(&t, FIXED_DT);
        terrain_clear_events(&t);
        CHECK(terrain_take_sound_events(&t) == material[variant]);
        CHECK(terrain_take_sound_events(&t) == 0); /* Consumed exactly once */
        p->spent = true;
        terrain_claw(&t, 0);
        CHECK(terrain_take_sound_events(&t) == 0);
    }
    terrain_clear(&t);
    terrain_add(&t, TERRAIN_WIRE, 1000.0f);
    CHECK(terrain_melee(&t, 990.0f, 1010.0f) == 1);
    CHECK(terrain_take_sound_events(&t) == TERRAIN_SOUND_HIT_WIRE);
    terrain_clear(&t);
    terrain_add(&t, TERRAIN_WALL, 1000.0f)->variant = 1;
    shoot_at(&t, 1000.0f);
    CHECK(terrain_take_sound_events(&t) == TERRAIN_SOUND_HIT_STONE);
}

static void test_explosions_preserve_source_kind(void)
{
    Terrain t;
    terrain_clear(&t);
    terrain_add(&t, TERRAIN_BARREL, 1000.0f)->blowing = true;
    terrain_plant_charge(&t, 3000.0f);
    terrain_add(&t, TERRAIN_WALL, 5000.0f)->fuse = 0.001f;
    t.items[1].fuse = 0.001f;
    terrain_update(&t, FIXED_DT);
    float xs[4];
    TerrainKind kinds[4];
    CHECK(terrain_explosions_typed(&t, xs, kinds, 4) == 3);
    CHECK(kinds[0] == TERRAIN_BARREL && kinds[1] == TERRAIN_CHARGE && kinds[2] == TERRAIN_WALL);
    CHECK_NEAR(xs[1], 3000.0f, 1e-3f);
    CHECK(terrain_explosions_typed(&t, xs, kinds, 4) == 0);
}

int main(void)
{
    printf("test_terrain\n");
    RUN(test_barricade_blocks_below_its_top);
    RUN(test_zombies_claw_through);
    RUN(test_she_stands_on_it_and_falls_when_it_breaks);
    RUN(test_jump_lands_on_top);
    RUN(test_barrels_chain);
    RUN(test_supply_once);
    RUN(test_wall_blocks_even_jumping);
    RUN(test_charge_blows_the_wall);
    RUN(test_barrel_by_a_wall_opens_it);
    RUN(test_dynamite_pickup);
    RUN(test_crate_breaks_into_loot);
    RUN(test_bottles_one_per_shot);
    RUN(test_lamp_falls_into_fire);
    RUN(test_blast_opens_coffins_and_crates);
    RUN(test_material_impacts_survive_event_clear);
    RUN(test_explosions_preserve_source_kind);
    return TEST_EXIT();
}
