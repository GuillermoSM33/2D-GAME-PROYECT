#ifndef APP_AUTOSAVE_H
#define APP_AUTOSAVE_H

#include "app/savegame.h"
#include "engine/storage.h"

#define AUTOSAVE_SECONDS (15.0 * 60.0)

typedef struct {
    Storage *store;
    SaveGame game;
    unsigned char bytes[SAVE_GAME_CAPACITY];
    double elapsed;
    float feedback_time, feedback_age, retry_wait;
    uint64_t submitted, observed;
    bool enabled, saving, failed;
} Autosave;

StorageLoad autosave_init(Autosave *save, bool enabled, const char *directory);
/* Counts real, active gameplay time. Menus, pause and the book do not count.
 * Returns true when the caller should capture its latest live state. */
bool autosave_tick(Autosave *save, double seconds, bool playing);
bool autosave_request(Autosave *save, const Profile *profiles, int hero,
                       const Volumes *volumes, const StagePlay *active);
void autosave_shutdown(Autosave *save);

#endif
