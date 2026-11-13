#include <limits.h>
#include <stdio.h>
#include <string.h>

#include "app/verify.h"
#include "config.h"
#include "engine/assets.h"
#include "engine/pixfont.h"
#include "game/character_skin.h"
#include "game/casefile.h"
#include "game/player.h"
#include "game/props.h"
#include "game/hud.h"
#include "game/ui.h"
#include "game/stage_run.h"

static bool verify_sheet(const AnimationDef *def)
{
    const EmbeddedImage *image = assets_find_image(def->sheet);
    int needed_w = (def->first_frame + def->frame_count) * def->frame_w;
    if (image == NULL) {
        fprintf(stderr, "FALTA: %s\n", def->sheet);
        return false;
    }
    if (image->width % def->frame_w != 0 || image->width < needed_w ||
        image->height != def->frame_h) {
        fprintf(stderr, "TAMAÑO INCORRECTO: %s es %dx%d; con cuadros de %dx%d "
                "el ancho debe ser múltiplo de %d (mínimo %d) y el alto %d\n",
                def->sheet, image->width, image->height, def->frame_w, def->frame_h,
                def->frame_w, needed_w, def->frame_h);
        return false;
    }
    return true;
}

static bool verify_image(const char *name, int width, int height);

/* Characters other than the cowgirl may still be on the stand-in (her art,
 * tinted). Once one has any sheet of its own, it needs all of them, each the
 * same size as hers, so the shared template (pivots, muzzle) still fits. */
