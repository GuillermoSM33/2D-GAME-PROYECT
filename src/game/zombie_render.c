#include "game/zombie_render.h"

#include <math.h>
#include <string.h>

#include "config.h"
#include "engine/assets.h"
#include "game/hang_render.h"
#include "game/health_bar.h"

#define BAR_W 64
#define BAR_H 6
#define BAR_GAP 14 /* Window px between the helmet and the bar */

SDL_Texture *zombie_animation_texture(const AnimationDef *animation, int *frame)
{
    if (!animation || !frame)
        return NULL;
    SDL_Texture *sheet = assets_texture(animation->sheet);
    if (!sheet) {
        const char *action = strrchr(animation->sheet, '/');
        action = action ? action + 1 : animation->sheet;
        const char *fallback = strcmp(action, "death") == 0 ? "sprites/zombies/riot/death" :
                               strcmp(action, "attack") == 0 ? "sprites/zombies/riot/attack" :
                               strcmp(action, "hurt") == 0 || strcmp(action, "caught") == 0
                                   ? "sprites/zombies/riot/hurt" : "sprites/zombies/riot/walk";
        sheet = assets_texture(fallback);
    }
    if (sheet) {
        int width = 0;
        SDL_QueryTexture(sheet, NULL, NULL, &width, NULL);
        int count = animation->frame_w > 0 ? width / animation->frame_w : 0;
        if (count > 0)
            *frame = *frame < 0 ? 0 : *frame >= count ? count - 1 : *frame;
    }
    return sheet;
}

static void draw_health_bar(SDL_Renderer *renderer, const Zombie *zombie, float camera_x)
{
    int x = (int)lroundf(zombie->x - camera_x) - BAR_W / 2;
    int y = BASELINE - (int)zombie_body_height(zombie) - BAR_GAP;
    health_bar_draw(renderer, x, y, BAR_W, BAR_H, zombie->health, zombie->max_health,
                    zombie->armor > 0.0f);
}

void zombie_render(SDL_Renderer *renderer, const Zombie *zombie, float camera_x)
{
    const AnimationDef *def = zombie->anim.def;
    int frame = zombie->anim.frame;
    SDL_Texture *sheet = zombie_animation_texture(def, &frame);
    float opacity = zombie_opacity(zombie);
    if (sheet == NULL || opacity <= 0.0f || zombie->hidden)
        return;

    bool left = zombie->facing < 0;
    float anchor_x = left ? (float)def->frame_w - def->anchor_x : def->anchor_x;
    SDL_Rect src = {frame * def->frame_w, 0, def->frame_w, def->frame_h};
    SDL_Rect dst = {
        (int)lroundf(zombie->x - camera_x - anchor_x * SPRITE_SCALE) + zombie_shudder(zombie) * SPRITE_SCALE,
        BASELINE - def->ground_y * SPRITE_SCALE - zombie_breath(zombie) * SPRITE_SCALE +
            (int)lroundf(zombie->depth * RIVER_DEEP_ROWS) * SPRITE_SCALE, /* Wading deep: sunk */
        def->frame_w * SPRITE_SCALE,
        def->frame_h * SPRITE_SCALE,
    };
    int flip = left ? SDL_FLIP_HORIZONTAL : SDL_FLIP_NONE;
    double angle = 0.0;
    bool hanging = zombie->caught > 0.0f && zombie->catch_kind != CATCH_NONE && zombie_alive(zombie);
    float lift = hanging ? hang_lift(zombie->catch_kind, zombie->catch_time) : 0.0f;
    if (hanging) { /* Up in a net, or head down from a snare like her */
        dst.x += hang_sway(zombie->catch_time) * SPRITE_SCALE;
        dst.y -= (int)lroundf(lift);
        int turn = zombie->catch_kind == CATCH_SNARE ? hang_turn(zombie->catch_time) : 0;
        if (turn == 1) /* Yanked off its feet: a quarter turn first */
            angle = left ? 90.0 : -90.0;
        if (turn == 2) {
            flip |= SDL_FLIP_VERTICAL;
            dst.y = BASELINE - (int)lroundf(lift) - (def->ground_y + 1) * SPRITE_SCALE;
            hang_rope(renderer, zombie->catch_anchor_x - camera_x, zombie->catch_anchor_y,
                      (float)(dst.x + (int)lroundf(anchor_x * SPRITE_SCALE)),
                      (float)(dst.y + (def->frame_h - 1 - def->ground_y) * SPRITE_SCALE));
        }
    }
    unsigned tint = zombie->stats ? zombie->stats->tint : 0xffffff;
    SDL_SetTextureColorMod(sheet, (Uint8)(tint >> 16), (Uint8)(tint >> 8), (Uint8)tint);
    SDL_SetTextureAlphaMod(sheet, (Uint8)lroundf(opacity * 255.0f));
    SDL_RenderCopyEx(renderer, sheet, &src, &dst, angle, NULL, (SDL_RendererFlip)flip);
    SDL_SetTextureAlphaMod(sheet, 255);
    SDL_SetTextureColorMod(sheet, 255, 255, 255);
    if (hanging && zombie->catch_kind == CATCH_NET)
        hang_net(renderer, (float)(dst.x + (int)lroundf(anchor_x * SPRITE_SCALE)),
                 (float)BASELINE - lift + 2.0f * SPRITE_SCALE, zombie->catch_time);

    if (zombie_alive(zombie) && zombie->health < zombie->max_health)
        draw_health_bar(renderer, zombie, camera_x);
}
