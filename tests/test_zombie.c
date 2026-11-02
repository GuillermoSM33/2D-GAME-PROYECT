#include "config.h"
#include "game/bullet.h"
#include "game/combat.h"
#include "game/damage.h"
#include "game/effects.h"
#include "game/player.h"
#include "game/zombie.h"
#include "test.h"

#define MUZZLE_Y (BASELINE - 35.0f * SPRITE_SCALE)

static int shots_to_kill(const ZombieStats *stats, int level)
{
    Zombie zombie;
    zombie_spawn(&zombie, stats, 600.0f);
    int shots = 0;
    while (zombie_alive(&zombie) && shots < 100) {
        zombie_hit(&zombie, weapon_damage(level));
        shots++;
    }
    return shots;
}

static void test_armor_takes_more_shots(void)
{
    CHECK(shots_to_kill(&ZOMBIE_COMMON, 1) == 5);
    CHECK(shots_to_kill(&ZOMBIE_RIOT, 1) == 10);
    CHECK(shots_to_kill(&ZOMBIE_COMMON, 2) == 4);
    CHECK(shots_to_kill(&ZOMBIE_RIOT, 2) == 6);
    CHECK(shots_to_kill(&ZOMBIE_RIOT, 3) == 5);
}

static void test_walks_to_player_and_waits(void)
{
    Zombie zombie;
    zombie_spawn(&zombie, &ZOMBIE_RIOT, 800.0f);
    CHECK(zombie.facing == -1);
    for (int i = 0; i < 60; i++)
        zombie_update(&zombie, 200.0f, false, FIXED_DT);
    CHECK_NEAR(zombie.x, 800.0f - ZOMBIE_SPEED, 0.5f);
    CHECK(zombie.state == ZOMBIE_WALK);
    for (int i = 0; i < 60 * 20; i++)
        zombie_update(&zombie, 200.0f, false, FIXED_DT);
    CHECK_NEAR(zombie.x, 200.0f + ZOMBIE_REACH, 0.01f); /* Never walks into her */
    CHECK(zombie.state == ZOMBIE_WAIT);
    zombie_update(&zombie, 700.0f, false, FIXED_DT);
    CHECK(zombie.facing == 1); /* Turns when she passes it */
}

static void test_bullet_stops_on_hit(void)
{
    Zombie zombie;
    Bullets bullets;
    Effects effects;
    effects_clear(&effects);
    zombie_spawn(&zombie, &ZOMBIE_RIOT, 600.0f);
    bullets_clear(&bullets);
    bullets_spawn(&bullets, 300.0f, 300.0f, MUZZLE_Y, 1);
    int hits = 0;
    for (int i = 0; i < 60; i++) {
        bullets_update(&bullets, FIXED_DT, 0.0f);
        hits += combat_bullets_vs_zombie(&bullets, &zombie, &effects);
    }
    CHECK(hits == 1);
    CHECK(bullets_active_count(&bullets) == 0);
    /* 10.8 through the armor: 10 off its health, the rest kept for the next hit. */
    CHECK(zombie.health ==
          ZOMBIE_RIOT.health - (int)damage_through_armor(weapon_damage(1), ZOMBIE_RIOT.armor));
    CHECK(zombie.state == ZOMBIE_HURT);
}

static void test_bullet_misses_above(void)
{
    Zombie zombie;
    Bullets bullets;
    Effects effects;
    effects_clear(&effects);
    zombie_spawn(&zombie, &ZOMBIE_RIOT, 600.0f);
    bullets_clear(&bullets);
    bullets_spawn(&bullets, 300.0f, 300.0f, BASELINE - ZOMBIE_HEIGHT * SPRITE_SCALE - 10.0f, 1);
    for (int i = 0; i < 60; i++) {
        bullets_update(&bullets, FIXED_DT, 0.0f);
        CHECK(combat_bullets_vs_zombie(&bullets, &zombie, &effects) == 0);
    }
}

