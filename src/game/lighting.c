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
                    const Player *player, bool night, float flashlight, float camera_x, double time)
{
    memset(lighting, 0, sizeof(*lighting));
    lighting->night = night;
    lighting->time = time;
    if (terrain) {
        for (int i = 0; i < terrain->count; i++) {
            const Piece *piece = &terrain->items[i];
            if (terrain_blocks(piece) && lighting->block_count < LIGHTING_MAX &&
                piece->x > camera_x - 650.0f && piece->x < camera_x + VIEW_WIDTH + 650.0f) {
                float half = terrain_piece_half_width(piece);
                lighting->blocks[lighting->block_count++] = (LightBlock){
                    piece->x - half, piece->x + half,
                    BASELINE - (piece->kind == TERRAIN_BARRICADE ? BARRICADE_TOP
                                                               : WALL_FRAME_H * SPRITE_SCALE),
                    BASELINE,
                };
            }
            bool outpost = piece->kind == TERRAIN_OUTPOST && piece->spent; /* Its floodlight, switched on */
            bool lying = terrain_burner_burning(piece);                    /* A drum burning on its side */
            if (piece->spent && !outpost && !lying)
                continue;
            if (piece->kind == TERRAIN_OUTPOST && !outpost)
                continue;
            if (outpost) {
                /* The fixed lens uses the same cone, falloff and occlusion as
                 * her flashlight. Its light belongs to the scene, not the PNG. */
                add_light(lighting, (WorldLight){
                    .kind = LIGHT_FLASHLIGHT,
                    .x = piece->x + (OUTPOST_LIGHT_COL - OUTPOST_FRAME_W * .5f) * SPRITE_SCALE,
                    .y = (GROUND_ROW - OUTPOST_FRAME_H + OUTPOST_LIGHT_ROW + .5f) * SPRITE_SCALE,
                    .radius = OUTPOST_LIGHT_REACH, .strength = 1.05f,
                    .direction = -1, .tilt = OUTPOST_LIGHT_TILT,
                }, camera_x);
                continue;
            }
            bool lamp = piece->kind == TERRAIN_LAMP;
            bool flame = piece->kind == TERRAIN_FIRE || piece->kind == TERRAIN_CAMPFIRE ||
                         piece->kind == TERRAIN_BURNER;
            if (!lamp && !flame)
                continue;
            float flicker = 0.94f + 0.035f * (float)sin(time * 7.0 + piece->x * .01) +
                            0.025f * (float)sin(time * 13.0 + piece->x * .03);
            WorldLight light = {
                .kind = lamp ? LIGHT_LANTERN : LIGHT_FLAME,
                .x = piece->x,
                .y = lying ? BASELINE - 40.0f
                    : lamp ? BASELINE - (LAMP_FRAME_H - 8) * SPRITE_SCALE
                          : BASELINE - (piece->kind == TERRAIN_CAMPFIRE ? 44.0f
                                        : piece->kind == TERRAIN_BURNER ? 150.0f : 18.0f),
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
    if (flashlight > 0.0f && player && player_light_ready(player)) {
        /* It sways a little in the hand, and more with each step. */
        /* A shot kicks the gun up, and a blow swings it: the lens and the beam go too. */
        float kick_x, kick_y, kick;
        player_light_kick(player, &kick_x, &kick_y, &kick);
        float hum = .97f + .03f * (float)sin(time * 9.0);
        WorldLight light = {.kind = LIGHT_FLASHLIGHT, .radius = 760.0f, .strength = .95f * flashlight * hum,
                            .direction = player->facing,
                            .tilt = .012f * (float)sin(time * 1.6) + kick}; /* Level, along the barrel */
        /* From the lens on her gun. */
        float stride_x = 0.0f;
        if (player->light_dx > 0.0f && (player->state == PLAYER_WALK || player->state == PLAYER_RUN)) {
            static const int SWAT_STRIDE_X[PLAYER_WALK_FRAMES] = {0, 0, 1, 1, 0, 0, -1, -1};
            stride_x = (float)SWAT_STRIDE_X[player->anim.frame % PLAYER_WALK_FRAMES];
        }
        float lens_dx = player->light_dx > 0.0f ? player->light_dx : PLAYER_LIGHT_DX;
        light.x = player->x + (float)player->facing * (lens_dx + stride_x + kick_x) * SPRITE_SCALE;
        light.y = BASELINE - player->jump.height -
                  ((player->light_rows > 0.0f ? player->light_rows : PLAYER_LIGHT_DY) -
                   (float)(player_sunk_rows(player) + player_light_sway(player)) - kick_y) * SPRITE_SCALE;
        add_light(lighting, light, camera_x);
    }
}

float lighting_flashlight_power(bool on, float since)
{
    if (!on)
        return clamp01(1.0f - since / .1f);
    if (since < 0.0f) /* Its clip or switch not reached yet */
        return 0.0f;
    static const struct { float until, power; } STUTTER[] = {
        {.05f, .85f}, {.11f, .1f}, {.17f, .7f}, {.23f, .2f}, {.3f, .8f},
    };
    for (size_t i = 0; i < sizeof(STUTTER) / sizeof(STUTTER[0]); i++)
        if (since < STUTTER[i].until)
            return STUTTER[i].power;
    return 1.0f;
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
        float c = cosf(light->tilt), s = sinf(light->tilt);
        float forward = dx * light->direction * c + dy * s;
        float sideways = fabsf(dy * c - dx * light->direction * s);
        if (forward <= 0.0f)
            return 0.0f;
        angular = clamp01(1.0f - sideways / (14.0f + forward * .3f));
        angular = sqrtf(angular); /* Even across the cone, soft only at its edge */
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
    float r = .58f, g = .57f, b = .67f;
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
