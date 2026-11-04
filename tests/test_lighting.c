#include <math.h>
#include <string.h>

#include "config.h"
#include "game/lighting.h"
#include "test.h"

static const WorldLight *find_light(const Lighting *lighting, LightKind kind)
{
    for (int i = 0; i < lighting->count; i++)
        if (lighting->lights[i].kind == kind)
            return &lighting->lights[i];
    return NULL;
}

static void test_real_source_height_and_spent_lamps(void)
{
    Terrain terrain;
    Lighting lighting;
    terrain_clear(&terrain);
    terrain_add(&terrain, TERRAIN_LAMP, 200.0f);
    terrain_add(&terrain, TERRAIN_FIRE, 400.0f);
    terrain_add(&terrain, TERRAIN_CAMPFIRE, 600.0f);
    Terrain before = terrain;
    lighting_build(&lighting, &terrain, NULL, NULL, true, false, 0.0f, 3.25);
    CHECK(memcmp(&terrain, &before, sizeof(terrain)) == 0);
    CHECK(lighting.count == 3 && lighting.night);
    const WorldLight *lamp = find_light(&lighting, LIGHT_LANTERN);
    CHECK(lamp != NULL);
    if (lamp)
        CHECK_NEAR(lamp->y, BASELINE - (LAMP_FRAME_H - 8) * SPRITE_SCALE, 0.01f);
    CHECK(lighting.lights[0].y < lighting.lights[2].y);
    CHECK(lighting.lights[2].y < lighting.lights[1].y);
    CHECK(lighting.lights[1].y < BASELINE);
    terrain.items[0].spent = true;
    lighting_build(&lighting, &terrain, NULL, NULL, true, false, 0.0f, 3.25);
    CHECK(lighting.count == 2 && find_light(&lighting, LIGHT_LANTERN) == NULL);
    terrain.items[1].spent = terrain.items[2].spent = true;
    lighting_build(&lighting, &terrain, NULL, NULL, true, false, 0.0f, 3.25);
    CHECK(lighting.count == 0);
}

static void test_visible_source_culling_and_bounded_capacity(void)
{
    Terrain terrain;
    Lighting lighting;
    terrain_clear(&terrain);
    terrain_add(&terrain, TERRAIN_LAMP, -10000.0f);
    terrain_add(&terrain, TERRAIN_FIRE, 10000.0f);
    terrain_add(&terrain, TERRAIN_CAMPFIRE, 500.0f);
    lighting_build(&lighting, &terrain, NULL, NULL, true, false, 0.0f, 1.0);
    CHECK(lighting.count == 1 && lighting.lights[0].x == 500.0f);
    terrain_clear(&terrain);
    for (int i = 0; i < TERRAIN_MAX; i++)
        CHECK(terrain_add(&terrain, TERRAIN_CAMPFIRE, 100.0f + i * 3.0f) != NULL);
    lighting_build(&lighting, &terrain, NULL, NULL, true, false, 0.0f, 1.0);
    CHECK(lighting.count == LIGHTING_MAX);
    for (int i = 0; i < lighting.count; i++)
        CHECK(lighting.lights[i].strength > 0.0f && isfinite(lighting.lights[i].strength));
    terrain_clear(&terrain);
    for (int i = 0; i < TERRAIN_MAX; i++)
        terrain_add(&terrain, TERRAIN_WALL, 50.0f + i * 3.0f);
    lighting_build(&lighting, &terrain, NULL, NULL, true, false, 0.0f, 1.0);
    CHECK(lighting.block_count == LIGHTING_MAX);
    CHECK(lighting.count == 0);
}

