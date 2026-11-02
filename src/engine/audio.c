#include "engine/audio.h"

#include <stdio.h>
#include <string.h>

#include <SDL.h>
#include <SDL_mixer.h>

#include "config.h"
#include "engine/assets.h"

#define MAX_SOUNDS 32
#define SOUNDS_PREFIX "sounds/"

typedef struct {
    const char *name; /* Without SOUNDS_PREFIX */
    Mix_Chunk *chunk;
} LoadedSound;

static LoadedSound sounds[MAX_SOUNDS];
static int sound_count;
static bool ready;
static float master = 1.0f;
static float groups[AUDIO_GROUPS] = {1.0f, 1.0f, 1.0f, 1.0f};

bool audio_init(void)
{
    if (SDL_InitSubSystem(SDL_INIT_AUDIO) != 0) {
        fprintf(stderr, "Sin audio (%s); el juego sigue sin sonido.\n", SDL_GetError());
        return false;
    }
    if (Mix_OpenAudio(AUDIO_RATE, AUDIO_S16SYS, 2, AUDIO_BUFFER) != 0) {
        fprintf(stderr, "Sin audio (%s); el juego sigue sin sonido.\n", Mix_GetError());
        SDL_QuitSubSystem(SDL_INIT_AUDIO);
        return false;
    }
    Mix_AllocateChannels(AUDIO_CHANNELS);
    size_t prefix_len = strlen(SOUNDS_PREFIX);
    for (int i = 0; i < embedded_blob_count && sound_count < MAX_SOUNDS; i++) {
        const EmbeddedBlob *blob = &embedded_blobs[i];
        if (strncmp(blob->name, SOUNDS_PREFIX, prefix_len) != 0)
            continue;
        SDL_RWops *rw = SDL_RWFromConstMem(blob->data, (int)blob->size);
        Mix_Chunk *chunk = rw ? Mix_LoadWAV_RW(rw, 1) : NULL;
        if (chunk == NULL) {
            fprintf(stderr, "No se pudo cargar '%s': %s\n", blob->name, Mix_GetError());
            continue;
        }
        Mix_VolumeChunk(chunk, SFX_VOLUME);
        sounds[sound_count].name = blob->name + prefix_len;
        sounds[sound_count].chunk = chunk;
        sound_count++;
    }
    ready = true;
    return true;
}

void audio_shutdown(void)
{
    if (!ready)
        return;
    Mix_HaltChannel(-1);
    for (int i = 0; i < sound_count; i++)
        Mix_FreeChunk(sounds[i].chunk);
    sound_count = 0;
    Mix_CloseAudio();
    SDL_QuitSubSystem(SDL_INIT_AUDIO);
    ready = false;
}

void audio_play(const char *name)
{
    audio_play_in(name, 0);
}

void audio_play_in(const char *name, int group)
{
    if (group < 0 || group >= AUDIO_GROUPS)
        group = 0;
    for (int i = 0; i < sound_count; i++) {
        if (strcmp(sounds[i].name, name) == 0) {
            int channel = Mix_PlayChannel(-1, sounds[i].chunk, 0);
            if (channel >= 0)
                Mix_Volume(channel, (int)(MIX_MAX_VOLUME * master * groups[group] + 0.5f));
            return;
        }
    }
}

static float clamp01(float v)
{
    return v < 0.0f ? 0.0f : v > 1.0f ? 1.0f : v;
}

void audio_set_master(float volume)
{
    master = clamp01(volume);
}

void audio_set_group(int group, float volume)
{
    if (group >= 0 && group < AUDIO_GROUPS)
        groups[group] = clamp01(volume);
}
