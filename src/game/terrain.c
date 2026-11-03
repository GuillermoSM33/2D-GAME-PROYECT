#include "game/terrain.h"

#include <math.h>
#include <string.h>

/* Art sizes (tools/make_terrain.py); each rests on its last row. */
static const struct {
    const char *sheet;
    int frame_w, frame_h, frames;
    int strikes; /* Claw strikes that wreck it; 0 = claws can't */
    int sink;    /* Art rows under the ground line */
} KINDS[TERRAIN_KINDS] = {
    [TERRAIN_BARRICADE] = {"sprites/terrain/barricade", BARRICADE_FRAME_W, BARRICADE_FRAME_H,
                           3 * BARRICADE_KINDS, BARRICADE_STRIKES},
    [TERRAIN_WALL] = {"sprites/terrain/wall", WALL_FRAME_W, WALL_FRAME_H, 3, WALL_STRIKES},
    [TERRAIN_BARREL] = {"sprites/terrain/barrel", BARREL_FRAME_W, BARREL_FRAME_H, 1, 0},
    [TERRAIN_DYNAMITE] = {"sprites/terrain/dynamite", DYNAMITE_FRAME_W, DYNAMITE_FRAME_H, 1, 0},
    [TERRAIN_SUPPLY] = {"sprites/terrain/supply", SUPPLY_FRAME_W, SUPPLY_FRAME_H, 2, 0},
    [TERRAIN_GOAL] = {"sprites/terrain/goal", GOAL_FRAME_W, GOAL_FRAME_H, 1, 0},
    [TERRAIN_CRATE] = {"sprites/terrain/crate", CRATE_FRAME_W, CRATE_FRAME_H, 11, 0},
    [TERRAIN_BOTTLES] = {"sprites/terrain/bottles", BOTTLES_FRAME_W, BOTTLES_FRAME_H, 4, 0},
    [TERRAIN_TRAP] = {"sprites/terrain/trap", TRAP_FRAME_W, TRAP_FRAME_H, 3, 0},
    [TERRAIN_COFFIN] = {"sprites/terrain/coffin", COFFIN_FRAME_W, COFFIN_FRAME_H, 4, 0},
    [TERRAIN_LAMP] = {"sprites/terrain/lamp", LAMP_FRAME_W, LAMP_FRAME_H, 2, 0},
    [TERRAIN_FIRE] = {"sprites/terrain/fire", FIRE_FRAME_W, FIRE_FRAME_H, 4, 0},
    [TERRAIN_BENCH] = {"sprites/terrain/bench", BENCH_FRAME_W, BENCH_FRAME_H, 1, 0},
    [TERRAIN_CAMPFIRE] = {"sprites/terrain/campfire", CAMPFIRE_FRAME_W, CAMPFIRE_FRAME_H,
                          2 * CAMPFIRE_FRAMES, 0},
    [TERRAIN_CHARGE] = {"sprites/terrain/charge", CHARGE_FRAME_W, CHARGE_FRAME_H, 2, 0},
    [TERRAIN_WIRE] = {"sprites/terrain/wire", WIRE_FRAME_W, WIRE_FRAME_H, 3, 0},
    [TERRAIN_NET] = {"sprites/terrain/net", NET_FRAME_W, NET_FRAME_H, 3, 0},
    [TERRAIN_SNARE] = {"sprites/terrain/snare", SNARE_FRAME_W, SNARE_FRAME_H, 3, 0},
    [TERRAIN_SPIKES] = {"sprites/terrain/spikes", SPIKES_FRAME_W, SPIKES_FRAME_H, 3, 0},
    [TERRAIN_RIVER] = {"sprites/terrain/river", RIVER_FRAME_W, RIVER_FRAME_H, 4, 0, RIVER_SINK},
    [TERRAIN_SIGN] = {"sprites/terrain/sign", SIGN_FRAME_W, SIGN_FRAME_H, 1, 0},
    [TERRAIN_PUDDLE] = {"sprites/terrain/puddle", PUDDLE_FRAME_W, PUDDLE_FRAME_H, 4, 0, PUDDLE_SINK},
};

/* Pivot at the bottom center of the blast, on the barrel's spot. */
static const AnimationDef ANIM_EXPLOSION = {
    .sheet = "sprites/effects/explosion", .frame_w = EXPLOSION_FRAME_W,
    .frame_h = EXPLOSION_FRAME_H, .first_frame = 0, .frame_count = EXPLOSION_FRAMES,
    .fps = EXPLOSION_FPS, .loop = false, .anchor_x = 36.0f, .ground_y = 71,
};