static void test_point_falloff_is_symmetric_and_monotonic(void)
{
    Lighting lighting = {.night = true};
    WorldLight light = {.kind = LIGHT_LANTERN, .x = 500.0f, .y = 250.0f,
                        .radius = 400.0f, .strength = 1.0f};
    float center = lighting_strength_at(&lighting, &light, 500.0f, 250.0f);
    float near = lighting_strength_at(&lighting, &light, 550.0f, 250.0f);
    float middle = lighting_strength_at(&lighting, &light, 650.0f, 250.0f);
    float far = lighting_strength_at(&lighting, &light, 850.0f, 250.0f);
    CHECK(center > near && near > middle && middle > far && far > 0.0f);
    CHECK_NEAR(near, lighting_strength_at(&lighting, &light, 450.0f, 250.0f), 0.0001f);
    CHECK(lighting_strength_at(&lighting, &light, 900.0f, 250.0f) == 0.0f);
    CHECK(lighting_strength_at(&lighting, &light, 1000.0f, 250.0f) == 0.0f);
    light.radius = 0.0f;
    CHECK(lighting_strength_at(&lighting, &light, 500.0f, 250.0f) == 0.0f);
}

static void test_walls_and_barricades_block_rays_passing_through(void)
{
    const TerrainKind kinds[] = {TERRAIN_WALL, TERRAIN_BARRICADE};
    for (int k = 0; k < 2; k++) {
        Terrain terrain;
        Lighting lighting;
        terrain_clear(&terrain);
        terrain_add(&terrain, kinds[k], 400.0f);
        lighting_build(&lighting, &terrain, NULL, NULL, true, false, 0.0f, 0.0);
        CHECK(lighting.block_count == 1);
        WorldLight light = {.kind = LIGHT_LANTERN, .x = 150.0f, .y = BASELINE - 20.0f,
                            .radius = 800.0f, .strength = 1.0f};
        CHECK(lighting_strength_at(&lighting, &light, 650.0f, BASELINE - 20.0f) == 0.0f);
        light.y = lighting.blocks[0].top - 30.0f;
        CHECK(lighting_strength_at(&lighting, &light, 650.0f, light.y) > 0.0f);
        terrain.items[0].spent = true;
        lighting_build(&lighting, &terrain, NULL, NULL, true, false, 0.0f, 0.0);
        CHECK(lighting.block_count == 0);
        light.y = BASELINE - 20.0f;
        CHECK(lighting_strength_at(&lighting, &light, 650.0f, light.y) > 0.0f);
    }
}

static void test_gun_and_light_sink_with_her_in_the_river(void)
{
    Player player;
    Lighting lighting;
    player_init(&player);
    player.x = 500.0f;
    float mx, dry, deep;
    player_muzzle(&player, &mx, &dry);
    lighting_build(&lighting, NULL, NULL, &player, true, 1.0f, 0.0f, 0.0);
    float light_dry = lighting.lights[0].y;
    player.depth = 1.0f;
    player_muzzle(&player, &mx, &deep);
    lighting_build(&lighting, NULL, NULL, &player, true, 1.0f, 0.0f, 0.0);
    CHECK_NEAR(deep - dry, RIVER_DEEP_ROWS * SPRITE_SCALE, 0.01f);
    CHECK_NEAR(lighting.lights[0].y - light_dry, RIVER_DEEP_ROWS * SPRITE_SCALE, 0.01f);
}

static void test_flashlight_goes_out_in_a_jump(void)
{
    /* The jump's art has no gun in hand: no gun, no beam. */
    Player player;
    Lighting lighting;
    player_init(&player);
    player.x = 500.0f;
    lighting_build(&lighting, NULL, NULL, &player, true, 1.0f, 0.0f, 0.0);
    CHECK(lighting.count == 1);
    player.state = PLAYER_JUMP;
    player.jump.airborne = true;
    lighting_build(&lighting, NULL, NULL, &player, true, 1.0f, 0.0f, 0.0);
    CHECK(lighting.count == 0);
    player.jump.airborne = false;
    player.state = PLAYER_LAND;
    lighting_build(&lighting, NULL, NULL, &player, true, 1.0f, 0.0f, 0.0);
    CHECK(lighting.count == 0);
}

