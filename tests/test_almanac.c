#include <limits.h>
#include <math.h>
#include <string.h>

#include "game/almanac.h"
#include "test.h"

static void test_variants_and_unknown_data(void)
{
    Almanac book;
    almanac_init(&book);
    CHECK(almanac_count(&book) == 0);
    for (int k = 0; k < ZOMBIE_KIND_COUNT; k++) {
        for (int runner = 0; runner < 2; runner++) {
            int index = almanac_index((ZombieKind)k, runner != 0);
            CHECK(almanac_kind(index) == (ZombieKind)k);
            CHECK(almanac_runner(index) == (runner != 0));
            AlmanacStats stats = {.health = 999};
            CHECK(!almanac_stats_at(&book, index, true, &stats));
            CHECK(stats.health == 0 && stats.armor == 0.0f && stats.damage == 0.0f);
            CHECK(!almanac_record_kill(&book, (ZombieKind)k, runner != 0));
            CHECK(almanac_discover(&book, (ZombieKind)k, runner != 0, 3));
            CHECK(!almanac_discover(&book, (ZombieKind)k, runner != 0, 1));
            CHECK(almanac_entry(&book, index)->seen == 2);
            CHECK(almanac_entry(&book, index)->max_level == 3);
        }
    }
    CHECK(almanac_count(&book) == ALMANAC_ENTRIES);
    CHECK(almanac_index(ZOMBIE_KIND_COUNT, false) == -1);
    CHECK(almanac_kind(-1) == ZOMBIE_KIND_COUNT);
    CHECK(almanac_entry(&book, ALMANAC_ENTRIES) == NULL);
    CHECK(!almanac_discover(&book, (ZombieKind)-1, false, 1));
}

static void test_discovery_requires_a_living_visible_encounter(void)
{
    Almanac book;
    AlmanacEncounter encounter;
    Zombie z[6];
    almanac_init(&book);
    almanac_encounter_start(&encounter);
    for (int i = 0; i < 6; i++)
        zombie_spawn(&z[i], zombie_stats((ZombieKind)i, false), 200.0f);
    z[0].awake = false;
    z[1].hidden = true;
    z[2].state = ZOMBIE_DEAD;
    z[3].x = -500.0f;
    z[4].x = 5000.0f;
    CHECK(almanac_observe(&book, &encounter, z, 6, 0.0f, VIEW_WIDTH) == 1);
    CHECK(almanac_count(&book) == 1);
    CHECK(almanac_entry(&book, almanac_index((ZombieKind)5, false))->seen == 1);
    for (int frame = 0; frame < 60; frame++)
        CHECK(almanac_observe(&book, &encounter, z, 6, 0.0f, VIEW_WIDTH) == 0);
    CHECK(almanac_entry(&book, almanac_index((ZombieKind)5, false))->seen == 1);
    z[0].awake = true;
    z[1].hidden = false;
    CHECK(almanac_observe(&book, &encounter, z, 6, 0.0f, VIEW_WIDTH) == 2);
    CHECK(almanac_count(&book) == 3);
    CHECK(!almanac_entry(&book, almanac_index((ZombieKind)2, false))->discovered);
}

static void test_unique_kills_and_stage_retry_preserve_book(void)
{
    Almanac book;
    AlmanacEncounter encounter;
    Zombie z[2];
    almanac_init(&book);
    almanac_encounter_start(&encounter);
    zombie_spawn(&z[0], zombie_stats(ZOMBIE_KIND_SOLDIER, false), 200.0f);
    zombie_spawn(&z[1], zombie_stats(ZOMBIE_KIND_SOLDIER, true), 400.0f);
    CHECK(almanac_observe(&book, &encounter, z, 2, 0.0f, VIEW_WIDTH) == 2);
    int index = almanac_index(ZOMBIE_KIND_SOLDIER, false);
    zombie_set_level(&z[0], 5);
    CHECK(almanac_observe(&book, &encounter, z, 2, 0.0f, VIEW_WIDTH) == 0);
    CHECK(book.entries[index].max_level == 5 && book.entries[index].seen == 1);
    z[0].state = ZOMBIE_DEAD;
    z[0].x = 10000.0f; /* Previously observed deaths still count off screen. */
    for (int frame = 0; frame < 60; frame++)
        almanac_observe(&book, &encounter, z, 2, 0.0f, VIEW_WIDTH);
    CHECK(book.entries[index].defeated == 1);
    CHECK(book.entries[index + 1].defeated == 0);
    almanac_encounter_start(&encounter);
    zombie_spawn(&z[0], zombie_stats(ZOMBIE_KIND_SOLDIER, false), 200.0f);
    CHECK(almanac_observe(&book, &encounter, z, 2, 0.0f, VIEW_WIDTH) == 0);
    CHECK(book.entries[index].seen == 2);
    CHECK(book.entries[index].max_level == 5 && book.entries[index].defeated == 1);
    CHECK(almanac_count(&book) == 2);
}

