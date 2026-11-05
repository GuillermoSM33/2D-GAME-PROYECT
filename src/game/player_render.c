#include "game/player_render.h"

#include <math.h>

#include "config.h"
#include "engine/assets.h"
#include "game/hang_render.h"

/* Rows [row0, row1) of one frame of def's sheet, placed as the whole frame
 * would be: pivot on her x, ground row on the baseline. */
static void draw_rows(SDL_Renderer *renderer, SDL_Texture *sheet, const AnimationDef *def, int frame,
                      int row0, int row1, const Player *player, float camera_x)
{
    bool left = player->facing == FACING_LEFT;
    /* Mirroring flips the pivot to the other side of the frame. */
    float anchor_x = left ? (float)def->frame_w - def->anchor_x : def->anchor_x;
    SDL_Rect src = {frame * def->frame_w, row0, def->frame_w, row1 - row0};
    SDL_Rect dst = {
        (int)lroundf(player->x - camera_x - anchor_x * SPRITE_SCALE),
        BASELINE - def->ground_y * SPRITE_SCALE - (int)lroundf(player->jump.height) + row0 * SPRITE_SCALE,
        def->frame_w * SPRITE_SCALE,
        (row1 - row0) * SPRITE_SCALE,
    };
    /* Left-facing frames are the right-facing art mirrored. */
    SDL_RenderCopyEx(renderer, sheet, &src, &dst, 0.0, NULL, left ? SDL_FLIP_HORIZONTAL : SDL_FLIP_NONE);
}

/* After a hit she blinks red; with no death sheet yet, a dead player is the
 * standing frame, dimmed. */
static void tint(SDL_Texture *sheet, const Player *player)
{
    bool blink_on = fmodf(player->hurt_time, 2.0f * PLAYER_BLINK_PERIOD) > PLAYER_BLINK_PERIOD;
    if (player->ghost) { /* Herself, seen by a parched mind: pale and see-through */
        SDL_SetTextureColorMod(sheet, 190, 205, 255);
        SDL_SetTextureAlphaMod(sheet, 110);
    } else if (!player_alive(player) && !player->fainted) { /* Fainted she is drawn as she is */
        SDL_SetTextureColorMod(sheet, 140, 90, 90);
        SDL_SetTextureAlphaMod(sheet, 170);
    } else if (player->hurt_time > 0.0f && blink_on) {
        SDL_SetTextureColorMod(sheet, 255, 90, 80);
    } else if (player->heal_time > 0.0f) {
        /* Healed: green, pulsing, fading out with the glow. */
        float k = player->heal_time / HEAL_GLOW_TIME;
        float pulse = 0.5f + 0.5f * sinf(player->heal_time * 18.0f);
        float g = fminf(1.0f, 1.3f * k) * (0.5f + 0.4f * pulse);
        SDL_SetTextureColorMod(sheet, (Uint8)(255.0f * (1.0f - g)), 255, (Uint8)(255.0f * (1.0f - g * 0.8f)));
    }
}

/* A green light round her while she glows from a heal, added over her. */
static void heal_glow(SDL_Renderer *renderer, const Player *player, float camera_x)
{
    SDL_Texture *glow = assets_texture("sprites/effects/glow");
    if (glow == NULL || player->heal_time <= 0.0f || !player_alive(player))
        return;
    float k = player->heal_time / HEAL_GLOW_TIME;
    int size = (int)(PLAYER_HEAD_HEIGHT * SPRITE_SCALE * (2.6f - 0.6f * k));
    SDL_Rect dst = {(int)lroundf(player->x - camera_x) - size / 2,
                    BASELINE - (int)lroundf(player->jump.height) - PLAYER_HEAD_HEIGHT * SPRITE_SCALE / 2 - size / 2,
                    size, size};
    SDL_SetTextureBlendMode(glow, SDL_BLENDMODE_ADD);
    SDL_SetTextureColorMod(glow, 40, 255, 70);
    SDL_SetTextureAlphaMod(glow, (Uint8)(255.0f * fminf(1.0f, 1.4f * k)));
    SDL_RenderCopy(renderer, glow, NULL, &dst);
    SDL_SetTextureColorMod(glow, 255, 255, 255);
    SDL_SetTextureAlphaMod(glow, 255);
}

static void untint(SDL_Texture *sheet)
{
    SDL_SetTextureColorMod(sheet, 255, 255, 255);
    SDL_SetTextureAlphaMod(sheet, 255);
}