static void test_flashlight_stutters_on_and_dies_off(void)
{
    CHECK(lighting_flashlight_power(true, -.01f) == 0.0f);
    CHECK(lighting_flashlight_power(true, .08f) < .5f);
    CHECK(lighting_flashlight_power(true, .15f) > .5f);
    CHECK(lighting_flashlight_power(true, 1.0f) == 1.0f);
    CHECK(lighting_flashlight_power(false, 0.0f) == 1.0f && lighting_flashlight_power(false, 1.0f) == 0.0f);
}

static void test_flashlight_follows_facing_and_jump(void)
{
    Player player;
    Lighting lighting;
    player_init(&player);
    player.x = 500.0f;
    player.facing = FACING_RIGHT;
    lighting_build(&lighting, NULL, NULL, &player, true, true, 0.0f, 0.0);
    CHECK(lighting.count == 1);
    WorldLight right = lighting.lights[0];
    CHECK(right.kind == LIGHT_FLASHLIGHT && right.x > player.x && right.y < BASELINE);
    CHECK(lighting_strength_at(&lighting, &right, right.x + 200.0f, right.y + 60.0f) > 0.0f);
    CHECK(lighting_strength_at(&lighting, &right, right.x - 200.0f, right.y) == 0.0f);
    CHECK(lighting_strength_at(&lighting, &right, right.x + 20.0f, right.y - 180.0f) == 0.0f);
    player.jump.height = 100.0f;
    player.facing = FACING_LEFT;
    lighting_build(&lighting, NULL, NULL, &player, true, true, 0.0f, 0.0);
    WorldLight left = lighting.lights[0];
    CHECK(left.x < player.x);
    CHECK_NEAR(left.y, right.y - player.jump.height, 0.01f);
    CHECK(lighting_strength_at(&lighting, &left, left.x - 200.0f, left.y + 60.0f) > 0.0f);
    CHECK(lighting_strength_at(&lighting, &left, left.x + 200.0f, left.y) == 0.0f);
    lighting_build(&lighting, NULL, NULL, &player, false, true, 0.0f, 0.0); /* By day too, if she wants */
    CHECK(lighting.count == 1);
    lighting_build(&lighting, NULL, NULL, &player, true, false, 0.0f, 0.0);
    CHECK(lighting.count == 0);
    player.state = PLAYER_DEAD;
    lighting_build(&lighting, NULL, NULL, &player, true, true, 0.0f, 0.0);
    CHECK(lighting.count == 0);
}

static void test_explosion_flash_tracks_animation_and_expires(void)
{
    Effects effects;
    Lighting lighting;
    effects_clear(&effects);
    CHECK(effects_spawn(&effects, terrain_explosion(), 500.0f, BASELINE, 1));
    CHECK(effects_spawn(&effects, effect_sparks(), 800.0f, BASELINE, 1));
    CHECK(effects_spawn(&effects, terrain_heal_effect(), 700.0f, BASELINE, 1));
    lighting_build(&lighting, NULL, &effects, NULL, true, false, 0.0f, 0.0);
    CHECK(lighting.count == 1 && lighting.lights[0].kind == LIGHT_EXPLOSION);
    float first_strength = lighting.lights[0].strength;
    float first_radius = lighting.lights[0].radius;
    effects_update(&effects, 2.5f / EXPLOSION_FPS);
    lighting_build(&lighting, NULL, &effects, NULL, true, false, 0.0f, 0.0);
    CHECK(lighting.count == 1);
    CHECK(lighting.lights[0].strength > 0.0f && lighting.lights[0].strength < first_strength);
    CHECK(lighting.lights[0].radius < first_radius);
    float middle = lighting.lights[0].strength;
    effects_update(&effects, 3.0f / EXPLOSION_FPS);
    lighting_build(&lighting, NULL, &effects, NULL, true, false, 0.0f, 0.0);
    CHECK(lighting.count == 1 && lighting.lights[0].strength < middle);
    effects_update(&effects, 2.0f);
    lighting_build(&lighting, NULL, &effects, NULL, true, false, 0.0f, 0.0);
    CHECK(lighting.count == 0);
}