void terrain_clear(Terrain *terrain)
{
    memset(terrain, 0, sizeof(*terrain));
}

Piece *terrain_add(Terrain *terrain, TerrainKind kind, float x)
{
    if (terrain->count >= TERRAIN_MAX)
        return NULL;
    Piece *piece = &terrain->items[terrain->count++];
    memset(piece, 0, sizeof(*piece));
    piece->kind = kind;
    piece->x = x;
    piece->zombie = -1;
    if (kind == TERRAIN_FIRE)
        piece->timer = FIRE_TIME;
    return piece;
}

bool terrain_blocks(const Piece *piece)
{
    return (piece->kind == TERRAIN_BARRICADE || piece->kind == TERRAIN_WALL) && !piece->spent;
}

float terrain_half_width(TerrainKind kind)
{
    return (float)(KINDS[kind].frame_w * SPRITE_SCALE) / 2.0f;
}

float terrain_floor(const Terrain *terrain, float x)
{
    for (int i = 0; i < terrain->count; i++) {
        const Piece *p = &terrain->items[i];
        if (p->kind == TERRAIN_BARRICADE && !p->spent && fabsf(x - p->x) <= terrain_half_width(p->kind))
            return BARRICADE_TOP;
    }
    return 0.0f;
}

void terrain_bounds(const Terrain *terrain, float x, float height, float *min_x, float *max_x)
{
    for (int i = 0; i < terrain->count; i++) {
        const Piece *p = &terrain->items[i];
        if (!terrain_blocks(p) || (p->kind == TERRAIN_BARRICADE && height >= BARRICADE_TOP))
            continue;
        float reach = terrain_half_width(p->kind) + PLAYER_BODY_HALF_WIDTH;
        if (x <= p->x && p->x - reach < *max_x)
            *max_x = fmaxf(*min_x, fminf(*max_x, p->x - reach));
        if (x > p->x && p->x + reach > *min_x)
            *min_x = fminf(*max_x, fmaxf(*min_x, p->x + reach));
    }
}

void terrain_wall_bounds(const Terrain *terrain, float x, float *min_x, float *max_x)
{
    Terrain walls = *terrain;
    for (int i = 0; i < walls.count; i++) {
        if (walls.items[i].kind == TERRAIN_BARRICADE)
            walls.items[i].spent = true;
    }
    terrain_bounds(&walls, x, 0.0f, min_x, max_x);
}

bool terrain_barricade_ahead(const Terrain *terrain, float x, int dir)
{
    for (int i = 0; i < terrain->count; i++) {
        const Piece *p = &terrain->items[i];
        if (p->kind != TERRAIN_BARRICADE || p->spent)
            continue;
        float edge = p->x - (float)dir * (terrain_half_width(p->kind) + PLAYER_BODY_HALF_WIDTH);
        float gap = (edge - x) * (float)dir;
        if (gap >= -1.0f && gap <= VAULT_REACH)
            return true;
    }
    return false;
}

float terrain_zombie_target(const Terrain *terrain, float zombie_x, float player_x, int *blocker)
{
    *blocker = -1;
    float best = 1e9f;
    float target = player_x;
    for (int i = 0; i < terrain->count; i++) {
        const Piece *p = &terrain->items[i];
        if (!terrain_blocks(p))
            continue;
        float half = terrain_half_width(p->kind);
        bool between = (zombie_x - p->x) * (player_x - p->x) < 0.0f;
        bool under_her = p->kind == TERRAIN_BARRICADE && fabsf(player_x - p->x) <= half;
        if (!between && !under_her)
            continue;
        float gap = fabsf(zombie_x - p->x);
        if (gap >= best)
            continue;
        best = gap;
        *blocker = i;
        /* zombie_update stops ZOMBIE_REACH short of its target: aim so it
         * stands right against it, claw on it. */
        float side = zombie_x < p->x ? -1.0f : 1.0f;
        target = p->x + side * (half + BARRICADE_CLAW_GAP - ZOMBIE_REACH);
    }
    return target;
}

/* Strikes that wreck it: a barricade's kind sets it (sandbags and logs take
 * half again as many as crates, the steel barrier twice). */
