#include "game/train.h"

#include <math.h>
#include <stddef.h>
#include <stdio.h>
#include "game/casefile.h"
#include "game/stage_run.h"

static float span(void) { return (float)(TRAIN_ROOM_W * SPRITE_SCALE); }
static float art(float x) { return x * SPRITE_SCALE; }
static bool near(float a, float b) { return fabsf(a - b) <= 32 * SPRITE_SCALE; }

float train_room_left(const StageRun *r, int room) { return r->train.left + (float)room * span(); }
float train_entry_x(const StageRun *r) { return r->train.left + art(TRAIN_ENTRY_ART); }
float train_suit_x(const StageRun *r) { return r->train.left + art(TRAIN_SUIT_ART); }
float train_tablet_x(const StageRun *r) { return r->train.left + art(TRAIN_TABLET_ART); }
float train_terminal_x(const StageRun *r) { return train_room_left(r, TRAIN_ROOMS - 1) + art(TRAIN_TERMINAL_ART); }
float train_exit_x(const StageRun *r) { return train_room_left(r, TRAIN_ROOMS - 1) + art(TRAIN_EXIT_ART); }

int train_supply_art(int room)
{
    switch (room) {
#define SUPPLY_CASE(index, x) case index: return x;
        TRAIN_SUPPLY_BAYS(SUPPLY_CASE)
#undef SUPPLY_CASE
    default: return -1;
    }
}

void train_install(StageRun *r)
{
    if (!r->train.present) return;
    Piece *train = NULL;
    for (int i = 0; i < r->terrain.count; i++)
        if (r->terrain.items[i].kind == TERRAIN_WALL && r->terrain.items[i].variant == FACADE_TRAIN)
            train = &r->terrain.items[i];
    if (!train) { r->train.present = false; return; }
    float from = train->x;
    float growth = TRAIN_W * SPRITE_SCALE + 160 * SPRITE_SCALE;
    for (int i = 0; i < r->terrain.count; i++) {
        Piece *p = &r->terrain.items[i];
        if (p != train && p->x > from) p->x += growth;
    }
    int first = r->train.first_zombie, count = r->train.zombie_count;
    r->train.left = from + 16 * SPRITE_SCALE;
    r->train.fumes = TRAIN_FUMES_TICK;
    r->train.right = r->train.left + TRAIN_ROOMS * span();
    for (int k = 0; k < r->zombie_count; k++) {
        if (k >= first && k < first + count) {
            int offset = k - first, room = offset / 2;
            r->zombies[k].x = r->train.left + (room + .5f + (offset % 2) * .15f) * span();
            r->group_of[k] = 40 + room;
            r->ambush_x[k] = 0;
            r->siren_of[k] = 0;
        } else {
            if (r->zombies[k].x > from) r->zombies[k].x += growth;
            if (r->ambush_x[k] > from) r->ambush_x[k] += growth;
        }
    }
    train->x = from + TRAIN_W * SPRITE_SCALE * .5f;
    train->spent = true; /* Passage is governed by boarding, never explosives. */
    r->goal_x += growth;
    /* The furniture has a dedicated clear floor bay in every other car. */
    for (int room = 1; room < TRAIN_CARS; room += 2)
        terrain_add(&r->terrain, TERRAIN_CRATE,
                    train_room_left(r, room) + art((float)train_supply_art(room)));
    /* Extending the road must not strand the existing container-seal clue. */
    for (int clue=0;clue<CLUE_COUNT;clue++) {
        if (CLUES[clue].stage!=TRAIN_STAGE || CLUES[clue].source!=CLUE_FROM_CRATE) continue;
        float at=r->start_x+CLUES[clue].at*(r->goal_x-r->start_x);
        if (at>=r->train.left && at<r->train.right) {
            int room=(int)((at-r->train.left)/span());
            int bay=train_supply_art(room);
            if (bay>=0) {
                float candidate=train_room_left(r,room)+art((float)bay);
                float share=(candidate-r->start_x)/(r->goal_x-r->start_x);
                if (casefile_crate_clue(TRAIN_STAGE,share)==clue) at=candidate;
            }
        }
        Piece *box=NULL;
        for (int i=0;i<r->terrain.count;i++)
            if (r->terrain.items[i].kind==TERRAIN_CRATE && fabsf(r->terrain.items[i].x-at)<CRATE_SPACING)
                box=&r->terrain.items[i];
        if (box) box->x=at;
        else terrain_add(&r->terrain,TERRAIN_CRATE,at);
    }
}

