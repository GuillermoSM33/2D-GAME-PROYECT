#include "game/zombie.h"

#include <math.h>
#include <string.h>

#include "config.h"
#include "game/camera.h"
#include "game/damage.h"
#include "game/progression.h"

#define ZOMBIE_WALK_SHEET "sprites/zombies/riot/walk"
#define ZOMBIE_HURT_SHEET "sprites/zombies/riot/hurt"
#define ZOMBIE_DEATH_SHEET "sprites/zombies/riot/death"
#define ZOMBIE_ATTACK_SHEET "sprites/zombies/riot/attack"

/* Time from the killing hit until the body lies on the ground, starting
 * from frame 1 (see zombie_hit). */
#define DEATH_FALL_TIME ((ZOMBIE_DEATH_FRAMES - 1) / ZOMBIE_DEATH_FPS)
#define DEATH_FADE_START (DEATH_FALL_TIME + ZOMBIE_CORPSE_TIME)

/* Measured on the art: the helmet stays on x 23..48 and the torso on 8..51
 * (arm included), so 27.5 keeps the body steady between frames. */
static const AnimationDef ANIM_WALK = {
    .sheet = ZOMBIE_WALK_SHEET, .frame_w = ZOMBIE_FRAME_W, .frame_h = ZOMBIE_FRAME_H,
    .first_frame = 0, .frame_count = ZOMBIE_WALK_FRAMES, .fps = ZOMBIE_WALK_FPS, .loop = true,
    .anchor_x = 27.5f, .ground_y = 68,
};

/* Same template and pivot; frame 0 already leans back 2 px. */
static const AnimationDef ANIM_HURT = {
    .sheet = ZOMBIE_HURT_SHEET, .frame_w = ZOMBIE_FRAME_W, .frame_h = ZOMBIE_FRAME_H,
    .first_frame = 0, .frame_count = ZOMBIE_HURT_FRAMES, .fps = ZOMBIE_HURT_FPS, .loop = false,
    .anchor_x = 27.5f, .ground_y = 68,
};

/* Standing frames keep the pivot; lying on frame 7, it reaches x 71 in front. */
static const AnimationDef ANIM_DEATH = {
    .sheet = ZOMBIE_DEATH_SHEET, .frame_w = ZOMBIE_FRAME_W, .frame_h = ZOMBIE_FRAME_H,
    .first_frame = 0, .frame_count = ZOMBIE_DEATH_FRAMES, .fps = ZOMBIE_DEATH_FPS, .loop = false,
    .anchor_x = 27.5f, .ground_y = 68,
};

/* The legs never move, so the walk pivot fits; the claw trail reaches x 63. */
static const AnimationDef ANIM_ATTACK = {
    .sheet = ZOMBIE_ATTACK_SHEET, .frame_w = ZOMBIE_FRAME_W, .frame_h = ZOMBIE_FRAME_H,
    .first_frame = 0, .frame_count = ZOMBIE_ATTACK_FRAMES, .fps = ZOMBIE_ATTACK_FPS, .loop = false,
    .anchor_x = 27.5f, .ground_y = 68,
};

static const AnimationDef *const LEGACY_ANIMATIONS[] = {&ANIM_WALK, &ANIM_HURT, &ANIM_DEATH, &ANIM_ATTACK};

/* One row owns the profession's identity, equipment and level-1 statistics.
 * A runner keeps that equipment and attack, trades health for speed, and
 * has its own run poses. Civilian clothing never creates armor. */