static void test_dead_fades_and_is_gone(void)
{
    Zombie zombie;
    zombie_spawn(&zombie, &ZOMBIE_RIOT, 700.0f);
    zombie.just_spawned = false;
    CHECK(zombie_hit(&zombie, 1000.0f) == HIT_KILL);
    CHECK(!zombie_alive(&zombie));
    float fall = (ZOMBIE_DEATH_FRAMES - 1) / ZOMBIE_DEATH_FPS;
    zombie_update(&zombie, 200.0f, false, fall + ZOMBIE_CORPSE_TIME);
    CHECK_NEAR(zombie_opacity(&zombie), 1.0f, 1e-6f); /* Lies there first */
    zombie_update(&zombie, 200.0f, false, ZOMBIE_FADE_TIME / 2.0f);
    CHECK_NEAR(zombie_opacity(&zombie), 0.5f, 0.01f);
    CHECK(!zombie_gone(&zombie));
    zombie_update(&zombie, 200.0f, false, ZOMBIE_FADE_TIME / 2.0f + 0.001f);
    CHECK(zombie_gone(&zombie)); /* The stage decides what comes next */
    CHECK(!zombie_alive(&zombie));
    /* With her near the left of the view, the next one enters on the right. */
    CHECK_NEAR(zombie_spawn_x(200.0f), VIEW_WIDTH - ZOMBIE_SPAWN_MARGIN, 0.01f);
}

static void test_level_scales_like_the_player(void)
{
    Zombie zombie;
    zombie_spawn(&zombie, &ZOMBIE_RIOT, 600.0f);
    CHECK(zombie.level == 1 && zombie.max_health == ZOMBIE_RIOT.health);
    CHECK_NEAR(zombie.armor, ZOMBIE_RIOT.armor, 1e-4f);
    zombie_set_level(&zombie, 3);
    CHECK(zombie.health == zombie.max_health && zombie.max_health == 220);
    CHECK_NEAR(zombie.armor, ZOMBIE_RIOT.armor + 2.0f * ZOMBIE_ARMOR_PER_LEVEL, 1e-4f);
    CHECK_NEAR(zombie_attack_damage(&zombie), damage_at_level(ZOMBIE_ATTACK_BASE, 3), 1e-4f);
}

static void test_dead_zombie_lets_bullets_pass(void)
{
    Zombie zombie;
    Bullets bullets;
    Effects effects;
    effects_clear(&effects);
    zombie_spawn(&zombie, &ZOMBIE_RIOT, 600.0f);
    zombie_hit(&zombie, 1000.0f);
    bullets_clear(&bullets);
    bullets_spawn(&bullets, 600.0f, 600.0f, MUZZLE_Y, 1);
    CHECK(combat_bullets_vs_zombie(&bullets, &zombie, &effects) == 0);
    CHECK(bullets_active_count(&bullets) == 1);
}

static void test_hurt_recoils_then_walks_on(void)
{
    Zombie zombie;
    zombie_spawn(&zombie, &ZOMBIE_RIOT, 800.0f);
    zombie_hit(&zombie, weapon_damage(1));
    CHECK(zombie.state == ZOMBIE_HURT);
    CHECK(zombie.anim.frame == 0);
    unsigned seen = 0;
    float x = zombie.x;
    for (int i = 0; i < 14; i++) { /* A bit less than 3 frames at 12 fps */
        zombie_update(&zombie, 200.0f, false, FIXED_DT);
        seen |= 1u << zombie.anim.frame;
    }
    CHECK(zombie.state == ZOMBIE_HURT);
    CHECK(zombie.x == x); /* Stands still while recoiling */
    CHECK(seen == (1u << ZOMBIE_HURT_FRAMES) - 1);
    for (int i = 0; i < 2; i++)
        zombie_update(&zombie, 200.0f, false, FIXED_DT);
    CHECK(zombie.state == ZOMBIE_WALK);
    CHECK(zombie.x < x);
}

