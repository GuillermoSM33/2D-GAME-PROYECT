#include "game/stage_run.h"

#include <math.h>
#include <string.h>

#include "game/combat.h"
#include "game/damage.h"

void run_start(StageRun *run, int stage_index, float player_x, bool drops_chests)
{
    memset(run, 0, sizeof(*run));
    run->stage_index = stage_index;
    run->drops_chests = drops_chests;
    run->stage = &STAGES[stage_index];
    run->mission_chest = -1;
    run->holding = -1;
    run->start_x = player_x;
    run->goal_x = player_x + run->stage->length;
    terrain_clear(&run->terrain);
    for (int c = 0; c < RUN_MAX_CHESTS; c++)
        chest_clear(&run->chests[c]);

    int group = 0, campfires = 0, walls = 0, facades = (int)stage_index, barricades = 0;
    Piece *fire, *wall, *barricade;
    for (int s = 0; s < run->stage->spot_count; s++) {
        const StageSpot *spot = &run->stage->spots[s];
        float x = player_x + spot->at * run->stage->length;
        switch (spot->kind) {
        case SPOT_ZOMBIES:
        case SPOT_ELITE:
        case SPOT_COFFINS:
        case SPOT_AMBUSH:
        case SPOT_RUNNERS:
            for (int i = 0; i < spot->count && run->zombie_count < RUN_MAX_ZOMBIES; i++) {
                int k = run->zombie_count++;
                Zombie *z = &run->zombies[k];
                float spacing = spot->kind == SPOT_COFFINS   ? COFFIN_SPACING
                                : spot->kind == SPOT_RUNNERS ? ROUTE_GROUP_SPACING * 0.6f
                                                             : ROUTE_GROUP_SPACING;
                zombie_spawn(z, stage_zombie_stats(run->stage, k), x + (float)i * spacing);
                zombie_set_level(z, stage_zombie_level(run->stage, k));
                z->awake = false;
                z->just_spawned = false;
                run->group_of[k] = group;
                if (spot->kind == SPOT_AMBUSH) { /* Off the road until she gets here */
                    z->x = x + (float)i; /* In route order, all sprung at x */
                    z->hidden = true;
                    run->ambush_x[k] = x;
                    continue;
                }
                /* Shut in, standing behind its lid, more often by night; the
                 * others stand asleep in the open. A fixed roll per zombie. */
                unsigned roll = ((unsigned)stage_index * 2654435761u) ^ ((unsigned)k * 40503u + 17u);
                roll = (roll ^ (roll >> 13)) * 0x5bd1e995u;
                int chance = run->stage->theme->night ? COFFIN_CHANCE_NIGHT : COFFIN_CHANCE_DAY;
                if (spot->kind == SPOT_COFFINS && (int)((roll >> 8) % 100u) < chance) {
                    Piece *coffin = terrain_add(&run->terrain, TERRAIN_COFFIN, z->x);
                    if (coffin) { /* Hidden only with a lid to burst: never unseen in the open */
                        z->hidden = true;
                        coffin->zombie = k;
                        coffin->variant = run->stage->theme->night;
                    }
                }
            }
            group++;
            break;
        case SPOT_CRATES:
        case SPOT_TRAPS:
        case SPOT_LAMPS:
            for (int i = 0; i < spot->count; i++) {
                TerrainKind kind = spot->kind == SPOT_CRATES ? TERRAIN_CRATE
                                   : spot->kind == SPOT_TRAPS ? TERRAIN_TRAP : TERRAIN_LAMP;
                float gap = spot->kind == SPOT_CRATES ? CRATE_SPACING
                            : spot->kind == SPOT_TRAPS ? TRAP_SPACING : LAMP_SPACING;
                terrain_add(&run->terrain, kind, x + (float)i * gap);
            }
            break;
        case SPOT_BOTTLES:
            terrain_add(&run->terrain, TERRAIN_BOTTLES, x);
            break;
        case SPOT_REST:
            terrain_add(&run->terrain, TERRAIN_BENCH, x);
            fire = terrain_add(&run->terrain, TERRAIN_CAMPFIRE, x + REST_GAP);
            if (fire) /* Every other one has a pot hung over it */
                fire->variant = campfires++ % 2 == 0;
            break;
        case SPOT_BARRICADE:
            barricade = terrain_add(&run->terrain, TERRAIN_BARRICADE, x);
            if (barricade) /* Its kind, in turn along the campaign */
                barricade->variant = (barricades++ + (int)stage_index) % BARRICADE_KINDS;
            break;
        case SPOT_WIRE:
            terrain_add(&run->terrain, TERRAIN_WIRE, x);
            break;
        case SPOT_RIVER:
            terrain_add(&run->terrain, TERRAIN_RIVER, x);
            break;
        case SPOT_PUDDLES:
            for (int i = 0; i < spot->count; i++)
                terrain_add(&run->terrain, TERRAIN_PUDDLE, x + (float)i * PUDDLE_SPACING);
            break;
        case SPOT_NET:
            terrain_add(&run->terrain, TERRAIN_NET, x);
            break;
        case SPOT_SNARE:
            terrain_add(&run->terrain, TERRAIN_SNARE, x);
            break;
        case SPOT_SPIKES:
            for (int i = 0; i < spot->count; i++)
                terrain_add(&run->terrain, TERRAIN_SPIKES, x + (float)i * TRAP_SPACING);
            break;
        case SPOT_WALL:
            if (spot->count > 1) /* A barrel against it: the other way through */
                terrain_add(&run->terrain, TERRAIN_BARREL, x - WALL_BARREL_GAP);
            wall = terrain_add(&run->terrain, TERRAIN_WALL, x);
            /* Every other one is a building across the road, its door barred. */
            if (wall && walls++ % 2 == 1)
                wall->variant = 1 + facades++ % FACADE_KINDS;
            break;
        case SPOT_DYNAMITE:
            terrain_add(&run->terrain, TERRAIN_DYNAMITE, x);
            break;
        case SPOT_BARRELS:
            for (int i = 0; i < spot->count; i++)
                terrain_add(&run->terrain, TERRAIN_BARREL, x + (float)i * BARREL_FRAME_W * SPRITE_SCALE * 1.5f);
            break;
        case SPOT_SUPPLY:
            terrain_add(&run->terrain, TERRAIN_SUPPLY, x);
            break;
        }
    }
    terrain_add(&run->terrain, TERRAIN_GOAL, run->goal_x);
    /* A few traps have a warning sign before them (it says what kind). */
    int pieces = run->terrain.count;
    for (int i = 0; i < pieces; i++) {
        const Piece *p = &run->terrain.items[i];
        bool trap = p->kind == TERRAIN_TRAP || p->kind == TERRAIN_SPIKES || p->kind == TERRAIN_NET ||
                    p->kind == TERRAIN_SNARE || p->kind == TERRAIN_WIRE;
        unsigned roll = ((unsigned)stage_index * 7919u + (unsigned)i * 104729u) * 2654435761u >> 16;
        if (!trap || (int)(roll % 100u) >= SIGN_CHANCE)
            continue;
        Piece *sign = terrain_add(&run->terrain, TERRAIN_SIGN, p->x - SIGN_GAP);
        if (sign)
            sign->variant = (int)p->kind;
    }
    for (int i = 0; i < run->terrain.count; i++) { /* What each crate holds, stencilled on it */
        if (run->terrain.items[i].kind == TERRAIN_CRATE)
            run->terrain.items[i].variant = (int)terrain_loot(stage_index, i);
    }
}

