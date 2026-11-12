/* Real embedded sheriff art and software rendering: both cylinder reloads
 * must animate and remain visible, including stationary reloads in fire. */
#define SDL_MAIN_HANDLED
#include <stdint.h>
#include <SDL.h>

#include "app/stage.h"
#include "engine/assets.h"
#include "game/player_render.h"
#include "test.h"

static SDL_Renderer *renderer;
static CharacterSkin skin;
static StagePlay play;
static Profile profile;
static AppOptions options;
static Uint32 pixels[160 * 272];

static uint32_t draw_body(void)
{
    SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255);
    SDL_RenderClear(renderer);
    player_render(renderer, &play.player, &skin, play.guns, 0, play.player.x - VIEW_WIDTH / 2);
    SDL_Rect body = {VIEW_WIDTH / 2 - 80, BASELINE - 264, 160, 272};
    CHECK(SDL_RenderReadPixels(renderer, &body, SDL_PIXELFORMAT_ARGB8888,
                               pixels, 160 * (int)sizeof(Uint32)) == 0);
    uint32_t hash = UINT32_C(2166136261);
    int visible = 0;
    for (int i = 0; i < 160 * 272; i++) {
        visible += (pixels[i] & 0xffffff) != 0;
        hash = (hash ^ pixels[i]) * UINT32_C(16777619);
    }
    CHECK(visible > 2000); /* A muzzle/torch alone cannot stand in for the body. */
    return hash;
}

static void reload_pair(bool walking, bool fire, int facing, bool light, bool automatic)
{
    profile = (Profile){0};
    progress_init(&profile.progress);
    stage_record_init(&profile.record);
    profile.progress.level = POWER_LEVEL;
    stage_start(&play, 0, &CHARACTERS[0], &profile.progress);
    terrain_clear(&play.run.terrain);
    play.run.zombie_count = 0;
    if (fire) {
        terrain_add(&play.run.terrain, TERRAIN_BARREL, play.player.x)->blowing = true;
        InputState idle = {0};
        CHECK(stage_step(&play, &idle, &profile, &options));
        terrain_add(&play.run.terrain, TERRAIN_FIRE, play.player.x);
        CHECK(play.player.health < play.player.max_health);
    }
    play.player.facing = facing;
    play.player.light_on = light;
    play.player.light_since = 10.0f;
    play.player.shot.rounds = automatic ? 1 : 2;
    play.player.shot.other_rounds = automatic ? 1 : 5;
    play.player.shot.next_other = !automatic && facing == FACING_LEFT;
    InputState input = {0};
    input.pressed[automatic ? ACTION_SHOOT : ACTION_RELOAD] = true;
    input.down[ACTION_SHOOT] = automatic;
    if (walking)
        input.down[facing == FACING_LEFT ? ACTION_LEFT : ACTION_RIGHT] = true;
    uint32_t last[2] = {0};
    int changes[2] = {0}, seen[2] = {0};
    for (int tick = 0; tick < 300; tick++) {
        CHECK(stage_step(&play, &input, &profile, &options));
        input.pressed[ACTION_RELOAD] = false;
        input.pressed[ACTION_SHOOT] = false;
        if (!shot_reloading(&play.player.shot)) {
            if (seen[0] > 0 && seen[1] > 0) break;
            continue;
        }
        int hand = play.player.shot.reload_other;
        if (automatic && hand) input.down[ACTION_SHOOT] = false;
        uint32_t hash = draw_body();
        changes[hand] += hash != last[hand];
        last[hand] = hash;
        seen[hand]++;
    }
    CHECK(seen[0] >= 60 && seen[1] >= 60);
    CHECK(changes[0] >= 6 && changes[1] >= 6);
    CHECK(play.player.shot.rounds == 8 && play.player.shot.other_rounds == 8);
}

static void stationary_duals_animate_both_reloads(void) { reload_pair(false, false, FACING_RIGHT, false, false); }
static void fire_damage_does_not_hide_a_stationary_reload(void) { reload_pair(false, true, FACING_RIGHT, false, false); }
static void an_empty_cylinder_on_fire_keeps_the_whole_character_visible(void) { reload_pair(false, true, FACING_RIGHT, false, true); }
static void walking_left_with_a_light_keeps_both_reloads_visible(void) { reload_pair(true, true, FACING_LEFT, true, false); }

static void low_reload_barrels_are_drawn_over_the_walking_legs(void)
{
    profile = (Profile){0};
    progress_init(&profile.progress);
    profile.progress.level = POWER_LEVEL;
    stage_start(&play, 0, &CHARACTERS[0], &profile.progress);
    play.player.shot.rounds = 2;
    play.player.shot.other_rounds = 8;
    InputState input = {0};
    input.down[ACTION_RIGHT] = true;
    for (int tick = 0; tick < 45; tick++) {
        input.pressed[ACTION_RELOAD] = tick == 0;
        player_update(&play.player, &input, FIXED_DT);
    }
    CHECK(play.player.reload_walk && shot_reloading(&play.player.shot));
    CHECK(skin.weapon_reload_lower[WEAPON_DUAL] != NULL);
    uint32_t complete = draw_body();
    SDL_Texture *lower = skin.weapon_reload_lower[WEAPON_DUAL];
    skin.weapon_reload_lower[WEAPON_DUAL] = NULL;
    CHECK(draw_body() != complete); /* A cropped body alone loses the low muzzle. */
    skin.weapon_reload_lower[WEAPON_DUAL] = lower;
}

int main(void)
{
    SDL_SetMainReady();
    SDL_setenv("SDL_VIDEODRIVER", "dummy", 1);
    CHECK(SDL_Init(SDL_INIT_VIDEO) == 0);
    SDL_Surface *surface = SDL_CreateRGBSurfaceWithFormat(0, VIEW_WIDTH, VIEW_HEIGHT, 32, SDL_PIXELFORMAT_ARGB8888);
    CHECK(surface != NULL);
    renderer = surface ? SDL_CreateSoftwareRenderer(surface) : NULL;
    CHECK(renderer != NULL);
    if (renderer) {
        CHECK(assets_load(renderer));
        skin_load(&skin, renderer, &CHARACTERS[0]);
        RUN(stationary_duals_animate_both_reloads);
        RUN(fire_damage_does_not_hide_a_stationary_reload);
        RUN(an_empty_cylinder_on_fire_keeps_the_whole_character_visible);
        RUN(walking_left_with_a_light_keeps_both_reloads_visible);
        RUN(low_reload_barrels_are_drawn_over_the_walking_legs);
        skin_free(&skin);
        assets_unload();
        SDL_DestroyRenderer(renderer);
    }
    SDL_FreeSurface(surface);
    SDL_Quit();
    return TEST_EXIT();
}
