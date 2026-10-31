#include "game/combat.h"

#include <math.h>

#include "config.h"

int combat_bullets_vs_zombie(Bullets *bullets, Zombie *zombie, float damage, Effects *effects)
{
    int hits = 0;
    for (int i = 0; i < BULLET_MAX && zombie_alive(zombie); i++) {
        Bullet *b = &bullets->items[i];
        if (!b->active || !zombie_overlaps(zombie, b->prev_x, b->x, b->y))
            continue;
        b->active = false;
        if (zombie_hit(zombie, damage) == HIT_ARMOR)
            effects_spawn(effects, effect_sparks(), zombie->x, b->y, zombie->facing);
        hits++;
    }
    return hits;
}

bool combat_zombie_vs_player(const Zombie *zombie, Player *player)
{
    if (!zombie->struck || !player_alive(player))
        return false;
    float gap = player->x - zombie->x;
    bool in_front = gap * (float)zombie->facing >= 0.0f;
    if (!in_front || fabsf(gap) > ZOMBIE_ATTACK_RANGE)
        return false;
    player_hit(player, zombie_attack_damage(zombie), zombie->facing);
    return true;
}
