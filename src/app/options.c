#include <math.h>

#include "app/options.h"
#include "engine/audio.h"
#include "engine/prefs.h"
#include "game/hud.h"

/* Volumes and display preferences belong to this application instance. */

#define PREF_FULLSCREEN "pantalla_completa"

void options_set_fullscreen(AppOptions *options, bool on)
{
    platform_set_fullscreen(options->display, on);
    options->volumes.fullscreen = options->display->fullscreen;
    if (options->remember_display)
        prefs_set_bool(PREF_FULLSCREEN, options->volumes.fullscreen);
}

static void apply_volumes(AppOptions *options)
{
    audio_set_master(volume_share(options->volumes.master));
    audio_set_music(volume_share(options->volumes.music));
    audio_set_group(SOUND_PLAYER, volume_share(options->volumes.player));
    audio_set_group(SOUND_ZOMBIE, volume_share(options->volumes.zombie));
}

/* A changed volume plays a sample of the group it controls. */
bool options_step(AppOptions *options, const InputState *input)
{
    int row = volume_menu_update(&options->volume_menu, &options->volumes, input);
    if (row == VOLUME_BACK)
        return false;
    if (row == VOLUME_FULLSCREEN) {
        options_set_fullscreen(options, options->volumes.fullscreen);
        audio_play("ui/confirm");
    } else if (row >= 0) {
        apply_volumes(options);
        if (row == VOLUME_ZOMBIE)
            audio_play_in("zombie/idle", SOUND_ZOMBIE);
        else if (row == VOLUME_PLAYER)
            audio_play_in("player/shot", SOUND_PLAYER);
        else if (row != VOLUME_MUSIC) /* The music itself is the sample */
            audio_play("ui/confirm");
    }
    return true;
}

/* The mouse over what the screen last drew: pointing at an item selects it
 * (*selected, when the screen has a list), clicking it confirms; clicking a
 * hint's key does what the key does; clicking a volume bar sets it there. */
void options_apply_pointer(AppOptions *options, InputState *input, int *selected)
{
    HudZone zone;
    if (!(input->pointer_moved || input->pointer_clicked) ||
        !hud_zone_at(input->pointer_x, input->pointer_y, &zone))
        return;
    if ((zone.kind == HUD_ZONE_ITEM || zone.kind == HUD_ZONE_VOLUME) && selected)
        *selected = zone.index;
    if (!input->pointer_clicked)
        return;
    switch (zone.kind) {
    case HUD_ZONE_ITEM:
    case HUD_ZONE_ACCEPT:
        input->pressed[ACTION_CONFIRM] = true;
        break;
    case HUD_ZONE_BACK:
        input->pressed[ACTION_QUIT] = true;
        break;
    case HUD_ZONE_RETRY:
        input->pressed[ACTION_RELOAD] = true;
        break;
    case HUD_ZONE_PHASE: /* The stage select's own: its screen acts on them */
    case HUD_ZONE_TAPE:
    case HUD_ZONE_BACKDROP:
        break;
    case HUD_ZONE_VOLUME:
        if (volume_set(&options->volumes, zone.index, (int)lroundf(zone.share * VOLUME_STEPS))) {
            apply_volumes(options);
            if (zone.index == VOLUME_ZOMBIE)
                audio_play_in("zombie/idle", SOUND_ZOMBIE);
            else if (zone.index == VOLUME_PLAYER)
                audio_play_in("player/shot", SOUND_PLAYER);
            else if (zone.index != VOLUME_MUSIC)
                audio_play("ui/confirm");
        }
        break;
    }
}


void options_init(AppOptions *options, Platform *display, bool remember_display)
{
    *options = (AppOptions){.display = display, .remember_display = remember_display};
    volumes_init(&options->volumes);
    list_menu_init(&options->volume_menu, VOLUME_ROWS);
    apply_volumes(options);
    if (remember_display && prefs_get_bool(PREF_FULLSCREEN, false))
        options_set_fullscreen(options, true);
}

void options_restore_volumes(AppOptions *options, const Volumes *volumes)
{
    options->volumes.master = volumes->master;
    options->volumes.music = volumes->music;
    options->volumes.player = volumes->player;
    options->volumes.zombie = volumes->zombie;
    apply_volumes(options);
}
