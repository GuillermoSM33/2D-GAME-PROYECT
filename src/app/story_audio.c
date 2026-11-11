#include "app/story_audio.h"

#include <math.h>
#include <string.h>

#include "engine/audio.h"
#include "game/settings.h"

typedef struct {
    int scene, line;
    float at;
    const char *sound;
    int group;
    float gain;
} StorySound;

/* Times match the actions in story_render.c. Captions have no typing noises
 * and the written dialogue has no voice. Existing recorded effects retain
 * their pitch and speed; distance is conveyed only by a quiet mix. */
static const StorySound SOUNDS[] = {
    /* El panteón: coffins set down, then the earth starts moving. */
    {1, 0, 0.6f, "world/hit_wood", SOUND_PLAYER, 0.32f},
    {1, 0, 1.1f, "world/hit_wood", SOUND_PLAYER, 0.30f},
    {1, 0, 1.6f, "world/hit_wood", SOUND_PLAYER, 0.28f},
    {1, 0, 2.1f, "world/hit_wood", SOUND_PLAYER, 0.26f},
    {1, 0, 2.6f, "world/hit_wood", SOUND_PLAYER, 0.24f},
    {1, 1, 1.2f, "crow/caw", SOUND_PLAYER, 0.38f},
    {1, 2, 0.6f, "weather/thunder", SOUND_MASTER, 0.38f},
    {1, 2, 1.0f, "world/hit_sand", SOUND_PLAYER, 0.65f},
    {1, 2, 1.35f, "world/hit_sand", SOUND_PLAYER, 0.32f},
    {1, 2, 1.6f, "zombie/spawn", SOUND_ZOMBIE, 0.60f},

    /* Toque de queda: slow steps, the sheriff's silent watch, lamps dying. */
    {2, 0, 0.8f, "world/footstep", SOUND_PLAYER, 0.30f},
    {2, 0, 1.1f, "zombie/idle", SOUND_ZOMBIE, 0.35f},
    {2, 0, 1.5f, "world/footstep_2", SOUND_PLAYER, 0.27f},
    {2, 0, 2.2f, "world/footstep_3", SOUND_PLAYER, 0.30f},
    {2, 0, 2.9f, "world/footstep_4", SOUND_PLAYER, 0.25f},
    {2, 0, 3.6f, "world/footstep", SOUND_PLAYER, 0.28f},
    {2, 0, 4.3f, "world/footstep_2", SOUND_PLAYER, 0.25f},
    {2, 2, 1.0f, "player/flashlight_off", SOUND_PLAYER, 0.32f},
    {2, 2, 1.9f, "player/flashlight_off", SOUND_PLAYER, 0.27f},
    {2, 2, 2.8f, "player/flashlight_off", SOUND_PLAYER, 0.22f},
    {2, 2, 3.3f, "world/footstep_3", SOUND_PLAYER, 0.25f},
    {2, 2, 3.4f, "zombie/idle", SOUND_ZOMBIE, 0.40f},

    /* El pueblo vacío: the visible crows take off; remaining neighbours sway. */
    {3, 0, 1.6f, "crow/caw", SOUND_PLAYER, 0.55f},
    {3, 0, 2.0f, "crow/caw", SOUND_PLAYER, 0.32f},
    {3, 1, 1.2f, "zombie/idle", SOUND_ZOMBIE, 0.35f},
    {3, 1, 4.3f, "zombie/idle", SOUND_ZOMBIE, 0.25f},
};

static const char *const LOOPS[] = {
    "weather/wind", "cinematic/lab_hum", "cinematic/lab_alarm",
};

static bool valid_story(const Story *story)
{
    return story && !story->done && story->beat.count > 0 &&
           story->beat.scene >= 1 && story->beat.scene <= 4 &&
           story->line >= 0 && story->line < story->beat.count &&
           isfinite(story->time) && story->time >= 0.0f;
}

void story_audio_stop(void)
{
    for (unsigned i = 0; i < sizeof(LOOPS) / sizeof(LOOPS[0]); i++)
        audio_stop_loop(LOOPS[i]);
    /* Stop each kind once, including the tails of a skipped shot. This does
     * not clear music or the rest of the game's sound catalogue. */
    for (unsigned i = 0; i < sizeof(SOUNDS) / sizeof(SOUNDS[0]); i++) {
        bool seen = false;
        for (unsigned j = 0; j < i; j++)
            if (strcmp(SOUNDS[j].sound, SOUNDS[i].sound) == 0) {
                seen = true;
                break;
            }
        if (!seen)
            audio_stop(SOUNDS[i].sound);
    }
}

static void begin_ambience(const Story *story)
{
    if (story->beat.scene == 4 && story->line > 0) {
        audio_loop_in("cinematic/lab_hum", SOUND_MASTER, 0.42f);
        if (story->line == 1)
            audio_loop_in("cinematic/lab_alarm", SOUND_MASTER, 0.26f);
    } else {
        audio_loop_in("weather/wind", SOUND_MASTER,
                      story->beat.scene == 3 ? 0.36f : 0.26f);
    }
}

void story_audio_start(const Story *story)
{
    story_audio_stop();
    if (valid_story(story))
        begin_ambience(story);
}

void story_audio_update(const Story *before, const Story *after, float dt)
{
    if (!valid_story(after)) {
        story_audio_stop();
        return;
    }
    if (!valid_story(before) || before->beat.scene != after->beat.scene ||
        before->line != after->line || after->time < before->time) {
        story_audio_start(after);
        return;
    }
    if (!isfinite(dt) || dt <= 0.0f || after->time <= before->time)
        return;
    /* Enter can complete the caption or jump to the next shot. Only the
     * interval that really elapsed may trigger its actions, never the
     * remaining effects of a shot the player has already skipped. */
    float end = fminf(after->time, before->time + dt + 0.00001f);
    for (unsigned i = 0; i < sizeof(SOUNDS) / sizeof(SOUNDS[0]); i++) {
        const StorySound *s = &SOUNDS[i];
        if (s->scene == after->beat.scene && s->line == after->line &&
            s->at > before->time && s->at <= end)
            audio_play_in_gain(s->sound, s->group, s->gain);
    }
}