/* Wet: now and then a drop falls off her (whole art px, pale blue). */
static void draw_drips(SDL_Renderer *renderer, const Player *player, float camera_x)
{
    if (player->wet <= 0.0f || !player_alive(player))
        return;
    const int px = SPRITE_SCALE;
    double t = SDL_GetTicks() / 1000.0;
    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
    SDL_SetRenderDrawColor(renderer, 0x9c, 0xcc, 0xe4, (Uint8)lroundf(200.0f * fminf(1.0f, player->wet * 2.0f)));
    for (int i = 0; i < 4; i++) {
        /* Each drop falls from her hair, hands or hem down to the ground, on its own beat. */
        static const int FROM[4][2] = {{-5, 50}, {6, 34}, {-3, 22}, {4, 14}};
        double phase = fmod(t * 1.3 + i * 0.37, 1.0);
        int x = (int)lroundf(player->x - camera_x) + FROM[i][0] * px * player->facing;
        int top = BASELINE - FROM[i][1] * px - (int)lroundf(player->jump.height);
        int y = top + (int)(phase * FROM[i][1] * px) / px * px;
        SDL_Rect r = {x / px * px, y, px, 2 * px};
        SDL_RenderFillRect(renderer, &r);
    }
}

/* Drinking or binding a wound: her own sheet for it (<id>/drink, <id>/bandage,
 * the shoot template). Walking meanwhile, the walk's legs below and it above
 * (for the bandage, down to her thigh). Returns whether it drew her. */
static bool draw_care(SDL_Renderer *renderer, const Player *player, const CharacterSkin *skin, int gun,
                      float camera_x)
{
    int frame;
    const AnimationDef *care = player_care_animation(player, &frame);
    SDL_Texture *sheet = care ? skin_sheet(skin, care->sheet, gun) : NULL;
    if (sheet == NULL)
        return false;
    const AnimationDef *walk_def = player->anim.def;
    bool walking = (player->state == PLAYER_WALK || player->state == PLAYER_RUN) && walk_def != NULL &&
                   walk_def->frame_w == PLAYER_WALK_FRAME_W;
    SDL_Texture *walk = walking ? skin_legs(skin, gun, skin_sheet(skin, walk_def->sheet, gun)) : NULL;
    int split = care->frame_h;
    if (walk) {
        int waist = PLAYER_WAIST_ROW + (care->ground_y - walk_def->ground_y);
        split = player->bandage > 0.0f ? waist + 8 : waist;
        tint(walk, player);
        draw_rows(renderer, walk, walk_def, player->anim.frame, PLAYER_WAIST_ROW, walk_def->frame_h, player, camera_x);
        untint(walk);
    }
    tint(sheet, player);
    draw_rows(renderer, sheet, care, frame, 0, split, player, camera_x);
    untint(sheet);
    if (walk && player->swap_time > 0.0f && skin->swap_far_sheet) { /* Her pistol, whole over the legs */
        tint(skin->swap_far_sheet, player);
        draw_rows(renderer, skin->swap_far_sheet, care, frame, 0, care->frame_h, player, camera_x);
        untint(skin->swap_far_sheet);
    }
    return true;
}

/* Hanging in a trap: up in a net bag, kicking, or yanked up by a foot from a
 * snare's sapling (a quarter turn, then head down: whole turns keep the
 * pixel art true); a blow at the ropes plays her strike. */
static void draw_caught(SDL_Renderer *renderer, const CharacterSkin *skin, int gun, const Player *player,
                        float camera_x)
{
    const AnimationDef *def = player->anim.def;
    int frame = player->anim.frame;
    if (player->catch_shake > 0.0f) {
        def = player_melee_animation(); /* The whole swing, not one frame popping in */
        frame = (int)((1.0f - player->catch_shake / CATCH_SHAKE_TIME) * (float)PLAYER_MELEE_FRAMES);
        frame = frame < PLAYER_MELEE_FRAMES ? frame : PLAYER_MELEE_FRAMES - 1;
    }
    SDL_Texture *sheet = skin_sheet(skin, def->sheet, gun);
    if (sheet == NULL)
        return;
    bool left = player->facing == FACING_LEFT;
    bool snare = player->catch_kind == CATCH_SNARE;
    float t = player->catch_time;
    float x = player->x - camera_x + (float)(hang_sway(t) * SPRITE_SCALE);
    float anchor_x = left ? (float)def->frame_w - def->anchor_x : def->anchor_x;
    float lift = hang_lift(player->catch_kind, t);
    SDL_Rect src = {frame * def->frame_w, 0, def->frame_w, def->frame_h};
    SDL_Rect dst = {(int)lroundf(x - anchor_x * SPRITE_SCALE),
                    BASELINE - def->ground_y * SPRITE_SCALE - (int)lroundf(lift),
                    def->frame_w * SPRITE_SCALE, def->frame_h * SPRITE_SCALE};
    int flip = left ? SDL_FLIP_HORIZONTAL : SDL_FLIP_NONE;
    double angle = 0.0;
    int turn = snare ? hang_turn(t) : 0;
    if (turn == 1) { /* Swung off her feet, sideways */
        angle = left ? 90.0 : -90.0;
        dst.y -= def->frame_h * SPRITE_SCALE / 4;
    } else if (turn == 2) { /* Head down: her feet where her hat was */
        flip |= SDL_FLIP_VERTICAL;
        dst.y = BASELINE - (int)lroundf(lift) - (def->ground_y + 1) * SPRITE_SCALE;
        float foot_y = (float)(dst.y + (def->frame_h - 1 - def->ground_y) * SPRITE_SCALE);
        hang_rope(renderer, player->catch_anchor_x - camera_x, player->catch_anchor_y, x, foot_y);
    }
    tint(sheet, player);
    SDL_RenderCopyEx(renderer, sheet, &src, &dst, angle, NULL, (SDL_RendererFlip)flip);
    untint(sheet);
    if (!snare)
        hang_net(renderer, player->catch_anchor_x - camera_x, player->catch_anchor_y, x,
                 (float)BASELINE - lift + 2.0f * SPRITE_SCALE, t);
}

