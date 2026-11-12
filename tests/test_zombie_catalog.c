#include <limits.h>
#include <math.h>
#include <string.h>

#include "config.h"
#include "game/damage.h"
#include "game/combat.h"
#include "game/progression.h"
#include "game/stages.h"
#include "game/zombie.h"
#include "test.h"

static void test_professions_and_runners_are_distinct_stable_variants(void)
{
    CHECK(ZOMBIE_KIND_COUNT == 30 && ZOMBIE_KINDS_FIRST_ROUTE == 25);
    for (int kind = 0; kind < ZOMBIE_KIND_COUNT; kind++) {
        const ZombieKindDef *def = zombie_kind_def((ZombieKind)kind);
        const ZombieStats *normal = zombie_stats((ZombieKind)kind, false);
        const ZombieStats *runner = zombie_stats((ZombieKind)kind, true);
        CHECK(def->id && *def->id && def->name && *def->name);
        CHECK(def->description && *def->description && def->armor_profession && *def->armor_profession);
        CHECK(def->stats == normal && normal != runner);
        CHECK(normal == zombie_stats((ZombieKind)kind, false));
        CHECK(runner == zombie_stats((ZombieKind)kind, true));
        CHECK(normal->kind == (ZombieKind)kind && !normal->runner);
        CHECK(runner->kind == (ZombieKind)kind && runner->runner);
        CHECK(runner->health == (int)lroundf((float)normal->health * .55f));
        CHECK(runner->health < normal->health);
        CHECK_NEAR(runner->speed, normal->speed * 1.8f, 1e-5f);
        CHECK_NEAR(runner->armor, normal->armor, 1e-5f);
        CHECK_NEAR(runner->attack_base, normal->attack_base, 1e-5f);
        for (int next = kind + 1; next < ZOMBIE_KIND_COUNT; next++)
            CHECK(strcmp(def->id, zombie_kind_def((ZombieKind)next)->id) != 0);
    }
    CHECK(zombie_stats(ZOMBIE_KIND_RIOT, false) == &ZOMBIE_RIOT);
    CHECK(zombie_stats(ZOMBIE_KIND_ELITE, false) == &ZOMBIE_ELITE);
    CHECK(zombie_stats((ZombieKind)-1, false) == &ZOMBIE_RIOT);
    CHECK(zombie_kind_def((ZombieKind)999) == zombie_kind_def(ZOMBIE_KIND_RIOT));
    CHECK(ZOMBIE_COMMON.health == 100 && ZOMBIE_COMMON.armor == 0.0f);
    CHECK(ZOMBIE_RUNNER.health == 55 && ZOMBIE_RUNNER.armor == 25.0f);
    CHECK_NEAR(ZOMBIE_RUNNER.speed, 1.8f, 1e-5f);
}

static void test_level_scaling_respects_equipment_and_keeps_speed(void)
{
    const int levels[] = {-1, 0, 1, 2, 5, 10, MAX_LEVEL, MAX_LEVEL + 1, INT_MAX};
    for (int kind = 0; kind < ZOMBIE_KIND_COUNT; kind++)
        for (int fast = 0; fast < 2; fast++) {
            const ZombieStats *stats = zombie_stats((ZombieKind)kind, fast != 0);
            float first_step = 0.0f;
            for (size_t l = 0; l < sizeof(levels) / sizeof(levels[0]); l++) {
                Zombie z;
                zombie_spawn(&z, stats, 0.0f);
                zombie_set_level(&z, levels[l]);
                int expected_level = levels[l] < 1 ? 1 : levels[l] > MAX_LEVEL ? MAX_LEVEL : levels[l];
                CHECK(z.level == expected_level);
                CHECK(z.kind == (ZombieKind)kind && z.runner == (fast != 0));
                CHECK(z.max_health == level_health(stats->health, levels[l]));
                CHECK(z.health == z.max_health && z.wound == 0.0f);
                CHECK_NEAR(z.armor, level_armor(stats->armor,
                           stats->armor > 0.0f ? ZOMBIE_ARMOR_PER_LEVEL : 0.0f, levels[l]), 1e-4f);
                CHECK_NEAR(zombie_attack_damage(&z), damage_at_level(stats->attack_base, expected_level), 1e-4f);
                if (stats->armor == 0.0f)
                    CHECK(z.armor == 0.0f); /* A level never invents armor on clothes or bare bones. */
                zombie_update(&z, 10000.0f, true, .1f);
                CHECK_NEAR(z.x, ZOMBIE_SPEED * stats->speed * .1f, 1e-4f);
                if (l == 0)
                    first_step = z.x;
                else
                    CHECK_NEAR(z.x, first_step, 1e-4f);
            }
        }
}

