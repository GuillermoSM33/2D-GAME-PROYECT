#ifndef APP_SAVEGAME_H
#define APP_SAVEGAME_H

#include <stddef.h>
#include <stdint.h>
#include "app/state.h"

#define SAVE_GAME_CAPACITY (128u * 1024u)

/* No raw struct dumps: savegame.c defines a versioned, little-endian schema.
 * Static references are stored as catalogue IDs, ricochet targets as indices.
 * Cosmetic smoke, particles and streamed scenery are regenerated on resume. */
typedef struct {
    Profile profiles[APP_PROFILE_CAPACITY];
    int hero;
    Volumes volumes;
    bool has_checkpoint;
    int checkpoint_hero;
    StagePlay checkpoint;
    int bullet_targets[BULLET_MAX];
} SaveGame;

void save_game_init(SaveGame *game);
void save_game_snapshot(SaveGame *game, const Profile *profiles, int hero,
                         const Volumes *volumes, const StagePlay *active);
bool save_game_encode(SaveGame *game, unsigned char *bytes, size_t capacity, size_t *size);
/* Transactional: a rejected file never changes output. Also a StorageValidator. */
bool save_game_decode(const unsigned char *bytes, size_t size, void *output);
bool save_game_resume(const SaveGame *game, StagePlay *play, int hero, int stage);
/* Starting another mission abandons the pending attempt with normal rollback. */
void save_game_abandon(SaveGame *game, Profile *profiles);

#endif
