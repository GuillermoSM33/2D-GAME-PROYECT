#ifndef ENGINE_STORAGE_H
#define ENGINE_STORAGE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* Opaque byte storage: knows nothing about game rules or save schemas.
 * A single worker writes alternate slots, never the currently valid slot.
 * A complete temporary file is published with rename only after fclose. */
typedef struct Storage Storage;
typedef bool (*StorageValidator)(const unsigned char *data, size_t size, void *context);
typedef enum { STORAGE_EMPTY, STORAGE_LOADED, STORAGE_RECOVERED, STORAGE_INVALID } StorageLoad;

/* NULL directory selects SDL_GetPrefPath, shared with engine/prefs.
 * A supplied directory must already exist (useful for isolated tests). */
Storage *storage_open(const char *directory);
StorageLoad storage_load(Storage *store, StorageValidator validate, void *context);

/* Copies a snapshot into the worker queue. No file I/O or waiting here.
 * A pending, not-yet-started snapshot may be replaced by a newer one. */
uint64_t storage_submit(Storage *store, const void *data, size_t size);
bool storage_busy(Storage *store);
bool storage_result(Storage *store, uint64_t *completed, bool *success);

/* Finishes the last queued snapshot and joins the worker on application exit. */
bool storage_close(Storage *store);

#endif