static void test_all_sheets_have_one_template_and_complete_frame_contract(void)
{
    const char *actions[] = {"idle", "walk", "run", "attack", "hurt", "death", "caught"};
    const int frames[] = {4, 8, 8, 6, 3, 8, 4};
    for (int kind = 0; kind < ZOMBIE_KIND_COUNT; kind++)
        for (int action = 0; action < ZOMBIE_ANIM_COUNT; action++) {
            const AnimationDef *anim = zombie_animation((ZombieKind)kind, (ZombieAnimation)action);
            char expected[128];
            snprintf(expected, sizeof(expected), "sprites/zombies/%s/%s",
                     zombie_kind_def((ZombieKind)kind)->id, actions[action]);
            CHECK(strcmp(anim->sheet, expected) == 0);
            CHECK(anim->frame_w == 72 && anim->frame_h == 72 && anim->first_frame == 0);
            CHECK(anim->frame_count == frames[action]);
            CHECK_NEAR(anim->anchor_x, 27.5f, 1e-5f);
            CHECK_NEAR(anim->ground_y, 68.0f, 1e-5f);
            bool loops = action == ZOMBIE_ANIM_IDLE || action == ZOMBIE_ANIM_WALK ||
                         action == ZOMBIE_ANIM_RUN || action == ZOMBIE_ANIM_CAUGHT;
            CHECK(anim->loop == loops);
        }
    int count = 0;
    const AnimationDef *const *all = zombie_animations(&count);
    CHECK(count == 4 + ZOMBIE_KIND_COUNT * ZOMBIE_ANIM_COUNT);
    for (int i = 0; i < count; i++) {
        CHECK(all[i] != NULL);
        for (int j = i + 1; j < count; j++) {
            if (all[i] == all[j])
                CHECK(strncmp(all[i]->sheet, "sprites/zombies/riot/", strlen("sprites/zombies/riot/")) == 0);
        }
    }
}

static void test_riot_and_elite_keep_the_original_four_sheets(void)
{
    const ZombieKind kinds[] = {ZOMBIE_KIND_RIOT, ZOMBIE_KIND_ELITE};
    const ZombieAnimation actions[] = {ZOMBIE_ANIM_WALK, ZOMBIE_ANIM_ATTACK,
                                       ZOMBIE_ANIM_HURT, ZOMBIE_ANIM_DEATH};
    const char *sheets[] = {"walk", "attack", "hurt", "death"};
    const int frames[] = {8, 6, 3, 8};
    for (int k = 0; k < 2; k++) {
        for (int action = 0; action < 4; action++) {
            const AnimationDef *def = zombie_animation(kinds[k], actions[action]);
            char expected[96];
            snprintf(expected, sizeof(expected), "sprites/zombies/%s/%s",
                     zombie_kind_def(kinds[k])->id, sheets[action]);
            CHECK(strcmp(def->sheet, expected) == 0);
            CHECK(def->frame_count == frames[action]);
        }
        Zombie zombie;
        zombie_spawn(&zombie, zombie_stats(kinds[k], false), 1000.0f);
        CHECK(zombie.anim.def == zombie_animation(kinds[k], ZOMBIE_ANIM_WALK));
        zombie_update(&zombie, zombie.x, true, FIXED_DT);
        CHECK(zombie.anim.def == zombie_animation(kinds[k], ZOMBIE_ANIM_ATTACK));
        zombie_hit(&zombie, 1.0f);
        CHECK(zombie.anim.def == zombie_animation(kinds[k], ZOMBIE_ANIM_HURT));
        zombie_hit(&zombie, 1000000.0f);
        CHECK(zombie.anim.def == zombie_animation(kinds[k], ZOMBIE_ANIM_DEATH));
        CHECK(zombie.anim.frame == 1);
    }
}