static int strikes(const Piece *p)
{
    static const int SHARE[BARRICADE_KINDS] = {2, 3, 3, 4}; /* Halves */
    if (p->kind == TERRAIN_BARRICADE && p->variant >= 0 && p->variant < BARRICADE_KINDS)
        return KINDS[p->kind].strikes * SHARE[p->variant] / 2;
    return KINDS[p->kind].strikes;
}

static unsigned impact_sound(const Piece *p)
{
    switch (p->kind) {
    case TERRAIN_BARRICADE:
        return p->variant == 3 ? TERRAIN_SOUND_HIT_METAL
             : p->variant == 1 ? TERRAIN_SOUND_HIT_SAND : TERRAIN_SOUND_HIT_WOOD;
    case TERRAIN_WALL:
        return p->variant == 1 ? TERRAIN_SOUND_HIT_STONE : TERRAIN_SOUND_HIT_WOOD;
    case TERRAIN_CRATE:
    case TERRAIN_COFFIN:
    case TERRAIN_BARREL:
        return TERRAIN_SOUND_HIT_WOOD;
    case TERRAIN_WIRE:
        return TERRAIN_SOUND_HIT_WIRE;
    default:
        return 0;
    }
}

bool terrain_claw(Terrain *terrain, int index)
{
    if (index < 0 || index >= terrain->count)
        return false;
    Piece *p = &terrain->items[index];
    if (!terrain_blocks(p))
        return false;
    terrain->sound_events |= impact_sound(p);
    p->damage++;
    p->spent = p->damage >= strikes(p);
    if (p->spent)
        p->fuse = 0.0f; /* A charge on a wall clawed down falls with it */
    return p->spent;
}

static void push_event(int *list, int *count, int index)
{
    if (*count < TERRAIN_EVENTS)
        list[(*count)++] = index;
}

/* A shot or a blast on a breakable piece. */
static void strike(Terrain *terrain, int index, bool blast)
{
    Piece *p = &terrain->items[index];
    if (p->spent)
        return;
    if (!blast)
        terrain->sound_events |= impact_sound(p);
    TerrainEvents *ev = &terrain->events;
    switch (p->kind) {
    case TERRAIN_CRATE:
        p->hits = blast ? CRATE_HITS : p->hits + 1;
        if (p->hits >= CRATE_HITS) {
            p->spent = true;
            if (ev->crate_count < TERRAIN_EVENTS)
                ev->crate_blasted[ev->crate_count] = blast;
            push_event(ev->crates, &ev->crate_count, index);
        }
        break;
    case TERRAIN_BOTTLES:
        if (blast) { /* Shattered, but not by her aim: no reward */
            p->hits = BOTTLE_COUNT;
            p->spent = true;
            break;
        }
        if (++p->hits >= BOTTLE_COUNT) {
            p->spent = true;
            push_event(ev->bottles, &ev->bottle_count, index);
        }
        break;
    case TERRAIN_LAMP: /* Down it comes; the oil catches */
        p->spent = true;
        terrain_add(terrain, TERRAIN_FIRE, p->x);
        break;
    case TERRAIN_WIRE:
        p->hits = blast ? WIRE_HITS : p->hits + 1;
        p->spent = p->hits >= WIRE_HITS;
        break;
    case TERRAIN_COFFIN:
        p->hits = blast ? COFFIN_HITS : p->hits + 1;
        if (p->hits >= COFFIN_HITS)
            terrain_open_coffin(terrain, index);
        break;
    default:
        break;
    }
}

int terrain_bench_near(const Terrain *terrain, float x)
{
    for (int i = 0; i < terrain->count; i++) {
        const Piece *p = &terrain->items[i];
        if (p->kind == TERRAIN_BENCH && fabsf(x - p->x) <= BENCH_RANGE)
            return i;
    }
    return -1;
}

int terrain_bench_heal(int stage_index, int index)
{
    unsigned h = (unsigned)(stage_index * 2654435761u) ^ (unsigned)(index * 40503u + 7u);
    h ^= h >> 11;
    h *= 0x9e3779b1u;
    h ^= h >> 16;
    return BENCH_HEAL_MIN + (int)(h % (unsigned)(BENCH_HEAL_MAX - BENCH_HEAL_MIN + 1));
}

bool terrain_by_campfire(const Terrain *terrain, float x)
{
    for (int i = 0; i < terrain->count; i++) {
        const Piece *p = &terrain->items[i];
        if (p->kind == TERRAIN_CAMPFIRE && fabsf(x - p->x) <= CAMPFIRE_RANGE)
            return true;
    }
    return false;
}

