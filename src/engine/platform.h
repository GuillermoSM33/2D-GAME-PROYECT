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
    SDL_Texture *canvas; /* Drawing goes here at the logical size; NULL draws straight to the window */
    int width, height;   /* The game's logical size */
    bool vsync;
    bool quit_requested;
    bool fullscreen;
    bool fullscreen_toggled; /* F11 switched it since the game last looked */
    bool focus_lost;         /* The window lost focus since the game last looked */
    const InputBinding *bindings;
    int binding_count;
    /* Presses seen as events since the last read, so a click or tap shorter
     * than one update is never lost. */
    bool latched[ACTION_COUNT];
    int pointer_x, pointer_y; /* The mouse, in window (logical) coordinates */
    bool pointer_moved, pointer_clicked; /* Since the last platform_read_pointer */
    bool mouse_blocked; /* Mouse bindings ignored until every button is up */
    /* The mouse buttons down, as their press and release events said. A
     * button counts as held only while these agree with SDL_GetMouseState:
     * with quick clicks that state has been seen stuck on "down" (sdl2-compat
     * on Wayland), which kept the dual pistols firing on their own. */
    Uint32 buttons_down;
} Platform;

bool platform_init(Platform *platform, const char *title, int width, int height);
void platform_shutdown(Platform *platform);

/* Shows the frame: the canvas scaled to fill the window (bars if the shape
 * differs), then drawing goes back into the canvas. */
void platform_present(Platform *platform);

/* Full screen at the desktop's resolution (no video mode change), or back to
 * a window. The game keeps its logical size and is scaled to fit, with bars
 * if the screen's shape differs. F11 also switches it. */
void platform_set_fullscreen(Platform *platform, bool on);

void platform_set_bindings(Platform *platform, const InputBinding *bindings, int count);

/* Drains pending OS events; sets quit_requested when the window is closed,
 * focus_lost when it loses focus, and switches full screen on F11. */
void platform_poll_events(Platform *platform);

/* Real keyboard/mouse state (not key events), so OS key auto-repeat never
 * matters, plus any presses latched since the previous call. */
void platform_read_actions(Platform *platform, bool down[ACTION_COUNT]);

/* Mouse buttons stop counting as actions until all are released, so the
 * click that picked a menu option is not also, say, a shot. */
void platform_block_mouse(Platform *platform);

/* The mouse since the previous call: where it is, whether it moved and
 * whether the left button was clicked (for clicking menus). */
void platform_read_pointer(Platform *platform, InputState *input);

double platform_time(void);

void platform_set_color(SDL_Renderer *renderer, unsigned rgb);

#endif
