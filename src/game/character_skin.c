#include "game/character_skin.h"

#include <math.h>
#include <stdio.h>
#include <string.h>

#include "config.h"
#include "engine/assets.h"

#define TEMPLATE_FOLDER "sprites/characters/cowgirl/"
#define MAX_COLORS 96

const char *const SKIN_SHEET_NAMES[SKIN_SHEETS] = {"walk", "jump", "shoot", "sit"};

/* The stand-in: every color of her sheet turned into a shade of the tint by
 * its brightness, so outline, shading and highlights still read. */
static SDL_Texture *tinted_copy(SDL_Renderer *renderer, const char *name, unsigned tint)
{
    const EmbeddedImage *image = assets_find_image(name);
    if (image == NULL)
        return NULL;
    static unsigned pairs[MAX_COLORS][2];
    int count = 0;
    size_t size = (size_t)image->width * (size_t)image->height * 4;
    for (size_t i = 0; i < size && count < MAX_COLORS; i += 4) {
        if (image->rgba[i + 3] == 0)
            continue;
        unsigned rgb = ((unsigned)image->rgba[i] << 16) | ((unsigned)image->rgba[i + 1] << 8) |
                       image->rgba[i + 2];
        int known = 0;
        for (int k = 0; k < count && !known; k++)
            known = pairs[k][0] == rgb;
        if (known)
            continue;
        float lum = 0.299f * image->rgba[i] + 0.587f * image->rgba[i + 1] + 0.114f * image->rgba[i + 2];
        float shade = lum / 150.0f; /* Mid tones at about the tint itself */
        unsigned out = 0;
        for (int c = 2; c >= 0; c--) {
            float v = (float)((tint >> (8 * c)) & 0xFF) * shade;
            out = (out << 8) | (unsigned)fminf(255.0f, roundf(v));
        }
        pairs[count][0] = rgb;
        pairs[count][1] = out;
        count++;
    }
    return assets_texture_recolored(renderer, name, (const unsigned (*)[2])pairs, count);
}

/* sprites/characters/<id>/<sheet>, or NULL. */
static SDL_Texture *own_sheet(const CharacterDef *character, const char *sheet)
{
    char own[96];
    if (sheet == NULL)
        return NULL;
    snprintf(own, sizeof(own), "sprites/characters/%s/%s", character->id, sheet);
    return assets_find_image(own) ? assets_texture(own) : NULL;
}

void skin_load(CharacterSkin *skin, SDL_Renderer *renderer, const CharacterDef *character)
{
    memset(skin, 0, sizeof(*skin));
    skin->character = character;
    for (int s = 0; s < SKIN_SHEETS; s++) {
        char own[96], template_name[96];
        snprintf(own, sizeof(own), "sprites/characters/%s/%s", character->id, SKIN_SHEET_NAMES[s]);
        snprintf(template_name, sizeof(template_name), TEMPLATE_FOLDER "%s", SKIN_SHEET_NAMES[s]);
        if (assets_find_image(own)) {
            skin->sheets[s] = assets_texture(own);
        } else {
            skin->sheets[s] = tinted_copy(renderer, template_name, character->placeholder_tint);
            skin->owned[s] = skin->sheets[s] != NULL;
            skin->placeholder = true;
        }
    }
    if (skin->placeholder)
        return;
    for (int w = 0; w < character->weapon_count; w++) {
        /* Its guns at level 1 and once its power has come. */
        WeaponId guns[2] = {character_weapon(character, w, 1), character_weapon(character, w, POWER_LEVEL)};
        for (int g = 0; g < 2; g++) {
            const WeaponDef *def = weapon_def(guns[g]);
            skin->weapon_shoot[guns[g]] = own_sheet(character, def->shoot_sheet);
            skin->weapon_walk[guns[g]] = own_sheet(character, def->walk_sheet);
            skin->weapon_jump[guns[g]] = own_sheet(character, def->jump_sheet);
            skin->weapon_stand[guns[g]] = own_sheet(character, def->stand_sheet);
            skin->weapon_legs[guns[g]] = own_sheet(character, def->legs_sheet);
            skin->weapon_power[guns[g]] = own_sheet(character, def->power_sheet);
            skin->weapon_power_lit[guns[g]] = own_sheet(character, def->power_lit_sheet);
            skin->weapon_shoot_other[guns[g]] = own_sheet(character, def->shoot_other_sheet);
            skin->weapon_shoot_lit[guns[g]] = own_sheet(character, def->shoot_lit_sheet);
            skin->weapon_shoot_other_lit[guns[g]] = own_sheet(character, def->shoot_other_lit_sheet);
            skin->weapon_reload[guns[g]] = own_sheet(character, def->reload_sheet);
            skin->weapon_sit[guns[g]] = own_sheet(character, def->sit_sheet);
            skin->weapon_melee[guns[g]] = own_sheet(character, def->melee_sheet);
            skin->weapon_melee_lit[guns[g]] = own_sheet(character, def->melee_lit_sheet);
            skin->weapon_light[guns[g]] = own_sheet(character, def->light_sheet);
            skin->weapon_light_walk[guns[g]] = own_sheet(character, def->light_walk_sheet);
        }
    }
    skin->stand_sheet = own_sheet(character, "stand");
    skin->legs_sheet = own_sheet(character, "legs");
    skin->swap_far_sheet = own_sheet(character, "swap_far");
    skin->light_far_sheet = own_sheet(character, "light_dual_far");
    skin->throw_sheet = own_sheet(character, "throw");
    skin->melee_sheet = own_sheet(character, "melee");
    skin->flashlight_sheet = own_sheet(character, "flashlight");
    skin->faint_sheet = own_sheet(character, "faint");
    skin->drink_sheet = own_sheet(character, "drink");
    skin->bandage_sheet = own_sheet(character, "bandage");
    skin->plant_sheet = own_sheet(character, "plant");
    skin->swap_sheet = own_sheet(character, "swap");
    skin->swap_lit_sheet = own_sheet(character, "swap_lit");
}

