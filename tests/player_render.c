/* Real embedded sheriff art and software rendering: both cylinder reloads
 * must animate and remain visible, including stationary reloads in fire. */
#define SDL_MAIN_HANDLED
#include <stdint.h>
#include <math.h>
#include <SDL.h>

#include "app/stage.h"
#include "engine/assets.h"
#include "game/car_pass.h"
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

static Uint32 reload_pixels[PLAYER_SHOOT_FRAME_W * SPRITE_SCALE * PLAYER_SHOOT_FRAME_H * SPRITE_SCALE];

static bool reload_steel(unsigned color)
{
    return color == 0xb3b8b6 || color == 0xa1aaa9 || color == 0x747b77;
}

static void walking_dual_reloads_keep_the_complete_guns_and_hands_in_every_pose(void)
{
    CharacterSkin sheriff = skin;
    const char *preview = SDL_getenv("THE_MIRACLE_RELOAD_PREVIEW");
    for (int suit = 0; suit < 2; suit++) {
        if (suit) CHECK(skin_load_suit(&skin, renderer, &CHARACTERS[0]));
        char name[128];
        const EmbeddedImage *full[2], *lower[2];
        for (int hand = 0; hand < 2; hand++) {
            snprintf(name, sizeof(name), "sprites/characters/cowgirl/%sreload_dual%s", suit ? "suit/" : "", hand ? "_b" : "");
            full[hand] = assets_find_image(name);
            snprintf(name, sizeof(name), "sprites/characters/cowgirl/%sreload_dual%s_lower", suit ? "suit/" : "", hand ? "_b" : "");
            lower[hand] = assets_find_image(name);
            CHECK(full[hand] != NULL && lower[hand] != NULL);
        }
        snprintf(name, sizeof(name), "sprites/characters/cowgirl/%slegs_dual", suit ? "suit/" : "");
        const EmbeddedImage *legs = assets_find_image(name);
        CHECK(legs != NULL);
        progress_init(&profile.progress);
        profile.progress.level = POWER_LEVEL;
        stage_start(&play, 0, &CHARACTERS[0], &profile.progress);
        play.player.shot.rounds = play.player.shot.other_rounds = 2;
        InputState input = {0};
        input.pressed[ACTION_RELOAD] = input.down[ACTION_RIGHT] = true;
        player_update(&play.player, &input, FIXED_DT);
        CHECK(play.player.reload_walk && shot_reloading(&play.player.shot));
        CHECK_NEAR(play.player.shot.mag_reload_time, 1.2f, .0001f);
        CHECK(play.player.shot.magazine == 8);
        const AnimationDef *def = play.player.anim.def, *walk = play.player.legs.def;
        int split = PLAYER_WAIST_ROW + def->ground_y - walk->ground_y;
        int x_offset = (int)lroundf(def->anchor_x - walk->anchor_x), y_offset = def->ground_y - walk->ground_y;
        int width = def->frame_w * SPRITE_SCALE, height = def->frame_h * SPRITE_SCALE;
        /* Each hand alone, each hand first in a pair, and each hand second.
         * Two opposite leg phases at every reload pose cover the walk cycle. */
        for (int mode = 0; mode < 6; mode++)
            for (int f = 0; f < PLAYER_DUAL_RELOAD_FRAMES; f++)
                for (int facing = -1; facing <= 1; facing += 2)
                    for (int phase = 0; phase < 2; phase++) {
                        int hand = mode % 2;
                        play.player.shot.reload_other = hand != 0;
                        play.player.shot.reload_pair = mode >= 2;
                        play.player.shot.reload_all = mode == 2 || mode == 3;
                        play.player.shot.mag_reload = play.player.shot.mag_reload_time *
                            (1.0f - ((float)f + .5f) / PLAYER_DUAL_RELOAD_FRAMES);
                        int frame = mode >= 4 ? f + PLAYER_DUAL_RELOAD_FRAMES
                                  : mode >= 2 && f > PLAYER_DUAL_RELOAD_HANDOFF_FRAME ? PLAYER_DUAL_RELOAD_HANDOFF_FRAME : f;
                        int step = (f + phase * walk->frame_count / 2) % walk->frame_count;
                        int leg_step = step * (legs->width / walk->frame_w) / walk->frame_count;
                        animation_seek(&play.player.legs, step);
                        play.player.facing = facing;
                        SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255);
                        SDL_RenderClear(renderer);
                        player_render(renderer, &play.player, &skin, play.guns, 0, play.player.x - VIEW_WIDTH / 2);
                        float anchor = facing < 0 ? def->frame_w - def->anchor_x : def->anchor_x;
                        SDL_Rect box = {(int)lroundf(VIEW_WIDTH / 2 - anchor * SPRITE_SCALE),
                                        BASELINE - def->ground_y * SPRITE_SCALE, width, height};
                        CHECK(SDL_RenderReadPixels(renderer, &box, SDL_PIXELFORMAT_ARGB8888, reload_pixels, width * 4) == 0);
                        int mismatches = 0, missing_gun = 0, highlights = 0;
                        if (!full[hand] || !lower[hand] || !legs) continue;
                        for (int y = 0; y < def->frame_h; y++)
                            for (int x = 0; x < def->frame_w; x++) {
                                const unsigned char *upper = full[hand]->rgba + (y * full[hand]->width + frame * def->frame_w + x) * 4;
                                const unsigned char *c = upper;
                                static const unsigned char transparent[4] = {0};
                                if (y >= split) {
                                    c = lower[hand]->rgba + (y * lower[hand]->width + frame * def->frame_w + x) * 4;
                                    if (!c[3]) {
                                        int lx = x - x_offset, ly = y - y_offset;
                                        c = lx >= 0 && lx < walk->frame_w && ly >= 0 && ly < walk->frame_h
                                              ? legs->rgba + (ly * legs->width + leg_step * walk->frame_w + lx) * 4 : transparent;
                                    }
                                }
                                unsigned expected = c[3] ? ((unsigned)c[0] << 16) | ((unsigned)c[1] << 8) | c[2] : 0;
                                int px = (facing < 0 ? def->frame_w - 1 - x : x) * SPRITE_SCALE + SPRITE_SCALE / 2;
                                unsigned actual = reload_pixels[(y * SPRITE_SCALE + SPRITE_SCALE / 2) * width + px] & 0xffffff;
                                mismatches += actual != expected;
                                unsigned gun = ((unsigned)upper[0] << 16) | ((unsigned)upper[1] << 8) | upper[2];
                                if (y >= split && upper[3] && reload_steel(gun)) {
                                    highlights++;
                                    missing_gun += actual != gun;
                                }
                            }
                        CHECK(mismatches == 0); /* Action over animated legs, no static thigh. */
                        CHECK(highlights > 0 && missing_gun == 0); /* Full-frame guns survive the cut. */
                        if (preview && phase == 0 && (mode == 2 || mode == 5)) {
                            SDL_Surface *shot = SDL_CreateRGBSurfaceWithFormatFrom(reload_pixels, width, height, 32, width * 4,
                                                                                  SDL_PIXELFORMAT_ARGB8888);
                            snprintf(name, sizeof(name), "%s/%s_%s_%02d.bmp", preview, suit ? "suit" : "sheriff",
                                     facing < 0 ? "left" : "right", f + (mode == 5 ? PLAYER_DUAL_RELOAD_FRAMES : 0));
                            CHECK(shot && SDL_SaveBMP(shot, name) == 0);
                            SDL_FreeSurface(shot);
                        }
                    }
        if (suit) skin_free(&skin);
        skin = sheriff;
    }
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

