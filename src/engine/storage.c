#include "engine/storage.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <SDL.h>
#ifdef _WIN32
#include <wchar.h>
#endif

#define STORAGE_LIMIT (1024u * 1024u)
#define HEADER_SIZE 24

struct Storage {
    char *directory;
    SDL_Thread *thread;
    SDL_mutex *mutex;
    SDL_cond *wake;
    unsigned char *pending;
    size_t pending_size;
    uint64_t submitted, pending_id, completed, generation;
    int active_slot;
    bool working, stopping, success;
};

static const unsigned char MAGIC[8] = {'V', 'A', 'Q', 'D', 'A', 'T', 'A', 1};

/* SDL returns UTF-8 paths. Use the Windows CRT's wide path functions there,
 * including slot publication, so accented Windows user names also work. */
static FILE *open_file(const char *path, bool writing)
{
#ifdef _WIN32
    wchar_t *wide = (wchar_t *)SDL_iconv_string("UTF-16LE", "UTF-8", path, strlen(path) + 1);
    FILE *file = wide ? _wfopen(wide, writing ? L"wb" : L"rb") : NULL;
    SDL_free(wide);
    return file;
#else
    return fopen(path, writing ? "wb" : "rb");
#endif
}

static void remove_file(const char *path)
{
#ifdef _WIN32
    wchar_t *wide = (wchar_t *)SDL_iconv_string("UTF-16LE", "UTF-8", path, strlen(path) + 1);
    if (wide) _wremove(wide);
    SDL_free(wide);
#else
    remove(path);
#endif
}

static bool publish_file(const char *temp, const char *path)
{
#ifdef _WIN32
    wchar_t *from = (wchar_t *)SDL_iconv_string("UTF-16LE", "UTF-8", temp, strlen(temp) + 1);
    wchar_t *to = (wchar_t *)SDL_iconv_string("UTF-16LE", "UTF-8", path, strlen(path) + 1);
    bool ok = from && to && _wrename(from, to) == 0;
    SDL_free(from);
    SDL_free(to);
    return ok;
#else
    return rename(temp, path) == 0;
#endif
}