/* The right edge of the group holding her: past its last zombie. */
static float group_wall(const StageRun *run, int group)
{
    float wall = 0.0f;
    for (int k = 0; k < run->zombie_count; k++) {
        if (run->group_of[k] != group)
            continue;
        wall = fmaxf(wall, run->zombies[k].x + ROUTE_LOCK_MARGIN);
        if (run->ambush_x[k] > 0.0f) /* An ambush holds her round its spot, with room to move */
            wall = fmaxf(wall, run->ambush_x[k] + AMBUSH_ROOM);
    }
    return wall;
}

/* Which group is holding her: the first woken one still alive, or -1. */
static int fighting_group(const StageRun *run)
{
    for (int k = 0; k < run->zombie_count; k++) {
        const Zombie *z = &run->zombies[k];
        if (z->awake && zombie_alive(z))
            return run->group_of[k];
    }
    return -1;
}

int run_fight_left(const StageRun *run)
{
    int group = fighting_group(run);
    int left = 0;
    for (int k = 0; k < run->zombie_count && group >= 0; k++)
        left += run->group_of[k] == group && zombie_alive(&run->zombies[k]);
    return left;
}

void run_place_player(const StageRun *run, Player *player)
{
    player->wading = terrain_river_at(&run->terrain, player->x);
    player->wind = run->stage->weather == WEATHER_WIND || run->stage->weather == WEATHER_STORM;
    player->hot = run->stage->hot;
    player->cold = run->stage->cold;
    player->cozy = terrain_by_campfire(&run->terrain, player->x);
    float min_x = -1e9f, max_x = 1e9f;
    if (run->wall_x > 0.0f)
        max_x = run->wall_x;
    max_x = fminf(max_x, run->goal_x + GOAL_FRAME_W * SPRITE_SCALE);
    if (player->vaulting) { /* Over the low ones, down to the ground past them */
        terrain_wall_bounds(&run->terrain, player->x, &min_x, &max_x);
        player_set_ground(player, 0.0f, min_x, max_x);
        return;
    }
    terrain_bounds(&run->terrain, player->x, player->jump.height, &min_x, &max_x);
    player_set_ground(player, terrain_floor(&run->terrain, player->x), min_x, max_x);
}

