#include "engine/audio.h"

#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <SDL.h>
#include <SDL_mixer.h>

#include "config.h"
#include "engine/assets.h"

#define SOUNDS_PREFIX "sounds/"
#define LOOP_CHANNELS 4 /* Wind, rain, river and fire keep playing under effects. */

typedef struct {
    const char *name; /* Without SOUNDS_PREFIX */
    Mix_Chunk *chunk;
} LoadedSound;

typedef struct {
    const LoadedSound *sound;
    int group;
    float gain;
    bool paused;
} Channel;

static LoadedSound *sounds;
static int sound_count;
static Channel channels[AUDIO_CHANNELS];
static bool ready;
static bool stage_paused;
static float master = 1.0f;
static float groups[AUDIO_GROUPS] = {1.0f, 1.0f, 1.0f, 1.0f};
static float music_level = 1.0f;
static Mix_Music *music;
static const char *music_name;
static const char *music_failed; /* Asked for every frame in menus: only say so once */

static float clamp01(float v)
{
    /* Also treats NaN as silence, instead of converting it to an integer. */
    return !(v > 0.0f) ? 0.0f : v > 1.0f ? 1.0f : v;
}

static int valid_group(int group)
{
    return group >= 0 && group < AUDIO_GROUPS ? group : 0;
}

static void channel_volume(int channel)
{
    const Channel *c = &channels[channel];
    Mix_Volume(channel, (int)(MIX_MAX_VOLUME * master * groups[c->group] * c->gain + 0.5f));
}

static const LoadedSound *find_sound(const char *name)
{
    if (!ready || name == NULL)
        return NULL;
    for (int i = 0; i < sound_count; i++)
        if (strcmp(sounds[i].name, name) == 0)
            return &sounds[i];
    return NULL;
}