static int verify_characters(void)
{
    int failures = 0;
    for (int c = 0; c < CHARACTER_COUNT; c++) {
        int own = 0;
        char names[SKIN_SHEETS][96];
        for (int s = 0; s < SKIN_SHEETS; s++) {
            snprintf(names[s], sizeof(names[s]), "sprites/characters/%s/%s", CHARACTERS[c].id,
                     SKIN_SHEET_NAMES[s]);
            own += assets_find_image(names[s]) != NULL;
        }
        if (own == 0) {
            printf("  %-22s arte provisional (la vaquera teñida)\n", CHARACTERS[c].name);
            continue;
        }
        for (int s = 0; s < SKIN_SHEETS; s++) {
            char template_name[96];
            snprintf(template_name, sizeof(template_name), "sprites/characters/cowgirl/%s",
                     SKIN_SHEET_NAMES[s]);
            const EmbeddedImage *ref = assets_find_image(template_name);
            failures += !verify_image(names[s], ref->width, ref->height);
        }
        /* A gun's own shoot and reload sheets are needed, the size of shoot.png... */
        const EmbeddedImage *shoot = assets_find_image("sprites/characters/cowgirl/shoot");
        /* Its guns, and the one its power gives it. */
        WeaponId guns[CHARACTER_MAX_WEAPONS + 1];
        int gun_count = 0;
        for (int w = 0; w < CHARACTERS[c].weapon_count; w++)
            guns[gun_count++] = CHARACTERS[c].weapons[w];
        if (CHARACTERS[c].power == POWER_DUAL_PISTOLS)
            guns[gun_count++] = CHARACTERS[c].power_weapon;
        for (int w = 0; w < gun_count; w++) { /* Its blow with each gun */
            const WeaponDef *def = weapon_def(guns[w]);
            char name[96];
            snprintf(name, sizeof(name), "sprites/characters/%s/%s", CHARACTERS[c].id,
                     def->melee_sheet ? def->melee_sheet : "melee");
            failures += !verify_image(name, PLAYER_MELEE_FRAMES * PLAYER_SHOOT_FRAME_W, shoot->height);
            if (def->light_sheet) {
                snprintf(name, sizeof(name), "sprites/characters/%s/%s", CHARACTERS[c].id, def->light_sheet);
                failures += !verify_image(name, PLAYER_LIGHT_FRAMES * PLAYER_SHOOT_FRAME_W, shoot->height);
                snprintf(name, sizeof(name), "sprites/characters/%s/%s", CHARACTERS[c].id, def->light_walk_sheet);
                failures += !verify_image(name, (PLAYER_WALK_FRAMES + PLAYER_LIGHT_BREATHS) * PLAYER_SHOOT_FRAME_W, shoot->height);
            }
        }
        {
            char name[96]; /* Its faint (tools/make_faint.py), its drink and bandage */
            snprintf(name, sizeof(name), "sprites/characters/%s/faint", CHARACTERS[c].id);
            failures += !verify_image(name, PLAYER_FAINT_FRAMES * PLAYER_FAINT_FRAME_W, PLAYER_WALK_FRAME_H);
            if (CHARACTERS[c].power == POWER_DUAL_PISTOLS) { /* Its second pistol, out and away */
                snprintf(name, sizeof(name), "sprites/characters/%s/swap", CHARACTERS[c].id);
                failures += !verify_image(name, PLAYER_SWAP_FRAMES * PLAYER_SHOOT_FRAME_W, shoot->height);
                snprintf(name, sizeof(name), "sprites/characters/%s/shoot_dual_b", CHARACTERS[c].id);
                failures += !verify_image(name, PLAYER_PISTON_FRAMES * PLAYER_SHOOT_FRAME_W, shoot->height);
                const char *ricochets[] = {"ricochet", "ricochet_lit", "ricochet_dual", "ricochet_dual_lit"};
                for (int k = 0; k < 4; k++) {
                    snprintf(name, sizeof(name), "sprites/characters/%s/%s", CHARACTERS[c].id, ricochets[k]);
                    failures += !verify_image(name, PLAYER_SHOOT_FRAMES * PLAYER_SHOOT_FRAME_W, shoot->height);
                }
                snprintf(name, sizeof(name), "sprites/characters/%s/stand_dual", CHARACTERS[c].id);
                failures += !verify_image(name, PLAYER_WALK_FRAME_W, PLAYER_WALK_FRAME_H);
                snprintf(name, sizeof(name), "sprites/characters/%s/stand", CHARACTERS[c].id);
                failures += !verify_image(name, PLAYER_WALK_FRAME_W, PLAYER_WALK_FRAME_H);
                snprintf(name, sizeof(name), "sprites/characters/%s/swap_lit", CHARACTERS[c].id);
                failures += !verify_image(name, PLAYER_SWAP_FRAMES * PLAYER_SHOOT_FRAME_W, shoot->height);
            }
            const char *care[] = {"drink", "bandage", "plant"};
            for (int k = 0; k < 3; k++) {
                snprintf(name, sizeof(name), "sprites/characters/%s/%s", CHARACTERS[c].id, care[k]);
                failures += !verify_image(name, PLAYER_CARE_FRAMES * PLAYER_SHOOT_FRAME_W, shoot->height);
            }
        }
        if (CHARACTERS[c].power == POWER_GRENADES) { /* Its throw, on the shoot template */
            char name[96];
            snprintf(name, sizeof(name), "sprites/characters/%s/throw", CHARACTERS[c].id);
            failures += !verify_image(name, PLAYER_THROW_FRAMES * PLAYER_SHOOT_FRAME_W, shoot->height);
        }
        for (int w = 0; w < gun_count; w++) {
            const WeaponDef *def = weapon_def(guns[w]);
            const char *sheets[] = {def->shoot_sheet, def->reload_sheet, def->reload_other_sheet,
                                    def->reload_lower_sheet, def->reload_other_lower_sheet};
            for (int k = 0; k < 5; k++) {
                char name[96];
                if (sheets[k] == NULL)
                    continue;
                snprintf(name, sizeof(name), "sprites/characters/%s/%s", CHARACTERS[c].id, sheets[k]);
                int frames = !def->piston ? PLAYER_SHOOT_FRAMES : k == 0 ? PLAYER_PISTON_FRAMES : PLAYER_DUAL_RELOAD_SHEET_FRAMES;
                failures += !verify_image(name, frames * PLAYER_SHOOT_FRAME_W, shoot->height);
            }
            if (def->sit_sheet) { /* ...and its sit sheet, the size of sit.png */
                const EmbeddedImage *sit = assets_find_image("sprites/characters/cowgirl/sit");
                char name[96];
                snprintf(name, sizeof(name), "sprites/characters/%s/%s", CHARACTERS[c].id, def->sit_sheet);
                failures += !verify_image(name, sit->width, sit->height);
            }
        }
    }
    return failures;
}

/* An embedded image with exactly this size. */
static bool verify_image(const char *name, int width, int height)
{
    const EmbeddedImage *image = assets_find_image(name);
    if (image == NULL) {
        fprintf(stderr, "FALTA: %s\n", name);
        return false;
    }
    if (image->width != width || image->height != height) {
        fprintf(stderr, "TAMAÑO INCORRECTO: %s es %dx%d; debe ser %dx%d\n", name,
                image->width, image->height, width, height);
        return false;
    }
    return true;
}

