#ifndef GAME_LIGHTING_H
#define GAME_LIGHTING_H

#include <stdbool.h>

#include "game/effects.h"
#include "game/player.h"
#include "game/terrain.h"

#define LIGHTING_MAX 48

typedef enum { LIGHT_FLAME, LIGHT_LANTERN, LIGHT_EXPLOSION, LIGHT_FLASHLIGHT } LightKind;

typedef struct {
    LightKind kind;
    float x, y, radius, strength;
    int direction; /* A flashlight points with its owner; point lights use 0. */
} WorldLight;

typedef struct {
    float left, right, top, bottom;
} LightBlock;

typedef struct {
    WorldLight lights[LIGHTING_MAX];
    int count;
    bool night;
    LightBlock blocks[LIGHTING_MAX];
    int block_count;
} Lighting;

typedef struct {
    float near_x, far_x, half_width, far_half_width, depth, opacity;
} GroundShadow;

/* Collect visible, live sources at their actual height. No renderer, RNG,
 * audio or game-state mutation: lighting is purely presentation. */
void lighting_build(Lighting *lighting, const Terrain *terrain, const Effects *effects,
                    const Player *player, bool night, bool flashlight, float camera_x, double time);

float lighting_strength_at(const Lighting *lighting, const WorldLight *light, float x, float y);
unsigned lighting_color_at(const Lighting *lighting, float x, float y);

/* A ground-plane projection, pointing away from a nearby source. The
 * perspective widens and softens the far end rather than drawing a disc. */
bool lighting_ground_shadow(const WorldLight *light, float foot_x, float height,
                            float half_width, GroundShadow *shadow);

#endif
