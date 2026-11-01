#include <math.h>
#include <string.h>

#include "config.h"
#include "game/char_select.h"
#include "game/characters.h"
#include "game/progression.h"
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
        Progress p = {level, 0, level, level};
        float base = progress_damage(&p);
        float armor = level_armor(ZOMBIE_RIOT.armor, ZOMBIE_ARMOR_PER_LEVEL, level);
        float revolver = weapon_dps(WEAPON_REVOLVER, base, armor);
        for (int w = 0; w < WEAPON_COUNT; w++) {
            float dps = weapon_dps(w, base, armor);
            CHECK(dps > revolver * 0.8f && dps < revolver * 1.2f);
        }
    }
    CHECK(weapon_def(WEAPON_SHOTGUN)->pellets == 3 && weapon_def(WEAPON_SHOTGUN)->range > 0.0f);
    CHECK(weapon_def(WEAPON_RIFLE)->reload_time < weapon_def(WEAPON_REVOLVER)->reload_time);
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

int main(void)
{
    printf("test_characters\n");
    RUN(test_three_characters_with_their_abilities);
    RUN(test_weapons_are_on_par);
    RUN(test_select_wraps_and_confirms);
    return TEST_EXIT();
}
