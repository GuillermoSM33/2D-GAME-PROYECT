#include "engine/platform.h"

#include <stdio.h>
#include <string.h>

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

    platform->window = SDL_CreateWindow(title, SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                                        width, height, SDL_WINDOW_ALLOW_HIGHDPI);
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
    SDL_RenderSetLogicalSize(platform->renderer, width, height);
    return true;
}

void platform_shutdown(Platform *platform)
{
    if (platform->renderer)
        SDL_DestroyRenderer(platform->renderer);
    if (platform->window)
        SDL_DestroyWindow(platform->window);
    SDL_Quit();
    memset(platform, 0, sizeof(*platform));
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
            if (!event.key.repeat)
                latch(platform, BIND_KEY, (int)event.key.keysym.sym);
            break;
        case SDL_MOUSEBUTTONDOWN:
            latch(platform, BIND_MOUSE, event.button.button);
            break;
        }
    }
}

void platform_read_actions(Platform *platform, bool down[ACTION_COUNT])
{
    const Uint8 *keys = SDL_GetKeyboardState(NULL);
    Uint32 buttons = SDL_GetMouseState(NULL, NULL);
    memcpy(down, platform->latched, sizeof(bool) * ACTION_COUNT);
    memset(platform->latched, 0, sizeof(platform->latched));
    for (int i = 0; i < platform->binding_count; i++) {
        const InputBinding *b = &platform->bindings[i];
        bool held = false;
        if (b->kind == BIND_KEY) {
            SDL_Scancode code = SDL_GetScancodeFromKey((SDL_Keycode)b->code);
            held = code != SDL_SCANCODE_UNKNOWN && keys[code];
        } else {
            held = (buttons & SDL_BUTTON((Uint32)b->code)) != 0;
        }
        if (held)
            down[b->action] = true;
    }
}

double platform_time(void)
{
    return (double)SDL_GetPerformanceCounter() / (double)SDL_GetPerformanceFrequency();
}

void platform_set_color(SDL_Renderer *renderer, unsigned rgb)
{
    SDL_SetRenderDrawColor(renderer, (rgb >> 16) & 0xFF, (rgb >> 8) & 0xFF, rgb & 0xFF, 0xFF);
}