static void swat_drink_uses_the_full_hand_sequence_and_keeps_the_slung_weapon_while_walking(void)
{
    CharacterSkin sheriff = skin;
    skin_load(&skin, renderer, &CHARACTERS[1]);
    const EmbeddedImage *legs = assets_find_image("sprites/characters/swat/legs");
    CHECK(legs != NULL);
    for (int slot = 0; slot < 2; slot++) {
        progress_init(&profile.progress);
        stage_start(&play, 0, &CHARACTERS[1], &profile.progress);
        WeaponId gun = play.guns[slot];
        play.guns[0] = gun;
        const WeaponDef *weapon = weapon_def(gun);
        CHECK(weapon->drink_frames == 31 && skin.weapon_drink[gun] != NULL);
        CHECK(skin.weapon_drink_lower[gun] != NULL);
        char name[96];
        snprintf(name, sizeof(name), "sprites/characters/swat/%s", weapon->drink_sheet);
        const EmbeddedImage *care = assets_find_image(name);
        snprintf(name, sizeof(name), "sprites/characters/swat/%s", weapon->drink_lower_sheet);
        const EmbeddedImage *lower = assets_find_image(name);
        CHECK(care != NULL && lower != NULL);
        if (!care || !lower || !legs) continue;
        for (int walking = 0; walking < 2; walking++) {
            InputState input = {0};
            input.down[ACTION_RIGHT] = walking;
            play.player.drink_time = 0.0f;
            player_update(&play.player, &input, FIXED_DT);
            play.player.light_on = false;
            play.player.light_since = 10.0f;
            for (int direction = -1; direction <= 1; direction += 2) {
                play.player.facing = direction;
                for (int f = 0; f < weapon->drink_frames; f++) {
                    play.player.drink_time = player_drink_duration(&play.player) * (1.0f - ((float)f + .5f) / (float)weapon->drink_frames);
                    int step = walking ? f % PLAYER_WALK_FRAMES : 0;
                    animation_seek(&play.player.anim, step);
                    draw_body();
                    int mismatches = 0;
                    for (int y = 2; y < 70; y++) {
                        for (int x = 12; x < 51; x++) {
                            const unsigned char *color = care->rgba + (y * care->width + f * 81 + x) * 4;
                            if (walking && y >= 51) {
                                color = lower->rgba + (y * lower->width + f * 81 + x) * 4;
                                if (!color[3])
                                    color = legs->rgba + ((y - 7) * legs->width + step * 42 + x - 12) * 4;
                            }
                            unsigned expected = color[3] ? ((unsigned)color[0] << 16) | ((unsigned)color[1] << 8) | color[2] : 0;
                            int px = direction < 0 ? 202 - 4 * x : -46 + 4 * x;
                            int py = -8 + 4 * y;
                            mismatches += (pixels[(py + 1) * 160 + px + 1] & 0xffffff) != expected;
                        }
                    }
                    CHECK(mismatches == 0);
                }
            }
        }
    }
    skin_free(&skin);
    skin = sheriff;
}

