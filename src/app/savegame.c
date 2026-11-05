#include "app/savegame.h"

#include <limits.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "app/stage.h"

/* Increment this schema when changing field order, enum/catalogue order or
 * the meaning of saved data. Never serialize native padding or addresses. */
#define SAVE_SCHEMA 3u
#define SAVE_MAGIC 0x31535156u
#define ANIMATION_LIMIT 512

_Static_assert(sizeof(float) == 4, "Save schema requires IEEE binary32 floats");
_Static_assert(INT_MAX >= 2147483647, "Save schema requires 32-bit integers");

typedef struct {
    unsigned char *bytes;
    size_t capacity, position;
    bool reading, ok;
    unsigned schema;
} Codec;

static void u32(Codec *c, uint32_t *value)
{
    if (!c->ok || c->position > c->capacity || c->capacity - c->position < 4) {
        c->ok = false;
        return;
    }
    if (c->reading) {
        *value = 0;
        for (int i = 0; i < 4; i++)
            *value |= (uint32_t)c->bytes[c->position++] << (8 * i);
    } else {
        for (int i = 0; i < 4; i++)
            c->bytes[c->position++] = (unsigned char)(*value >> (8 * i));
    }
}

static void integer(Codec *c, int *value)
{
    uint32_t raw = (uint32_t)*value;
    u32(c, &raw);
    if (c->reading && c->ok)
        *value = raw <= INT_MAX ? (int)raw : (int)((int64_t)raw - INT64_C(4294967296));
}

static void real(Codec *c, float *value)
{
    uint32_t raw;
    memcpy(&raw, value, sizeof(raw));
    u32(c, &raw);
    if (c->reading && c->ok)
        memcpy(value, &raw, sizeof(raw));
    if (!isfinite(*value) || fabsf(*value) > 1e8f)
        c->ok = false;
}

#define I(field) do { int v = (int)(field); integer(c, &v); if (c->reading) (field) = v; } while (0)
#define U(field) do { uint32_t v = (uint32_t)(field); u32(c, &v); if (c->reading) (field) = v; } while (0)
#define F(field) real(c, &(field))
#define B(field) do { int v = (field) ? 1 : 0; integer(c, &v); if (v < 0 || v > 1) c->ok = false; if (c->reading) (field) = v != 0; } while (0)
#define CHECK(condition) do { if (!(condition)) c->ok = false; } while (0)
#define A(field) animation(c, &(field))

static int animation_catalogue(const AnimationDef **all)
{
    int count, total = 1;
    all[0] = NULL;
    const AnimationDef *const *list = player_state_animations(&count);
    for (int i = 0; i < count; i++) all[total++] = list[i];
    list = zombie_animations(&count);
    for (int i = 0; i < count; i++) all[total++] = list[i];
    list = bullet_animations(&count);
    for (int i = 0; i < count; i++) all[total++] = list[i];
    all[total++] = chest_animation();
    return total;
}

static void animation(Codec *c, Animation *a)
{
    const AnimationDef *all[ANIMATION_LIMIT];
    int count = animation_catalogue(all), id = -1;
    for (int i = 0; i < count; i++)
        if (a->def == all[i]) { id = i; break; }
    I(id);
    CHECK(id >= 0 && id < count);
    if (!c->ok) return;
    if (c->reading) a->def = all[id];
    F(a->time); I(a->frame); B(a->finished);
    if (a->def)
        CHECK(a->frame >= a->def->first_frame && a->frame < a->def->first_frame + a->def->frame_count);
}

static void stats(Codec *c, Zombie *z)
{
    const ZombieStats *all[4 + ZOMBIE_KIND_COUNT * 2] = {
        &ZOMBIE_COMMON, &ZOMBIE_RIOT, &ZOMBIE_ELITE, &ZOMBIE_RUNNER,
    };
    int count = 4, id = -1;
    for (int i = 0; i < ZOMBIE_KIND_COUNT; i++)
        for (int runner = 0; runner < 2; runner++)
            all[count++] = zombie_stats((ZombieKind)i, runner != 0);
    for (int i = 0; i < count; i++)
        if (z->stats == all[i]) { id = i; break; }
    I(id);
    CHECK(id >= 0 && id < count);
    if (c->reading && c->ok) z->stats = all[id];
}