static void test_bullet_stream_cannot_pin_it(void)
{
    Zombie zombie;
    zombie_spawn(&zombie, &ZOMBIE_RIOT, 800.0f);
    CHECK(zombie_hit(&zombie, weapon_damage(1)) == HIT_STAGGER);
    for (int i = 0; i < 20; i++) /* Recoil over */
        zombie_update(&zombie, 200.0f, false, FIXED_DT);
    CHECK(zombie.state == ZOMBIE_WALK);
    CHECK(zombie_hit(&zombie, weapon_damage(1)) == HIT_ARMOR);
    CHECK(zombie.state == ZOMBIE_WALK); /* Still recovering: keeps walking */
    /* ...but loses health */
    CHECK(zombie.health == ZOMBIE_RIOT.health -
                           (int)(2.0f * damage_through_armor(weapon_damage(1), ZOMBIE_RIOT.armor)));
    for (int i = 0; i < 40; i++)
        zombie_update(&zombie, 200.0f, false, FIXED_DT);
    CHECK(zombie_hit(&zombie, weapon_damage(1)) == HIT_STAGGER); /* Recovered */
}

static void test_every_bullet_sparks(void)
{
    Zombie zombie;
    Bullets bullets;
    Effects effects;
    effects_clear(&effects);
    zombie_spawn(&zombie, &ZOMBIE_RIOT, 600.0f);
    bullets_clear(&bullets);
    /* First hit recoils: its sheet already has sparks, so no extra effect. */
    bullets_spawn(&bullets, 560.0f, 560.0f, MUZZLE_Y, 1);
    combat_bullets_vs_zombie(&bullets, &zombie, &effects);
    CHECK(zombie.state == ZOMBIE_HURT);
    CHECK(effects_active_count(&effects) == 0);
    /* The next ones only hit the armor, and each sparks. */
    for (int shot = 0; shot < 3; shot++) {
        bullets_spawn(&bullets, 560.0f, 560.0f, MUZZLE_Y, 1);
        combat_bullets_vs_zombie(&bullets, &zombie, &effects);
    }
    CHECK(effects_active_count(&effects) == 3);
    const Effect *e = &effects.items[0];
    CHECK(e->x == zombie.x && e->y == MUZZLE_Y && e->facing == zombie.facing);
}

static void test_sparks_play_once(void)
{
    Effects effects;
    effects_clear(&effects);
    effects_spawn(&effects, effect_sparks(), 300.0f, 300.0f, 1);
    unsigned seen = 0;
    int steps = 0;
    while (effects_active_count(&effects) && steps < 100) {
        seen |= 1u << effects.items[0].anim.frame;
        effects_update(&effects, FIXED_DT);
        steps++;
    }
    CHECK(seen == (1u << SPARKS_FRAMES) - 1);
    CHECK(steps == 10); /* 2 frames at 12 fps */
}

static void test_point_blank_shot_hits(void)
{
    /* The muzzle can end up past the body when she stands right next to it. */
    Zombie zombie;
    Bullets bullets;
    Effects effects;
    effects_clear(&effects);
    zombie_spawn(&zombie, &ZOMBIE_RIOT, 600.0f);
    bullets_clear(&bullets);
    bullets_spawn(&bullets, 560.0f, 560.0f + 35.5f * SPRITE_SCALE, MUZZLE_Y, 1);
    CHECK(combat_bullets_vs_zombie(&bullets, &zombie, &effects) == 1);
}

static void test_fast_bullet_does_not_skip_through(void)
{
    Zombie zombie;
    Bullets bullets;
    Effects effects;
    effects_clear(&effects);
    zombie_spawn(&zombie, &ZOMBIE_RIOT, 600.0f);
    bullets_clear(&bullets);
    bullets_spawn(&bullets, 300.0f, 300.0f, MUZZLE_Y, 1);
    bullets_update(&bullets, 0.5f, 0.0f); /* One huge step from 300 to 750 */
    CHECK(combat_bullets_vs_zombie(&bullets, &zombie, &effects) == 1);
}

static void test_lethal_hit_skips_hurt(void)
{
    Zombie zombie;
    zombie_spawn(&zombie, &ZOMBIE_RIOT, 800.0f);
    CHECK(zombie_hit(&zombie, 1000.0f) == HIT_KILL);
    CHECK(zombie.state == ZOMBIE_DEAD);
}

static void test_death_falls_and_stays_down(void)
{
    Zombie zombie;
    zombie_spawn(&zombie, &ZOMBIE_RIOT, 600.0f);
    zombie_hit(&zombie, 1000.0f);
    CHECK(zombie.anim.frame == 1); /* Jolt with sparks right away */
    unsigned seen = 0;
    for (int i = 0; i < 60 * 2; i++) {
        zombie_update(&zombie, 200.0f, false, FIXED_DT);
        seen |= 1u << zombie.anim.frame;
    }
    CHECK(seen == 0xFEu); /* Frames 1-7 */
    CHECK(zombie.anim.frame == ZOMBIE_DEATH_FRAMES - 1);
    CHECK(zombie.x == 600.0f); /* Does not slide while falling */
}