#define ZOMBIE_KINDS(X) \
    X(RIOT, "riot", "Antidisturbios", "Casco, peto y rodilleras; avanza protegido.", "Peto antidisturbios", 100, 85, 15.0f, 1.00f) \
    X(SOLDIER, "soldier", "Soldado", "Uniforme militar con casco y chaleco.", "Chaleco militar y casco", 110, 65, 16.0f, 1.05f) \
    X(POLICE, "police", "Policía", "Uniforme policial y protección ligera.", "Chaleco policial", 95, 45, 14.0f, 1.10f) \
    X(RIOT_SHIELD, "riot_shield", "Antidisturbios con escudo", "El escudo lo protege y vuelve más lento.", "Escudo, casco y peto pesado", 140, 110, 16.0f, 0.72f) \
    X(CIVIL_MALE_1, "civil_male_1", "Civil: jornalero", "Camisa rojiza de trabajo y pantalón oscuro.", "Ropa, sin protección", 90, 0, 12.0f, 1.00f) \
    X(CIVIL_MALE_2, "civil_male_2", "Civil: comerciante", "Camisa clara, tirantes y pantalón de faena.", "Ropa, sin protección", 100, 0, 13.0f, 0.95f) \
    X(CIVIL_MALE_3, "civil_male_3", "Civil: viajero", "Ropa ligera de camino.", "Ropa, sin protección", 85, 0, 12.0f, 1.10f) \
    X(CIVIL_MALE_4, "civil_male_4", "Civil: minero", "Ropa de faena y botas gastadas.", "Ropa, sin protección", 110, 0, 14.0f, 0.90f) \
    X(CIVIL_MALE_5, "civil_male_5", "Civil: granjero", "Abrigo gastado, camisa clara y pantalón oscuro.", "Ropa, sin protección", 95, 0, 13.0f, 1.05f) \
    X(CIVIL_FEMALE_1, "civil_female_1", "Civil: viajera", "Ropa ligera de viaje.", "Ropa, sin protección", 85, 0, 12.0f, 1.05f) \
    X(CIVIL_FEMALE_2, "civil_female_2", "Civil: comerciante", "Vestido rojizo de trabajo, rasgado al caminar.", "Ropa, sin protección", 95, 0, 13.0f, 1.00f) \
    X(CIVIL_FEMALE_3, "civil_female_3", "Civil: costurera", "Chaleco de cuero sobre camisa y pantalón.", "Ropa, sin protección", 90, 0, 12.0f, 1.10f) \
    X(CIVIL_FEMALE_4, "civil_female_4", "Civil: ranchera", "Peto de faena remendado y camisa de trabajo.", "Ropa, sin protección", 100, 0, 14.0f, 0.98f) \
    X(CIVIL_FEMALE_5, "civil_female_5", "Civil: pobladora", "Blusa y ropa cotidiana del pueblo.", "Ropa, sin protección", 88, 0, 12.0f, 1.08f) \
    X(BURNED, "burned", "Quemado", "Ropa carbonizada y piel dañada por el fuego.", "Sin protección", 80, 0, 13.0f, 0.95f) \
    X(SKELETON, "skeleton", "Zombi muy degradado", "Zombi humanoide reanimado tras un envejecimiento extremo; piel y ropa muy deterioradas.", "Sin protección", 65, 0, 11.0f, 1.10f) \
    X(DOG, "dog", "Perro infectado", "Cuadrúpedo pequeño; se acerca con rapidez.", "Sin protección", 65, 0, 13.0f, 1.55f) \
    X(SHERIFF, "sheriff", "Sheriff", "Sombrero, placa y chaleco bajo el abrigo.", "Chaleco bajo el abrigo", 110, 30, 16.0f, 1.05f) \
    X(COWBOY, "cowboy", "Vaquero", "Sombrero y prendas de cuero del camino.", "Cuero ligero", 105, 10, 15.0f, 1.10f) \
    X(MOTORCYCLE, "motorcycle", "Motociclista", "Casco y chaqueta de cuero reforzada.", "Casco y cuero reforzado", 120, 55, 16.0f, 0.95f) \
    X(PRIEST, "priest", "Sacerdote", "Sotana rasgada y cuello claro.", "Sotana, sin protección", 90, 0, 12.0f, 0.95f) \
    X(JAILER, "jailer", "Carcelero", "Uniforme de guardia y chaleco de servicio.", "Chaleco de guardia", 130, 75, 17.0f, 0.85f) \
    X(FIREFIGHTER, "firefighter", "Bombero", "Casco y chaquetón grueso de rescate.", "Casco y chaquetón", 135, 45, 17.0f, 0.80f) \
    X(BUTCHER, "butcher", "Carnicero", "Delantal de cuero y cuerpo pesado.", "Delantal de cuero grueso", 150, 20, 19.0f, 0.80f) \
    X(ELITE, "elite", "Antidisturbios de élite", "Peto reforzado y garra más peligrosa.", "Armadura antidisturbios reforzada", 150, 120, 20.25f, 1.00f) \
    X(CITY_OFFICE, "city_office", "Ciudad: oficinista", "Camisa blanca, corbata roja floja, pantalón de vestir y gafete.", "Ropa, sin protección", 90, 0, 12.0f, 1.05f) \
    X(CITY_NURSE, "city_nurse", "Ciudad: enfermera", "Uniforme quirúrgico azul, estetoscopio y coleta.", "Ropa, sin protección", 85, 0, 12.0f, 1.10f) \
    X(CITY_WORKER, "city_worker", "Ciudad: obrero", "Casco naranja, chaleco reflejante y mezclilla.", "Casco de obra y chaleco", 115, 25, 15.0f, 0.92f) \
    X(CITY_GUARD, "city_guard", "Ciudad: guardia de seguridad", "Gorra negra, camisa celeste con charreteras y pantalón azul marino.", "Uniforme, sin protección", 105, 5, 14.0f, 1.00f) \
    X(CITY_POLICE, "city_police", "Ciudad: patrullero", "Uniforme azul marino, placa, radio al hombro y cinturón de servicio.", "Uniforme y cinturón de servicio", 110, 30, 15.0f, 1.00f)