static void progress(Codec *c, Progress *p)
{
    I(p->level); I(p->xp); I(p->weapon_level); I(p->armor_level); I(p->gold);
    CHECK(p->level >= 1 && p->level <= MAX_LEVEL && p->xp >= 0 && p->gold >= 0);
    CHECK(p->weapon_level >= 1 && p->weapon_level <= MAX_LEVEL);
    CHECK(p->armor_level >= 1 && p->armor_level <= MAX_LEVEL);
    if (p->level >= 1 && p->level <= MAX_LEVEL)
        CHECK(p->level == MAX_LEVEL ? p->xp == 0 : p->xp < xp_to_next(p->level));
}

static void character(Codec *c, int *index)
{
    /* Stable character IDs survive a change in menu ordering. */
    char id[64] = {0};
    if (!c->reading && *index >= 0 && *index < CHARACTER_COUNT)
        snprintf(id, sizeof(id), "%s", CHARACTERS[*index].id);
    int length = (int)strlen(id);
    I(length);
    CHECK(length > 0 && length < (int)sizeof(id));
    if (!c->ok || c->capacity - c->position < (size_t)length) { c->ok = false; return; }
    if (c->reading) memcpy(id, c->bytes + c->position, (size_t)length);
    else memcpy(c->bytes + c->position, id, (size_t)length);
    c->position += (size_t)length;
    id[length] = '\0';
    *index = -1;
    for (int i = 0; i < CHARACTER_COUNT; i++)
        if (strcmp(id, CHARACTERS[i].id) == 0) *index = i;
    CHECK(*index >= 0);
}

static void profile(Codec *c, Profile *p)
{
    progress(c, &p->progress);
    if (c->schema >= 2) {
        I(p->inventory.water); I(p->inventory.dynamite);
        CHECK(p->inventory.water >= 0 && p->inventory.dynamite >= 0);
    }
    for (int i = 0; i < 16; i++) {
        B(p->record.cleared[i]);
        if (c->schema >= 2) { U(p->record.stars[i]); U(p->record.best_ticks[i]); }
        CHECK(p->record.stars[i] <= 3);
    }
    for (int i = 0; i < ALMANAC_ENTRIES; i++) {
        AlmanacEntry *e = &p->almanac.entries[i];
        B(e->discovered); I(e->seen); I(e->defeated); I(e->max_level);
        CHECK(e->seen >= 0 && e->defeated >= 0 && e->max_level >= 0 && e->max_level <= MAX_LEVEL);
        CHECK(!e->discovered || e->max_level >= 1);
    }
}

static void codec_Player(Codec *c, Player *p);
static void codec_Zombie(Codec *c, Zombie *p);
static void codec_Piece(Codec *c, Piece *p);
static void codec_Chest(Codec *c, Chest *p);
static void codec_Grenade(Codec *c, Grenade *p);
static void codec_Bullet(Codec *c, Bullet *p);
static void codec_Crow(Codec *c, Crow *p);
static void codec_Bat(Codec *c, Bat *p);

