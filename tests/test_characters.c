#include <math.h>
#include <stdio.h>
#include <string.h>

#include "config.h"
#include "game/char_select.h"
#include "game/characters.h"
#include "game/damage.h"
#include "game/progression.h"
#include "game/shoot.h"
#include "game/weapons.h"
#include "game/zombie.h"
#include "test.h"

static void test_three_characters_with_their_abilities(void)
{
    CHECK(CHARACTER_COUNT == 3);
    CHECK(strcmp(CHARACTERS[0].id, "cowgirl") == 0 && character_drops_chests(&CHARACTERS[0]));
    CHECK(CHARACTERS[1].ability == ABILITY_WEAPON_SWAP && CHARACTERS[1].weapon_count == 2);
    CHECK(CHARACTERS[2].ability == ABILITY_EXPERIMENTAL_WEAPON);
    CHECK(weapon_def(CHARACTERS[2].weapons[0])->armor_share < 1.0f);
    for (int c = 0; c < CHARACTER_COUNT; c++) {
        CHECK(CHARACTERS[c].weapon_count >= 1 && CHARACTERS[c].weapon_count <= CHARACTER_MAX_WEAPONS);
        CHECK(CHARACTERS[c].ability_lines[0] != NULL);
        /* Only the cowgirl makes zombies drop chests. */
        CHECK(character_drops_chests(&CHARACTERS[c]) == (c == 0));
    }
}

static void test_weapons_are_on_par(void)
{
    /* Each gun its own way, but none much stronger against the riot zombie at
     * any level: within 20% of the revolver's damage per second. */
    for (int level = 1; level <= 6; level++) {
        Progress p = {level, 0, level, level, 0};
        float base = progress_damage(&p);
        float armor = level_armor(ZOMBIE_RIOT.armor, ZOMBIE_ARMOR_PER_LEVEL, level);
        float revolver = weapon_dps(WEAPON_REVOLVER, base, armor);
        for (int w = 0; w < WEAPON_COUNT; w++) {
            if (w == WEAPON_DUAL)
                continue; /* A level's reward: stronger on purpose (below) */
            float dps = weapon_dps(w, base, armor);
            CHECK(dps > revolver * 0.8f && dps < revolver * 1.2f);
        }
    }
    CHECK(weapon_def(WEAPON_SHOTGUN)->pellets == 3 && weapon_def(WEAPON_SHOTGUN)->range > 0.0f);
    CHECK(weapon_def(WEAPON_RIFLE)->reload_time < weapon_def(WEAPON_REVOLVER)->reload_time);
}

#define KILLS 3 /* A stage's worth of riot zombies, one after another */

/* Seconds to kill KILLS riot zombies of zombie_level in a row with this gun
 * at weapon_level, pulling the trigger every step and landing every pellet:
 * the real shot timing (draw, bursts, reloads, magazines) and the real hits. */
static float time_to_kill(WeaponId id, int weapon_level, int zombie_level)
{
    const WeaponDef *w = weapon_def(id);
    Zombie zombie;
    zombie_spawn(&zombie, &ZOMBIE_RIOT, 0.0f);
    zombie_set_level(&zombie, zombie_level);
    Shot shot;
    shot_reset(&shot);
    shot_set_reload(&shot, w->reload_time);
    shot_set_burst(&shot, w->burst, w->burst_gap, w->automatic);
    shot_set_magazine(&shot, w->magazine, w->magazine_reload, -1);
    int kills = 0;
    for (int step = 0; step < 20000; step++) {
        shot_start(&shot);
        if (!shot_update(&shot, FIXED_DT))
            continue;
        for (int p = 0; p < w->pellets; p++)
            zombie_hit_through(&zombie, weapon_damage(weapon_level) * w->damage_mult, w->armor_share);
        if (zombie_alive(&zombie))
            continue;
        if (++kills == KILLS)
            return (float)step * FIXED_DT;
        zombie_spawn(&zombie, &ZOMBIE_RIOT, 0.0f); /* The next one, right away */
        zombie_set_level(&zombie, zombie_level);
    }
    return 1e9f;
}

static void test_guns_kill_about_as_fast(void)
{
    /* Against the riot zombie, at every weapon level and with the zombie up to
     * 2 levels either side (weapon upgrades will open that gap): on average
     * within 10% of the revolver, and never off by more than 25% (whole
     * shots make some steps). */
    for (int id = 0; id < WEAPON_COUNT; id++) {
        if (id == WEAPON_DUAL)
            continue;
        float sum = 0.0f;
        int n = 0;
        for (int wl = 1; wl <= 8; wl++)
            for (int zl = wl - 2; zl <= wl + 2; zl++) {
                if (zl < 1)
                    continue;
                float ratio = time_to_kill(id, wl, zl) / time_to_kill(WEAPON_REVOLVER, wl, zl);
                CHECK(ratio > 0.75f && ratio < 1.25f);
                sum += ratio;
                n++;
            }
        CHECK(sum / (float)n > 0.9f && sum / (float)n < 1.1f);
    }
}

