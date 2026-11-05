#include "app/navigation.h"
#include "engine/audio.h"

/* Book gestures have their own paper foley, for mouse and keyboard alike.
 * Looking across cards keeps the existing quiet menu click. */
bool play_almanac_sounds(Screen before, Screen after,
                                const AlmanacView *previous, const AlmanacView *view)
{
    if (before != SCREEN_ALMANAC && after != SCREEN_ALMANAC)
        return false;
    if (before != SCREEN_ALMANAC)
        audio_play("ui/book_open");
    else if (after != SCREEN_ALMANAC)
        audio_play("ui/book_close");
    else if (previous->detail != view->detail || previous->scroll != view->scroll)
        audio_play("ui/book_page");
    else if (previous->selected != view->selected)
        audio_play("ui/move");
    return true;
}