static void run(Codec *c, StageRun *r)
{
    I(r->stage_index);
    CHECK(r->stage_index >= 0 && r->stage_index < STAGE_COUNT);
    if (!c->ok) return;
    r->stage = &STAGES[r->stage_index];
    B(r->drops_chests); I(r->phase); I(r->defeated); I(r->dynamite);
    if (c->schema >= 2) {
        MissionReport *m = &r->mission;
        U(m->ticks); F(m->tick_fraction); I(m->stars); I(m->health_percent);
        B(m->new_record); B(m->claimed); I(m->base_xp); I(m->base_gold);
        I(m->star_xp); I(m->star_gold); I(m->record_xp); I(m->record_gold);
        CHECK(m->tick_fraction >= 0.0f && m->tick_fraction < 1.0f);
        CHECK(m->stars >= 0 && m->stars <= 3 && m->health_percent >= 0 && m->health_percent <= 100);
        CHECK(!m->claimed && m->base_xp >= 0 && m->base_gold >= 0 && m->star_xp >= 0 && m->star_gold >= 0);
        CHECK(m->record_xp >= 0 && m->record_gold >= 0);
    }
    F(r->start_x); F(r->goal_x); F(r->wall_x); F(r->target_x); I(r->holding);
    I(r->mission_chest); B(r->hinted);
    F(r->wire_timer); F(r->fire_tick); F(r->warmth); F(r->heal_carry);
    F(r->bolt_wait); F(r->bolt_warn); F(r->bolt_x); F(r->bolt_show); U(r->bolt_seed);
    CHECK(r->phase == RUN_FIGHTING && r->defeated >= 0 && r->defeated <= r->stage->zombies);
    CHECK(r->dynamite >= 0 && r->holding >= -1 && r->holding < RUN_MAX_ZOMBIES);
    CHECK(r->mission_chest >= -1 && r->mission_chest < RUN_MAX_CHESTS && r->goal_x > r->start_x);
    I(r->zombie_count);
    CHECK(r->zombie_count >= 0 && r->zombie_count <= RUN_MAX_ZOMBIES);
    for (int i = 0; c->ok && i < r->zombie_count; i++) {
        codec_Zombie(c, &r->zombies[i]);
        I(r->group_of[i]); B(r->beaten[i]); B(r->chest_done[i]);
        F(r->ambush_x[i]); F(r->zombie_wire[i]);
        CHECK(r->group_of[i] >= -1 && r->group_of[i] < RUN_MAX_ZOMBIES);
    }
    for (int i = 0; i < RUN_MAX_CHESTS; i++) codec_Chest(c, &r->chests[i]);
    I(r->terrain.count);
    CHECK(r->terrain.count >= 0 && r->terrain.count <= TERRAIN_MAX);
    for (int i = 0; c->ok && i < r->terrain.count; i++) codec_Piece(c, &r->terrain.items[i]);
    for (int i = 0; i < RUN_MAX_GRENADES; i++) codec_Grenade(c, &r->grenades[i]);
}

static bool target_valid(const SaveGame *game, int target)
{
    return target == 0 || (target > 0 && target <= game->checkpoint.run.zombie_count) ||
           (target >= 1001 && target < 1001 + game->checkpoint.run.terrain.count);
}

static void rebind_targets(const SaveGame *game, StagePlay *play)
{
    for (int i = 0; i < BULLET_MAX; i++) {
        int target = game->bullet_targets[i];
        play->bullets.items[i].glanced = target == 0 ? NULL : target >= 1001
            ? (const void *)&play->run.terrain.items[target - 1001]
            : (const void *)&play->run.zombies[target - 1];
    }
}