#define NORMAL_STATS(kind_, id_, name_, description_, equipment_, hp_, armor_, attack_, speed_) \
    [ZOMBIE_KIND_##kind_] = {.health = hp_, .armor = armor_, .attack_base = attack_, \
        .tint = 0xffffff, .speed = speed_, .kind = ZOMBIE_KIND_##kind_, .runner = false},
static const ZombieStats BASE_STATS[ZOMBIE_KIND_COUNT] = {ZOMBIE_KINDS(NORMAL_STATS)};
#undef NORMAL_STATS

#define RUNNER_STATS(kind_, id_, name_, description_, equipment_, hp_, armor_, attack_, speed_) \
    [ZOMBIE_KIND_##kind_] = {.health = ((hp_) * 55 + 50) / 100, .armor = armor_, .attack_base = attack_, \
        .tint = ZOMBIE_KIND_##kind_ == ZOMBIE_KIND_ELITE ? 0xffa080 : 0xffffff, \
        .speed = (speed_) * 1.8f, .kind = ZOMBIE_KIND_##kind_, .runner = true},
static const ZombieStats RUNNER_STATS[ZOMBIE_KIND_COUNT] = {ZOMBIE_KINDS(RUNNER_STATS)};
#undef RUNNER_STATS

#define KIND_DEF(kind_, id_, name_, description_, equipment_, hp_, armor_, attack_, speed_) \
    [ZOMBIE_KIND_##kind_] = {id_, name_, description_, equipment_, \
        ZOMBIE_KIND_##kind_ == ZOMBIE_KIND_RIOT ? &ZOMBIE_RIOT : \
        ZOMBIE_KIND_##kind_ == ZOMBIE_KIND_ELITE ? &ZOMBIE_ELITE : &BASE_STATS[ZOMBIE_KIND_##kind_]},
static const ZombieKindDef KIND_DEFS[ZOMBIE_KIND_COUNT] = {ZOMBIE_KINDS(KIND_DEF)};
#undef KIND_DEF

#define ANIM_DEF(id_, action_, count_, fps_, loop_) { \
    .sheet = "sprites/zombies/" id_ "/" action_, .frame_w = ZOMBIE_FRAME_W, .frame_h = ZOMBIE_FRAME_H, \
    .first_frame = 0, .frame_count = count_, .fps = fps_, .loop = loop_, .anchor_x = 27.5f, .ground_y = 68}
#define KIND_ANIMS(kind_, id_, name_, description_, equipment_, hp_, armor_, attack_, speed_) \
    [ZOMBIE_KIND_##kind_] = { \
        [ZOMBIE_ANIM_IDLE] = ANIM_DEF(id_, "idle", 4, 3.0f, true), \
        [ZOMBIE_ANIM_WALK] = ANIM_DEF(id_, "walk", ZOMBIE_WALK_FRAMES, ZOMBIE_WALK_FPS, true), \
        [ZOMBIE_ANIM_RUN] = ANIM_DEF(id_, "run", ZOMBIE_WALK_FRAMES, ZOMBIE_WALK_FPS, true), \
        [ZOMBIE_ANIM_ATTACK] = ANIM_DEF(id_, "attack", ZOMBIE_ATTACK_FRAMES, ZOMBIE_ATTACK_FPS, false), \
        [ZOMBIE_ANIM_HURT] = ANIM_DEF(id_, "hurt", ZOMBIE_HURT_FRAMES, ZOMBIE_HURT_FPS, false), \
        [ZOMBIE_ANIM_DEATH] = ANIM_DEF(id_, "death", ZOMBIE_DEATH_FRAMES, ZOMBIE_DEATH_FPS, false), \
        [ZOMBIE_ANIM_CAUGHT] = ANIM_DEF(id_, "caught", 4, 6.0f, true)},
static const AnimationDef KIND_ANIMATIONS[ZOMBIE_KIND_COUNT][ZOMBIE_ANIM_COUNT] = {ZOMBIE_KINDS(KIND_ANIMS)};
#undef KIND_ANIMS
#undef ANIM_DEF

static ZombieKind valid_kind(ZombieKind kind)
{
    return kind >= 0 && kind < ZOMBIE_KIND_COUNT ? kind : ZOMBIE_KIND_RIOT;
}

const ZombieKindDef *zombie_kind_def(ZombieKind kind)
{
    return &KIND_DEFS[valid_kind(kind)];
}

const ZombieStats *zombie_stats(ZombieKind kind, bool runner)
{
    kind = valid_kind(kind);
    return runner ? &RUNNER_STATS[kind] : KIND_DEFS[kind].stats;
}

const AnimationDef *zombie_animation(ZombieKind kind, ZombieAnimation action)
{
    kind = valid_kind(kind);
    if (action < 0 || action >= ZOMBIE_ANIM_COUNT)
        action = ZOMBIE_ANIM_WALK;
    /* The riot keeps its original definitions and pixels. Every other kind,
     * including the elite copy, owns a complete folder in the catalogue. */
    if (kind == ZOMBIE_KIND_RIOT) {
        switch (action) {
        case ZOMBIE_ANIM_WALK: return &ANIM_WALK;
        case ZOMBIE_ANIM_ATTACK: return &ANIM_ATTACK;
        case ZOMBIE_ANIM_HURT: return &ANIM_HURT;
        case ZOMBIE_ANIM_DEATH: return &ANIM_DEATH;
        default: break;
        }
    }
    return &KIND_ANIMATIONS[kind][action];
}

static const AnimationDef *locomotion(const Zombie *zombie)
{
    return zombie_animation(zombie->kind, zombie->runner ? ZOMBIE_ANIM_RUN : ZOMBIE_ANIM_WALK);
}

const ZombieStats ZOMBIE_COMMON = {
    .health = 100, .armor = 0.0f, .attack_base = ZOMBIE_ATTACK_BASE, .tint = 0xffffff, .speed = 1.0f,
    .kind = ZOMBIE_KIND_CIVIL_MALE_1,
};
const ZombieStats ZOMBIE_RIOT = {
    .health = 100, .armor = 85.0f, .attack_base = ZOMBIE_ATTACK_BASE, .tint = 0xffffff, .speed = 1.0f,
    .kind = ZOMBIE_KIND_RIOT,
};
/* About twice as long to put down as a riot zombie, and its claw hurts a
 * third more: one per stage, guarding something. */
const ZombieStats ZOMBIE_ELITE = {
    .health = 150, .armor = 120.0f, .attack_base = ZOMBIE_ATTACK_BASE * 1.35f, .tint = 0xffa080,
    .speed = 1.0f,
    .kind = ZOMBIE_KIND_ELITE,
};
/* Half the health and little armor, but it closes in almost twice as fast:
 * it comes in packs and catches her if she runs. */
const ZombieStats ZOMBIE_RUNNER = {
    .health = 55, .armor = 25.0f, .attack_base = ZOMBIE_ATTACK_BASE, .tint = 0xb8f0a0,
    .speed = 1.8f,
    .kind = ZOMBIE_KIND_RIOT, .runner = true,
};

void zombie_spawn(Zombie *zombie, const ZombieStats *stats, float x)
{
    memset(zombie, 0, sizeof(*zombie));
    zombie->stats = stats ? stats : &ZOMBIE_RIOT;
    zombie->kind = valid_kind(zombie->stats->kind);
    zombie->runner = zombie->stats->runner;
    zombie->x = x;
    zombie->facing = -1; /* zombie_update turns it toward the player */
    zombie->state = ZOMBIE_WALK;
    zombie->awake = true;
    zombie->just_spawned = true;
    zombie->growl_time = ZOMBIE_GROWL_INTERVAL; /* Its spawn growl counts as the first */
    animation_play(&zombie->anim, locomotion(zombie));
    zombie_set_level(zombie, 1);
}

void zombie_set_level(Zombie *zombie, int level)
{
    zombie->level = level < 1 ? 1 : level > MAX_LEVEL ? MAX_LEVEL : level;
    zombie->max_health = level_health(zombie->stats->health, zombie->level);
    float armor_growth = zombie->stats->armor > 0.0f || zombie->stats == &ZOMBIE_COMMON
                             ? ZOMBIE_ARMOR_PER_LEVEL : 0.0f;
    zombie->armor = level_armor(zombie->stats->armor, armor_growth, zombie->level);
    zombie->health = zombie->max_health;
    zombie->wound = 0.0f;
}

float zombie_spawn_x(float player_x)
{
    float left = camera_left(player_x);
    return player_x - left <= VIEW_WIDTH / 2.0f ? left + VIEW_WIDTH - ZOMBIE_SPAWN_MARGIN
                                                  : left + ZOMBIE_SPAWN_MARGIN;
}

void zombie_wake(Zombie *zombie)
{
    if (zombie->awake)
        return;
    zombie->awake = true;
    zombie->just_spawned = true;
    zombie->rouse = ZOMBIE_ROUSE_TIME;
}

int zombie_breath(const Zombie *zombie)
{
    if (zombie->state == ZOMBIE_DEAD)
        return 0;
    if (zombie->awake) /* Woken: it jerks upright, then settles */
        return zombie->rouse > ZOMBIE_ROUSE_TIME - 0.15f ? 2 : 0;
    return fmodf(zombie->idle_time, ZOMBIE_BREATH_TIME) < ZOMBIE_BREATH_TIME / 2.0f ? 1 : 0;
}

void zombie_update(Zombie *zombie, float player_x, bool player_alive, float dt)
{
    zombie->struck = false;
    if (!zombie->awake && zombie->state != ZOMBIE_DEAD) {
        /* A real idle loop: each sleeper breathes on its own beat. */
        if (zombie->idle_time == 0.0f)
            zombie->idle_time = fmodf(zombie->x * 0.013f, ZOMBIE_BREATH_TIME) + 0.001f;
        zombie->idle_time += dt;
        zombie->facing = player_x < zombie->x ? -1 : 1;
        animation_play(&zombie->anim, zombie_animation(zombie->kind, ZOMBIE_ANIM_IDLE));
        animation_update(&zombie->anim, dt);
        return;
    }
    if (zombie->caught > 0.0f && zombie->state != ZOMBIE_DEAD) {
        /* A caught loop is independent of hit recoil, including while the
         * hanging renderer rotates or lifts it in a net or a snare. */
        zombie->caught -= dt;
        zombie->catch_time += dt;
        zombie->facing = player_x < zombie->x ? -1 : 1;
        animation_play(&zombie->anim, zombie_animation(zombie->kind, ZOMBIE_ANIM_CAUGHT));
        animation_update(&zombie->anim, dt);
        if (zombie->caught > 0.0f)
            return;
        zombie->caught = 0.0f;
        zombie->catch_kind = CATCH_NONE; /* Dropped out of the net or the snare */
        zombie->state = ZOMBIE_WALK;
        animation_play(&zombie->anim, locomotion(zombie));
    }
    if (zombie->rouse > 0.0f && zombie->state != ZOMBIE_DEAD && zombie->state != ZOMBIE_HURT) {
        /* Woken: it jerks upright and shudders, turned on her, then lurches
         * into its first step and sets off. */
        zombie->rouse -= dt;
        zombie->facing = player_x < zombie->x ? -1 : 1;
        animation_play(&zombie->anim, locomotion(zombie));
        animation_set_frame(&zombie->anim, zombie->rouse > ZOMBIE_ROUSE_TIME / 2.0f ? 0 : 1);
        if (zombie->rouse > 0.0f)
            return;
        zombie->rouse = 0.0f;
        animation_play(&zombie->anim, locomotion(zombie));
    }
    if (zombie->stagger_time > 0.0f)
        zombie->stagger_time = fmaxf(0.0f, zombie->stagger_time - dt);
    if (zombie->attack_cooldown > 0.0f)
        zombie->attack_cooldown = fmaxf(0.0f, zombie->attack_cooldown - dt);
    if (zombie->state != ZOMBIE_DEAD) {
        zombie->growl_time -= dt;
        if (zombie->growl_time <= 0.0f) {
            zombie->growl_due = true;
            zombie->growl_time += ZOMBIE_GROWL_INTERVAL;
        }
    }

    if (zombie->state == ZOMBIE_DEAD) {
        zombie->dead_time += dt;
        animation_update(&zombie->anim, dt); /* Holds the last frame once down */
        return;
    }

    if (zombie->state == ZOMBIE_HURT) {
        animation_update(&zombie->anim, dt);
        if (!zombie->anim.finished)
            return;
        animation_play(&zombie->anim, locomotion(zombie));
    }

    /* The swipe plays out facing where it started; a recoil cuts it short. */
    if (zombie->state == ZOMBIE_ATTACK) {
        int before = zombie->anim.frame;
        animation_update(&zombie->anim, dt);
        zombie->struck = before < ZOMBIE_ATTACK_STRIKE_FRAME &&
                         zombie->anim.frame >= ZOMBIE_ATTACK_STRIKE_FRAME;
        if (!zombie->anim.finished)
            return;
        zombie->attack_cooldown = ZOMBIE_ATTACK_COOLDOWN;
        animation_play(&zombie->anim, locomotion(zombie));
    }

    float gap = player_x - zombie->x;
    zombie->facing = gap < 0.0f ? -1 : 1;
    if (fabsf(gap) <= ZOMBIE_REACH) {
        if (player_alive && zombie->attack_cooldown <= 0.0f) {
            zombie->state = ZOMBIE_ATTACK;
            animation_play(&zombie->anim, zombie_animation(zombie->kind, ZOMBIE_ANIM_ATTACK));
            animation_restart(&zombie->anim);
            return;
        }
        /* Waiting keeps breathing rather than freezing the walking pose. */
        zombie->state = ZOMBIE_WAIT;
        animation_play(&zombie->anim, zombie_animation(zombie->kind, ZOMBIE_ANIM_IDLE));
        animation_update(&zombie->anim, dt);
        return;
    }
    zombie->state = ZOMBIE_WALK;
    animation_play(&zombie->anim, locomotion(zombie));
    float pace = zombie->stats->speed;
    if (zombie->wind != 0) /* Pushed along, or walking into it */
        pace *= zombie->facing == zombie->wind ? WIND_WITH : WIND_AGAINST;
    if (zombie->wading) /* The river flows right */
        pace *= RIVER_SLOW * (zombie->facing > 0 ? RIVER_WITH : RIVER_AGAINST);
    float step = fminf(ZOMBIE_SPEED * pace * dt, fabsf(gap) - ZOMBIE_REACH);
    zombie->x += (float)zombie->facing * step;
    animation_update(&zombie->anim, dt * pace);
}

HitResult zombie_hit(Zombie *zombie, float damage)
{
    return zombie_hit_through(zombie, damage, 1.0f);
}

HitResult zombie_hit_through(Zombie *zombie, float damage, float armor_share)
{
    if (!zombie_alive(zombie))
        return HIT_NONE;
    zombie->wound += damage_through_armor(damage, zombie->armor * armor_share);
    int points = (int)zombie->wound;
    zombie->wound -= (float)points;
    zombie->health -= points;
    if (zombie->health > 0) {
        if (zombie->stagger_time > 0.0f)
            return HIT_ARMOR;
        zombie->state = ZOMBIE_HURT;
        zombie->stagger_time = ZOMBIE_HURT_FRAMES / ZOMBIE_HURT_FPS + ZOMBIE_STAGGER_COOLDOWN;
        animation_play(&zombie->anim, zombie_animation(zombie->kind, ZOMBIE_ANIM_HURT));
        animation_restart(&zombie->anim);
        return HIT_STAGGER;
    }
    zombie->health = 0;
    zombie->state = ZOMBIE_DEAD;
    zombie->dead_time = 0.0f;
    zombie->just_died = true;
    zombie->growl_due = false; /* The death groan replaces a growl due now */
    /* Frame 0 is the standing pose: start on the jolt, which has the sparks. */
    animation_play(&zombie->anim, zombie_animation(zombie->kind, ZOMBIE_ANIM_DEATH));
    animation_seek(&zombie->anim, 1);
    return HIT_KILL;
}

float zombie_attack_damage(const Zombie *zombie)
{
    return damage_at_level(zombie->stats->attack_base, zombie->level);
}

int zombie_shudder(const Zombie *zombie)
{
    if (!zombie->awake || zombie->rouse <= ZOMBIE_ROUSE_TIME / 2.0f || zombie->state == ZOMBIE_DEAD)
        return 0;
    return (int)(zombie->rouse * 25.0f) % 2 ? 1 : -1;
}

bool zombie_alive(const Zombie *zombie)
{
    return zombie->state != ZOMBIE_DEAD;
}

bool zombie_overlaps(const Zombie *zombie, float x0, float x1, float y)
{
    float half = zombie_body_half_width(zombie);
    return fmaxf(x0, x1) >= zombie->x - half && fminf(x0, x1) <= zombie->x + half &&
           y <= BASELINE && y >= BASELINE - zombie_body_height(zombie);
}

float zombie_body_height(const Zombie *zombie)
{
    return (zombie && zombie->kind == ZOMBIE_KIND_DOG ? 38.0f : ZOMBIE_HEIGHT) * SPRITE_SCALE;
}

float zombie_body_half_width(const Zombie *zombie)
{
    return (zombie && zombie->kind == ZOMBIE_KIND_DOG ? 22.0f : ZOMBIE_HALF_WIDTH) * SPRITE_SCALE;
}

const AnimationDef *zombie_walk_animation(void)
{
    return &ANIM_WALK;
}

bool zombie_down(const Zombie *zombie)
{
    return !zombie_alive(zombie) && zombie->dead_time >= DEATH_FALL_TIME;
}

bool zombie_gone(const Zombie *zombie)
{
    return !zombie_alive(zombie) && zombie->dead_time >= DEATH_FADE_START + ZOMBIE_FADE_TIME;
}

float zombie_opacity(const Zombie *zombie)
{
    if (zombie_alive(zombie))
        return 1.0f;
    float fading = zombie->dead_time - DEATH_FADE_START;
    return fminf(1.0f, fmaxf(0.0f, 1.0f - fading / ZOMBIE_FADE_TIME));
}

const AnimationDef *const *zombie_animations(int *count)
{
    static const AnimationDef *animations[4 + ZOMBIE_KIND_COUNT * ZOMBIE_ANIM_COUNT];
    static bool ready;
    if (!ready) {
        int next = 0;
        for (int i = 0; i < 4; i++)
            animations[next++] = LEGACY_ANIMATIONS[i];
        for (int kind = 0; kind < ZOMBIE_KIND_COUNT; kind++)
            for (int action = 0; action < ZOMBIE_ANIM_COUNT; action++)
                animations[next++] = zombie_animation((ZombieKind)kind, (ZombieAnimation)action);
        ready = true;
    }
    *count = (int)(sizeof(animations) / sizeof(animations[0]));
    return animations;
}
