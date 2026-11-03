#include "game/almanac.h"

#include <limits.h>
#include <math.h>
#include <string.h>

static bool valid_entry(int entry)
{
    return entry >= 0 && entry < ALMANAC_ENTRIES;
}

static int valid_level(int level)
{
    return level < 1 ? 1 : level > MAX_LEVEL ? MAX_LEVEL : level;
}

static void increment(int *value)
{
    if (*value < INT_MAX)
        (*value)++;
}

void almanac_init(Almanac *book)
{
    memset(book, 0, sizeof(*book));
}

void almanac_encounter_start(AlmanacEncounter *encounter)
{
    for (int i = 0; i < RUN_MAX_ZOMBIES; i++) {
        encounter->entry[i] = -1;
        encounter->defeated[i] = false;
    }
}

int almanac_index(ZombieKind kind, bool runner)
{
    return kind >= 0 && kind < ZOMBIE_KIND_COUNT ? (int)kind * 2 + (runner ? 1 : 0) : -1;
}

ZombieKind almanac_kind(int entry)
{
    return valid_entry(entry) ? (ZombieKind)(entry / 2) : ZOMBIE_KIND_COUNT;
}

bool almanac_runner(int entry)
{
    return valid_entry(entry) && (entry % 2) != 0;
}

const AlmanacEntry *almanac_entry(const Almanac *book, int entry)
{
    return book && valid_entry(entry) ? &book->entries[entry] : NULL;
}

int almanac_count(const Almanac *book)
{
    int count = 0;
    if (book)
        for (int i = 0; i < ALMANAC_ENTRIES; i++)
            count += book->entries[i].discovered ? 1 : 0;
    return count;
}

bool almanac_discover(Almanac *book, ZombieKind kind, bool runner, int level)
{
    int index = almanac_index(kind, runner);
    if (!book || index < 0)
        return false;
    AlmanacEntry *entry = &book->entries[index];
    bool fresh = !entry->discovered;
    entry->discovered = true;
    increment(&entry->seen);
    level = valid_level(level);
    if (entry->max_level < level)
        entry->max_level = level;
    return fresh;
}

bool almanac_record_kill(Almanac *book, ZombieKind kind, bool runner)
{
    int index = almanac_index(kind, runner);
    if (!book || index < 0 || !book->entries[index].discovered)
        return false;
    increment(&book->entries[index].defeated);
    return true;
}

int almanac_observe(Almanac *book, AlmanacEncounter *encounter, const Zombie *zombies,
                    int count, float camera_x, float view_width)
{
    if (!book || !encounter || !zombies || count <= 0 || !isfinite(camera_x) ||
        !isfinite(view_width) || view_width <= 0.0f)
        return 0;
    if (count > RUN_MAX_ZOMBIES)
        count = RUN_MAX_ZOMBIES;
    int discoveries = 0;
    for (int i = 0; i < count; i++) {
        const Zombie *z = &zombies[i];
        int index = almanac_index(z->kind, z->runner);
        if (!z->stats || index < 0)
            continue;
        bool alive = zombie_alive(z);
        bool visible = alive && z->awake && !z->hidden &&
                       zombie_overlaps(z, camera_x, camera_x + view_width, BASELINE);
        if (visible) {
            if (encounter->entry[i] != index || encounter->defeated[i]) {
                discoveries += almanac_discover(book, z->kind, z->runner, z->level) ? 1 : 0;
                encounter->entry[i] = index;
                encounter->defeated[i] = false;
            } else if (book->entries[index].max_level < valid_level(z->level)) {
                book->entries[index].max_level = valid_level(z->level);
            }
        }
        if (!alive && encounter->entry[i] == index && !encounter->defeated[i]) {
            almanac_record_kill(book, z->kind, z->runner);
            encounter->defeated[i] = true;
        }
    }
    return discoveries;
}

bool almanac_stats_at(const Almanac *book, int index, bool observed, AlmanacStats *stats)
{
    if (!stats)
        return false;
    memset(stats, 0, sizeof(*stats));
    const AlmanacEntry *entry = almanac_entry(book, index);
    if (!entry || !entry->discovered)
        return false;
    Zombie specimen;
    zombie_spawn(&specimen, zombie_stats(almanac_kind(index), almanac_runner(index)), 0.0f);
    zombie_set_level(&specimen, observed ? valid_level(entry->max_level) : 1);
    stats->level = specimen.level;
    stats->health = specimen.max_health;
    stats->damage = zombie_attack_damage(&specimen);
    stats->armor = specimen.armor;
    stats->speed = specimen.stats->speed * ZOMBIE_SPEED;
    return true;
}

