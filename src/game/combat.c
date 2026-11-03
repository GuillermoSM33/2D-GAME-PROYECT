#include "game/combat.h"

#include <math.h>

#include "config.h"

int combat_bullets_vs_zombie(Bullets *bullets, Zombie *zombie, Effects *effects)
{
    int hits = 0;
    for (int i = 0; i < BULLET_MAX && zombie_alive(zombie); i++) {
        Bullet *b = &bullets->items[i];
        if (!b->active || b->glanced == zombie || !zombie_overlaps(zombie, b->prev_x, b->x, b->y))
            continue;
        if (zombie_hit_through(zombie, b->spec.damage, b->spec.armor_share) == HIT_ARMOR &&
            zombie->armor > 0.0f)
            effects_spawn(effects, effect_sparks(), zombie->x, b->y, zombie->facing);
        hits++;
        if (b->spec.ricochet) {
            /* It glances off on to the next one: weaker, unless this one fell. */
            b->spec.ricochet = false;
            b->spec.damage *= zombie_alive(zombie) ? RICOCHET_LOSS : RICOCHET_KILL_BONUS;
            b->glanced = zombie;
            effects_spawn(effects, effect_sparks(), zombie->x, b->y, zombie->facing);
            continue;
        }
        b->active = false;
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
    if (player->jump.height > ZOMBIE_CLAW_HEIGHT)
        return false; /* Over its claw: high in a jump, or up on a barricade */
    player_hit(player, zombie_attack_damage(zombie), zombie->facing);
    return true;
}
