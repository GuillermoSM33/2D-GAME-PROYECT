#ifndef GAME_COMBAT_H
#define GAME_COMBAT_H

#include "game/bullet.h"
#include "game/effects.h"
#include "game/player.h"
#include "game/zombie.h"

/* Bullets that reach a living zombie stop there and deal damage. Each one
 * sparks on the armor (the recoil and death sheets draw their own). Returns
 * how many hit. */
int combat_bullets_vs_zombie(Bullets *bullets, Zombie *zombie, float damage, Effects *effects);

/* Resolves a claw strike (zombie->struck): it lands if the player is still
 * within ZOMBIE_ATTACK_RANGE in front of the zombie, and pushes her away.
 * Returns true if it landed. */
bool combat_zombie_vs_player(const Zombie *zombie, Player *player);

#endif