int run_bullets(StageRun *run, Bullets *bullets, Effects *effects)
{
    /* Walls first: nothing behind one gets hit. */
    int hits = terrain_shoot(&run->terrain, bullets);
    for (int k = 0; k < run->zombie_count; k++) {
        if (run->zombies[k].awake && !run->zombies[k].hidden) /* Asleep they are out of the fight */
            hits += combat_bullets_vs_zombie(bullets, &run->zombies[k], effects);
    }
    return hits;
}

bool run_vault(StageRun *run, Player *player)
{
    if (!terrain_barricade_ahead(&run->terrain, player->x, player->facing) || player->jump.height > 0.0f)
        return false;
    return player_vault(player);
}

static void heal(StageRun *run, Player *player, int points)
{
    int room = player->max_health - player->health;
    points = points < room ? points : room;
    if (points <= 0)
        return;
    player->health += points;
    run->healed += points;
}

bool run_sit(StageRun *run, Player *player, unsigned reload_guns)
{
    int bench = terrain_bench_near(&run->terrain, player->x);
    if (bench < 0)
        return false;
    float seat = run->terrain.items[bench].x; /* In its middle, facing the viewer */
    if (!player_sit(player, seat, reload_guns))
        return false;
    Piece *p = &run->terrain.items[bench];
    if (!p->spent) { /* Its rest heals once */
        p->spent = true;
        heal(run, player, terrain_bench_heal(run->stage_index, bench));
    }
    return true;
}

void run_melee(StageRun *run, const Player *player, const Progress *progress)
{
    float front = player->x + (float)player->facing * PLAYER_BODY_HALF_WIDTH;
    float reach = front + (float)player->facing * MELEE_REACH;
    float lo = fminf(player->x, reach), hi = fmaxf(player->x, reach);
    for (int k = 0; k < run->zombie_count; k++) {
        Zombie *z = &run->zombies[k];
        float half = ZOMBIE_HALF_WIDTH * SPRITE_SCALE;
        if (!z->awake || z->hidden || !zombie_alive(z) || z->x + half < lo || z->x - half > hi)
            continue;
        zombie_hit_through(z, progress_damage(progress) * MELEE_DAMAGE_MULT, MELEE_ARMOR_SHARE);
        z->x += (float)player->facing * MELEE_PUSH;
        run->melee_hits++;
    }
    run->melee_hits += terrain_melee(&run->terrain, front, reach);
}

/* Barbed wire: while she is in it, it bites every WIRE_BITE_EVERY (a cut,
 * bleeding, a limp), pushing her back out the way she came. */
static void snag_wire(StageRun *run, Player *player, float dt)
{
    run->wire_timer = fmaxf(0.0f, run->wire_timer - dt);
    int i = terrain_wire_at(&run->terrain, player->x, player->jump.height);
    if (i < 0 || run->wire_timer > 0.0f || !player_alive(player))
        return;
    run->wire_timer = WIRE_BITE_EVERY;
    run->wire_bit = true;
    float claw = damage_at_level(ZOMBIE_ATTACK_BASE, run->stage->zombie_level);
    player_hit(player, claw * WIRE_SELF_MULT, player->facing > 0 ? -1 : 1);
    player_bleed(player, claw * BLEED_SHARE);
}

int run_crate_gold(const StageRun *run)
{
    return GOLD_CRATE + GOLD_CRATE_PER_STAGE * run->stage_index;
}

bool run_use(StageRun *run, const Player *player)
{
    if (run->dynamite <= 0 || !player_alive(player) || player->state == PLAYER_SIT)
        return false;
    bool wall = terrain_wall_near(&run->terrain, player->x);
    if (!wall && terrain_bench_near(&run->terrain, player->x) >= 0)
        return false; /* E there sits her down */
    if (wall ? !terrain_light_charge(&run->terrain, player->x) : !terrain_plant_charge(&run->terrain, player->x))
        return false;
    run->dynamite--;
    run->charge_lit = true;
    return true;
}

