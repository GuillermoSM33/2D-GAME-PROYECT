#ifndef GAME_WORLD_H
#define GAME_WORLD_H

#include <stdbool.h>

#include "config.h"
#include "game/props.h"
#include "game/themes.h"

/* Procedural level, streamed in chunks of WORLD_CHUNK_W px. A chunk's props
 * come only from WORLD_SEED, its index and the theme, so dropping it and
 * loading it again later gives the exact same scenery. */

typedef struct {
    PropKind kind;
    int variant; /* Frame of its sheet */
    float x;     /* Center, window px from the chunk's left edge */
} Prop;

typedef struct {
    bool loaded;
    int index; /* Chunk number along the world, from 0 */
    Prop props[WORLD_MAX_PROPS];
    int prop_count;
} Chunk;

/* A strip of chunks that scrolls with the camera. */
typedef struct {
    int chunk_count; /* Chunks needed to cover the world */
    Chunk slots[WORLD_CACHE_CHUNKS];
    int loads; /* Chunks generated so far (for tests and debugging) */
} ChunkLayer;

typedef struct {
    const ThemeDef *theme;
    ChunkLayer ground; /* Props standing on the ground line */
} World;

void world_init(World *world, const ThemeDef *theme);

/* Loads the chunks in view of a camera at camera_left (plus the margin) and
 * frees the rest. Call it every frame; it does nothing when nothing changes. */
void world_stream(World *world, float camera_left);

/* The loaded chunk with that index, or NULL. */
const Chunk *layer_chunk(const ChunkLayer *layer, int index);

/* Chunk range [*first, *last] the layer needs for that camera. */
void layer_visible(const ChunkLayer *layer, float camera_left, int *first, int *last);

int layer_loaded_count(const ChunkLayer *layer);

/* Fills a chunk from the seed and the theme: the same index always gives the
 * same chunk. */
void chunk_generate(Chunk *chunk, int index, const ThemeDef *theme);

#endif
