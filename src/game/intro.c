#include <string.h>

#include "config.h"
#include "game/intro.h"
#include "game/settings.h"

/* One scene of the script. Its fades are to and from black; 0 is a hard cut. */
typedef struct {
    float length;
    float fade_in, fade_out;
    const char *caption; /* NULL: none */
    float caption_at;    /* Seconds in when it starts typing */
    bool dialog;         /* Someone says it (in her color), not the narrator */
} SceneDef;

static const SceneDef SCENES[INTRO_SCENES] = {
    [INTRO_REC] = {7.0f, 0.0f, 0.25f, NULL, 0.0f, false},
    [INTRO_MONITORS] = {9.0f, 0.25f, 0.25f, "Lo llamaron The Miracle.\nUna cura para todas las enfermedades.", 1.0f, false},
    [INTRO_ALARM] = {7.0f, 0.25f, 0.25f, "Lo que crearon no se podía detener.", 1.2f, false},
    [INTRO_MERCS] = {8.0f, 0.25f, 0.0f, "Alguien vino a borrar todo rastro.", 1.5f, false},
    [INTRO_SAMPLE] = {6.0f, 0.0f, 0.0f, "¡Si disparas, se rompe!", 1.4f, true},
    [INTRO_SHOT] = {5.0f, 0.0f, 0.6f, NULL, 0.0f, false},
    [INTRO_ROAD] = {8.0f, 0.8f, 0.6f, "La llevaron al hospital\nde Ojo de Cuervo.", 1.2f, false},
    [INTRO_TOWN] = {9.0f, 0.6f, 0.6f, "En tres días,\nel pueblo dejó de contestar.", 1.2f, false},
    [INTRO_GRAVE] = {8.0f, 0.6f, 0.8f, "Los muertos no se quedaron quietos.", 3.6f, false},
    [INTRO_TITLE] = {9.0f, 1.0f, 0.0f, NULL, 0.0f, false},
};

/* Seconds into INTRO_TITLE where the short version starts: the sheriff has
 * faded and the dust is about to bring the title up. */
#define SHORT_INTO_TITLE 4.0f
#define CAPTION_RATE 26.0f   /* Letters typed per second */
#define CAPTION_FADE 0.5f    /* Seconds it takes to fade out, before the scene's own fade */