static void checkpoint(Codec *c, SaveGame *game)
{
    StagePlay *p = &game->checkpoint;
    I(p->weapon_slot); B(p->single_fire); B(p->duals_out); F(p->power_cooldown);
    B(p->ricochet_armed); B(p->ricochet_fired);
    for (int i = 0; i < CHARACTER_MAX_WEAPONS; i++) {
        I(p->guns[i]); I(p->rounds[i]);
        CHECK(p->guns[i] >= 0 && p->guns[i] < WEAPON_COUNT);
        if (p->guns[i] >= 0 && p->guns[i] < WEAPON_COUNT)
            CHECK(p->rounds[i] >= -1 || weapon_def(p->guns[i])->magazine == 0);
    }
    codec_Player(c, &p->player);
    run(c, &p->run);
    progress(c, &p->progress_at_start);
    if (c->schema >= 2) {
        I(p->inventory_at_start.water); I(p->inventory_at_start.dynamite);
        CHECK(p->inventory_at_start.water >= 0 && p->inventory_at_start.dynamite >= 0);
    }
    B(p->flashlight); F(p->flashlight_since); B(p->flashlight_click_pending);
    for (int i = 0; i < RUN_MAX_ZOMBIES; i++) {
        I(p->encounter.entry[i]); B(p->encounter.defeated[i]);
        CHECK(p->encounter.entry[i] >= -1 && p->encounter.entry[i] < ALMANAC_ENTRIES);
    }
    for (int i = 0; i < BULLET_MAX; i++) {
        codec_Bullet(c, &p->bullets.items[i]); I(game->bullet_targets[i]);
        CHECK(target_valid(game, game->bullet_targets[i]));
    }
    I(p->crows.count);
    CHECK(p->crows.count >= 0 && p->crows.count <= CROWS_MAX);
    for (int i = 0; c->ok && i < p->crows.count; i++) codec_Crow(c, &p->crows.items[i]);
    for (int i = 0; i < BATS_MAX; i++) codec_Bat(c, &p->bats.items[i]);
    if (game->checkpoint_hero >= 0 && game->checkpoint_hero < CHARACTER_COUNT) {
        p->character = &CHARACTERS[game->checkpoint_hero];
        CHECK(p->weapon_slot >= 0 && p->weapon_slot < p->character->weapon_count);
        CHECK(stage_unlocked(&game->profiles[game->checkpoint_hero].record, p->run.stage_index));
        CHECK(p->player.level == game->profiles[game->checkpoint_hero].progress.level);
    }
    CHECK(p->player.state != PLAYER_DEAD && p->player.health > 0);
}

static void game_codec(Codec *c, SaveGame *game)
{
    uint32_t magic = SAVE_MAGIC, version = SAVE_SCHEMA;
    u32(c, &magic); u32(c, &version);
    CHECK(magic == SAVE_MAGIC && version >= 1 && version <= SAVE_SCHEMA);
    c->schema = version;
    int stages = STAGE_COUNT, entries = ALMANAC_ENTRIES, count = CHARACTER_COUNT;
    I(stages); I(entries); I(count);
    CHECK(stages == STAGE_COUNT && entries == ALMANAC_ENTRIES);
    CHECK(count > 0 && count <= APP_PROFILE_CAPACITY && CHARACTER_COUNT <= APP_PROFILE_CAPACITY);
    unsigned seen = 0;
    for (int i = 0; c->ok && i < count; i++) {
        int index = i;
        character(c, &index);
        if (!c->ok) return;
        CHECK(!(seen & (1u << index)));
        seen |= 1u << index;
        profile(c, &game->profiles[index]);
    }
    character(c, &game->hero);
    I(game->volumes.master);
    if (c->schema >= 3) I(game->volumes.music); /* Older saves keep the default */
    I(game->volumes.player); I(game->volumes.zombie);
    CHECK(game->volumes.master >= 0 && game->volumes.master <= VOLUME_STEPS);
    CHECK(game->volumes.music >= 0 && game->volumes.music <= VOLUME_STEPS);
    CHECK(game->volumes.player >= 0 && game->volumes.player <= VOLUME_STEPS);
    CHECK(game->volumes.zombie >= 0 && game->volumes.zombie <= VOLUME_STEPS);
    B(game->has_checkpoint);
    if (game->has_checkpoint && c->ok) {
        character(c, &game->checkpoint_hero);
        if (c->ok) checkpoint(c, game);
    }
}

void save_game_init(SaveGame *game)
{
    memset(game, 0, sizeof(*game));
    for (int i = 0; i < APP_PROFILE_CAPACITY; i++) {
        progress_init(&game->profiles[i].progress);
        stage_record_init(&game->profiles[i].record);
        almanac_init(&game->profiles[i].almanac);
    }
    volumes_init(&game->volumes);
}