int train_room(const StageRun *r, float x)
{
    if (!r->train.present || !r->train.inside) return -1;
    int room = (int)floorf((x - r->train.left) / span());
    return room < 0 ? 0 : room >= TRAIN_ROOMS ? TRAIN_ROOMS - 1 : room;
}

static bool crew(const StageRun *r, int k)
{
    return k >= r->train.first_zombie && k < r->train.first_zombie + r->train.zombie_count && k < r->zombie_count;
}

int train_crew_left(const StageRun *r)
{
    int left = 0;
    for (int k = r->train.first_zombie; k < r->train.first_zombie + r->train.zombie_count; k++)
        left += k < r->zombie_count && zombie_alive(&r->zombies[k]);
    return left;
}

bool train_zombies_clear(const StageRun *r)
{
    return train_crew_left(r) == 0;
}

int train_crew_in_room(const StageRun *r, int room)
{
    int count = 0;
    for (int k = 0; k < r->zombie_count; k++) {
        if (!crew(r, k) || !zombie_alive(&r->zombies[k])) continue;
        int at = (int)floorf((r->zombies[k].x - r->train.left) / span());
        at = at < 0 ? 0 : at >= TRAIN_ROOMS ? TRAIN_ROOMS - 1 : at;
        count += at == room;
    }
    return count;
}

bool train_zombie_visible(const StageRun *r, int index)
{
    if (!r->train.present) return true;
    return crew(r, index) == r->train.inside;
}

int train_part_room(int part)
{
    static const int rooms[TRAIN_PARTS_ABOARD] = {1, 6, TRAIN_CARS}; /* Prototypes, cryo, machinery */
    return part >= 0 && part < TRAIN_PARTS_ABOARD ? rooms[part] : -1;
}

int train_parts_aboard(unsigned parts)
{
    return train_part_count(parts & TRAIN_PART_MASK);
}

bool train_part_position(const StageRun *r, int part, float *x)
{
    if (part < 0 || part >= EXPERIMENTAL_PARTS) return false;
    if (r->stage_index == TRAIN_STAGE && part < TRAIN_PARTS_ABOARD && r->train.present) {
        *x = train_room_left(r, train_part_room(part)) + art(TRAIN_CRADLE_ART + .5f);
        return true;
    }
    float share = 0;
    if (r->stage_index == 8 && part >= 3 && part <= 4) share = part == 3 ? .32f : .76f;
    if (r->stage_index == 9 && part >= 5) share = .26f + (part - 5) * .29f;
    if (share == 0) return false;
    *x = r->start_x + share * (r->goal_x - r->start_x);
    /* A quest component cannot land inside a road barrier or closed doorway. */
    for (int pass=0;pass<4;pass++) for (int i=0;i<r->terrain.count;i++) {
        const Piece *p=&r->terrain.items[i];
        float reach=terrain_piece_half_width(p)+PLAYER_BODY_HALF_WIDTH+24*SPRITE_SCALE;
        bool footprint=p->kind==TERRAIN_WALL || p->kind==TERRAIN_BARRICADE;
        if (footprint && fabsf(*x-p->x)<reach) *x=p->x-reach;
    }
    return true;
}

int train_part_near(const StageRun *r, const Player *p)
{
    if (r->stage_index == TRAIN_STAGE && !r->train.inside) return -1;
    for (int part = 0; part < EXPERIMENTAL_PARTS; part++) {
        float x;
        if (!(r->weapon_parts & (1u << part)) && train_part_position(r, part, &x) && near(p->x, x)) return part;
    }
    return -1;
}

bool train_room_toxic(int room)
{
    return room == 2 || room == 6; /* The cultures' smashed tank; the cryo pod that burst */
}

bool train_in_fumes(const StageRun *r, const Player *p)
{
    return r->train.present && r->train.inside && !r->train.suit && player_alive(p) &&
           train_room_toxic(train_room(r, p->x));
}

void train_update(StageRun *r, Player *p, float dt)
{
    if (!train_in_fumes(r, p)) {
        r->train.fumes = TRAIN_FUMES_TICK; /* A breath of clean air first, then a tick a second */
        return;
    }
    r->train.fumes -= dt;
    if (r->train.fumes > 0.0f) return;
    r->train.fumes += TRAIN_FUMES_TICK;
    player_fumes(p, TRAIN_FUMES_SHARE);
}