static void swat_breathing_with_the_flashlight_keeps_the_belt_connected(void)
{
    CharacterSkin sheriff = skin;
    skin_load(&skin, renderer, &CHARACTERS[1]);
    progress_init(&profile.progress);
    for (int slot = 0; slot < 2; slot++) {
        stage_start(&play, 0, &CHARACTERS[1], &profile.progress);
        play.guns[0] = play.guns[slot];
        play.player.light_on = true;
        play.player.light_time = 1.0f;
        for (int direction = -1; direction <= 1; direction += 2) {
            play.player.facing = direction;
            for (int breath = 0; breath < PLAYER_LIGHT_BREATHS; breath++) {
                play.player.light_since = (8.25f + (float)breath) / PLAYER_LIGHT_BREATH_FPS;
                draw_body();
                for (int x = 27; x < 38; x++) {
                    int px = direction < 0 ? 202 - 4 * x : -46 + 4 * x;
                    int py = -8 + 4 * 50;
                    CHECK((pixels[(py + 1) * 160 + px + 1] & 0xffffff) != 0);
                }
            }
        }
    }
    skin_free(&skin);
    skin = sheriff;
}

static void swat_walking_pelvis_matches_the_standing_belt_root_in_both_directions(void)
{
    CharacterSkin sheriff = skin;
    skin_load(&skin, renderer, &CHARACTERS[1]);
    const EmbeddedImage *standing = assets_find_image("sprites/characters/swat/shoot");
    CHECK(standing != NULL);
    progress_init(&profile.progress);
    for (int slot = 0; slot < 2; slot++) {
        for (int direction = -1; direction <= 1; direction += 2) {
            stage_start(&play, 0, &CHARACTERS[1], &profile.progress);
            play.guns[0] = play.guns[slot];
            InputState move = {0};
            move.down[direction < 0 ? ACTION_LEFT : ACTION_RIGHT] = true;
            player_update(&play.player, &move, FIXED_DT);
            play.player.light_since = 10.0f;
            for (int lit = 0; lit < 2; lit++) {
                play.player.light_on = lit;
                for (int f = 0; f < PLAYER_WALK_FRAMES; f++) {
                    animation_seek(&play.player.anim, f);
                    draw_body();
                    int mismatches = 0;
                    if (standing) {
                        for (int x = 22; x < 43; x++) {
                            const unsigned char *c = standing->rgba + (52 * standing->width + x) * 4;
                            unsigned expected = c[3] ? ((unsigned)c[0] << 16) | ((unsigned)c[1] << 8) | c[2] : 0;
                            int px = direction < 0 ? 202 - 4 * x : -46 + 4 * x;
                            int py = -8 + 4 * 52;
                            mismatches += (pixels[(py + 1) * 160 + px + 1] & 0xffffff) != expected;
                        }
                    }
                    CHECK(mismatches == 0);
                }
            }
        }
    }
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

static void check_entire_cell(const EmbeddedImage *image, int frame, const AnimationDef *def)
{
    int width = def->frame_w, height = def->frame_h;
    static Uint32 cell[324 * 320];
    SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255);
    SDL_RenderClear(renderer);
    player_render(renderer, &play.player, &skin, play.guns, play.weapon_slot, play.player.x - VIEW_WIDTH / 2);
    float anchor = play.player.facing < 0 ? width - def->anchor_x : def->anchor_x;
    SDL_Rect box = {VIEW_WIDTH / 2 - (int)lroundf(anchor * SPRITE_SCALE),
                    BASELINE - def->ground_y * SPRITE_SCALE, width * SPRITE_SCALE, height * SPRITE_SCALE};
    CHECK(SDL_RenderReadPixels(renderer, &box, SDL_PIXELFORMAT_ARGB8888, cell,
                              box.w * (int)sizeof(Uint32)) == 0);
    int mismatches = 0;
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            const unsigned char *c = image->rgba + (y * image->width + frame * width + x) * 4;
            unsigned expected = c[3] ? ((unsigned)c[0] << 16) | ((unsigned)c[1] << 8) | c[2] : 0;
            int px = (play.player.facing < 0 ? width - 1 - x : x) * SPRITE_SCALE + 1;
            unsigned actual = cell[(y * SPRITE_SCALE + 1) * box.w + px] & 0xffffff;
            mismatches += actual != expected;
        }
    }
    if (mismatches)
        fprintf(stderr, "  cell %s frame=%d facing=%d gun=%d differences=%d\n",
                image->name, frame, play.player.facing, play.guns[play.weapon_slot], mismatches);
    CHECK(mismatches == 0);
}

