#include <string.h>

#include "config.h"
#include "game/camera.h"
#include "game/stages.h"
#include "game/world.h"
#include "test.h"

static void test_camera_follows_and_stops_at_ends(void)
{
    CHECK_NEAR(camera_left(PLAYER_START_X), PLAYER_START_X - VIEW_WIDTH * CAMERA_PLAYER_SHARE, 0.01f);
    CHECK_NEAR(camera_left(100.0f), 0.0f, 0.01f);
    CHECK_NEAR(camera_left(WORLD_WIDTH - 100.0f), WORLD_WIDTH - VIEW_WIDTH, 0.01f);
}

static void test_same_index_same_chunk(void)
{
    Chunk a, b;
    chunk_generate(&a, 57, &THEME_ATARDECER);
    chunk_generate(&b, 57, &THEME_ATARDECER);
    CHECK(memcmp(&a, &b, sizeof(a)) == 0);
    /* Neighbors differ (somewhere in the first few, at least). */
    int differ = 0;
    for (int i = 58; i < 64; i++) {
        chunk_generate(&b, i, &THEME_ATARDECER);
        differ += b.prop_count != a.prop_count || memcmp(a.props, b.props, sizeof(a.props)) != 0;
    }
    CHECK(differ > 0);
}

static void test_props_fit_their_chunk_and_sheet(void)
{
    int big = 0;
    for (int i = 0; i < 200; i++) {
        Chunk c;
        chunk_generate(&c, i, &THEME_ATARDECER);
        CHECK(c.prop_count > 0 && c.prop_count <= WORLD_MAX_PROPS); /* Grass at least */
        for (int p = 0; p < c.prop_count; p++) {
            const Prop *prop = &c.props[p];
            const PropDef *def = prop_def(prop->kind);
            float half_w = (float)(def->frame_w * SPRITE_SCALE) / 2.0f;
            /* Whole sprite inside the chunk, so culling by chunk never cuts one. */
            CHECK(prop->x - half_w >= -0.01f && prop->x + half_w <= WORLD_CHUNK_W + 0.01f);
            CHECK(prop->variant >= 0 && prop->variant < def->variants);
            big += prop->kind != PROP_GRASS;
        }
    }
    CHECK(big > 100 && big < 400); /* About 0.6 per half chunk */
}

static void test_theme_picks_its_props(void)
{
    ThemeDef only_fences = {.name = "test", .prop_weights = {[PROP_FENCE] = 1}};
    int fences = 0;
    for (int i = 0; i < 100; i++) {
        Chunk c;
        chunk_generate(&c, i, &only_fences);
        for (int p = 0; p < c.prop_count; p++) {
            CHECK(c.props[p].kind == PROP_FENCE || c.props[p].kind == PROP_GRASS);
            fences += c.props[p].kind == PROP_FENCE;
        }
    }
    CHECK(fences > 0);
    /* Graves belong to the graveyard, not to the sunset. */
    CHECK(THEME_ATARDECER.prop_weights[PROP_TOMBSTONE] == 0);
    CHECK(THEME_CEMENTERIO.prop_weights[PROP_TOMBSTONE] > THEME_CEMENTERIO.prop_weights[PROP_FENCE]);
    for (int s = 0; s < STAGE_COUNT; s++)
        CHECK(STAGES[s].theme != NULL);
    /* The landscape darkens with the stages: the boss stage has its own. */
    CHECK(STAGES[0].theme == &THEME_ATARDECER);
    CHECK(STAGES[4].theme == &THEME_PUEBLO_FANTASMA); /* The first route's end */
    CHECK(STAGES[STAGE_COUNT - 1].theme == &THEME_BASE_MILITAR); /* The second's */
    for (int s = 5; s < STAGE_COUNT; s++) /* The town: no grass, no cacti */
        CHECK(STAGES[s].theme->city && STAGES[s].theme->prop_weights[PROP_CACTUS] == 0);
}

