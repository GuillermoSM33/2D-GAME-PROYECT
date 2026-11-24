#ifndef APP_STAGE_H
#define APP_STAGE_H

#include "app/options.h"
#include "app/state.h"

/* Application orchestration: pure rules in game/, effects through engine/. */
const WeaponDef *stage_weapon(const StagePlay *play);
bool stage_single_fire(const StagePlay *play);
void stage_start(StagePlay *play, int index, const CharacterDef *character, const Progress *progress);
void stage_start_profile(StagePlay *play, int index, const CharacterDef *character, Profile *profile);
void stage_fire_weapon(StagePlay *play, const Progress *progress);
void stage_swap_weapon(StagePlay *play);
void stage_refresh_weapons(StagePlay *play, int level);
bool stage_can_swap_duals(const StagePlay *play, const Progress *progress);
typedef enum {
    STAGE_ITEM_SUIT, STAGE_ITEM_WEAPON, STAGE_ITEM_WATER, STAGE_ITEM_DYNAMITE,
    STAGE_ITEM_GOLD, STAGE_ITEM_TABLET, STAGE_ITEM_PARTS
} StageInventoryKind;
typedef struct {
    StageInventoryKind kind;
    int slot; /* A weapon slot, or -1 for the sheriff's holstered second gun. */
    const char *action, *detail;
    bool enabled;
} StageInventoryChoice;
int stage_inventory_rows(const StagePlay *play, const Progress *progress);
StageInventoryChoice stage_inventory_choice(const StagePlay *play, const Progress *progress);
void stage_drop_unearned(StagePlay *play, Profile *profile);
void stage_pause(StagePlay *play);
bool stage_step(StagePlay *play, const InputState *input, Profile *profile, AppOptions *options);
void play_zombie_voice(Zombie *zombie);

#endif