static void check_entire_swat_cell(const EmbeddedImage *image, int frame)
{
    check_entire_cell(image, frame, play.player.anim.def);
}

static void every_sheriff_walk_frame_is_visible_in_both_skins_and_directions(void)
{
    CharacterSkin normal = skin;
    for (int suit = 0; suit < 2; suit++) {
        if (suit) CHECK(skin_load_suit(&skin, renderer, &CHARACTERS[0]));
        for (int dual = 0; dual < 2; dual++) {
            progress_init(&profile.progress);
            profile.progress.level = dual ? POWER_LEVEL : 1;
            stage_start(&play, 0, &CHARACTERS[0], &profile.progress);
            play.player.light_on = false;
            play.player.light_since = 10.0f;
            play.player.state = PLAYER_WALK;
            animation_play(&play.player.anim, player_walk_animation(PLAYER_SHERIFF_WALK_FRAMES));
            char name[96];
            snprintf(name, sizeof(name), "sprites/characters/cowgirl/%swalk%s", suit ? "suit/" : "", dual ? "_dual" : "");
            const EmbeddedImage *image = assets_find_image(name);
            CHECK(image != NULL);
            if (!image) continue;
            CHECK(image->width == PLAYER_SHERIFF_WALK_FRAMES * PLAYER_WALK_FRAME_W);
            snprintf(name, sizeof(name), "sprites/characters/cowgirl/%slight_walk%s", suit ? "suit/" : "", dual ? "_dual" : "");
            const EmbeddedImage *lit = assets_find_image(name);
            CHECK(lit != NULL);
            if (!lit) continue;
            CHECK(lit->width == (PLAYER_SHERIFF_WALK_FRAMES + PLAYER_LIGHT_BREATHS) * PLAYER_SHOOT_FRAME_W);
            for (int direction = -1; direction <= 1; direction += 2) {
                play.player.facing = direction;
                play.player.state = PLAYER_WALK;
                for (int frame = 0; frame < PLAYER_SHERIFF_WALK_FRAMES; frame++) {
                    play.player.light_on = false;
                    animation_seek(&play.player.anim, frame);
                    check_entire_swat_cell(image, frame);
                    draw_body();
                    play.player.light_on = true;
                    check_entire_cell(lit, frame, player_melee_animation());
                }
                play.player.state = PLAYER_IDLE;
                for (int breath = 0; breath < PLAYER_LIGHT_BREATHS; breath++) {
                    play.player.light_since = (12.0f + (float)breath + .25f) / PLAYER_LIGHT_BREATH_FPS;
                    check_entire_cell(lit, PLAYER_SHERIFF_WALK_FRAMES + breath, player_melee_animation());
                }
            }
        }
        if (suit) skin_free(&skin);
        skin = normal;
    }
}

