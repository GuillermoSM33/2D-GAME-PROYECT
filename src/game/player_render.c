#include "game/player_render.h"

#include <math.h>

#include "config.h"
#include "engine/assets.h"

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
    if (!player_alive(player)) {
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

void player_render(SDL_Renderer *renderer, const Player *player, const CharacterSkin *skin,
                   const WeaponId *guns, int weapon_slot, float camera_x)
{
    const AnimationDef *def = player->anim.def;
    if (player->state == PLAYER_SIT && player->sit_gun >= 0)
        weapon_slot = player->sit_gun; /* The gun on her lap, not the one in hand */
    int gun = guns[weapon_slot];
    SDL_Texture *sheet = def ? skin_sheet(skin, def->sheet, gun) : NULL;
    int frame = player->anim.frame;
    if (sheet == NULL && def && player_reload_animation(def)) {
        /* No reload art (a stand-in skin): hold the recoil frame, same template. */
        sheet = skin_sheet(skin, "shoot", gun);
        frame = PLAYER_SHOOT_RELOAD_FRAME;
    }
    if (sheet == NULL)
        return;

    const AnimationDef *legs = player->legs.def;
    SDL_Texture *walk = legs ? skin_sheet(skin, legs->sheet, gun) : NULL;
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
        return;
    }
    tint(sheet, player);
    draw_rows(renderer, sheet, def, frame, 0, def->frame_h, player, camera_x);
    untint(sheet);
    heal_glow(renderer, player, camera_x);
}