static void test_every_variant_idles_runs_attacks_recovers_and_stays_dead(void)
{
    for (int kind = 0; kind < ZOMBIE_KIND_COUNT; kind++)
        for (int fast = 0; fast < 2; fast++) {
            Zombie z;
            zombie_spawn(&z, zombie_stats((ZombieKind)kind, fast != 0), 1000.0f);
            z.awake = false;
            zombie_update(&z, 0.0f, true, .5f);
            CHECK(z.anim.def == zombie_animation(z.kind, ZOMBIE_ANIM_IDLE));
            CHECK(z.anim.frame > 0 && z.x == 1000.0f); /* Idle is animated, not a frozen walk frame. */
            zombie_wake(&z);
            for (int i = 0; i < 60; i++)
                zombie_update(&z, 0.0f, true, FIXED_DT);
            CHECK(z.x < 1000.0f && z.state == ZOMBIE_WALK);
            CHECK(z.anim.def == zombie_animation(z.kind, fast ? ZOMBIE_ANIM_RUN : ZOMBIE_ANIM_WALK));

            zombie_update(&z, z.x, true, FIXED_DT);
            CHECK(z.state == ZOMBIE_ATTACK && z.anim.def == zombie_animation(z.kind, ZOMBIE_ANIM_ATTACK));
            int struck = 0;
            for (int i = 0; i < 36; i++) {
                zombie_update(&z, z.x, true, FIXED_DT);
                if (z.struck)
                    CHECK(z.anim.frame == ZOMBIE_ATTACK_STRIKE_FRAME);
                struck += z.struck;
            }
            CHECK(struck == 1 && z.state == ZOMBIE_WAIT);
            CHECK(z.anim.def == zombie_animation(z.kind, ZOMBIE_ANIM_IDLE));
            CHECK(zombie_hit(&z, 1.0f) == HIT_STAGGER);
            CHECK(z.anim.def == zombie_animation(z.kind, ZOMBIE_ANIM_HURT));
            for (int i = 0; i < 20; i++)
                zombie_update(&z, z.x + 1000.0f, true, FIXED_DT);
            CHECK(z.state == ZOMBIE_WALK);

            CHECK(zombie_hit(&z, 1000000.0f) == HIT_KILL);
            CHECK(z.anim.def == zombie_animation(z.kind, ZOMBIE_ANIM_DEATH) && z.anim.frame == 1);
            float x = z.x;
            unsigned seen = 0;
            for (int i = 0; i < 120; i++) {
                zombie_update(&z, 0.0f, false, FIXED_DT);
                seen |= 1u << z.anim.frame;
            }
            CHECK(seen == 0xFEu && z.anim.frame == 7 && z.x == x);
            CHECK(zombie_hit(&z, 1000.0f) == HIT_NONE);
        }
}

static void test_caught_loop_releases_back_to_motion_even_after_hurt(void)
{
    for (int kind = 0; kind < ZOMBIE_KIND_COUNT; kind++)
        for (int fast = 0; fast < 2; fast++) {
            Zombie z;
            zombie_spawn(&z, zombie_stats((ZombieKind)kind, fast != 0), 0.0f);
            zombie_hit(&z, 1.0f); /* The trap's initial impact recoils the body. */
            z.caught = .6f;
            z.catch_kind = CATCH_NET;
            for (int i = 0; i < 20; i++)
                zombie_update(&z, 1000.0f, true, FIXED_DT);
            CHECK(z.caught > 0.0f && z.x == 0.0f);
            CHECK(z.anim.def == zombie_animation(z.kind, ZOMBIE_ANIM_CAUGHT));
            CHECK(z.anim.frame > 0);
            for (int i = 0; i < 60; i++)
                zombie_update(&z, 1000.0f, true, FIXED_DT);
            CHECK(z.caught == 0.0f && z.catch_kind == CATCH_NONE);
            CHECK(z.state == ZOMBIE_WALK && z.x > 0.0f);
            CHECK(z.anim.def == zombie_animation(z.kind, fast ? ZOMBIE_ANIM_RUN : ZOMBIE_ANIM_WALK));
        }
}