/* The noises of the script: what each scene sounds like. No voices. */
static const IntroCue CUES[] = {
    {INTRO_REC, 1.2f, CUE_PLAY, "player/flashlight_on", SOUND_PLAYER, 0.5f}, /* The camera clicks on */
    {INTRO_REC, 2.2f, CUE_PLAY, "world/footstep", SOUND_PLAYER, 0.45f},       /* Her careful steps */
    {INTRO_REC, 3.3f, CUE_PLAY, "world/footstep_2", SOUND_PLAYER, 0.45f},
    {INTRO_REC, 4.4f, CUE_PLAY, "world/footstep_3", SOUND_PLAYER, 0.45f},
    {INTRO_REC, 5.5f, CUE_PLAY, "world/footstep_4", SOUND_PLAYER, 0.45f},
    {INTRO_ALARM, 0.3f, CUE_PLAY, "world/ambush", SOUND_PLAYER, 0.8f},        /* The monitor goes red */
    {INTRO_ALARM, 4.0f, CUE_PLAY, "weather/lightning_warn", SOUND_PLAYER, 0.5f},
    {INTRO_MERCS, 0.8f, CUE_PLAY, "player/flashlight_on", SOUND_PLAYER, 0.9f}, /* Their lights */
    {INTRO_MERCS, 1.3f, CUE_PLAY, "player/flashlight_on", SOUND_PLAYER, 0.7f},
    {INTRO_MERCS, 2.4f, CUE_PLAY, "world/run_step", SOUND_PLAYER, 0.6f},       /* Boots coming */
    {INTRO_MERCS, 3.0f, CUE_PLAY, "world/run_step_2", SOUND_PLAYER, 0.65f},
    {INTRO_MERCS, 3.6f, CUE_PLAY, "world/run_step_3", SOUND_PLAYER, 0.7f},
    {INTRO_MERCS, 4.2f, CUE_PLAY, "world/run_step_4", SOUND_PLAYER, 0.75f},
    {INTRO_MERCS, 4.8f, CUE_PLAY, "world/run_step", SOUND_PLAYER, 0.8f},
    {INTRO_MERCS, 5.4f, CUE_PLAY, "world/run_step_2", SOUND_PLAYER, 0.85f},
    {INTRO_MERCS, 6.2f, CUE_PLAY, "weapons/rifle_empty", SOUND_PLAYER, 0.7f},  /* A rifle readied */
    {INTRO_SHOT, 0.35f, CUE_PLAY, "weapons/rifle_shot", SOUND_PLAYER, 1.0f},
    {INTRO_SHOT, 0.40f, CUE_PLAY, "world/glass", SOUND_PLAYER, 1.0f},          /* The sample breaks */
    {INTRO_SHOT, 1.30f, CUE_PLAY, "world/hit_metal", SOUND_PLAYER, 0.8f},      /* The camera hits the floor */
    {INTRO_ROAD, 0.0f, CUE_LOOP, "weather/wind", SOUND_PLAYER, 0.45f},
    {INTRO_TOWN, 1.8f, CUE_PLAY, "crow/caw", SOUND_PLAYER, 0.7f},
    {INTRO_TOWN, 4.6f, CUE_PLAY, "zombie/idle", SOUND_ZOMBIE, 0.6f},
    {INTRO_TOWN, 6.2f, CUE_PLAY, "crow/caw", SOUND_PLAYER, 0.9f},             /* The crows take off */
    {INTRO_GRAVE, 0.4f, CUE_PLAY, "weather/thunder", SOUND_PLAYER, 0.55f},
    {INTRO_GRAVE, 1.6f, CUE_PLAY, "world/hit_sand", SOUND_PLAYER, 0.9f},       /* The first grave gives */
    {INTRO_GRAVE, 2.4f, CUE_PLAY, "zombie/spawn", SOUND_ZOMBIE, 1.0f},
    {INTRO_GRAVE, 3.0f, CUE_PLAY, "world/wood", SOUND_PLAYER, 1.0f},           /* A coffin bursts open */
    {INTRO_GRAVE, 3.3f, CUE_PLAY, "world/hit_sand", SOUND_PLAYER, 0.8f},       /* The second grave */
    {INTRO_GRAVE, 4.0f, CUE_PLAY, "zombie/spawn", SOUND_ZOMBIE, 0.9f},
    {INTRO_GRAVE, 5.6f, CUE_PLAY, "zombie/idle", SOUND_ZOMBIE, 0.8f},
    {INTRO_TITLE, 4.0f, CUE_MUSIC, MENU_MUSIC, 0, 1.0f},                      /* The title's theme */
    {INTRO_TITLE, 8.6f, CUE_STOP_LOOP, "weather/wind", SOUND_PLAYER, 0.0f},
};
#define CUE_COUNT ((int)(sizeof(CUES) / sizeof(CUES[0])))

float intro_scene_length(IntroScene scene)
{
    return scene >= 0 && scene < INTRO_SCENES ? SCENES[scene].length : 0.0f;
}

static float scene_start(IntroScene scene)
{
    float t = 0.0f;
    for (int s = 0; s < (int)scene; s++)
        t += SCENES[s].length;
    return t;
}

float intro_total_length(void)
{
    return scene_start(INTRO_SCENES);
}

float intro_short_start(void)
{
    return scene_start(INTRO_TITLE) + SHORT_INTO_TITLE;
}

static float cue_time(const IntroCue *cue)
{
    return scene_start(cue->scene) + cue->at;
}