void almanac_view_init(AlmanacView *view)
{
    memset(view, 0, sizeof(*view));
}

void almanac_view_select(AlmanacView *view, int entry)
{
    if (entry < 0)
        entry = 0;
    if (entry >= ALMANAC_ENTRIES)
        entry = ALMANAC_ENTRIES - 1;
    view->selected = entry;
    view->scroll = (entry / ALMANAC_PAGE_SIZE) * ALMANAC_PAGE_SIZE;
}

int almanac_pages(void)
{
    return (ALMANAC_ENTRIES + ALMANAC_PAGE_SIZE - 1) / ALMANAC_PAGE_SIZE;
}

int almanac_hit(const AlmanacView *view, int x, int y)
{
    if (!view || view->detail || x < ALMANAC_GRID_X || y < ALMANAC_GRID_Y)
        return -1;
    int column = (x - ALMANAC_GRID_X) / (ALMANAC_CARD_W + ALMANAC_CARD_GAP);
    int row = (y - ALMANAC_GRID_Y) / (ALMANAC_CARD_H + ALMANAC_CARD_GAP);
    if (column >= ALMANAC_COLUMNS || row >= ALMANAC_ROWS ||
        (x - ALMANAC_GRID_X) % (ALMANAC_CARD_W + ALMANAC_CARD_GAP) >= ALMANAC_CARD_W ||
        (y - ALMANAC_GRID_Y) % (ALMANAC_CARD_H + ALMANAC_CARD_GAP) >= ALMANAC_CARD_H)
        return -1;
    int entry = view->scroll + row * ALMANAC_COLUMNS + column;
    return valid_entry(entry) ? entry : -1;
}

static bool inside(int x, int y, int left, int top, int w, int h)
{
    return x >= left && x < left + w && y >= top && y < top + h;
}

bool almanac_view_update(AlmanacView *view, const InputState *input)
{
    if (input->pressed[ACTION_QUIT]) {
        if (!view->detail)
            return false;
        view->detail = false;
        return true;
    }
    int selected = valid_entry(view->selected) ? view->selected : 0;
    if (input->pressed[ACTION_LEFT])
        selected = (selected + ALMANAC_ENTRIES - 1) % ALMANAC_ENTRIES;
    if (input->pressed[ACTION_RIGHT])
        selected = (selected + 1) % ALMANAC_ENTRIES;
    if (input->pressed[ACTION_UP]) {
        if (selected >= ALMANAC_COLUMNS)
            selected -= ALMANAC_COLUMNS;
        else {
            int column = selected % ALMANAC_COLUMNS;
            selected = ((ALMANAC_ENTRIES - 1) / ALMANAC_COLUMNS) * ALMANAC_COLUMNS + column;
            if (selected >= ALMANAC_ENTRIES)
                selected -= ALMANAC_COLUMNS;
        }
    }
    if (input->pressed[ACTION_DOWN])
        selected = selected + ALMANAC_COLUMNS < ALMANAC_ENTRIES
                       ? selected + ALMANAC_COLUMNS : selected % ALMANAC_COLUMNS;
    if (!view->detail && (input->pointer_moved || input->pointer_clicked)) {
        int hit = almanac_hit(view, input->pointer_x, input->pointer_y);
        if (hit >= 0) {
            selected = hit;
            if (input->pointer_clicked)
                view->detail = true;
        }
    }
    if (input->pointer_clicked) {
        if (inside(input->pointer_x, input->pointer_y, WINDOW_WIDTH - 194,
                   ALMANAC_FOOTER_Y, 170, 42)) {
            if (!view->detail)
                return false;
            view->detail = false;
        } else if (!view->detail && inside(input->pointer_x, input->pointer_y,
                   ALMANAC_GRID_X, ALMANAC_PAGE_Y, 44, 30)) {
            int page = (selected / ALMANAC_PAGE_SIZE + almanac_pages() - 1) % almanac_pages();
            selected = page * ALMANAC_PAGE_SIZE;
        } else if (!view->detail && inside(input->pointer_x, input->pointer_y,
                   ALMANAC_GRID_X + ALMANAC_GRID_W - 44, ALMANAC_PAGE_Y, 44, 30)) {
            int page = (selected / ALMANAC_PAGE_SIZE + 1) % almanac_pages();
            selected = page * ALMANAC_PAGE_SIZE;
        }
    }
    almanac_view_select(view, selected);
    if (input->pressed[ACTION_CONFIRM])
        view->detail = !view->detail;
    return true;
}
