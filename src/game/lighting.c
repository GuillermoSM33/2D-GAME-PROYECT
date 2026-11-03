#include "game/lighting.h"

#include <math.h>
#include <string.h>

#include "config.h"

static float clamp01(float value)
{
    return value < 0.0f ? 0.0f : value > 1.0f ? 1.0f : value;
}

static void add_light(Lighting *lighting, WorldLight light, float camera_x)
{
    if (lighting->count >= LIGHTING_MAX || light.strength <= 0.0f ||
        light.x + light.radius < camera_x || light.x - light.radius > camera_x + VIEW_WIDTH)
        return;
    lighting->lights[lighting->count++] = light;
}

void lighting_build(Lighting *lighting, const Terrain *terrain, const Effects *effects,
                    const Player *player, bool night, bool flashlight, float camera_x, double time)
{
    memset(lighting, 0, sizeof(*lighting));
    lighting->night = night;
    if (terrain) {
        for (int i = 0; i < terrain->count; i++) {
            const Piece *piece = &terrain->items[i];
            if (terrain_blocks(piece) && lighting->block_count < LIGHTING_MAX &&
                piece->x > camera_x - 650.0f && piece->x < camera_x + VIEW_WIDTH + 650.0f) {
                float half = terrain_half_width(piece->kind);
                lighting->blocks[lighting->block_count++] = (LightBlock){
                    piece->x - half, piece->x + half,
                    BASELINE - (piece->kind == TERRAIN_BARRICADE ? BARRICADE_TOP
                                                               : WALL_FRAME_H * SPRITE_SCALE),
                    BASELINE,
                };
            }
            if (piece->spent)
                continue;
            bool lamp = piece->kind == TERRAIN_LAMP;
            bool flame = piece->kind == TERRAIN_FIRE || piece->kind == TERRAIN_CAMPFIRE;
            if (!lamp && !flame)
                continue;
            float flicker = 0.94f + 0.035f * (float)sin(time * 7.0 + piece->x * .01) +
                            0.025f * (float)sin(time * 13.0 + piece->x * .03);
            WorldLight light = {
                .kind = lamp ? LIGHT_LANTERN : LIGHT_FLAME, .x = piece->x,
                .y = lamp ? BASELINE - (LAMP_FRAME_H - 8) * SPRITE_SCALE
                          : BASELINE - (piece->kind == TERRAIN_CAMPFIRE ? 44.0f : 18.0f),
                .radius = lamp ? LAMP_LIGHT * 1.35f : FIRE_LIGHT * .88f,
                .strength = (lamp ? .95f : .82f) * flicker,
            };
            add_light(lighting, light, camera_x);
        }
    }
    if (effects) {
        for (int i = 0; i < EFFECT_MAX; i++) {
            const Effect *effect = &effects->items[i];
            if (!effect->active || !effect->anim.def ||
                strcmp(effect->anim.def->sheet, "sprites/effects/explosion") != 0)
                continue;
            const AnimationDef *def = effect->anim.def;
            float progress = clamp01((effect->anim.frame + effect->anim.time * def->fps -
                                     floorf(effect->anim.time * def->fps)) / (float)def->frame_count);
            WorldLight light = {
                .kind = LIGHT_EXPLOSION, .x = effect->x, .y = effect->y - 70.0f,
                .radius = 480.0f - 150.0f * progress,
                .strength = 1.65f * (1.0f - progress) * (1.0f - progress),
            };
            add_light(lighting, light, camera_x);
        }
    }
    if (night && flashlight && player && player_alive(player)) {
        WorldLight light = {.kind = LIGHT_FLASHLIGHT, .radius = 610.0f, .strength = .88f,
                            .direction = player->facing};
        /* A small hand-held light sits alongside the weapon, not at the
         * character's feet or behind the head. */
        light.x = player->x + player->facing * 48.0f;
        light.y = BASELINE - player->jump.height - 130.0f;
        add_light(lighting, light, camera_x);
    }
}

/* Segment against the interior of an opaque structure. Samples on the
 * visible front face still receive light; a ray continuing through it does not. */