void save_game_snapshot(SaveGame *game, const Profile *profiles, int hero,
                         const Volumes *volumes, const StagePlay *active)
{
    for (int i = 0; i < CHARACTER_COUNT && i < APP_PROFILE_CAPACITY; i++)
        game->profiles[i] = profiles[i];
    game->hero = hero;
    game->volumes = *volumes;
    if (!active) return; /* Keep an unresumed checkpoint while browsing menus. */
    game->has_checkpoint = active->run.phase == RUN_FIGHTING && player_alive(&active->player);
    game->profiles[hero].inventory = (Inventory){active->player.water, active->run.dynamite};
    if (active->run.phase != RUN_CLEARED && !game->has_checkpoint) {
        game->profiles[hero].progress = active->progress_at_start;
        game->profiles[hero].inventory = active->inventory_at_start;
    }
    if (!game->has_checkpoint) return;
    game->checkpoint_hero = hero;
    game->checkpoint = *active;
    for (int b = 0; b < BULLET_MAX; b++) {
        const void *target = active->bullets.items[b].glanced;
        game->bullet_targets[b] = 0;
        for (int i = 0; target && i < active->run.zombie_count; i++)
            if (target == &active->run.zombies[i]) game->bullet_targets[b] = i + 1;
        for (int i = 0; target && i < active->run.terrain.count; i++)
            if (target == &active->run.terrain.items[i]) game->bullet_targets[b] = i + 1001;
    }
    rebind_targets(game, &game->checkpoint);
}

bool save_game_encode(SaveGame *game, unsigned char *bytes, size_t capacity, size_t *size)
{
    Codec c = {.bytes = bytes, .capacity = capacity, .ok = bytes != NULL, .schema = SAVE_SCHEMA};
    game_codec(&c, game);
    *size = c.ok ? c.position : 0;
    return c.ok;
}

bool save_game_decode(const unsigned char *bytes, size_t size, void *output)
{
    if (!bytes || !output || !size || size > SAVE_GAME_CAPACITY) return false;
    SaveGame *candidate = malloc(sizeof(*candidate));
    if (!candidate) return false;
    save_game_init(candidate);
    Codec c = {.bytes = (unsigned char *)bytes, .capacity = size, .reading = true, .ok = true};
    game_codec(&c, candidate);
    bool ok = c.ok && c.position == size;
    if (ok) {
        SaveGame *game = output;
        *game = *candidate;
        if (game->has_checkpoint) {
            rebind_targets(game, &game->checkpoint);
            if (c.schema == 1)
                game->profiles[game->checkpoint_hero].inventory =
                    (Inventory){game->checkpoint.player.water, game->checkpoint.run.dynamite};
        }
    }
    free(candidate);
    return ok;
}

void save_game_abandon(SaveGame *game, Profile *profiles)
{
    if (!game->has_checkpoint) return;
    int hero = game->checkpoint_hero;
    profiles[hero].progress = game->checkpoint.progress_at_start;
    profiles[hero].inventory = game->checkpoint.inventory_at_start;
    game->profiles[hero] = profiles[hero];
    game->has_checkpoint = false;
}

bool save_game_resume(const SaveGame *game, StagePlay *play, int hero, int stage)
{
    if (!game->has_checkpoint || game->checkpoint_hero != hero || game->checkpoint.run.stage_index != stage)
        return false;
    const StagePlay *cp = &game->checkpoint;
    stage_start(play, stage, &CHARACTERS[hero], &game->profiles[hero].progress);
    play->weapon_slot = cp->weapon_slot; play->single_fire = cp->single_fire;
    play->duals_out = cp->duals_out; play->power_cooldown = cp->power_cooldown;
    play->ricochet_armed = cp->ricochet_armed; play->ricochet_fired = cp->ricochet_fired;
    memcpy(play->guns, cp->guns, sizeof(play->guns));
    memcpy(play->rounds, cp->rounds, sizeof(play->rounds));
    play->player = cp->player; play->run = cp->run; play->encounter = cp->encounter;
    play->bullets = cp->bullets; play->crows = cp->crows; play->bats = cp->bats;
    play->progress_at_start = cp->progress_at_start;
    play->inventory_at_start = cp->inventory_at_start;
    play->flashlight = cp->flashlight; play->flashlight_since = cp->flashlight_since;
    play->flashlight_click_pending = cp->flashlight_click_pending;
    /* Rebind to this live run, not the decoded snapshot's arrays. */
    rebind_targets(game, play);
    for (int i = 0; i < play->run.zombie_count; i++)
        play->prev_zombie_x[i] = play->run.zombies[i].x;
    return true;
}