void skin_free(CharacterSkin *skin)
{
    for (int s = 0; s < SKIN_SHEETS; s++) {
        if (skin->owned[s] && skin->sheets[s])
            SDL_DestroyTexture(skin->sheets[s]);
    }
    memset(skin, 0, sizeof(*skin));
}

SDL_Texture *skin_stand(const CharacterSkin *skin, int gun)
{
    if (gun >= 0 && gun < WEAPON_COUNT && skin->weapon_stand[gun])
        return skin->weapon_stand[gun];
    return skin->stand_sheet;
}

SDL_Texture *skin_legs(const CharacterSkin *skin, int gun, SDL_Texture *walk)
{
    if (gun >= 0 && gun < WEAPON_COUNT && skin->weapon_legs[gun])
        return skin->weapon_legs[gun];
    return skin->legs_sheet ? skin->legs_sheet : walk;
}

SDL_Texture *skin_sheet(const CharacterSkin *skin, const char *template_sheet, int gun)
{
    const char *file = strrchr(template_sheet, '/');
    file = file ? file + 1 : template_sheet;
    bool known = gun >= 0 && gun < WEAPON_COUNT;
    if (strcmp(file, "shoot") == 0 && known && skin->weapon_shoot[gun])
        return skin->weapon_shoot[gun];
    if (strcmp(file, "walk") == 0 && known && skin->weapon_walk[gun])
        return skin->weapon_walk[gun];
    if (strcmp(file, "jump") == 0 && known && skin->weapon_jump[gun])
        return skin->weapon_jump[gun];
    if (strcmp(file, "sit") == 0 && known && skin->weapon_sit[gun])
        return skin->weapon_sit[gun];
    if (strcmp(file, "reload") == 0)
        return known ? skin->weapon_reload[gun] : NULL;
    if (strcmp(file, "light") == 0)
        return known ? skin->weapon_light[gun] : NULL;
    if (strcmp(file, "throw") == 0)
        return skin->throw_sheet;
    if (strcmp(file, "faint") == 0)
        return skin->faint_sheet;
    if (strcmp(file, "drink") == 0)
        return skin->drink_sheet;
    if (strcmp(file, "bandage") == 0)
        return skin->bandage_sheet;
    if (strcmp(file, "swap_lit") == 0)
        return skin->swap_lit_sheet;
    if (strcmp(file, "swap") == 0)
        return skin->swap_sheet;
    if (strcmp(file, "plant") == 0)
        return skin->plant_sheet;
    if (strcmp(file, "melee") == 0) {
        if (known && skin->weapon_melee[gun])
            return skin->weapon_melee[gun];
        if (skin->melee_sheet)
            return skin->melee_sheet;
        file = "shoot"; /* No blow of its own: its shoot sheet's first frames */
        if (known && skin->weapon_shoot[gun])
            return skin->weapon_shoot[gun];
    }
    for (int s = 0; s < SKIN_SHEETS; s++) {
        if (strcmp(file, SKIN_SHEET_NAMES[s]) == 0)
            return skin->sheets[s];
    }
    return NULL;
}