int terrain_smokes(const Terrain *terrain, float *xs, int max)
{
    int n = 0;
    for (int i = 0; i < terrain->count && n < max; i++) {
        const Piece *p = &terrain->items[i];
        if ((p->kind == TERRAIN_FIRE && !p->spent) || p->kind == TERRAIN_CAMPFIRE)
            xs[n++] = p->x;
    }
    return n;
}

void terrain_open_coffin(Terrain *terrain, int index)
{
    Piece *p = &terrain->items[index];
    if (p->kind != TERRAIN_COFFIN || p->spent)
        return;
    p->spent = true;
    push_event(terrain->events.coffins, &terrain->events.coffin_count, index);
}

Loot terrain_loot(int stage_index, int index)
{
    /* A small hash of the stage and the crate: fixed, but varied along the road. */
    unsigned h = (unsigned)(stage_index * 7919 + index * 104729 + 17);
    h ^= h >> 13;
    h *= 0x5bd1e995u;
    h ^= h >> 15;
    unsigned roll = h % 100u;
    if (roll < LOOT_AMMO_CHANCE)
        return LOOT_AMMO;
    if (roll < LOOT_AMMO_CHANCE + LOOT_HEALTH_CHANCE)
        return LOOT_HEALTH;
    if (roll < LOOT_AMMO_CHANCE + LOOT_HEALTH_CHANCE + LOOT_DYNAMITE_CHANCE)
        return LOOT_DYNAMITE;
    if (roll < LOOT_AMMO_CHANCE + LOOT_HEALTH_CHANCE + LOOT_DYNAMITE_CHANCE + LOOT_WATER_CHANCE)
        return LOOT_WATER;
    return LOOT_GOLD;
}

static bool breakable(const Piece *p)
{
    return !p->spent && (p->kind == TERRAIN_CRATE || p->kind == TERRAIN_BOTTLES ||
                         p->kind == TERRAIN_LAMP || p->kind == TERRAIN_COFFIN ||
                         p->kind == TERRAIN_WIRE);
}

int terrain_shoot(Terrain *terrain, Bullets *bullets)
{
    int hits = 0;
    for (int i = 0; i < terrain->count; i++) {
        Piece *p = &terrain->items[i];
        bool wall = p->kind == TERRAIN_WALL && !p->spent;
        bool barrel = p->kind == TERRAIN_BARREL && !p->spent && !p->blowing;
        bool target = breakable(p);
        if (!wall && !barrel && !target)
            continue;
        float half = terrain_half_width(p->kind);
        float top = BASELINE - (float)(KINDS[p->kind].frame_h * SPRITE_SCALE) - BARREL_SHOT_MARGIN;
        for (int b = 0; b < BULLET_MAX; b++) {
            Bullet *bullet = &bullets->items[b];
            if (!bullet->active || (barrel && bullet->y < top))
                continue; /* Over a barrel's lid: it flies on */
            float lo = fminf(bullet->prev_x, bullet->x), hi = fmaxf(bullet->prev_x, bullet->x);
            if (hi < p->x - half || lo > p->x + half)
                continue;
            if (target && bullet->glanced == p)
                continue; /* It already glanced off this one */
            hits++;
            terrain->sound_events |= impact_sound(p);
            if (target && bullet->spec.ricochet) {
                /* The cowgirl's ricochet: it breaks through on to the next. */
                bullet->spec.ricochet = false;
                bullet->glanced = p;
                strike(terrain, i, false);
                bullet->spec.damage *= p->spent ? RICOCHET_KILL_BONUS : RICOCHET_LOSS;
                if (p->spent)
                    break;
                continue;
            }
            bullet->active = false;
            if (barrel) {
                p->blowing = true;
                break;
            }
            if (target) {
                strike(terrain, i, false);
                if (p->spent)
                    break;
            }
        }
    }
    return hits;
}

static Piece *wall_near(Terrain *terrain, float x)
{
    for (int i = 0; i < terrain->count; i++) {
        Piece *p = &terrain->items[i];
        if (p->kind == TERRAIN_WALL && !p->spent && p->fuse <= 0.0f &&
            fabsf(x - p->x) <= terrain_half_width(p->kind) + PLAYER_BODY_HALF_WIDTH + WALL_USE_RANGE)
            return p;
    }
    return NULL;
}

