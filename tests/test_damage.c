#include "config.h"
#include "game/damage.h"
#include "test.h"

static void test_weapon_levels(void)
{
    CHECK_NEAR(weapon_damage(1), 30.0f, 1e-4f);
    CHECK_NEAR(weapon_damage(2), 48.0f, 1e-4f); /* 30 + 30 * 0.6 */
    CHECK_NEAR(weapon_damage(3), 66.0f, 1e-4f);
    CHECK_NEAR(weapon_damage(0), weapon_damage(1), 1e-6f);
}

static void test_armor_reduction(void)
{
    CHECK(damage_after_armor(20.0f, 0.0f) == 20);
    CHECK(damage_after_armor(20.0f, 80.0f) == 11);  /* 20 * 100 / 180 */
    CHECK(damage_after_armor(32.0f, 80.0f) == 18);
    CHECK(damage_after_armor(20.0f, 100.0f) == 10); /* 100 armor halves it */
}

static void test_never_immune(void)
{
    CHECK(damage_after_armor(1.0f, 10000.0f) == 1);
    CHECK(damage_after_armor(20.0f, -50.0f) == 20); /* Negative armor is ignored */
}

int main(void)
{
    printf("test_damage\n");
    RUN(test_weapon_levels);
    RUN(test_armor_reduction);
    RUN(test_never_immune);
    return TEST_EXIT();
}