static void test_killing_shot_adds_no_extra_sparks(void)
{
    Zombie zombie;
    Bullets bullets;
    Effects effects;
    effects_clear(&effects);
    zombie_spawn(&zombie, &ZOMBIE_RIOT, 600.0f);
    zombie.health = 1;
    bullets_clear(&bullets);
    bullets_spawn(&bullets, 560.0f, 560.0f, MUZZLE_Y, 1);
    combat_bullets_vs_zombie(&bullets, &zombie, &effects);
    CHECK(zombie.state == ZOMBIE_DEAD);
    CHECK(effects_active_count(&effects) == 0);
}

/* A zombie already standing within reach of a player at x. */
static void zombie_next_to(Zombie *zombie, Player *player, float x)
{
    player_init(player);
    player->x = x;
    zombie_spawn(zombie, &ZOMBIE_RIOT, x + ZOMBIE_REACH);
}

static void test_claw_uses_weapon_formula(void)
{
    Zombie zombie;
    zombie_spawn(&zombie, &ZOMBIE_RIOT, 600.0f);
    CHECK_NEAR(zombie_attack_damage(&zombie), 15.0f, 1e-4f);
    CHECK_NEAR(damage_at_level(ZOMBIE_ATTACK_BASE, 2), 24.0f, 1e-4f);
    CHECK(damage_after_armor(zombie_attack_damage(&zombie), PLAYER_ARMOR) == 12);
}

static void test_attacks_on_strike_frame(void)
{
    Zombie zombie;
    Player player;
    zombie_next_to(&zombie, &player, 300.0f);
    zombie_update(&zombie, player.x, true, FIXED_DT);
    CHECK(zombie.state == ZOMBIE_ATTACK);
    int strikes = 0, strike_step = -1;
    for (int i = 1; i < 60; i++) {
        zombie_update(&zombie, player.x, true, FIXED_DT);
        if (zombie.struck) {
            strikes++;
            strike_step = i;
            CHECK(zombie.anim.frame == ZOMBIE_ATTACK_STRIKE_FRAME);
            CHECK(combat_zombie_vs_player(&zombie, &player));
        }
    }
    CHECK(strikes == 1);
    /* Two wind-up frames at 10 fps: the claw lands 0.2 s in. */
    CHECK(strike_step >= 11 && strike_step <= 13);
    CHECK(player.health == PLAYER_HEALTH - 12);
    CHECK(player.knockback_dir == -1); /* Pushed away from a zombie on her right */
}

static void test_waits_between_attacks(void)
{
    Zombie zombie;
    Player player;
    zombie_next_to(&zombie, &player, 300.0f);
    float attack_time = ZOMBIE_ATTACK_FRAMES / ZOMBIE_ATTACK_FPS;
    int steps = (int)((attack_time + ZOMBIE_ATTACK_COOLDOWN * 0.5f) / FIXED_DT);
    for (int i = 0; i < steps; i++)
        zombie_update(&zombie, player.x, true, FIXED_DT);
    CHECK(zombie.state == ZOMBIE_WAIT);
    for (int i = 0; i < (int)(ZOMBIE_ATTACK_COOLDOWN / FIXED_DT); i++)
        zombie_update(&zombie, player.x, true, FIXED_DT);
    CHECK(zombie.state == ZOMBIE_ATTACK);
}

static void test_nine_claws_kill_her(void)
{
    Zombie zombie;
    Player player;
    zombie_next_to(&zombie, &player, 300.0f);
    int landed = 0;
    for (int i = 0; i < 60 * 30 && player_alive(&player); i++) {
        player.x = 300.0f; /* Stands her ground despite the push */
        zombie_update(&zombie, player.x, player_alive(&player), FIXED_DT);
        landed += combat_zombie_vs_player(&zombie, &player);
    }
    CHECK(landed == 9); /* 100 health, 12 per claw */
    CHECK(player.health == 0);
    CHECK(player.state == PLAYER_DEAD);
    for (int i = 0; i < 60 * 3; i++)
        zombie_update(&zombie, player.x, player_alive(&player), FIXED_DT);
    CHECK(zombie.state == ZOMBIE_WAIT); /* No attacking a body */
}