/* The dual walking path already has an exhaustive action/legs comparison
 * above. Cover the upright single reload and planted dual reloads as well:
 * comparing the actual frame prevents a renderer cut or a lighting overlay
 * from erasing a correctly authored forearm, glove or held weapon. */
static void single_and_planted_dual_reloads_keep_every_action_pixel(void)
{
    CharacterSkin normal = skin;
    static unsigned char combined[PLAYER_SHOOT_FRAME_W * PLAYER_SHOOT_FRAME_H * 4];
    for (int suit = 0; suit < 2; suit++) {
        if (suit) CHECK(skin_load_suit(&skin, renderer, &CHARACTERS[0]));
        for (int dual = 0; dual < 2; dual++) {
            progress_init(&profile.progress);
            profile.progress.level = dual ? POWER_LEVEL : 1;
            stage_start(&play, 0, &CHARACTERS[0], &profile.progress);
            play.player.light_on = false;
            play.player.shot.rounds = 2;
            play.player.shot.other_rounds = 3;
            InputState input = {0};
            input.pressed[ACTION_RELOAD] = true;
            player_update(&play.player, &input, FIXED_DT);
            CHECK(shot_reloading(&play.player.shot));
            const AnimationDef *def = play.player.anim.def;
            const AnimationDef *walk = player_walk_animation(PLAYER_SHERIFF_WALK_FRAMES);
            int split = PLAYER_WAIST_ROW + def->ground_y - walk->ground_y;
            int dx = (int)lroundf(def->anchor_x - walk->anchor_x), dy = def->ground_y - walk->ground_y;
            char name[128];
            snprintf(name, sizeof(name), "sprites/characters/cowgirl/%slegs", suit ? "suit/" : "");
            const EmbeddedImage *legs = assets_find_image(name);
            CHECK(legs != NULL);
            for (int hand = 0; hand < (dual ? 2 : 1); hand++) {
                snprintf(name, sizeof(name), "sprites/characters/cowgirl/%sreload%s",
                         suit ? "suit/" : "", dual ? (hand ? "_dual_b" : "_dual") : "");
                const EmbeddedImage *image = assets_find_image(name);
                CHECK(image != NULL);
                if (!image || !legs) continue;
                int count = dual ? PLAYER_DUAL_RELOAD_SHEET_FRAMES : PLAYER_RELOAD_FRAMES;
                for (int frame = 0; frame < count; frame++) {
                    play.player.shot.reload_other = hand != 0;
                    play.player.shot.reload_pair = dual && frame >= PLAYER_DUAL_RELOAD_FRAMES;
                    play.player.shot.reload_all = false;
                    int progress = dual ? frame % PLAYER_DUAL_RELOAD_FRAMES : frame;
                    int frames = dual ? PLAYER_DUAL_RELOAD_FRAMES : PLAYER_RELOAD_FRAMES;
                    play.player.shot.mag_reload = play.player.shot.mag_reload_time *
                        (1.0f - ((float)progress + .5f) / (float)frames);
                    animation_set_frame(&play.player.anim, dual ? 0 : frame);
                    for (int facing = -1; facing <= 1; facing += 2) {
                        play.player.facing = facing;
                        play.player.state = PLAYER_SHOOT;
                        play.player.reload_walk = false;
                        check_entire_cell(image, frame, def);
                        if (dual) continue; /* Its walking cases are tested above. */
                        for (int phase = 0; phase < 3; phase++) {
                            int step = phase == 0 ? 0 : phase == 1 ? 7 : walk->frame_count - 1;
                            animation_play(&play.player.legs, walk);
                            animation_seek(&play.player.legs, step);
                            int leg_frame = player_walk_art_frame(&play.player.legs, legs->width / walk->frame_w);
                            for (int y = 0; y < def->frame_h; y++)
                                for (int x = 0; x < def->frame_w; x++) {
                                    const unsigned char *c = image->rgba +
                                        (y * image->width + frame * def->frame_w + x) * 4;
                                    static const unsigned char transparent[4] = {0};
                                    if (y >= split) {
                                        int lx = x - dx, ly = y - dy;
                                        c = lx >= 0 && lx < walk->frame_w && ly >= 0 && ly < walk->frame_h
                                                ? legs->rgba + (ly * legs->width + leg_frame * walk->frame_w + lx) * 4
                                                : transparent;
                                    }
                                    for (int channel = 0; channel < 4; channel++)
                                        combined[(y * def->frame_w + x) * 4 + channel] = c[channel];
                                }
                            EmbeddedImage expected = {.name = "single walking reload composite", .width = def->frame_w,
                                                       .height = def->frame_h, .rgba = combined};
                            play.player.state = PLAYER_WALK;
                            play.player.reload_walk = true;
                            check_entire_cell(&expected, 0, def);
                        }
                    }
                }
            }
        }
        if (suit) skin_free(&skin);
        skin = normal;
    }
}

