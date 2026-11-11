#include "engine/platform.h"

#include <stdio.h>
#include <string.h>

/* Share of the screen's usable area the first window takes. */
#define WINDOW_SCREEN_SHARE 0.85f

bool platform_init(Platform *platform, const char *title, int width, int height)
{
    memset(platform, 0, sizeof(*platform));
    if (SDL_Init(SDL_INIT_VIDEO) != 0) {
        fprintf(stderr, "No se pudo iniciar SDL: %s\n", SDL_GetError());
        fprintf(stderr, "Abre una sesión de escritorio Linux (no una terminal SSH sin DISPLAY).\n");
        return false;
    }
    /* Pixel art: never smooth when scaling. */
    SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "nearest");

    /* The window opens as large as the screen comfortably fits (keeping the
     * game's shape), and can be resized; the picture scales with it. */
    int window_w = width, window_h = height;
    SDL_Rect usable;
    if (SDL_GetDisplayUsableBounds(0, &usable) == 0) {
        float scale = SDL_min(usable.w * WINDOW_SCREEN_SHARE / width,
                              usable.h * WINDOW_SCREEN_SHARE / height);
        if (scale > 1.0f) {
            window_w = (int)(width * scale);
            window_h = (int)(height * scale);
        }
    }
    platform->window = SDL_CreateWindow(title, SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                                        window_w, window_h,
                                        SDL_WINDOW_ALLOW_HIGHDPI | SDL_WINDOW_RESIZABLE);
    if (platform->window)
        SDL_SetWindowMinimumSize(platform->window, width / 2, height / 2);
    if (platform->window == NULL) {
        fprintf(stderr, "No se pudo crear la ventana: %s\n", SDL_GetError());
        SDL_Quit();
        return false;
    }

    platform->renderer = SDL_CreateRenderer(platform->window, -1,
                                            SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC);
    platform->vsync = platform->renderer != NULL;
    if (platform->renderer == NULL)
        platform->renderer = SDL_CreateRenderer(platform->window, -1, SDL_RENDERER_SOFTWARE);
    if (platform->renderer == NULL) {
        fprintf(stderr, "No se pudo crear el renderer: %s\n", SDL_GetError());
        SDL_DestroyWindow(platform->window);
        SDL_Quit();
        return false;
    }
    platform->width = width;
    platform->height = height;
    /* Everything is drawn into a canvas of the logical size, so the game's own
     * scale and viewport changes never undo the window's scaling. */
    if (SDL_RenderTargetSupported(platform->renderer))
        platform->canvas = SDL_CreateTexture(platform->renderer, SDL_PIXELFORMAT_RGBA8888,
                                             SDL_TEXTUREACCESS_TARGET, width, height);
    if (platform->canvas)
        SDL_SetRenderTarget(platform->renderer, platform->canvas);
    else
        SDL_RenderSetLogicalSize(platform->renderer, width, height);
    return true;
}

/* Where the game's picture goes in an area of w x h: as large as fits, keeping
 * its shape, centered (bars on the sides that are left over). */
static SDL_Rect fit_rect(const Platform *platform, int w, int h)
{
    float scale = SDL_min((float)w / platform->width, (float)h / platform->height);
    SDL_Rect rect;
    rect.w = (int)(platform->width * scale);
    rect.h = (int)(platform->height * scale);
    rect.x = (w - rect.w) / 2;
    rect.y = (h - rect.h) / 2;
    return rect;
}

void platform_present(Platform *platform)
{
    if (platform->canvas) {
        int out_w, out_h;
        SDL_SetRenderTarget(platform->renderer, NULL);
        SDL_RenderSetScale(platform->renderer, 1.0f, 1.0f);
        SDL_RenderSetViewport(platform->renderer, NULL);
        SDL_SetRenderDrawColor(platform->renderer, 0, 0, 0, 255);
        SDL_RenderClear(platform->renderer);
        if (SDL_GetRendererOutputSize(platform->renderer, &out_w, &out_h) == 0) {
            SDL_Rect dest = fit_rect(platform, out_w, out_h);
            SDL_RenderCopy(platform->renderer, platform->canvas, NULL, &dest);
        }
    }
    SDL_RenderPresent(platform->renderer);
    if (platform->canvas)
        SDL_SetRenderTarget(platform->renderer, platform->canvas);
}

/* A mouse position in window points, in the game's logical coordinates. With
 * no canvas, SDL's logical size already converted it. */
static void set_pointer(Platform *platform, int x, int y)
{
    int win_w, win_h;
    if (platform->canvas) {
        SDL_GetWindowSize(platform->window, &win_w, &win_h);
        SDL_Rect area = fit_rect(platform, win_w, win_h);
        if (area.w > 0 && area.h > 0) {
            x = (x - area.x) * platform->width / area.w;
            y = (y - area.y) * platform->height / area.h;
        }
    }
    platform->pointer_x = x;
    platform->pointer_y = y;
}