bool terrain_wall_near(const Terrain *terrain, float x)
{
    return wall_near((Terrain *)terrain, x) != NULL;
}

bool terrain_light_charge(Terrain *terrain, float x)
{
    Piece *p = wall_near(terrain, x);
    if (p == NULL)
        return false;
    p->fuse = CHARGE_FUSE;
    return true;
}

int terrain_melee(Terrain *terrain, float x0, float x1)
{
    int hits = 0;
    float lo = fminf(x0, x1), hi = fmaxf(x0, x1);
    for (int i = 0; i < terrain->count; i++) {
        Piece *p = &terrain->items[i];
        float half = terrain_half_width(p->kind);
        if (hi < p->x - half || lo > p->x + half)
            continue;
        if (terrain_blocks(p)) {
            terrain_claw(terrain, i);
            hits++;
        } else if (breakable(p)) {
            int blows = p->kind == TERRAIN_WIRE ? WIRE_MELEE_HITS : 1;
            for (int b = 0; b < blows; b++)
                strike(terrain, i, false);
            hits++;
        }
    }
    return hits;
}

int terrain_wire_at(const Terrain *terrain, float x, float height)
{
    if (height >= WIRE_TOP)
        return -1;
    for (int i = 0; i < terrain->count; i++) {
        const Piece *p = &terrain->items[i];
        if (p->kind == TERRAIN_WIRE && !p->spent && fabsf(x - p->x) <= terrain_half_width(p->kind))
            return i;
    }
    return -1;
}

int terrain_sink(TerrainKind kind)
{
    return KINDS[kind].sink;
}

int terrain_sign_ahead(const Terrain *terrain, float x, int dir, float range)
{
    for (int i = 0; i < terrain->count; i++) {
        const Piece *p = &terrain->items[i];
        float gap = (p->x - x) * (float)dir;
        if (p->kind == TERRAIN_SIGN && gap >= 0.0f && gap <= range)
            return p->variant;
    }
    return -1;
}

bool terrain_river_at(const Terrain *terrain, float x)
{
    for (int i = 0; i < terrain->count; i++) {
        const Piece *p = &terrain->items[i];
        /* Its banks are dry: the water starts a few art px in. */
        if (p->kind == TERRAIN_RIVER && fabsf(x - p->x) <= terrain_half_width(p->kind) - 5 * SPRITE_SCALE)
            return true;
    }
    return false;
}

bool terrain_splash(Terrain *terrain, float x)
{
    bool wet = terrain_river_at(terrain, x);
    for (int i = 0; i < terrain->count; i++) {
        Piece *p = &terrain->items[i];
        if (p->kind == TERRAIN_PUDDLE && fabsf(x - p->x) <= terrain_half_width(p->kind)) {
            p->ripple = RIPPLE_TIME;
            wet = true;
        }
    }
    return wet;
}

bool terrain_spikes_out(const Piece *piece)
{
    return piece->timer > SPIKES_REARM && piece->timer <= SPIKES_OUT + SPIKES_REARM;
}

bool terrain_wire_ahead(const Terrain *terrain, float x, int dir, float range)
{
    for (int i = 0; i < terrain->count; i++) {
        const Piece *p = &terrain->items[i];
        if (p->kind != TERRAIN_WIRE || p->spent)
            continue;
        float gap = (p->x - x) * (float)dir;
        if (gap >= -terrain_half_width(p->kind) && gap <= range)
            return true;
    }
    return false;
}

bool terrain_plant_charge(Terrain *terrain, float x)
{
    Piece *p = terrain_add(terrain, TERRAIN_CHARGE, x);
    if (p == NULL)
        return false;
    p->fuse = CHARGE_FUSE;
    return true;
}

void terrain_clear_events(Terrain *terrain)
{
    memset(&terrain->events, 0, sizeof(terrain->events));
}

unsigned terrain_take_sound_events(Terrain *terrain)
{
    unsigned events = terrain->sound_events;
    terrain->sound_events = 0;
    return events;
}