static void test_campaign_contains_all_fifty_without_adding_bodies_or_elites(void)
{
    bool seen[ZOMBIE_KIND_COUNT][2] = {{false}};
    /* The first route's counts as they were; the second route's, longer. */
    const int original_counts[] = {10, 14, 13, 19, 22, 28, 31, 33, 36, 38};
    int elites = 0;
    CHECK(STAGE_COUNT == 10);
    for (int s = 0; s < STAGE_COUNT; s++) {
        CHECK(STAGES[s].zombies == original_counts[s]);
        int index = 0;
        for (int spot = 0; spot < STAGES[s].spot_count; spot++) {
            const StageSpot *p = &STAGES[s].spots[spot];
            if (!spot_has_zombies(p->kind))
                continue;
            for (int body = 0; body < p->count; body++, index++) {
                const ZombieStats *stats = stage_zombie_stats(&STAGES[s], index);
                CHECK(stats == stage_zombie_stats(&STAGES[s], index));
                seen[stats->kind][stats->runner ? 1 : 0] = true;
                if (s == 0)
                    CHECK(stats == &ZOMBIE_RIOT);
                if (p->kind == SPOT_RUNNERS)
                    CHECK(stats->runner);
                if (p->kind == SPOT_ELITE) {
                    CHECK(stats == &ZOMBIE_ELITE);
                    elites++;
                } else {
                    CHECK(stats != &ZOMBIE_ELITE); /* No extra elite-reward economy. */
                }
            }
        }
        CHECK(index == STAGES[s].zombies);
    }
    CHECK(elites == 3 + 5); /* 1-3, 1-4, 1-5; 2-2, 2-3, 2-4 and two in 2-5 */
    for (int kind = 0; kind < ZOMBIE_KIND_COUNT; kind++)
        CHECK(seen[kind][0] && seen[kind][1]);
}

static void test_dog_collision_matches_lower_body_and_standard_gun_height(void)
{
    for (int fast = 0; fast < 2; fast++) {
        Zombie dog;
        zombie_spawn(&dog, zombie_stats(ZOMBIE_KIND_DOG, fast != 0), 1000.0f);
        CHECK_NEAR(zombie_body_height(&dog), 38.0f * SPRITE_SCALE, 1e-5f);
        CHECK_NEAR(zombie_body_half_width(&dog), 22.0f * SPRITE_SCALE, 1e-5f);
        CHECK(!zombie_overlaps(&dog, 900.0f, 1100.0f,
                              BASELINE - zombie_body_height(&dog) - 1.0f));
        Bullets bullets;
        Effects effects;
        bullets_clear(&bullets);
        effects_clear(&effects);
        float y = BASELINE - PLAYER_MUZZLE_DY * SPRITE_SCALE;
        bullets_spawn(&bullets, 900.0f, 1100.0f, y, 1);
        CHECK(combat_bullets_vs_zombie(&bullets, &dog, &effects) == 1);
        CHECK(dog.health < dog.max_health && bullets_active_count(&bullets) == 0);
    }
}

static void test_repeated_hits_on_unarmored_bodies_do_not_emit_metal_sparks(void)
{
    const ZombieKind kinds[] = {ZOMBIE_KIND_CIVIL_MALE_1, ZOMBIE_KIND_DOG, ZOMBIE_KIND_RIOT};
    for (int k = 0; k < 3; k++) {
        Zombie z;
        zombie_spawn(&z, zombie_stats(kinds[k], false), 1000.0f);
        zombie_hit(&z, 1.0f); /* Recoil immunity should not turn flesh into armor. */
        Bullets bullets;
        Effects effects;
        bullets_clear(&bullets);
        effects_clear(&effects);
        float y = BASELINE - PLAYER_MUZZLE_DY * SPRITE_SCALE;
        bullets_spawn(&bullets, 900.0f, 1100.0f, y, 1);
        CHECK(combat_bullets_vs_zombie(&bullets, &z, &effects) == 1);
        CHECK(effects_active_count(&effects) == (z.armor > 0.0f ? 1 : 0));
    }
}

int main(void)
{
    printf("test_zombie_catalog\n");
    RUN(test_professions_and_runners_are_distinct_stable_variants);
    RUN(test_level_scaling_respects_equipment_and_keeps_speed);
    RUN(test_all_sheets_have_one_template_and_complete_frame_contract);
    RUN(test_riot_and_elite_keep_the_original_four_sheets);
    RUN(test_every_variant_idles_runs_attacks_recovers_and_stays_dead);
    RUN(test_caught_loop_releases_back_to_motion_even_after_hurt);
    RUN(test_campaign_contains_all_fifty_without_adding_bodies_or_elites);
    RUN(test_dog_collision_matches_lower_body_and_standard_gun_height);
    RUN(test_repeated_hits_on_unarmored_bodies_do_not_emit_metal_sparks);
    return TEST_EXIT();
}