static void test_stats_match_game_and_counters_saturate(void)
{
    Almanac book;
    almanac_init(&book);
    for (int k = 0; k < ZOMBIE_KIND_COUNT; k++) {
        for (int runner = 0; runner < 2; runner++) {
            almanac_discover(&book, (ZombieKind)k, runner != 0, 7);
            int index = almanac_index((ZombieKind)k, runner != 0);
            AlmanacStats actual;
            for (int observed = 0; observed < 2; observed++) {
                Zombie reference;
                zombie_spawn(&reference, zombie_stats((ZombieKind)k, runner != 0), 0.0f);
                zombie_set_level(&reference, observed ? 7 : 1);
                CHECK(almanac_stats_at(&book, index, observed != 0, &actual));
                CHECK(actual.health == reference.max_health && actual.level == reference.level);
                CHECK_NEAR(actual.armor, reference.armor, 0.001f);
                CHECK_NEAR(actual.damage, zombie_attack_damage(&reference), 0.001f);
                CHECK_NEAR(actual.speed, reference.stats->speed * ZOMBIE_SPEED, 0.001f);
            }
        }
    }
    book.entries[0].seen = book.entries[0].defeated = INT_MAX;
    almanac_discover(&book, ZOMBIE_KIND_RIOT, false, INT_MAX);
    almanac_record_kill(&book, ZOMBIE_KIND_RIOT, false);
    CHECK(book.entries[0].seen == INT_MAX && book.entries[0].defeated == INT_MAX);
    CHECK(book.entries[0].max_level == MAX_LEVEL);
}

static void test_view_edges_level_visibility_and_reused_slot(void)
{
    Almanac book;
    AlmanacEncounter encounter;
    Zombie z;
    almanac_init(&book);
    almanac_encounter_start(&encounter);
    zombie_spawn(&z, zombie_stats(ZOMBIE_KIND_DOG, true), 0.0f);
    float half = zombie_body_half_width(&z);
    z.x = -half - 1.0f;
    CHECK(almanac_observe(&book, &encounter, &z, 1, 0.0f, VIEW_WIDTH) == 0);
    z.x = -half + 1.0f;
    CHECK(almanac_observe(&book, &encounter, &z, 1, 0.0f, VIEW_WIDTH) == 1);
    int index = almanac_index(ZOMBIE_KIND_DOG, true);
    z.x = 10000.0f;
    zombie_set_level(&z, 10);
    almanac_observe(&book, &encounter, &z, 1, 0.0f, VIEW_WIDTH);
    CHECK(book.entries[index].max_level == 1);
    z.x = 200.0f;
    almanac_observe(&book, &encounter, &z, 1, 0.0f, VIEW_WIDTH);
    CHECK(book.entries[index].max_level == 10 && book.entries[index].seen == 1);
    z.state = ZOMBIE_DEAD;
    almanac_observe(&book, &encounter, &z, 1, 0.0f, VIEW_WIDTH);
    zombie_spawn(&z, zombie_stats(ZOMBIE_KIND_DOG, true), 200.0f);
    CHECK(almanac_observe(&book, &encounter, &z, 1, 0.0f, VIEW_WIDTH) == 0);
    CHECK(book.entries[index].seen == 2 && book.entries[index].defeated == 1);
    CHECK(almanac_observe(&book, &encounter, &z, 1, NAN, VIEW_WIDTH) == 0);
    CHECK(almanac_observe(&book, &encounter, &z, 1, 0.0f, 0.0f) == 0);
}

