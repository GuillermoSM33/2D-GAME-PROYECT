/* SDL dummy-device integration check; intentionally outside test_*.c, which
 * the Makefile builds without SDL. See docs/AUDIO.md for the build command. */
#define SDL_MAIN_HANDLED
#include <math.h>
#include <string.h>

#include <SDL.h>
#include <SDL_mixer.h>

#include "config.h"
#include "engine/assets.h"
#include "engine/audio.h"
#include "test.h"

/* Forty independent sounds detect the old 32-sound loading limit without
 * having to embed all of the game's images in this small audio check. */
static unsigned char wave[44 + 8000];
#define BLOB(n) {"sounds/test/" n, sizeof(wave), wave}
const EmbeddedBlob embedded_blobs[] = {
    BLOB("00"), BLOB("01"), BLOB("02"), BLOB("03"), BLOB("04"),
    BLOB("05"), BLOB("06"), BLOB("07"), BLOB("08"), BLOB("09"),
    BLOB("10"), BLOB("11"), BLOB("12"), BLOB("13"), BLOB("14"),
    BLOB("15"), BLOB("16"), BLOB("17"), BLOB("18"), BLOB("19"),
    BLOB("20"), BLOB("21"), BLOB("22"), BLOB("23"), BLOB("24"),
    BLOB("25"), BLOB("26"), BLOB("27"), BLOB("28"), BLOB("29"),
    BLOB("30"), BLOB("31"), BLOB("32"), BLOB("33"), BLOB("34"),
    BLOB("35"), BLOB("36"), BLOB("37"), BLOB("38"), BLOB("39"),
    {"music/test", sizeof(wave), wave}, /* Not an effect: never loaded as one */
};
const int embedded_blob_count = (int)(sizeof(embedded_blobs) / sizeof(embedded_blobs[0]));

static void loading_and_channels(void)
{
    audio_play_in_gain("test/39", 1, 0.8f);
    CHECK(Mix_Playing(4) == 1);
    CHECK(Mix_Volume(4, -1) == 102);
    audio_loop_in("test/00", 1, 0.5f);
    audio_loop_in("test/01", 2, 0.25f);
    audio_loop_in("test/02", 0, 0.5f);
    audio_loop_in("test/03", 0, 0.5f);
    CHECK(Mix_Playing(-1) == 5); /* Four beds under one effect */
    audio_loop_in("test/00", 1, 0.5f);
    CHECK(Mix_Playing(-1) == 5);
    audio_loop_in("test/04", 0, 1.0f); /* No fifth ambience channel. */
    CHECK(Mix_Playing(-1) == 5);
    for (int i = 0; i < AUDIO_CHANNELS; i++)
        audio_play("test/39");
    CHECK(Mix_Playing(-1) == AUDIO_CHANNELS);
    for (int ch = 0; ch < 4; ch++)
        CHECK(Mix_GetChunk(ch) != Mix_GetChunk(4));
    audio_stop("test/39");
    CHECK(Mix_Playing(-1) == 4);
}

static void live_volumes(void)
{
    audio_set_master(0.5f);
    CHECK(Mix_Volume(0, -1) == 32);
    CHECK(Mix_Volume(1, -1) == 16);
    audio_set_group(1, 0.25f);
    CHECK(Mix_Volume(0, -1) == 8);
    CHECK(Mix_Volume(1, -1) == 16);
    audio_loop_in("test/00", 2, 0.75f);
    CHECK(Mix_Volume(0, -1) == 48);
    audio_set_master(0.0f);
    CHECK(Mix_Volume(0, -1) == 0);
    CHECK(Mix_Volume(1, -1) == 0);
    audio_set_master(1.0f);
    audio_set_group(1, 1.0f);
    CHECK(Mix_Volume(0, -1) == 96);
    CHECK(Mix_Volume(1, -1) == 32);
    audio_play_in_gain("test/39", 1, 0.25f);
    CHECK(Mix_Volume(4, -1) == 32);
    audio_set_group(1, 0.5f);
    CHECK(Mix_Volume(4, -1) == 16);
    audio_set_master(NAN);
    CHECK(Mix_Volume(4, -1) == 0);
    audio_set_master(1.0f);
    audio_set_group(1, 1.0f);
}

static void pause_and_stop(void)
{
    audio_pause(true);
    for (int ch = 0; ch <= 4; ch++)
        CHECK(Mix_Paused(ch) == 1);
    audio_play("test/38"); /* Pause menu clicks still work. */
    CHECK(Mix_Playing(5) == 1);
    CHECK(Mix_Paused(5) == 0);
    audio_pause(true);
    CHECK(Mix_Paused(5) == 0);
    audio_pause(false);
    CHECK(Mix_Paused(-1) == 0);
    audio_stop_loop("test/00");
    CHECK(Mix_Playing(0) == 0);
    CHECK(Mix_Playing(1) == 1);
    audio_stop("test/39");
    CHECK(Mix_Playing(4) == 0);
    CHECK(Mix_Playing(5) == 1);
    CHECK(Mix_Playing(2) == 1 && Mix_Playing(3) == 1);
    audio_stop_all();
    CHECK(Mix_Playing(-1) == 0);
    audio_play("test/missing");
    audio_play(NULL);
    CHECK(Mix_Playing(-1) == 0);
}