static void test_night_color_is_warm_near_sources_and_day_stays_white(void)
{
    Lighting lighting = {.night = true, .count = 1};
    lighting.lights[0] = (WorldLight){.kind = LIGHT_FLAME, .x = 500.0f, .y = 300.0f,
                                     .radius = 300.0f, .strength = 0.95f};
    unsigned ambient = lighting_color_at(&lighting, 0.0f, 0.0f);
    unsigned warm = lighting_color_at(&lighting, 500.0f, 300.0f);
    CHECK((ambient & 255u) > ((ambient >> 16) & 255u));
    CHECK(((warm >> 16) & 255u) > ((ambient >> 16) & 255u));
    CHECK(((warm >> 16) & 255u) >= ((warm >> 8) & 255u));
    CHECK(((warm >> 8) & 255u) > (warm & 255u));
    lighting.night = false;
    CHECK(lighting_color_at(&lighting, 500.0f, 300.0f) == 0xffffffu);
    CHECK(lighting_color_at(&lighting, 0.0f, 0.0f) == 0xffffffu);
}

static void test_ground_shadows_follow_source_height_and_perspective(void)
{
    WorldLight light = {.kind = LIGHT_LANTERN, .x = 300.0f, .y = BASELINE - 200.0f,
                        .radius = 700.0f, .strength = 1.0f};
    GroundShadow right, left, low;
    CHECK(lighting_ground_shadow(&light, 400.0f, 150.0f, 25.0f, &right));
    CHECK(right.near_x == 400.0f && right.far_x > right.near_x);
    CHECK(right.far_half_width > right.half_width && right.depth > 0.0f);
    CHECK(right.opacity > 0.0f && right.opacity <= 0.48f);
    CHECK(lighting_ground_shadow(&light, 200.0f, 150.0f, 25.0f, &left));
    CHECK(left.far_x < left.near_x);
    CHECK_NEAR(right.far_x - right.near_x, left.near_x - left.far_x, 0.01f);
    light.y = BASELINE - 80.0f;
    CHECK(lighting_ground_shadow(&light, 400.0f, 150.0f, 25.0f, &low));
    CHECK(low.far_x - low.near_x > right.far_x - right.near_x);
    CHECK(low.far_half_width > right.far_half_width);
    light.y = BASELINE - 5.0f;
    CHECK(lighting_ground_shadow(&light, 400.0f, 500.0f, 25.0f, &low));
    CHECK(low.far_x - low.near_x <= 240.0f);
    CHECK(!lighting_ground_shadow(&light, light.x + light.radius, 150.0f, 25.0f, &low));
    CHECK(!lighting_ground_shadow(&light, 400.0f, 0.0f, 25.0f, &low));
    CHECK(!lighting_ground_shadow(&light, 400.0f, 150.0f, 0.0f, &low));
    light.strength = 0.0f;
    CHECK(!lighting_ground_shadow(&light, 400.0f, 150.0f, 25.0f, &low));
}

int main(void)
{
    RUN(test_real_source_height_and_spent_lamps);
    RUN(test_visible_source_culling_and_bounded_capacity);
    RUN(test_point_falloff_is_symmetric_and_monotonic);
    RUN(test_walls_and_barricades_block_rays_passing_through);
    RUN(test_flashlight_follows_facing_and_jump);
    RUN(test_flashlight_stutters_on_and_dies_off);
    RUN(test_flashlight_goes_out_in_a_jump);
    RUN(test_gun_and_light_sink_with_her_in_the_river);
    RUN(test_explosion_flash_tracks_animation_and_expires);
    RUN(test_night_color_is_warm_near_sources_and_day_stays_white);
    RUN(test_ground_shadows_follow_source_height_and_perspective);
    return TEST_EXIT();
}
