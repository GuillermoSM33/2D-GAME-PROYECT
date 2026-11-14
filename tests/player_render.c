/* Real embedded sheriff art and software rendering: both cylinder reloads
 * must animate and remain visible, including stationary reloads in fire. */
#define SDL_MAIN_HANDLED
#include <stdint.h>
#include <math.h>
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

static void swat_reload_keeps_the_whole_walking_thigh_and_magazine(void)
{
    CharacterSkin sheriff = skin;
    skin_load(&skin, renderer, &CHARACTERS[1]);
    const EmbeddedImage *walk = assets_find_image("sprites/characters/swat/legs");
    CHECK(walk != NULL);
    profile = (Profile){0};
    progress_init(&profile.progress);
    stage_start(&play, 0, &CHARACTERS[1], &profile.progress);
    play.flashlight = false;
    play.player.light_on = false;
    play.player.light_since = 10.0f;
    play.player.shot.rounds = 2;
    InputState input = {0};
    input.down[ACTION_RIGHT] = true;
    input.pressed[ACTION_RELOAD] = true;
    player_update(&play.player, &input, FIXED_DT);
    CHECK(play.player.reload_walk && shot_reloading(&play.player.shot));
    /* The removed magazine reaches below the belt in painted reload frame 2. */
    play.player.shot.mag_reload = play.player.shot.mag_reload_time * .70f;
    input.pressed[ACTION_RELOAD] = false;
    player_update(&play.player, &input, FIXED_DT);
    for (int left = 0; left < 2; left++) {
        play.player.facing = left ? FACING_LEFT : FACING_RIGHT;
        for (int f = 0; f < PLAYER_WALK_FRAMES; f++) {
            animation_seek(&play.player.legs, f);
            draw_body();
            int mismatches = 0;
            if (walk) {
                for (int y = 51; y < 55; y++)
                    for (int x = 3; x <= 36; x++) { /* Below the magazine, across both moving legs. */
                        const unsigned char *c = walk->rgba + (y * walk->width + f * 42 + x) * 4;
                        unsigned expected = c[3] ? ((unsigned)c[0] << 16) | ((unsigned)c[1] << 8) | c[2] : 0;
                        int px = left ? 154 - 4 * x : 2 + 4 * x;
                        int py = 20 + 4 * y;
                        mismatches += (pixels[(py + 1) * 160 + px + 1] & 0xffffff) != expected;
                    }
            }
            CHECK(mismatches == 0); /* No piece of the standing thigh may cover the moving one. */
        }
    }
    play.player.facing = FACING_RIGHT;
    uint32_t complete = draw_body();
    SDL_Texture *lower = skin.weapon_reload_lower[WEAPON_RIFLE];
    CHECK(lower != NULL);
    skin.weapon_reload_lower[WEAPON_RIFLE] = NULL;
    CHECK(draw_body() != complete);
    skin.weapon_reload_lower[WEAPON_RIFLE] = lower;
    /* Idle uses the separate neutral stance, with both boots grounded. */
    shot_cancel(&play.player.shot);
    input = (InputState){0};
    player_update(&play.player, &input, FIXED_DT);
    CHECK(play.player.state == PLAYER_IDLE);
    CHECK(skin.stand_sheet != NULL);
    draw_body();
    skin_free(&skin);
    skin = sheriff;
}

static void swat_uses_painted_carry_and_each_visible_muzzle(void)
{
    CharacterSkin sheriff = skin;
    skin_load(&skin, renderer, &CHARACTERS[1]);
    progress_init(&profile.progress);
    for (int slot = 0; slot < 2; slot++) {
        stage_start(&play, 0, &CHARACTERS[1], &profile.progress);
        play.player.light_since = 10.0f; /* The light-off transition has finished. */
        WeaponId id = play.guns[slot];
        const WeaponDef *weapon = weapon_def(id);
        play.weapon_slot = slot;
        /* draw_body uses slot zero: assign the reviewed gun there too. */
        play.guns[0] = id;
        play.weapon_slot = 0;
        CHECK(skin.weapon_carry[id] != NULL);
        for (int dir = -1; dir <= 1; dir += 2) {
            play.player.facing = dir;
            draw_body();
            static Uint32 wide[320 * 272], fallback[320 * 272];
            SDL_Rect region = {VIEW_WIDTH / 2 - 160, BASELINE - 264, 320, 272};
            CHECK(SDL_RenderReadPixels(renderer, &region, SDL_PIXELFORMAT_ARGB8888, wide,
                                       320 * (int)sizeof(Uint32)) == 0);
            SDL_Texture *carry = skin.weapon_carry[id];
            skin.weapon_carry[id] = NULL;
            draw_body();
            CHECK(SDL_RenderReadPixels(renderer, &region, SDL_PIXELFORMAT_ARGB8888, fallback,
                                       320 * (int)sizeof(Uint32)) == 0);
            int differences = 0;
            for (int i = 0; i < 320 * 272; i++) differences += wide[i] != fallback[i];
            CHECK(differences > 0); /* The complete muzzle must survive beyond the narrow utility template. */
            skin.weapon_carry[id] = carry;
            for (int sunk = 0; sunk < 2; sunk++) {
                play.player.wading = sunk;
                play.player.depth = sunk ? .5f : 0.0f;
                play.player.jump.height = 12.0f;
                bullets_clear(&play.bullets);
                stage_fire_weapon(&play, &profile.progress);
                const Bullet *bullet = &play.bullets.items[0];
                CHECK(bullet->active);
                CHECK(fabsf(bullet->x - (play.player.x + dir * weapon->muzzle_dx * SPRITE_SCALE)) < .01f);
                /* The central shotgun pellet follows the same barrel row. */
                int center = weapon->pellets / 2;
                bullet = &play.bullets.items[center];
                float y = BASELINE - (weapon->muzzle_rows - player_sunk_rows(&play.player)) * SPRITE_SCALE - 12.0f;
                CHECK(fabsf(bullet->y - y) < .01f);
            }
            play.player.wading = false;
            play.player.jump.height = 0.0f;
        }
    }
    skin_free(&skin);
    skin = sheriff;
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
        RUN(swat_reload_keeps_the_whole_walking_thigh_and_magazine);
        RUN(swat_uses_painted_carry_and_each_visible_muzzle);
        skin_free(&skin);
        assets_unload();
        SDL_DestroyRenderer(renderer);
    }
    SDL_FreeSurface(surface);
    SDL_Quit();
    return TEST_EXIT();
}