/* Explicit schema fields, including in-progress actions and physical timers. */

static void codec_Jump(Codec *c, Jump *p)
{
    B(p->airborne);
    F(p->time);
    F(p->height);
    F(p->base);
    F(p->lift);
}

static void codec_Shot(Codec *c, Shot *p)
{
    B(p->active);
    B(p->fired);
    I(p->start_frame);
    F(p->time);
    F(p->reload);
    F(p->reload_time);
    I(p->burst);
    F(p->burst_gap);
    B(p->automatic);
    B(p->piston);
    B(p->other_gun);
    B(p->next_other);
    B(p->held);
    B(p->queued);
    I(p->burst_left);
    F(p->burst_timer);
    I(p->magazine);
    F(p->mag_reload_time);
    I(p->rounds);
    F(p->mag_reload);
}

static void codec_Player(Codec *c, Player *p)
{
    F(p->x);
    I(p->facing);
    I(p->state);
    codec_Jump(c, &p->jump);
    codec_Shot(c, &p->shot);
    B(p->shot_fired);
    B(p->threw);
    B(p->thrown);
    B(p->struck);
    B(p->landed);
    F(p->melee_wait);
    B(p->wading);
    F(p->depth);
    I(p->wind);
    B(p->hot);
    B(p->cold);
    B(p->cozy);
    F(p->wet);
    F(p->fatigue);
    B(p->fainted);
    I(p->water);
    F(p->drink_time);
    F(p->refreshed);
    B(p->drank);
    F(p->thirst);
    B(p->ghost);
    I(p->wind_feel);
    I(p->current_feel);
    F(p->bandage);
    B(p->bandaged);
    F(p->bandage_shown);
    B(p->power_shot);
    F(p->swap_time);
    B(p->swap_back);
    F(p->plant_time);
    B(p->burned);
    B(p->burn_bandaged);
    I(p->catch_kind);
    I(p->catch_blows);
    F(p->catch_time);
    F(p->catch_shake);
    F(p->catch_anchor_x);
    F(p->catch_anchor_y);
    I(p->health);
    I(p->level);
    I(p->max_health);
    F(p->armor);
    F(p->hurt_time);
    F(p->heal_time);
    B(p->bleeding);
    F(p->bleed_tick);
    F(p->bleed_damage);
    F(p->slow_time);
    F(p->knockback_time);
    I(p->knockback_dir);
    F(p->floor);
    F(p->min_x);
    F(p->max_x);
    B(p->vaulting);
    B(p->reload_walk);
    B(p->light_on);
    F(p->light_since);
    F(p->light_time);
    F(p->light_rows);
    B(p->light_swings);
    A(p->legs);
    F(p->sit_time);
    U(p->sit_guns);
    I(p->sit_gun);
    F(p->sit_gun_time);
    B(p->sit_reloaded);
    I(p->sit_reloaded_gun);
    A(p->anim);
    CHECK(p->state >= PLAYER_IDLE && p->state <= PLAYER_DEAD);
    CHECK(p->facing == FACING_LEFT || p->facing == FACING_RIGHT);
    CHECK(p->level >= 1 && p->level <= MAX_LEVEL && p->max_health > 0);
    CHECK(p->health >= 0 && p->health <= p->max_health && p->water >= 0);
    CHECK(p->catch_kind >= CATCH_NONE && p->catch_kind <= CATCH_SNARE);
    CHECK(p->sit_gun >= -1 && p->sit_gun < CHARACTER_MAX_WEAPONS);
    /* Earlier sessions decremented this unused counter for infinite-ammo
     * guns too. Accept those harmless negatives without relaxing validation
     * for a real magazine. Stored, unequipped guns use -1 for "full". */
    CHECK(p->shot.magazine >= 0 && (p->shot.magazine == 0 || p->shot.rounds >= 0));
}