static void render_at(SDL_Renderer *renderer, const Player *player, const CharacterSkin *skin,
                      const WeaponId *guns, int weapon_slot, float camera_x);

void player_render(SDL_Renderer *renderer, const Player *player, const CharacterSkin *skin,
                   const WeaponId *guns, int weapon_slot, float camera_x)
{
    /* Wading the deep river she is drawn sunk in it, whole art px at a time;
     * its water goes over her after (terrain_render_front). */
    int sunk = player_sunk_rows(player);
    if (sunk == 0) {
        render_at(renderer, player, skin, guns, weapon_slot, camera_x);
        return;
    }
    Player wading = *player;
    wading.jump.height -= (float)(sunk * SPRITE_SCALE);
    render_at(renderer, &wading, skin, guns, weapon_slot, camera_x);
}

static void render_at(SDL_Renderer *renderer, const Player *player, const CharacterSkin *skin,
                      const WeaponId *guns, int weapon_slot, float camera_x)
{
    const AnimationDef *def = player->anim.def;
    if (player->state == PLAYER_SIT && player->sit_gun >= 0)
        weapon_slot = player->sit_gun; /* The gun on her lap, not the one in hand */
    int gun = guns[weapon_slot];
    SDL_Texture *sheet = def ? skin_sheet(skin, def->sheet, gun) : NULL;
    int frame = player->anim.frame;
    if (player->state == PLAYER_IDLE && def && def->frame_w == PLAYER_WALK_FRAME_W && skin_stand(skin, gun)) {
        sheet = skin_stand(skin, gun); /* Stood still: its own pose, if it has one */
        frame = 0;
    }
    if (sheet == NULL && def && player_reload_animation(def)) {
        /* No reload art (a stand-in skin): hold the recoil frame, same template. */
        sheet = skin_sheet(skin, "shoot", gun);
        frame = PLAYER_SHOOT_RELOAD_FRAME;
    }
    if (sheet == NULL && player->fainted) { /* No faint art: the standing frame, dimmed */
        def = NULL;
        sheet = skin_sheet(skin, "walk", gun);
        frame = 0;
    }
    if (sheet == NULL)
        return;
    if (def == NULL) {
        static const AnimationDef STAND = {.frame_w = PLAYER_WALK_FRAME_W, .frame_h = PLAYER_WALK_FRAME_H,
                                           .anchor_x = 19.5f, .ground_y = 61};
        def = &STAND;
    }
    if (player->state == PLAYER_CAUGHT) {
        draw_caught(renderer, skin, gun, player, camera_x);
        return;
    }
    /* A blow with the flashlight on its gun. */
    if (player->state == PLAYER_MELEE && player->light_on && gun >= 0 && gun < WEAPON_COUNT && skin->weapon_melee_lit[gun])
        sheet = skin->weapon_melee_lit[gun];
    /* Two guns take turns; with the flashlight on, its own sheets: it stays up, lit,
     * and the other works beside it. */
    bool lit_duals = false;
    if (player->state == PLAYER_SHOOT && gun >= 0 && gun < WEAPON_COUNT && !shot_reloading(&player->shot)) {
        bool other = player->shot.other_gun && skin->weapon_shoot_other[gun];
        SDL_Texture *lit = other ? skin->weapon_shoot_other_lit[gun] : skin->weapon_shoot_lit[gun];
        if (player->light_on && lit) {
            sheet = lit;
            lit_duals = true;
        } else if (other) {
            sheet = skin->weapon_shoot_other[gun];
        }
    }
    /* Its gun is up already with the light on: no drawing it or putting it away. */
    if (player->state == PLAYER_SHOOT && player->light_on && !lit_duals && player_light_progress(player) >= 1.0f &&
        !shot_reloading(&player->shot) && gun >= 0 && gun < WEAPON_COUNT && skin->weapon_light[gun])
        frame = player_lit_shoot_frame(frame);
    if (player->state == PLAYER_SHOOT && player->shot.piston) /* Two guns: their own, finer sheets */
        frame = player->shot.active ? shot_piston_frame(&player->shot) : frame * PLAYER_PISTON_FRAMES / PLAYER_SHOOT_FRAMES;
    if (player->state == PLAYER_SHOOT && player->power_shot && gun >= 0 && gun < WEAPON_COUNT) { /* Her ricochet */
        SDL_Texture *power = player->light_on ? skin->weapon_power_lit[gun] : skin->weapon_power[gun];
        if (power) {
            sheet = power;
            frame = player->anim.frame;
            lit_duals = true; /* The flashlight, if on, is on this sheet */
        }
    }

    /* The flashlight up: her gun held level with it, on legs that go on walking. */
    int light_frame = 0;
    const AnimationDef *light = player_light_animation(player, &light_frame);
    SDL_Texture *light_sheet = light ? skin_sheet(skin, light->sheet, gun) : NULL;
    if (light_sheet) {
        bool walking = player->state != PLAYER_IDLE && def->frame_w == PLAYER_WALK_FRAME_W;
        SDL_Texture *light_walk = light_frame == PLAYER_LIGHT_FRAMES - 1 && gun >= 0 && gun < WEAPON_COUNT
                                      ? skin->weapon_light_walk[gun] : NULL;
        if (light_walk && (walking || player->state == PLAYER_IDLE)) {
            /* All on: its torso rocking with its legs, or stood there, breathing. */
            int shown = walking ? frame : PLAYER_WALK_FRAMES + player_light_breath(player);
            tint(light_walk, player);
            draw_rows(renderer, light_walk, light, shown, 0, light->frame_h, player, camera_x);
            untint(light_walk);
            heal_glow(renderer, player, camera_x);
            draw_drips(renderer, player, camera_x);
            return;
        }
        int split = light->frame_h;
        if (walking) {
            split = PLAYER_WAIST_ROW + (light->ground_y - def->ground_y);
            SDL_Texture *under = skin_legs(skin, gun, sheet);
            tint(under, player);
            draw_rows(renderer, under, def, frame, PLAYER_WAIST_ROW, def->frame_h, player, camera_x);
            untint(under);
        }
        tint(light_sheet, player);
        draw_rows(renderer, light_sheet, light, light_frame, 0, split, player, camera_x);
        if (walking && player->shot.piston && skin->light_far_sheet) { /* Her other pistol, whole over the legs */
            tint(skin->light_far_sheet, player);
            draw_rows(renderer, skin->light_far_sheet, light, light_frame, 0, light->frame_h, player, camera_x);
            untint(skin->light_far_sheet);
        }
        untint(light_sheet);
        heal_glow(renderer, player, camera_x);
        draw_drips(renderer, player, camera_x);
        return;
    }

    const AnimationDef *legs = player->legs.def;
    SDL_Texture *walk = legs ? skin_legs(skin, gun, skin_sheet(skin, legs->sheet, gun)) : NULL;
    if (player->reload_walk && walk) {
        /* Walking while reloading: the walk's legs below her waist, the
         * reload above it. Every sheet shares the ground row, so the waist is
         * the same height above it in both. */
        int waist = PLAYER_WAIST_ROW + (def->ground_y - legs->ground_y);
        tint(walk, player);
        draw_rows(renderer, walk, legs, player->legs.frame, PLAYER_WAIST_ROW, legs->frame_h, player, camera_x);
        untint(walk);
        tint(sheet, player);
        draw_rows(renderer, sheet, def, frame, 0, waist, player, camera_x);
        untint(sheet);
        heal_glow(renderer, player, camera_x);
        draw_drips(renderer, player, camera_x);
        return;
    }
    if (!draw_care(renderer, player, skin, gun, camera_x)) {
        tint(sheet, player);
        draw_rows(renderer, sheet, def, frame, 0, def->frame_h, player, camera_x);
        untint(sheet);
        if (player->light_on && !lit_duals && player->state == PLAYER_SHOOT && skin->flashlight_sheet &&
            player_light_progress(player) >= PLAYER_LIGHT_CLICK && frame < PLAYER_SHOOT_FRAMES)
            draw_rows(renderer, skin->flashlight_sheet, def, frame, 0, def->frame_h, player, camera_x);
    }
    heal_glow(renderer, player, camera_x);
    draw_drips(renderer, player, camera_x);
}
