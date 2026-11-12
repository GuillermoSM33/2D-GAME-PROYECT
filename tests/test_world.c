#include <math.h>
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
    /* Every stage's theme: the town's props are the widest (a fallen pole, 600 px). */
    for (int s = 0; s < STAGE_COUNT; s++) {
        const ThemeDef *theme = STAGES[s].theme;
        int big = 0;
        for (int i = 0; i < WORLD_CHUNKS; i++) {
            Chunk c;
            chunk_generate(&c, i, theme);
            CHECK(c.prop_count > 0 && c.prop_count <= WORLD_MAX_PROPS); /* Grass at least */
            for (int p = 0; p < c.prop_count; p++) {
                const Prop *prop = &c.props[p];
                const PropDef *def = prop_def(prop->kind);
                float half_w = (float)(def->frame_w * SPRITE_SCALE) / 2.0f;
                /* Whole sprite inside the chunk, so culling by chunk never cuts one. */
                CHECK(prop->x - half_w >= -0.01f && prop->x + half_w <= WORLD_CHUNK_W + 0.01f);
                CHECK(prop->variant >= 0 && prop->variant < def->variants);
                bool tuft = prop->kind == PROP_GRASS || prop->kind == PROP_LITTER;
                big += !tuft;
                for (int q = 0; q < p && !tuft; q++) { /* Big props never stand on each other */
                    const Prop *other = &c.props[q];
                    if (other->kind == PROP_GRASS || other->kind == PROP_LITTER)
                        continue;
                    float reach = half_w + (float)(prop_def(other->kind)->frame_w * SPRITE_SCALE) / 2.0f;
                    CHECK(fabsf(prop->x - other->x) >= reach * 0.69f);
                }
            }
        }
        /* At most WORLD_BIG_SLOTS a chunk, a little over half of them taken. */
        CHECK(big > WORLD_CHUNKS && big < WORLD_CHUNKS * 3);
    }
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

static void test_every_theme_lights_its_scenery(void)
{
    /* The scenery is drawn once, in daylight. Each theme preserves its tonal
     * range, with haze inside it or darker. Warm/red illumination can have
     * little blue contrast: shading needs luminance contrast, not identical
     * minimum contrast in every RGB channel. */
    CHECK(!THEME_ATARDECER.fog);
    const ThemeDef *nights[] = {&THEME_CEMENTERIO, &THEME_NOCHE, &THEME_PUEBLO_FANTASMA};
    for (int t = 0; t < 3; t++)
        CHECK(nights[t]->fog && nights[t]->night);
    for (int s = 0; s < STAGE_COUNT; s++) {
        const ThemeDef *theme = STAGES[s].theme;
        const unsigned luminance_weights[] = {114, 587, 299}; /* B, G, R, /1000 */
        unsigned contrast = 0;
        for (int shift = 0; shift <= 16; shift += 8) {
            unsigned lo = (theme->prop_shadow >> shift) & 0xFF, hi = (theme->prop_light >> shift) & 0xFF;
            CHECK(hi > lo);
            contrast += (hi - lo) * luminance_weights[shift / 8];
            CHECK(((theme->haze >> shift) & 0xFF) <= hi);
        }
        CHECK(contrast >= 48 * 1000); /* Room for the art's shading in the theme's actual light */
        /* By night the scenery stays under the lights that matter. */
        unsigned red = (theme->prop_light >> 16) & 0xFF, green = (theme->prop_light >> 8) & 0xFF;
        CHECK(!theme->night || (red + green) / 2 < 150);
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
    CHECK(BACKGROUND_LAYERS[0].width * SPRITE_SCALE >= VIEW_WIDTH);
    const BackgroundLayer *ground = &BACKGROUND_LAYERS[BACKGROUND_LAYER_COUNT - 1];
    CHECK(ground->top_row == GROUND_ROW && ground->parallax == 1.0f);
    CHECK((ground->top_row + ground->height) * SPRITE_SCALE >= VIEW_HEIGHT);
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
    RUN(test_every_theme_lights_its_scenery);
    RUN(test_loads_only_what_is_in_view);
    RUN(test_walking_streams_new_side_and_drops_old);
    RUN(test_background_layers_cover_the_view);
    return TEST_EXIT();
}