void intro_start(Intro *intro, IntroMode mode)
{
    memset(intro, 0, sizeof(*intro));
    intro->mode = mode;
    intro->end = intro_total_length();
    intro->time = mode == INTRO_SHORT ? intro_short_start() : 0.0f;
    /* The short version still needs what the title scene sets going (its
     * music), but none of the noises before it. */
    while (intro->next_cue < CUE_COUNT && cue_time(&CUES[intro->next_cue]) < intro->time &&
           !(mode == INTRO_SHORT && CUES[intro->next_cue].kind == CUE_MUSIC))
        intro->next_cue++;
}

int intro_update(Intro *intro, float dt, bool skip, const IntroCue **fired, int max)
{
    if (intro->done)
        return 0;
    if (skip) {
        intro->time = intro->end;
        intro->next_cue = CUE_COUNT;
        intro->done = intro->skipped = true;
        return 0;
    }
    intro->time += dt;
    int count = 0;
    while (intro->next_cue < CUE_COUNT && cue_time(&CUES[intro->next_cue]) <= intro->time) {
        if (count < max)
            fired[count++] = &CUES[intro->next_cue];
        intro->next_cue++;
    }
    if (intro->time >= intro->end) {
        intro->time = intro->end;
        intro->done = true;
    }
    return count;
}

IntroScene intro_scene(const Intro *intro, float *local)
{
    float t = intro->time;
    for (int s = 0; s < INTRO_SCENES; s++) {
        if (t < SCENES[s].length || s == INTRO_SCENES - 1) {
            if (local)
                *local = t;
            return (IntroScene)s;
        }
        t -= SCENES[s].length;
    }
    if (local)
        *local = 0.0f;
    return INTRO_TITLE;
}

static float clamp01(float v)
{
    return v < 0.0f ? 0.0f : v > 1.0f ? 1.0f : v;
}

float intro_black(const Intro *intro)
{
    float local;
    IntroScene s = intro_scene(intro, &local);
    const SceneDef *def = &SCENES[s];
    /* The short version opens on the title's backdrop, already lit. */
    if (intro->mode == INTRO_SHORT)
        return 0.0f;
    float black = 0.0f;
    if (def->fade_in > 0.0f && local < def->fade_in)
        black = 1.0f - local / def->fade_in;
    if (def->fade_out > 0.0f && local > def->length - def->fade_out)
        black = clamp01((local - (def->length - def->fade_out)) / def->fade_out);
    return clamp01(black);
}

/* Bytes of the first n whole UTF-8 letters of s. */
static int utf8_prefix(const char *s, int letters)
{
    int bytes = 0;
    while (s[bytes] && letters > 0) {
        bytes++;
        while ((s[bytes] & 0xC0) == 0x80)
            bytes++;
        letters--;
    }
    return bytes;
}

bool intro_caption(const Intro *intro, char *buf, int size, float *alpha, bool *dialog)
{
    float local;
    IntroScene s = intro_scene(intro, &local);
    const SceneDef *def = &SCENES[s];
    if (def->caption == NULL || local < def->caption_at || size <= 0)
        return false;
    int letters = (int)((local - def->caption_at) * CAPTION_RATE) + 1;
    int bytes = utf8_prefix(def->caption, letters);
    if (bytes >= size)
        bytes = size - 1;
    memcpy(buf, def->caption, (size_t)bytes);
    buf[bytes] = '\0';
    float out_at = def->length - def->fade_out - CAPTION_FADE;
    float a = local > out_at ? 1.0f - (local - out_at) / CAPTION_FADE : 1.0f;
    if (alpha)
        *alpha = clamp01(a);
    if (dialog)
        *dialog = def->dialog;
    return a > 0.0f;
}

const char *intro_caption_text(IntroScene scene)
{
    return scene >= 0 && scene < INTRO_SCENES ? SCENES[scene].caption : NULL;
}

const IntroCue *intro_cues(int *count)
{
    if (count)
        *count = CUE_COUNT;
    return CUES;
}