static void give_xp(StageRun *run, Progress *progress, int xp)
{
    run->xp_gained += xp;
    run->levels_gained += progress_add_xp(progress, xp);
}

static void place_chest(StageRun *run, float x, int xp, bool mission)
{
    for (int c = 0; c < RUN_MAX_CHESTS; c++) {
        if (chest_present(&run->chests[c]))
            continue;
        chest_place(&run->chests[c], x, xp);
        if (mission)
            run->mission_chest = c;
        return;
    }
}

/* A zombie is down: its chest, if it leaves one, where it fell. The last one
 * leaves its own too; the mission's chest waits at the gate besides. */
static void zombie_chest(StageRun *run, int k, const Progress *progress)
{
    run->chest_done[k] = true;
    bool elite = run->zombies[k].stats == &ZOMBIE_ELITE;
    bool drop = elite || (run->drops_chests && stage_chest_after(run->stage, k));
    if (!drop)
        return;
    float share = (float)(k + 1) / (float)run->stage->zombies;
    int xp = chest_xp(progress->level, run->stage->zombie_level, run->stage->complexity, share, false);
    if (!elite)
        xp = (int)lroundf((float)xp * stage_xp_share(run->stage));
    place_chest(run, run->zombies[k].x, xp, false);
}

/* Barrels going up: bodies close by take the blast, her included. */
static void blow_up(StageRun *run, Player *player, const Progress *progress)
{
    float xs[RUN_MAX_BLASTS];
    int n = terrain_explosions(&run->terrain, xs, RUN_MAX_BLASTS);
    for (int b = 0; b < n; b++) {
        run->blast_x[run->blasts++] = xs[b];
        float damage = progress_damage(progress) * BARREL_DAMAGE_MULT;
        for (int k = 0; k < run->zombie_count; k++) {
            Zombie *z = &run->zombies[k];
            if (z->awake && fabsf(z->x - xs[b]) - ZOMBIE_HALF_WIDTH * SPRITE_SCALE <= BARREL_RADIUS)
                zombie_hit_through(z, damage, BARREL_ARMOR_SHARE);
        }
        if (fabsf(player->x - xs[b]) - PLAYER_BODY_HALF_WIDTH <= BARREL_RADIUS) {
            float claw = damage_at_level(ZOMBIE_ATTACK_BASE, run->stage->zombie_level);
            player_hit(player, claw * BARREL_SELF_MULT, player->x < xs[b] ? -1 : 1);
        }
    }
}

void run_throw(StageRun *run, const Player *player)
{
    for (int g = 0; g < RUN_MAX_GRENADES; g++) {
        Grenade *n = &run->grenades[g];
        if (n->active)
            continue;
        n->active = true;
        n->x = player->x + (float)player->facing * 30.0f;
        n->height = player->jump.height + 150.0f; /* Out of her raised hand */
        n->vx = (float)player->facing * GRENADE_SPEED_X;
        n->vy = GRENADE_SPEED_Y;
        n->fuse = GRENADE_FUSE;
        return;
    }
}

/* One grenade going off: bodies within reach take it, her included, and
 * what breaks nearby breaks (terrain_grenade). */
static void grenade_blast(StageRun *run, Player *player, const Progress *progress, float x)
{
    if (run->blasts < RUN_MAX_BLASTS)
        run->blast_x[run->blasts++] = x;
    float damage = progress_damage(progress) * GRENADE_DAMAGE_MULT;
    for (int k = 0; k < run->zombie_count; k++) {
        Zombie *z = &run->zombies[k];
        if (z->awake && !z->hidden && zombie_alive(z) &&
            fabsf(z->x - x) - ZOMBIE_HALF_WIDTH * SPRITE_SCALE <= GRENADE_RADIUS)
            zombie_hit_through(z, damage, BARREL_ARMOR_SHARE);
    }
    if (fabsf(player->x - x) - PLAYER_BODY_HALF_WIDTH <= GRENADE_RADIUS) {
        float claw = damage_at_level(ZOMBIE_ATTACK_BASE, run->stage->zombie_level);
        player_hit(player, claw * GRENADE_SELF_MULT, player->x < x ? -1 : 1);
    }
    terrain_grenade(&run->terrain, x, GRENADE_RADIUS);
}