/* The stage tracks as shipped: this is what proves the OGG decoder is there. */
static void shipped_tracks_decode(void)
{
    static const char *const paths[] = {"assets/music/ruta_1_1.ogg", "assets/music/ruta_1_2.ogg",
                                        "assets/music/ruta_1_3.ogg", "assets/music/ruta_1_4.ogg",
                                        "assets/music/ruta_1_5.ogg", "assets/music/menu.ogg"};
    for (int i = 0; i < 6; i++) {
        SDL_RWops *rw = SDL_RWFromFile(paths[i], "rb");
        CHECK(rw != NULL);
        Mix_Music *track = rw ? Mix_LoadMUS_RW(rw, 1) : NULL;
        CHECK(track != NULL);
        if (track) {
            CHECK(Mix_GetMusicType(track) == MUS_OGG);
            CHECK(Mix_PlayMusic(track, -1) == 0);
            CHECK(Mix_PlayingMusic() == 1);
            Mix_HaltMusic();
            Mix_FreeMusic(track);
        }
    }
}

static void music(void)
{
    audio_set_master(1.0f);
    audio_set_music(1.0f);
    audio_music_play("music/test");
    CHECK(Mix_PlayingMusic() == 1);
    CHECK(Mix_VolumeMusic(-1) == MUSIC_VOLUME);
    CHECK(Mix_Playing(-1) == 0); /* It takes none of the effects' channels */
    audio_set_music(0.5f);
    CHECK(Mix_VolumeMusic(-1) == (int)(MUSIC_VOLUME * 0.5f + 0.5f));
    audio_set_master(0.0f);
    CHECK(Mix_VolumeMusic(-1) == 0);
    audio_set_master(1.0f);
    audio_set_music(1.0f);
    audio_music_play("music/test"); /* The same one: left alone */
    CHECK(Mix_PlayingMusic() == 1 && Mix_FadingMusic() == MIX_NO_FADING);
    audio_stop_all(); /* Clearing a stage's sounds leaves the music */
    audio_pause(true);
    CHECK(Mix_PlayingMusic() == 1 && Mix_PausedMusic() == 0);
    audio_pause(false);
    audio_music_stop(200);
    CHECK(Mix_FadingMusic() == MIX_FADING_OUT);
    audio_music_play("music/test"); /* A retry during the fade starts over, in full */
    CHECK(Mix_PlayingMusic() == 1 && Mix_FadingMusic() == MIX_NO_FADING);
    audio_music_stop(0);
    CHECK(Mix_PlayingMusic() == 0);
    audio_music_play("music/missing");
    audio_music_play(NULL);
    audio_music_stop(0);
    CHECK(Mix_PlayingMusic() == 0);
}

static void lifecycle(void)
{
    audio_shutdown();
    audio_shutdown();
    audio_play("test/39");
    audio_loop_in("test/00", 0, 1.0f);
    audio_stop(NULL);
    audio_stop_all();
    audio_pause(true);
    CHECK(audio_init());
    audio_play("test/39");
    CHECK(Mix_Playing(4) == 1);
    CHECK(audio_init()); /* Repeated init leaves the current sound intact. */
    CHECK(Mix_Playing(4) == 1);
    audio_shutdown();
    SDL_setenv("SDL_AUDIODRIVER", "missing_audio_driver_for_test", 1);
    CHECK(!audio_init());
    audio_play("test/39");
    audio_loop_in("test/00", 0, 1.0f);
    audio_set_master(0.5f);
    audio_stop("test/39");
    audio_stop_loop("test/00");
    audio_pause(false);
    audio_shutdown();
    SDL_setenv("SDL_AUDIODRIVER", "dummy", 1);
    CHECK(audio_init());
    audio_play("test/39");
    CHECK(Mix_Playing(4) == 1);
    CHECK(Mix_Volume(4, -1) == 64);
    audio_shutdown();
}

int main(void)
{
    SDL_SetMainReady();
    SDL_setenv("SDL_AUDIODRIVER", "dummy", 1);
    /* One second, 8000 Hz, unsigned 8-bit mono PCM. */
    static const unsigned char header[44] = {
        'R','I','F','F',0x64,0x1f,0,0,'W','A','V','E',
        'f','m','t',' ',16,0,0,0,1,0,1,0,0x40,0x1f,0,0,
        0x40,0x1f,0,0,1,0,8,0,'d','a','t','a',0x40,0x1f,0,0,
    };
    memcpy(wave, header, sizeof(header));
    memset(wave + sizeof(header), 128, sizeof(wave) - sizeof(header));
    CHECK(audio_init());
    if (test_failures)
        return TEST_EXIT();
    RUN(loading_and_channels);
    RUN(live_volumes);
    RUN(pause_and_stop);
    RUN(music);
    RUN(shipped_tracks_decode);
    RUN(lifecycle);
    return TEST_EXIT();
}
