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

static bool casefile_screen(Screen screen)
{
    return screen == SCREEN_CASEFILE || screen == SCREEN_EXAMINE || screen == SCREEN_REPORT;
}

bool play_casefile_sounds(Screen before, Screen after,
                           const BoardView *previous, const BoardView *view)
{
    if (!casefile_screen(before) && !casefile_screen(after))
        return false;
    if (!casefile_screen(before))
        audio_play("ui/book_open");
    else if (!casefile_screen(after))
        audio_play("ui/book_close");
    else if (after == SCREEN_REPORT && before != after)
        audio_play("ui/book_open");
    else if (before == SCREEN_REPORT && before != after) {
        audio_stop("ui/stamp");
        audio_play("ui/book_close");
    } else if (before != after)
        audio_play("ui/book_page");
    else if (before == SCREEN_CASEFILE) {
        if (view->wrong_time > previous->wrong_time)
            audio_play("ui/back");
        else if (previous->asking != view->asking)
            audio_play(view->asking ? "ui/confirm" : "ui/back");
        else if (previous->row != view->row || previous->col != view->col ||
                 (view->asking && previous->option != view->option))
            audio_play("ui/move");
    }
    return true;
}

void play_tape_sounds(const TapeView *previous, const TapeView *view, const CaseFile *file,
                       const InputState *input, int result)
{
    int x = TAPE_X + view->selected * TAPE_STEP;
    bool clicked = input->pointer_clicked && input->pointer_x >= x && input->pointer_x < x + TAPE_W &&
                   input->pointer_y >= TAPE_Y && input->pointer_y < TAPE_Y + TAPE_H + 70;
    if (result >= 0)
        audio_play("ui/confirm");
    else if (result == TAPE_BACK ||
             (!tape_unlocked(file, view->selected) && (input->pressed[ACTION_CONFIRM] || clicked)))
        audio_play("ui/back");
    else if (previous->selected != view->selected)
        audio_play("ui/move");
}