static bool blocked(const Lighting *lighting, float x0, float y0, float x1, float y1)
{
    float dx = x1 - x0, dy = y1 - y0;
    for (int i = 0; i < lighting->block_count; i++) {
        const LightBlock *block = &lighting->blocks[i];
        float enter = 0.0f, leave = 1.0f;
        const float starts[] = {x0, y0}, delta[] = {dx, dy};
        const float lo[] = {block->left, block->top}, hi[] = {block->right, block->bottom};
        bool misses = false;
        for (int axis = 0; axis < 2; axis++) {
            if (fabsf(delta[axis]) < .0001f) {
                if (starts[axis] < lo[axis] || starts[axis] > hi[axis])
                    misses = true;
            } else {
                float a = (lo[axis] - starts[axis]) / delta[axis];
                float b = (hi[axis] - starts[axis]) / delta[axis];
                if (a > b) { float swap = a; a = b; b = swap; }
                enter = fmaxf(enter, a);
                leave = fminf(leave, b);
            }
        }
        if (!misses && enter < leave && enter > .003f && leave < .995f)
            return true;
    }
    return false;
}

float lighting_strength_at(const Lighting *lighting, const WorldLight *light, float x, float y)
{
    if (!lighting || !light || light->radius <= 0.0f)
        return 0.0f;
    float dx = x - light->x, dy = y - light->y;
    float distance = (dx * dx + dy * dy) / (light->radius * light->radius);
    if (distance >= 1.0f)
        return 0.0f;
    float angular = 1.0f;
    if (light->kind == LIGHT_FLASHLIGHT) {
        float forward = dx * light->direction * .958f + dy * .287f;
        float sideways = fabsf(dy * .958f - dx * light->direction * .287f);
        if (forward <= 0.0f)
            return 0.0f;
        angular = clamp01(1.0f - sideways / (14.0f + forward * .43f));
        angular *= angular;
    }
    if (blocked(lighting, light->x, light->y, x, y))
        return 0.0f;
    float edge = 1.0f - distance;
    return light->strength * edge * edge / (1.0f + 4.0f * distance) * angular;
}

unsigned lighting_color_at(const Lighting *lighting, float x, float y)
{
    if (!lighting || !lighting->night)
        return 0xffffff;
    float r = .67f, g = .66f, b = .73f;
    for (int i = 0; i < lighting->count; i++) {
        const WorldLight *light = &lighting->lights[i];
        float strength = lighting_strength_at(lighting, light, x, y);
        r += strength * .76f;
        g += strength * (light->kind == LIGHT_FLASHLIGHT ? .64f : .47f);
        b += strength * (light->kind == LIGHT_FLASHLIGHT ? .44f : .22f);
    }
    return ((unsigned)lroundf(clamp01(r) * 255.0f) << 16) |
           ((unsigned)lroundf(clamp01(g) * 255.0f) << 8) |
           (unsigned)lroundf(clamp01(b) * 255.0f);
}

bool lighting_ground_shadow(const WorldLight *light, float foot_x, float height,
                            float half_width, GroundShadow *shadow)
{
    if (!light || !shadow || height <= 0.0f || half_width <= 0.0f)
        return false;
    float gap = foot_x - light->x;
    float reach = fabsf(gap) / fmaxf(1.0f, light->radius);
    if (reach >= 1.0f || light->strength <= 0.0f)
        return false;
    float source_height = fmaxf(24.0f, BASELINE - light->y);
    float length = fminf(240.0f, height * (40.0f + fabsf(gap)) / source_height);
    float direction = gap < 0.0f ? -1.0f : 1.0f;
    *shadow = (GroundShadow){
        .near_x = foot_x, .far_x = foot_x + direction * length,
        .half_width = half_width, .far_half_width = half_width * (1.0f + length / 220.0f),
        .depth = 7.0f + length * .055f,
        .opacity = fminf(.48f, light->strength * .34f) * (1.0f - reach) * (1.0f - reach),
    };
    return shadow->opacity > .025f;
}