/* Grenades in the air: an arc, bounces off the ground and off walls. */
static void move_grenades(StageRun *run, Player *player, const Progress *progress, float dt)
{
    for (int g = 0; g < RUN_MAX_GRENADES; g++) {
        Grenade *n = &run->grenades[g];
        if (!n->active)
            continue;
        float next = n->x + n->vx * dt;
        if (terrain_stops(&run->terrain, n->x, next, n->height))
            n->vx = -n->vx * GRENADE_BOUNCE; /* Off the wall */
        else
            n->x = next;
        n->vy -= GRENADE_GRAVITY * dt;
        n->height += n->vy * dt;
        if (n->height <= 0.0f) { /* Off the ground, less each time, rolling out */
            n->height = 0.0f;
            n->vy = -n->vy * GRENADE_BOUNCE;
            n->vx *= GRENADE_BOUNCE + 0.25f;
            if (n->vy < 60.0f)
                n->vy = 0.0f;
        }
        n->fuse -= dt;
        if (n->fuse <= 0.0f) {
            n->active = false;
            grenade_blast(run, player, progress, n->x);
        }
    }
}

/* A group wakes all at once, when its farthest zombie is close enough that
 * every one of them already stands in view. */
static void wake_groups(StageRun *run, const Player *player)
{
    for (int k = 0; k < run->zombie_count; k++) {
        if (run->zombies[k].awake || run->zombies[k].hidden)
            continue;
        int group = run->group_of[k];
        float farthest = -1e9f;
        for (int j = 0; j < run->zombie_count; j++) {
            if (run->group_of[j] == group)
                farthest = fmaxf(farthest, run->zombies[j].x);
        }
        if (farthest - player->x > ROUTE_WAKE_DISTANCE)
            continue;
        for (int j = 0; j < run->zombie_count; j++) {
            /* Those in a coffin wait for it to burst; ambushers for their spot. */
            if (run->group_of[j] != group || run->zombies[j].awake || run->zombies[j].hidden)
                continue;
            zombie_wake(&run->zombies[j]);
            run->elite_woke |= run->zombies[j].stats == &ZOMBIE_ELITE;
        }
    }
}

/* She reaches an ambush: its zombies walk in from off screen, one behind
 * her, the next ahead (if no wall or barricade is between), and so on. */
static void spring_ambushes(StageRun *run, const Player *player)
{
    int behind = 0, ahead = 0;
    for (int k = 0; k < run->zombie_count; k++) {
        Zombie *z = &run->zombies[k];
        if (run->ambush_x[k] <= 0.0f || !z->hidden || player->x < run->ambush_x[k])
            continue;
        float front = player->x + AMBUSH_AHEAD + (float)ahead * AMBUSH_SPACING;
        bool open = !terrain_stops(&run->terrain, player->x, front, 0.0f);
        if (open && behind > ahead) {
            z->x = front;
            ahead++;
        } else {
            z->x = player->x - AMBUSH_BEHIND - (float)behind * AMBUSH_SPACING;
            behind++;
        }
        z->hidden = false;
        zombie_wake(z);
        z->facing = z->x < player->x ? 1 : -1;
        run->ambushed = true;
    }
}

/* Zombies on the same side of her closer than this one: they queue up
 * instead of piling on one spot. */
static int queue_rank(const StageRun *run, int k)
{
    const Zombie *z = &run->zombies[k];
    float side = z->x - run->target_x;
    int rank = 0;
    for (int j = 0; j < run->zombie_count; j++) {
        const Zombie *o = &run->zombies[j];
        if (j == k || !o->awake || !zombie_alive(o))
            continue;
        float other = o->x - run->target_x;
        if (other * side > 0.0f && (fabsf(other) < fabsf(side) || (fabsf(other) == fabsf(side) && j < k)))
            rank++;
    }
    return rank;
}

static void move_zombies(StageRun *run, Player *player, Progress *progress, float dt)
{
    run->target_x = player->x;
    for (int k = 0; k < run->zombie_count; k++) {
        Zombie *z = &run->zombies[k];
        int barricade;
        float target = terrain_zombie_target(&run->terrain, z->x, player->x, &barricade);
        if (z->awake && zombie_alive(z)) /* Each one in line stands a step farther back */
            target += (z->x < target ? -1.0f : 1.0f) * ROUTE_QUEUE_STEP * (float)queue_rank(run, k);
        z->wading = terrain_river_at(&run->terrain, z->x);
        z->wind = player->wind;
        zombie_update(z, target, player_alive(player), dt);
        if (z->struck) {
            if (barricade >= 0)
                terrain_claw(&run->terrain, barricade);
            else
                combat_zombie_vs_player(z, player);
        }
        if (!zombie_alive(z) && !run->beaten[k]) {
            run->beaten[k] = true;
            run->defeated++;
            give_xp(run, progress,
                    (int)lroundf((float)kill_xp(z->level, progress->level) * stage_xp_share(run->stage)));
        }
        if (zombie_down(z) && !run->chest_done[k])
            zombie_chest(run, k, progress);
    }
}

