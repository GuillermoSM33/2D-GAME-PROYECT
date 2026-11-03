/* More than 128 embedded images must load on a windowless SDL renderer.
 * Own fixtures replace assets_data.o, so this checks the loader independently
 * of the size or availability of the game's sprite catalogue. */
#define SDL_MAIN_HANDLED
#include <stdlib.h>
#include <string.h>

#include <SDL.h>

#include "engine/assets.h"
#include "test.h"

static const unsigned char opaque_pixel[] = {36, 81, 129, 255};
static const unsigned char last_pixel[] = {201, 101, 51, 128};
static const unsigned char blob_data[] = {17, 42};

#define IMAGE(n) {"sprites/test/" n, 1, 1, opaque_pixel}
#define TEN(n) IMAGE(n "0"), IMAGE(n "1"), IMAGE(n "2"), IMAGE(n "3"), IMAGE(n "4"), \
               IMAGE(n "5"), IMAGE(n "6"), IMAGE(n "7"), IMAGE(n "8"), IMAGE(n "9")
const EmbeddedImage embedded_images[] = {
    TEN("00"), TEN("01"), TEN("02"), TEN("03"), TEN("04"),
    TEN("05"), TEN("06"), TEN("07"), TEN("08"), TEN("09"),
    TEN("10"), TEN("11"), TEN("12"), TEN("13"), TEN("14"),
    IMAGE("150"), IMAGE("151"), IMAGE("152"), IMAGE("153"), IMAGE("154"),
    IMAGE("155"), IMAGE("156"), IMAGE("157"), IMAGE("158"),
    {"sprites/test/159", 1, 1, last_pixel},
};
#undef TEN
#undef IMAGE
const int embedded_image_count = (int)(sizeof(embedded_images) / sizeof(embedded_images[0]));
const EmbeddedBlob embedded_blobs[] = {{"test/blob", sizeof(blob_data), blob_data}};
const int embedded_blob_count = (int)(sizeof(embedded_blobs) / sizeof(embedded_blobs[0]));

static SDL_Surface *canvas;
static SDL_Renderer *renderer;

static void embedded_lookup_and_unloaded_lifecycle(void)
{
    CHECK(embedded_image_count == 160);
    CHECK(assets_find_image("sprites/test/159") == &embedded_images[159]);
    CHECK(assets_find_image("sprites/test/missing") == NULL);
    CHECK(assets_find_image(NULL) == NULL);
    CHECK(assets_find_blob("test/blob") == &embedded_blobs[0]);
    CHECK(assets_find_blob("missing") == NULL);
    CHECK(assets_find_blob(NULL) == NULL);
    assets_unload();
    assets_unload();
    CHECK(assets_texture("sprites/test/159") == NULL);
    CHECK(assets_texture(NULL) == NULL);
    CHECK(!assets_load(NULL));
    CHECK(assets_texture("sprites/test/000") == NULL);
}

static void catalogue_beyond_old_capacity_and_native_pixels(void)
{
    CHECK(assets_load(renderer));
    for (int i = 0; i < embedded_image_count; i++) {
        SDL_Texture *texture = assets_texture(embedded_images[i].name);
        CHECK(texture != NULL);
        if (!texture)
            continue;
        int width = 0, height = 0;
        CHECK(SDL_QueryTexture(texture, NULL, NULL, &width, &height) == 0);
        CHECK(width == 1 && height == 1);
        SDL_ScaleMode scale = SDL_ScaleModeLinear;
        SDL_BlendMode blend = SDL_BLENDMODE_NONE;
        CHECK(SDL_GetTextureScaleMode(texture, &scale) == 0);
        CHECK(scale == SDL_ScaleModeNearest);
        CHECK(SDL_GetTextureBlendMode(texture, &blend) == 0);
        CHECK(blend == SDL_BLENDMODE_BLEND);
    }
    CHECK(assets_texture("missing") == NULL);

    /* Region access must retain the original alpha, before any rendering. */
    SDL_Surface *region = assets_surface_region("sprites/test/159", 0, 0, 1, 1);
    CHECK(region != NULL);
    if (region) {
        Uint8 r, g, b, a;
        Uint32 pixel;
        memcpy(&pixel, region->pixels, sizeof(pixel));
        SDL_GetRGBA(pixel, region->format, &r, &g, &b, &a);
        CHECK(r == last_pixel[0] && g == last_pixel[1] && b == last_pixel[2]);
        CHECK(a == 128);
    }
    SDL_FreeSurface(region);

    SDL_Texture *last = assets_texture("sprites/test/159");
    if (!last)
        return;
    CHECK(SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE) == 0);
    CHECK(SDL_SetRenderDrawColor(renderer, 20, 40, 60, 255) == 0);
    CHECK(SDL_RenderClear(renderer) == 0);
    SDL_Rect destination = {2, 2, 4, 4};
    CHECK(SDL_RenderCopy(renderer, last, NULL, &destination) == 0);
    unsigned char pixels[8 * 8 * 4];
    CHECK(SDL_RenderReadPixels(renderer, NULL, SDL_PIXELFORMAT_RGBA32, pixels, 8 * 4) == 0);
    for (int y = 0; y < 8; y++)
        for (int x = 0; x < 8; x++) {
            const unsigned char *pixel = &pixels[(y * 8 + x) * 4];
            bool inside = x >= 2 && x < 6 && y >= 2 && y < 6;
            const int background[] = {20, 40, 60};
            for (int channel = 0; channel < 3; channel++) {
                int expected = inside
                    ? (last_pixel[channel] * 128 + background[channel] * 127) / 255
                    : background[channel];
                CHECK(abs((int)pixel[channel] - expected) <= 1);
            }
            CHECK(pixel[3] == 255);
        }
    assets_unload();
}