bool train_exit_open(const StageRun *r)
{
    return r->train.control_read && train_zombies_clear(r) &&
           (r->weapon_parts & TRAIN_PART_MASK) == TRAIN_PART_MASK;
}

TrainGoal train_next_goal(const StageRun *r, const Player *p, float *x)
{
    float best = 1e30f, at = p->x;
    if (r->train.present && !r->train.complete && !r->train.inside) {
        *x = train_entry_x(r);
        return run_fight_left(r) > 0 ? TRAIN_GOAL_YARD : TRAIN_GOAL_BOARD;
    }
    if (r->train.present && r->train.inside && !r->train.tablet) { /* The terminal's key, by the door */
        *x = train_tablet_x(r);
        return TRAIN_GOAL_TABLET;
    }
    int nearest = -1;
    for (int part = 0; part < EXPERIMENTAL_PARTS; part++) {
        float where;
        if (r->weapon_parts & (1u << part) || !train_part_position(r, part, &where)) continue;
        if (r->train.present && !r->train.inside) continue; /* The train's are behind her now */
        if (fabsf(where - p->x) < best) { best = fabsf(where - p->x); at = where; nearest = part; }
    }
    /* Parts and the terminal open the hatch together: whichever is closer. */
    bool terminal = r->train.present && r->train.inside && !r->train.control_read;
    if (terminal && fabsf(train_terminal_x(r) - p->x) < best) {
        *x = train_terminal_x(r);
        return TRAIN_GOAL_TERMINAL;
    }
    if (nearest >= 0) {
        *x = at;
        return r->train.inside ? TRAIN_GOAL_PART : TRAIN_GOAL_ROAD_PART;
    }
    if (!r->train.present || !r->train.inside) return TRAIN_GOAL_NONE;
    if (!train_zombies_clear(r)) {
        for (int k = 0; k < r->zombie_count; k++)
            if (crew(r, k) && zombie_alive(&r->zombies[k]) && fabsf(r->zombies[k].x - p->x) < best) {
                best = fabsf(r->zombies[k].x - p->x);
                at = r->zombies[k].x;
            }
        *x = at;
        return TRAIN_GOAL_CREW;
    }
    *x = train_exit_x(r);
    return TRAIN_GOAL_EXIT;
}

float train_camera(const StageRun *r, float camera)
{
    if (!r->train.present || !r->train.inside) return camera;
    float lo = r->train.left, hi = r->train.right - VIEW_WIDTH;
    return camera < lo ? lo : camera > hi ? hi : camera;
}

const char *train_prompt(const StageRun *r, const Player *p, TrainPromptKind *kind)
{
    static char line[96];
    *kind = TRAIN_PROMPT_USE;
    if (r->phase != RUN_FIGHTING || !player_alive(p) || p->jump.height > 0 ||
        p->state == PLAYER_CAR || p->state == PLAYER_CAUGHT || p->state == PLAYER_SIT) return NULL;
    int part = train_part_near(r,p);
    if (part >= 0) {
        snprintf(line, sizeof(line), "RECOGER PIEZA: %s", train_part_name(part));
        return line;
    }
    if (!r->train.present) return NULL;
    if (!r->train.inside && !r->train.complete && near(p->x, train_entry_x(r))) {
        int left = run_fight_left(r);
        if (left == 0) return "ENTRAR AL TREN LABORATORIO";
        *kind = TRAIN_PROMPT_BLOCKED;
        snprintf(line, sizeof(line), "PUERTA BLOQUEADA · %s %d EN EL PATIO", left == 1 ? "QUEDA" : "QUEDAN", left);
        return line;
    }
    if (!r->train.inside) return NULL;
    if (near(p->x, train_entry_x(r))) return r->train.suit ? "DEJAR EL TRAJE Y SALIR AL PATIO" : "SALIR AL PATIO";
    if (near(p->x, train_suit_x(r))) return r->train.suit ? "QUITARSE EL TRAJE" : "PONERSE UN TRAJE AISLANTE";
    if (!r->train.tablet && near(p->x, train_tablet_x(r))) return "TOMAR LA TABLETA · MAPA DEL TREN";
    if (near(p->x, train_terminal_x(r))) {
        if (!r->train.control_read) {
            if (r->train.tablet) return "CONECTAR LA TABLETA · LEER EL ARCHIVO 4";
            *kind = TRAIN_PROMPT_BLOCKED;
            return "TERMINAL BLOQUEADA · FALTA LA TABLETA DEL VAGÓN 01";
        }
        *kind = TRAIN_PROMPT_DONE;
        return "ARCHIVO 4 LEÍDO: CERRO GRIS, BÚNKER 2";
    }
    if (near(p->x, train_exit_x(r))) {
        int parts = TRAIN_PARTS_ABOARD - train_parts_aboard(r->weapon_parts);
        int crew_left = train_crew_left(r);
        *kind = TRAIN_PROMPT_BLOCKED;
        if (!r->train.control_read) return "SALIDA CERRADA · LEE EL ARCHIVO 4";
        if (parts > 0) {
            snprintf(line, sizeof(line), "SALIDA CERRADA · %s %d %s", parts == 1 ? "FALTA" : "FALTAN", parts,
                     parts == 1 ? "PIEZA" : "PIEZAS");
            return line;
        }
        if (crew_left > 0) {
            snprintf(line, sizeof(line), "SALIDA CERRADA · %s %d %s", crew_left == 1 ? "QUEDA" : "QUEDAN",
                     crew_left, crew_left == 1 ? "INFECTADO" : "INFECTADOS");
            return line;
        }
        *kind = TRAIN_PROMPT_USE;
        return "SALIR DEL TREN Y CONTINUAR";
    }
    return NULL;
}