void terrain_update(Terrain *terrain, float dt)
{
    for (int i = 0; i < terrain->count; i++) {
        Piece *p = &terrain->items[i];
        if (p->kind == TERRAIN_FIRE && !p->spent) {
            p->timer -= dt;
            p->spent = p->timer <= 0.0f;
            continue;
        }
        if (p->kind == TERRAIN_CAMPFIRE) {
            p->timer = fmodf(p->timer + dt, 60.0f);
            continue;
        }
        if (p->kind == TERRAIN_RIVER || p->kind == TERRAIN_PUDDLE) {
            p->timer = fmodf(p->timer + dt, 60.0f);
            p->ripple = fmaxf(0.0f, p->ripple - dt);
            continue;
        }
        if (p->kind == TERRAIN_SPIKES) {
            p->timer = fmaxf(0.0f, p->timer - dt);
            continue;
        }
        if ((p->kind == TERRAIN_TRAP || p->kind == TERRAIN_NET || p->kind == TERRAIN_SNARE) && p->spent) {
            p->timer = fminf(p->timer + dt, 10.0f); /* Since it sprang */
            continue;
        }
        if (p->fuse <= 0.0f)
            continue;
        p->fuse -= dt;
        if (p->fuse <= 0.0f) {
            p->fuse = 0.0f;
            p->blowing = true;
        }
    }
}

int terrain_explosions(Terrain *terrain, float *xs, int max)
{
    return terrain_explosions_typed(terrain, xs, NULL, max);
}

int terrain_explosions_typed(Terrain *terrain, float *xs, TerrainKind *kinds, int max)
{
    int count = 0;
    bool more = true;
    while (more) { /* A blast sets off the barrels next to it, in the same step */
        more = false;
        for (int i = 0; i < terrain->count; i++) {
            Piece *p = &terrain->items[i];
            if (!p->blowing)
                continue;
            p->blowing = false;
            p->spent = true;
            if (count < max) {
                if (kinds)
                    kinds[count] = p->kind;
                xs[count++] = p->x;
            }
            /* Burning bits left on the ground round it, each dying out on its own. */
            for (int f = -1; f <= 1; f++) {
                Piece *fire = terrain_add(terrain, TERRAIN_FIRE, p->x + (float)f * BLAST_FIRE_SPREAD);
                if (fire)
                    fire->timer = BLAST_FIRE_TIME + 0.3f * (float)(f * f) * (f < 0 ? -1.0f : 1.0f);
            }
            for (int k = 0; k < terrain->count; k++) {
                Piece *q = &terrain->items[k];
                float gap = fabsf(q->x - p->x);
                if (q->kind == TERRAIN_BARREL && !q->spent && !q->blowing && gap <= BARREL_CHAIN_RADIUS) {
                    q->blowing = true;
                    more = true;
                } else if (terrain_blocks(q) && gap <= BARREL_RADIUS + terrain_half_width(q->kind)) {
                    q->spent = true; /* Blown apart */
                    q->fuse = 0.0f;
                } else if (breakable(q) && gap <= BARREL_RADIUS + terrain_half_width(q->kind)) {
                    strike(terrain, k, true);
                }
            }
        }
    }
    return count;
}

int terrain_take_dynamite(Terrain *terrain, float x)
{
    int taken = 0;
    for (int i = 0; i < terrain->count; i++) {
        Piece *p = &terrain->items[i];
        if (p->kind == TERRAIN_DYNAMITE && !p->spent && fabsf(x - p->x) <= PICKUP_RANGE) {
            p->spent = true;
            taken += DYNAMITE_PER_BOX;
        }
    }
    return taken;
}

bool terrain_take_supply(Terrain *terrain, float player_x)
{
    for (int i = 0; i < terrain->count; i++) {
        Piece *p = &terrain->items[i];
        if (p->kind == TERRAIN_SUPPLY && !p->spent && fabsf(player_x - p->x) <= SUPPLY_RANGE) {
            p->spent = true;
            return true;
        }
    }
    return false;
}

float terrain_goal_x(const Terrain *terrain)
{
    for (int i = 0; i < terrain->count; i++) {
        if (terrain->items[i].kind == TERRAIN_GOAL)
            return terrain->items[i].x;
    }
    return 0.0f;
}

