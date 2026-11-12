#include "game/world.h"

#include <math.h>
#include <stdint.h>
#include <string.h>

/* Salts keep each random choice independent of the others. */
enum { SALT_DECOR = 1, SALT_GRASS_COUNT, SALT_GRASS };

#define DECOR_CHANCE 0.55f /* Per slot of a chunk: one big prop (cactus, fence, tree...) */
#define DECOR_OVERLAP 0.7f /* Two big props may share this much of their frames' empty edges */
#define GRASS_MIN 2        /* Grass tufts scattered over every chunk */
#define GRASS_MAX 6

static uint32_t hash32(uint32_t x)
{
    /* lowbias32: cheap, well mixed, and the same on every platform. */
    x ^= x >> 16;
    x *= 0x7feb352dU;
    x ^= x >> 15;
    x *= 0x846ca68bU;
    x ^= x >> 16;
    return x;
}

/* Deterministic value in [0, 1) for (n, salt, k). */
static float rand01(int n, int salt, int k)
{
    uint32_t h = hash32(WORLD_SEED ^ hash32((uint32_t)n * 2654435761U ^ hash32((uint32_t)salt * 97U + (uint32_t)k)));
    return (float)(h >> 8) / 16777216.0f;
}

static void add_prop(Chunk *chunk, PropKind kind, float pick, float x)
{
    if (chunk->prop_count >= WORLD_MAX_PROPS)
        return;
    int variant = (int)(pick * (float)prop_def(kind)->variants);
    chunk->props[chunk->prop_count++] = (Prop){kind, variant, x};
}

/* A prop kind drawn by the theme's weights, or -1 if it has none. */
static int pick_kind(const ThemeDef *theme, float r)
{
    int total = 0;
    for (int k = 0; k < PROP_KIND_COUNT; k++)
        total += theme->prop_weights[k];
    if (total <= 0)
        return -1;
    int target = (int)(r * (float)total);
    for (int k = 0; k < PROP_KIND_COUNT; k++) {
        target -= theme->prop_weights[k];
        if (target < 0)
            return k;
    }
    return -1;
}

void chunk_generate(Chunk *chunk, int index, const ThemeDef *theme)
{
    memset(chunk, 0, sizeof(*chunk));
    chunk->loaded = true;
    chunk->index = index;

    /* Big props first, one chance per slot, somewhere in it. They keep clear
     * of the chunk's edges by half their width, so none overlaps the next
     * chunk's (and culling by chunk never cuts one), and of each other: one
     * that would stand on another is left out. */
    float slot_w = (float)WORLD_CHUNK_W / WORLD_BIG_SLOTS;
    for (int slot = 0; slot < WORLD_BIG_SLOTS; slot++) {
        if (rand01(index, SALT_DECOR, slot * 4) >= DECOR_CHANCE)
            continue;
        int kind = pick_kind(theme, rand01(index, SALT_DECOR, slot * 4 + 1));
        if (kind < 0)
            continue;
        float half_w = (float)(prop_def(kind)->frame_w * SPRITE_SCALE) / 2.0f;
        float x = ((float)slot + rand01(index, SALT_DECOR, slot * 4 + 2)) * slot_w;
        x = fminf((float)WORLD_CHUNK_W - half_w, fmaxf(half_w, x));
        bool clear = true;
        for (int p = 0; p < chunk->prop_count; p++) {
            float other = (float)(prop_def(chunk->props[p].kind)->frame_w * SPRITE_SCALE) / 2.0f;
            if (fabsf(chunk->props[p].x - x) < (half_w + other) * DECOR_OVERLAP)
                clear = false;
        }
        if (clear)
            add_prop(chunk, kind, rand01(index, SALT_DECOR, slot * 4 + 3), x);
    }

    int tufts = GRASS_MIN + (int)(rand01(index, SALT_GRASS_COUNT, 0) * (GRASS_MAX - GRASS_MIN + 1));
    PropKind tuft = theme->city ? PROP_LITTER : PROP_GRASS; /* No grass on asphalt */
    float half_w = (float)(prop_def(tuft)->frame_w * SPRITE_SCALE) / 2.0f;
    for (int g = 0; g < tufts; g++) {
        float x = half_w + rand01(index, SALT_GRASS, g * 2) * (WORLD_CHUNK_W - 2.0f * half_w);
        add_prop(chunk, tuft, rand01(index, SALT_GRASS, g * 2 + 1), x);
    }
}

void world_init(World *world, const ThemeDef *theme)
{
    memset(world, 0, sizeof(*world));
    world->theme = theme;
    world->ground.chunk_count = (int)ceilf(WORLD_WIDTH / WORLD_CHUNK_W);
}

void layer_visible(const ChunkLayer *layer, float camera_left, int *first, int *last)
{
    int a = (int)floorf(camera_left / WORLD_CHUNK_W) - WORLD_LOAD_MARGIN;
    int b = (int)floorf((camera_left + VIEW_WIDTH - 1.0f) / WORLD_CHUNK_W) + WORLD_LOAD_MARGIN;
    *first = a < 0 ? 0 : a;
    *last = b >= layer->chunk_count ? layer->chunk_count - 1 : b;
}

const Chunk *layer_chunk(const ChunkLayer *layer, int index)
{
    for (int i = 0; i < WORLD_CACHE_CHUNKS; i++) {
        if (layer->slots[i].loaded && layer->slots[i].index == index)
            return &layer->slots[i];
    }
    return NULL;
}

int layer_loaded_count(const ChunkLayer *layer)
{
    int count = 0;
    for (int i = 0; i < WORLD_CACHE_CHUNKS; i++)
        count += layer->slots[i].loaded;
    return count;
}

void world_stream(World *world, float camera_left)
{
    ChunkLayer *layer = &world->ground;
    int first, last;
    layer_visible(layer, camera_left, &first, &last);
    /* Drop what fell out of range first, so its slot can be reused. */
    for (int i = 0; i < WORLD_CACHE_CHUNKS; i++) {
        Chunk *chunk = &layer->slots[i];
        if (chunk->loaded && (chunk->index < first || chunk->index > last))
            chunk->loaded = false;
    }
    for (int index = first; index <= last; index++) {
        if (layer_chunk(layer, index))
            continue;
        for (int i = 0; i < WORLD_CACHE_CHUNKS; i++) {
            if (!layer->slots[i].loaded) {
                chunk_generate(&layer->slots[i], index, world->theme);
                layer->loads++;
                break;
            }
        }
    }
}