static void test_navigation_pointer_pages_and_details(void)
{
    AlmanacView view;
    InputState input;
    almanac_view_init(&view);
    input_init(&input);
    input.pressed[ACTION_LEFT] = true;
    CHECK(almanac_view_update(&view, &input));
    CHECK(view.selected == ALMANAC_ENTRIES - 1);
    CHECK(view.scroll == ((ALMANAC_ENTRIES - 1) / ALMANAC_PAGE_SIZE) * ALMANAC_PAGE_SIZE);
    CHECK(almanac_pages() == (ALMANAC_ENTRIES + ALMANAC_PAGE_SIZE - 1) / ALMANAC_PAGE_SIZE);
    input_init(&input);
    input.pressed[ACTION_RIGHT] = true;
    CHECK(almanac_view_update(&view, &input));
    CHECK(view.selected == 0 && view.scroll == 0);
    CHECK(almanac_hit(&view, ALMANAC_GRID_X + 4, ALMANAC_GRID_Y + 4) == 0);
    CHECK(almanac_hit(&view, ALMANAC_GRID_X + ALMANAC_CARD_W + 2, ALMANAC_GRID_Y + 4) == -1);
    input_init(&input);
    input.pointer_clicked = true;
    input.pointer_x = ALMANAC_GRID_X + ALMANAC_CARD_W + ALMANAC_CARD_GAP + 4;
    input.pointer_y = ALMANAC_GRID_Y + 4;
    CHECK(almanac_view_update(&view, &input));
    CHECK(view.selected == 1 && view.detail);
    CHECK(almanac_hit(&view, input.pointer_x, input.pointer_y) == -1);
    input_init(&input);
    input.pressed[ACTION_QUIT] = true;
    CHECK(almanac_view_update(&view, &input));
    CHECK(!view.detail);
    CHECK(!almanac_view_update(&view, &input));
    almanac_view_select(&view, ALMANAC_ENTRIES + 100);
    CHECK(view.selected == ALMANAC_ENTRIES - 1);
    int unused = ALMANAC_ENTRIES - view.scroll;
    if (unused < ALMANAC_PAGE_SIZE) {
        int column = unused % ALMANAC_COLUMNS, row = unused / ALMANAC_COLUMNS;
        CHECK(almanac_hit(&view, ALMANAC_GRID_X + column * (ALMANAC_CARD_W + ALMANAC_CARD_GAP) + 4,
                         ALMANAC_GRID_Y + row * (ALMANAC_CARD_H + ALMANAC_CARD_GAP) + 4) == -1);
    }
    almanac_view_init(&view);
    input_init(&input);
    input.pressed[ACTION_UP] = true;
    CHECK(almanac_view_update(&view, &input));
    CHECK(view.selected % ALMANAC_COLUMNS == 0 && view.selected > 0);
    input_init(&input);
    input.pressed[ACTION_DOWN] = true;
    CHECK(almanac_view_update(&view, &input));
    CHECK(view.selected == 0);
    input_init(&input);
    input.pointer_clicked = true;
    input.pointer_x = ALMANAC_GRID_X + ALMANAC_GRID_W - 10;
    input.pointer_y = ALMANAC_PAGE_Y + 5;
    CHECK(almanac_view_update(&view, &input));
    CHECK(view.selected == ALMANAC_PAGE_SIZE && view.scroll == ALMANAC_PAGE_SIZE);
    input.pointer_x = ALMANAC_GRID_X + 10;
    CHECK(almanac_view_update(&view, &input));
    CHECK(view.selected == 0 && view.scroll == 0);
    input.pointer_x = WINDOW_WIDTH - 100;
    input.pointer_y = ALMANAC_FOOTER_Y + 5;
    CHECK(!almanac_view_update(&view, &input));
}

int main(void)
{
    RUN(test_variants_and_unknown_data);
    RUN(test_discovery_requires_a_living_visible_encounter);
    RUN(test_unique_kills_and_stage_retry_preserve_book);
    RUN(test_stats_match_game_and_counters_saturate);
    RUN(test_view_edges_level_visibility_and_reused_slot);
    RUN(test_navigation_pointer_pages_and_details);
    return TEST_EXIT();
}