int terrain_frame(const Piece *piece)
{
    switch (piece->kind) {
    case TERRAIN_BARRICADE: /* Three frames per kind */
        return piece->variant * 3 + (piece->spent ? 2 : piece->damage * 2 >= strikes(piece) ? 1 : 0);
    case TERRAIN_WALL:
        if (piece->spent)
            return 2;
        return piece->damage * 2 >= KINDS[piece->kind].strikes ? 1 : 0;
    case TERRAIN_WIRE:
        return piece->spent ? 2 : piece->hits > 0 ? 1 : 0;
    case TERRAIN_RIVER: /* The current, looping */
        return (int)(piece->timer * RIVER_FPS) % 4;
    case TERRAIN_PUDDLE: /* Rings while stepped in, else a shimmer */
        if (piece->ripple > 0.0f)
            return piece->ripple > RIPPLE_TIME / 2.0f ? 2 : 3;
        return (int)(piece->timer * 2.0f) % 2;
    case TERRAIN_SPIKES: /* Coming up, out, else sunk */
        if (piece->timer > SPIKES_OUT + SPIKES_REARM)
            return 1;
        return terrain_spikes_out(piece) ? 2 : 0;
    case TERRAIN_COFFIN: /* variant 1: the night's */
        return piece->variant * 2 + (piece->spent ? 1 : 0);
    case TERRAIN_SUPPLY:
    case TERRAIN_LAMP:
        return piece->spent ? 1 : 0;
    case TERRAIN_TRAP: /* Armed; springing for a moment (timer: since); sprung */
    case TERRAIN_NET:
    case TERRAIN_SNARE:
        if (!piece->spent)
            return 0;
        return piece->timer < SPRING_TIME ? 1 : 2;
    case TERRAIN_CHARGE:
        return (int)(piece->fuse * 10.0f) % 2;
    case TERRAIN_CRATE:
        /* Per loot (variant): whole, split; then the one broken frame. */
        return piece->spent ? 10 : piece->variant * 2 + (piece->hits > 0);
    case TERRAIN_BOTTLES:
        return piece->hits < BOTTLE_COUNT ? piece->hits : BOTTLE_COUNT;
    case TERRAIN_FIRE:
        return (int)(piece->timer * FIRE_FPS) % FIRE_FRAMES;
    case TERRAIN_CAMPFIRE:
        return piece->variant * CAMPFIRE_FRAMES + (int)(piece->timer * FIRE_FPS) % CAMPFIRE_FRAMES;
    default:
        return 0;
    }
}

const char *terrain_sheet(TerrainKind kind)
{
    return KINDS[kind].sheet;
}

void terrain_frame_size(TerrainKind kind, int *w, int *h, int *frames)
{
    *w = KINDS[kind].frame_w;
    *h = KINDS[kind].frame_h;
    *frames = KINDS[kind].frames;
}

const char *terrain_ruins_sheet(void)
{
    return "sprites/terrain/wall_ruins";
}

const char *terrain_facade_sheet(void)
{
    return "sprites/terrain/facades";
}

const char *terrain_door_sheet(void)
{
    return "sprites/terrain/door";
}

void terrain_grenade(Terrain *terrain, float x, float radius)
{
    for (int i = 0; i < terrain->count; i++) {
        Piece *p = &terrain->items[i];
        float gap = fabsf(p->x - x);
        if (p->kind == TERRAIN_BARREL && !p->spent && !p->blowing && gap <= BARREL_CHAIN_RADIUS)
            p->blowing = true;
        else if (breakable(p) && gap <= radius + terrain_half_width(p->kind))
            strike(terrain, i, true);
    }
}

bool terrain_stops(const Terrain *terrain, float x0, float x1, float height)
{
    float lo = fminf(x0, x1), hi = fmaxf(x0, x1);
    for (int i = 0; i < terrain->count; i++) {
        const Piece *p = &terrain->items[i];
        if (!terrain_blocks(p) || (p->kind == TERRAIN_BARRICADE && height >= BARRICADE_TOP))
            continue;
        float half = terrain_half_width(p->kind);
        if (hi >= p->x - half && lo <= p->x + half)
            return true;
    }
    return false;
}

const char *terrain_charge_sheet(void)
{
    return "sprites/terrain/charge";
}

static const AnimationDef ANIM_HEAL = {
    .sheet = "sprites/effects/heal", .frame_w = HEAL_FRAME_W, .frame_h = HEAL_FRAME_H,
    .first_frame = 0, .frame_count = HEAL_FRAMES, .fps = HEAL_FPS, .loop = false,
    .anchor_x = 31.5f, .ground_y = HEAL_FRAME_H - 1,
};

const AnimationDef *terrain_heal_effect(void)
{
    return &ANIM_HEAL;
}

const AnimationDef *terrain_explosion(void)
{
    return &ANIM_EXPLOSION;
}