/* Coffins she comes near burst open; then every coffin that burst (near,
 * shot or blown) lets its zombie out, already hunting. */
static void open_coffins(StageRun *run, const Player *player)
{
    Terrain *t = &run->terrain;
    for (int i = 0; i < t->count; i++) {
        const Piece *p = &t->items[i];
        if (p->kind == TERRAIN_COFFIN && !p->spent && fabsf(p->x - player->x) <= COFFIN_RANGE)
            terrain_open_coffin(t, i);
    }
    for (int e = 0; e < t->events.coffin_count; e++) {
        int k = t->items[t->events.coffins[e]].zombie;
        if (k < 0 || k >= run->zombie_count)
            continue;
        run->zombies[k].hidden = false;
        zombie_wake(&run->zombies[k]);
        run->coffins_burst++;
    }
}

/* Crates broken open and fences cleared on this step pay out. */
static void collect(StageRun *run, Player *player, Progress *progress)
{
    const TerrainEvents *ev = &run->terrain.events;
    int chest = chest_xp(progress->level, run->stage->zombie_level, run->stage->complexity, 0.5f, false);
    for (int e = 0; e < ev->crate_count && run->loot_count < TERRAIN_EVENTS; e++) {
        Loot loot = terrain_loot(run->stage_index, ev->crates[e]);
        if (loot == LOOT_HEALTH && ev->crate_blasted[e])
            continue; /* Blown up with it: no blast ever heals */
        run->loot[run->loot_count] = loot;
        run->loot_x[run->loot_count++] = run->terrain.items[ev->crates[e]].x;
        if (loot == LOOT_HEALTH) {
            int heal = (int)lroundf((float)player->max_health * LOOT_HEALTH_SHARE);
            player->health = player->health + heal < player->max_health ? player->health + heal
                                                                         : player->max_health;
        } else if (loot == LOOT_DYNAMITE) {
            run->dynamite++;
        } else if (loot == LOOT_WATER) {
            player->water++;
        } else if (loot == LOOT_GOLD) {
            give_xp(run, progress, (int)lroundf((float)chest * LOOT_GOLD_SHARE));
            int gold = run_crate_gold(run);
            progress->gold += gold;
            run->gold_gained += gold;
        }
    }
    for (int e = 0; e < ev->bottle_count; e++) {
        run->bottles_hit++;
        give_xp(run, progress, (int)lroundf((float)chest * BOTTLES_XP_SHARE));
    }
}

/* Bear traps snap on the first foot: a zombie's holds it, hers bites her. */
static void spring_traps(StageRun *run, Player *player, const Progress *progress)
{
    Terrain *t = &run->terrain;
    for (int i = 0; i < t->count; i++) {
        Piece *p = &t->items[i];
        if (p->kind != TERRAIN_TRAP || p->spent)
            continue;
        for (int k = 0; k < run->zombie_count && !p->spent; k++) {
            Zombie *z = &run->zombies[k];
            if (!z->awake || !zombie_alive(z) || fabsf(z->x - p->x) > TRAP_REACH)
                continue;
            p->spent = true;
            run->traps_sprung++;
            z->caught = TRAP_HOLD;
            zombie_hit_through(z, progress_damage(progress) * TRAP_DAMAGE_MULT, 0.5f);
        }
        if (!p->spent && player->jump.height <= 0.0f && fabsf(player->x - p->x) <= TRAP_REACH) {
            p->spent = true;
            run->traps_sprung++;
            float claw = damage_at_level(ZOMBIE_ATTACK_BASE, run->stage->zombie_level);
            player_hit(player, claw * TRAP_SELF_MULT, player->facing > 0 ? -1 : 1);
            player_bleed(player, claw * BLEED_SHARE);
        }
    }
}

/* Nets and snares hang up the first to step in: a zombie for a while (and
 * the drop hurts it), her until she cuts free (player_struggle). */