static void reload_and_unload_release_the_complete_catalogue(void)
{
    /* Render once before taking the baseline: SDL may retain a reusable
     * render-command buffer, which is owned by the renderer, not assets. */
    int unloaded_allocations = SDL_GetNumAllocations();
    CHECK(assets_load(renderer));
    int loaded_allocations = SDL_GetNumAllocations();
    CHECK(loaded_allocations > unloaded_allocations);
    for (int attempt = 0; attempt < 4; attempt++) {
        SDL_Texture *last = assets_texture("sprites/test/159");
        CHECK(last != NULL);
        if (!last)
            break;
        CHECK(SDL_SetTextureColorMod(last, 8, 17, 26) == 0);
        CHECK(SDL_SetTextureAlphaMod(last, 19) == 0);
        CHECK(assets_load(renderer));
        CHECK(SDL_GetNumAllocations() == loaded_allocations);
        last = assets_texture("sprites/test/159");
        CHECK(last != NULL);
        if (last) {
            Uint8 r, g, b, a;
            CHECK(SDL_GetTextureColorMod(last, &r, &g, &b) == 0);
            CHECK(r == 255 && g == 255 && b == 255);
            CHECK(SDL_GetTextureAlphaMod(last, &a) == 0);
            CHECK(a == 255);
        }
    }
    /* Failed reload must release the old table too, rather than leave stale
     * textures discoverable under names from the previous successful load. */
    CHECK(!assets_load(NULL));
    for (int i = 0; i < embedded_image_count; i++)
        CHECK(assets_texture(embedded_images[i].name) == NULL);
    CHECK(SDL_GetNumAllocations() == unloaded_allocations);
    assets_unload();
    assets_unload();
    CHECK(SDL_GetNumAllocations() == unloaded_allocations);
    CHECK(assets_load(renderer));
    CHECK(assets_texture("sprites/test/159") != NULL);
    assets_unload();
    CHECK(SDL_GetNumAllocations() == unloaded_allocations);
}

int main(void)
{
    printf("assets_loader (160-image offscreen regression)\n");
    SDL_SetMainReady();
    CHECK(SDL_setenv("SDL_VIDEODRIVER", "dummy", 1) == 0);
    /* A global linear preference catches a loader that forgets to set the
     * explicit per-texture nearest mode required by native pixel art. */
    CHECK(SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "1") == SDL_TRUE);
    CHECK(SDL_Init(SDL_INIT_VIDEO) == 0);
    canvas = SDL_CreateRGBSurfaceWithFormat(0, 8, 8, 32, SDL_PIXELFORMAT_RGBA32);
    CHECK(canvas != NULL);
    if (canvas)
        renderer = SDL_CreateSoftwareRenderer(canvas);
    CHECK(renderer != NULL);
    if (!test_failures) {
        RUN(embedded_lookup_and_unloaded_lifecycle);
        RUN(catalogue_beyond_old_capacity_and_native_pixels);
        RUN(reload_and_unload_release_the_complete_catalogue);
    }
    assets_unload();
    SDL_DestroyRenderer(renderer);
    SDL_FreeSurface(canvas);
    SDL_Quit();
    return TEST_EXIT();
}
