#ifndef GAME_MISSION_H
#define GAME_MISSION_H

#include "game/stages.h"

typedef struct {
    unsigned seconds[3]; /* Index 0 = one star, 2 = three stars. */
    int health_percent[3];
} MissionGoals;

typedef struct {
    unsigned ticks;
    float tick_fraction;
    int stars, health_percent;
    bool new_record, claimed;
    int base_xp, base_gold;
    int star_xp, star_gold, record_xp, record_gold;
} MissionReport;

MissionGoals mission_goals(int stage_index);
void mission_advance(MissionReport *report, float seconds);
int mission_health_percent(int health, int max_health);
int mission_stars(int stage_index, unsigned ticks, int health, int max_health);
int mission_base_xp(int stage_index);
int mission_base_gold(int stage_index);
/* Freezes the result and updates personal bests once. Base rewards are
 * granted by the mission chest; only star/record extras remain to be paid. */
bool mission_finish(MissionReport *report, StageRecord *record, int stage_index,
                      int health, int max_health);
void mission_format_time(unsigned ticks, char *text, unsigned capacity);

#endif