static void spring_hangers(StageRun *run, Player *player, const Progress *progress)
{
    Terrain *t = &run->terrain;
    for (int i = 0; i < t->count; i++) {
        Piece *p = &t->items[i];
        if ((p->kind != TERRAIN_NET && p->kind != TERRAIN_SNARE) || p->spent)
            continue;
        CatchKind kind = p->kind == TERRAIN_NET ? CATCH_NET : CATCH_SNARE;
        /* The sprung sapling's tip, where the rope hangs from. */
        float tip_x = p->x + (float)(SNARE_TIP_X - SNARE_FRAME_W / 2) * SPRITE_SCALE;
        float tip_y = (float)(BASELINE - (SNARE_FRAME_H - 1 - SNARE_TIP_Y) * SPRITE_SCALE);
        for (int k = 0; k < run->zombie_count && !p->spent; k++) {
            Zombie *z = &run->zombies[k];
            if (!z->awake || z->hidden || !zombie_alive(z) || z->caught > 0.0f ||
                fabsf(z->x - p->x) > TRAP_REACH)
                continue;
            p->spent = true;
            run->traps_sprung++;
            z->x = p->x;
            z->caught = kind == CATCH_NET ? NET_HOLD : SNARE_HOLD;
            z->catch_kind = kind;
            z->catch_time = 0.0f;
            z->catch_anchor_x = tip_x;
            z->catch_anchor_y = tip_y;
            zombie_hit_through(z, progress_damage(progress) * TRAP_DAMAGE_MULT * 0.5f, 0.5f);
        }
        if (!p->spent && player->jump.height <= 0.0f && fabsf(player->x - p->x) <= TRAP_REACH) {
            p->spent = true;
            run->traps_sprung++;
            player->x = p->x;
            player_catch(player, kind, tip_x, tip_y);
        }
    }
}

/* Spike plates: a step sets one off; while its spikes are out, whoever is
 * on it (and not over it in a jump) is run through, once a cycle. */
static void spikes(StageRun *run, Player *player, const Progress *progress)
{
    Terrain *t = &run->terrain;
    for (int i = 0; i < t->count; i++) {
        Piece *p = &t->items[i];
        if (p->kind != TERRAIN_SPIKES)
            continue;
        float half = terrain_half_width(p->kind);
        bool her = player_alive(player) && player->jump.height < SPIKES_TOP &&
                   fabsf(player->x - p->x) <= half + PLAYER_BODY_HALF_WIDTH * 0.5f;
        if (p->timer <= 0.0f) {
            bool stepped = her && player->jump.height <= 0.0f;
            for (int k = 0; k < run->zombie_count && !stepped; k++) {
                const Zombie *z = &run->zombies[k];
                stepped = z->awake && zombie_alive(z) && z->caught <= 0.0f && fabsf(z->x - p->x) <= half;
            }
            if (stepped) {
                p->timer = SPIKES_DELAY + SPIKES_OUT + SPIKES_REARM;
                p->hits = 0;
            }
            continue;
        }
        if (!terrain_spikes_out(p) || p->hits > 0)
            continue;
        p->hits = 1; /* Out: they run through whoever is on it, once */
        run->traps_sprung++;
        if (her) {
            float claw = damage_at_level(ZOMBIE_ATTACK_BASE, run->stage->zombie_level);
            player_hit(player, claw * SPIKES_SELF_MULT, player->facing > 0 ? -1 : 1);
            player_bleed(player, claw * BLEED_SHARE);
        }
        for (int k = 0; k < run->zombie_count; k++) {
            Zombie *z = &run->zombies[k];
            if (z->awake && !z->hidden && zombie_alive(z) && fabsf(z->x - p->x) <= half)
                zombie_hit_through(z, progress_damage(progress) * SPIKES_DAMAGE_MULT, 0.3f);
        }
    }
}

/* Burning oil: every FIRE_TICK, whoever stands in it gets burnt. */
static void burn(StageRun *run, Player *player, const Progress *progress, float dt)
{
    run->fire_tick -= dt;
    if (run->fire_tick > 0.0f)
        return;
    run->fire_tick += FIRE_TICK;
    const Terrain *t = &run->terrain;
    for (int i = 0; i < t->count; i++) {
        const Piece *p = &t->items[i];
        if (p->kind != TERRAIN_FIRE || p->spent)
            continue;
        for (int k = 0; k < run->zombie_count; k++) {
            Zombie *z = &run->zombies[k];
            if (z->awake && zombie_alive(z) && fabsf(z->x - p->x) <= FIRE_REACH)
                zombie_hit_through(z, progress_damage(progress) * FIRE_DAMAGE_MULT, 0.3f);
        }
        if (player->jump.height <= 0.0f && fabsf(player->x - p->x) <= FIRE_REACH) {
            float claw = damage_at_level(ZOMBIE_ATTACK_BASE, run->stage->zombie_level);
            player_hit(player, claw * FIRE_SELF_MULT, player->x < p->x ? -1 : 1);
        }
    }
}