bool train_use(StageRun *r, Player *p)
{
    TrainPromptKind kind;
    if (!train_prompt(r,p,&kind)) return false;
    int part = train_part_near(r,p);
    if (part >= 0) { r->weapon_parts |= 1u << part; return true; }
    if (!r->train.inside && !r->train.complete && near(p->x,train_entry_x(r))) {
        if (run_fight_left(r) == 0) {
            r->train.inside = true;
            p->x = train_entry_x(r) + 36 * SPRITE_SCALE;
        }
    } else if (r->train.inside && near(p->x,train_entry_x(r))) {
        r->train.inside = false;
        r->train.suit = false; /* Left in the decontamination capsule */
        p->x = train_entry_x(r) - 12 * SPRITE_SCALE;
    } else if (r->train.inside && near(p->x,train_suit_x(r))) {
        r->train.suit = !r->train.suit;
    } else if (r->train.inside && !r->train.tablet && near(p->x,train_tablet_x(r))) {
        r->train.tablet = true;
    } else if (r->train.inside && near(p->x,train_terminal_x(r))) {
        if (r->train.tablet) r->train.control_read = true;
    } else if (r->train.inside && near(p->x,train_exit_x(r)) && train_exit_open(r)) {
        r->train.complete = true;
        r->train.inside = false;
        r->train.suit = false; /* Hung in the hatch's airlock */
        p->x = r->train.right + 80 * SPRITE_SCALE;
    }
    return true; /* A locked terminal/exit still consumes E; never plants dynamite. */
}

const char *train_room_name(int room)
{
    static const char *const names[TRAIN_ROOMS] = {"DESCONTAMINACIÓN", "PROTOTIPOS", "CULTIVOS MRC-2",
        "CIRUGÍA", "ANÁLISIS", "CONTENCIÓN", "CRIOGENIA", "ARCHIVO MÓVIL", "DORMITORIO", "COMEDOR",
        "ENFERMERÍA", "ARMERÍA", "COMUNICACIONES", "MÁQUINAS", "CONTROL"};
    return room >= 0 && room < TRAIN_ROOMS ? names[room] : "TREN LABORATORIO 4-G";
}

const char *train_part_name(int part)
{
    static const char *const names[EXPERIMENTAL_PARTS] = {"CÁMARA DE PLASMA", "BOBINA CRIOGÉNICA",
        "CELDA DE POTENCIA", "REGULADOR", "LENTE DE ENFOQUE", "INYECTOR", "AISLANTE", "NÚCLEO DE CONTROL"};
    return part >= 0 && part < EXPERIMENTAL_PARTS ? names[part] : "PROTOTIPO";
}

int train_part_count(unsigned parts)
{
    int count = 0;
    for (int k = 0; k < EXPERIMENTAL_PARTS; k++) count += (parts >> k) & 1u;
    return count;
}