static void test_stepping_back_dodges(void)
{
    Zombie zombie;
    Player player;
    zombie_next_to(&zombie, &player, 300.0f);
    zombie_update(&zombie, player.x, true, FIXED_DT);
    player.x = zombie.x - ZOMBIE_ATTACK_RANGE - 1.0f;
    for (int i = 0; i < 30; i++) {
        zombie_update(&zombie, 300.0f, true, FIXED_DT); /* Committed to the swipe */
        CHECK(!combat_zombie_vs_player(&zombie, &player));
    }
    CHECK(player.health == PLAYER_HEALTH);
}

static void test_shot_interrupts_swipe(void)
{
    Zombie zombie;
    Player player;
    zombie_next_to(&zombie, &player, 300.0f);
    zombie_update(&zombie, player.x, true, FIXED_DT);
    CHECK(zombie.state == ZOMBIE_ATTACK);
    CHECK(zombie_hit(&zombie, weapon_damage(1)) == HIT_STAGGER);
    for (int i = 0; i < 12; i++) {
        zombie_update(&zombie, player.x, true, FIXED_DT);
        CHECK(!zombie.struck);
    }
}

static void test_growls_every_interval_while_alive(void)
{
    Zombie zombie;
    zombie_spawn(&zombie, &ZOMBIE_RIOT, 800.0f);
    CHECK(zombie.just_spawned);
    int growls = 0;
    for (float t = 0.0f; t < 3.0f * ZOMBIE_GROWL_INTERVAL - FIXED_DT / 2.0f; t += FIXED_DT) {
        zombie_update(&zombie, 200.0f, false, FIXED_DT);
        growls += zombie.growl_due;
        zombie.growl_due = false;
    }
    CHECK(growls == 3); /* At 6, 12 and 18 s; the spawn growl covers 0 */
}

static void test_death_groans_and_stops_growling(void)
{
    Zombie zombie;
    zombie_spawn(&zombie, &ZOMBIE_RIOT, 800.0f);
    zombie.just_spawned = false;
    CHECK(zombie_hit(&zombie, 1000.0f) == HIT_KILL);
    CHECK(zombie.just_died);
    zombie.just_died = false;
    CHECK(zombie_hit(&zombie, 1000.0f) == HIT_NONE && !zombie.just_died); /* Dies only once */
    /* Silent while it lies there and fades. */
    int growls = 0;
    while (!zombie_gone(&zombie)) {
        zombie_update(&zombie, 200.0f, false, FIXED_DT);
        growls += zombie.growl_due;
    }
    CHECK(growls == 0);
}

int main(void)
{
    printf("test_zombie\n");
    RUN(test_armor_takes_more_shots);
    RUN(test_walks_to_player_and_waits);
    RUN(test_bullet_stops_on_hit);
    RUN(test_bullet_misses_above);
    RUN(test_dead_fades_and_is_gone);
    RUN(test_level_scales_like_the_player);
    RUN(test_dead_zombie_lets_bullets_pass);
    RUN(test_hurt_recoils_then_walks_on);
    RUN(test_bullet_stream_cannot_pin_it);
    RUN(test_every_bullet_sparks);
    RUN(test_sparks_play_once);
    RUN(test_death_falls_and_stays_down);
    RUN(test_killing_shot_adds_no_extra_sparks);
    RUN(test_point_blank_shot_hits);
    RUN(test_fast_bullet_does_not_skip_through);
    RUN(test_lethal_hit_skips_hurt);
    RUN(test_claw_uses_weapon_formula);
    RUN(test_attacks_on_strike_frame);
    RUN(test_waits_between_attacks);
    RUN(test_nine_claws_kill_her);
    RUN(test_stepping_back_dodges);
    RUN(test_shot_interrupts_swipe);
    RUN(test_growls_every_interval_while_alive);
    RUN(test_death_groans_and_stops_growling);
    return TEST_EXIT();
}