void run_update(StageRun *run, Player *player, Progress *progress, float dt)
{
    run->xp_gained = run->levels_gained = run->chests_opened = run->blasts = 0;
    run->cleared_now = run->group_beaten = run->elite_woke = run->supply_taken = false;
    run->dynamite_taken = false; /* charge_lit is cleared here too, after main saw it */
    run->charge_lit = false;
    run->loot_count = run->bottles_hit = run->coffins_burst = run->traps_sprung = 0;
    run->ambushed = run->crate_hint = false;
    run->gold_gained = run->melee_hits = 0;
    run->wire_bit = false;
    if (run->phase == RUN_CLEARED || run->phase == RUN_FAILED) {
        terrain_clear_events(&run->terrain);
        return;
    }
    if (!player_alive(player)) {
        run->phase = RUN_FAILED;
        terrain_clear_events(&run->terrain);
        return;
    }

    int holding = run->holding;
    spring_ambushes(run, player);
    run->omen = false;
    for (int k = 0; k < run->zombie_count; k++) { /* Some ambushes she can feel coming */
        float at = run->ambush_x[k];
        if (at <= 0.0f || !run->zombies[k].hidden || player->x >= at || at - player->x > OMEN_RANGE)
            continue;
        unsigned roll = ((unsigned)(at * 0.37f) * 2654435761u) >> 16;
        run->omen |= (int)(roll % 100u) < OMEN_CHANCE;
    }
    wake_groups(run, player);
    terrain_update(&run->terrain, dt);
    if (!run->hinted && run->stage_index < 2) { /* Nothing else says crates hold things */
        for (int i = 0; i < run->terrain.count; i++) {
            const Piece *p = &run->terrain.items[i];
            if (p->kind == TERRAIN_CRATE && !p->spent && p->x > player->x &&
                p->x - player->x <= CRATE_HINT_RANGE) {
                run->hinted = run->crate_hint = true;
                break;
            }
        }
    }
    blow_up(run, player, progress);
    move_grenades(run, player, progress, dt);
    open_coffins(run, player);
    collect(run, player, progress);
    move_zombies(run, player, progress, dt);
    spring_traps(run, player, progress);
    spring_hangers(run, player, progress);
    spikes(run, player, progress);
    snag_wire(run, player, dt);
    burn(run, player, progress, dt);
    /* By a campfire: CAMPFIRE_HEAL every CAMPFIRE_HEAL_TIME, fractions kept. */
    if (terrain_by_campfire(&run->terrain, player->x) && player->health < player->max_health &&
        !run->stage->hot) { /* In the heat a fire only wears her out */
        run->warmth += dt;
        if (run->warmth >= CAMPFIRE_HEAL_TIME) {
            run->warmth -= CAMPFIRE_HEAL_TIME;
            run->heal_carry += CAMPFIRE_HEAL;
            int whole = (int)run->heal_carry;
            run->heal_carry -= (float)whole;
            heal(run, player, whole);
        }
    } else {
        run->warmth = 0.0f;
    }
    terrain_clear_events(&run->terrain);
    int now = fighting_group(run);
    if (holding >= 0 && now != holding)
        run->group_beaten = true;
    run->holding = now;
    run->wall_x = now >= 0 ? group_wall(run, now) : 0.0f;

    int boxes = terrain_take_dynamite(&run->terrain, player->x);
    if (boxes > 0) {
        run->dynamite += boxes;
        run->dynamite_taken = true;
    }
    if (terrain_take_supply(&run->terrain, player->x)) {
        run->supply_taken = true;
        run->dynamite += stage_supply_dynamite(run->stage);
        player->water += SUPPLY_WATER;
        int heal = (int)lroundf((float)player->max_health * SUPPLY_HEAL_SHARE);
        player->health = player->health + heal < player->max_health ? player->health + heal
                                                                     : player->max_health;
    }

    /* Once every body is gone (so their chests are out on the road too). */
    bool all_gone = run->defeated >= run->stage->zombies;
    for (int k = 0; k < run->zombie_count; k++)
        all_gone &= run->chest_done[k];
    if (all_gone && run->mission_chest < 0) {
        int xp = chest_xp(progress->level, run->stage->zombie_level, run->stage->complexity, 1.0f, true);
        place_chest(run, run->goal_x, xp, true);
    }
    for (int c = 0; c < RUN_MAX_CHESTS; c++) {
        Chest *chest = &run->chests[c];
        if (!chest_present(chest))
            continue;
        chest_update(chest, player->x, player_alive(player), dt);
        if (chest->just_opened) {
            run->opened_x[run->chests_opened++] = chest->x;
            give_xp(run, progress, chest->reward_xp);
            int gold = c == run->mission_chest ? GOLD_MISSION : GOLD_CHEST;
            progress->gold += gold;
            run->gold_gained += gold;
        }
        if (c == run->mission_chest && !chest_present(chest)) {
            run->phase = RUN_CLEARED;
            run->cleared_now = true;
        }
    }
}