static uint32_t read32(const unsigned char *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

static void write32(unsigned char *p, uint32_t value)
{
    for (int i = 0; i < 4; i++)
        p[i] = (unsigned char)(value >> (i * 8));
}

static uint32_t crc32(const unsigned char *data, size_t size, uint32_t crc)
{
    for (size_t i = 0; i < size; i++) {
        crc ^= data[i];
        for (int bit = 0; bit < 8; bit++)
            crc = (crc >> 1) ^ (0xedb88320u & (0u - (crc & 1u)));
    }
    return crc;
}

static char *slot_path(const Storage *s, int slot, bool temporary)
{
    size_t count = strlen(s->directory) + 40;
    char *path = malloc(count);
    if (path)
        snprintf(path, count, "%s/avance_%c.sav%s", s->directory, 'a' + slot, temporary ? ".tmp" : "");
    return path;
}

static unsigned char *read_slot(Storage *s, int slot, size_t *size, uint64_t *generation, bool *exists)
{
    char *path = slot_path(s, slot, false);
    FILE *file = path ? open_file(path, false) : NULL;
    free(path);
    if (!file)
        return NULL;
    *exists = true;
    unsigned char header[HEADER_SIZE], *data = NULL;
    if (fread(header, 1, sizeof(header), file) != sizeof(header) || memcmp(header, MAGIC, 8))
        goto finish;
    *size = read32(header + 16);
    *generation = (uint64_t)read32(header + 8) | (uint64_t)read32(header + 12) << 32;
    if (!*size || *size > STORAGE_LIMIT || !*generation)
        goto finish;
    data = malloc(*size);
    if (!data)
        goto finish;
    if (fread(data, 1, *size, file) != *size || fgetc(file) != EOF || ferror(file) ||
        ~crc32(data, *size, crc32(header, 20, 0xffffffffu)) != read32(header + 20)) {
        free(data);
        data = NULL;
    }
finish:
    fclose(file);
    return data;
}

StorageLoad storage_load(Storage *s, StorageValidator validate, void *context)
{
    if (!s || !validate || storage_busy(s))
        return STORAGE_INVALID;
    unsigned char *data[2];
    size_t size[2] = {0};
    uint64_t generation[2] = {0};
    bool exists[2] = {false};
    for (int i = 0; i < 2; i++)
        data[i] = read_slot(s, i, &size[i], &generation[i], &exists[i]);
    int first = generation[1] > generation[0] ? 1 : 0, selected = -1;
    bool rejected = (exists[0] && !data[0]) || (exists[1] && !data[1]);
    for (int order = 0; order < 2; order++) {
        int i = order == 0 ? first : 1 - first;
        if (data[i] && validate(data[i], size[i], context)) {
            selected = i;
            break;
        }
        rejected |= exists[i];
    }
    if (selected >= 0) {
        SDL_LockMutex(s->mutex);
        s->active_slot = selected;
        s->generation = generation[selected];
        SDL_UnlockMutex(s->mutex);
    }
    free(data[0]);
    free(data[1]);
    return selected >= 0 ? (rejected ? STORAGE_RECOVERED : STORAGE_LOADED)
                         : exists[0] || exists[1] ? STORAGE_INVALID : STORAGE_EMPTY;
}

static bool write_slot(Storage *s, int slot, const unsigned char *data, size_t size, uint64_t generation)
{
    char *path = slot_path(s, slot, false), *temp = slot_path(s, slot, true);
    FILE *file = temp ? open_file(temp, true) : NULL;
    bool ok = file && path;
    unsigned char header[HEADER_SIZE];
    memcpy(header, MAGIC, 8);
    write32(header + 8, (uint32_t)generation);
    write32(header + 12, (uint32_t)(generation >> 32));
    write32(header + 16, (uint32_t)size);
    write32(header + 20, ~crc32(data, size, crc32(header, 20, 0xffffffffu)));
    if (file) {
        ok = ok && fwrite(header, 1, sizeof(header), file) == sizeof(header) &&
             fwrite(data, 1, size, file) == size;
        if (fflush(file) != 0)
            ok = false;
        if (fclose(file) != 0)
            ok = false;
    }
    if (ok) {
        /* Windows rename cannot replace an existing file. Only the inactive
         * slot is removed; the last accepted save remains untouched. */
        remove_file(path);
        ok = publish_file(temp, path);
    }
    if (!ok && temp)
        remove_file(temp);
    free(path);
    free(temp);
    return ok;
}

static int worker(void *context)
{
    Storage *s = context;
    SDL_LockMutex(s->mutex);
    for (;;) {
        while (!s->pending && !s->stopping)
            SDL_CondWait(s->wake, s->mutex);
        if (!s->pending && s->stopping)
            break;
        unsigned char *data = s->pending;
        size_t size = s->pending_size;
        uint64_t id = s->pending_id, generation = s->generation + 1;
        int slot = s->active_slot == 0 ? 1 : 0;
        s->pending = NULL;
        s->working = true;
        SDL_UnlockMutex(s->mutex);
        bool ok = generation != 0 && write_slot(s, slot, data, size, generation);
        free(data);
        SDL_LockMutex(s->mutex);
        if (ok) {
            s->generation = generation;
            s->active_slot = slot;
        }
        s->completed = id;
        s->success = ok;
        s->working = false;
    }
    SDL_UnlockMutex(s->mutex);
    return 0;
}

Storage *storage_open(const char *directory)
{
    Storage *s = calloc(1, sizeof(*s));
    if (!s)
        return NULL;
    s->active_slot = -1;
    if (directory)
        s->directory = SDL_strdup(directory);
    else
        s->directory = SDL_GetPrefPath("TheMiracle", "TheMiracle");
    s->mutex = SDL_CreateMutex();
    s->wake = SDL_CreateCond();
    if (s->directory && s->mutex && s->wake)
        s->thread = SDL_CreateThread(worker, "autosave", s);
    if (!s->thread) {
        storage_close(s);
        return NULL;
    }
    return s;
}

uint64_t storage_submit(Storage *s, const void *data, size_t size)
{
    if (!s || !data || !size || size > STORAGE_LIMIT)
        return 0;
    unsigned char *copy = malloc(size);
    if (!copy)
        return 0;
    memcpy(copy, data, size);
    SDL_LockMutex(s->mutex);
    free(s->pending);
    s->pending = copy;
    s->pending_size = size;
    s->pending_id = ++s->submitted;
    uint64_t id = s->pending_id;
    SDL_CondSignal(s->wake);
    SDL_UnlockMutex(s->mutex);
    return id;
}

bool storage_busy(Storage *s)
{
    if (!s)
        return false;
    SDL_LockMutex(s->mutex);
    bool busy = s->working || s->pending;
    SDL_UnlockMutex(s->mutex);
    return busy;
}

bool storage_result(Storage *s, uint64_t *completed, bool *success)
{
    if (!s)
        return false;
    SDL_LockMutex(s->mutex);
    *completed = s->completed;
    *success = s->success;
    SDL_UnlockMutex(s->mutex);
    return *completed != 0;
}

bool storage_close(Storage *s)
{
    if (!s)
        return false;
    if (s->thread) {
        SDL_LockMutex(s->mutex);
        s->stopping = true;
        SDL_CondSignal(s->wake);
        SDL_UnlockMutex(s->mutex);
        SDL_WaitThread(s->thread, NULL);
    }
    if (s->wake)
        SDL_DestroyCond(s->wake);
    if (s->mutex)
        SDL_DestroyMutex(s->mutex);
    free(s->pending);
    SDL_free(s->directory);
    bool success = s->submitted == 0 || (s->completed == s->submitted && s->success);
    free(s);
    return success;
}