static void swat_grenade_and_bench_keep_each_full_frame_in_both_directions(void)
{
    CharacterSkin sheriff = skin;
    skin_load(&skin, renderer, &CHARACTERS[1]);
    for (int slot = 0; slot < 2; slot++) {
        for (int direction = -1; direction <= 1; direction += 2) {
            progress_init(&profile.progress);
            stage_start(&play, 0, &CHARACTERS[1], &profile.progress);
            play.weapon_slot = slot;
            play.player.facing = direction;
            char name[96];
            const WeaponDef *weapon = weapon_def(play.guns[slot]);
            snprintf(name, sizeof(name), "sprites/characters/swat/%s", weapon->throw_sheet);
            const EmbeddedImage *image = assets_find_image(name);
            CHECK(image != NULL && skin.weapon_throw[play.guns[slot]] != NULL);
            CHECK(player_throw(&play.player));
            if (image) for (int frame = 0; frame < PLAYER_THROW_FRAMES; frame++) {
                animation_seek(&play.player.anim, frame);
                check_entire_swat_cell(image, frame);
            }
            stage_start(&play, 0, &CHARACTERS[1], &profile.progress);
            play.weapon_slot = slot;
            play.player.facing = direction;
            CHECK(player_sit(&play.player, play.player.x, 1u << slot));
            snprintf(name, sizeof(name), "sprites/characters/swat/%s", weapon->sit_sheet ? weapon->sit_sheet : "sit");
            image = assets_find_image(name);
            CHECK(image != NULL);
            if (image) for (int frame = 0; frame < 40; frame++) {
                play.player.sit_time = 1.0f;
                play.player.sit_gun = -1;
                if (frame < 8) play.player.sit_time = ((float)frame + .5f) / 8.0f;
                else if (frame < 12) {
                    static const int rest[] = {1, 2, 1, 3};
                    animation_set_frame(&play.player.anim, rest[frame - 8]);
                } else if (frame < 36) {
                    play.player.sit_gun = slot;
                    play.player.sit_gun_time = ((float)(frame - 12) + .5f) / 24.0f * 2.8f;
                } else animation_set_frame(&play.player.anim, 10 + frame - 36);
                check_entire_swat_cell(image, frame);
            }
        }
    }
    skin_free(&skin);
    skin = sheriff;
}

static bool solid(const EmbeddedImage *image, int x, int y)
{
    return x >= 0 && y >= 0 && x < image->width && y < image->height && image->rgba[(y * image->width + x) * 4 + 3];
}

/* Through a car (N), on every car, both ways, opened or broken into: what of
 * her is in the car (row 1 of her sheet) always lies on the car, under its
 * panels and doors or seen through a doorway or its glass; never above its
 * roof (her hat ducks under it) nor below its floor. While she is out of it
 * (walking, opening, breaking the glass and reaching in by it, shutting)
 * nothing of her is in that row, so the car never covers her. Checked with
 * car_plan and the embedded sheets the game draws. */