static void test_recolors_cover_every_prop_color(void)
{
    /* The sunset keeps the props' own colors; the others swap all six. */
    const ThemeDef *themes[] = {&THEME_CEMENTERIO, &THEME_NOCHE, &THEME_PUEBLO_FANTASMA};
    const unsigned colors[] = {0x312224, 0x4f2b2a, 0x45332a, 0x5e302a, 0x6d3d1f, 0x5a4334};
    CHECK(THEME_ATARDECER.prop_recolor_count == 0 && !THEME_ATARDECER.fog);
    for (int t = 0; t < 3; t++) {
        CHECK(themes[t]->fog);
        for (int c = 0; c < 6; c++) {
            int found = 0;
            for (int k = 0; k < themes[t]->prop_recolor_count; k++)
                found += themes[t]->prop_recolor[k][0] == colors[c];
            CHECK(found == 1);
        }
    }
}

static void test_loads_only_what_is_in_view(void)
{
    World world;
    world_init(&world, &THEME_ATARDECER);
    float cam = camera_left(PLAYER_START_X);
    world_stream(&world, cam);
    int first, last;
    layer_visible(&world.ground, cam, &first, &last);
    CHECK(layer_loaded_count(&world.ground) == last - first + 1);
    CHECK(last - first + 1 <= VIEW_WIDTH / WORLD_CHUNK_W + 1 + 2 * WORLD_LOAD_MARGIN);
    for (int i = first; i <= last; i++)
        CHECK(layer_chunk(&world.ground, i) != NULL);
    CHECK(layer_chunk(&world.ground, first - 1) == NULL);
    CHECK(layer_chunk(&world.ground, last + 1) == NULL);
}

static void test_walking_streams_new_side_and_drops_old(void)
{
    World world;
    world_init(&world, &THEME_ATARDECER);
    float cam = camera_left(PLAYER_START_X);
    world_stream(&world, cam);
    int first, last;
    layer_visible(&world.ground, cam, &first, &last);
    int loads = world.ground.loads;

    /* Walk right by two chunks: two new on the right, two dropped on the left. */
    world_stream(&world, cam + 2.0f * WORLD_CHUNK_W);
    CHECK(world.ground.loads == loads + 2);
    CHECK(layer_chunk(&world.ground, last + 2) != NULL);
    CHECK(layer_chunk(&world.ground, first) == NULL);

    /* Back left: the left side is generated again, identical. */
    Chunk expected;
    chunk_generate(&expected, first, &THEME_ATARDECER);
    world_stream(&world, cam);
    const Chunk *again = layer_chunk(&world.ground, first);
    CHECK(again != NULL && memcmp(again, &expected, sizeof(expected)) == 0);
    CHECK(layer_chunk(&world.ground, last + 2) == NULL);

    /* Standing still loads nothing. */
    loads = world.ground.loads;
    world_stream(&world, cam);
    CHECK(world.ground.loads == loads);
}

static void test_background_layers_cover_the_view(void)
{
    /* Back to front, the sky from the top and the ground down to the bottom. */
    CHECK(BACKGROUND_LAYERS[0].top_row == 0 && !BACKGROUND_LAYERS[0].repeat);
    CHECK(BACKGROUND_LAYERS[0].width * SPRITE_SCALE >= WINDOW_WIDTH);
    const BackgroundLayer *ground = &BACKGROUND_LAYERS[BACKGROUND_LAYER_COUNT - 1];
    CHECK(ground->top_row == GROUND_ROW && ground->parallax == 1.0f);
    CHECK((ground->top_row + ground->height) * SPRITE_SCALE >= WINDOW_HEIGHT);
    for (int i = 1; i < BACKGROUND_LAYER_COUNT; i++) {
        CHECK(BACKGROUND_LAYERS[i].parallax > BACKGROUND_LAYERS[i - 1].parallax);
        CHECK(BACKGROUND_LAYERS[i].repeat);
    }
}

int main(void)
{
    printf("test_world\n");
    RUN(test_camera_follows_and_stops_at_ends);
    RUN(test_same_index_same_chunk);
    RUN(test_props_fit_their_chunk_and_sheet);
    RUN(test_theme_picks_its_props);
    RUN(test_recolors_cover_every_prop_color);
    RUN(test_loads_only_what_is_in_view);
    RUN(test_walking_streams_new_side_and_drops_old);
    RUN(test_background_layers_cover_the_view);
    return TEST_EXIT();
}
