#include "game/player_render.h"

#include <math.h>

#include "config.h"
#include "engine/assets.h"

void player_render(SDL_Renderer *renderer, const Player *player, const CharacterSkin *skin,
                   float camera_x)
{
    const AnimationDef *def = player->anim.def;
    SDL_Texture *sheet = def ? skin_sheet(skin, def->sheet) : NULL;
    if (sheet == NULL)
        return;

    bool left = player->facing == FACING_LEFT;
    /* Mirroring flips the pivot to the other side of the frame. */
    float anchor_x = left ? (float)def->frame_w - def->anchor_x : def->anchor_x;
    SDL_Rect src = {player->anim.frame * def->frame_w, 0, def->frame_w, def->frame_h};
    SDL_Rect dst = {
        (int)lroundf(player->x - camera_x - anchor_x * SPRITE_SCALE),
        BASELINE - def->ground_y * SPRITE_SCALE - (int)lroundf(player->jump.height),
        def->frame_w * SPRITE_SCALE,
        def->frame_h * SPRITE_SCALE,
    };
    /* After a hit she blinks red; with no death sheet yet, a dead player is
     * the standing frame, dimmed. */
    bool blink_on = fmodf(player->hurt_time, 2.0f * PLAYER_BLINK_PERIOD) > PLAYER_BLINK_PERIOD;
    if (!player_alive(player)) {
        SDL_SetTextureColorMod(sheet, 140, 90, 90);
        SDL_SetTextureAlphaMod(sheet, 170);
    } else if (player->hurt_time > 0.0f && blink_on) {
        SDL_SetTextureColorMod(sheet, 255, 90, 80);
    }
    /* Left-facing frames are the right-facing art mirrored. */
    SDL_RenderCopyEx(renderer, sheet, &src, &dst, 0.0, NULL,
                     left ? SDL_FLIP_HORIZONTAL : SDL_FLIP_NONE);
    SDL_SetTextureColorMod(sheet, 255, 255, 255);
    SDL_SetTextureAlphaMod(sheet, 255);
}