static void test_dual_pistols_are_a_reward(void)
{
    /* The cowgirl's level-3 guns: faster than her single cannon, by 10% to
     * 50% on average, never slower, at the levels she has them. */
    float sum = 0.0f;
    int n = 0;
    for (int wl = POWER_LEVEL; wl <= 8; wl++)
        for (int zl = wl - 2; zl <= wl + 2; zl++) {
            float speedup = time_to_kill(WEAPON_REVOLVER, wl, zl) / time_to_kill(WEAPON_DUAL, wl, zl);
            CHECK(speedup >= 1.0f);
            sum += speedup;
            n++;
        }
    printf("    duales: %.2fx el revolver\n", sum / (float)n);
    CHECK(sum / (float)n > 1.1f && sum / (float)n < 1.5f);
}

static void test_armor_by_character(void)
{
    /* The SWAT is the armored one and gains the most each level; the cowgirl
     * the least (her guns are her strength). Everyone's grows with level. */
    const CharacterDef *cowgirl = &CHARACTERS[0], *swat = &CHARACTERS[1];
    for (int level = 1; level <= 10; level++) {
        CHECK(character_armor(swat, level) > character_armor(cowgirl, level));
        for (int c = 0; c < CHARACTER_COUNT; c++)
            CHECK(character_armor(&CHARACTERS[c], level + 1) > character_armor(&CHARACTERS[c], level));
    }
    CHECK(swat->armor_per_level > cowgirl->armor_per_level);
}

static void test_select_wraps_and_confirms(void)
{
    CharSelect select;
    char_select_init(&select, 0);
    InputState input;
    input_init(&input);
    input.pressed[ACTION_LEFT] = true;
    CHECK(char_select_update(&select, &input) == -1 && select.selected == CHARACTER_COUNT - 1);
    input.pressed[ACTION_LEFT] = false;
    input.pressed[ACTION_RIGHT] = true;
    char_select_update(&select, &input);
    CHECK(select.selected == 0);
    input.pressed[ACTION_RIGHT] = false;
    input.pressed[ACTION_CONFIRM] = true;
    CHECK(char_select_update(&select, &input) == 0);
    char_select_init(&select, 99);
    CHECK(select.selected == 0);
}

static void test_each_weapon_has_its_own_sound(void)
{
    const WeaponDef *cowgirl = weapon_def(WEAPON_REVOLVER);
    CHECK(strcmp(cowgirl->shot_sound, "player/shot") == 0);
    CHECK(strcmp(cowgirl->cycle_sound, "player/reload") == 0);
    for (int id = 0; id < WEAPON_COUNT; id++) {
        const WeaponDef *w = weapon_def((WeaponId)id);
        CHECK(w->shot_sound && w->reload_sound && w->empty_sound && w->melee_sound);
        if (id != WEAPON_REVOLVER) {
            CHECK(strcmp(w->shot_sound, cowgirl->shot_sound) != 0);
            CHECK(strcmp(w->reload_sound, cowgirl->reload_sound) != 0);
        }
        for (int other = id + 1; other < WEAPON_COUNT; other++) {
            const WeaponDef *next = weapon_def((WeaponId)other);
            CHECK(strcmp(w->shot_sound, next->shot_sound) != 0);
            CHECK(strcmp(w->reload_sound, next->reload_sound) != 0);
            CHECK(strcmp(w->empty_sound, next->empty_sound) != 0);
            CHECK(strcmp(w->melee_sound, next->melee_sound) != 0);
        }
    }
    const WeaponDef *shotgun = weapon_def(WEAPON_SHOTGUN);
    CHECK(shotgun->cycle_sound && strcmp(shotgun->cycle_sound, shotgun->reload_sound) != 0);
}

int main(void)
{
    printf("test_characters\n");
    RUN(test_three_characters_with_their_abilities);
    RUN(test_weapons_are_on_par);
    RUN(test_guns_kill_about_as_fast);
    RUN(test_dual_pistols_are_a_reward);
    RUN(test_armor_by_character);
    RUN(test_select_wraps_and_confirms);
    RUN(test_each_weapon_has_its_own_sound);
    return TEST_EXIT();
}