static void codec_Zombie(Codec *c, Zombie *p)
{
    stats(c, p);
    I(p->kind);
    B(p->runner);
    I(p->level);
    I(p->max_health);
    F(p->armor);
    F(p->x);
    I(p->facing);
    I(p->state);
    B(p->awake);
    F(p->idle_time);
    F(p->rouse);
    B(p->hidden);
    F(p->caught);
    I(p->catch_kind);
    B(p->wading);
    F(p->depth);
    I(p->wind);
    F(p->catch_time);
    F(p->catch_anchor_x);
    F(p->catch_anchor_y);
    I(p->health);
    F(p->wound);
    F(p->stagger_time);
    F(p->dead_time);
    F(p->attack_cooldown);
    B(p->struck);
    B(p->just_spawned);
    B(p->growl_due);
    B(p->just_died);
    F(p->growl_time);
    A(p->anim);
    CHECK(p->kind >= 0 && p->kind < ZOMBIE_KIND_COUNT);
    CHECK(p->state >= ZOMBIE_WALK && p->state <= ZOMBIE_DEAD);
    CHECK(p->level >= 1 && p->level <= MAX_LEVEL && p->max_health > 0);
    CHECK(p->health >= 0 && p->health <= p->max_health);
    CHECK(p->facing == -1 || p->facing == 1);
    CHECK(p->catch_kind >= CATCH_NONE && p->catch_kind <= CATCH_SNARE);
}

static void codec_Piece(Codec *c, Piece *p)
{
    I(p->kind);
    F(p->x);
    I(p->damage);
    B(p->spent);
    B(p->blowing);
    F(p->fuse);
    I(p->hits);
    F(p->timer);
    I(p->zombie);
    F(p->ripple);
    I(p->variant);
    CHECK(p->kind >= 0 && p->kind < TERRAIN_KINDS);
    CHECK(p->zombie >= -1 && p->zombie < RUN_MAX_ZOMBIES);
    CHECK(p->variant >= 0 && p->variant <= 64 && p->damage >= 0 && p->hits >= 0);
}

static void codec_Chest(Codec *c, Chest *p)
{
    I(p->state);
    F(p->x);
    F(p->time);
    I(p->reward_xp);
    B(p->just_opened);
    A(p->anim);
    CHECK(p->state >= CHEST_NONE && p->state <= CHEST_FADING && p->reward_xp >= 0);
}

static void codec_Grenade(Codec *c, Grenade *p)
{
    B(p->active);
    F(p->x);
    F(p->height);
    F(p->vx);
    F(p->vy);
    F(p->fuse);
}

static void codec_BulletSpec(Codec *c, BulletSpec *p)
{
    F(p->damage);
    F(p->speed);
    F(p->range);
    F(p->armor_share);
    U(p->tint);
    F(p->slope);
    B(p->ricochet);
}

static void codec_Bullet(Codec *c, Bullet *p)
{
    B(p->active);
    F(p->x);
    F(p->y);
    F(p->prev_x);
    I(p->dir);
    F(p->flown);
    F(p->bounce_y);
    F(p->bounce_left);
    B(p->burst);
    codec_BulletSpec(c, &p->spec);
    A(p->anim);
    CHECK(!p->active || p->dir == -1 || p->dir == 1);
}

static void codec_Crow(Codec *c, Crow *p)
{
    F(p->x);
    F(p->height);
    F(p->vx);
    F(p->vy);
    I(p->facing);
    B(p->flying);
    B(p->gone);
    B(p->dead);
    F(p->dead_time);
    F(p->time);
}

static void codec_Bat(Codec *c, Bat *p)
{
    F(p->x);
    F(p->home);
    F(p->height);
    F(p->base);
    F(p->vx);
    F(p->vy);
    I(p->facing);
    B(p->alive);
    B(p->fleeing);
    B(p->dead);
    F(p->dead_time);
    F(p->time);
}