static void car_crossing_keeps_her_on_the_right_side_of_the_car(void)
{
    const char *sheets[] = {"sprites/characters/cowgirl/car", "sprites/characters/swat/car",
                            "sprites/characters/swat/car_shotgun"};
    const EmbeddedImage *body = assets_find_image("sprites/terrain/car_passage");
    CHECK(body != NULL && body->width == CAR_DOOR_STATES * VEHICLE_LOOKS * CAR_WRECK_W);
    for (int who = 0; who < 3 && body; who++) {
        const EmbeddedImage *her = assets_find_image(sheets[who]);
        CHECK(her != NULL && her->width == CAR_PASS_FRAMES * CAR_FRAME_W && her->height == 2 * CAR_FRAME_H);
        if (!her) continue;
        for (int look = 0; look < VEHICLE_LOOKS; look++)
            for (int facing = -1; facing <= 1; facing += 2)
                for (int smash = 0; smash < 2; smash++) {
                    float car_x = 4000.0f;
                    float from = car_x - (float)facing * (CAR_WRECK_W * SPRITE_SCALE / 2.0f + PLAYER_BODY_HALF_WIDTH);
                    CarPlan plan;
                    car_plan(&plan, from, car_x, look, facing, smash);
                    float end = plan.at[CAR_STEPS], hit = car_plan_action(&plan);
                    CHECK(end > 2.0f && end < CAR_PASS_MAX_SECONDS);
                    float last = from;
                    int stray = 0, covered = 0;
                    for (float t = 0.0f; t < end; t += FIXED_DT) {
                        float x = car_plan_x(&plan, t);
                        CHECK((x - last) * (float)facing >= -0.001f); /* Never back the way she came */
                        last = x;
                        int frame = car_plan_frame(&plan, t);
                        float phase;
                        CarStep step = car_plan_step(&plan, t, &phase);
                        int glass = smash && t >= hit ? (facing > 0 ? 1 : 2) : 0;
                        int state = look * CAR_DOOR_STATES + car_plan_doors(&plan, t, glass);
                        bool out_of_it = step == CAR_STEP_WALK_IN || step == CAR_STEP_SETTLE ||
                                         step == CAR_STEP_REACH || step == CAR_STEP_STRIKE ||
                                         step == CAR_STEP_PULL || step == CAR_STEP_READY ||
                                         step == CAR_STEP_WALK_OUT;
                        for (int y = 0; y < CAR_FRAME_H; y++)
                            for (int col = 0; col < CAR_FRAME_W; col++) {
                                if (!solid(her, frame * CAR_FRAME_W + col, CAR_FRAME_H + y))
                                    continue;
                                covered += out_of_it;
                                /* Her pixel's middle, in art px from the car frame's left. */
                                float left = facing > 0 ? (float)col - 31.5f : 30.5f - (float)col;
                                float at = (x - car_x) / SPRITE_SCALE + left + 0.5f + CAR_WRECK_W / 2.0f;
                                int cx = (int)floorf(at), cy = y - (68 - CAR_WRECK_H);
                                bool on = false;
                                for (int d = -1; d <= 1 && !on; d++) /* A px of rounding either way */
                                    on = cx + d >= 0 && cx + d < CAR_WRECK_W &&
                                         solid(body, state * CAR_WRECK_W + cx + d, cy);
                                stray += !on;
                            }
                    }
                    CHECK(stray == 0);
                    CHECK(covered == 0);
                }
    }
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
        RUN(every_sheriff_walk_frame_is_visible_in_both_skins_and_directions);
        RUN(single_and_planted_dual_reloads_keep_every_action_pixel);
        RUN(stationary_duals_animate_both_reloads);
        RUN(fire_damage_does_not_hide_a_stationary_reload);
        RUN(an_empty_cylinder_on_fire_keeps_the_whole_character_visible);
        RUN(walking_left_with_a_light_keeps_both_reloads_visible);
        RUN(low_reload_barrels_are_drawn_over_the_walking_legs);
        RUN(walking_dual_reloads_keep_the_complete_guns_and_hands_in_every_pose);
        RUN(swat_reload_keeps_the_whole_walking_thigh_and_magazine);
        RUN(swat_uses_painted_carry_and_each_visible_muzzle);
        RUN(swat_drink_uses_the_full_hand_sequence_and_keeps_the_slung_weapon_while_walking);
        RUN(swat_breathing_with_the_flashlight_keeps_the_belt_connected);
        RUN(swat_walking_pelvis_matches_the_standing_belt_root_in_both_directions);
        RUN(swat_grenade_and_bench_keep_each_full_frame_in_both_directions);
        RUN(car_crossing_keeps_her_on_the_right_side_of_the_car);
        skin_free(&skin);
        assets_unload();
        SDL_DestroyRenderer(renderer);
    }
    SDL_FreeSurface(surface);
    SDL_Quit();
    return TEST_EXIT();
}