int app_verify_assets(void)
{
    const AnimationDef *anims[ZOMBIE_KIND_COUNT * ZOMBIE_ANIM_COUNT + 64];
    int player_count;
    const AnimationDef *const *player_anims = player_animations(&player_count);
    int anim_count = 0;
    for (int i = 0; i < player_count; i++)
        anims[anim_count++] = player_anims[i];
    anims[anim_count++] = bullet_animation();
    int zombie_count;
    const AnimationDef *const *zombie_anims = zombie_animations(&zombie_count);
    for (int i = 0; i < zombie_count; i++)
        anims[anim_count++] = zombie_anims[i];
    anims[anim_count++] = effect_sparks();
    anims[anim_count++] = chest_animation();
    anims[anim_count++] = chest_sparks();
    anims[anim_count++] = terrain_explosion();
    anims[anim_count++] = terrain_heal_effect();

    int failures = 0;
    for (int i = 0; i < anim_count; i++)
        failures += !verify_sheet(anims[i]);
    for (int s = 0; s < STAGE_COUNT; s++) {
        for (int i = 0; i < BACKGROUND_LAYER_COUNT; i++) {
            const BackgroundLayer *layer = &BACKGROUND_LAYERS[i];
            char name[96];
            snprintf(name, sizeof(name), "backgrounds/%s/%s", STAGES[s].theme->name, layer->file);
            failures += !verify_image(name, layer->width, layer->height);
        }
        if (STAGES[s].theme->fog) {
            char name[96];
            snprintf(name, sizeof(name), "backgrounds/%s/%s", STAGES[s].theme->name, FOG_LAYER.file);
            failures += !verify_image(name, FOG_LAYER.width, FOG_LAYER.height);
        }
    }
    for (int k = 0; k < PROP_KIND_COUNT; k++) {
        const PropDef *def = prop_def(k);
        failures += !verify_image(def->sheet, def->frame_w * def->variants, def->frame_h);
    }
    for (int k = 0; k < TERRAIN_KINDS; k++) {
        int w, h, frames;
        terrain_frame_size(k, &w, &h, &frames);
        failures += !verify_image(terrain_sheet(k), frames * w, h);
    }
    failures += !verify_image(terrain_charge_sheet(), 2 * CHARGE_FRAME_W, CHARGE_FRAME_H);
    failures += !verify_image(terrain_ruins_sheet(), WALL_RUINS_W, WALL_RUINS_H);
    failures += !verify_image(terrain_facade_sheet(), FACADE_KINDS * FACADE_W, FACADE_H);
    failures += !verify_image(terrain_city_front_sheet(), FACADE_URBAN * CITY_FRONT_W, CITY_FRONT_H);
    failures += !verify_image(terrain_car_wreck_sheet(), 3 * VEHICLE_LOOKS * CAR_WRECK_W, CAR_WRECK_H);
    failures += !verify_image(terrain_supply_truck_sheet(), 2 * VEHICLE_FRAME_W, VEHICLE_FRAME_H);
    failures += !verify_image("sprites/effects/flare", FLARE_FRAMES * FLARE_FRAME_W, FLARE_FRAME_H);
    failures += !verify_image("sprites/effects/paper", 4 * TUMBLE_FRAME, TUMBLE_FRAME);
    failures += !verify_image("sprites/effects/hydrant_jet", 4 * JET_FRAME_W, JET_FRAME_H);
    failures += !verify_image(terrain_door_sheet(), 3 * 3 * DOOR_FRAME_W, DOOR_FRAME_H); /* Planks, shutter, coupling */
    failures += !verify_image(terrain_train_sheet(), TRAIN_W, TRAIN_H);
    failures += !verify_image("sprites/sparrow/sparrow", CROW_FRAMES * CROW_FRAME_W, CROW_FRAME_H);
    failures += !verify_image("sprites/weapons/grenade", 4 * GRENADE_FRAME, GRENADE_FRAME);
    failures += !verify_image("sprites/effects/blood", 4 * 8, 4);
    failures += !verify_image("sprites/terrain/wire", 3 * WIRE_FRAME_W, WIRE_FRAME_H);
    failures += !verify_image("sprites/terrain/net", 3 * NET_FRAME_W, NET_FRAME_H);
    failures += !verify_image("sprites/terrain/snare", 3 * SNARE_FRAME_W, SNARE_FRAME_H);
    failures += !verify_image("sprites/terrain/spikes", 3 * SPIKES_FRAME_W, SPIKES_FRAME_H);
    failures += !verify_image("sprites/effects/net_bag", 4 * NET_BAG_W, NET_BAG_H);
    failures += !verify_image("sprites/crow/crow", CROW_FRAMES * CROW_FRAME_W, CROW_FRAME_H);
    failures += !verify_image("sprites/bat/bat", BAT_FRAMES * BAT_FRAME_W, BAT_FRAME_H);
    failures += !verify_image("sprites/terrain/river", 4 * RIVER_FRAME_W, RIVER_FRAME_H);
    failures += !verify_image("sprites/terrain/river_front", 4 * RIVER_FRAME_W, RIVER_FRONT_H);
    failures += !verify_image("sprites/terrain/puddle", 4 * PUDDLE_FRAME_W, PUDDLE_FRAME_H);
    failures += !verify_image("sprites/terrain/sign", SIGN_FRAME_W, SIGN_FRAME_H);
    failures += !verify_image("sprites/effects/splash", SPLASH_FRAMES * SPLASH_FRAME_W, SPLASH_FRAME_H);
    failures += !verify_image("sprites/effects/tumbleweed", 4 * TUMBLE_FRAME, TUMBLE_FRAME);
    failures += !verify_image("sprites/terrain/barricade", 3 * BARRICADE_SHEET_KINDS * BARRICADE_FRAME_W,
                              BARRICADE_FRAME_H);
    failures += !verify_image("sprites/props/houses", HOUSE_FRAMES * HOUSE_FRAME_W, HOUSE_FRAME_H);
    failures += !verify_image("sprites/effects/glow", GLOW_SIZE, GLOW_SIZE);
    const char *badges[] = {"sprites/ui/badge_player", "sprites/ui/badge_zombie"};
    for (size_t i = 0; i < sizeof(badges) / sizeof(badges[0]); i++)
        failures += !verify_image(badges[i], BADGE_W, BADGE_H);
    /* The interface kit (tools/make_ui.py) and its font. */
    const struct {
        const char *name;
        int w, h;
    } kit[] = {
        {"sprites/ui/panel", 24, 24}, {"sprites/ui/button", 32, 16}, {"sprites/ui/key", 14, 14},
        {"sprites/ui/pip", 12, 10}, {"sprites/ui/bar", 12, 8},
        {"sprites/ui/notice_dev", UI_NOTICE_W, UI_NOTICE_H},
        {"sprites/ui/icons", ICON_COUNT * UI_ICON_SIZE, UI_ICON_SIZE},
        {"sprites/ui/icons_hd", ICON_COUNT * UI_ICON_HD_SIZE, UI_ICON_HD_SIZE},
        {"sprites/ui/weapons", (WEAPON_COUNT + 1) * UI_WEAPON_W, UI_WEAPON_H}, {"sprites/ui/weapons_hd", (WEAPON_COUNT + 1) * UI_WEAPON_W * 2, UI_WEAPON_H * 2}, /* + the grenade */
        {"sprites/clues/clues", CLUE_COUNT * 24, 24}, {"sprites/clues/stamp", 81, 40},
        {"sprites/vial/held", 64, 100},
        {"sprites/mercenary/walk", 12 * PLAYER_SHOOT_FRAME_W, PLAYER_SHOOT_FRAME_H},
        {"sprites/mercenary/aim", 4 * 110, 130},
        {"sprites/ambulance/drive", 4 * 72, 34},
    };
    for (size_t i = 0; i < sizeof(kit) / sizeof(kit[0]); i++)
        failures += !verify_image(kit[i].name, kit[i].w, kit[i].h);
    if (!pixfont_init()) {
        fprintf(stderr, "FALTA o INCOMPLETA: sprites/ui/font (corre tools/make_ui.py)\n");
        failures++;
    }
    if (!hud_verify_layout()) {
        fprintf(stderr, "HUD: elementos fuera de sus límites o texto sin espacio.\n");
        failures++;
    }
    failures += verify_characters();
    if (assets_find_blob(MENU_MUSIC_CITY) == NULL) {
        fprintf(stderr, "FALTA: %s\n", MENU_MUSIC_CITY);
        failures++;
    }
    if (assets_find_blob(MENU_MUSIC) == NULL) {
        fprintf(stderr, "FALTA: %s\n", MENU_MUSIC);
        failures++;
    }
    for (int s = 0; s < STAGE_COUNT; s++)
        if (assets_find_blob(STAGES[s].music) == NULL) {
            fprintf(stderr, "FALTA: %s\n", STAGES[s].music);
            failures++;
        }
    const char *blobs[] = {"fonts/DejaVuSansMono", "fonts/DejaVuSansMono-Bold",
                           "sounds/player/shot", "sounds/player/reload", "sounds/zombie/spawn",
                           "sounds/zombie/idle", "sounds/zombie/death", "sounds/world/explosion",
                           "sounds/world/supply", "sounds/world/fuse",
                           "sounds/world/glass", "sounds/world/wood", "sounds/world/snap",
                           "sounds/player/drink", "sounds/crow/caw", "sounds/crow/death",
                           "sounds/sparrow/chirp", "sounds/sparrow/death", "sounds/world/siren",
                           "sounds/world/horde", "sounds/world/flare", "sounds/world/city", "sounds/world/hydrant",
                           "sounds/dog/spawn", "sounds/dog/idle", "sounds/dog/death",
                           "sounds/player/hurt", "sounds/player/jump", "sounds/player/land",
                           "sounds/player/death", "sounds/player/bandage", "sounds/player/faint",
                           "sounds/effects/hit_flesh", "sounds/effects/hit_armor",
                           "sounds/world/hit_wood", "sounds/world/hit_metal", "sounds/world/hit_stone",
                           "sounds/world/hit_wire", "sounds/world/hit_sand", "sounds/world/wire",
                           "sounds/world/rope", "sounds/world/trap_escape", "sounds/world/ambush",
                           "sounds/world/grenade_explosion", "sounds/world/dynamite_explosion",
                           "sounds/world/footstep", "sounds/world/footstep_2", "sounds/world/footstep_3",
                           "sounds/world/footstep_4", "sounds/world/run_step", "sounds/world/run_step_2",
                           "sounds/world/run_step_3", "sounds/world/run_step_4",
                           "sounds/world/footstep_water", "sounds/world/footstep_water_2",
                           "sounds/world/footstep_water_3", "sounds/world/footstep_water_4",
                           "sounds/world/run_step_water", "sounds/world/run_step_water_2",
                           "sounds/world/run_step_water_3", "sounds/world/run_step_water_4",
                           "sounds/world/sit",
                           "sounds/world/stand", "sounds/world/chest", "sounds/world/level_up",
                           "sounds/world/victory", "sounds/weather/wind", "sounds/weather/rain",
                           "sounds/weather/thunder", "sounds/ui/move", "sounds/ui/confirm",
                           "sounds/ui/back", "sounds/weapons/switch", "sounds/weapons/grenade_throw",
                           "sounds/weapons/ricochet", "sounds/weapons/fire_mode",
                           "sounds/player/flashlight_on", "sounds/player/flashlight_off",
                           "sounds/world/grenade_bounce", "sounds/world/splash",
                           "sounds/bat/flee", "sounds/bat/death", "sounds/bat/chirp",
                           "sounds/ui/book_open", "sounds/ui/book_close", "sounds/ui/book_page",
                           "sounds/weather/lightning_warn", "sounds/world/river", "sounds/world/fire"};
    for (size_t i = 0; i < sizeof(blobs) / sizeof(blobs[0]); i++) {
        if (assets_find_blob(blobs[i]) == NULL) {
            fprintf(stderr, "FALTA: %s\n", blobs[i]);
            failures++;
        }
    }
    for (int id = 0; id < WEAPON_COUNT; id++) {
        const WeaponDef *w = weapon_def((WeaponId)id);
        const char *paths[] = {w->shot_sound, w->cycle_sound, w->reload_sound,
                              w->empty_sound, w->melee_sound};
        for (size_t s = 0; s < sizeof(paths) / sizeof(paths[0]); s++) {
            if (!paths[s])
                continue;
            char name[128];
            snprintf(name, sizeof(name), "sounds/%s", paths[s]);
            if (!assets_find_blob(name)) {
                fprintf(stderr, "FALTA: %s (%s)\n", name, w->name);
                failures++;
            }
        }
    }
    if (failures)
        return 1;
    printf("OK: %d imagen(es) y %d fuente(s)/sonido(s) incrustados.\n",
           embedded_image_count, embedded_blob_count);
    for (int i = 0; i < anim_count; i++) {
        const AnimationDef *def = anims[i];
        printf("  %-22s frames %d-%d de %d × %d px\n", def->sheet, def->first_frame,
               def->first_frame + def->frame_count - 1, def->frame_w, def->frame_h);
    }
    printf("Escala: %d×\n", SPRITE_SCALE);
    return 0;
}