void platform_shutdown(Platform *platform)
{
    if (platform->canvas)
        SDL_DestroyTexture(platform->canvas);
    if (platform->renderer)
        SDL_DestroyRenderer(platform->renderer);
    if (platform->window)
        SDL_DestroyWindow(platform->window);
    SDL_Quit();
    memset(platform, 0, sizeof(*platform));
}

void platform_set_fullscreen(Platform *platform, bool on)
{
    if (SDL_SetWindowFullscreen(platform->window, on ? SDL_WINDOW_FULLSCREEN_DESKTOP : 0) != 0) {
        fprintf(stderr, "No se pudo cambiar a %s: %s\n",
                on ? "pantalla completa" : "ventana", SDL_GetError());
        return;
    }
    platform->fullscreen = on;
}

void platform_set_bindings(Platform *platform, const InputBinding *bindings, int count)
{
    platform->bindings = bindings;
    platform->binding_count = count;
    memset(platform->latched, 0, sizeof(platform->latched));
}

static void latch(Platform *platform, BindingKind kind, int code)
{
    for (int i = 0; i < platform->binding_count; i++) {
        const InputBinding *b = &platform->bindings[i];
        if (b->kind == BIND_MOUSE && platform->mouse_blocked)
            continue;
        if (b->kind == kind && b->code == code)
            platform->latched[b->action] = true;
    }
}

void platform_poll_events(Platform *platform)
{
    SDL_Event event;
    while (SDL_PollEvent(&event)) {
        switch (event.type) {
        case SDL_QUIT:
            platform->quit_requested = true;
            break;
        case SDL_KEYDOWN:
            if (event.key.repeat)
                break;
            if (event.key.keysym.sym == SDLK_F11) {
                platform_set_fullscreen(platform, !platform->fullscreen);
                platform->fullscreen_toggled = true;
                break;
            }
            latch(platform, BIND_KEY, (int)event.key.keysym.sym);
            break;
        case SDL_WINDOWEVENT:
            if (event.window.event == SDL_WINDOWEVENT_FOCUS_LOST) {
                platform->focus_lost = true;
                platform->buttons_down = 0; /* Its release may go to another window */
            }
            break;
        case SDL_MOUSEBUTTONUP:
            platform->buttons_down &= ~SDL_BUTTON((Uint32)event.button.button);
            break;
        case SDL_MOUSEBUTTONDOWN:
            platform->buttons_down |= SDL_BUTTON((Uint32)event.button.button);
            latch(platform, BIND_MOUSE, event.button.button);
            if (event.button.button == SDL_BUTTON_LEFT) {
                set_pointer(platform, event.button.x, event.button.y);
                platform->pointer_clicked = true;
            }
            break;
        case SDL_MOUSEMOTION:
            set_pointer(platform, event.motion.x, event.motion.y);
            platform->pointer_moved = true;
            break;
        }
    }
}

void platform_read_actions(Platform *platform, bool down[ACTION_COUNT])
{
    const Uint8 *keys = SDL_GetKeyboardState(NULL);
    /* Held only if the events and SDL's own state both say so (platform.h). */
    Uint32 buttons = SDL_GetMouseState(NULL, NULL) & platform->buttons_down;
    memcpy(down, platform->latched, sizeof(bool) * ACTION_COUNT);
    memset(platform->latched, 0, sizeof(platform->latched));
    if (platform->mouse_blocked && buttons == 0)
        platform->mouse_blocked = false;
    for (int i = 0; i < platform->binding_count; i++) {
        const InputBinding *b = &platform->bindings[i];
        bool held = false;
        if (b->kind == BIND_KEY) {
            SDL_Scancode code = SDL_GetScancodeFromKey((SDL_Keycode)b->code);
            held = code != SDL_SCANCODE_UNKNOWN && keys[code];
        } else if (!platform->mouse_blocked) {
            held = (buttons & SDL_BUTTON((Uint32)b->code)) != 0;
        }
        if (held)
            down[b->action] = true;
    }
}

void platform_block_mouse(Platform *platform)
{
    platform->mouse_blocked = true;
}

void platform_read_pointer(Platform *platform, InputState *input)
{
    input->pointer_x = platform->pointer_x;
    input->pointer_y = platform->pointer_y;
    input->pointer_moved = platform->pointer_moved;
    input->pointer_clicked = platform->pointer_clicked;
    platform->pointer_moved = platform->pointer_clicked = false;
}

double platform_time(void)
{
    return (double)SDL_GetPerformanceCounter() / (double)SDL_GetPerformanceFrequency();
}

void platform_set_color(SDL_Renderer *renderer, unsigned rgb)
{
    SDL_SetRenderDrawColor(renderer, (rgb >> 16) & 0xFF, (rgb >> 8) & 0xFF, rgb & 0xFF, 0xFF);
}