bool audio_init(void)
{
    if (ready)
        return true;
    if (SDL_InitSubSystem(SDL_INIT_AUDIO) != 0) {
        fprintf(stderr, "Sin audio (%s); el juego sigue sin sonido.\n", SDL_GetError());
        return false;
    }
    if (Mix_OpenAudio(AUDIO_RATE, AUDIO_S16SYS, 2, AUDIO_BUFFER) != 0) {
        fprintf(stderr, "Sin audio (%s); el juego sigue sin sonido.\n", Mix_GetError());
        SDL_QuitSubSystem(SDL_INIT_AUDIO);
        return false;
    }
    if (Mix_AllocateChannels(AUDIO_CHANNELS) < AUDIO_CHANNELS) {
        fprintf(stderr, "Sin audio (no se pudieron reservar los canales); el juego sigue sin sonido.\n");
        Mix_CloseAudio();
        SDL_QuitSubSystem(SDL_INIT_AUDIO);
        return false;
    }
    Mix_ReserveChannels(LOOP_CHANNELS);
    memset(channels, 0, sizeof(channels));
    size_t prefix_len = strlen(SOUNDS_PREFIX);
    int capacity = 0;
    for (int i = 0; i < embedded_blob_count; i++)
        if (strncmp(embedded_blobs[i].name, SOUNDS_PREFIX, prefix_len) == 0)
            capacity++;
    sounds = calloc((size_t)(capacity > 0 ? capacity : 1), sizeof(*sounds));
    if (sounds == NULL) {
        fprintf(stderr, "Sin audio (sin memoria para los sonidos); el juego sigue sin sonido.\n");
        Mix_CloseAudio();
        SDL_QuitSubSystem(SDL_INIT_AUDIO);
        return false;
    }
    for (int i = 0; i < embedded_blob_count; i++) {
        const EmbeddedBlob *blob = &embedded_blobs[i];
        if (strncmp(blob->name, SOUNDS_PREFIX, prefix_len) != 0)
            continue;
        SDL_RWops *rw = blob->size <= INT_MAX ? SDL_RWFromConstMem(blob->data, (int)blob->size) : NULL;
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

void audio_stop_all(void)
{
    if (!ready)
        return;
    Mix_HaltChannel(-1);
    memset(channels, 0, sizeof(channels));
    stage_paused = false;
}

void audio_pause(bool paused)
{
    if (!ready || stage_paused == paused)
        return;
    stage_paused = paused;
    for (int ch = 0; ch < AUDIO_CHANNELS; ch++) {
        if (paused && Mix_Playing(ch)) {
            channels[ch].paused = true;
            Mix_Pause(ch);
        } else if (!paused && channels[ch].paused) {
            channels[ch].paused = false;
            Mix_Resume(ch);
        }
    }
}

static void music_volume(void)
{
    Mix_VolumeMusic((int)(MUSIC_VOLUME * master * music_level + 0.5f));
}

static void music_release(void)
{
    if (music == NULL)
        return;
    Mix_HaltMusic(); /* First: freeing a track that is fading would wait for the fade */
    Mix_FreeMusic(music);
    music = NULL;
    music_name = NULL;
}

void audio_music_play(const char *name)
{
    if (!ready || name == NULL)
        return;
    if (music_name && strcmp(music_name, name) == 0 && Mix_PlayingMusic() && Mix_FadingMusic() != MIX_FADING_OUT)
        return;
    if (music_failed && strcmp(music_failed, name) == 0)
        return;
    music_release();
    const EmbeddedBlob *blob = NULL;
    for (int i = 0; i < embedded_blob_count && blob == NULL; i++)
        if (strcmp(embedded_blobs[i].name, name) == 0)
            blob = &embedded_blobs[i];
    SDL_RWops *rw = blob && blob->size <= INT_MAX ? SDL_RWFromConstMem(blob->data, (int)blob->size) : NULL;
    music = rw ? Mix_LoadMUS_RW(rw, 1) : NULL;
    if (music == NULL || Mix_PlayMusic(music, -1) != 0) {
        fprintf(stderr, "No se pudo reproducir '%s': %s\n", name, Mix_GetError());
        music_release();
        music_failed = name;
        return;
    }
    music_name = blob->name;
    music_volume();
}

void audio_music_stop(int fade_ms)
{
    if (!ready || music == NULL)
        return;
    if (fade_ms > 0 && Mix_PlayingMusic()) {
        if (Mix_FadingMusic() != MIX_FADING_OUT)
            Mix_FadeOutMusic(fade_ms);
    } else {
        music_release();
    }
}

void audio_set_music(float volume)
{
    music_level = clamp01(volume);
    if (ready)
        music_volume();
}

void audio_shutdown(void)
{
    if (!ready)
        return;
    audio_stop_all();
    music_release();
    for (int i = 0; i < sound_count; i++)
        Mix_FreeChunk(sounds[i].chunk);
    free(sounds);
    sounds = NULL;
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
    audio_play_in_gain(name, group, 1.0f);
}

void audio_play_in_gain(const char *name, int group, float gain)
{
    const LoadedSound *sound = find_sound(name);
    if (sound == NULL)
        return;
    for (int ch = LOOP_CHANNELS; ch < AUDIO_CHANNELS; ch++) {
        if (Mix_Playing(ch))
            continue;
        channels[ch] = (Channel){sound, valid_group(group), clamp01(gain), false};
        /* Set before playback, so reusing a loud channel cannot briefly make
         * a quiet footstep or ambience burst at its previous volume. */
        channel_volume(ch);
        Mix_PlayChannel(ch, sound->chunk, 0);
        return;
    }
    /* When every effect channel is busy, leave the playing sounds intact. */
}

void audio_loop_in(const char *name, int group, float gain)
{
    const LoadedSound *sound = find_sound(name);
    if (sound == NULL)
        return;
    int available = -1;
    for (int ch = 0; ch < LOOP_CHANNELS; ch++) {
        if (channels[ch].sound == sound && Mix_Playing(ch)) {
            channels[ch].group = valid_group(group);
            channels[ch].gain = clamp01(gain);
            channel_volume(ch);
            return;
        }
        if (!Mix_Playing(ch) && available < 0)
            available = ch;
    }
    if (available < 0)
        return;
    channels[available] = (Channel){sound, valid_group(group), clamp01(gain), false};
    channel_volume(available);
    Mix_PlayChannel(available, sound->chunk, -1);
}

void audio_stop(const char *name)
{
    const LoadedSound *sound = find_sound(name);
    if (sound == NULL)
        return;
    for (int ch = 0; ch < AUDIO_CHANNELS; ch++) {
        if (channels[ch].sound != sound)
            continue;
        Mix_HaltChannel(ch);
        channels[ch] = (Channel){0};
    }
}

void audio_stop_loop(const char *name)
{
    const LoadedSound *sound = find_sound(name);
    if (sound == NULL)
        return;
    for (int ch = 0; ch < LOOP_CHANNELS; ch++) {
        if (channels[ch].sound != sound)
            continue;
        Mix_HaltChannel(ch);
        channels[ch] = (Channel){0};
    }
}

void audio_set_master(float volume)
{
    master = clamp01(volume);
    if (ready)
        music_volume();
    if (ready)
        for (int ch = 0; ch < AUDIO_CHANNELS; ch++)
            if (channels[ch].sound != NULL && Mix_Playing(ch))
                channel_volume(ch);
}

void audio_set_group(int group, float volume)
{
    if (group < 0 || group >= AUDIO_GROUPS)
        return;
    groups[group] = clamp01(volume);
    if (ready)
        for (int ch = 0; ch < AUDIO_CHANNELS; ch++)
            if (channels[ch].sound != NULL && channels[ch].group == group && Mix_Playing(ch))
                channel_volume(ch);
}
