#ifndef ENGINE_PLATFORM_H
#define ENGINE_PLATFORM_H

#include <stdbool.h>

#include <SDL.h>

#include "engine/input.h"

typedef enum {
    BIND_KEY,  /* code is a layout-aware SDL_Keycode, e.g. SDLK_a */
    BIND_MOUSE /* code is an SDL mouse button, e.g. SDL_BUTTON_LEFT */
} BindingKind;

typedef struct {
    BindingKind kind;
    int code;
    Action action;
} InputBinding;

typedef struct {
    SDL_Window *window;
    SDL_Renderer *renderer;
    bool vsync;
    bool quit_requested;
    const InputBinding *bindings;
    int binding_count;
    /* Presses seen as events since the last read, so a click or tap shorter
     * than one update is never lost. */
    bool latched[ACTION_COUNT];
    int pointer_x, pointer_y; /* The mouse, in window (logical) coordinates */
    bool pointer_moved, pointer_clicked; /* Since the last platform_read_pointer */
} Platform;

bool platform_init(Platform *platform, const char *title, int width, int height);
void platform_shutdown(Platform *platform);

void platform_set_bindings(Platform *platform, const InputBinding *bindings, int count);

/* Drains pending OS events; sets quit_requested when the window is closed. */
void platform_poll_events(Platform *platform);

/* Real keyboard/mouse state (not key events), so OS key auto-repeat never
 * matters, plus any presses latched since the previous call. */
void platform_read_actions(Platform *platform, bool down[ACTION_COUNT]);

/* The mouse since the previous call: where it is, whether it moved and
 * whether the left button was clicked (for clicking menus). */
void platform_read_pointer(Platform *platform, InputState *input);

double platform_time(void);

void platform_set_color(SDL_Renderer *renderer, unsigned rgb);

#endif
